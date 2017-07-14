"""Ladybug datetime."""
from datetime import datetime


class DateTime(datetime):
    """Create Ladybug Date time.

    Args:
        month: A value for month between 1-12. (Defualt: 1)
        day: A value for day between 1-31. (Defualt: 1)
        hour: A value for hour between 0-23. (Defualt: 0)
        minute: A value for month between 0-59. (Defualt: 0)
    """

    __slots__ = ()

    def __new__(cls, month=1, day=1, hour=0, minute=0):
        """Create Ladybug datetime."""
        hour, minute = cls._calculateHourAndMinute(hour + minute / 60.0)
        try:
            return datetime.__new__(cls, 2015, month, day, hour, minute)
        except ValueError as e:
            raise ValueError("{}:\n\t({}/{}@{}:{})(m/d@h:m)".format(
                e, month, day, hour, minute
            ))

    @classmethod
    def fromHoy(cls, hoy):
        """Create Ladybug Datetime from an hour of the year.

        Args:
            hoy: A float value 0 <= and < 8760
        """
        return cls.fromMoy(round(hoy * 60))

    @classmethod
    def fromMoy(cls, moy):
        """Create Ladybug Datetime from a minute of the year.

        Args:
            moy: An integer value 0 <= and < 525600
        """
        numOfMinutesUntilMonth = (0, 44640, 84960, 129600, 172800, 217440,
                                  260640, 305280, 349920, 393120, 437760,
                                  480960, 525600)

        # find month
        for monthCount in range(12):
            if int(moy) < numOfMinutesUntilMonth[monthCount + 1]:
                month = monthCount + 1
                break
        try:
            day = int((moy - numOfMinutesUntilMonth[month - 1]) / (60 * 24)) + 1
        except UnboundLocalError:
            raise ValueError(
                "moy must be positive and smaller than 525600. Invalid input %d" % (moy)
            )
        else:
            hour = int((moy / 60) % 24)
            minute = int(moy % 60)

            return cls(month, day, hour, minute)

    @classmethod
    def fromDateTimeString(cls, datetimeString):
        """Create Ladybug DateTime from a DateTime string.

        Usage:

            dt = DateTime.fromDateTimeString("31 Dec 12:00")
        """
        dt = datetime.strptime(datetimeString, '%d %b %H:%M')
        return cls(dt.month, dt.day, dt.hour, dt.minute)

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
        return (self.doy - 1) * 24 + self.floatHour

    @property
    def moy(self):
        """Calculate minute of the year for this date time."""
        return self.intHOY * 60 + self.minute  # minute of the year

    @property
    def floatHour(self):
        """Get hour and minute as a float value (e.g. 6.25 for 6:15)."""
        return self.hour + self.minute / 60.0

    @property
    def intHOY(self):
        """Calculate hour of the year for this date time as an integer.

        This output assumes the minute is 0.
        """
        return (self.doy - 1) * 24 + self.hour

    @staticmethod
    def _calculateHourAndMinute(floatHour):
        """Calculate hour and minutes as integers from a float hour."""
        hour, minute = int(floatHour), int(round((floatHour - int(floatHour)) * 60))
        if minute == 60:
            return hour + 1, 0
        else:
            return hour, minute

    def addminutes(self, minutes):
        """Create a new DateTime after the minutes are added.

        minutes: An integer value for minutes.
        """
        _moy = self.moy + int(minutes)
        return self.__class__.fromMoy(_moy)

    def subminutes(self, minutes):
        """Create a new DateTime after the minutes are subtracted.

        minutes: An integer value for the number of minutes.
        """
        return self.addminutes(-minutes)

    def addhour(self, hour):
        """Create a new DateTime from this time + timedelta.

        hours: A float value in hours (e.g. .5 = half an hour)
        """
        return self.addminutes((self.hoy + hour) * 60)

    def subhour(self, hour):
        """Create a new DateTime from this time - timedelta.

        hour: A float value in hours (e.g. .5 is half an hour and 2 is two hours).
        """
        return self.addhour(-hour)

    def toSimpleString(self, separator="_"):
        """Return a simplified string."""
        return self.strftime('%d_%b_%H_%M').replace("_", separator)

    def __str__(self):
        """Return date time as a string."""
        return self.strftime('%d %b %H:%M')

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__str__()

    def __repr__(self):
        """Return date time as a string."""
        return self.__str__()
