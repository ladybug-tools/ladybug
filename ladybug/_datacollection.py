# coding=utf-8
"""Ladybug data collection."""
from __future__ import division

from .header import Header
from .dt import DateTime
from .analysisperiod import AnalysisPeriod

from copy import deepcopy
import string


class DiscontinuousCollection(object):
    """Class for Discontinouus Data Collections."""

    __slots__ = ('_header', '_values', '_datetimes')

    def __init__(self, header, values, datetimes):
        """Init class."""
        assert isinstance(header, Header), \
            'header must be a Ladybug Header object. Got {}'.format(type(header))
        assert isinstance(datetimes, list), \
            'datetimes must be a list. Got {}'.format(type(datetimes))

        self._header = header
        self._datetimes = datetimes
        self.values = values

    @classmethod
    def from_json(cls, data):
        """Create a Data Collection from a dictionary.

        Args:
            {
                "header": A Ladybug Header,
                "values": An array of values,
                "datetimes": An array of datetimes
            }
        """
        assert 'header' in data, 'Required keyword "header" is missing!'
        assert 'values' in data, 'Required keyword "values" is missing!'
        assert 'datetimes' in data, 'Required keyword "datetimes" is missing!'
        return cls(Header.from_json(data['header']),
                   data['values'],
                   [DateTime.from_json(dat) for dat in data['datetimes']])

    @property
    def header(self):
        """Return the header for this collection."""
        return self._header

    @property
    def datetimes(self):
        """Return datetimes for this collection as a tuple."""
        return tuple(self._datetimes)

    @property
    def values(self):
        """Return the list of numerical values."""
        return self._values

    @values.setter
    def values(self, values):
        assert isinstance(values, list), \
            'values must be a list. Got {}'.format(type(values))
        assert len(values) == len(self.datetimes), \
            'Length of values list must match length of datetimes list. {} != {}'.format(
                len(values), len(self.datetimes))
        self._values = values

    @property
    def bounds(self):
        """Return a tuple as (min, max)."""
        return (min(self.values), max(self.values))

    @property
    def min(self):
        """Return the min of the Data Collection values."""
        return min(self.values)

    @property
    def max(self):
        """Return the max of the Data Collection values."""
        return max(self.values)

    @property
    def average(self):
        """Return the average of the Data Collection values."""
        return sum(self.values) / len(self.values)

    def duplicate(self):
        """Return a copy of the current Data Collection."""
        return DiscontinuousCollection(
            self.header.duplicate(), deepcopy(self.values), self.datetimes)

    def convert_to_unit(self, unit):
        """Convert the Data Collection to the input unit."""
        self._values = self._header.data_type.to_unit(
            self._values, unit, self._header.unit)
        self._header._unit = unit

    def convert_to_ip(self):
        """Convert the Data Collection to IP units."""
        self._values, self._header._unit = self._header.data_type.to_ip(
                self._data, self._header.unit)

    def convert_to_si(self):
        """Convert the Data Collection to SI units."""
        self._values, self._header._unit = self._header.data_type.to_si(
                self._data, self._header.unit)

    def to_unit(self, unit):
        """Return a Data Collection in the input unit."""
        new_data_c = self.duplicate()
        new_data_c.convert_to_unit(unit)
        return new_data_c

    def to_ip(self):
        """Return a Data Collection in IP units."""
        new_data_c = self.duplicate()
        new_data_c.convert_to_ip()
        return new_data_c

    def to_si(self):
        """Return a Data Collection in SI units."""
        new_data_c = self.duplicate()
        new_data_c.convert_to_si()
        return new_data_c

    def is_in_data_type_range(self, raise_exception=True):
        """Check if the Data Collection values are in permissable ranges for the data_type.

        If this method returns False, the Data Collection's data is
        physically or mathematically impossible for the data_type."""
        return self._header.data_type.is_in_range(
            self.values, self._header.unit, raise_exception)

    def is_in_epw_range(self, raise_exception=True):
        """Check if Data Collection values are in permissable ranges for EPW files."""
        return self._header.data_type.is_in_range_epw(
            self.values, self._header.unit, raise_exception)

    def get_highest_values(self, count):
        """Find the highest values in the Data Collection.

        Args:
            count: Integer representing the number of highest values to account for.

        Returns:
            highest_values: The n highest values in data list, ordered from
                highest to lowest.
            highest_values_index: Indicies of the n highest values in data
                list, ordered from highest to lowest.
        """
        count = int(count)
        assert count <= len(self._values), \
            'count must be smaller than or equal to values length. {} > {}.'.format(
                count, len(self._values))
        assert count > 0, \
            'count must be greater than 0. Got {}.'.format(count)
        highest_values = sorted(self._values, reverse=True)[0:count]
        highest_values_index = sorted(range(len(self._values)),
                                      key=lambda k: self._values[k],
                                      reverse=True)[0:count]
        return highest_values, highest_values_index

    def get_lowest_values(self, count):
        """Find the lowest values in the Data Collection.

        Args:
            count: Integer representing the number of lowest values to account for.

        Returns:
            highest_values: The n lowest values in data list, ordered from
                lowest to lowest.
            lowest_values_index: Indicies of the n lowest values in data
                list, ordered from lowest to lowest.
        """
        count = int(count)
        assert count <= len(self._values), \
            'count must be <= to Data Collection len. {} > {}.'.format(
                count, len(self._values))
        assert count > 0, \
            'count must be greater than 0. Got {}.'.format(count)
        lowest_values = sorted(self._values)[0:count]
        lowest_values_index = sorted(range(len(self._values)),
                                     key=lambda k: self._values[k])[0:count]
        return lowest_values, lowest_values_index

    def filter_by_conditional_statement(self, statement):
        """Filter the list based on a conditional statement.

        Args:
            statement: A conditional statement as a string (e.g. a > 25 and a%5 == 0).
                The variable should always be named as 'a' (without quotations).

        Return:
            A new Data Collection containing only the filtered data

        Usage:
           epw = EPW("c:/ladybug/weatherdata.epw")
           DBT = epw.dry_bulb_temperature
           # filter data for when dry bulb temperature is more then 25
           filtered_DBT = DBT.filter_by_conditional_statement('x > 25')
        """
        self._check_conditional_statement(statement, 1)
        statement = statement.replace('a', 'd')

        _filt_values = []
        _filt_datetimes = []
        for i, d in enumerate(self.values):
            if eval(statement, globals={'d': d}):
                _filt_values.append(d)
                _filt_datetimes.append(self.datetimes[i])

        # create a new Data Collection
        _filt_header = self.header.duplicate()
        return DiscontinuousCollection(_filt_header, _filt_values, _filt_datetimes)

    def filter_by_pattern(self, pattern):
        """Filter the Data Collection based on a list of booleans.

        Args:
            pattern: A list of True/False values.  Typically, this is a list
                with a length matching the length of the Data Collections values
                but it can also be a pattern to be repeated over the Data Collection.

        Return:
            A new Data Collection with filtered data
        """
        try:
            _len = len(pattern)
        except TypeError:
            raise TypeError("pattern should be a list of Booleans.")
        _filt_values = [d for i, d in enumerate(self.values) if pattern[i % _len]]
        _filt_datetimes = [d for i, d in enumerate(self.datetimes) if pattern[i % _len]]
        _filt_header = self.header.duplicate()
        return DiscontinuousCollection(_filt_header, _filt_values, _filt_datetimes)

    def is_collection_aligned(self, data_collection):
        """Check if this Data Collection is aligned with another.

        Aligned Data Collections are of the same type, the same number of values
        and have matching datetimes.

        Args:
            data_collection: The Data Collection which you want to test if this
                collection is aligned with.

        Return:
            True if collections are aligned, Fale if not aligned
        """
        if type(self) != type(data_collection):
            return False
        elif len(self.values) != len(data_collection.values):
            return False
        elif self.datetimes != data_collection.datetimes:
            return False
        else:
            return True

    @staticmethod
    def filter_collections_by_statement(data_collections, statement):
        """Generate a filtered data collections according to a conditional statement.

        Args:
            data_collections: A list of aligned Data Collections to be evaluated
                against the statement.
            statement: A conditional statement as a string (e.g. a>25 and a%5==0).
                The variable should always be named as 'a' (without quotations).

        Return:
            collections: A list of Data Collections that have been filtered based
                on the statement.
        """
        pattern = DiscontinuousCollection.pattern_from_collections_and_statement(
            data_collections, statement)
        collections = [coll.filter_by_pattern(pattern) for coll in data_collections]
        return collections

    @staticmethod
    def pattern_from_collections_and_statement(data_collections, statement):
        """Generate a list of booleans from data collections and a conditional statement.

        Args:
            data_collections: A list of aligned Data Collections to be evaluated
                against the statement.
            statement: A conditional statement as a string (e.g. a>25 and a%5==0).
                The variable should always be named as 'a' (without quotations).

        Return:
            pattern: A list of True/False booleans with the length of the
                Data Collections where True meets the conditional statement
                and False does not.
        """
        DiscontinuousCollection.are_collections_aligned(data_collections)
        correct_var = DiscontinuousCollection._check_conditional_statement(
            statement, len(data_collections))

        pattern = []
        for i in range(len(data_collections[0])):
            num_statement = statement
            for j, coll in enumerate(data_collections):
                var = correct_var[j]
                num_statement = num_statement.replace(var, coll[i])
            pattern.append(eval(num_statement, globals={}))
        return pattern

    @staticmethod
    def are_collections_aligned(data_collections, raise_exception=True):
        """Test if a series of Data Collections are aligned with one another.

        Aligned Data Collections are of the same type, the same number of values
        and have matching datetimes.

        Args:
            data_collections: A list of Data Collections for which you want to
                test if they are al aligned with one another.

        Return:
            True if collections are aligned, Fale if not aligned
        """
        if len(data_collections) > 1:
            first_coll = data_collections[0]
            for coll in data_collections[1:]:
                if not first_coll.is_collection_aligned(coll):
                    if raise_exception is True:
                        error_msg = '{} Data Collection is not aligned with '\
                            '{} Data Collection.'.format(
                                first_coll.header.data_type, coll.header.data_type)
                        raise ValueError(error_msg)
                    return False
        return True

    def _check_conditional_statement(self, statement, num_collections):
        """Method to check conditional statements to be sure that they are valid.

        Args:
            statement: A conditional statement as a string (e.g. a>25 and a%5==0).
                The variable should always be named as 'a' (without quotations).
            num_collections: An integer representing the number of data collections
                that the statement will be evaluating.

        Return:
            correct_var: A list of the correct variable names that should be
                used within the statement (eg. ['a', 'b', 'c'])
        """
        # Determine what the list of variables should be based on the num_collections
        correct_var = list(string.ascii_lowercase)[:num_collections]

        # Clean out the oeprators of the statement
        st_statement = statement.lower() \
            .replace("and", "").replace("or", "") \
            .replace("not", "").replace("in", "").replace("is", "")
        parsed_st = [s for s in st_statement if s.isalpha()]

        # Perform the chec
        assert list(set(parsed_st)) == correct_var, \
            'Invalid conditional statement: {}\n '\
            'Statement should be a valid Python statement'\
            ' and the variables should be named as follows: {}'.format(
                statement, ', '.join(correct_var))
        return correct_var

    def __len__(self):
        return len(self._values)

    def __getitem__(self, key):
        return self._values[key]

    def __setitem__(self, key, value):
        self._values[key] = value

    def __delitem__(self, key):
        del self._values[key]
        del self._datetimes[key]

    def __iter__(self):
        return iter(self._values)

    def __reversed__(self):
        return reversed(self._values)

    def __contains__(self, item):
        return item in self._values

    def to_json(self):
        """Convert Data Collection to a dictionary."""
        return {
            'header': self.header.to_json(),
            'values': self._values,
            'datetimes': [dat.to_json() for dat in self._datetimes]
        }

    def ToString(self):
        """Overwrite .NET ToString method."""
        return self.__repr__()

    def __repr__(self):
        """Discontinuous Collection representation."""
        return "Discontinuous Data Collection\n{} ({})\n...{} values...".format(
            self.header.data_type, self.header.unit, len(self._values))


