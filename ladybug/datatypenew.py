"""Ladybug data types."""
import math
from .euclid import Vector3

PI = math.pi


class DataTypes(object):
    """Available data type classes organized by full name of the data type."""
    TYPES = {
        'Generic Type': 'DataTypeBase',
        'Temperature': 'Temperature',
        'Dry Bulb Temperature': 'DryBulbTemperature',
        'Dew Point Temperature': 'DewPointTemperature',
        'Sky Temperature': 'SkyTemperature',
        'Mean Radiant Temperature': 'MeanRadiantTemperature',
        'Relative Humidity': 'RelativeHumidity',
        }

    @classmethod
    def type_by_name(cls, type_name):
        """Return the name of the class using the name of the data type."""
        assert isinstance(type_name, str), \
            'type_name must be a text string got {}'.format(type(type_name))
        data_types = cls.TYPES
        if type_name.title() in data_types.keys():
            d_type = None
            statement = 'd_type = {}()'.format(data_types[type_name.title()])
            exec(statement)
            return d_type
        else:
            return GenericType(type_name.title())

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """DataTypes representation."""
        types = ('{}'.format(key) for key in self.TYPES.keys())
        return '\n'.join(types)


class DataTypeBase(object):
    """Base type for data types.

    Attributes:
        name: The full name of the data type as a string.
        units: A list of all accetpable units of the data type as abbreviated text.
            The first item of the list should be the standard SI unit.
            The second item of the list should be the stadard IP unit (if such exist).
            The rest of the list should be any other acceptable units.
            (eg. [C, F, K])
        min: Optional lower value for the data type.
        max: Optional upper value for the data type.
        missing: Optional missing value for the data type.
        unit_descr: An optional description of the units if the numerical values
            of these units relate to specific categories.
            (eg. -1 = Cold, 0 = Neutral, +1 = Hot) (eg. 0 = False, 1 = True)
        cumulative: Boolean value to tell whether the value is cumulative over
            a time period or represents conditions at an instant in time
            (or an average over a time period). The default is False.
    """

    name = 'Generic Type'
    units = [None]
    min = float('-inf')
    max = float('+inf')
    missing = None
    unit_descr = ''
    cumulative = False

    def __init__(self):
        """Init DataType."""

    @classmethod
    def from_json(cls, data):
        """Create a data type from a dictionary.

        Args:
            data: Data as a dictionary.
                {
                    "name": data type name as a string
                }
        """
        assert 'name' in data, 'Required keyword "name" is missing!'
        return DataTypes.type_by_name(data['name'])

    def is_unit_acceptable(self, unit, raise_exception=False):
        """Check if a certain unit is acceptable for the data type.

        Args:
            unit: A text string representing the abbreviated unit.
            raise_exception: Set to True to raise an exception if not acceptable.
        """
        _is_acceptable = unit in self.units

        if _is_acceptable or raise_exception is False:
            return _is_acceptable
        else:
            raise ValueError(
                '{0} is not an acceptable unit type for {1}. '
                'Choose from the following: {2}'.format(
                    unit, self.__class__.__name__, self.units
                )
            )

    def to_ip(self, data):
        """Method that converts a list of values from SI to IP."""
        raise NotImplementedError(
            'to_ip is not implemented on %s' % self.__class__.__name__
        )

    def to_si(self, data):
        """Method that converts a list of values from IP to SI."""
        raise NotImplementedError(
            'to_si is not implemented on %s' % self.__class__.__name__
        )

    def is_missing(self, values):
        """Check if a list of values contains missing data."""
        for value in values:
            if value == self.missing:
                return True
        return False

    def is_in_range(self, values, unit=None, raise_exception=False):
        """check if a list of values is within acceptable ranges.

        Args:
            values: A list of values.
            unit: The unit of the values.  If not specified, the default metric
                unit will be assumed.
            raise_exception: Set to True to raise an exception if not in range.
        """
        if unit is None or unit == self.units[0]:
            minimum = self.min
            maximum = self.max
        else:
            self.is_unit_acceptable(unit, True)
            min_statement = "minimum = self.{}_to_{}(self.min)".format(
                self.units[0], unit)
            max_statement = "maximum = self.{}_to_{}(self.max)".format(
                self.units[0], unit)
            exec(min_statement)
            exec(max_statement)

        for value in values:
            if value == self.missing:
                continue
            if value < minimum or value > maximum:
                if not raise_exception:
                    return False
                else:
                    raise ValueError(
                        '{0} should be between {1} and {2}. Got {3}'.format(
                            self.__class__.__name__, self.min, self.max, value
                        )
                    )
        return True

    def to_json(self):
        "Get data type as a json object"
        return {
            'name': self.name
        }

    @property
    def isDataType(self):
        """Return True."""
        return True

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """Return Ladybug data type as a string."""
        return self.name


