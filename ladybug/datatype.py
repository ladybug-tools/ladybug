# coding=utf-8
"""Ladybug data types."""
# from abc import ABCMeta, abstractmethod
import math
from .euclid import Vector3
from .dt import DateTime

PI = math.pi


class DataTypeBase(object):
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


class DataPoint(DataTypeBase):
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
        DataTypeBase.__init__(self, value, datetime, standard, nickname)

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


# TODO: Add methods for toKelvin for temperature
# TODO: Add toAtmospheres, toBars, toPsi, toInWater for pressure
class Temperature(DataPoint):
    """Base type for temperature.

    Attributes:
        value: Input value
        datetime: Date time data for this value (Default: None)
        standard: 'SI' or 'IP' (Default: 'SI')
        nickname: Optional nickname for data (e.g. Dew Point Temperature)
    """

    __slots__ = ()
    minimum = float('-inf')
    maximum = float('inf')
    missing = 99.9
    value_type = float
    unitSI = 'C'
    unitIP = 'F'

    def __init__(self, value, datetime=None, standard='SI', nickname=None):
        """Init class."""
        DataPoint.__init__(self, value, datetime, standard, nickname)

    @property
    def to_ip(self):
        """Return the value in F assuming input value is in C."""
        return self.value * 9 / 5 + 32

    @property
    def to_si(self):
        """Return the value in C assuming input value is in F."""
        return (self.value - 32) * 5 / 9


class DryBulbTemperature(Temperature):
    """Dry bulb temperature.

    Attributes:
        value: Input value
        datetime: Date time data for this value (Default: None)
        standard: 'SI' or 'IP' (Default: 'SI')
        nickname: Optional nickname for data (e.g. Dew Point Temperature)
    """

    __slots__ = ()
    minimum = -70
    maximum = 70


class DewPointTemperature(Temperature):
    """Dew point temperature.

    Attributes:
        value: Input value
        datetime: Date time data for this value (Default: None)
        standard: 'SI' or 'IP' (Default: 'SI')
        nickname: Optional nickname for data (e.g. Dew Point Temperature)
    """

    __slots__ = ()
    minimum = -70
    maximum = 70


class RelativeHumidity(DataPoint):
    """Relative humidity.

    Attributes:
        value: Input value
        datetime: Date time data for this value (Default: None)
        standard: 'SI' or 'IP' (Default: 'SI')
        nickname: Optional nickname for data (e.g. Dew Point Temperature)
    """

    __slots__ = ()
    minimum = 0
    maximum = 100
    missing = 999
    value_type = int
    unitSI = '%'
    unitIP = '%'

    def __init__(self, value, datetime=None, standard='SI', nickname=None):
        """Init class."""
        DataPoint.__init__(self, value, datetime, standard, nickname)

    @property
    def to_ip(self):
        """Return the value in IP."""
        return self.value

    @property
    def to_si(self):
        """Return the value in SI."""
        return self.value


class Pressure(DataPoint):
    """Atmospheric Pressure.

    Attributes:
        value: Input value
        datetime: Date time data for this value (Default: None)
        standard: 'SI' or 'IP' (Default: 'SI')
        nickname: Optional nickname for data (e.g. Dew Point Temperature)
    """

    __slots__ = ()
    minimum = 31000
    maximum = 120000
    missing = 999999
    value_type = int
    unitSI = 'Pa'
    unitIP = 'in'

    def __init__(self, value, datetime=None, standard='SI', nickname=None):
        """Init class."""
        DataPoint.__init__(self, value, datetime, standard, nickname)

    @property
    def to_ip(self):
        """Return the value in IP."""
        return self.value * 0.0002953

    @property
    def to_si(self):
        """Return the value in SI."""
        return self.value / 0.0002953


class Radiation(DataPoint):
    """Radiation.

    Attributes:
        value: Input value
        datetime: Date time data for this value (Default: None)
        standard: 'SI' or 'IP' (Default: 'SI')
        nickname: Optional nickname for data (e.g. Dew Point Temperature)
    """

    __slots__ = ()
    minimum = 0
    missing = 9999
    value_type = int
    unitSI = 'Wh/m2'
    unitIP = 'BTU/ft2'

    def __init__(self, value, datetime=None, standard='SI', nickname=None):
        """Init class."""
        DataPoint.__init__(self, value, datetime, standard, nickname)

    @property
    def to_ip(self):
        """Return the value in IP assuming input value is in SI."""
        return self.value * 0.316998331

    @property
    def to_si(self):
        """Return the value in SI assuming input value is in IP."""
        return self.value / 0.316998331


