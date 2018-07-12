"""Ladybug datetime."""
# coding=utf-8
from datetime import datetime


class DateTime(datetime):
    """Create Ladybug Date time.

    Args:
        month: A value for month between 1-12 (Defualt: 1).
        day: A value for day between 1-31 (Defualt: 1).
        hour: A value for hour between 0-23 (Defualt: 0).
        minute: A value for month between 0-59 (Defualt: 0).
        leap_year: A boolean to indicate if datetime is for a leap year
            (Default: False).
    """

    __slots__ = ()

    def __new__(cls, month=1, day=1, hour=0, minute=0, leap_year=False):
        """Create Ladybug datetime.

        Args:
            month: A value for month between 1-12 (Defualt: 1).
            day: A value for day between 1-31 (Defualt: 1).
            hour: A value for hour between 0-23 (Defualt: 0).
            minute: A value for month between 0-59 (Defualt: 0).
            leap_year: A boolean to indicate if datetime is for a leap year
                (Default: False).
        """
        year = 2016 if leap_year else 2017
        hour, minute = cls._calculate_hour_and_minute(hour + minute / 60.0)
        try:
            return datetime.__new__(cls, year, month, day, hour, minute)
        except ValueError as e:
            raise ValueError("{}:\n\t({}/{}@{}:{})(m/d@h:m)".format(
                e, month, day, hour, minute
            ))

    @classmethod
    def from_json(cls, data):
        """Creat datetime from a dictionary.

        Args:
            data: {
                'month': A value for month between 1-12. (Defualt: 1)
                'day': A value for day between 1-31. (Defualt: 1)
                'hour': A value for hour between 0-23. (Defualt: 0)
                'minute': A value for month between 0-59. (Defualt: 0)
            }
        """
        if 'month' not in data:
            data['month'] = 1

        if 'day' not in data:
            data['day'] = 1

        if 'hour' not in data:
            data['hour'] = 0

        if 'minute' not in data:
            data['minute'] = 0

        if 'year' not in data:
            data['year'] = 2017

        leap_year = True if int(data['year']) == 2016 else False
        return cls(data['month'], data['day'], data['hour'], data['minute'], leap_year)

    @classmethod
    def from_hoy(cls, hoy, leap_year=False):
        """Create Ladybug Datetime from an hour of the year.

        Args:
            hoy: A float value 0 <= and < 8760
        """
        return cls.from_moy(round(hoy * 60), leap_year)

    @classmethod
    def from_moy(cls, moy, leap_year=False):
        """Create Ladybug Datetime from a minute of the year.

        Args:
            moy: An integer value 0 <= and < 525600
        """
        if not leap_year:
            num_of_minutes_until_month = (0, 44640, 84960, 129600, 172800, 217440,
                                          260640, 305280, 349920, 393120, 437760,
                                          480960, 525600)
        else:
            num_of_minutes_until_month = (0, 44640, 84960 + 1440, 129600 + 1440,
                                          172800 + 1440, 217440 + 1440, 260640 + 1440,
                                          305280 + 1440, 349920 + 1440, 393120 + 1440,
                                          437760 + 1440, 480960 + 1440, 525600 + 1440)
        # find month
        for monthCount in range(12):
            if int(moy) < num_of_minutes_until_month[monthCount + 1]:
                month = monthCount + 1
                break
        try:
            day = int((moy - num_of_minutes_until_month[month - 1]) / (60 * 24)) + 1
        except UnboundLocalError:
            raise ValueError(
                "moy must be positive and smaller than 525600. Invalid input %d" % (moy)
            )
        else:
            hour = int((moy / 60) % 24)
            minute = int(moy % 60)

            return cls(month, day, hour, minute, leap_year)

    @classmethod
    def from_date_time_string(cls, datetime_string, leap_year=False):
        """Create Ladybug DateTime from a DateTime string.

        Usage:

            dt = DateTime.from_date_time_string("31 Dec 12:00")
        """
        dt = datetime.strptime(datetime_string, '%d %b %H:%M')
        return cls(dt.month, dt.day, dt.hour, dt.minute, leap_year)

    @property
    def isDateTime(self):
        """Check if data is ladybug data."""
        return True

    @property
    def doy(self):
        """Calculate day of the year for this date time."""
        return self.timetuple().tm_yday

    @property
    def hoy(self):
        """Calculate hour of the year for this date time."""
        return (self.doy - 1) * 24 + self.float_hour

    @property
    def moy(self):
        """Calculate minute of the year for this date time."""
        return self.int_hoy * 60 + self.minute  # minute of the year

    @property
    def float_hour(self):
        """Get hour and minute as a float value (e.g. 6.25 for 6:15)."""
        return self.hour + self.minute / 60.0

    @property
    def int_hoy(self):
        """Calculate hour of the year for this date time as an integer.

        This output assumes the minute is 0.
        """
        return (self.doy - 1) * 24 + self.hour

    @staticmethod
    def _calculate_hour_and_minute(float_hour):
        """Calculate hour and minutes as integers from a float hour."""
        hour, minute = int(float_hour), int(round((float_hour - int(float_hour)) * 60))
        if minute == 60:
            return hour + 1, 0
        else:
            return hour, minute

    def add_minute(self, minute):
        """Create a new DateTime after the minutes are added.

        Args:
            minute: An integer value for minutes.
        """
        _moy = self.moy + int(minute)
        return self.__class__.from_moy(_moy)

    def sub_minute(self, minute):
        """Create a new DateTime after the minutes are subtracted.

        Args:
            minute: An integer value for the number of minutes.
        """
        return self.add_minute(-minute)

    def add_hour(self, hour):
        """Create a new DateTime from this time + timedelta.

        Args:
            hours: A float value in hours (e.g. .5 = half an hour)
        """
        return self.add_minute(hour * 60)

    def sub_hour(self, hour):
        """Create a new DateTime from this time - timedelta.

        Args:
            hour: A float value in hours (e.g. .5 is half an hour and 2 is two hours).
        """
        return self.add_hour(-hour)

    def to_simple_string(self, separator="_"):
        """Return a simplified string."""
        return self.strftime('%d_%b_%H_%M').replace("_", separator)

    def __str__(self):
        """Return date time as a string."""
        return self.strftime('%d %b %H:%M')

    def to_json(self):
        """Get date time as a dictionary."""
        return {'year': self.year,
                'month': self.month,
                'day': self.day,
                'hour': self.hour,
                'minute': self.minute}

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__str__()

    def __repr__(self):
        """Return date time as a string."""
        return self.__str__()
