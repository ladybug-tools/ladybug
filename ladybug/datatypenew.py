# coding=utf-8
from __future__ import division
"""Ladybug data types."""
from ladybug.datatype import DataPoint

import math
from copy import deepcopy

PI = math.pi


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
        unit_descr: An optional description of the units if numerical values
            of these units relate to specific categories.
            (eg. -1 = Cold, 0 = Neutral, +1 = Hot) (eg. 0 = False, 1 = True)
        cumulative: Boolean to tell whether the value can be cumulative over
            a time period or can only represent conditions at an instant or an
            average over a time period. (Default: False).
        min_epw: Lower limit for the data type when it occurs in EPW files.
            (Default: -inf)
        max_epw: Upper limit for the data type when it occurs in EPW files.
            (Default: +inf)
        missing_epw: Missing value for the data type when it occurs in EPW files.
            (Default: None)
        middle_hour_epw: Boolean to note whether the data type represents conditions
            on the half hour (True) as opposed to the hour (False)) when it is
            found in an EPW file. (Default: False).
    """

    name = 'Data Type Base'
    units = [None]
    min = float('-inf')
    max = float('+inf')

    unit_descr = ''
    cumulative = False

    min_epw = float('-inf')
    max_epw = float('+inf')
    missing_epw = None
    middle_hour_epw = False

    def __init__(self):
        """Init DataType."""

    @classmethod
    def from_json(cls, data):
        """Create a data type from a dictionary.

        Args:
            data: Data as a dictionary.
                {
                    "name": data type name as a string
                    "units": list of acceptable units
                }
        """
        assert 'name' in data, 'Required keyword "name" is missing!'
        assert 'units' in data, 'Required keyword "units" is missing!'
        return DataTypes.type_by_name_and_unit(data['name'], data['units'][0])

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

    def to_json(self):
        """Get data type as a json object"""
        return {
            'name': self.name,
            'units': self.units
        }

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


""" ************ FUNDAMENTAL DATA TYPES ************ """
# TODO: Add data types for Area, Volume, MassFlowRate
# TODO: Add data types for Conductivity, ThermalResistance, UValue, RValue(with clo)
# TODO: Add data types for PMV, MetabolicRate, ThermalCondition, Comfort
# TODO: Add PPD to hinherit from Percentage, SET and UTCI to inherit from Temperature


class Unitless(DataTypeBase):
    """Type for any data without a recognizable name and no units."""
    def __init__(self, name):
        """Init Generic Type."""
        self.name = name


class GenericType(DataTypeBase):
    """Type for any data without a recognizable name."""
    def __init__(self, name, unit):
        """Init Generic Type."""
        self.name = name
        self.units = [unit]

    def to_ip(self, values, from_unit):
        """Return values in IP."""
        return values, from_unit

    def to_si(self, values, from_unit):
        """Return values in SI."""
        return values, from_unit


class Temperature(DataTypeBase):
    """Temperature"""
    name = 'Temperature'
    units = ['C', 'F', 'K']
    min = -273.15

    def _C_to_F(self, value):
        return value * 9 / 5 + 32

    def _C_to_K(self, value):
        return value + 273.15

    def _F_to_C(self, value):
        return (value - 32) * 5 / 9

    def _K_to_C(self, value):
        return value - 273.15

    def to_unit(self, values, unit, from_unit):
        """Return values in a given unit given the input from_unit."""
        return self._to_unit_base('C', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP given the input from_unit."""
        if from_unit == 'F':
            return values, from_unit
        else:
            return self.to_unit(values, 'F', from_unit), 'F'

    def to_si(self, values, from_unit):
        """Return values in SI given the input from_unit."""
        if from_unit == 'C' or from_unit == 'K':
            return values, from_unit
        else:
            return self.to_unit(values, 'C', from_unit), 'C'

    @property
    def isTemperature(self):
        """Return True."""
        return True