class HourlyDiscontinuousCollection(DiscontinuousCollection):
    """Discontinous Data Collection at hourly or sub-hourly intervals."""

    def __init__(self, header, values, datetimes):
        """Init class."""
        assert isinstance(header, Header), \
            'header must be a Ladybug Header object. Got {}'.format(type(header))
        assert isinstance(header.analysis_period, AnalysisPeriod), \
            'header of {} must have an analysis_period.'.format(self.__class__.__name__)
        assert isinstance(datetimes, list), \
            'datetimes must be a list. Got {}'.format(type(datetimes))

        self._header = header
        self._datetimes = datetimes
        self.values = values

    @property
    def timestep_text(self):
        """Return a text string representing the timestep of the collection."""
        if self.header.analysis_period.timestep == 1:
            return 'Hourly'
        else:
            return '{} Minute'.format(60 / self.header.analysis_period.timestep)

    def duplicate(self):
        """Return a copy of the current Data Collection."""
        return HourlyDiscontinuousCollection(
            self.header.duplicate(), deepcopy(self.values), self.datetimes)

    def filter_by_analysis_period(self, analysis_period):
        """
        Filter a Data Collection based on an analysis period.

        Args:
           analysis period: A Ladybug analysis period

        Return:
            A new Data Collection with filtered data
        """
        self._check_analysis_period_timestep(analysis_period)
        _filtered_data = self.filter_by_hoys(analysis_period.hoys)
        _filtered_data.header._analysis_period = analysis_period
        return _filtered_data

    def filter_by_moys(self, moys):
        """Filter the list based on a list of minutes of the year.

        Args:
           moys: A List of minutes of the year [0..8759 * 60]

        Return:
            A new Data Collection with filtered data
        """
        _filt_values = []
        _filt_datetimes = []
        for i, d in enumerate(self.datetimes):
            if d.moy in moys:
                _filt_datetimes.append(d)
                _filt_values.append(self.values[i])
        _filt_header = self.header.duplicate()
        return HourlyDiscontinuousCollection(_filt_header, _filt_values, _filt_datetimes)

    def filter_by_hoys(self, hoys):
        """Filter the Data Collection based on an analysis period.

        Args:
           hoys: A List of hours of the year 0..8759

        Return:
            A new Data Collection with filtered data
        """
        _moys = tuple(int(hour * 60) for hour in hoys)
        return self.filter_by_moys(_moys)

    def _check_analysis_period_timestep(self, analysis_period):
        assert self.header.analysis_period.timestep == analysis_period.timestep, \
            'analysis_period timestep must match that on the'\
            'Collection header. {} != {}'.format(
                analysis_period.timestep, self.header.analysis_period.timestep)

    def __repr__(self):
        """Hourly Discontinuous Collection representation."""
        return "{} Discontinuous Data Collection\n{}\n{} ({})\n...{} values...".format(
            self.timestep_text, self.header.analysis_period,
            self.header.data_type, self.header.unit, len(self._values))