class Illuminance(DataPoint):
    """Illuminance.

    Attributes:
        value: Input value
        datetime: Date time data for this value (Default: None)
        standard: 'SI' or 'IP' (Default: 'SI')
        nickname: Optional nickname for data (e.g. Dew Point Temperature)
    """

    __slots__ = ()
    minimum = 0
    missing = 999999
    value_type = int
    unitSI = 'lux'
    unitIP = 'fc'

    def __init__(self, value, datetime=None, standard='SI', nickname=None):
        """Init class."""
        DataPoint.__init__(self, value, datetime, standard, nickname)

    @property
    def to_ip(self):
        """Return the value in IP assuming input value is in SI."""
        return self.value * 0.09290304

    @property
    def to_si(self):
        """Return the value in SI assuming input value is in IP."""
        return self.value / 0.09290304


class Luminance(Illuminance):
    """Luminance.

    Attributes:
        value: Input value
        datetime: Date time data for this value (Default: None)
        standard: 'SI' or 'IP' (Default: 'SI')
        nickname: Optional nickname for data (e.g. Dew Point Temperature)
    """

    __slots__ = ()
    minimum = 0
    missing = 9999
    value_type = int
    unitSI = 'Cd/m2'
    unitIP = 'Cd/ft2'

    def __init__(self, value, datetime=None, standard='SI', nickname=None):
        """Init class."""
        Illuminance.__init__(self, value, datetime, standard, nickname)


class Angle(DataPoint):
    """Angle.

    Attributes:
        value: Input value
        datetime: Date time data for this value (Default: None)
        standard: 'SI' or 'IP' (Default: 'SI')
        nickname: Optional nickname for data (e.g. Dew Point Temperature)
    """

    __slots__ = ()
    minimum = 0
    maximum = 360
    missing = 999
    value_type = int
    unitSI = 'degrees'
    unitIP = 'radians'

    def __init__(self, value, datetime=None, standard='SI', nickname=None):
        """Init class."""
        DataPoint.__init__(self, value, datetime, standard, nickname)

    @property
    def to_ip(self):
        """Return the value in IP assuming input value is in SI."""
        return (self.value * PI) / 360

    @property
    def to_si(self):
        """Return the value in SI assuming input value is in IP."""
        return (self.value / PI) * 360


class Speed(DataPoint):
    """Speed.

    Attributes:
        value: Input value
        datetime: Date time data for this value (Default: None)
        standard: 'SI' or 'IP' (Default: 'SI')
        nickname: Optional nickname for data (e.g. Dew Point Temperature)
    """

    __slots__ = ()
    minimum = 0
    missing = 999
    value_type = float
    unitSI = 'm/s'
    unitIP = 'mph'

    def __init__(self, value, datetime=None, standard='SI', nickname=None):
        """Init class."""
        DataPoint.__init__(self, value, datetime, standard, nickname)

    @property
    def to_ip(self):
        """Return the value in IP assuming input value is in SI."""
        return self.value * 2.23694  # m/s to mph

    @property
    def to_si(self):
        """Return the value in SI assuming input value is in IP."""
        return self.value / 2.23694  # mph to m/s


class WindSpeed(Speed):
    """Wind Speed.

    Attributes:
        value: Input value
        datetime: Date time data for this value (Default: None)
        standard: 'SI' or 'IP' (Default: 'SI')
        nickname: Optional nickname for data (e.g. Dew Point Temperature)
    """

    __slots__ = ()
    maximum = 40


class Time(DataPoint):
    """Time.

    Attributes:
        value: Input value
        datetime: Date time data for this value (Default: None)
        standard: 'SI' or 'IP' (Default: 'SI')
        nickname: Optional nickname for data (e.g. Dew Point Temperature)
    """

    __slots__ = ()
    minimum = 0
    missing = 99 * 3600
    value_type = int
    unitSI = 'second'
    unitIP = 'second'

    def __init__(self, value, datetime=None, standard='SI', nickname=None):
        """Init class."""
        DataPoint.__init__(self, value, datetime, standard, nickname)


class Tenth(DataPoint):
    """Tenth.

    Attributes:
        value: Input value
        datetime: Date time data for this value (Default: None)
        standard: 'SI' or 'IP' (Default: 'SI')
        nickname: Optional nickname for data (e.g. Dew Point Temperature)
    """

    __slots__ = ()
    minimum = 0
    maximum = 10
    missing = 99
    value_type = int
    unitSI = None
    unitIP = None

    def __init__(self, value, datetime=None, standard='SI', nickname=None):
        """Init class."""
        DataPoint.__init__(self, value, datetime, standard, nickname)


