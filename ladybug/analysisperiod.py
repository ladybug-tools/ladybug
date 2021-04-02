# coding=utf-8
"""Ladybug analysis period class."""
from __future__ import division

from .dt import DateTime

from datetime import datetime, timedelta
import sys
if (sys.version_info >= (3, 0)):
    xrange = range


class AnalysisPeriod(object):
    """An analysis period between two dates of the year and between certain hours.

    Args:
        st_month: An integer between 1-12 for starting month (default = 1)
        st_day: An integer between 1-31 for starting day (default = 1).
                Note that some months are shorter than 31 days.
        st_hour: An integer between 0-23 for starting hour (default = 0)
        end_month: An integer between 1-12 for ending month (default = 12)
        end_day: An integer between 1-31 for ending day (default = 31)
                Note that some months are shorter than 31 days.
        end_hour: An integer between 0-23 for ending hour (default = 23)
        timestep: An integer for the number of timesteps per hour. (Default: 1).
                Choose from: 1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60
        is_leap_year: A boolean to indicate whether the AnalysisPeriod represents
            a leap year. (Default: False)

    Properties:
        * st_month
        * st_day
        * end_hour
        * end_month
        * end_day
        * end_hour
        * timestep
        * is_leap_year
        * st_time
        * end_time
        * datetimes
        * moys
        * hoys
        * hoys_int
        * doys_int
        * months_int
        * months_per_hour
        * minute_intervals
        * is_annual
        * is_overnight
        * is_reversed
    """

    VALIDTIMESTEPS = {1: 60, 2: 30, 3: 20, 4: 15, 5: 12,
                      6: 10, 10: 6, 12: 5, 15: 4, 20: 3, 30: 2, 60: 1}
    NUMOFDAYSEACHMONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    NUMOFDAYSEACHMONTHLEAP = (31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    MONTHNAMES = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
                  7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}

    __slots__ = (
        '_is_leap_year', '_st_time', '_num_of_days_each_month', '_is_overnight',
        '_is_reversed', '_timestep', '_minute_intervals', '_end_time',
        '_timestamps_data', '_datetimes'
    )

    def __init__(self, st_month=1, st_day=1, st_hour=0, end_month=12,
                 end_day=31, end_hour=23, timestep=1, is_leap_year=False):
        """Init an analysis period.
        """

        st_month = st_month or 1
        st_day = st_day or 1
        st_hour = st_hour or 0
        end_month = end_month or 12
        end_day = end_day or 31
        end_hour = 23 if end_hour is None else end_hour
        timestep = timestep or 1
        self._is_leap_year = is_leap_year or False

        # calculate start time and end time
        self._st_time = DateTime(int(st_month), int(st_day), int(st_hour),
                                 leap_year=is_leap_year)

        self._num_of_days_each_month = self.NUMOFDAYSEACHMONTH if not self.is_leap_year \
            else self.NUMOFDAYSEACHMONTHLEAP
        if int(end_day) > self._num_of_days_each_month[int(end_month) - 1]:
            end = self._num_of_days_each_month[end_month - 1]
            print("Updated end_day from {} to {}".format(end_day, end))
            end_day = end

        self._end_time = DateTime(int(end_month), int(end_day), int(end_hour),
                                  leap_year=is_leap_year)

        if self.st_time.hour <= self.end_time.hour:
            self._is_overnight = False  # each segments of hours will be in a single day
        else:
            self._is_overnight = True

        # A reversed analysis period defines a period that starting month is after
        # ending month (e.g DEC to JUN)
        if self.st_time.hoy > self.end_time.hoy:
            self._is_reversed = True
        else:
            self._is_reversed = False

        # check time step
        if timestep not in self.VALIDTIMESTEPS:
            raise ValueError("Invalid timestep."
                             "Valid values are %s" % str(self.VALIDTIMESTEPS.keys()))
        self._timestep = timestep
        self._minute_intervals = timedelta(1 / (24.0 * self.timestep))

        # _timestamps_data is a dictionary for datetimes.
        # key values will be minute of year
        self._timestamps_data = None  # set to None for now and calculate upon request
        self._datetimes = None

    @classmethod
    def from_dict(cls, data):
        """Create an analysis period from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "st_month": 1  # An integer between 1-12 for starting month (default = 1)
            "st_day": 1  # An integer between 1-31 for starting day (default = 1).
                       # Note that some months are shorter than 31 days.
            "st_hour": 0  # An integer between 0-23 for starting hour (default = 0)
            "end_month": 12  # An integer between 1-12 for ending month (default = 12)
            "end_day": 31  # An integer between 1-31 for ending day (default = 31)
                         #Note that some months are shorter than 31 days.
            "end_hour": 23  # An integer between 0-23 for ending hour (default = 23)
            "timestep": 1 # An integer number from 1, 2, 3, 4, 5, 6, 10, 12, 15,
                          #20, 30, 60
            }
        """
        keys = ('st_month', 'st_day', 'st_hour', 'end_month',
                'end_day', 'end_hour', 'timestep', 'is_leap_year')
        for key in keys:
            if key not in data:
                data[key] = None

        return cls(
            data['st_month'], data['st_day'], data['st_hour'], data['end_month'],
            data['end_day'], data['end_hour'], data['timestep'],
            data['is_leap_year'])

    @classmethod
    def from_string(cls, analysis_period_string):
        """Create an Analysis Period object from an analysis period string.

        Format is: %s/%s to %s/%s between %s and %s @%s
        """
        # %s/%s to %s/%s between %s to %s @%s*
        is_leap_year = True if analysis_period_string.strip()[-1] == '*' else False
        ap = analysis_period_string.lower().replace(' ', '') \
            .replace('to', ' ') \
            .replace('and', ' ') \
            .replace('/', ' ') \
            .replace('between', ' ') \
            .replace('@', ' ') \
            .replace('*', '')
        try:
            st_month, st_day, end_month, end_day, \
                st_hour, end_hour, timestep = ap.split(' ')
            return cls(st_month, st_day, st_hour, end_month,
                       end_day, end_hour, int(timestep), is_leap_year)
        except Exception as e:
            raise ValueError(str(e))

    @classmethod
    def from_start_end_datetime(cls, start_datetime, end_datetime, timestep):
        """Create and AnalysisPeriod from start and end date objects.

        Args:
            start_datetime: A Ladybug DateTime object for the start of the period.
            end_datetime: A Ladybug DateTime object for the end of the period.
            timestep: An integer for the number of timesteps per hour. (Default: 1).
                Choose from: 1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60
        """
        assert start_datetime.leap_year == end_datetime.leap_year, \
            'Period start_datetime and end_datetime leap_year property must match'
        return cls(start_datetime.month, start_datetime.day, start_datetime.hour,
                   end_datetime.month, end_datetime.day, end_datetime.hour,
                   int(timestep), start_datetime.leap_year)

    @property
    def st_month(self):
        """Start month."""
        return self.st_time.month

    @property
    def st_day(self):
        """Start day."""
        return self.st_time.day

    @property
    def st_hour(self):
        """Start hour."""
        return self.st_time.hour

    @property
    def end_month(self):
        """End month."""
        return self.end_time.month

    @property
    def end_day(self):
        """End day."""
        return self.end_time.day

    @property
    def end_hour(self):
        """End hour."""
        return self.end_time.hour

    @property
    def timestep(self):
        """Timestep."""
        return self._timestep

    @property
    def is_leap_year(self):
        """A boolean to indicate if analysis period is for a leap year."""
        return self._is_leap_year

    @property
    def st_time(self):
        """Start datetime."""
        return self._st_time

    @property
    def end_time(self):
        """End datetime."""
        return self._end_time

    @property
    def datetimes(self):
        """A sorted list of hourly datetimes in this analysis period."""
        if self._timestamps_data is None:
            self._calculate_timestamps()
        return tuple(self._datetimes)

    @property
    def moys(self):
        """A sorted list of hourly minutes of year in this analysis period as integers.
        """
        if self._timestamps_data is None:
            self._calculate_timestamps()
        return tuple(self._timestamps_data)

    @property
    def hoys(self):
        """A sorted list of hours of year in this analysis period."""
        if self._timestamps_data is None:
            self._calculate_timestamps()
        return tuple(moy / 60.0 for moy in self._timestamps_data)

    @property
    def hoys_int(self):
        """A sorted list of hours of year in this analysis period as integers."""
        if self._timestamps_data is None:
            self._calculate_timestamps()
        return tuple(int(moy / 60.0) for moy in self._timestamps_data)

    @property
    def doys_int(self):
        """A sorted list of days of the year in this analysis period as integers."""
        if not self._is_reversed:
            return self._calc_daystamps(self.st_time, self.end_time)
        else:
            doys_st = self._calc_daystamps(
                self.st_time, DateTime.from_last_hour(self.is_leap_year))
            doys_end = self._calc_daystamps(
                DateTime.from_first_hour(self.is_leap_year), self.end_time)
            return doys_st + doys_end

    @property
    def months_int(self):
        """A sorted list of months of the year in this analysis period as integers."""
        if not self._is_reversed:
            return list(xrange(self.st_time.month, self.end_time.month + 1))
        else:
            months_st = list(xrange(self.st_time.month, 13))
            months_end = list(xrange(1, self.end_time.month + 1))
            return months_st + months_end

    @property
    def months_per_hour(self):
        """A list of tuples representing months per hour in this analysis period."""
        month_hour = []
        hour_range = xrange(self.st_hour, (self.end_hour + 1) * self.timestep)
        for month in self.months_int:
            month_hour.extend(
                [(month, int(hr / self.timestep),
                  int((hr % self.timestep) * (60 / self.timestep)))
                 for hr in hour_range])
        return month_hour

    @property
    def minute_intervals(self):
        """The number of minutes between each of the timesteps of the analysis period."""
        return self._minute_intervals

    @property
    def is_annual(self):
        """Check if an analysis period is annual."""
        return (self.st_month, self.st_day, self.st_hour, self.end_month,
                self.end_day, self.end_hour) == (1, 1, 0, 12, 31, 23)

    @property
    def is_reversed(self):
        """Return True if the analysis period is reversed.

        A reversed analysis period defines a period that starting month is after
        ending month (e.g DEC to JUN).
        """
        return self._is_reversed

    @property
    def is_overnight(self):
        """Return True if the analysis period is overnight.

        If an analysis period is overnight each segments of hours
        will be in two different days (e.g. from 9pm to 2am).
        """
        return self._is_overnight

    def is_possible_hour(self, hour):
        """Check if a float hour is a possible hour for this analysis period."""
        if hour > 23 and self.is_possible_hour(0):
            hour = int(hour)
        if not self._is_overnight:
            return self.st_time.hour <= hour <= self.end_time.hour
        else:
            return self.st_time.hour <= hour <= 23 or \
                0 <= hour <= self.end_time.hour

    def is_time_included(self, time):
        """Check if time is included in analysis period.

        Note that time filtering in Ladybug Tools is slightly different than "normal"
        filtering since start hour and end hour will be applied for every day.
        For instance 2/20 9am to 2/22 5pm means hour between 9-17 during 20, 21
        and 22 of Feb.

        Args:
            time: A DateTime to be tested

        Returns:
            A boolean. True if time is included in analysis period
        """
        if self._timestamps_data is None:
            self._calculate_timestamps()
        return time.moy in self._timestamps_data

    def duplicate(self):
        """Return a copy of the analysis period."""
        return self.__copy__()

    def __copy__(self):
        return AnalysisPeriod(self.st_month, self.st_day, self.st_hour,
                              self.end_month, self.end_day, self.end_hour,
                              self.timestep, self.is_leap_year)

    def to_dict(self):
        """Convert the analysis period to a dictionary."""
        return {
            'st_month': self.st_month,
            'st_day': self.st_day,
            'st_hour': self.st_hour,
            'end_month': self.end_month,
            'end_day': self.end_day,
            'end_hour': self.end_hour,
            'timestep': self.timestep,
            'is_leap_year': self.is_leap_year,
            'type': 'AnalysisPeriod'
        }

    def _calc_timestamps(self, st_time, end_time):
        """Calculate timesteps between start time and end time.

        Use this method only when start time month is before end time month.
        """
        # calculate based on minutes
        # I have to convert the object to DateTime because of how Dynamo
        # works: https://github.com/DynamoDS/Dynamo/issues/6683
        # Do not modify this line to datetime
        curr = datetime(st_time.year, st_time.month, st_time.day, st_time.hour,
                        st_time.minute, self.is_leap_year)
        end_time = datetime(end_time.year, end_time.month, end_time.day,
                            end_time.hour, end_time.minute, self.is_leap_year)

        while curr <= end_time:
            if self.is_possible_hour(curr.hour + (curr.minute / 60.0)):
                time = DateTime(curr.month, curr.day, curr.hour, curr.minute,
                                self.is_leap_year)
                self._timestamps_data.append(time.moy)
                self._datetimes.append(time)
            curr += self.minute_intervals

        if self.timestep != 1 and curr.hour == 23 and self.is_possible_hour(0):
            # This is for cases that timestep is more than one
            # and last hour of the day is part of the calculation
            curr = end_time
            for _ in list(xrange(self.timestep))[1:]:
                curr += self.minute_intervals
                time = DateTime(curr.month, curr.day, curr.hour, curr.minute,
                                self.is_leap_year)
                self._timestamps_data.append(time.moy)
                self._datetimes.append(time)

    def _calculate_timestamps(self):
        """Return a list of Ladybug DateTimes in this analysis period."""
        self._timestamps_data = []
        self._datetimes = []
        if not self._is_reversed:
            self._calc_timestamps(self.st_time, self.end_time)
        else:
            self._calc_timestamps(
                self.st_time, DateTime.from_last_hour(self.is_leap_year))
            self._calc_timestamps(
                DateTime.from_first_hour(self.is_leap_year), self.end_time)

    def _calc_daystamps(self, st_time, end_time):
        """Calculate days of the year between start time and end time.

        Use this method only when start time month is before end time month.
        """
        start_doy = sum(self._num_of_days_each_month[:st_time.month - 1]) + \
            st_time.day
        end_doy = sum(self._num_of_days_each_month[:end_time.month - 1]) + \
            end_time.day + 1
        return list(range(start_doy, end_doy))

    def __len__(self):
        """Number of steps in the analysis period.

        The length will be number of hours * timestep.
        """
        if self.st_hour == 1 and self.end_hour == 23:  # use fast method
            if not self._is_reversed:
                return (self.end_time.int_hoy + 1 - self.st_time.int_hoy) * self.timestep
            else:
                first = DateTime.from_last_hour(self.is_leap_year).int_hoy - \
                    self.st_time.int_hoy
                second = self.end_time.int_hoy - \
                    DateTime.from_first_hour(self.is_leap_year).int_hoy
                return ((first + second + 2) * self.timestep)
        else:
            if self._timestamps_data is None:
                self._calculate_timestamps()
            return len(self._timestamps_data)

    def __str__(self):
        """Return analysis period as a string."""
        return self.__repr__()

    def ToString(self):
        """Overwrite .NET representation."""
        return self.__repr__()

    def __repr__(self):
        """Return analysis period as a string."""
        base_string = "%s/%s to %s/%s between %s and %s @%d"
        if self.is_leap_year:
            base_string += '*'

        return base_string % \
            (self.st_time.month, self.st_time.day,
             self.end_time.month, self.end_time.day,
             self.st_time.hour, self.end_time.hour,
             self.timestep)

    def __key(self):
        return(self.st_time, self.end_time, self.timestep, self.is_leap_year)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, AnalysisPeriod) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)
