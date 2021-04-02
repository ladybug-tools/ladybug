# coding=utf-8
"""Ladybug Data Collections.

Collections have the following inheritance structure:

.. code-block:: shell

                             Base
           ___________________|__________________
          |             |           |            |
        Hourly        Daily     Monthly     MonthlyPerHour
    Discontinuous
          |
        Hourly
      Continuous


All Data Collections in this module have the ability to:
    * max, min, bounds, average, median, total, percentile, highest/lowest values
    * perform unit conversions on the data: to_unit, to_ip, to_si
    * filter based on conditional statements
    * filter based on analysis period

The Hourly Continuous Collection should be used for all annual hourly data
since it possesses the features of the other classes but includes
faster versions of certain methods as well as an interpolate_data() method.

If one is applying multiple operations to a Continuous Data Collection, it is
recommended that one filter based on analysis period first since these methods
are faster when the collection is continuous.
"""
from __future__ import division

from ._datacollectionbase import BaseCollection
from .header import Header
from .analysisperiod import AnalysisPeriod
from .dt import DateTime

from collections import OrderedDict
try:
    from collections.abc import Iterable  # python < 3.7
except ImportError:
    from collections import Iterable  # python >= 3.8
try:
    from itertools import izip as zip  # python 2
except ImportError:
    xrange = range  # python 3


