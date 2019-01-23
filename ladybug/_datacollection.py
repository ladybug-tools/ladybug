# coding=utf-8
"""Ladybug Data Collections.

Collections have the following inheritence structure:
                         Base
       ___________________|__________________
      |             |           |            |

    Hourly        Daily     Monthly     MonthlyPerHour
Discontinuous
      |

    Hourly
  Continuous


All Data Collections have the ability to:
    * max, min, bounds, average, median, total, get_percentile, get_highest/lowest values
    * filter based on conditional statements
    * perform unit conversions on the data: to_unit, to_ip, to_si

All collections except for the Base have the ability to:
    * filter based on analysis period

The Hourly Continuous Collection should be used for all annual hourly data
since it possesses the features of the other classes but includes
faster versions of certain methods as well as an interpolate_data() method.

If one is applying multiple operations to a Continuous Data Collection, it is
recommended that one filter based on analysis period first since these methods
are faster when the collection is continuous.
"""
from __future__ import division

from .header import Header
from .dt import DateTime
from .analysisperiod import AnalysisPeriod

from string import ascii_lowercase
from collections import OrderedDict
import math
try:
    from itertools import izip as zip  # python 2
except ImportError:
    xrange = range  # python 3


class BaseCollection(object):
    """Base class for all Data Collections."""

    __slots__ = ('_header', '_values', '_datetimes')

    def __init__(self, header, values, datetimes):
        """Initialize base collection.

        Args:
            header: A Ladybug Header object.
            values: A list of values.
            datetimes: A list of Ladybug DateTime objects that aligns with
                the list of values.
        """
        assert isinstance(header, Header), \
            'header must be a Ladybug Header object. Got {}'.format(type(header))
        assert isinstance(datetimes, (list, tuple)), \
            'datetimes must be a list or tuple. Got {}'.format(type(datetimes))
        if isinstance(datetimes, tuple):
            datetimes = list(datetimes)

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
        """Return the Data Collection's list of numerical values."""
        return tuple(self._values)

    @values.setter
    def values(self, values):
        assert isinstance(values, (list, tuple)), \
            'values must be a list or tuple. Got {}'.format(type(values))
        if isinstance(values, tuple):
            values = list(values)
        assert len(values) == len(self.datetimes), \
            'Length of values list must match length of datetimes list. {} != {}'.format(
                len(values), len(self.datetimes))
        self._values = values

    @property
    def bounds(self):
        """Return a tuple as (min, max)."""
        return (min(self._values), max(self._values))

    @property
    def min(self):
        """Return the min of the Data Collection values."""
        return min(self._values)

    @property
    def max(self):
        """Return the max of the Data Collection values."""
        return max(self._values)

    @property
    def average(self):
        """Return the average of the Data Collection values."""
        return sum(self._values) / len(self._values)

    @property
    def median(self):
        """Return the median of the Data Collection values."""
        return self._percentile(self._values, 50)

    @property
    def total(self):
        """Return the total of the Data Collection values."""
        return sum(self._values)

    def duplicate(self):
        """Return a copy of the current Data Collection."""
        return self.__class__(
            self.header.duplicate(), self.values, self.datetimes)

    def get_aligned_collection(self, value=0, data_type=None, unit=None):
        """Return a Collection aligned with this one that is composed of a single repeated value.

        Args:
            value: The value to be repeated in the aliged collection values.
                Default: 0.
            data_type: The data type of the aligned collection. Default is to
                use the data type of this collection.
            unit: The unit of the aligned collection. Default is to
                use the unit of this collection.
        """
        data_type = data_type or self.header.data_type
        unit = unit or self.header.unit
        values = [value] * len(self._values)
        header = Header(data_type, unit, self.header.analysis_period,
                        self.header.metadata)
        return self.__class__(header, values, self.datetimes)

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

    def get_percentile(self, percentile):
        """Filter the Data Collection based on a conditional statement.

        Args:
            percentile: A float value from 0 to 100 representing the
                requested percentile.

        Return:
            The Data Collection value at the input percentile
        """
        return self._percentile(self._values, percentile)

    def filter_by_conditional_statement(self, statement):
        """Filter the Data Collection based on a conditional statement.

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
        for i, d in enumerate(self._values):
            if eval(statement, globals={'d': d}):
                _filt_values.append(d)
                _filt_datetimes.append(self.datetimes[i])

        # create a new Data Collection
        _filt_header = self.header.duplicate()
        if self.__class__.__name__ == 'HourlyContinuousCollection':
            return HourlyDiscontinuousCollection(
                _filt_header, _filt_values, _filt_datetimes)
        else:
            return self.__class__(_filt_header, _filt_values, _filt_datetimes)

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
        _filt_values = [d for i, d in enumerate(self._values) if pattern[i % _len]]
        _filt_datetimes = [d for i, d in enumerate(self.datetimes) if pattern[i % _len]]
        _filt_header = self.header.duplicate()
        if self.__class__.__name__ == 'HourlyContinuousCollection':
            return HourlyDiscontinuousCollection(
                _filt_header, _filt_values, _filt_datetimes)
        else:
            return self.__class__(_filt_header, _filt_values, _filt_datetimes)

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
        pattern = BaseCollection.pattern_from_collections_and_statement(
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
        BaseCollection.are_collections_aligned(data_collections)
        correct_var = BaseCollection._check_conditional_statement(
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
        correct_var = list(ascii_lowercase)[:num_collections]

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

    def _is_in_data_type_range(self, raise_exception=True):
        """Check if the Data Collection values are in permissable ranges for the data_type.

        If this method returns False, the Data Collection's data is
        physically or mathematically impossible for the data_type."""
        return self._header.data_type.is_in_range(
            self._values, self._header.unit, raise_exception)

    def _is_in_epw_range(self, raise_exception=True):
        """Check if Data Collection values are in permissable ranges for EPW files."""
        return self._header.data_type.is_in_range_epw(
            self._values, self._header.unit, raise_exception)

    def _percentile(self, values, percent, key=lambda x: x):
        """Find the percentile of a list of values.

        Args:
            values: A list of values for which percentiles are desired
            percent: A float value from 0 to 100 representing the requested percentile.
            key: optional key function to compute value from each element of N.

        Return:
            The percentile of the values
        """
        vals = sorted(values)
        k = (len(vals) - 1) * (percent / 100)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return key(vals[int(k)])
        d0 = key(vals[int(f)]) * (c-k)
        d1 = key(vals[int(c)]) * (k-f)
        return d0+d1

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
            'datetimes': [dat.to_json() for dat in self.datetimes]
        }

    def ToString(self):
        """Overwrite .NET ToString method."""
        return self.__repr__()

    def __repr__(self):
        """Discontinuous Collection representation."""
        return "Discontinuous Data Collection\n{} ({})\n...{} values...".format(
            self.header.data_type, self.header.unit, len(self._values))


class HourlyDiscontinuousCollection(BaseCollection):
    """Discontinous Data Collection at hourly or sub-hourly intervals."""

    def __init__(self, header, values, datetimes):
        """Initialize hourly discontinuous collection.

        Args:
            header: A Ladybug Header object.  Note that this header
                must have an AnalysisPeriod on it.
            values: A list of values.
            datetimes: A list of Ladybug DateTime objects that aligns with
                the list of values.
        """
        assert isinstance(header, Header), \
            'header must be a Ladybug Header object. Got {}'.format(type(header))
        assert isinstance(header.analysis_period, AnalysisPeriod), \
            'header of {} must have an analysis_period.'.format(self.__class__.__name__)
        assert isinstance(datetimes, (list, tuple)), \
            'datetimes must be a list or tuple. Got {}'.format(type(datetimes))
        if isinstance(datetimes, tuple):
            datetimes = list(datetimes)

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

    def filter_by_analysis_period(self, analysis_period):
        """
        Filter a Data Collection based on an analysis period.

        Args:
           analysis period: A Ladybug analysis period

        Return:
            A new Data Collection with filtered data
        """
        self._check_analysis_period(analysis_period)
        _filtered_data = self.filter_by_moys(analysis_period.moys)
        _filtered_data.header._analysis_period = analysis_period
        return _filtered_data

    def filter_by_hoys(self, hoys):
        """Filter the Data Collection based on an analysis period.

        Args:
           hoys: A List of hours of the year 0..8759

        Return:
            A new Data Collection with filtered data
        """
        _moys = tuple(int(hour * 60) for hour in hoys)
        return self.filter_by_moys(_moys)

    def filter_by_moys(self, moys):
        """Filter the Data Collection based on a list of minutes of the year.

        Args:
           moys: A List of minutes of the year [0..8759 * 60]

        Return:
            A new Data Collection with filtered data
        """
        _filt_values, _filt_datetimes = self._filter_by_moys_slow(moys)
        return HourlyDiscontinuousCollection(
            self.header.duplicate(), _filt_values, _filt_datetimes)

    def group_by_day(self):
        """Return a dictionary of this collection's values grouped by each day of year.

        Key values are between 1-365.
        """
        data_by_day = OrderedDict()
        for d in xrange(1, 366):
            data_by_day[d] = []
        for v, dt in zip(self._values, self.datetimes):
            data_by_day[dt.doy].append(v)
        return data_by_day

    def average_daily(self):
        """Return a daily collection of values averaged for each day."""
        data_dict = self.group_by_day()
        avg_data, d_times = [], []
        for i in self.header.analysis_period.doys_int:
            vals = data_dict[i]
            if vals != []:
                avg_data.append(sum(vals)/len(vals))
                d_times.append(i)
        new_header = self.header.duplicate()
        new_header.metadata['statistical operation'] = 'Average'
        return DailyCollection(new_header, avg_data, d_times)

    def total_daily(self):
        """Return a daily collection of values totaled over each day."""
        data_dict = self.group_by_day()
        total_data, d_times = [], []
        for i in self.header.analysis_period.doys_int:
            vals = data_dict[i]
            if vals != []:
                total_data.append(sum(vals))
                d_times.append(i)
        new_header = self.header.duplicate()
        new_header.metadata['statistical operation'] = 'Total'
        return DailyCollection(new_header, total_data, d_times)

    def percentile_daily(self, percentile):
        """Return a daily collection of values at the input percentile of each day.

        Args:
            percentile: A float value from 0 to 100 representing the
                requested percentile.
        """
        data_dict = self.group_by_day()
        per_data, d_times = [], []
        for i in self.header.analysis_period.doys_int:
            vals = data_dict[i]
            if vals != []:
                per_data.append(self._percentile(vals, percentile))
                d_times.append(i)
        new_header = self.header.duplicate()
        new_header.metadata['statistical operation'] = '{} Percentile'.format(percentile)
        return DailyCollection(new_header, per_data, d_times)

    def group_by_month(self):
        """Return a dictionary of this collection's values grouped by each month.

        Key values are between 1-12.
        """
        data_by_month = OrderedDict()
        for d in xrange(1, 13):
            data_by_month[d] = []
        for v, dt in zip(self._values, self.datetimes):
            data_by_month[dt.month].append(v)
        return data_by_month

    def average_monthly(self):
        """Return a monthly collection of values averaged for each month."""
        data_dict = self.group_by_month()
        avg_data, d_times = [], []
        for i in self.header.analysis_period.months_int:
            vals = data_dict[i]
            if vals != []:
                avg_data.append(sum(vals)/len(vals))
                d_times.append(i)
        new_header = self.header.duplicate()
        new_header.metadata['statistical operation'] = 'Average'
        return MonthlyCollection(new_header, avg_data, d_times)

    def total_monthly(self):
        """Return a monthly collection of values totaled over each month."""
        data_dict = self.group_by_month()
        total_data, d_times = [], []
        for i in self.header.analysis_period.months_int:
            vals = data_dict[i]
            if vals != []:
                total_data.append(sum(vals))
                d_times.append(i)
        new_header = self.header.duplicate()
        new_header.metadata['statistical operation'] = 'Total'
        return MonthlyCollection(new_header, total_data, d_times)

    def percentile_monthly(self, percentile):
        """Return a monthly collection of values at the input percentile of each month.

        Args:
            percentile: A float value from 0 to 100 representing the
                requested percentile.
        """
        data_dict = self.group_by_month()
        per_data, d_times = [], []
        for i in self.header.analysis_period.months_int:
            vals = data_dict[i]
            if vals != []:
                per_data.append(self._percentile(vals, percentile))
                d_times.append(i)
        new_header = self.header.duplicate()
        new_header.metadata['statistical operation'] = '{} Percentile'.format(percentile)
        return MonthlyCollection(new_header, per_data, d_times)

    def group_by_month_per_hour(self):
        """Return a dictionary of this collection's values grouped by each month per hour.

        Key values are tuples of 2 integers:
        The first represents the month of the year between 1-12.
        The first represents the hour of the day between 0-24.
        (eg. (12, 23) for December at 11 PM)
        """
        data_by_month_per_hour = OrderedDict()
        for m in xrange(1, 13):
            for h in xrange(0, 24):
                data_by_month_per_hour[(m, h)] = []
        for v, dt in zip(self.values, self.datetimes):
            data_by_month_per_hour[(dt.month, dt.hour)].append(v)
        return data_by_month_per_hour

    def average_monthly_per_hour(self):
        """Return a monthly per hour data collection of average values."""
        data_dict = self.group_by_month_per_hour()
        avg_data, d_times = [], []
        for i in self.header.analysis_period.months_per_hour:
            vals = data_dict[i]
            if vals != []:
                avg_data.append(sum(vals)/len(vals))
                d_times.append(i)
        new_header = self.header.duplicate()
        new_header.metadata['statistical operation'] = 'Average'
        return MonthlyPerHourCollection(new_header, avg_data, d_times)

    def total_monthly_per_hour(self):
        """Return a monthly per hour collection of totaled values."""
        data_dict = self.group_by_month_per_hour()
        total_data, d_times = [], []
        for i in self.header.analysis_period.months_per_hour:
            vals = data_dict[i]
            if vals != []:
                total_data.append(sum(vals))
                d_times.append(i)
        new_header = self.header.duplicate()
        new_header.metadata['statistical operation'] = 'Total'
        return MonthlyPerHourCollection(new_header, total_data, d_times)

    def percentile_monthly_per_hour(self, percentile):
        """Return a monthly per hour collection of values at the input percentile.

        Args:
            percentile: A float value from 0 to 100 representing the
                requested percentile.
        """
        data_dict = self.group_by_month_per_hour()
        total_data, d_times = [], []
        for i in self.header.analysis_period.months_per_hour:
            vals = data_dict[i]
            if vals != []:
                total_data.append(self._percentile(vals, percentile))
                d_times.append(i)
        new_header = self.header.duplicate()
        new_header.metadata['statistical operation'] = '{} Percentile'.format(percentile)
        return MonthlyPerHourCollection(new_header, total_data, d_times)

    def _filter_by_moys_slow(self, moys):
        """Filter the Data Collection with a slow method that always works."""
        _filt_values = []
        _filt_datetimes = []
        for i, d in enumerate(self.datetimes):
            if d.moy in moys:
                _filt_datetimes.append(d)
                _filt_values.append(self._values[i])
        return _filt_values, _filt_datetimes

    def _check_analysis_period(self, analysis_period):
        assert self.header.analysis_period.timestep == analysis_period.timestep,\
            'analysis_period timestep must match that on the'\
            'Collection header. {} != {}'.format(
                analysis_period.timestep, self.header.analysis_period.timestep)
        assert self.header.analysis_period.is_leap_year is analysis_period.is_leap_year,\
            'analysis_period is_leap_year must match that on the'\
            'Collection header. {} != {}'.format(
                analysis_period.is_leap_year, self.header.analysis_period.is_leap_year)

    def __repr__(self):
        """Hourly Discontinuous Collection representation."""
        return "{} Discontinuous Data Collection\n{}\n{} ({})\n...{} values...".format(
            self.timestep_text, self.header.analysis_period,
            self.header.data_type, self.header.unit, len(self._values))


class HourlyContinuousCollection(HourlyDiscontinuousCollection):
    """Class for Continouus Data Collections at hourly or sub-hourly intervals."""

    def __init__(self, header, values):
        """Initialize hourly discontinuous collection.

        Args:
            header: A Ladybug Header object.  Note that this header
                must have an AnalysisPeriod on it that aligns with the
                list of values.
            values: A list of values.  Note that the length of this list
                must align with the AnalysisPeriod on the header.
        """
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
        return cls(Header.from_json(data['header']), data['values'])

    @property
    def values(self):
        """Return the Data Collection's list of numerical values."""
        return tuple(self._values)

    @values.setter
    def values(self, values):
        assert isinstance(values, (list, tuple)), \
            'values must be a list or a tuple. Got {}'.format(type(values))
        if isinstance(values, tuple):
            values = list(values)
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
        return self.__class__(_new_header, _new_values)

    def filter_by_analysis_period(self, analysis_period):
        """Filter the Data Collection based on an analysis period.

        Args:
           analysis period: A Ladybug analysis period

        Return:
            A new Data Collection with filtered data
        """
        self._check_analysis_period(analysis_period)
        analysis_period = self._get_analysis_period_subset(analysis_period)

        if analysis_period.st_hour == 0 and analysis_period.end_hour == 23:
            # We can still return an Hourly Continuous Data Collection
            t_s = 60 / analysis_period.timestep
            st_ind = int((analysis_period.st_time.moy / t_s) -
                         (self.header.analysis_period.st_time.moy / t_s))
            end_ind = int((analysis_period.end_time.moy / t_s) -
                          (analysis_period.st_time.moy / t_s) + st_ind + 1)
            if end_ind > st_ind:
                _filt_values = self._values[st_ind:end_ind]
            else:
                _filt_values = self._values[st_ind:] + self._values[:end_ind]
            _filt_header = self.header.duplicate()
            _filt_header._analysis_period = analysis_period
            return HourlyContinuousCollection(_filt_header, _filt_values)
        else:
            # Filter using  HOYs and the result cannot be continuous
            _filtered_data = self.filter_by_moys(analysis_period.moys)
            _filtered_data.header._analysis_period = analysis_period
            return _filtered_data

    def filter_by_moys(self, moys):
        """Filter the Data Collection based on a list of minutes of the year.

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

        _filt_values = [self._values[i] for i in _filt_indices]
        _filt_datetimes = [self.datetimes[i] for i in _filt_indices]
        _filt_header = self.header.duplicate()
        return HourlyDiscontinuousCollection(_filt_header, _filt_values, _filt_datetimes)

    def group_by_day(self):
        """Return a dictionary of this collection's values grouped by each day of year.

        Key values are between 1-365.
        """
        hourly_data_by_day = OrderedDict()
        for d in xrange(1, 366):
            hourly_data_by_day[d] = []
        a_per = self.header.analysis_period
        indx_per_day = 24 * a_per.timestep
        start_doy = sum(a_per._num_of_days_each_month[:a_per.st_time.month-1]) \
            + a_per.st_time.day
        if not a_per.is_reversed:
            for i in range(0, len(self._values), indx_per_day):
                hourly_data_by_day[start_doy] = self._values[i:i + indx_per_day]
                start_doy += 1
        else:
            end_ind = 24 * a_per.timestep * (365 - start_doy)
            for i in range(0, end_ind + 1, indx_per_day):
                hourly_data_by_day[start_doy] = self._values[i:i + indx_per_day]
                start_doy += 1
            start_doy = 1
            for i in range(end_ind, len(self._values), indx_per_day):
                hourly_data_by_day[start_doy] = self._values[i:i + indx_per_day]
                start_doy += 1
        return hourly_data_by_day

    def group_by_month(self):
        """Return a dictionary of this collection's values grouped by each month.

        Key values are between 1-12.
        """
        hourly_data_by_month = OrderedDict()
        for d in xrange(1, 13):
            hourly_data_by_month[d] = []

        a_per = self.header.analysis_period
        a_per_months = a_per.months_int
        indx = 24 * a_per.timestep * abs(
            a_per.st_day - 1 - a_per._num_of_days_each_month[a_per_months[0]-1])
        hourly_data_by_month[a_per_months[0]] = self._values[0:indx + 1]

        if len(a_per_months) > 1:
            for mon in a_per_months[1:]:
                interval = a_per._num_of_days_each_month[mon - 1] * 24 * a_per.timestep
                try:
                    hourly_data_by_month[mon] = self._values[indx:indx + interval + 1]
                except IndexError:
                    hourly_data_by_month[mon] = self._values[indx:]  # last items
                indx += interval
        return hourly_data_by_month

    def duplicate(self):
        """Return a copy of the current Data Collection."""
        return HourlyContinuousCollection(
            self.header.duplicate(), self._values)

    def get_aligned_collection(self, value=0, data_type=None, unit=None):
        """Return a Collection aligned with this one that is composed of a single repeated value.

        Args:
            value: The value to be repeated in the aliged collection values.
                Default: 0.
            data_type: The data type of the aligned collection. Default is to
                use the data type of this collection.
            unit: The unit of the aligned collection. Default is to
                use the unit of this collection.
        """
        data_type = data_type or self.header.data_type
        unit = unit or self.header.unit
        values = [value] * len(self._values)
        header = Header(data_type, unit, self.header.analysis_period,
                        self.header.metadata)
        return self.__class__(header, values)

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
        elif self.header.analysis_period != data_collection.header.analysis_period:
                return False
        return True

    def to_discontinuous(self):
        """Return a discontinuous version of the current collection."""
        return HourlyDiscontinuousCollection(self.header.duplicate(),
                                             self.values, self.datetimes)

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

    def _get_analysis_period_subset(self, a_per):
        """Return an analysis_period is always a subset of the Data Collection"""
        if self.header.analysis_period.is_annual:
            return a_per

        new_needed = False
        n_ap = [a_per.st_month, a_per.st_day, a_per.st_hour,
                a_per.end_month, a_per.end_day, a_per.end_hour,
                a_per.timestep, a_per.is_leap_year]
        if a_per.st_hour < self.header.analysis_period.st_hour:
            n_ap[2] = self.header.analysis_period.st_hour
            new_needed = True
        elif a_per.end_hour > self.header.analysis_period.end_hour:
            n_ap[5] = self.header.analysis_period.end_hour
            new_needed = True
        elif a_per.st_time.doy < self.header.analysis_period.st_time.doy:
            n_ap[0] = self.header.analysis_period.st_month
            n_ap[1] = self.header.analysis_period.st_day
            new_needed = True
        elif a_per.end_time.doy > self.header.analysis_period.end_time.doy:
            n_ap[3] = self.header.analysis_period.end_month
            n_ap[4] = self.header.analysis_period.end_day
            new_needed = True
        if new_needed is False:
            return a_per
        else:
            return AnalysisPeriod(n_ap[0], n_ap[1], n_ap[2], n_ap[3],
                                  n_ap[4], n_ap[5], n_ap[6], n_ap[7])

    def __delitem__(self, key):
        raise TypeError('Convert this Collection to Discontinuous to use del().')

    def __repr__(self):
        """Hourly Discontinuous Collection representation."""
        return "{} Continuous Data Collection\n{}\n{} ({})\n...{} values...".format(
            self.timestep_text, self.header.analysis_period,
            self.header.data_type, self.header.unit, len(self._values))


class MonthlyCollection(BaseCollection):
    """Class for Monthly Data Collections."""

    def __init__(self, header, values, datetimes):
        """Initialize monthly collection.

        Args:
            header: A Ladybug Header object.  Note that this header
                must have an AnalysisPeriod on it.
            values: A list of values.
            datetimes: A list of integers that aligns with the list of values.
                Each integer in the list is 1-12 and denotes the month of the
                year for each value of the collection.
        """
        assert isinstance(header, Header), \
            'header must be a Ladybug Header object. Got {}'.format(type(header))
        assert isinstance(header.analysis_period, AnalysisPeriod), \
            'header of {} must have an analysis_period.'.format(self.__class__.__name__)
        assert isinstance(datetimes, (list, tuple)), \
            'datetimes must be a list or a tuple. Got {}'.format(type(datetimes))
        if isinstance(datetimes, tuple):
            datetimes = list(datetimes)

        self._header = header
        self._datetimes = datetimes
        self.values = values

    def filter_by_analysis_period(self, analysis_period):
        """Filter the Data Collection based on an analysis period.

        Args:
           analysis period: A Ladybug analysis period

        Return:
            A new Data Collection with filtered data
        """
        _filtered_data = self.filter_by_months(analysis_period.months_int)
        _filtered_data.header._analysis_period = analysis_period
        return _filtered_data

    def filter_by_months(self, months):
        """Filter the Data Collection based on a list of months of the year (as integers).

        Args:
           months: A List of months of the year [1..12]

        Return:
            A new Data Collection with filtered data
        """
        _filt_values = []
        _filt_datetimes = []
        for i, d in enumerate(self.datetimes):
            if d in months:
                _filt_datetimes.append(d)
                _filt_values.append(self._values[i])
        _filt_header = self.header.duplicate()
        return MonthlyCollection(_filt_header, _filt_values, _filt_datetimes)

    def __repr__(self):
        """Monthly Collection representation."""
        a_per = self.header.analysis_period
        return "Monthly Collection\n{} to {}\n{} ({})\n...{} values...".format(
            a_per.MONTHNAMES[a_per.st_month], a_per.MONTHNAMES[a_per.end_month],
            self.header.data_type, self.header.unit, len(self._values))


class DailyCollection(BaseCollection):
    """Class for Daily Data Collections."""

    def __init__(self, header, values, datetimes):
        """Initialize daily collection.

        Args:
            header: A Ladybug Header object.  Note that this header
                must have an AnalysisPeriod on it.
            values: A list of values.
            datetimes: A list of integers that aligns with the list of values.
                Each integer in the list is 1-365 and denotes the day of the
                year for each value of the collection.
        """
        assert isinstance(header, Header), \
            'header must be a Ladybug Header object. Got {}'.format(type(header))
        assert isinstance(header.analysis_period, AnalysisPeriod), \
            'header of {} must have an analysis_period.'.format(self.__class__.__name__)
        assert isinstance(datetimes, (list, tuple)), \
            'datetimes must be a list or a tuple. Got {}'.format(type(datetimes))
        if isinstance(datetimes, tuple):
            datetimes = list(datetimes)

        self._header = header
        self._datetimes = datetimes
        self.values = values

    def filter_by_analysis_period(self, analysis_period):
        """Filter the Data Collection based on an analysis period.

        Args:
           analysis period: A Ladybug analysis period

        Return:
            A new Data Collection with filtered data
        """
        _filtered_data = self.filter_by_doys(analysis_period.doys_int)
        _filtered_data.header._analysis_period = analysis_period
        return _filtered_data

    def filter_by_doys(self, doys):
        """Filter the Data Collection based on a list of days of the year (as integers).

        Args:
           doys: A List of days of the year [1..365]

        Return:
            A new Data Collection with filtered data
        """
        _filt_values = []
        _filt_datetimes = []
        for i, d in enumerate(self.datetimes):
            if d in doys:
                _filt_datetimes.append(d)
                _filt_values.append(self._values[i])
        _filt_header = self.header.duplicate()
        return DailyCollection(_filt_header, _filt_values, _filt_datetimes)

    def __repr__(self):
        """Daily Collection representation."""
        a_per = self.header.analysis_period
        return "Daily Collection\n{}/{} to {}/{}\n{} ({})\n...{} values...".format(
            a_per.st_month, a_per.st_day, a_per.end_month, a_per.end_day,
            self.header.data_type, self.header.unit, len(self._values))


class MonthlyPerHourCollection(BaseCollection):
    """Class for Monthly Per Hour Collections."""

    def __init__(self, header, values, datetimes):
        """Initialize monthly per hour collection.

        Args:
            header: A Ladybug Header object.  Note that this header
                must have an AnalysisPeriod on it.
            values: A list of values.
            datetimes: A list of tuples that aligns with the list of values.
                Each tuple should possess two values: the first is the month
                and the second is the hour. (eg. (12, 23) = December at 11 PM)
        """
        assert isinstance(header, Header), \
            'header must be a Ladybug Header object. Got {}'.format(type(header))
        assert isinstance(header.analysis_period, AnalysisPeriod), \
            'header of {} must have an analysis_period.'.format(self.__class__.__name__)
        assert isinstance(datetimes, (list, tuple)), \
            'datetimes must be a list or a tuple. Got {}'.format(type(datetimes))
        if isinstance(datetimes, tuple):
            datetimes = list(datetimes)

        self._header = header
        self._datetimes = datetimes
        self.values = values

    def filter_by_analysis_period(self, analysis_period):
        """Filter the Data Collection based on an analysis period.

        Args:
           analysis period: A Ladybug analysis period

        Return:
            A new Data Collection with filtered data
        """
        _filtered_data = self.filter_by_months_per_hour(
            analysis_period.months_per_hour_str)
        _filtered_data.header._analysis_period = analysis_period
        return _filtered_data

    def filter_by_months_per_hour(self, months_per_hour):
        """Filter the Data Collection based on a list of months per hour (as strings).

        Args:
           months_per_hour: A list of tuples representing months per hour.
               Each tuple should possess two values: the first is the month
               and the second is the hour. (eg. (12, 23) = December at 11 PM)

        Return:
            A new Data Collection with filtered data
        """
        _filt_values = []
        _filt_datetimes = []
        for i, d in enumerate(self.datetimes):
            if d in months_per_hour:
                _filt_datetimes.append(d)
                _filt_values.append(self._values[i])
        return MonthlyPerHourCollection(
            self.header.duplicate(), _filt_values, _filt_datetimes)

    def __repr__(self):
        """Monthly Per Hour Collection representation."""
        return "Monthly Per Hour Collection\n{}@{} to {}@{}\n"\
            "{} ({})\n...{} values...".format(
                self.header.analysis_period.st_month,
                self.header.analysis_period.st_hour,
                self.header.analysis_period.end_month,
                self.header.analysis_period.end_hour,
                self.header.data_type, self.header.unit, len(self._values))
