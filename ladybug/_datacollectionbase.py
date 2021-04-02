# coding=utf-8
"""Base class for Ladybug Data Collections."""

from __future__ import division

from .header import Header
from .datatype.base import DataTypeBase
from .datatype import TYPESDICT, BASETYPES

try:
    from collections.abc import Iterable  # python < 3.7
except ImportError:
    from collections import Iterable  # python >= 3.8
from string import ascii_lowercase
import math

try:
    from itertools import izip as zip  # python 2
except ImportError:
    xrange = range  # python 3


class BaseCollection(object):
    """Base class for all Data Collections.

    Args:
        header: A Ladybug Header object.
        values: A list of values.
        datetimes: A list of Ladybug DateTime objects that aligns with
            the list of values.
    """

    __slots__ = ('_header', '_values', '_datetimes', '_validated_a_period')
    _collection_type = None
    _mutable = True
    _enumeration = None

    def __init__(self, header, values, datetimes):
        """Initialize base collection.
        """
        assert isinstance(header, Header), \
            'header must be a Ladybug Header object. Got {}'.format(type(header))
        assert isinstance(datetimes, Iterable) \
            and not isinstance(datetimes, (str, dict, bytes, bytearray)), \
            'datetimes should be a list or tuple. Got {}'.format(type(datetimes))

        self._header = header
        self._datetimes = tuple(datetimes)
        self.values = values
        self._validated_a_period = False

    @classmethod
    def from_dict(cls, data):
        """Create a Data Collection from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "header": {},  # A Ladybug Header
            "values": [],  # An array of values
            "datetimes": [],  # An array of datetimes
            "validated_a_period": True  # Boolean for whether header analysis_period
                                        # is valid
            }
        """
        assert 'header' in data, 'Required keyword "header" is missing!'
        assert 'values' in data, 'Required keyword "values" is missing!'
        assert 'datetimes' in data, 'Required keyword "datetimes" is missing!'
        coll = cls(Header.from_dict(data['header']), data['values'], data['datetimes'])
        if 'validated_a_period' in data:
            coll._validated_a_period = data['validated_a_period']
        return coll

    @property
    def header(self):
        """Get the header for this collection."""
        return self._header

    @property
    def datetimes(self):
        """Get a tuple of datetimes for this collection, which align with the values."""
        return self._datetimes

    @property
    def values(self):
        """Get a tuple of numerical values for this collection."""
        return tuple(self._values)

    @values.setter
    def values(self, values):
        self._check_values(values)
        self._values = list(values)

    @property
    def validated_a_period(self):
        """Boolean for whether the header analysis_period is validated against datetimes.

        This will always be True when a collection is derived from a continuous one.
        """
        return self._validated_a_period

    @property
    def bounds(self):
        """Get a tuple of two value as (min, max) of the data."""
        return (min(self._values), max(self._values))

    @property
    def min(self):
        """Get the min of the Data Collection values."""
        return min(self._values)

    @property
    def max(self):
        """Get the max of the Data Collection values."""
        return max(self._values)

    @property
    def average(self):
        """Get the average of the Data Collection values."""
        return sum(self._values) / len(self._values)

    @property
    def median(self):
        """Get the median of the Data Collection values."""
        return self._percentile(self._values, 50)

    @property
    def total(self):
        """Get the total of the Data Collection values."""
        return sum(self._values)

    def convert_to_unit(self, unit):
        """Convert the Data Collection to the input unit.

        Note that this mutates the data collection object, which can have unintended
        consequences depending on how the data collection is used. Use to_unit to
        get a new instance of a collection without mutating this one.
        """
        self._values = self._header.data_type.to_unit(
            self._values, unit, self._header.unit)
        self._header._unit = unit

    def convert_to_ip(self):
        """Convert the Data Collection to IP units.

        Note that this mutates the data collection object, which can have unintended
        consequences depending on how the data collection is used. Use to_ip to
        get a new instance of a collection without mutating this one.
        """
        self._values, self._header._unit = self._header.data_type.to_ip(
            self._values, self._header.unit)

    def convert_to_si(self):
        """Convert the Data Collection to SI units.

        Note that this mutates the data collection object, which can have unintended
        consequences depending on how the data collection is used. Use to_si to
        get a new instance of a collection without mutating this one.
        """
        self._values, self._header._unit = self._header.data_type.to_si(
            self._values, self._header.unit)

    def to_unit(self, unit):
        """Get a Data Collection in the input unit.

        Args:
            unit: Text for the unit to convert the data to (eg. 'C' or 'kWh'). This
                unit must appear under the data collection's header.data_type.units.
        """
        new_data_c = self.duplicate()
        new_data_c.convert_to_unit(unit)
        return new_data_c

    def to_ip(self):
        """Get a Data Collection in IP units."""
        new_data_c = self.duplicate()
        new_data_c.convert_to_ip()
        return new_data_c

    def to_si(self):
        """Get a Data Collection in SI units."""
        new_data_c = self.duplicate()
        new_data_c.convert_to_si()
        return new_data_c

    def is_in_data_type_range(self, raise_exception=True):
        """Check if collection values are in physically possible ranges for the data_type.

        If this method returns False, the collection's values are physically or
        mathematically impossible for the data_type (eg. temperature below
        absolute zero).

        Args:
            raise_exception: Boolean to note whether an exception should be raised
                if an impossible value is found. (Default: True).
        """
        return self._header.data_type.is_in_range(
            self._values, self._header.unit, raise_exception)

    def to_mutable(self):
        """Get a mutable version of this collection."""
        return self.duplicate()

    def to_immutable(self):
        """Get an immutable version of this collection."""
        if self._enumeration is None:
            self._get_mutable_enumeration()
        col_obj = self._enumeration['immutable'][self._collection_type]
        new_obj = col_obj(self.header, self.values, self.datetimes)
        new_obj._validated_a_period = self._validated_a_period
        return new_obj

    def normalize_by_area(self, area, area_unit):
        """Get a Data Collection that is normalized by an area value.

        Note that this method will raise a ValueError if the data type in the header
        of the data collection does not have a normalized_type. Also note that a
        ZeroDivisionError will be raised if the input area is equal to 0.

        Args:
            area: Number representing area by which all of the data is normalized.
            area_unit: Text for the units that the area value is in. Acceptable
                inputs include 'm2', 'ft2' and any other unit that is supported
                in the normalized_type of this datacollection's data type.
        """
        # get an instance of the normalized data type
        head = self.header
        norm_type_class = head.data_type.normalized_type
        assert norm_type_class is not None, \
            'Data type "{}" cannot be normalized by area to yield a useful '\
            'metric.'.format(head.data_type)

        # create the new data collection and assign normalized values
        new_data_c = self.duplicate()
        new_data_c._values = [val / area for val in self.values]

        # normalize the data type and unit in the header
        new_data_c._header._unit = '{}/{}'.format(head.unit, area_unit)
        new_data_c._header._data_type = norm_type_class()
        new_data_c._header._data_type.is_unit_acceptable(new_data_c._header._unit)
        if 'type' in head.metadata:  # key used to identify sophisticated data types
            new_data_c._header.metadata['type'] = \
                '{} {}'.format(new_data_c._header.metadata['type'], 'Intensity')
        return new_data_c

    def highest_values(self, count):
        """Get a list of the the x highest values of the Data Collection and their indices.

        This is useful for situations where one needs to know the times of
        the year when the largest values of a data collection occur.  For example,
        there is a European daylight code that requires an analysis for the hours
        of the year with the greatest exterior illuminance level.  This method
        can be used to help build a schedule for such a study.

        Args:
            count: Integer representing the number of highest values to account for.

        Returns:
            A tuple with two elements.

            -   highest_values:
                The n highest values in data list, ordered from
                highest to lowest.

            -   highest_values_index:
                Indices of the n highest values in data
                list, ordered from highest to lowest.
        """
        count = int(count)
        assert count <= len(self._values), \
            'count must be smaller than or equal to values length. {} > {}.'.format(
                count, len(self._values))
        assert count > 0, \
            'count must be greater than 0. Got {}.'.format(count)
        highest_values = sorted(self._values, reverse=True)[0:count]
        highest_values_index = sorted(list(xrange(len(self._values))),
                                      key=lambda k: self._values[k],
                                      reverse=True)[0:count]
        return highest_values, highest_values_index

    def lowest_values(self, count):
        """Get a list of the the x lowest values of the Data Collection and their indices.

        This is useful for situations where one needs to know the times of
        the year when the smallest values of a data collection occur.

        Args:
            count: Integer representing the number of lowest values to account for.

        Returns:
            A tuple with two elements.

            -   highest_values:
                The n lowest values in data list, ordered from
                lowest to lowest.
            -   lowest_values_index:
                Indices of the n lowest values in data
                list, ordered from lowest to lowest.
        """
        count = int(count)
        assert count <= len(self._values), \
            'count must be <= to Data Collection len. {} > {}.'.format(
                count, len(self._values))
        assert count > 0, \
            'count must be greater than 0. Got {}.'.format(count)
        lowest_values = sorted(self._values)[0:count]
        lowest_values_index = sorted(list(xrange(len(self._values))),
                                     key=lambda k: self._values[k])[0:count]
        return lowest_values, lowest_values_index

    def percentile(self, percentile):
        """Get a value representing a the input percentile of the Data Collection.

        Args:
            percentile: A float value from 0 to 100 representing the
                requested percentile.

        Returns:
            The Data Collection value at the input percentile
        """
        assert 0 <= percentile <= 100, \
            'percentile must be between 0 and 100. Got {}'.format(percentile)
        return self._percentile(self._values, percentile)

    def filter_by_conditional_statement(self, statement):
        """Filter the Data Collection based on a conditional statement.

        Args:
            statement: A conditional statement as a string (e.g. a > 25 and a%5 == 0).
                The variable should always be named as 'a' (without quotations).

        Returns:
            A new Data Collection containing only the filtered data
        """
        _filt_values, _filt_datetimes = self._filter_by_statement(statement)
        if self._enumeration is None:
            self._get_mutable_enumeration()
        col_obj = self._enumeration['mutable'][self._collection_type]
        try:
            collection = col_obj(self.header.duplicate(), _filt_values, _filt_datetimes)
        except AssertionError as e:
            raise AssertionError('No value meets the conditional statement.'
                                 '\n{}'.format(e))
        collection._validated_a_period = self._validated_a_period
        return collection

    def filter_by_pattern(self, pattern):
        """Filter the Data Collection based on a list of booleans.

        Args:
            pattern: A list of True/False values.  Typically, this is a list
                with a length matching the length of the Data Collections values
                but it can also be a pattern to be repeated over the Data Collection.

        Returns:
            A new Data Collection with filtered data
        """
        _filt_values, _filt_datetimes = self._filter_by_pattern(pattern)
        if self._enumeration is None:
            self._get_mutable_enumeration()
        col_obj = self._enumeration['mutable'][self._collection_type]
        collection = col_obj(self.header.duplicate(), _filt_values, _filt_datetimes)
        collection._validated_a_period = self._validated_a_period
        return collection

    def is_collection_aligned(self, data_collection):
        """Check if this Data Collection is aligned with another.

        Aligned Data Collections are of the same Data Collection class, have the
        same number of values and have matching datetimes.

        Args:
            data_collection: The Data Collection which you want to test if this
                collection is aligned with.

        Returns:
            True if collections are aligned, False if not aligned
        """
        if self._collection_type != data_collection._collection_type:
            return False
        elif len(self.values) != len(data_collection.values):
            return False
        elif self.datetimes != data_collection.datetimes:
            return False
        else:
            return True

    def get_aligned_collection(self, value=0, data_type=None, unit=None, mutable=None):
        """Get a collection aligned with this one composed of one repeated value.

        Aligned Data Collections are of the same Data Collection class, have the same
        number of values and have matching datetimes.

        Args:
            value: A value to be repeated in the aliged collection values or
                A list of values that has the same length as this collection.
                Default: 0.
            data_type: The data type of the aligned collection. Default is to
                use the data type of this collection.
            unit: The unit of the aligned collection. Default is to
                use the unit of this collection or the base unit of the
                input data_type (if it exists).
            mutable: An optional Boolean to set whether the returned aligned
                collection is mutable (True) or immutable (False). The default is
                None, which will simply set the aligned collection to have the
                same mutability as the starting collection.
        """
        # set up the header of the new collection
        header = self._check_aligned_header(data_type, unit)

        # set up the values of the new collection
        values = self._check_aligned_value(value)

        # get the correct base class for the aligned collection (mutable or immutable)
        if mutable is None:
            collection = self.__class__(header, values, self.datetimes)
        else:
            if self._enumeration is None:
                self._get_mutable_enumeration()
            if not mutable:
                col_obj = self._enumeration['immutable'][self._collection_type]
            else:
                col_obj = self._enumeration['mutable'][self._collection_type]
            collection = col_obj(header, values, self.datetimes)
        collection._validated_a_period = self._validated_a_period
        return collection

    def duplicate(self):
        """Get a copy of this Data Collection."""
        return self.__copy__()

    def to_dict(self):
        """Convert Data Collection to a dictionary."""
        return {
            'header': self.header.to_dict(),
            'values': self._values,
            'datetimes': self.datetimes,
            'validated_a_period': self._validated_a_period,
            'type': self.__class__.__name__
        }

    @staticmethod
    def filter_collections_by_statement(data_collections, statement):
        """Generate a filtered data collections according to a conditional statement.

        Args:
            data_collections: A list of aligned Data Collections to be evaluated
                against the statement.
            statement: A conditional statement as a string (e.g. a>25 and a%5==0).
                The variable should always be named as 'a' (without quotations).

        Returns:
            collections -- A list of Data Collections that have been filtered based
            on the statement.
        """
        pattern = BaseCollection.pattern_from_collections_and_statement(
            data_collections, statement)
        try:
            collections = [coll.filter_by_pattern(pattern) for coll in data_collections]
        except AssertionError as e:
            raise AssertionError('No value meets the conditional statement.'
                                 '\n{}'.format(e))
        return collections

    @staticmethod
    def pattern_from_collections_and_statement(data_collections, statement):
        """Generate a list of booleans from data collections and a conditional statement.

        Args:
            data_collections: A list of aligned Data Collections to be evaluated
                against the statement.
            statement: A conditional statement as a string (e.g. a>25 and a%5==0).
                The variable should always be named as 'a' (without quotations).

        Returns:
            pattern -- A list of True/False booleans with the length of the
            Data Collections where True meets the conditional statement
            and False does not.
        """
        BaseCollection.are_collections_aligned(data_collections)
        correct_var = BaseCollection._check_conditional_statement(
            statement, len(data_collections))

        # replace the operators of the statement with non-alphanumeric characters
        # necessary to avoid replacing the characters of the operators
        num_statement_clean = BaseCollection._replace_operators(statement)

        pattern = []
        for i in xrange(len(data_collections[0])):
            num_statement = num_statement_clean
            # replace the variable names with their numerical values
            for j, coll in enumerate(data_collections):
                var = correct_var[j]
                num_statement = num_statement.replace(var, str(coll[i]))
            # put back the operators
            num_statement = BaseCollection._restore_operators(num_statement)
            pattern.append(eval(num_statement, {}))
        return pattern

    @staticmethod
    def are_collections_aligned(data_collections, raise_exception=True):
        """Test if a series of Data Collections are aligned with one another.

        Aligned Data Collections are of the same Data Collection class, have the
        same number of values and have matching datetimes.

        Args:
            data_collections: A list of Data Collections for which you want to
                test if they are al aligned with one another.

        Returns:
            True if collections are aligned, False if not aligned
        """
        if len(data_collections) > 1:
            first_coll = data_collections[0]
            for coll in data_collections[1:]:
                if not first_coll.is_collection_aligned(coll):
                    if raise_exception:
                        error_msg = '{} Data Collection is not aligned with '\
                            '{} Data Collection.'.format(
                                first_coll.header.data_type, coll.header.data_type)
                        raise ValueError(error_msg)
                    return False
        return True

    @staticmethod
    def compute_function_aligned(funct, data_collections, data_type, unit):
        """Compute a function with a list of aligned data collections or individual values.

        Args:
            funct: A function with a single numerical value as output and one or
                more numerical values as input.
            data_collections: A list with a length equal to the number of arguments
                for the function. Items of the list can be either Data Collections
                or individual values to be used at each datetime of other collections.
            data_type: An instance of a Ladybug data type that describes the results
                of the funct.
            unit: The units of the funct results.

        Returns:
            A Data Collection with the results function. If all items in this list of
            data_collections are individual values, only a single value will be returned.

        Usage:

        .. code-block:: python

            from ladybug.datacollection import HourlyContinuousCollection
            from ladybug.epw import EPW
            from ladybug.psychrometrics import humid_ratio_from_db_rh
            from ladybug.datatype.percentage import HumidityRatio

            epw_file_path = './epws/denver.epw'
            denver_epw = EPW(epw_file_path)
            pressure_at_denver = 85000
            hr_inputs = [denver_epw.dry_bulb_temperature,
                         denver_epw.relative_humidity,
                         pressure_at_denver]
            humid_ratio = HourlyContinuousCollection.compute_function_aligned(
                humid_ratio_from_db_rh, hr_inputs, HumidityRatio(), 'fraction')
            # humid_ratio will be a Data Collection of humidity ratios at Denver
        """
        # check that all inputs are either data collections or floats
        data_colls = []
        for i, func_input in enumerate(data_collections):
            if isinstance(func_input, BaseCollection):
                data_colls.append(func_input)
            else:
                try:
                    data_collections[i] = float(func_input)
                except ValueError:
                    raise TypeError('Expected a number or a Data Collection. '
                                    'Got {}'.format(type(func_input)))

        # run the function and return the result
        if len(data_colls) == 0:
            return funct(*data_collections)
        else:
            BaseCollection.are_collections_aligned(data_colls)
            val_len = len(data_colls[0].values)
            for i, col in enumerate(data_collections):
                data_collections[i] = [col] * val_len if isinstance(col, float) else col
            result = data_colls[0].get_aligned_collection(data_type=data_type, unit=unit)
            for i in xrange(val_len):
                result[i] = funct(*[col[i] for col in data_collections])
            return result

    def _time_aggregated_collection(self, timestep):
        """Get a time-aggregated version of this collection."""
        # get an instance of the time aggregated data type
        head = self.header
        time_class = head.data_type.time_aggregated_type
        assert time_class is not None, \
            'Data type "{}" cannot be time aggregated to yield a useful '\
            'metric.'.format(head.data_type)

        # create the new data collection and assign normalized values
        new_data_c = self.to_unit(head.data_type.units[0])
        factor = head.data_type.time_aggregated_factor / timestep
        new_data_c._values = [val * factor for val in new_data_c._values]
        new_data_c._header._data_type = time_class()
        new_data_c._header._unit = new_data_c._header._data_type.units[0]
        return new_data_c

    def _time_rate_of_change_collection(self, timestep):
        """Get a time-rate-of-change version of this collection."""
        # get an instance of the time aggregated data type
        head = self.header
        dat_type, time_class = head.data_type, None
        # first see if there's a specific data type for the current one
        for typ_clss in TYPESDICT.values():
            if typ_clss._time_aggregated_type is None:
                continue
            elif dat_type.__class__ == typ_clss._time_aggregated_type:
                time_class = typ_clss
                break
        # then, check to see if there's any base type
        if time_class is None:
            for typ_clss_name in BASETYPES:
                typ_clss = TYPESDICT[typ_clss_name]
                if typ_clss._time_aggregated_type is None:
                    continue
                elif isinstance(dat_type, typ_clss._time_aggregated_type):
                    time_class = typ_clss
                break
        # if nothing was found, throw an error
        if time_class is None:
            raise ValueError('Data type "{}" does not have a time-rate-of-'
                             'change metric.'.format(head.data_type))

        # create the new data collection and assign normalized values
        new_data_c = self.to_unit(head.data_type.units[0])
        factor = typ_clss._time_aggregated_factor / timestep
        new_data_c._values = [val / factor for val in new_data_c._values]
        new_data_c._header._data_type = time_class()
        new_data_c._header._unit = new_data_c._header._data_type.units[0]
        return new_data_c

    @staticmethod
    def _check_conditional_statement(statement, num_collections):
        """Method to check conditional statements to be sure that they are valid.

        Args:
            statement: A conditional statement as a string (e.g. a>25 and a%5==0).
                The variable should always be named as 'a' (without quotations).
            num_collections: An integer representing the number of data collections
                that the statement will be evaluating.

        Returns:
            correct_var -- A list of the correct variable names that should be
                used within the statement (eg. ['a', 'b', 'c'])
        """
        # Determine what the list of variables should be based on the num_collections
        correct_var = list(ascii_lowercase)[:num_collections]

        # Clean out the operators of the statement
        st_statement = BaseCollection._remove_operators(statement)
        parsed_st = [s for s in st_statement if s.isalpha()]

        # Perform the check
        for var in parsed_st:
            if var not in correct_var:
                raise ValueError(
                    'Invalid conditional statement: {}\n '
                    'Statement should be a valid Python statement'
                    ' and the variables should be named as follows: {}'.format(
                        statement, ', '.join(correct_var))
                )
        return correct_var

    @staticmethod
    def _remove_operators(statement):
        """Remove logical operators from a statement."""
        return statement.lower().replace("and", "").replace("or", "") \
            .replace("not", "").replace("in", "").replace("is", "")

    @staticmethod
    def _replace_operators(statement):
        """Replace logical operators of a statement with non-alphanumeric characters."""
        return statement.lower().replace("and", "&&").replace("or", "||") \
            .replace("not", "~").replace("in", "<<").replace("is", "$")

    @staticmethod
    def _restore_operators(statement):
        """Restore python logical operators from previously replaced ones."""
        return statement.replace("&&", "and").replace("||", "or") \
            .replace("~", "not").replace("<<", "in").replace("$", "is")

    @staticmethod
    def linspace(start, stop, num):
        """Get evenly spaced numbers calculated over the interval start, stop.

        This method is similar to native Python range except that it takes a number of
        divisions instead of a step. It is also equivalent to numpy's linspace method.

        Args:
            start: Start interval index as integer or float.
            stop: Stop interval index as integer or float.
            num: Number of divisions as integer.

        Returns:
            A list of numbers.

        Usage:

        .. code-block:: python

            from BaseCollection import linspace

            linspace(0, 5, 6)
            # >> [0., 1., 2., 3., 4., 5.]
        """
        try:
            delta = stop - start
            return [i * (delta / (num - 1)) + start for i in range(num)]
        except ZeroDivisionError:
            return [start]

    @staticmethod
    def arange(start, stop, step):
        """Return evenly spaced fractional or whole values within a given interval.

        This function acts like the Python range method, but can also account for
        fractional values. It is equivalent to the numpy.arange function.

        Args:
            start: Number for inclusive start of interval.
            stop: Number for exclusive end of interval.
            step: Number for step size of interval.

        Returns:
            Generator of evenly spaced values.

        Usage:

        .. code-block:: python

            from BaseCollection import arange

            arange(1, 351, 50)
            # >> [1, 51, 101, 151, 201, 251, 301]
        """

        val = start

        if start <= stop:
            def ineq(a, b): return a < b
        else:
            def ineq(a, b): return a > b

        while ineq(val, stop) and abs(val - stop) > 1e-10:
            yield val
            val += step

    @staticmethod
    def histogram(values, bins, key=None):
        """Compute the frequency histogram from a list of values.

        The data is binned inclusive of the lower bound but exclusive of the upper bound
        for intervals. See usage for example of losing the last number in the following
        dataset because of exclusive upper bound.

        Args:
            values: Set of numerical data as a list.
            bins: A monotonically increasing array of uniform-width bin edges, excluding
                the rightmost edge.
            key: Optional parameter to define key to bin values by, as a function. If not
                provided, the histogram will be binned by the value.

        Returns:
            A list of lists representing the ordered values binned by frequency.

        Usage:

        .. code-block:: python

            from BaseCollection import histogram

            # Simple example
            histogram([0, 0, 0.9, 1, 1.5, 1.99, 2, 3], (0, 1, 2, 3))
            # >> [[0, 0, 0.9], [1, 1.5, 1.99], [2]]

            # With key parameter
            histogram(
                zip([0, 0, 0.9, 1, 1.5, 1.99],
                    ['a', 'b', 'c', 'd', 'e', 'f']),
                    (0, 1, 2), key=lambda k: k[0])
            # >> [[(0, 'a'), (0, 'b'), (0.9, 'c')], [(1, 'd'), (1.5, 'e'), (1.99, 'f')]]
        """
        if key is None:
            def key(v):
                return v

        vals = sorted(values, key=key)
        min_bound, max_bound = min(bins), max(bins)
        bin_bound_num = len(bins)

        # Init histogram bins
        hist = [[] for i in range(bin_bound_num - 1)]
        bin_index = 0

        for val in vals:
            k = key(val)
            # Ignore values out of range
            if k < min_bound or k > max_bound:
                continue

            # This loop will iterate through the bin upper bounds.
            # If the value is within the bounds, the lower bound
            # of the bin_index is updated, and the loop is broken
            for i in range(bin_index, bin_bound_num - 1):
                if k < bins[i + 1]:
                    hist[i].append(val)
                    bin_index = i
                    break
        return hist

    @staticmethod
    def histogram_circular(values, bins, hist_range=None, key=None):
        """Compute the frequency histogram from a list of circular values.

        Circular values refers to a set of values where there is no distinction between
        values at the lower or upper end of the range, for example angles in a circle, or
        time. The data is binned inclusive of the lower bound but exclusive of the upper
        bound for intervals.

        Args:
            values: Set of numerical data as a list.
            bins: An array of uniform-width bin edges, excluding the rightmost edge.
                These values do not have to be monotonically increasing.
            hist_range: Optional parameter to define the lower and upper range of the
                histogram as a tuple of numbers. If not provided the range is
                ``(min(key(values)), max(key(values))+1)``.
            key: Optional parameter to define key to bin values by, as a function. If not
                provided, the histogram will be binned by the value.

        Returns:
            A list of lists representing the ordered values binned by frequency.

        Usage:

        .. code-block:: python

            from BaseCollection import histogram_circular

            histogram_circular([358, 359, 0, 1, 2, 3], (358, 0, 3))
            # >> [[358, 359], [0, 1, 2]]
        """
        if key is None:
            def key(v):
                return v

        vals = sorted(values, key=key)

        if hist_range is None:
            hist_range = (key(vals[0]), key(vals[-1]) + 1)

        bin_bound_num = len(bins) - 1

        # Init histogram bins
        hist = [[] for i in range(bin_bound_num)]
        for val in vals:
            k = key(val)

            # Ignore values out of range
            if k < hist_range[0] or k >= hist_range[1]:
                continue

            # This loop will iterate through the bin upper bounds.
            # If the value is within the bounds, the loop is broken.
            # Since values at the end of the list can still be binned
            # into the earlier histogram bars for circular
            # data, we don't update the bin_index.
            for i in range(bin_bound_num):
                if bins[i] < bins[i + 1]:
                    if k >= bins[i] and k < bins[i + 1]:
                        hist[i].append(val)
                        break
                else:
                    # If the interval starts data from the end of the list,
                    # split the conditional checks into two to check two
                    # intervals.
                    interval1 = (k <= hist_range[1] and k >= bins[i])
                    interval2 = (k < bins[i + 1] and k >= hist_range[0])
                    if interval1 or interval2:
                        hist[i].append(val)
                        break

        return hist

    def _filter_by_statement(self, statement):
        """Filter the data collection based on a conditional statement."""
        self.__class__._check_conditional_statement(statement, 1)
        _filt_values, _filt_datetimes = [], []
        for i, a in enumerate(self._values):
            if eval(statement, {'a': a}):
                _filt_values.append(a)
                _filt_datetimes.append(self.datetimes[i])
        return _filt_values, _filt_datetimes

    def _filter_by_pattern(self, pattern):
        """Filter the Filter the Data Collection based on a list of booleans."""
        try:
            _len = len(pattern)
        except TypeError:
            raise TypeError("pattern is not a list of Booleans. Got {}".format(
                type(pattern)))
        _filt_values = [d for i, d in enumerate(self._values) if pattern[i % _len]]
        _filt_datetimes = [d for i, d in enumerate(self.datetimes) if pattern[i % _len]]
        return _filt_values, _filt_datetimes

    def _check_values(self, values):
        """Check values whenever they come through the values setter."""
        assert isinstance(values, Iterable) and not \
            isinstance(values, (str, dict, bytes, bytearray)), \
            'values should be a list or tuple. Got {}'.format(type(values))
        assert len(values) == len(self.datetimes), \
            'Length of values list must match length of datetimes list. ' \
            '{} != {}'.format(len(values), len(self.datetimes))
        assert len(values) > 0, 'Data Collection must include at least one value'

    def _check_aligned_header(self, data_type, unit):
        """Check the header inputs whenever get_aligned_collection is called."""
        if data_type is not None:
            assert isinstance(data_type, DataTypeBase), \
                'data_type must be a Ladybug DataType. Got {}'.format(type(data_type))
            if unit is None:
                unit = data_type.units[0]
        else:
            data_type = self.header.data_type
            unit = unit or self.header.unit
        return Header(data_type, unit, self.header.analysis_period, self.header.metadata)

    def _check_aligned_value(self, value):
        """Check the value input whenever get_aligned_collection is called."""
        if isinstance(value, Iterable) and not isinstance(
                value, (str, dict, bytes, bytearray)):
            assert len(value) == len(self._values), "Length of value ({}) must match "\
                "the length of this collection's values ({})".format(
                    len(value), len(self._values))
            values = value
        else:
            values = [value] * len(self._values)
        return values

    def _percentile(self, values, percent, key=lambda x: x):
        """Find the percentile of a list of values.

        Args:
            values: A list of values for which percentiles are desired
            percent: A float value from 0 to 100 representing the requested percentile.
            key: optional key function to compute value from each element of N.

        Returns:
            The percentile of the values
        """
        vals = sorted(values)
        k = (len(vals) - 1) * (percent / 100)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return key(vals[int(k)])
        d0 = key(vals[int(f)]) * (c - k)
        d1 = key(vals[int(c)]) * (k - f)
        return d0 + d1

    def _average(self, vals):
        return sum(vals) / len(vals)

    def _total(self, vals):
        return sum(vals)

    def _get_percentile_function(self, percentile):
        def percentile_function(vals):
            return self._percentile(vals, percentile)
        return percentile_function

    def _get_mutable_enumeration(self):
        self._enumeration = {'mutable': {}, 'immutable': {}}
        for clss in self._all_subclasses(BaseCollection):
            if clss._mutable:
                self._enumeration['mutable'][clss._collection_type] = clss
            else:
                self._enumeration['immutable'][clss._collection_type] = clss

    def _all_subclasses(self, clss):
        return set(clss.__subclasses__()).union(
            [s for c in clss.__subclasses__() for s in self._all_subclasses(c)])

    def __len__(self):
        return len(self._values)

    def __getitem__(self, key):
        return self._values[key]

    def __setitem__(self, key, value):
        self._values[key] = value

    def __iter__(self):
        return iter(self._values)

    def __contains__(self, item):
        return item in self._values

    def __add__(self, other):
        new_vals = self._add_values(other)
        new_obj = self.__class__(self.header.duplicate(), new_vals, self.datetimes)
        new_obj._validated_a_period = self._validated_a_period
        return new_obj

    def __sub__(self, other):
        new_vals = self._sub_values(other)
        new_obj = self.__class__(self.header.duplicate(), new_vals, self.datetimes)
        new_obj._validated_a_period = self._validated_a_period
        return new_obj

    def __mul__(self, other):
        new_vals = self._mul_values(other)
        new_obj = self.__class__(self.header.duplicate(), new_vals, self.datetimes)
        new_obj._validated_a_period = self._validated_a_period
        return new_obj

    def __div__(self, other):
        new_vals = self._div_values(other)
        new_obj = self.__class__(self.header.duplicate(), new_vals, self.datetimes)
        new_obj._validated_a_period = self._validated_a_period
        return new_obj

    def __truediv__(self, other):
        new_vals = self._div_values(other)
        new_obj = self.__class__(self.header.duplicate(), new_vals, self.datetimes)
        new_obj._validated_a_period = self._validated_a_period
        return new_obj

    def __neg__(self):
        new_vals = [-v_1 for v_1 in self._values]
        new_obj = self.__class__(self.header.duplicate(), new_vals, self.datetimes)
        new_obj._validated_a_period = self._validated_a_period
        return new_obj

    def _add_values(self, other):
        if isinstance(other, (int, float)):
            new_vals = [v_1 + other for v_1 in self._values]
        else:
            assert self._collection_type == other._collection_type, \
                '{} cannot be added to {}'.format(self.__class__, other.__class__)
            assert len(self) == len(other), 'Length of DataCollections must match in ' \
                'order to add them together. {} != {}'.format(len(self), len(other))
            new_vals = [v_1 + v_2 for v_1, v_2 in zip(self._values, other._values)]
        return new_vals

    def _sub_values(self, other):
        if isinstance(other, (int, float)):
            new_vals = [v_1 - other for v_1 in self._values]
        else:
            assert self._collection_type == other._collection_type, \
                '{} cannot be subtracted from {}'.format(other.__class__, self.__class__)
            assert len(self) == len(other), 'Length of DataCollections must match ' \
                'to subtract one from the other. {} != {}'.format(len(self), len(other))
            new_vals = [v_1 - v_2 for v_1, v_2 in zip(self._values, other._values)]
        return new_vals

    def _mul_values(self, other):
        if isinstance(other, (int, float)):
            new_vals = [v_1 * other for v_1 in self._values]
        else:
            assert self._collection_type == other._collection_type, \
                '{} cannot be multiplied by {}'.format(other.__class__, self.__class__)
            assert len(self) == len(other), 'Length of DataCollections must match ' \
                'to multiply them together. {} != {}'.format(len(self), len(other))
            new_vals = [v_1 * v_2 for v_1, v_2 in zip(self._values, other._values)]
        return new_vals

    def _div_values(self, other):
        if isinstance(other, (int, float)):
            new_vals = [v_1 / other for v_1 in self._values]
        else:
            assert self._collection_type == other._collection_type, \
                '{} cannot be divided by {}'.format(other.__class__, self.__class__)
            assert len(self) == len(other), 'Length of DataCollections must match ' \
                'to divide them. {} != {}'.format(len(self), len(other))
            new_vals = [v_1 / v_2 for v_1, v_2 in zip(self._values, other._values)]
        return new_vals

    @property
    def is_continuous(self):
        """Boolean denoting whether the data collection is continuous."""
        return False

    @property
    def is_mutable(self):
        """Boolean denoting whether the data collection is mutable."""
        return self._mutable

    def __key(self):
        return self.header, self.values, self.datetimes, self.validated_a_period

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__key() == other.__key()

    def __ne__(self, value):
        return not self.__eq__(value)

    def __copy__(self):
        collection = self.__class__(
            self.header.duplicate(), list(self._values), self.datetimes)
        collection._validated_a_period = self._validated_a_period
        return collection

    def ToString(self):
        """Overwrite .NET ToString method."""
        return self.__repr__()

    def __repr__(self):
        """Discontinuous Collection representation."""
        return "Discontinuous Data Collection\n{} ({})\n...{} values...".format(
            self.header.data_type, self.header.unit, len(self._values))
