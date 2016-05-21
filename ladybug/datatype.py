"""Ladybug data types."""
from abc import ABCMeta, abstractmethod


class DataTypeBase(object):
    """Base type for data."""

    __metaclass__ = ABCMeta
    __slots__ = ('standard',)

    def __init__(self, standard=None):
        """Init DataType."""
        self.standard = standard

    @property
    def unit(self):
        """Return current Unit."""
        if not self.standard:
            return None
        return self.unitSI if self.standard == 'SI' else \
            self.unitIP

    @abstractmethod
    def toIP(self):
        """Write a static method that converts a value from SI to IP."""
        pass

    @abstractmethod
    def toSI(self):
        """Write a static method that converts a value from IP to SI."""
        pass

    def convertToSI(self):
        """Change value to SI."""
        if self.standard == 'SI':
            return
        else:
            self.standard = 'SI'
            self.value = self.toSI(self.value)

    def convertToIP(self):
        """change value to IP."""
        if self.standard == 'IP':
            return
        else:
            self.standard = 'IP'
            self.value = self.toIP(self.value)

    def isInRange(self, value, raiseException=False):
        """check if the value is in range."""
        _isInRange = self.minimum <= value <= self.maximum \
            if self.standard == 'SI' \
            else self.toIP(self.minimum) <= value <= self.toIP(self.maximum)

        if _isInRange or not raiseException:
            return _isInRange
        else:
            raise ValueError(
                'Input should be between {0} and {1}'.format(self.minimum,
                                                             self.maximum)
            )

    def fullString(self):
        """Return value and units."""
        return "{0} {1}".format(self.__repr__(),
                                self.unit if self.unit else "")

    def ToString(self):
        """Overwrite .NET representation."""
        return self.__repr__()

    def __str__(self):
        """Return string representation."""
        return self.__repr__()

    def __repr__(self):
        """Return string representation."""
        return str(self.value)


# TODO: Add methods for toKelvin
class Temperature(DataTypeBase):
    """Base type for temperature.

    Attributes:
        value: Input value
        standard: 'SI' or 'IP' (Default: 'SI')
    """

    minimum = float('-inf')
    maximum = float('inf')
    valueType = float
    unitSI = 'C'
    unitIP = 'F'
    __slots__ = ('__value',)

    def __init__(self, value, standard='SI'):
        """Init class."""
        DataTypeBase.__init__(self, standard)
        self.value = value

    @property
    def value(self):
        """Get/set value."""
        return self.__value

    @value.setter
    def value(self, v):
        """Set value."""
        self.isInRange(map(self.valueType, (v,))[0], True)
        self.__value = v

    @staticmethod
    def toIP(value):
        """Return the value in F assuming input value is in C."""
        return value * 9 / 5 + 32

    @staticmethod
    def toSI(value):
        """Return the value in C assuming input value is in F."""
        return (value - 32) * 5 / 9


class DryBulbTemperature(Temperature):
    """Dry bulb temperature.

    Attributes:
        value: Input value
        standard: 'SI' or 'IP' (Default: 'SI')
    """

    minimum = -70
    maximum = 70
    __slots__ = ()

    def __init__(self, value, standard='SI'):
        """Init class."""
        Temperature.__init__(self, value, standard)


class RelativeHumidity(DataTypeBase):
    """Relative Humidity.

    Attributes:
        value: Input value
        standard: 'SI' or 'IP' (Default: 'SI')
    """

    minimum = 0
    maximum = 100
    valueType = float
    unitSI = '%'
    unitIP = '%'
    __slots__ = ('__value',)

    def __init__(self, value, standard='SI'):
        """Init class."""
        DataTypeBase.__init__(self, standard)
        self.value = value

    @property
    def value(self):
        """Get/set value."""
        return self.__value

    @value.setter
    def value(self, v):
        """Set value."""
        self.isInRange(map(self.valueType, (v,))[0], True)
        self.__value = v

    @staticmethod
    def toIP(value):
        """Return the value in IP assuming input value is in SI."""
        return value

    @staticmethod
    def toSI(value):
        """Return the value in SI assuming input value is in IP."""
        return value