class Percentage(DataTypeBase):
    """Percentage"""
    name = 'Percentage'
    units = ['%', 'fraction', 'tenths', 'thousandths']

    def _pct_to_fraction(self, value):
        return value / 100

    def _pct_to_tenths(self, value):
        return value / 10

    def _pct_to_thousandths(self, value):
        return value * 10

    def _fraction_to_pct(self, value):
        return value * 100

    def _tenths_to_pct(self, value):
        return value * 10

    def _thousandths_to_pct(self, value):
        return value / 10

    def to_unit(self, values, unit, from_unit):
        """Return values in a given unit given the input from_unit."""
        return self._to_unit_base('%', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP given the input from_unit."""
        return values, from_unit

    def to_si(self, values, from_unit):
        """Return values in SI given the input from_unit."""
        return values, from_unit

    @property
    def isPercentage(self):
        """Return True."""
        return True


class Distance(DataTypeBase):
    """Distance"""
    name = 'Distance'
    units = ['m', 'ft', 'mm', 'in', 'km', 'mi', 'cm']
    min = 0

    def _m_to_ft(self, value):
        return value * 3.28084

    def _m_to_mm(self, value):
        return value * 1000

    def _m_to_in(self, value):
        return value * 39.3701

    def _m_to_km(self, value):
        return value / 1000

    def _m_to_mi(self, value):
        return value / 1609.344

    def _m_to_cm(self, value):
        return value * 100

    def _ft_to_m(self, value):
        return value / 3.28084

    def _mm_to_m(self, value):
        return value / 1000

    def _in_to_m(self, value):
        return value / 39.3701

    def _km_to_m(self, value):
        return value * 1000

    def _mi_to_m(self, value):
        return value * 1609.344

    def _cm_to_m(self, value):
        return value / 100

    def to_unit(self, values, unit, from_unit):
        """Return values in a given unit given the input from_unit."""
        return self._to_unit_base('m', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP given the input from_unit."""
        ip_units = ['ft', 'in', 'mi']
        if from_unit in ip_units:
            return values, from_unit
        elif from_unit == 'mm':
            return self.to_unit(values, 'in', from_unit), 'in'
        elif from_unit == 'km':
            return self.to_unit(values, 'mi', from_unit), 'mi'
        else:
            return self.to_unit(values, 'ft', from_unit), 'ft'

    def to_si(self, values, from_unit):
        """Return values in SI given the input from_unit."""
        si_units = ['m', 'mm', 'km', 'cm']
        if from_unit in si_units:
            return values, from_unit
        elif from_unit == 'in':
            return self.to_unit(values, 'mm', from_unit), 'mm'
        elif from_unit == 'mi':
            return self.to_unit(values, 'km', from_unit), 'km'
        else:
            return self.to_unit(values, 'm', from_unit), 'm'

    @property
    def isDistance(self):
        """Return True."""
        return True


class Area(DataTypeBase):
    """Area"""
    name = 'Area'
    units = ['m2', 'ft2', 'mm2', 'in2', 'km2', 'mi2', 'cm2', 'ha', 'acre']
    min = 0

    def _m2_to_ft2(self, value):
        return value * 10.7639

    def _m2_to_mm2(self, value):
        return value * 1000000

    def _m2_to_in2(self, value):
        return value * 1550

    def _m2_to_km2(self, value):
        return value / 1000000

    def _m2_to_mi2(self, value):
        return value / 2590000

    def _m2_to_cm2(self, value):
        return value * 10000

    def _m2_to_ha(self, value):
        return value / 10000

    def _m2_to_acre(self, value):
        return value / 4046.86

    def _ft2_to_m2(self, value):
        return value / 10.7639

    def _mm2_to_m2(self, value):
        return value / 1000000

    def _in2_to_m2(self, value):
        return value / 1550

    def _km2_to_m2(self, value):
        return value * 1000000

    def _mi2_to_m2(self, value):
        return value * 2590000

    def _cm2_to_m2(self, value):
        return value / 10000

    def _ha_to_m2(self, value):
        return value * 10000

    def _acre_to_m2(self, value):
        return value * 4046.86

    def to_unit(self, values, unit, from_unit):
        """Return values in a given unit given the input from_unit."""
        return self._to_unit_base('m2', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP given the input from_unit."""
        ip_units = ['ft2', 'in2', 'mi2', 'acre']
        if from_unit in ip_units:
            return values, from_unit
        elif from_unit == 'mm2' or from_unit == 'cm2':
            return self.to_unit(values, 'in2', from_unit), 'in2'
        elif from_unit == 'km2':
            return self.to_unit(values, 'mi2', from_unit), 'mi2'
        elif from_unit == 'ha':
            return self.to_unit(values, 'acre', from_unit), 'acre'
        else:
            return self.to_unit(values, 'ft2', from_unit), 'ft2'

    def to_si(self, values, from_unit):
        """Return values in SI given the input from_unit."""
        si_units = ['m2', 'mm2', 'km2', 'cm2', 'ha']
        if from_unit in si_units:
            return values, from_unit
        elif from_unit == 'in2':
            return self.to_unit(values, 'mm2', from_unit), 'mm2'
        elif from_unit == 'mi2':
            return self.to_unit(values, 'km2', from_unit), 'km2'
        elif from_unit == 'acre':
            return self.to_unit(values, 'ha', from_unit), 'ha'
        else:
            return self.to_unit(values, 'm2', from_unit), 'm2'

    @property
    def isArea(self):
        """Return True."""
        return True


class Pressure(DataTypeBase):
    """Pressure"""
    name = 'Pressure'
    units = ['Pa', 'inHg', 'atm', 'bar', 'Torr', 'psi', 'inH2O']

    def _Pa_to_inHg(self, value):
        return value * 0.0002953

    def _Pa_to_atm(self, value):
        return value / 101325

    def _Pa_to_bar(self, value):
        return value / 100000

    def _Pa_to_Torr(self, value):
        return value * 0.00750062

    def _Pa_to_psi(self, value):
        return value * 0.000145038

    def _Pa_to_inH2O(self, value):
        return value * 0.00401865

    def _inHg_to_Pa(self, value):
        return value / 0.0002953

    def _atm_to_Pa(self, value):
        return value * 101325

    def _bar_to_Pa(self, value):
        return value * 100000

    def _Torr_to_Pa(self, value):
        return value / 0.00750062

    def _psi_to_Pa(self, value):
        return value / 0.000145038

    def _inH2O_to_Pa(self, value):
        return value / 0.00401865

    def to_unit(self, values, unit, from_unit):
        """Return values in a given unit given the input from_unit."""
        return self._to_unit_base('Pa', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP given the input from_unit."""
        ip_units = ['inHg', 'psi', 'inH2O']
        if from_unit in ip_units:
            return values, from_unit
        else:
            return self.to_unit(values, 'inHg', from_unit), 'inHg'

    def to_si(self, values, from_unit):
        """Return values in SI given the input from_unit."""
        si_units = ['Pa', 'bar']
        if from_unit in si_units:
            return values, from_unit
        else:
            return self.to_unit(values, 'Pa', from_unit), 'Pa'

    @property
    def isPressure(self):
        """Return True."""
        return True


class Energy(DataTypeBase):
    """Energy"""
    name = 'Energy'
    units = ['kWh', 'kBtu', 'Wh', 'Btu', 'MMBtu', 'J', 'kJ', 'MJ', 'GJ',
             'therm', 'cal', 'kcal']
    cumulative = True

    def _kWh_to_kBtu(self, value):
        return value * 3.41214

    def _kWh_to_Wh(self, value):
        return value * 1000

    def _kWh_to_Btu(self, value):
        return value * 3412.14

    def _kWh_to_MMBtu(self, value):
        return value * 0.00341214

    def _kWh_to_J(self, value):
        return value * 3600000

    def _kWh_to_kJ(self, value):
        return value * 3600

    def _kWh_to_MJ(self, value):
        return value * 3.6

    def _kWh_to_GJ(self, value):
        return value * 0.0036

    def _kWh_to_therm(self, value):
        return value * 0.0341214

    def _kWh_to_cal(self, value):
        return value * 860421

    def _kWh_to_kcal(self, value):
        return value * 860.421

    def _kBtu_to_kWh(self, value):
        return value / 3.41214

    def _Wh_to_kWh(self, value):
        return value / 1000

    def _Btu_to_kWh(self, value):
        return value / 3412.14

    def _MMBtu_to_kWh(self, value):
        return value / 0.00341214

    def _J_to_kWh(self, value):
        return value / 3600000

    def _kJ_to_kWh(self, value):
        return value / 3600

    def _MJ_to_kWh(self, value):
        return value / 3.6

    def _GJ_to_kWh(self, value):
        return value / 0.0036

    def _therm_to_kWh(self, value):
        return value / 0.0341214

    def _cal_to_kWh(self, value):
        return value / 860421

    def _kcal_to_kWh(self, value):
        return value / 860.421

    def to_unit(self, values, unit, from_unit):
        """Return values in a given unit given the input from_unit."""
        return self._to_unit_base('kWh', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP given the input from_unit."""
        ip_units = ['kBtu', 'Btu', 'MMBtu', 'therm']
        if from_unit in ip_units:
            return values, from_unit
        elif from_unit == 'Wh':
            return self.to_unit(values, 'Btu', from_unit), 'Btu'
        else:
            return self.to_unit(values, 'kBtu', from_unit), 'kBtu'

    def to_si(self, values, from_unit):
        """Return values in SI given the input from_unit."""
        si_units = ['kWh', 'Wh', 'J', 'kJ', 'MJ', 'GJ']
        if from_unit in si_units:
            return values, from_unit
        elif from_unit == 'Btu':
            return self.to_unit(values, 'Wh', from_unit), 'Wh'
        else:
            return self.to_unit(values, 'kWh', from_unit), 'kWh'

    @property
    def isEnergy(self):
        """Return True."""
        return True


class EnergyIntensity(DataTypeBase):
    """Energy Intensity"""
    name = 'Energy Intensity'
    units = ['kWh/m2', 'kBtu/ft2', 'Wh/m2', 'Btu/ft2']
    cumulative = True

    def _kWh_m2_to_kBtu_ft2(self, value):
        return value * 0.316998

    def _kWh_m2_to_Wh_m2(self, value):
        return value * 1000

    def _kWh_m2_to_Btu_ft2(self, value):
        return value * 316.998

    def _kBtu_ft2_to_kWh_m2(self, value):
        return value / 0.316998

    def _Wh_m2_to_kWh_m2(self, value):
        return value / 1000

    def _Btu_ft2_to_kWh_m2(self, value):
        return value / 316.998

    def to_unit(self, values, unit, from_unit):
        """Return values in a given unit given the input from_unit."""
        return self._to_unit_base('kWh/m2', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP given the input from_unit."""
        ip_units = ['kBtu/ft2', 'Btu/ft2']
        if from_unit in ip_units:
            return values, from_unit
        elif from_unit == 'Wh/m2':
            return self.to_unit(values, 'Btu/ft2', from_unit), 'Btu/ft2'
        else:
            return self.to_unit(values, 'kBtu/ft2', from_unit), 'kBtu/ft2'

    def to_si(self, values, from_unit):
        """Return values in SI given the input from_unit."""
        si_units = ['kWh/m2', 'Wh/m2']
        if from_unit in si_units:
            return values, from_unit
        elif from_unit == 'Btu/ft2':
            return self.to_unit(values, 'Wh/m2', from_unit), 'Wh/m2'
        else:
            return self.to_unit(values, 'kWh/m2', from_unit), 'kWh/m2'

    @property
    def isEnergyIntensity(self):
        """Return True."""
        return True


class Power(DataTypeBase):
    """Power"""
    name = 'Power'
    units = ['W', 'Btu/h', 'kW', 'kBtu/h', 'TR', 'hp']

    def _W_to_Btu_h(self, value):
        return value * 3.41214

    def _W_to_kW(self, value):
        return value / 1000

    def _W_to_kBtu_h(self, value):
        return value * 0.00341214

    def _W_to_TR(self, value):
        return value / 3516.85

    def _W_to_hp(self, value):
        return value / 745.7

    def _Btu_h_to_W(self, value):
        return value / 3.41214

    def _kW_to_W(self, value):
        return value * 1000

    def _kBtu_h_to_W(self, value):
        return value / 0.00341214

    def _TR_to_W(self, value):
        return value * 3516.85

    def _hp_to_W(self, value):
        return value * 745.7

    def to_unit(self, values, unit, from_unit):
        """Return values in a given unit given the input from_unit."""
        return self._to_unit_base('W', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP given the input from_unit."""
        ip_units = ['Btu/h', 'kBtu/h', 'TR', 'hp']
        if from_unit in ip_units:
            return values, from_unit
        elif from_unit == 'kW':
            return self.to_unit(values, 'kBtu/h', from_unit), 'kBtu/h'
        else:
            return self.to_unit(values, 'Btu/h', from_unit), 'Btu/h'

    def to_si(self, values, from_unit):
        """Return values in SI given the input from_unit."""
        si_units = ['kW', 'W']
        if from_unit in si_units:
            return values, from_unit
        elif from_unit == 'kBtu/h':
            return self.to_unit(values, 'kW', from_unit), 'kW'
        else:
            return self.to_unit(values, 'W', from_unit), 'W'

    @property
    def isPower(self):
        """Return True."""
        return True


class EnergyFlux(DataTypeBase):
    """Energy Flux"""
    name = 'Energy Flux'
    units = ['W/m2', 'Btu/h-ft2', 'kW/m2', 'kBtu/h-ft2', 'W/ft2']

    def _W_m2_to_Btu_hft2(self, value):
        return value / 3.15459075

    def _W_m2_to_kW_m2(self, value):
        return value / 1000

    def _W_m2_to_kBtu_hft2(self, value):
        return value / 3154.59075

    def _W_m2_to_W_ft2(self, value):
        return value / 10.7639

    def _Btu_hft2_to_W_m2(self, value):
        return value * 3.15459075

    def _kW_m2_to_W_m2(self, value):
        return value * 1000

    def _kBtu_hft2_to_W_m2(self, value):
        return value * 3154.59075

    def _W_ft2_to_W_m2(self, value):
        return value * 10.7639

    def to_unit(self, values, unit, from_unit):
        """Return values in a given unit given the input from_unit."""
        return self._to_unit_base('W/m2', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP given the input from_unit."""
        ip_units = ['Btu/h-ft2', 'kBtu/h-ft2']
        if from_unit in ip_units:
            return values, from_unit
        elif from_unit == 'kW/m2':
            return self.to_unit(values, 'kBtu/h-ft2', from_unit), 'kBtu/h-ft2'
        else:
            return self.to_unit(values, 'Btu/h-ft2', from_unit), 'Btu/h-ft2'

    def to_si(self, values, from_unit):
        """Return values in SI given the input from_unit."""
        si_units = ['W/m2', 'kW/m2']
        if from_unit in si_units:
            return values, from_unit
        elif from_unit == 'kBtu/h-ft2':
            return self.to_unit(values, 'kW/m2', from_unit), 'kW/m2'
        else:
            return self.to_unit(values, 'W/m2', from_unit), 'W/m2'

    @property
    def isEnergyFlux(self):
        """Return True."""
        return True


class Illuminance(DataTypeBase):
    """Illuminance"""
    name = 'Illuminance'
    units = ['lux', 'fc']
    min = 0
    min_epw = 0
    missing_epw = 999999  # note will be missing if >= 999900

    def _lux_to_fc(self, value):
        return value / 10.7639

    def _fc_to_lux(self, value):
        return value * 10.7639

    def to_unit(self, values, unit, from_unit):
        """Return values in a given unit given the input from_unit."""
        return self._to_unit_base('lux', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in fc given the input from_unit."""
        if from_unit == 'fc':
            return values, from_unit
        else:
            return self.to_unit(values, 'fc', from_unit), 'fc'

    def to_si(self, values, from_unit):
        """Return values in lux given the input from_unit."""
        if from_unit == 'lux':
            return values, from_unit
        else:
            return self.to_unit(values, 'lux', from_unit), 'lux'

    @property
    def isIlluminance(self):
        """Return True."""
        return True


class Luminance(DataTypeBase):
    """Luminance"""
    name = 'Luminance'
    units = ['cd/m2', 'cd/ft2']
    min = 0
    min_epw = 0
    missing_epw = 9999  # note will be missing if >= 999900

    def _cd_m2_to_cd_ft2(self, value):
        return value / 10.7639

    def _cd_ft2_to_cd_m2(self, value):
        return value * 10.7639

    def to_unit(self, values, unit, from_unit):
        """Return values in a given unit given the input from_unit."""
        return self._to_unit_base('cd/m2', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in cd/ft2 given the input from_unit."""
        if from_unit == 'cd/ft2':
            return values, from_unit
        else:
            return self.to_unit(values, 'cd/ft2', from_unit), 'cd/ft2'

    def to_si(self, values, from_unit):
        """Return values in cd/m2 given the input from_unit."""
        if from_unit == 'cd/m2':
            return values, from_unit
        else:
            return self.to_unit(values, 'cd/m2', from_unit), 'cd/m2'

    @property
    def isLuminance(self):
        """Return True."""
        return True


class Angle(DataTypeBase):
    """Angle"""
    name = 'Angle'
    units = ['degrees', 'radians']

    def _degrees_to_radians(self, value):
        return (value * PI) / 180

    def _radians_to_degrees(self, value):
        return (value / PI) * 180

    def to_unit(self, values, unit, from_unit):
        """Return values in a given unit given the input from_unit."""
        return self._to_unit_base('degrees', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP."""
        return values, from_unit

    def to_si(self, values, from_unit):
        """Return values in SI."""
        return values, from_unit

    @property
    def isAngle(self):
        """Return True."""
        return True


class Mass(DataTypeBase):
    """Mass"""
    name = 'Mass'
    units = ['kg', 'lb', 'g', 'tonne', 'ton']
    min = 0

    def _kg_to_lb(self, value):
        return value * 2.20462

    def _kg_to_g(self, value):
        return value * 1000

    def _kg_to_tonne(self, value):
        return value / 1000

    def _kg_to_ton(self, value):
        return value / 907.185

    def _lb_to_kg(self, value):
        return value / 2.20462

    def _g_to_kg(self, value):
        return value / 1000

    def _tonne_to_kg(self, value):
        return value * 1000

    def _ton_to_kg(self, value):
        return value * 907.185

    def to_unit(self, values, unit, from_unit):
        """Return values in a given unit given the input from_unit."""
        return self._to_unit_base('kg', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP given the input from_unit."""
        ip_units = ['lb', 'ton']
        if from_unit in ip_units:
            return values, from_unit
        elif from_unit == 'tonne':
            return self.to_unit(values, 'ton', from_unit), 'ton'
        else:
            return self.to_unit(values, 'lb', from_unit), 'lb'

    def to_si(self, values, from_unit):
        """Return values in SI given the input from_unit."""
        si_units = ['kg', 'g', 'tonne']
        if from_unit in si_units:
            return values, from_unit
        elif from_unit == 'ton':
            return self.to_unit(values, 'tonne', from_unit), 'tonne'
        else:
            return self.to_unit(values, 'kg', from_unit), 'kg'

    @property
    def isMass(self):
        """Return True."""
        return True


class Speed(DataTypeBase):
    """Speed"""
    name = 'Speed'
    units = ['m/s', 'mph', 'km/h', 'knot', 'ft/s']
    min = 0

    def _m_s_to_mph(self, value):
        return value * 2.23694

    def _m_s_to_km_h(self, value):
        return value * 3.6

    def _m_s_to_knot(self, value):
        return value * 1.94384

    def _m_s_to_ft_s(self, value):
        return value * 3.28084

    def _mph_to_m_s(self, value):
        return value / 2.23694

    def _km_h_to_m_s(self, value):
        return value / 3.6

    def _knot_to_m_s(self, value):
        return value / 1.94384

    def _ft_s_to_m_s(self, value):
        return value / 3.28084

    def to_unit(self, values, unit, from_unit):
        """Return values in a given unit given the input from_unit."""
        return self._to_unit_base('m/s', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP units given the input from_unit."""
        ip_units = ['mph', 'ft/s']
        if from_unit in ip_units:
            return values, from_unit
        else:
            return self.to_unit(values, 'mph', from_unit), 'mph'

    def to_si(self, values, from_unit):
        """Return values in SI units given the input from_unit."""
        si_units = ['m/s', 'km/h']
        if from_unit in si_units:
            return values, from_unit
        else:
            return self.to_unit(values, 'm/s', from_unit), 'm/s'

    @property
    def isSpeed(self):
        """Return True."""
        return True


class VolumeFlowRate(DataTypeBase):
    """Volume Flow Rate"""
    name = 'Volume Flow Rate'
    units = ['m3/s', 'ft3/s', 'L/s', 'cfm', 'gpm']
    min = 0

    def _m3_s_to_ft3_s(self, value):
        return value * 35.3147

    def _m3_s_to_L_s(self, value):
        return value * 1000

    def _m3_s_to_cfm(self, value):
        return value * 2118.88

    def _m3_s_to_gpm(self, value):
        return value * 15850.3231

    def _ft3_s_to_m3_s(self, value):
        return value / 35.3147

    def _L_s_to_m3_s(self, value):
        return value / 1000

    def _cfm_to_m3_s(self, value):
        return value / 2118.88

    def _gpm_to_m3_s(self, value):
        return value / 15850.3231

    def to_unit(self, values, unit, from_unit):
        """Return values in a given unit given the input from_unit."""
        return self._to_unit_base('m3/s', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP units given the input from_unit."""
        ip_units = ['ft3/s', 'cfm', 'gpm']
        if from_unit in ip_units:
            return values, from_unit
        elif from_unit == 'L/s':
            return self.to_unit(values, 'cfm', from_unit), 'cfm'
        else:
            return self.to_unit(values, 'ft3/s', from_unit), 'ft3/s'

    def to_si(self, values, from_unit):
        """Return values in SI units given the input from_unit."""
        si_units = ['m3/s', 'L/s']
        if from_unit in si_units:
            return values, from_unit
        elif from_unit == 'cfm':
            return self.to_unit(values, 'L/s', from_unit), 'L/s'
        else:
            return self.to_unit(values, 'm3/s', from_unit), 'm3/s'

    @property
    def isFlowRate(self):
        """Return True."""
        return True


""" ************ DERIVATIVE DATA TYPES ************ """


class DryBulbTemperature(Temperature):
    name = 'Dry Bulb Temperature'
    min_epw = -70
    max_epw = 70
    missing_epw = 99.9


class DewPointTemperature(Temperature):
    name = 'Dew Point Temperature'
    min_epw = -70
    max_epw = 70
    missing_epw = 99.9


class SkyTemperature(Temperature):
    name = 'Sky Temperature'


class MeanRadiantTemperature(Temperature):
    name = 'Mean Radiant Temperature'


class RelativeHumidity(Percentage):
    name = 'Relative Humidity'
    min = 0
    min_epw = 0
    max_epw = 110
    missing_epw = 999


class TotalSkyCover(Percentage):
    # (used if Horizontal IR Intensity missing)
    name = 'Total Sky Cover'
    min = 0
    max = 100
    min_epw = 0
    max_epw = 100
    missing_epw = 99


class OpaqueSkyCover(Percentage):
    # (used if Horizontal IR Intensity missing)
    name = 'Opaque Sky Cover'
    min = 0
    max = 100
    min_epw = 0
    max_epw = 100
    missing_epw = 99


class AerosolOpticalDepth(Percentage):
    name = 'Aerosol Optical Depth'
    min = 0
    max = 100
    min_epw = 0
    max_epw = 100
    missing_epw = 0.999


class Albedo(Percentage):
    name = 'Albedo'
    min = 0
    max = 100
    min_epw = 0
    max_epw = 100
    missing_epw = 0.999


class LiquidPrecipitationQuantity(Percentage):
    name = 'LiquidPrecipitationQuantity'
    min = 0
    min_epw = 0
    max_epw = 100
    missing_epw = 99


class AtmosphericStationPressure(Pressure):
    name = 'Atmospheric Station Pressure'
    min = 0
    min_epw = 31000
    max_epw = 120000
    missing_epw = 999999


class Radiation(EnergyIntensity):
    name = 'Radiation'
    min = 0
    min_epw = 0
    missing_epw = 9999

    @property
    def isRadiation(self):
        """Return True."""
        return True


class GlobalHorizontalRadiation(Radiation):
    name = 'Global Horizontal Radiation'
    middle_hour_epw = True


class DirectNormalRadiation(Radiation):
    name = 'Direct Normal Radiation'
    middle_hour_epw = True


class DiffuseHorizontalRadiation(Radiation):
    name = 'Diffuse Horizontal Radiation'
    middle_hour_epw = True


class DirectHorizontalRadiation(Radiation):
    name = 'Direct Horizontal Radiation'
    middle_hour_epw = True


class HorizontalInfraredRadiationIntensity(Radiation):
    name = 'Horizontal Infrared Radiation Intensity'


class ExtraterrestrialHorizontalRadiation(Radiation):
    name = 'Extraterrestrial Horizontal Radiation'
    middle_hour_epw = True


class ExtraterrestrialDirectNormalRadiation(Radiation):
    name = 'Extraterrestrial Direct Normal Radiation'
    middle_hour_epw = True


class Irradiance(EnergyFlux):
    name = 'Irradiance'
    min = 0
    min_epw = 0
    missing_epw = 9999

    @property
    def isIrradiance(self):
        """Return True."""
        return True


class GlobalHorizontalIrradiance(Irradiance):
    name = 'Global Horizontal Irradiance'
    middle_hour_epw = True


class DirectNormalIrradiance(Irradiance):
    name = 'Direct Normal Irradiance'
    middle_hour_epw = True


class DiffuseHorizontalIrradiance(Irradiance):
    name = 'Diffuse Horizontal Irradiance'
    middle_hour_epw = True


class DirectHorizontalIrradiance(Irradiance):
    name = 'Direct Horizontal Irradiance'
    middle_hour_epw = True


class HorizontalInfraredRadiationIrradiance(Irradiance):
    name = 'Horizontal Infrared Irradiance'


class GlobalHorizontalIlluminance(Illuminance):
    name = 'Global Horizontal Illuminance'
    middle_hour_epw = True


class DirectNormalIlluminance(Illuminance):
    name = 'Direct Normal Illuminance'
    middle_hour_epw = True


class DiffuseHorizontalIlluminance(Illuminance):
    name = 'Diffuse Horizontal Illuminance'
    middle_hour_epw = True


class ZenithLuminance(Luminance):
    name = 'Zenith Luminance'
    middle_hour_epw = True


class WindDirection(Angle):
    name = 'Wind Direction'
    min_epw = 0
    max_epw = 360
    missing_epw = 999


class WindSpeed(Speed):
    name = 'Wind Speed'
    min_epw = 0
    max_epw = 40
    missing_epw = 999


class Visibility(Distance):
    name = 'Visibility'
    missing_epw = 9999


class CeilingHeight(Distance):
    name = 'Ceiling Height'
    missing_epw = 99999


class PrecipitableWater(Distance):
    name = 'Precipitable Water'
    missing_epw = 999


class SnowDepth(Distance):
    name = 'Snow Depth'
    missing_epw = 999


class LiquidPrecipitationDepth(Distance):
    name = 'Liquid Precipitation Depth'
    missing_epw = 999


class DaysSinceLastSnowfall(DataTypeBase):
    name = 'Days Since Last Snowfall'
    missing_epw = 99


class DataTypes(object):
    """Available data type classes organized by full name of the data type."""
    TYPES = {
        'Temperature': Temperature(),
        'Percentage': Percentage(),
        'Distance': Distance(),
        'Pressure': Pressure(),
        'Energy': Energy(),
        'EnergyIntensity': EnergyIntensity(),
        'Power': Power(),
        'EnergyFlux': EnergyFlux(),
        'Illuminance': Illuminance(),
        'Luminance': Luminance(),
        'Angle': Angle(),
        'Mass': Mass(),
        'Speed': Speed(),
        'VolumeFlowRate': VolumeFlowRate(),
        'DryBulbTemperature': DryBulbTemperature(),
        'DewPointTemperature': DewPointTemperature(),
        'SkyTemperature': SkyTemperature(),
        'MeanRadiantTemperature': MeanRadiantTemperature(),
        'RelativeHumidity': RelativeHumidity(),
        'TotalSkyCover': TotalSkyCover(),
        'OpaqueSkyCover': OpaqueSkyCover(),
        'AerosolOpticalDepth': AerosolOpticalDepth(),
        'Albedo': Albedo(),
        'LiquidPrecipitationQuantity': LiquidPrecipitationQuantity(),
        'AtmosphericStationPressure': AtmosphericStationPressure(),
        'Radiation': Radiation(),
        'GlobalHorizontalRadiation': GlobalHorizontalRadiation(),
        'DirectNormalRadiation': DirectNormalRadiation(),
        'DiffuseHorizontalRadiation': DiffuseHorizontalRadiation(),
        'DirectHorizontalRadiation': DirectHorizontalRadiation(),
        'HorizontalInfraredRadiationIntensity': HorizontalInfraredRadiationIntensity(),
        'ExtraterrestrialHorizontalRadiation': ExtraterrestrialHorizontalRadiation(),
        'ExtraterrestrialDirectNormalRadiation': ExtraterrestrialDirectNormalRadiation(),
        'Irradiance': Irradiance(),
        'GlobalHorizontalIrradiance': GlobalHorizontalIrradiance(),
        'DirectNormalIrradiance': DirectNormalIrradiance(),
        'DiffuseHorizontalIrradiance': DiffuseHorizontalIrradiance(),
        'DirectHorizontalIrradiance': DirectHorizontalIrradiance(),
        'ZenithLuminance': ZenithLuminance(),
        'WindDirection': WindDirection(),
        'WindSpeed': WindSpeed(),
        'Visibility': Visibility(),
        'CeilingHeight': CeilingHeight(),
        'PrecipitableWater': PrecipitableWater(),
        'SnowDepth': SnowDepth(),
        'LiquidPrecipitationDepth': LiquidPrecipitationDepth(),
        'DaysSinceLastSnowfall': DaysSinceLastSnowfall()
        }
    BASETYPES = (
        Temperature(),
        Percentage(),
        Distance(),
        Pressure(),
        Energy(),
        EnergyIntensity(),
        Power(),
        EnergyFlux(),
        Illuminance(),
        Luminance(),
        Angle(),
        Mass(),
        Speed(),
        VolumeFlowRate()
    )

    @classmethod
    def all_possible_units(cls):
        """Return a text string indicating all possible units."""
        unit_txt = []
        for base_d_type in cls.BASETYPES:
            unit_list = ', '.join(base_d_type.units)
            unit_txt.append('{}: {}'.format(base_d_type.name, unit_list))
        return '\n'.join(unit_txt)

    @classmethod
    def type_by_name(cls, type_name):
        """Return a class instance of a given data type using the name of the type.

        The type_name can be either the class name or the name property of the type.
        """
        assert isinstance(type_name, str), \
            'type_name must be a text string got {}'.format(type(type_name))
        data_types = cls.TYPES
        if type_name in data_types:
            return deepcopy(data_types[type_name])
        elif type_name.title().replace(' ', '') in data_types:
            return deepcopy(data_types[type_name.title().replace(' ', '')])
        else:
            return None

    @classmethod
    def type_by_unit(cls, unit_name):
        """Return a class instance of a given data type using the name of the unit.

        Note this method can only return fundamental classes (those that inherit
        directly from DataTypeBase).
        """
        assert isinstance(unit_name, str), \
            'unit_name must be a text string got {}'.format(type(unit_name))
        d_type = None
        for base_d_type in cls.BASETYPES:
            if unit_name in base_d_type.units:
                d_type = deepcopy(base_d_type)
        return d_type

    @classmethod
    def type_by_name_and_unit(cls, type_name, unit=None):
        """Return a class instance of a given data type using the tpye_name and unit.

        This method will always return a DataType object.  If an existing one cannot be
        found by name, it will be found by unit, and if neither methods find an
        existing DataType, a generic one will be returned.
        """
        d_type = cls.type_by_name(type_name)
        if d_type:
            d_type.is_unit_acceptable(unit, True)
            return d_type
        elif unit:
            d_type = cls.type_by_unit(unit)
            if d_type:
                d_type.name = type_name
                return d_type
            else:
                return GenericType(type_name, unit)
        else:
            return Unitless(type_name)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """DataTypes representation."""
        types = ('{}'.format(key) for key in self.TYPES)
        return '\n'.join(types)
