# coding=utf-8
"""Base data type."""
from __future__ import division

from ..datapoint import DataPoint


class DataTypeBase(object):
    """Base class for data types.

    Attributes:
        name: The full name of the data type as a string.
        units: A list of all accetpable units of the data type as abbreviated text.
            The first item of the list should be the standard SI unit.
            The second item of the list should be the stadard IP unit (if it exists).
            The rest of the list can be any other acceptable units.
            (eg. [C, F, K])
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

    name = 'Data Type Base'
    units = [None]
    min = float('-inf')
    max = float('+inf')

    abbreviation = ''
    unit_descr = ''
    point_in_time = True
    cumulative = False

    min_epw = float('-inf')
    max_epw = float('+inf')
    missing_epw = None

    def __init__(self):
        """Init DataType."""

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

    def is_in_range(self, values, unit=None, raise_exception=False):
        """Check if a list of values is within acceptable ranges.

        Args:
            values: A list of values.
            unit: The unit of the values.  If not specified, the default metric
                unit will be assumed.
            raise_exception: Set to True to raise an exception if not in range.
        """
        self._check_values(values)
        if unit is None or unit == self.units[0]:
            minimum = self.min
            maximum = self.max
        else:
            namespace = {'self': self, 'minimum': None, 'maximum': None}
            self.is_unit_acceptable(unit, True)
            min_statement = "minimum = self._{}_to_{}(self.min)".format(
                self._clean(self.units[0]), self._clean(unit))
            max_statement = "maximum = self._{}_to_{}(self.max)".format(
                self._clean(self.units[0]), self._clean(unit))
            exec(min_statement, namespace)
            exec(max_statement, namespace)
            minimum, maximum = namespace['minimum'], namespace['maximum']

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

    def is_in_range_epw(self, values, unit=None, raise_exception=False):
        """Check if a list of values is within acceptable ranges for an EPW file.

        Args:
            values: A list of values.
            unit: The unit of the values.  If not specified, the default metric
                unit will be assumed.
            raise_exception: Set to True to raise an exception if not in range.
        """
        self._check_values(values)
        if unit is None or unit == self.units[0]:
            minimum = self.min_epw
            maximum = self.max_epw
        else:
            namespace = {'self': self, 'minimum': None, 'maximum': None}
            self.is_unit_acceptable(unit, True)
            min_statement = "minimum = self._{}_to_{}(self.min_epw)".format(
                self._clean(self.units[0]), self._clean(unit))
            max_statement = "maximum = self._{}_to_{}(self.max_epw)".format(
                self._clean(self.units[0]), self._clean(unit))
            exec(min_statement, namespace)
            exec(max_statement, namespace)
            minimum, maximum = namespace['minimum'], namespace['maximum']

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

    def _check_values(self, values):
        """Check to be sure values are numbers before doing numerical operations."""
        if len(values) > 0:
            assert isinstance(values[0], (float, int, DataPoint)), \
                "values must be numbers to perform math operations. Got {}".format(
                    type(values[0]))

    def _to_unit_base(self, base_unit, values, unit, from_unit):
        """Return values in a given unit given the input from_unit."""
        self._check_values(values)
        namespace = {'self': self, 'values': values}
        if not from_unit == base_unit:
            self.is_unit_acceptable(from_unit, True)
            statement = 'values = [self._{}_to_{}(val) for val in values]'.format(
                self._clean(from_unit), self._clean(base_unit))
            exec(statement, namespace)
            values = namespace['values']
        if not unit == base_unit:
            self.is_unit_acceptable(unit, True)
            statement = 'values = [self._{}_to_{}(val) for val in values]'.format(
                self._clean(base_unit), self._clean(unit))
            exec(statement, namespace)
            values = namespace['values']
        return values

    def _clean(self, unit):
        """Clean out special characters from unit abbreviations."""
        return unit.replace(
            '/', '_').replace(
                '-', '').replace(
                    ' ', '').replace(
                        '%', 'pct')

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
