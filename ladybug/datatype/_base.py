# coding=utf-8
"""Base data type."""
from __future__ import division

import re


class DataTypeBase(object):
    """Base class for data types.

    Properties:
        name: The full name of the data type as a string.
        units: A list of all accetpable units of the data type as abbreviated text.
            The first item of the list should be the standard SI unit.
            The second item of the list should be the stadard IP unit (if it exists).
            The rest of the list can be any other acceptable units.
            (eg. [C, F, K])
        si_units: A list of acceptable SI units.
        ip_units: A list of acceptable IP units.
        min: Lower limit for the data type, values below which should be physically
            or mathematically impossible. (Default: -inf)
        max: Upper limit for the data type, values above which should be physically
            or mathematically impossible. (Default: +inf)
        abbreviation: An optional abbreviation for the data type as text.
            (eg. 'UTCI' for Universal Thermal Climate Index).
            This can also be a letter that represents the data type in a formula.
            (eg. 'A' for Area; 'P' for Pressure)
        unit_descr: An optional description of the units if numerical values
            of these units relate to specific categories.
            (eg. -1 = Cold, 0 = Neutral, +1 = Hot) (eg. 0 = False, 1 = True)
        point_in_time: Boolean to note whether the data type represents conditions
            at a single instant in time (True) as opposed to being an average or
            accumulation over time (False) when it is found in hourly lists of data.
            (True Examples: Temperature, WindSpeed)
            (False Examples: Energy, Radiation, Illuminance)
        cumulative: Boolean to tell whether the data type can be cumulative when it
            is represented over time (True) or it can only be averaged over time
            to be meaningful (False). Note that cumulative cannot be True
            when point_in_time is also True.
            (False Examples: Temperature, Irradiance, Illuminance)
            (True Examples: Energy, Radiation)
        min_epw: Lower limit for the data type when it occurs in EPW files.
            (Default: -inf)
        max_epw: Upper limit for the data type when it occurs in EPW files.
            (Default: +inf)
        missing_epw: Missing value for the data type when it occurs in EPW files.
            (Default: None)
    """
    _name = None
    _units = [None]
    _si_units = [None]
    _ip_units = [None]
    _min = float('-inf')
    _max = float('+inf')

    _abbreviation = ''
    _unit_descr = ''
    _point_in_time = True
    _cumulative = False

    _min_epw = float('-inf')
    _max_epw = float('+inf')
    _missing_epw = None

    def __init__(self):
        """Init DataType."""
        pass

    @classmethod
    def from_json(cls, data):
        """Create a data type from a dictionary.

        Args:
            data: Data as a dictionary.
                {
                    "name": data type name as a string
                    "base_unit": the base unit of the data type
                    "is_generic": boolean to indicate whether the data type is generic
                }
        """
        assert 'name' in data, 'Required keyword "name" is missing!'
        assert 'base_unit' in data, 'Required keyword "base_unit" is missing!'
        assert 'is_generic' in data, 'Required keyword "is_generic" is missing!'

        from ..datatype import _data_types
        from .generic import GenericType

        formatted_name = data['name'].title().replace(' ', '')
        if data['is_generic'] is True:
            return GenericType(data['name'], data['base_unit'])
        elif formatted_name in _data_types._TYPES:
            clss = _data_types._TYPES[formatted_name]
            return clss()
        elif data['base_unit'] in _data_types._BASEUNITS:
            clss = _data_types._TYPES[_data_types._BASEUNITS[data['base_unit']]]
            instance = clss()
            instance._name = data['name']
            return instance
        else:
            raise ValueError(
                'Data Type {} could not be recognized'.format(data['name']))

    def is_unit_acceptable(self, unit, raise_exception=True):
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

    def to_unit(self, values, unit, from_unit=None):
        """Convert a list of values to a given unit from a given from_unit."""
        raise NotImplementedError(
            'to_unit is not implemented on %s' % self.__class__.__name__
        )

    def to_ip(self, values, from_unit=None):
        """Converts a list of values to IP from a given from_unit."""
        raise NotImplementedError(
            'to_ip is not implemented on %s' % self.__class__.__name__
        )

    def to_si(self, values, from_unit=None):
        """Convert a list of values to SI from a given from_unit."""
        raise NotImplementedError(
            'to_si is not implemented on %s' % self.__class__.__name__
        )

    def is_missing(self, value):
        """Check if a value contains missing data when in an EPW."""
        if value == self.missing_epw:
            return True
        return False

    def is_in_range(self, values, unit=None, raise_exception=True):
        """Check if a list of values is within acceptable ranges.

        Args:
            values: A list of values.
            unit: The unit of the values.  If not specified, the default metric
                unit will be assumed.
            raise_exception: Set to True to raise an exception if not in range.
        """
        assert self._is_numeric(values)
        if unit is None or unit == self.units[0]:
            minimum = self.min
            maximum = self.max
        else:
            namespace = {'self': self}
            self.is_unit_acceptable(unit, True)
            min_statement = "self._{}_to_{}(self.min)".format(
                self._clean(self.units[0]), self._clean(unit))
            max_statement = "self._{}_to_{}(self.max)".format(
                self._clean(self.units[0]), self._clean(unit))
            minimum = eval(min_statement, namespace)
            maximum = eval(max_statement, namespace)

        for value in values:
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

    def is_in_range_epw(self, values, unit=None, raise_exception=True):
        """Check if a list of values is within acceptable ranges for an EPW file.

        Args:
            values: A list of values.
            unit: The unit of the values.  If not specified, the default metric
                unit will be assumed.
            raise_exception: Set to True to raise an exception if not in range.
        """
        assert self._is_numeric(values)
        if unit is None or unit == self.units[0]:
            minimum = self.min_epw
            maximum = self.max_epw
        else:
            namespace = {'self': self}
            self.is_unit_acceptable(unit, True)
            min_statement = "self._{}_to_{}(self.min_epw)".format(
                self._clean(self.units[0]), self._clean(unit))
            max_statement = "self._{}_to_{}(self.max_epw)".format(
                self._clean(self.units[0]), self._clean(unit))
            minimum = eval(min_statement, namespace)
            maximum = eval(max_statement, namespace)

        for value in values:
            if self.is_missing(value):
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
        """Get data type as a json object"""
        return {
            'name': self.name,
            'base_unit': self.units[0],
            'is_generic': hasattr(self, 'isGeneric')
        }

    # TODO: Un-comment the numeric check once we have gotten rid of the DataPoint class
    # Presently, I can't add a check for DataPoint type because it's outside the module
    def _is_numeric(self, values):
        """Check to be sure values are numbers before doing numerical operations."""
        if len(values) > 0:
            pass
            """
            assert isinstance(values[0], (float, int)), \
                "values must be numbers to perform math operations. Got {}".format(
                    type(values[0]))
            """
        return True

    def _to_unit_base(self, base_unit, values, unit, from_unit):
        """Return values in a given unit given the input from_unit."""
        assert self._is_numeric(values)
        namespace = {'self': self, 'values': values}
        if not from_unit == base_unit:
            self.is_unit_acceptable(from_unit, True)
            statement = '[self._{}_to_{}(val) for val in values]'.format(
                self._clean(from_unit), self._clean(base_unit))
            values = eval(statement, namespace)
            namespace['values'] = values
        if not unit == base_unit:
            self.is_unit_acceptable(unit, True)
            statement = '[self._{}_to_{}(val) for val in values]'.format(
                self._clean(base_unit), self._clean(unit))
            values = eval(statement, namespace)
        return values

    def _clean(self, unit):
        """Clean out special characters from unit abbreviations."""
        return unit.replace(
            '/', '_').replace(
                '-', '').replace(
                    ' ', '').replace(
                        '%', 'pct')

    @property
    def name(self):
        """The data type name."""
        if self._name is None:
            return re.sub(r"(?<=\w)([A-Z])", r" \1", self.__class__.__name__)
        else:
            return self._name

    @property
    def units(self):
        """A list of all acceptabledata type units."""
        return self._units

    @property
    def si_units(self):
        """A list of acceptable si_units."""
        return self._si_units

    @property
    def ip_units(self):
        """A list of acceptable ip_units."""
        return self._ip_units

    @property
    def min(self):
        """The minimum value of the data type."""
        return self._min

    @property
    def max(self):
        """The maximum possible value of the data type."""
        return self._max

    @property
    def abbreviation(self):
        """The abbreviation of the data type."""
        return self._abbreviation

    @property
    def unit_descr(self):
        """A description of the data type."""
        return self._unit_descr

    @property
    def point_in_time(self):
        """Whether the data type is point_in_time."""
        return self._point_in_time

    @property
    def cumulative(self):
        """Whether the data type is cumulative."""
        return self._cumulative

    @property
    def min_epw(self):
        """Minimum acceptable value for an EPW."""
        return self._min_epw

    @property
    def max_epw(self):
        """Maxmimum acceptable value for an EPW."""
        return self._max_epw

    @property
    def missing_epw(self):
        """Missing value for an EPW."""
        return self._missing_epw

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