class HourlyDiscontinuousCollection(BaseCollection):
    """Discontinuous Data Collection at hourly or sub-hourly intervals.

    Args:
        header: A Ladybug Header object.  Note that this header
            must have an AnalysisPeriod on it.
        values: A list of values.
        datetimes: A list of Ladybug DateTime objects that aligns with
            the list of values.


    Properties:
        * average
        * bounds
        * datetimes
        * header
        * is_continuous
        * is_mutable
        * max
        * median
        * min
        * moys_dict
        * timestep_text
        * total
        * validated_a_period
        * values
    """

    _collection_type = 'HourlyDiscontinuous'

    def __init__(self, header, values, datetimes):
        """Initialize hourly discontinuous collection.
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
                "header": {}  # A Ladybug Header,
                "values": []  # An array of values,
                "datetimes": []  # An array of datetimes,
                "validated_a_period": True  # Boolean for whether header
                                            # analysis_period is valid
                }
        """
        assert 'header' in data, 'Required keyword "header" is missing!'
        assert 'values' in data, 'Required keyword "values" is missing!'
        assert 'datetimes' in data, 'Required keyword "datetimes" is missing!'
        collection = cls(Header.from_dict(data['header']), data['values'],
                         [DateTime.from_array(dat) for dat in data['datetimes']])
        if 'validated_a_period' in data:
            collection._validated_a_period = data['validated_a_period']
        return collection

    @property
    def timestep_text(self):
        """Return a text string representing the timestep of the collection."""
        if self.header.analysis_period.timestep == 1:
            return 'Hourly'
        else:
            return '{} Minute'.format(int(60 / self.header.analysis_period.timestep))

    @property
    def moys_dict(self):
        """Return a dictionary of this collection's values where the keys are the moys.

        This is useful for aligning the values with another list of datetimes.
        """
        moy_dict = {}
        for val, dt in zip(self.values, self.datetimes):
            moy_dict[dt.moy] = val
        return moy_dict

    def filter_by_analysis_period(self, analysis_period):
        """Filter a Data Collection based on an analysis period.

        Args:
           analysis period: A Ladybug analysis period.

        Return:
            A new Data Collection with filtered data.
        """
        self._check_analysis_period(analysis_period)
        _filtered_data = self.filter_by_moys(analysis_period.moys)
        _filtered_data.header._analysis_period = analysis_period
        return _filtered_data

    def filter_by_hoys(self, hoys):
        """Filter the Data Collection using a list of hours of the year (hoys).

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
        collection = HourlyDiscontinuousCollection(
            self.header.duplicate(), _filt_values, _filt_datetimes)
        collection._validated_a_period = self._validated_a_period
        return collection

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
        return self._time_interval_operation('daily', 'average')

    def total_daily(self):
        """Return a daily collection of values totaled over each day."""
        return self._time_interval_operation('daily', 'total')

    def percentile_daily(self, percentile):
        """Return a daily collection of values at the input percentile of each day.

        Args:
            percentile: A float value from 0 to 100 representing the
                requested percentile.
        """
        return self._time_interval_operation('daily', 'percentile', percentile)

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
        return self._time_interval_operation('monthly', 'average')

    def total_monthly(self):
        """Return a monthly collection of values totaled over each month."""
        return self._time_interval_operation('monthly', 'total')

    def percentile_monthly(self, percentile):
        """Return a monthly collection of values at the input percentile of each month.

        Args:
            percentile: A float value from 0 to 100 representing the
                requested percentile.
        """
        return self._time_interval_operation('monthly', 'percentile', percentile)

    def group_by_month_per_hour(self):
        """Return a dictionary of this collection's values grouped by each month per hour.

        Key values are tuples of 3 integers.

        -   The first represents the month of the year between 1-12.

        -   The second represents the hour of the day between 0-24.

        -   The third represents the minute of the minute of the hour between 0-59.
        """
        t_step = self.header.analysis_period.timestep
        data_by_month_per_hour = OrderedDict()
        for m in xrange(1, 13):
            for h in xrange(0, 24 * t_step):
                float_hr = h / t_step
                hr, mi = int(float_hr), int((h % t_step) * (60 / t_step))
                data_by_month_per_hour[(m, hr, mi)] = []
        for v, dt in zip(self.values, self.datetimes):
            data_by_month_per_hour[(dt.month, dt.hour, dt.minute)].append(v)
        return data_by_month_per_hour

    def average_monthly_per_hour(self):
        """Return a monthly per hour data collection of average values."""
        return self._time_interval_operation('monthlyperhour', 'average')

    def total_monthly_per_hour(self):
        """Return a monthly per hour collection of totaled values."""
        return self._time_interval_operation('monthlyperhour', 'total')

    def percentile_monthly_per_hour(self, percentile):
        """Return a monthly per hour collection of values at the input percentile.

        Args:
            percentile: A float value from 0 to 100 representing the
                requested percentile.
        """
        return self._time_interval_operation('monthlyperhour', 'percentile', percentile)

    def interpolate_holes(self):
        """Linearly interpolate over holes in this collection to make it continuous.

        Returns:
            continuous_collection -- A HourlyContinuousCollection with the same data
            as this collection but with missing data filled by means of a
            linear interpolation.
        """
        # validate analysis_period and use the resulting period to generate datetimes
        assert self.validated_a_period, 'validated_a_period property must be' \
            ' True to use interpolate_holes(). Run validate_analysis_period().'
        mins_per_step = int(60 / self.header.analysis_period.timestep)
        new_datetimes = self.header.analysis_period.datetimes
        new_values = []

        # if the first steps are a hole, duplicate the first value.
        i = 0
        if new_datetimes[0] != self.datetimes[0]:
            n_steps = int((self.datetimes[0].moy - new_datetimes[0].moy) / mins_per_step)
            new_values.extend([self._values[0]] * n_steps)
            i = n_steps - 1

        # go through the values interpolating any holes.
        for j in xrange(len(self._values)):
            if new_datetimes[i] == self.datetimes[j]:  # there is no hole.
                new_values.append(self._values[j])
                i += 1
            else:  # there is a hole between this step and the previous step.
                n_steps = int(
                    (self.datetimes[j].moy - new_datetimes[i].moy) / mins_per_step)
                intp_vals = self._xxrange(self._values[j - 1], self._values[j], n_steps)
                new_values.extend(list(intp_vals)[1:] + [self._values[j]])
                i += n_steps

        # if the last steps are a hole duplicate the last value.
        if len(new_values) != len(new_datetimes):
            n_steps = len(new_datetimes) - len(new_values)
            new_values.extend([self._values[-1]] * n_steps)

        # build the new continuous data collection.
        return HourlyContinuousCollection(self.header.duplicate(), new_values)

    def cull_to_timestep(self, timestep=1):
        """Get a collection with only datetimes that fit a timestep."""
        valid_s = self.header.analysis_period.VALIDTIMESTEPS.keys()
        assert timestep in valid_s, \
            'timestep {} is not valid. Choose from: {}'.format(timestep, valid_s)

        new_ap, new_values, new_datetimes = self._timestep_cull(timestep)
        new_header = self.header.duplicate()
        new_header._analysis_period = new_ap
        new_coll = HourlyDiscontinuousCollection(
            new_header, new_values, new_datetimes)
        new_coll._validated_a_period = True
        return new_coll

    def convert_to_culled_timestep(self, timestep=1):
        """Convert this collection to one that only has datetimes that fit a timestep."""
        valid_s = self.header.analysis_period.VALIDTIMESTEPS.keys()
        assert timestep in valid_s, \
            'timestep {} is not valid. Choose from: {}'.format(timestep, valid_s)

        new_ap, new_values, new_datetimes = self._timestep_cull(timestep)
        self.header._analysis_period = new_ap
        self._values = new_values
        self._datetimes = new_datetimes

    def to_time_aggregated(self):
        """Get a collection where data has been aggregated over the collection timestep.

        For example, if the collection has a Power data type in W, this method
        will return a collection with an Energy data type in kWh.
        """
        return self._time_aggregated_collection(self.header.analysis_period.timestep)

    def to_time_rate_of_change(self):
        """Get a collection that has been converted to time-rate-of-change units.

        For example, if the collection has an Energy data type in kWh, this method
        will return a collection with a Power data type in W.
        """
        return self._time_rate_of_change_collection(self.header.analysis_period.timestep)

    def validate_analysis_period(self):
        """Get a collection where the header analysis_period aligns with datetimes.

        This means that checks for five criteria will be performed:

        1)  All datetimes in the data collection are in chronological order starting
            from the analysis_period start hour to the end hour.

        2)  No duplicate datetimes exist in the data collection.

        3)  There are no datetimes that lie outside of the analysis_period time range.

        4)  There are no datetimes that do not align with the analysis_period
            timestep.

        5)  Datetimes for February 29th are excluded if is_leap_year is False on
            the analysis_period.

        Note that there is no need to run this check any time that a discontinuous
        data collection has been derived from a continuous one or when the
        validated_a_period attribute of the collection is True.  Furthermore, most
        methods on this data collection will still run without a validated
        analysis_period.
        """
        a_per = self.header.analysis_period
        n_ap = [a_per.st_month, a_per.st_day, a_per.st_hour, a_per.end_month,
                a_per.end_day, a_per.end_hour, a_per.timestep, a_per.is_leap_year]

        # make sure that datetimes are all in chronological order.
        sort_datetimes, sort_values = zip(*sorted(zip(self.datetimes, self.values)))
        if not a_per.is_reversed and not a_per.is_annual:
            if sort_datetimes[0].doy < a_per.st_time.doy:
                n_ap[0] = sort_datetimes[0].month
                n_ap[1] = sort_datetimes[0].day
            if sort_datetimes[-1].doy > a_per.end_time.doy:
                n_ap[3] = sort_datetimes[-1].month
                n_ap[4] = sort_datetimes[-1].day
        elif a_per.is_reversed:
            last_ind = None
            for i, date_t in enumerate(sort_datetimes):
                last_ind = i if date_t.moy <= a_per.end_time.moy else last_ind
            if last_ind is not None:
                last_ind = last_ind + 1
                sort_datetimes = sort_datetimes[last_ind:] + sort_datetimes[:last_ind]
                sort_values = sort_values[last_ind:] + sort_values[:last_ind]
            # If datetimes are outside the a_period range, just make it annual.
            # There's no way to know what side of the analysis_period should be extended.
            if sort_datetimes[0].doy > a_per.end_time.doy and \
                    sort_datetimes[0].doy < a_per.st_time.doy:
                n_ap[0], n_ap[1], n_ap[3], n_ap[4] = 1, 1, 12, 31
                sort_datetimes, sort_values = zip(*sorted(zip(
                    self.datetimes, self.values)))

        # check that no hours lie outside of the analysis_period
        if not a_per.is_annual:
            if a_per.st_hour != 0:
                for date_t in sort_datetimes:
                    n_ap[2] = date_t.hour if date_t.hour < n_ap[2] else n_ap[2]
            if a_per.end_hour != 23:
                for date_t in sort_datetimes:
                    n_ap[5] = date_t.hour if date_t.hour > n_ap[5] else n_ap[5]

        # check that there are no duplicate datetimes.
        for i in xrange(len(sort_datetimes)):
            assert sort_datetimes[i] != sort_datetimes[i - 1], 'Duplicate datetime ' \
                'was found in the collection: {}'.format(sort_datetimes[i])

        # check that the analysis_period timestep is correct.
        mins_per_step = int(60 / n_ap[6])
        for date_t in sort_datetimes:
            if date_t.moy % mins_per_step != 0:
                i = 0
                valid_steps = sorted(a_per.VALIDTIMESTEPS.keys())
                while date_t.moy % mins_per_step != 0 and i < len(valid_steps):
                    mins_per_step = int(60 / valid_steps[i])
                    i += 1
                n_ap[6] = int(60 / mins_per_step)

        # check that the analysis_period leap_year is correct.
        if not a_per.is_leap_year:
            for date_t in sort_datetimes:
                if date_t.month == 2 and date_t.day == 29:
                    n_ap[7] = True

        # build a validated collection.
        new_ap = AnalysisPeriod(*n_ap)
        new_header = self.header.duplicate()
        new_header._analysis_period = new_ap
        new_coll = HourlyDiscontinuousCollection(new_header, sort_values, sort_datetimes)
        new_coll._validated_a_period = True
        return new_coll

    def to_dict(self):
        """Convert Data Collection to a dictionary."""
        return {
            'header': self.header.to_dict(),
            'values': self._values,
            'datetimes': [dat.to_array() for dat in self.datetimes],
            'validated_a_period': self._validated_a_period,
            'type': self.__class__.__name__
        }

    def _xxrange(self, start, end, step_count):
        """Generate n values between start and end."""
        _step = (end - start) / float(step_count)
        return (start + (i * _step) for i in xrange(int(step_count)))

    def _filter_by_moys_slow(self, moys):
        """Filter the Data Collection with a slow method that always works."""
        _filt_values = []
        _filt_datetimes = []
        for i, d in enumerate(self.datetimes):
            if d.moy in moys:
                _filt_datetimes.append(d)
                _filt_values.append(self._values[i])
        return _filt_values, _filt_datetimes

    def _timestep_cull(self, timestep):
        """Cull out values that do not fit a timestep."""
        new_values = []
        new_datetimes = []
        mins_per_step = int(60 / timestep)
        for i, date_t in enumerate(self.datetimes):
            if date_t.moy % mins_per_step == 0:
                new_datetimes.append(date_t)
                new_values.append(self.values[i])
        a_per = self.header.analysis_period
        new_ap = AnalysisPeriod(a_per.st_month, a_per.st_day, a_per.st_hour,
                                a_per.end_month, a_per.end_day, a_per.end_hour,
                                timestep, a_per.is_leap_year)
        return new_ap, new_values, new_datetimes

    def _check_analysis_period(self, analysis_period):
        assert self.header.analysis_period.timestep == analysis_period.timestep,\
            'analysis_period timestep must match that on the'\
            'Collection header. {} != {}'.format(
                analysis_period.timestep, self.header.analysis_period.timestep)
        assert self.header.analysis_period.is_leap_year is analysis_period.is_leap_year,\
            'analysis_period is_leap_year must match that on the'\
            'Collection header. {} != {}'.format(
                analysis_period.is_leap_year, self.header.analysis_period.is_leap_year)

    def _time_interval_operation(self, interval, operation, percentile=0):
        """Get a collection of a certain time interval with a given math operation."""
        # retrive the function that correctly describes the operation
        if operation == 'average':
            funct = self._average
        elif operation == 'total':
            funct = self._total
        else:
            assert 0 <= percentile <= 100, \
                'percentile must be between 0 and 100. Got {}'.format(percentile)
            funct = self._get_percentile_function(percentile)

        # retrive the data that correctly describes the time interval
        if interval == 'monthly':
            data_dict = self.group_by_month()
            dates = self.header.analysis_period.months_int
        elif interval == 'daily':
            data_dict = self.group_by_day()
            dates = self.header.analysis_period.doys_int
        elif interval == 'monthlyperhour':
            data_dict = self.group_by_month_per_hour()
            dates = self.header.analysis_period.months_per_hour
        else:
            raise ValueError('Invalid input value for interval: {}'.format(interval))
        # get the data and header for the new collection
        new_data, d_times = [], []
        for i in dates:
            vals = data_dict[i]
            if vals != []:
                new_data.append(funct(vals))
                d_times.append(i)
        new_header = self.header.duplicate()
        if operation == 'percentile':
            new_header.metadata['operation'] = '{} percentile'.format(percentile)
        else:
            new_header.metadata['operation'] = operation

        # build the final data collection
        if interval == 'monthly':
            collection = MonthlyCollection(new_header, new_data, d_times)
        elif interval == 'daily':
            collection = DailyCollection(new_header, new_data, d_times)
        elif interval == 'monthlyperhour':
            collection = MonthlyPerHourCollection(new_header, new_data, d_times)

        collection._validated_a_period = True
        return collection

    def __repr__(self):
        """Hourly Discontinuous Collection representation."""
        return "{} Discontinuous Data Collection\n{}\n{} ({})\n...{} values...".format(
            self.timestep_text, self.header.analysis_period,
            self.header.data_type, self.header.unit, len(self._values))


class HourlyContinuousCollection(HourlyDiscontinuousCollection):
    """Class for Continuous Data Collections at hourly or sub-hourly intervals.

    Args:
        header: A Ladybug Header object. Note that this header
            must have an AnalysisPeriod on it that aligns with the
            list of values.
        values: A list of values. Note that the length of this list
            must align with the AnalysisPeriod on the header.

    Properties:
        * average
        * bounds
        * datetimes
        * header
        * is_continuous
        * is_mutable
        * max
        * median
        * min
        * moys_dict
        * timestep_text
        * total
        * validated_a_period
        * values
    """

    _collection_type = 'HourlyContinuous'

    def __init__(self, header, values):
        """Initialize hourly discontinuous collection.
        """
        assert isinstance(header, Header), \
            'header must be a Ladybug Header object. Got {}'.format(type(header))
        assert header.analysis_period.st_hour == 0, \
            'analysis_period start hour of {} must be 0. Got {}'.format(
                self.__class__.__name__, header.analysis_period.st_hour)
        assert header.analysis_period.end_hour == 23, \
            'analysis_period end hour of {} must be 23. Got {}'.format(
                self.__class__.__name__, header.analysis_period.end_hour)

        self._header = header
        self.values = values
        self._datetimes = None
        self._validated_a_period = True

    @classmethod
    def from_dict(cls, data):
        """Create a Data Collection from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

                {
                "header": {}  # A Ladybug Header,
                "values": []  # An array of values,
                }
        """
        assert 'header' in data, 'Required keyword "header" is missing!'
        assert 'values' in data, 'Required keyword "values" is missing!'
        return cls(Header.from_dict(data['header']), data['values'])

    @property
    def datetimes(self):
        """Return datetimes for this collection as a tuple."""
        if self._datetimes is None:
            self._datetimes = self.header.analysis_period.datetimes
        return self._datetimes

    def interpolate_holes(self):
        """All continuous collections do not have holes in the data set.

        Therefore, there is no need to run this method on a continuous collection.
        """
        return self.duplicate()

    def interpolate_to_timestep(self, timestep, cumulative=None):
        """Interpolate data for a finer timestep using a linear interpolation.

        Args:
            timestep: Target timestep as an integer. Target timestep must be
                divisible by current timestep.
            cumulative: A boolean that sets whether the interpolation
                should treat the data collection values as cumulative, in
                which case the value at each timestep is the value over
                that timestep (instead of over the hour). The default will
                check the DataType to see if this type of data is typically
                cumulative over time.

        Return:
            A continuous hourly data collection with data interpolated to
            the input timestep.
        """
        assert timestep % self.header.analysis_period.timestep == 0, \
            'Target timestep({}) must be divisible by current timestep({})' \
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
        if cumulative or (cumulative is None and native_cumulative):
            for i, d in enumerate(_new_values):
                _new_values[i] = d / timestep

        # shift data by a half-hour if data is averaged or cumulative over an hour
        if not self.header.data_type.point_in_time:
            shift_dist = int(timestep / 2)
            _new_values = _new_values[-shift_dist:] + _new_values[:-shift_dist]

        # build a new header
        a_per = self.header.analysis_period
        _new_a_per = AnalysisPeriod(a_per.st_month, a_per.st_day, a_per.st_hour,
                                    a_per.end_month, a_per.end_day, a_per.end_hour,
                                    timestep, a_per.is_leap_year)
        _new_header = self.header.duplicate()
        _new_header._analysis_period = _new_a_per
        return HourlyContinuousCollection(_new_header, _new_values)

    def filter_by_conditional_statement(self, statement):
        """Filter the Data Collection based on a conditional statement.

        Args:
            statement: A conditional statement as a string (e.g. a > 25 and a%5 == 0).
                The variable should always be named as 'a' (without quotations).

        Return:
            A new Data Collection containing only the filtered data
        """
        _filt_values, _filt_datetimes = self._filter_by_statement(statement)
        collection = HourlyDiscontinuousCollection(
            self.header.duplicate(), _filt_values, _filt_datetimes)
        collection._validated_a_period = True
        return collection

    def filter_by_pattern(self, pattern):
        """Filter the Data Collection based on a list of booleans.

        Args:
            pattern: A list of True/False values.  Typically, this is a list
                with a length matching the length of the Data Collections values
                but it can also be a pattern to be repeated over the Data Collection.

        Return:
            A new Data Collection with filtered data
        """
        _filt_values, _filt_datetimes = self._filter_by_pattern(pattern)
        collection = HourlyDiscontinuousCollection(
            self.header.duplicate(), _filt_values, _filt_datetimes)
        collection._validated_a_period = True
        return collection

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
                          (analysis_period.st_time.moy / t_s) + st_ind +
                          analysis_period.timestep)
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

    def filter_by_hoys(self, hoys):
        """Filter the Data Collection using a list of hours of the year (hoys).

        Args:
           hoys: A List of hours of the year 0..8759

        Return:
            A new Data Collection with filtered data
        """
        existing_hoys = self.header.analysis_period.hoys
        hoys = [h for h in hoys if h in existing_hoys]
        _moys = tuple(int(hour * 60) for hour in hoys)
        return self.filter_by_moys(_moys)

    def filter_by_moys(self, moys):
        """Filter the Data Collection based on a list of minutes of the year.

        Args:
           moys: A List of minutes of the year [0..8759 * 60]

        Return:
            A new Data Collection with filtered data
        """
        t_s = 60 / self.header.analysis_period.timestep
        st_ind = self.header.analysis_period.st_time.moy / t_s
        if not self.header.analysis_period.is_reversed:
            _filt_indices = [int(moy / t_s - st_ind) for moy in moys]
        else:
            if not self.header.analysis_period.is_leap_year:
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
        coll = HourlyDiscontinuousCollection(_filt_header, _filt_values, _filt_datetimes)
        coll._validated_a_period = True
        return coll

    def group_by_day(self):
        """Return a dictionary of this collection's values grouped by each day of year.

        Key values are between 1-365.
        """
        hourly_data_by_day = OrderedDict()
        for d in xrange(1, 366):
            hourly_data_by_day[d] = []
        a_per = self.header.analysis_period
        indx_per_day = 24 * a_per.timestep
        start_doy = sum(a_per._num_of_days_each_month[:a_per.st_time.month - 1]) \
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
            a_per.st_day - 1 - a_per._num_of_days_each_month[a_per_months[0] - 1])
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

    def to_immutable(self):
        """Get an immutable version of this collection."""
        if self._enumeration is None:
            self._get_mutable_enumeration()
        col_obj = self._enumeration['immutable'][self._collection_type]
        return col_obj(self.header, self.values)

    def get_aligned_collection(self, value=0, data_type=None, unit=None, mutable=None):
        """Return a Collection aligned with this one composed of one repeated value.

        Aligned Data Collections are of the same Data Collection class,
        have the same number of values and have matching datetimes.

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
            collection = self.__class__(header, values)
        else:
            if self._enumeration is None:
                self._get_mutable_enumeration()
            if not mutable:
                col_obj = self._enumeration['immutable'][self._collection_type]
            else:
                col_obj = self._enumeration['mutable'][self._collection_type]
            collection = col_obj(header, values)
        return collection

    def is_collection_aligned(self, data_collection):
        """Check if this Data Collection is aligned with another.

        Aligned Data Collections are of the same Data Collection class,
        have the same number of values and have matching datetimes.

        Args:
            data_collection: The Data Collection which you want to test if this
                collection is aligned with.

        Return:
            True if collections are aligned, False if not aligned
        """
        if self._collection_type != data_collection._collection_type:
            return False
        elif len(self.values) != len(data_collection.values):
            return False
        elif self.header.analysis_period != data_collection.header.analysis_period:
            return False
        return True

    def to_discontinuous(self):
        """Return a discontinuous version of the current collection."""
        collection = HourlyDiscontinuousCollection(self.header.duplicate(),
                                                   self.values, self.datetimes)
        collection._validated_a_period = True
        return collection

    def validate_analysis_period(self, overwrite_period=False):
        """All continuous collections already have valid header analysis_periods.

        Therefore, this method just returns a copy of the current collection.
        """
        return self.duplicate()

    def to_dict(self):
        """Convert Data Collection to a dictionary."""
        return {
            'header': self.header.to_dict(),
            'values': self._values,
            'type': self.__class__.__name__
        }

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
        if a_per.end_hour > self.header.analysis_period.end_hour:
            n_ap[5] = self.header.analysis_period.end_hour
            new_needed = True
        if a_per.st_time.doy < self.header.analysis_period.st_time.doy:
            n_ap[0] = self.header.analysis_period.st_month
            n_ap[1] = self.header.analysis_period.st_day
            new_needed = True
        if a_per.end_time.doy > self.header.analysis_period.end_time.doy:
            n_ap[3] = self.header.analysis_period.end_month
            n_ap[4] = self.header.analysis_period.end_day
            new_needed = True
        if not new_needed:
            return a_per
        return AnalysisPeriod(*n_ap)

    def _check_values(self, values):
        """Check values whenever they come through the values setter."""
        assert isinstance(values, Iterable) and not isinstance(
            values, (str, dict, bytes, bytearray)), \
            'values should be a list or tuple. Got {}'.format(type(values))
        assert len(values) == len(self.header.analysis_period), 'Length of ' \
            'values does not match that expected by the header analysis_period.'\
            ' {} != {}'.format(len(values), len(self.header.analysis_period))

    @property
    def is_continuous(self):
        """Boolean denoting whether the data collection is continuous."""
        return True

    def __add__(self, other):
        new_vals = self._add_values(other)
        return self.__class__(self.header, new_vals)

    def __sub__(self, other):
        new_vals = self._sub_values(other)
        return self.__class__(self.header, new_vals)

    def __mul__(self, other):
        new_vals = self._mul_values(other)
        return self.__class__(self.header, new_vals)

    def __div__(self, other):
        new_vals = self._div_values(other)
        return self.__class__(self.header, new_vals)

    def __truediv__(self, other):
        new_vals = self._div_values(other)
        return self.__class__(self.header, new_vals)

    def __neg__(self):
        new_vals = [-v_1 for v_1 in self._values]
        return self.__class__(self.header, new_vals)

    def __key(self):
        return (self.header, self.values)

    def __copy__(self):
        return self.__class__(self.header.duplicate(), list(self._values))

    def __repr__(self):
        """Hourly Discontinuous Collection representation."""
        return "{} Continuous Data Collection\n{}\n{} ({})\n...{} values...".format(
            self.timestep_text, self.header.analysis_period,
            self.header.data_type, self.header.unit, len(self._values))


