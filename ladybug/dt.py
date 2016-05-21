"""Ladybug datetime."""
from datetime import datetime


class LBDateTime(datetime):
    """Create Ladybug Date time.

    Args:
        month: A value for month between 1-12. (Defualt: 1)
        day: A value for day between 1-31. (Defualt: 1)
        hour: A value for hour between 0-23. (Defualt: 0)
        minute: A value for month between 1-59. (Defualt: 0)
    """

    __slots__ = ()

    def __new__(cls, month=1, day=1, hour=0, minute=0):
        """Create Ladybug datetime."""
        return datetime.__new__(cls, 2015, month, day, hour, minute)

    @classmethod
    def fromHOY(cls, HOY):
        """Create Ladybug Datetime from an hour of the year.

        Args:
            HOY: A float value between 0..8760
        """
        numOfDaysUntilMonth = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]
        numOfHoursUntilMonth = [24 * numOfDay for numOfDay in numOfDaysUntilMonth]

        # find month
        for monthCount in range(12):
            if HOY <= numOfHoursUntilMonth[monthCount + 1]:
                month = monthCount + 1
                break

        day = int((HOY - numOfHoursUntilMonth[month - 1]) / 24) + 1
        hour = int(HOY % 24)
        minute = (hour - int(hour)) * 60

        return cls(month, day, hour, minute)

    @classmethod
    def fromDateTimeString(cls, datetimeString):
        """Create Ladybug DateTime from a LBDateTime string.

        Usage:

            dt = ("31 Dec 2015 at 12:00")
        """
        dt = datetime.strptime(datetimeString, '%d %b %Y at %H:%M')
        return cls(dt.month, dt.day, dt.hour, dt.minute)

    @property
    def DOY(self):
        """Calculate day of the year for this date time."""
        return self.timetuple().tm_yday

    @property
    def HOY(self):
        """Calculate hour of the year for this date time."""
        return (self.DOY - 1) * 24 + self.floatHour

    @property
    def MOY(self):
        """Calculate minute of the year for this date time."""
        return self.intHOY * 60 + self.minute

    @property
    def floatHour(self):
        """Get hour and minute as a float value (e.g. 6.25 for 6:15)."""
        return self.hour + self.minute / 60.0

    @property
    def intHOY(self):
        """Calculate hour of the year for this date time as an integer.

        This output assumes the minute is 0.
        """
        return (self.DOY - 1) * 24 + self.hour

    @property
    def MOY(self):
        """Calculate minute of the year for this date time."""
        return self.intHOY * 60 + self.minute  # minute of the year

    def __str__(self):
        """Return date time as a string."""
        return self.strftime('%d %b at %H:%M')

    def ToString(self):
        """Overwrite .NET ToString."""
        self.__str__()

    def __repr__(self):
        """Return date time as a string."""
        self.__str__()