class HourlyContinuousCollection(HourlyDiscontinuousCollection):
    """Class for Continouus Data Collections at hourly or sub-hourly intervals."""

    def __init__(self, header, values):
        """Init class."""
        assert isinstance(header, Header), \
            'header must be a Ladybug Header object. Got {}'.format(type(header))
        assert isinstance(header.analysis_period, AnalysisPeriod), \
            'header of {} must have an analysis_period.'.format(self.__class__.__name__)
        assert header.analysis_period.st_hour == 0, \
            'analysis_period start hour of {} must be 0. Got {}'.format(
                self.__class__.__name__, header.analysis_period.st_hour)
        assert header.analysis_period.end_hour == 23, \
            'analysis_period end hour of {} must be 23. Got {}'.format(
                self.__class__.__name__, header.analysis_period.end_hour)

        self._header = header
        self.values = values
        self._datetimes = None

    @classmethod
    def from_json(cls, data):
        """Create a Data Collection from a dictionary.

        Args:
            {
                "header": A Ladybug Header,
                "values": An array of values,
            }
        """
        assert 'header' in data, 'Required keyword "header" is missing!'
        assert 'values' in data, 'Required keyword "values" is missing!'
        return cls(Header.from_json(data['header']),
                   data['values'])

    @property
    def values(self):
        """Return the list of numerical values."""
        return self._values

    @values.setter
    def values(self, values):
        assert isinstance(values, list), \
            'values must be a list. Got {}'.format(type(values))
        if self.header.analysis_period.is_annual:
            a_period_len = 8760 * self.header.analysis_period.timestep
            if self.header.analysis_period.is_leap_year is True:
                a_period_len = a_period_len + 24 * self.header.analysis_period.timestep
        else:
            a_period_len = len(self.header.analysis_period.moys)
        assert len(values) == a_period_len, \
            'Length of values does not match that expected by the '\
            'header analysis_period. {} != {}'.format(
                len(values), a_period_len)
        self._values = values

    @property
    def datetimes(self):
        """Return datetimes for this collection as a tuple."""
        if self._datetimes is None:
            self._datetimes = self.header.analysis_period.datetimes
        return tuple(self._datetimes)

    def interpolate_data(self, timestep, cumulative=None):
        """Interpolate data for a finer timestep using a linear interpolation.

        Args:
            timestep: Target timestep as an integer. Target timestep must be
                divisable by current timestep.
            cumulative: A boolean that sets whether the interpolation
                should treat the data colection values as cumulative, in
                which case the value at each timestep is the value over
                that timestep (instead of over the hour). The default will
                check the DataType to see if this type of data is typically
                cumulative over time.

        Return:
            A continuous hourly data collection with data interpolated to
                the input timestep.
        """
        assert timestep % self.header.analysis_period.timestep == 0, \
            'Target timestep({}) must be divisable by current timestep({})' \
            .format(timestep, self.header.analysis_period.timestep)
        if cumulative is not None:
            assert isinstance(cumulative, bool), \
                'Expected Boolean. Got {}'.format(type(cumulative))

        # generate new data
        _new_values = []
        _data_length = len(self._values)
        for d in xrange(_data_length):
            for _v in self._xxrange(self[d], self[(d + 1) % _data_length], timestep):
                _new_values.append(_v)

        # divide cumulative values by the timestep
        native_cumulative = self.header.data_type.cumulative
        if cumulative is True or (cumulative is None and native_cumulative):
            for i, d in enumerate(_new_values):
                _new_values[i] = d / timestep

        # shift data by a half-hour if data is averaged or cumulative over an hour
        if self.header.data_type.point_in_time is False:
            shift_dist = int(timestep / 2)
            _new_values = _new_values[-shift_dist:] + _new_values[:-shift_dist]

        # build a new header
        _new_header = self.header.duplicate()
        _new_header._analysis_period._timestep = timestep
        return HourlyContinuousCollection(_new_header, _new_values)

    def filter_by_analysis_period(self, analysis_period):
        """
        Filter a Data Collection based on an analysis period.

        Args:
           analysis period: A Ladybug analysis period

        Return:
            A new Data Collection with filtered data
        """
        self._check_analysis_period_timestep(analysis_period)
        if not self.header.analysis_period.is_annual:
            self._check_analysis_period_range(analysis_period)
        if analysis_period.st_hour == 0 and analysis_period.end_hour == 23:
            # We can still return an Hourly Continuous Data Collection
            t_s = 60 / analysis_period.timestep
            st_ind = int((analysis_period.st_time.moy / t_s) -
                         (self.header.analysis_period.st_time.moy / t_s))
            end_ind = int((analysis_period.end_time.moy / t_s) -
                          (analysis_period.st_time.moy / t_s) + st_ind + 1)
            if end_ind > st_ind:
                _filt_values = self.values[st_ind:end_ind]
            else:
                _filt_values = self.values[st_ind:] + self.values[:end_ind]
            _filt_header = self.header.duplicate()
            _filt_header._analysis_period = analysis_period
            return HourlyContinuousCollection(_filt_header, _filt_values)
        else:
            # We have to filter using  HOYs and the result cannot be continuous
            _filtered_data = self.filter_by_hoys(analysis_period.hoys)
            _filtered_data.header._analysis_period = analysis_period
            return _filtered_data

    def filter_by_moys(self, moys):
        """Filter the list based on a list of minutes of the year.

        Args:
           moys: A List of minutes of the year [0..8759 * 60]

        Return:
            A new Data Collection with filtered data
        """
        t_s = 60 / self.header.analysis_period.timestep
        st_ind = self.header.analysis_period.st_time.moy / t_s
        if self.header.analysis_period.is_reversed is False:
            _filt_indices = [int(moy / t_s - st_ind) for moy in moys]
        else:
            if self.header.analysis_period.is_leap_year is False:
                eoy_ind = 8759 * self.header.analysis_period.timestep - st_ind
            else:
                eoy_ind = 8783 * self.header.analysis_period.timestep - st_ind
            _filt_indices = []
            for moy in moys:
                ind = moy / t_s
                if ind > st_ind:
                    _filt_indices.append(int(ind - st_ind))
                else:
                    _filt_indices.append(int(ind + eoy_ind))

        _filt_values = [self.values[i] for i in _filt_indices]
        _filt_datetimes = [self.datetimes[i] for i in _filt_indices]
        _filt_header = self.header.duplicate()
        return HourlyDiscontinuousCollection(_filt_header, _filt_values, _filt_datetimes)

    def duplicate(self):
        """Return a copy of the current Data Collection."""
        return HourlyContinuousCollection(
            self.header.duplicate(), deepcopy(self.values))

    def is_collection_aligned(self, data_collection):
        """Check if this Data Collection is aligned with another.

        Aligned Data Collections are of the same type, the same number of values
        and have matching datetimes.

        Args:
            data_collection: The Data Collection which you want to test if this
                collection is aligned with.

        Return:
            True if collections are aligned, Fale if not aligned
        """
        if type(self) != type(data_collection):
            return False
        elif len(self.values) != len(data_collection.values):
            return False
        else:
            ap1 = self.header.analysis_period
            ap2 = data_collection.header.analysis_period
            if (ap1.st_time, ap1.end_time) != (ap2.st_time, ap2.end_time):
                return False
        return True

    def to_discontinuous(self):
        """Return a Discontinuous version of the current Collection."""

    def to_json(self):
        """Convert Data Collection to a dictionary."""
        return {
            'header': self.header.to_json(),
            'values': self._values
        }

    def _xxrange(self, start, end, step_count):
        """Generate n values between start and end."""
        _step = (end - start) / float(step_count)
        return (start + (i * _step) for i in xrange(int(step_count)))

    def _check_analysis_period_range(self, analysis_period):
        """Checkthat the analysis_period is a subset of the Data Collection's"""
        error_msg = 'analysis_period is not a subset of Data Collection.'
        assert analysis_period.st_hour >= self.header.analysis_period.st_hour, \
            '{} st_hour is too early.'.format(error_msg)
        assert analysis_period.end_hour <= self.header.analysis_period.end_hour, \
            '{} end_hour is too late.'.format(error_msg)
        assert analysis_period.st_time.doy >= \
            self.header.analysis_period.st_time.doy, \
            '{} Start date is too early'.format(error_msg)
        assert analysis_period.end_time.doy <= \
            self.header.analysis_period.end_time.doy, \
            '{} End date is too late'.format(error_msg)

    def __delitem__(self, key):
        raise TypeError('Convert this Collection to Discontinuous to use del().')

    def __repr__(self):
        """Hourly Discontinuous Collection representation."""
        return "{} Continuous Data Collection\n{}\n{} ({})\n...{} values...".format(
            self.timestep_text, self.header.analysis_period,
            self.header.data_type, self.header.unit, len(self._values))


"""Methods to be overwritten:
    __init__ (No need for datetimes but header requires an AnalysisPeriod)
    datetimes (check if they exist and, if not, generate them from AnalysisPeriod)
    from_json (no need for datetimes as we have the AnalysisPeriod)
    to_json (no need for datetimes as we have the AnalysisPeriod)
    values.setter (check to be sure that lenth of values aligns with AnalysisPeriod)
    duplicate
    __delitem__ (can't delete an item without making the collection discontinouous)
    is_collection_aligned (only need to check the analysisperiod and not all datetimes)
    filter_by_analysis_period
    filter_by_moys
"""

"""Methods to add:
    interpolate_data
    group_by_day
    group_by_month
    average_daily
    average_monthly
    average_monthly_for_each_hour
    total_daily
    total_monthly
    total_monthly_for_each_hour
"""