class DailyCollection(BaseCollection):
    """Class for Daily Data Collections.

    Args:
        header: A Ladybug Header object.  Note that this header
            must have an AnalysisPeriod on it.
        values: A list of values.
        datetimes: A list of integers that aligns with the list of values.
            Each integer in the list is 1-365 and denotes the day of the
            year for each value of the collection.

    Properties:
        * average
        * bounds
        * datetimes
        * header
        * is_continuous
        * is_mutable
        * max
        * median
        * min
        * total
        * validated_a_period
        * values
    """
    _collection_type = 'Daily'

    def __init__(self, header, values, datetimes):
        """Initialize daily collection.
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

    def filter_by_analysis_period(self, analysis_period):
        """Filter the Data Collection based on an analysis period.

        Args:
           analysis period: A Ladybug analysis period

        Return:
            A new Data Collection with filtered data
        """
        self._check_analysis_period(analysis_period)
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

    def group_by_month(self):
        """Return a dictionary of this collection's values grouped by each month.

        Key values are between 1-12.
        """
        data_by_month = OrderedDict()
        for d in xrange(1, 13):
            data_by_month[d] = []
        for v, doy in zip(self._values, self.datetimes):
            dt = DateTime.from_hoy(((doy - 1) * 24) + 1)
            data_by_month[dt.month].append(v)
        return data_by_month

    def average_monthly(self):
        """Return a monthly collection of values averaged for each month."""
        return self._monthly_operation('average')

    def total_monthly(self):
        """Return a monthly collection of values totaled over each month."""
        return self._monthly_operation('total')

    def percentile_monthly(self, percentile):
        """Return a monthly collection of values at the input percentile of each month.

        Args:
            percentile: A float value from 0 to 100 representing the
                requested percentile.
        """
        return self._monthly_operation('percentile', percentile)

    def to_time_aggregated(self):
        """Get a collection where data has been aggregated over the collection timestep.

        For example, if the collection has a Power data type in W, this method
        will return a collection with an Energy data type in kWh.
        """
        return self._time_aggregated_collection(1. / 24.)

    def to_time_rate_of_change(self):
        """Get a collection that has been converted to time rate of change units.

        For example, if the collection has an Energy data type in kWh, this method
        will return a collection with a Power data type in W.
        """
        return self._time_rate_of_change_collection(1. / 24.)

    def validate_analysis_period(self):
        """Get a collection where the header analysis_period aligns with datetimes.

        This means that checks for four criteria will be performed:

        1)  All days in the data collection are chronological starting from the
            analysis_period start day to the end day.

        2)  No duplicate days exist in the data collection.

        3)  There are no days that lie outside of the analysis_period time range.

        4)  February 29th is excluded if is_leap_year is False on the analysis_period.

        Note that there is no need to run this check any time that a discontinuous
        data collection has been derived from a continuous one or when the
        validated_a_period attribute of the collection is True.
        """
        a_per = self.header.analysis_period
        n_ap = [a_per.st_month, a_per.st_day, a_per.st_hour, a_per.end_month,
                a_per.end_day, a_per.end_hour, a_per.timestep, a_per.is_leap_year]

        # check that the analysis_period leap_year is correct.
        if not a_per.is_leap_year:
            for date_t in self.datetimes:
                if date_t == 366:
                    n_ap[7] = True

        # make sure that datetimes are all in chronological order.
        sort_datetimes, sort_values = zip(*sorted(zip(self.datetimes, self.values)))
        if not a_per.is_reversed and not a_per.is_annual:
            if sort_datetimes[0] < a_per.st_time.doy:
                new_start = DateTime.from_hoy((sort_datetimes[0] - 1) * 24, n_ap[7])
                n_ap[0] = new_start.month
                n_ap[1] = new_start.day
            if sort_datetimes[-1] > a_per.end_time.doy:
                new_end = DateTime.from_hoy((sort_datetimes[-1] - 1) * 24, n_ap[7])
                n_ap[3] = new_end.month
                n_ap[4] = new_end.day
        elif a_per.is_reversed:
            last_ind = None
            for i, date_t in enumerate(sort_datetimes):
                last_ind = i if date_t <= a_per.end_time.doy else last_ind
            if last_ind is not None:
                last_ind = last_ind + 1
                sort_datetimes = sort_datetimes[last_ind:] + sort_datetimes[:last_ind]
                sort_values = sort_values[last_ind:] + sort_values[:last_ind]
            # If datetimes are outside the a_period range, just make it annual.
            # There's no way to know what side of the analysis_period should be extended.
            if sort_datetimes[0] > a_per.end_time.doy and \
                    sort_datetimes[0] < a_per.st_time.doy:
                n_ap[0], n_ap[1], n_ap[3], n_ap[4] = 1, 1, 12, 31
                sort_datetimes, sort_values = zip(*sorted(zip(
                    self.datetimes, self.values)))

        # check that there are no duplicate days.
        for i in xrange(len(sort_datetimes)):
            assert sort_datetimes[i] != sort_datetimes[i - 1], 'Duplicate day of year ' \
                'was found in the collection: {}'.format(sort_datetimes[i])

        # build a validated collection.
        new_ap = AnalysisPeriod(*n_ap)
        new_header = self.header.duplicate()
        new_header._analysis_period = new_ap
        new_coll = DailyCollection(new_header, sort_values, sort_datetimes)
        new_coll._validated_a_period = True
        return new_coll

    def _check_analysis_period(self, analysis_period):
        assert self.header.analysis_period.is_leap_year is analysis_period.is_leap_year,\
            'analysis_period is_leap_year must match that on the'\
            'Collection header. {} != {}'.format(
                analysis_period.is_leap_year, self.header.analysis_period.is_leap_year)

    def _monthly_operation(self, operation, percentile=0):
        """Get a MonthlyCollection given a certain operation."""
        # Retrive the correct operation.
        if operation == 'average':
            funct = self._average
        elif operation == 'total':
            funct = self._total
        else:
            assert 0 <= percentile <= 100, \
                'percentile must be between 0 and 100. Got {}'.format(percentile)
            funct = self._get_percentile_function(percentile)

        # Get the data for the new collection
        data_dict = self.group_by_month()
        new_data, d_times = [], []
        for i in self.header.analysis_period.months_int:
            vals = data_dict[i]
            if vals != []:
                new_data.append(funct(vals))
                d_times.append(i)

        # build the new monthly collection
        new_header = self.header.duplicate()
        if operation == 'percentile':
            new_header.metadata['operation'] = '{} percentile'.format(percentile)
        else:
            new_header.metadata['operation'] = operation
        collection = MonthlyCollection(new_header, new_data, d_times)
        collection._validated_a_period = True
        return collection

    @property
    def is_continuous(self):
        """Boolean denoting whether the data collection is continuous."""
        return self._validated_a_period and \
            len(self.values) == len(self.header.analysis_period.doys_int)

    def __repr__(self):
        """Daily Collection representation."""
        a_per = self.header.analysis_period
        return "Daily Collection\n{}/{} to {}/{}\n{} ({})\n...{} values...".format(
            a_per.st_month, a_per.st_day, a_per.end_month, a_per.end_day,
            self.header.data_type, self.header.unit, len(self._values))


class MonthlyCollection(BaseCollection):
    """Class for Monthly Data Collections.

    Args:
        header: A Ladybug Header object.  Note that this header
            must have an AnalysisPeriod on it.
        values: A list of values.
        datetimes: A list of integers that aligns with the list of values.
            Each integer in the list is 1-12 and denotes the month of the
            year for each value of the collection.

    Properties:
        * average
        * bounds
        * datetimes
        * header
        * is_continuous
        * is_mutable
        * max
        * median
        * min
        * total
        * validated_a_period
        * values
    """

    _collection_type = 'Monthly'

    def __init__(self, header, values, datetimes):
        """Initialize monthly collection.
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

    def validate_analysis_period(self):
        """Get a collection where the header analysis_period aligns with datetimes.

        This means that checks for three criteria will be performed:

        1)  All months in the data collection are chronological starting from the
            analysis_period start month to the end month.

        2)  No duplicate months exist in the data collection.

        3)  There are no months that lie outside of the analysis_period range.

        Note that there is no need to run this check any time that a
        data collection has been derived from a continuous one or when the
        validated_a_period attribute of the collection is True.
        """
        a_per = self.header.analysis_period
        n_ap = [a_per.st_month, a_per.end_month]

        # make sure that months are in chronological order.
        sort_datetimes, sort_values = zip(*sorted(zip(self.datetimes, self.values)))
        # check that no datetimes lie outside of the analysis_period
        if not a_per.is_reversed and not a_per.is_annual:
            if sort_datetimes[0] < a_per.st_month:
                n_ap[0] = sort_datetimes[0]
            if sort_datetimes[-1] > a_per.end_month:
                n_ap[1] = sort_datetimes[-1]
        elif a_per.is_reversed:
            last_ind = None
            for i, date_t in enumerate(sort_datetimes):
                last_ind = i if date_t <= a_per.end_time.month else last_ind
            if last_ind is not None:
                last_ind = last_ind + 1
                sort_datetimes = sort_datetimes[last_ind:] + sort_datetimes[:last_ind]
                sort_values = sort_values[last_ind:] + sort_values[:last_ind]
            if sort_datetimes[0] > a_per.end_time.month and \
                    sort_datetimes[0] < a_per.st_time.month:
                n_ap = [1, 12]
                sort_datetimes, sort_values = zip(*sorted(zip(
                    self.datetimes, self.values)))

        # check that there are no duplicate months.
        for i in xrange(len(sort_datetimes)):
            assert sort_datetimes[i] != sort_datetimes[i - 1], 'Duplicate month ' \
                'was found in the collection: {}'.format(sort_datetimes[i])

        # build a validated collection.
        new_ap = AnalysisPeriod(st_month=n_ap[0], end_month=n_ap[1])
        new_header = self.header.duplicate()
        new_header._analysis_period = new_ap
        new_coll = MonthlyCollection(new_header, sort_values, sort_datetimes)
        new_coll._validated_a_period = True
        return new_coll

    @property
    def is_continuous(self):
        """Boolean denoting whether the data collection is continuous."""
        return self._validated_a_period and \
            len(self.values) == len(self.header.analysis_period.months_int)

    def __repr__(self):
        """Monthly Collection representation."""
        a_per = self.header.analysis_period
        return "Monthly Collection\n{} to {}\n{} ({})\n...{} values...".format(
            a_per.MONTHNAMES[a_per.st_month], a_per.MONTHNAMES[a_per.end_month],
            self.header.data_type, self.header.unit, len(self._values))


