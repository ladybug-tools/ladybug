# coding=utf-8
"""Ladybug analysis period class."""
from .dt import DateTime
from datetime import datetime, timedelta


class AnalysisPeriod(object):
    """Ladybug Analysis Period.

    A continuous analysis period between two days of the year between certain hours.

    Attributes:
        st_month: An integer between 1-12 for starting month (default = 1)
        st_day: An integer between 1-31 for starting day (default = 1).
                Note that some months are shorter than 31 days.
        st_hour: An integer between 0-23 for starting hour (default = 0)
        end_month: An integer between 1-12 for ending month (default = 12)
        end_day: An integer between 1-31 for ending day (default = 31)
                Note that some months are shorter than 31 days.
        end_hour: An integer between 0-23 for ending hour (default = 23)
        timestep: An integer number from 1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60

    Class methods:
        from_string: Create an Analysis Period object from an analysis period string.
            %s/%s to %s/%s between %s to %s @%s

    Properties:
        isAnalysisPeriod: Always return True. Useful for type checking.
        datetimes: Sorted list of datetimes in this analysis period.
        hoys: A sorted list of hours of year in this analysis period.
        int_hoys: A sorted list of hours of year values in this analysis period as
            integers.
        is_annual: Check if an analysis period is annual.
        is_overnight: If an analysis perido is not overnight each segments of hours
            will be in the same day (self.st_time.hoy < self.end_time.hoy)
        is_reversed: A reversed analysis period defines a period that starting month
            is after ending month (e.g DEC to JUN)
    """

    VALIDTIMESTEPS = {1: 60, 2: 30, 3: 20, 4: 15, 5: 12,
                      6: 10, 10: 6, 12: 5, 15: 4, 20: 3, 30: 2, 60: 1}
    NUMOFDAYSEACHMONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    NUMOFDAYSEACHMONTHLEAP = (31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

    # TODO: handle timestep between 1-60
    def __init__(self, st_month=1, st_day=1, st_hour=0, end_month=12,
                 end_day=31, end_hour=23, timestep=1, is_leap_year=False):
        """Init an analysis period.

        A continuous analysis period between two days of the year between certain hours

        Args:
            st_month: An integer between 1-12 for starting month (default = 1)
            st_day: An integer between 1-31 for starting day (default = 1).
                    Note that some months are shorter than 31 days.
            st_hour: An integer between 0-23 for starting hour (default = 0)
            end_month: An integer between 1-12 for ending month (default = 12)
            end_day: An integer between 1-31 for ending day (default = 31)
                    Note that some months are shorter than 31 days.
            end_hour: An integer between 0-23 for ending hour (default = 23)
            timestep: An integer number from 1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60
        """

        st_month = st_month or 1
        st_day = st_day or 1
        st_hour = st_hour or 0
        end_month = end_month or 12
        end_day = end_day or 31
        end_hour = end_hour or 23
        timestep = timestep or 1
        self._is_leap_year = is_leap_year or False

        # calculate start time and end time
        self.st_time = DateTime(int(st_month), int(st_day), int(st_hour),
                                leap_year=is_leap_year)

        num_of_days_each_month = self.NUMOFDAYSEACHMONTH if not self.is_leap_year \
            else self.NUMOFDAYSEACHMONTHLEAP
        if int(end_day) > num_of_days_each_month[int(end_month) - 1]:
            end = num_of_days_each_month[end_month - 1]
            print("Updated end_day from {} to {}".format(end_day, end))
            end_day = end

        self.end_time = DateTime(int(end_month), int(end_day), int(end_hour),
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

        # calculate time stamp
        self.timestep = timestep
        self.minute_intervals = timedelta(1 / (24.0 * self.timestep))
        # calculate timestamps and hours_of_year
        # A dictionary for datetimes. Key values will be minute of year
        self._timestamps_data = []
        self._calculate_timestamps()

    @classmethod
    def from_json(cls, data):
        """Create an analysis period from a dictionary.
        Args:
            data: {
            st_month: An integer between 1-12 for starting month (default = 1)
            st_day: An integer between 1-31 for starting day (default = 1).
                    Note that some months are shorter than 31 days.
            st_hour: An integer between 0-23 for starting hour (default = 0)
            end_month: An integer between 1-12 for ending month (default = 12)
            end_day: An integer between 1-31 for ending day (default = 31)
                    Note that some months are shorter than 31 days.
            end_hour: An integer between 0-23 for ending hour (default = 23)
            timestep: An integer number from 1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60
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
    def from_analysis_period(cls, analysis_period=None):
        """Create and AnalysisPeriod from an analysis period.

        This method is useful to be called from inside Grasshopper or Dynamo
        """
        if not analysis_period:
            return cls()
        elif hasattr(analysis_period, 'isAnalysisPeriod'):
            return analysis_period
        elif isinstance(analysis_period, str):
            try:
                return cls.from_string(analysis_period)
            except Exception as e:
                raise ValueError(
                    "{} is not convertable to an AnalysisPeriod: {}".format(
                        analysis_period, e)
                )

    @classmethod
    def from_string(cls, analysis_period_string):
        """Create an Analysis Period object from an analysis period string.

            %s/%s to %s/%s between %s to %s @%s
        """
        # %s/%s to %s/%s between %s to %s @%s*
        is_leap_year = True if analysis_period_string.strip()[-1] == '*' else False
        ap = analysis_period_string.lower().replace(' ', '') \
            .replace('to', ' ') \
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

    @property
    def isAnalysisPeriod(self):
        """Return True."""
        return True

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
        """Start month."""
        return self.end_time.month

    @property
    def end_day(self):
        """Start day."""
        return self.end_time.day

    @property
    def end_hour(self):
        """Start hour."""
        return self.end_time.hour

    @property
    def is_leap_year(self):
        """A boolean to indicate if analysis period is for a leap year."""
        return self._is_leap_year

    @property
    def datetimes(self):
        """A sorted list of datetimes in this analysis period."""
        # sort dictionary based on key values (minute of the year)
        return tuple(DateTime.from_moy(moy, self.is_leap_year)
                     for moy in self._timestamps_data)

    @property
    def hoys(self):
        """A sorted list of hours of year in this analysis period."""
        return tuple(moy / 60.0 for moy in self._timestamps_data)

    @property
    def hoys_int(self):
        """A sorted list of hours of year values in this analysis period as integers."""
        return tuple(int(moy / 60.0) for moy in self._timestamps_data)

    @property
    def is_annual(self):
        """Check if an analysis period is annual."""
        num_of_days = 8760 if not self.is_leap_year else 8760 + 24
        return True if len(self._timestamps_data) / self.timestep == num_of_days \
            else False

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

        If an analysis perido is overnight each segments of hours
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
            curr += self.minute_intervals

        if self.timestep != 1 and curr.hour == 23 and self.is_possible_hour(0):
            # This is for cases that timestep is more than one
            # and last hour of the day is part of the calculation
            curr = end_time
            for i in range(self.timestep)[1:]:
                curr += self.minute_intervals
                time = DateTime(curr.month, curr.day, curr.hour, curr.minute,
                                self.is_leap_year)
                self._timestamps_data.append(time.moy)

    def _calculate_timestamps(self):
        """Return a list of Ladybug DateTime in this analysis period."""
        if not self._is_reversed:
            self._calc_timestamps(self.st_time, self.end_time)
        else:
            self._calc_timestamps(self.st_time, DateTime.from_hoy(8759))
            self._calc_timestamps(DateTime.from_hoy(0), self.end_time)

    def is_time_included(self, time):
        """Check if time is included in analysis period.

        Return True if time is inside this analysis period,
        otherwise return False

        Args:
            time: A DateTime to be tested

        Returns:
            A boolean. True if time is included in analysis period
        """
        # time filtering in Ladybug and honeybee is slightly different since
        # start hour and end hour will be applied for every day.
        # For instance 2/20 9am to 2/22 5pm means hour between 9-17
        # during 20, 21 and 22 of Feb.
        return time.moy in self._timestamps_data

    def to_json(self):
        """Convert the analysis period to a dictionary."""
        return {
            'st_month': self.st_month,
            'st_day': self.st_day,
            'st_hour': self.st_hour,
            'end_month': self.end_month,
            'end_day': self.end_day,
            'end_hour': self.end_hour,
            'timestep': self.timestep,
            'is_leap_year': self.is_leap_year
        }

    def ToString(self):
        """Overwrite .NET representation."""
        return self.__repr__()

    def __len__(self):
        """Number of hours of the year.

        The length will be number of hours * timestep.
        """
        return len(self.hoys)

    def __str__(self):
        """Return analysis period as a string."""
        return self.__repr__()

    def __repr__(self):
        """Return analysis period as a string."""
        base_string = "%s/%s to %s/%s between %s to %s @%d"
        if self.is_leap_year:
            base_string += '*'

        return base_string % \
            (self.st_time.month, self.st_time.day,
             self.end_time.month, self.end_time.day,
             self.st_time.hour, self.end_time.hour,
             self.timestep)