class Thousandths(DataPoint):
    """Thousandths.

    Attributes:
        value: Input value
        datetime: Date time data for this value (Default: None)
        standard: 'SI' or 'IP' (Default: 'SI')
        nickname: Optional nickname for data (e.g. Dew Point Temperature)
    """

    __slots__ = ()
    minimum = 0
    missing = 999
    value_type = float
    unitSI = 'thousandths'
    unitIP = 'thousandths'

    def __init__(self, value, datetime=None, standard='SI', nickname=None):
        """Init class."""
        DataPoint.__init__(self, value, datetime, standard, nickname)


class Distance(DataPoint):
    """Distance.

    Attributes:
        value: Input value
        datetime: Date time data for this value (Default: None)
        standard: 'SI' or 'IP' (Default: 'SI')
        nickname: Optional nickname for data (e.g. Dew Point Temperature)
        conversion: Optional value for conversion to meters or foot before
            creating the object.
    """

    __slots__ = ()
    minimum = 0
    value_type = float
    unitSI = 'm'
    unitIP = 'foot'

    def __init__(self, value, datetime=None, standard='SI', nickname=None,
                 conversion=1):
        """Init class."""
        DataPoint.__init__(self, value * conversion, datetime, standard, nickname)

    @property
    def to_ip(self):
        """Return the value in IP assuming input value is in SI."""
        return self.value * 3.28084

    @property
    def to_si(self):
        """Return the value in SI assuming input value is in IP."""
        return self.value / 3.28084


class SkyPatch(DataPoint):
    """SkyPatch.

    Attributes:
        value: Input value
        vector: Sky vector as a tuple
        id: patch number
    """

    __slots__ = ('vector',)
    minimum = 0
    value_type = float
    unitSI = 'steradian'
    unitIP = 'steradian'

    def __init__(self, value, vector, id=None):
        """Init class."""
        DataPoint.__init__(self, value, datetime=None, standard=None, nickname=id)
        self.vector = Vector3(*vector)

    @property
    def id(self):
        """Sky patch number."""
        return self.nickname


class PredictedMeanVote(DataPoint):
    """Predicted Mean Vote (PMV).

    Attributes:
        value: Input value
        datetime: Date time data for this value (Default: None)
        standard: 'SI' or 'IP' (Default: 'SI')
        nickname: Optional nickname for data (e.g. Dew Point Temperature)
    """

    __slots__ = ()
    minimum = -50
    maximum = 50
    value_type = float
    unitSI = 'PMV'
    unitIP = 'PMV'

    def __init__(self, value, datetime=None, standard='SI', nickname=None):
        """Init class."""
        DataPoint.__init__(self, value, datetime, standard, nickname)


class PercentagePeopleDissatisfied(DataPoint):
    """Percentage of People Dissatisfied (PPD).

    Attributes:
        value: Input value
        datetime: Date time data for this value (Default: None)
        standard: 'SI' or 'IP' (Default: 'SI')
        nickname: Optional nickname for data (e.g. Dew Point Temperature)
    """

    __slots__ = ()
    minimum = 0
    maximum = 100
    value_type = float
    unitSI = '%'
    unitIP = '%'

    def __init__(self, value, datetime=None, standard='SI', nickname=None):
        """Init class."""
        DataPoint.__init__(self, value, datetime, standard, nickname)


class MetabolicRate(DataPoint):
    """Metabolic Rate (met).

    Attributes:
        value: Input value
        datetime: Date time data for this value (Default: None)
        standard: 'SI' or 'IP' (Default: 'SI')
        nickname: Optional nickname for data (e.g. Dew Point Temperature)
    """

    __slots__ = ()
    minimum = 0
    value_type = float
    unitSI = 'met'
    unitIP = 'met'

    def __init__(self, value, datetime=None, standard='SI', nickname=None):
        """Init class."""
        DataPoint.__init__(self, value, datetime, standard, nickname)


class Clothing(DataPoint):
    """Clothing Level (clo).

    Attributes:
        value: Input value
        datetime: Date time data for this value (Default: None)
        standard: 'SI' or 'IP' (Default: 'SI')
        nickname: Optional nickname for data (e.g. Dew Point Temperature)
    """

    __slots__ = ()
    minimum = 0
    value_type = float
    unitSI = 'clo'
    unitIP = 'clo'

    def __init__(self, value, datetime=None, standard='SI', nickname=None):
        """Init class."""
        DataPoint.__init__(self, value, datetime, standard, nickname)
