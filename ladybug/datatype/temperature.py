# coding=utf-8
"""Temperature data type."""
from __future__ import division

from .base import DataTypeBase


class Temperature(DataTypeBase):
    """Temperature

    Properties:
        *   name
        *   units
        *   si_units
        *   ip_units
        *   min
        *   max
        *   abbreviation
        *   unit_descr
        *   point_in_time
        *   cumulative
    """
    _units = ('C', 'F', 'K')
    _si_units = ('C', 'K')
    _ip_units = ('F')
    _min = -273.15
    _abbreviation = 'T'

    def _C_to_F(self, value):
        return value * 9. / 5. + 32.

    def _C_to_K(self, value):
        return value + 273.15

    def _F_to_C(self, value):
        return (value - 32.) * 5. / 9.

    def _K_to_C(self, value):
        return value - 273.15

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('C', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        if from_unit == 'F':
            return values, from_unit
        else:
            return self.to_unit(values, 'F', from_unit), 'F'

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        if from_unit == 'C' or from_unit == 'K':
            return values, from_unit
        else:
            return self.to_unit(values, 'C', from_unit), 'C'

    @property
    def isTemperature(self):
        """Return True."""
        return True


class DryBulbTemperature(Temperature):
    """
    Properties:
        *   name
        *   units
        *   si_units
        *   ip_units
        *   min
        *   max
        *   abbreviation
        *   unit_descr
        *   point_in_time
        *   cumulative
    """
    _abbreviation = 'DBT'


class DewPointTemperature(Temperature):
    """
    Properties:
        *   name
        *   units
        *   si_units
        *   ip_units
        *   min
        *   max
        *   abbreviation
        *   unit_descr
        *   point_in_time
        *   cumulative
    """
    _abbreviation = 'DPT'


class WetBulbTemperature(Temperature):
    """
    Properties:
        *   name
        *   units
        *   si_units
        *   ip_units
        *   min
        *   max
        *   abbreviation
        *   unit_descr
        *   point_in_time
        *   cumulative
    """
    _abbreviation = 'WBT'


class SkyTemperature(Temperature):
    """
    Properties:
        *   name
        *   units
        *   si_units
        *   ip_units
        *   min
        *   max
        *   abbreviation
        *   unit_descr
        *   point_in_time
        *   cumulative
    """
    _abbreviation = 'Tsky'


class GroundTemperature(Temperature):
    """
    Properties:
        *   name
        *   units
        *   si_units
        *   ip_units
        *   min
        *   max
        *   abbreviation
        *   unit_descr
        *   point_in_time
        *   cumulative
    """
    _abbreviation = 'Tground'


class AirTemperature(Temperature):
    """
    Properties:
        *   name
        *   units
        *   si_units
        *   ip_units
        *   min
        *   max
        *   abbreviation
        *   unit_descr
        *   point_in_time
        *   cumulative
    """
    _abbreviation = 'Tair'


class RadiantTemperature(Temperature):
    """
    Properties:
        *   name
        *   units
        *   si_units
        *   ip_units
        *   min
        *   max
        *   abbreviation
        *   unit_descr
        *   point_in_time
        *   cumulative
    """
    _abbreviation = 'Trad'


class OperativeTemperature(Temperature):
    """
    Properties:
        *   name
        *   units
        *   si_units
        *   ip_units
        *   min
        *   max
        *   abbreviation
        *   unit_descr
        *   point_in_time
        *   cumulative
    """
    _abbreviation = 'To'


class MeanRadiantTemperature(Temperature):
    """
    Properties:
        *   name
        *   units
        *   si_units
        *   ip_units
        *   min
        *   max
        *   abbreviation
        *   unit_descr
        *   point_in_time
        *   cumulative
    """
    _abbreviation = 'MRT'


class StandardEffectiveTemperature(Temperature):
    """
    Properties:
        *   name
        *   units
        *   si_units
        *   ip_units
        *   min
        *   max
        *   abbreviation
        *   unit_descr
        *   point_in_time
        *   cumulative
    """
    _abbreviation = 'SET'


class UniversalThermalClimateIndex(Temperature):
    """
    Properties:
        *   name
        *   units
        *   si_units
        *   ip_units
        *   min
        *   max
        *   abbreviation
        *   unit_descr
        *   point_in_time
        *   cumulative
    """
    _abbreviation = 'UTCI'


class PrevailingOutdoorTemperature(Temperature):
    """
    Properties:
        *   name
        *   units
        *   si_units
        *   ip_units
        *   min
        *   max
        *   abbreviation
        *   unit_descr
        *   point_in_time
        *   cumulative
    """
    _abbreviation = 'Tprevail'
