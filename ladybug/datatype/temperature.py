# coding=utf-8
"""Temperature data type."""
from __future__ import division

from .base import DataTypeBase


class Temperature(DataTypeBase):
    """Temperature
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


class DryBulbTemperature(Temperature):
    _abbreviation = 'DBT'


class DewPointTemperature(Temperature):
    _abbreviation = 'DPT'


class WetBulbTemperature(Temperature):
    _abbreviation = 'WBT'


class SkyTemperature(Temperature):
    _abbreviation = 'Tsky'


class GroundTemperature(Temperature):
    _abbreviation = 'Tground'


class AirTemperature(Temperature):
    _abbreviation = 'Tair'


class RadiantTemperature(Temperature):
    _abbreviation = 'Trad'


class OperativeTemperature(Temperature):
    _abbreviation = 'To'


class MeanRadiantTemperature(Temperature):
    _abbreviation = 'MRT'


class StandardEffectiveTemperature(Temperature):
    _abbreviation = 'SET'


class UniversalThermalClimateIndex(Temperature):
    _abbreviation = 'UTCI'


class PrevailingOutdoorTemperature(Temperature):
    _abbreviation = 'Tprevail'
