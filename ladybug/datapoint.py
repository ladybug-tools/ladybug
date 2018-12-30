# coding=utf-8
"""Ladybug data collection."""
from __future__ import division

from .dt import DateTime


class DataPointBase(object):
    """Base type for data.

    Attributes:
        value: Input value
        datetime: Date time data for this value (Default: None)
        standard: 'SI' or 'IP' (Default: 'SI')
        nickname: Optional nickname for data (e.g. Dew Point Temperature)
    """

    __slots__ = ('_standard', '_value', 'datetime', 'nickname')

    minimum = float('-inf')
    maximum = float('+inf')
    value_type = None
    unitSI = None
    unitIP = None
    missing = None
    mute = False  # print warnings for missing data

    def __init__(self, value, datetime=None, standard=None, nickname=None):
        """Init DataType."""
        self.nickname = nickname
        self.standard = standard
        self.datetime = datetime
        self.value = value

    # TODO: Add support for type
    @classmethod
    def from_json(cls, data):
        """Create a data point from a dictionary.

        Args:
            json_data: Data as a dictionary.
                {
                    "value": A number or a string,
                    "standard": SI/IP,
                    "datetime": {}, // A ladybug datetime schema
                    "nickname": A string for nickname
                }
        """
        # check for value to be available
        assert 'value' in data, 'Required keyword "value" is missing!'

        if 'datetime' not in data:
            data['dateTime'] = {}

        if 'standard' not in data:
            data['standard'] = 'SI'

        if 'nickname' not in data:
            data['nickname'] = None

        datetime = DateTime.from_json(data['datetime'])
        return cls(data['value'], datetime, data['standard'], data['nickname'])

    @property
    def value(self):
        """Get/set value."""
        return self._value

    @value.setter
    def value(self, v):
        """Set value."""
        if not self.value_type:
            self._value = v
        else:
            try:
                if self.value_type is str:
                    _v = str(v)
                else:
                    _v = self.value_type(v)
            except Exception:
                raise ValueError(
                    "Failed to convert {} to {}".format(v, self.value_type))
            else:
                self._value = _v
                self.is_in_range(_v, True)

    @property
    def standard(self):
        """standard SI/IP"""
        return self._standard

    @standard.setter
    def standard(self, value):
        value = value or 'SI'
        if value not in ('SI', 'IP'):
            raise ValueError('Invalid standard: {}. Choose SI or IP.'.format(value))
        self._standard = value

    @property
    def unit(self):
        """Return current Unit."""
        if not self.standard:
            return None
        return self.unitSI if self.standard == 'SI' else \
            self.unitIP

    @property
    def to_ip(self):
        """Write a static method that converts a value from SI to IP."""
        raise NotImplementedError(
            'to_ip is not implemented to %s' % self.__class__.__name__
        )

    @property
    def to_si(self):
        """Write a static method that converts a value from IP to SI."""
        raise NotImplementedError(
            'to_si is not implemented to %s' % self.__class__.__name__
        )

    def convert_to_si(self):
        """Change value to SI.

        To only get the value in SI use to_si property.
        """
        if not self.standard:
            raise Exception("Failed to convert to SI. "
                            "Current system is unknown.")

        if self.standard == 'SI':
            return
        else:
            self.standard = 'SI'
            self.value = self.to_si

    def convert_to_ip(self):
        """change value to IP.

        To only get the value in IP use to_ip property.
        """
        if not self.standard:
            raise Exception("Failed to convert to IP. "
                            "Current system is unknown.")

        if self.standard == 'IP':
            return
        else:
            self.standard = 'IP'
            self.value = self.to_ip

    def _is_missed_data(self, v):
        """Check if the value is missed data."""
        _isMissed = v == self.missing

        if not self.mute and _isMissed:
            print("{} value is missing!".format(
                self.__class__.__name__ if not self.nickname else self.nickname
            ))

        return _isMissed

    def is_in_range(self, value, raise_exception=False):
        """check if the value is in range."""
        if not self.standard:
            return True

        if self._is_missed_data(self):
            return True

        _isInRange = self.minimum <= value <= self.maximum \
            if self.standard == 'SI' \
            else self.to_ip(self.minimum) <= value <= self.to_ip(self.maximum)

        if _isInRange or not raise_exception:
            return _isInRange
        else:
            raise ValueError(
                '{0} should be between {1} and {2}'.format(
                    self.__class__.__name__, self.minimum, self.maximum
                )
            )

    def to_json(self):
        "Get data point as a json object"
        return {
            'value': self.value,
            'datetime': self.datetime.to_json() if self.datetime else {},
            'standard': self.standard,
            'nickname': self.nickname,
            'type': self.__class__.__name__
        }

    def ToString(self):
        """Overwrite .NET representation."""
        return self.__repr__()

    def __str__(self):
        """Return full information."""
        # Temperature: 21C
        return "{}{}{}".format(
            self.__repr__(),
            self.unit if self.unit else "",
            " at %s" % self.datetime if self.datetime else "")

    def __repr__(self):
        """Return string representation."""
        return str(self.value)

    def __int__(self):
        """Return integer value."""
        try:
            return int(self.value)
        except ValueError:
            raise ValueError(
                "Failed to convert {} to an integer.".format(self.value)
            )

    def __float__(self):
        """Return float value."""
        return float(self.value)

    def __eq__(self, other):
        return self.value == float(other)

    def __ne__(self, other):
        return self.value != float(other)

    def __lt__(self, other):
        return self.value < other

    def __gt__(self, other):
        return self.value > other

    def __le__(self, other):
        return self.value <= other

    def __ge__(self, other):
        return self.value >= other

    def __add__(self, other):
        return self.value + other

    def __sub__(self, other):
        return self.value - other

    def __mul__(self, other):
        return self.value * other

    def __floordiv__(self, other):
        return self.value // other

    def __div__(self, other):
        return self.value / other

    def __mod__(self, other):
        return self.value % other

    def __pow__(self, other):
        return self.value ** other

    def __radd__(self, other):
        return self.__add__(other)

    def __rsub__(self, other):
        return other - self.value

    def __rmul__(self, other):
        return self.__mul__(other)

    def __rfloordiv__(self, other):
        return other // self.value

    def __rdiv__(self, other):
        return other / self.value

    def __rmod__(self, other):
        return other % self.value

    def __rpow__(self, other):
        return other ** self.value


class DataPoint(DataPointBase):
    """A single Ladybug data point.

    Attributes:
        value: Input value
        datetime: Date time data for this value (Default: None)
        standard: 'SI' or 'IP' (Default: 'SI')
        nickname: Optional nickname for data (e.g. Dew Point Temperature)
    """

    __slots__ = ()
    minimum = float('-inf')
    maximum = float('+inf')
    value_type = None
    unitSI = None
    unitIP = None
    missing = None

    def __init__(self, value, datetime=None, standard='SI', nickname=None):
        """Init class."""
        DataPointBase.__init__(self, value, datetime, standard, nickname)

    @classmethod
    def from_data(cls, value):
        """Try to create a DataPoint from input data."""
        if hasattr(value, 'isData'):
            return value

        try:
            return cls(value)
        except Exception as e:
            raise ValueError(
                "Failed to create a DataPoint from %s!\n%s" % (value, e))

    @property
    def isDataPoint(self):
        """Return True if Ladybug data point."""
        return True
