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
            HOY: A float value 0 <= and < 8760
        """
        # numOfDaysUntilMonth = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]
        numOfHoursUntilMonth = [0, 744, 1416, 2160, 2880, 3624, 4344, 5088,
                                5832, 6552, 7296, 8016, 8760]

        HOY += 1

        # find month
        for monthCount in range(12):
            if HOY <= numOfHoursUntilMonth[monthCount + 1]:
                month = monthCount + 1
                break
        try:
            day = int((HOY - numOfHoursUntilMonth[month - 1]) / 24) + 1
        except UnboundLocalError:
            raise ValueError(
                "HOY must be between 0..8759. Invalid input %d" % (HOY - 1)
            )
        else:
            hour = HOY % 24 - 1

            if HOY % 24 == 0:
                hour = 23
                day -= 1

            minute = int((hour - int(hour)) * 60)
            return cls(month, day, int(hour), minute)

    @classmethod
    def fromMOY(cls, MOY):
        """Create Ladybug Datetime from a minute of the year.

        Args:
            MOY: An integer value 0 <= and < 525600
        """
        return cls.fromHOY(MOY / 60.0)

    @classmethod
    def fromDateTimeString(cls, datetimeString):
        """Create Ladybug DateTime from a LBDateTime string.

        Usage:

            dt = LBDateTime.fromDateTimeString("31 Dec 2015 at 12:00")
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
        return (self.DOY - 1) * 24 + self.hour

    def __str__(self):
        """Return date time as a string."""
        return self.strftime('%d %b at %H:%M')

    def ToString(self):
        """Overwrite .NET ToString."""
        self.__str__()

    def __repr__(self):
        """Return date time as a string."""
        self.__str__()