class MonthlyPerHourCollection(BaseCollection):
    """Class for Monthly Per Hour Collections.

    Args:
        header: A Ladybug Header object.  Note that this header
            must have an AnalysisPeriod on it.
        values: A list of values.
        datetimes: A list of tuples that aligns with the list of values.
            Each tuple should possess three values: the first is the month, the
            second is the hour, and the third is the minute. (eg. (12, 23, 30) =
            December at 11:30 PM).

    Properties:
        * average
        * bounds
        * datetimes
        * header
        * is_continuous
        * is_mutable
        * max
        * median
        * min
        * total
        * validated_a_period
        * values
    """

    _collection_type = 'MonthlyPerHour'

    def __init__(self, header, values, datetimes):
        """Initialize monthly per hour collection.
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

    def filter_by_analysis_period(self, analysis_period):
        """Filter the Data Collection based on an analysis period.

        Args:
           analysis period: A Ladybug analysis period

        Return:
            A new Data Collection with filtered data
        """
        _filtered_data = self.filter_by_months_per_hour(
            analysis_period.months_per_hour)
        _filtered_data.header._analysis_period = analysis_period
        return _filtered_data

    def filter_by_months_per_hour(self, months_per_hour):
        """Filter the Data Collection based on a list of months per hour (as strings).

        Args:
           months_per_hour: A list of tuples representing months per hour.
               Each tuple should possess three values: the first is the month, the
               second is the hour and the third is the minute. (eg. (12, 23, 30) =
               December at 11:30 PM)

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

    def validate_analysis_period(self):
        """Get a collection where the header analysis_period aligns with datetimes.

        This means that checks for three criteria will be performed:

        1)  All datetimes in the data collection are chronological starting from the
            analysis_period start datetime to the end datetime.

        2)  No duplicate datetimes exist in the data collection.

        3)  There are no datetimes that lie outside of the analysis_period range.

        Note that there is no need to run this check any time that a
        data collection has been derived from a continuous one or when the
        validated_a_period attribute of the collection is True.
        """
        a_per = self.header.analysis_period
        n_ap = [a_per.st_month, a_per.st_hour, a_per.end_month, a_per.end_hour]

        # make sure that months are in chronological order.
        sort_datetimes, sort_values = zip(*sorted(zip(self.datetimes, self.values),
                                                  key=lambda x: (x[0][0], x[0][1])))
        if not a_per.is_reversed and not a_per.is_annual:
            if sort_datetimes[0][0] < a_per.st_month:
                n_ap[0] = sort_datetimes[0][0]
            if sort_datetimes[-1][0] > a_per.end_month:
                n_ap[2] = sort_datetimes[-1][0]
        elif a_per.is_reversed:
            last_ind = None
            for i, date_t in enumerate(sort_datetimes):
                last_ind = i if date_t[0] <= a_per.end_time.month \
                    and date_t[1] <= a_per.end_time.hour else last_ind
            if last_ind is not None:
                last_ind = last_ind + 1
                sort_datetimes = sort_datetimes[last_ind:] + sort_datetimes[:last_ind]
                sort_values = sort_values[last_ind:] + sort_values[:last_ind]
            if sort_datetimes[0][0] > a_per.end_time.month and \
                    sort_datetimes[0][0] < a_per.st_time.month:
                n_ap[0], n_ap[2] = 1, 12
                sort_datetimes, sort_values = zip(*sorted(zip(
                    self.datetimes, self.values), key=lambda x: (x[0][0], x[0][1])))

        # check that there are no duplicate months.
        for i in xrange(len(sort_datetimes)):
            assert sort_datetimes[i] != sort_datetimes[i - 1], 'Duplicate ' \
                '(month, hour) was found in the collection: {}'.format(sort_datetimes[i])

        # check that no hours lie outside of the analysis_period
        if not a_per.is_annual:
            if a_per.st_hour != 0:
                for date_t in sort_datetimes:
                    n_ap[1] = date_t[1] if date_t[1] < n_ap[1] else n_ap[1]
            if a_per.end_hour != 23:
                for date_t in sort_datetimes:
                    n_ap[3] = date_t[1] if date_t[1] > n_ap[3] else n_ap[3]

        # build a validated collection.
        new_ap = AnalysisPeriod(st_month=n_ap[0], st_hour=n_ap[1],
                                end_month=n_ap[2], end_hour=n_ap[3])
        new_header = self.header.duplicate()
        new_header._analysis_period = new_ap
        new_coll = MonthlyPerHourCollection(new_header, sort_values, sort_datetimes)
        new_coll._validated_a_period = True
        return new_coll

    @property
    def is_continuous(self):
        """Boolean denoting whether the data collection is continuous."""
        a_per = self.header.analysis_period
        return self._validated_a_period and a_per.st_hour == 0 and a_per.end_hour \
            == 23 and len(self.values) == len(a_per.months_per_hour)

    def __repr__(self):
        """Monthly Per Hour Collection representation."""
        return "Monthly Per Hour Collection\n{}@{} to {}@{}\n"\
            "{} ({})\n...{} values...".format(
                self.header.analysis_period.st_month,
                self.header.analysis_period.st_hour,
                self.header.analysis_period.end_month,
                self.header.analysis_period.end_hour,
                self.header.data_type, self.header.unit, len(self._values))