class GenericType(DataTypeBase):
    """Type for any data without a recognizable name."""
    def __init__(self, name):
        """Init Generic Type."""
        self.name = name


class Temperature(DataTypeBase):
    """Temperature."""
    name = 'Temperature'
    units = ['C', 'F', 'K']
    min = -273.15

    def C_to_F(self, values):
        """Return a list of values in F assuming input values are in C."""
        return [value * 9 / 5 + 32 for value in values]

    def C_to_K(self, values):
        """Return a list of values in K assuming input values are in C."""
        return [value + 273.15 for value in values]

    def F_to_C(self, values):
        """Return a list of values in C assuming input values are in F."""
        return [(value - 32) * 5 / 9 for value in values]

    def K_to_C(self, values):
        """Return a list of values in K assuming input values are in C."""
        return [value - 273.15 for value in values]

    def to_ip(self, values, unit='C'):
        """Return a list of values in F given the input unit."""
        if not unit == 'C':
            self.is_unit_acceptable(unit, True)
            statement = 'values = self.{}_to_C(values)'.format(unit)
            exec(statement)
        return self.C_to_F(values)

    def to_si(self, values, unit='F'):
        """Return a list of values in C given the input unit."""
        self.is_unit_acceptable(unit, True)
        statement = 'values = self.{}_to_C(values)'.format(unit)
        exec(statement)
        return values

    @property
    def isTemperature(self):
        """Return True."""
        return True


class DryBulbTemperature(Temperature):
    """Dry Bulb Temperature."""
    name = 'Dry Bulb Temperature'
    missing = 99.9


class DewPointTemperature(Temperature):
    """Dew Point Temperature."""
    name = 'Dew Point Temperature'
    missing = 99.9


class SkyTemperature(Temperature):
    """Sky Temperature."""
    name = 'Sky Temperature'
    missing = 99.9


class MeanRadiantTemperature(Temperature):
    """Mean Radiant Temperature."""
    name = 'Mean Radiant Temperature'


class RelativeHumidity(DataTypeBase):
    """Relative Humidity."""
    name = 'Relative Humidity'
    units = ['%']
    min = 0
    max = 100
    missing = 999

    def to_ip(self, values):
        """Return the value in IP."""
        return values

    def to_si(self, values):
        """Return the value in SI."""
        return values

    @property
    def isRelativeHumidity(self):
        """Return True."""
        return True


class Pressure(DataTypeBase):
    """Pressure"""
    name = 'Pressure'
    units = ['Pa', 'inHg', 'atm', 'bar', 'Torr', 'psi', 'inH2O', 'kPa']

    def Pa_to_inHg(self, values):
        """Return the value in inHg given an input in Pa."""
        return [value * 0.0002953 for value in values]

    def Pa_to_atm(self, values):
        """Return the value in atm given an input in Pa."""
        return [value / 101325 for value in values]

    def Pa_to_bar(self, values):
        """Return the value in bat given an input in Pa."""
        return [value / 100000 for value in values]

    def inHg_to_Pa(self, values):
        """Return the value in Pa given an input in inHg."""
        return [value / 0.0002953 for value in values]

    def atm_to_Pa(self, values):
        """Return the value in atm given an input in Pa."""
        return [value * 101325 for value in values]

    def bar_to_Pa(self, values):
        """Return the value in bar given an input in Pa."""
        return [value * 100000 for value in values]

    def to_ip(self, values, unit='Pa'):
        """Return a list of values in inHg given the input unit."""
        if not unit == 'Pa':
            self.is_unit_acceptable(unit, True)
            statement = 'values = self.{}_to_Pa(values)'.format(unit)
            exec(statement)
        return self.Pa_to_inHg(values)

    def to_si(self, values, unit='inHg'):
        """Return a list of values in Pa given the input unit."""
        self.is_unit_acceptable(unit, True)
        statement = 'values = self.{}_to_Pa(values)'.format(unit)
        exec(statement)
        return values
