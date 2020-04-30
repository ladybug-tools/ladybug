# coding=utf-8
"""Energy intensity data type."""
from __future__ import division

from .base import DataTypeBase


class EnergyIntensity(DataTypeBase):
    """Energy Intensity
    """
    _units = ('kWh/m2', 'kBtu/ft2', 'Wh/m2', 'Btu/ft2', 'kWh/ft2', 'kBtu/m2')
    _si_units = ('kWh/m2', 'Wh/m2')
    _ip_units = ('kBtu/ft2', 'Btu/ft2')
    _abbreviation = 'EUI'
    _point_in_time = False
    _cumulative = True

    def _kWh_m2_to_kBtu_ft2(self, value):
        return value * 0.316998

    def _kWh_m2_to_Wh_m2(self, value):
        return value * 1000.

    def _kWh_m2_to_Btu_ft2(self, value):
        return value * 316.998

    def _kWh_m2_to_kWh_ft2(self, value):
        return value / 10.7639

    def _kWh_m2_to_kBtu_m2(self, value):
        return value * 3.41214

    def _kBtu_ft2_to_kWh_m2(self, value):
        return value / 0.316998

    def _Wh_m2_to_kWh_m2(self, value):
        return value / 1000.

    def _Btu_ft2_to_kWh_m2(self, value):
        return value / 316.998

    def _kWh_ft2_to_kWh_m2(self, value):
        return value * 10.7639

    def _kBtu_m2_to_kWh_m2(self, value):
        return value / 3.41214

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('kWh/m2', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        if from_unit in self.ip_units:
            return values, from_unit
        elif from_unit == 'Wh/m2':
            return self.to_unit(values, 'Btu/ft2', from_unit), 'Btu/ft2'
        else:
            return self.to_unit(values, 'kBtu/ft2', from_unit), 'kBtu/ft2'

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        if from_unit in self.si_units:
            return values, from_unit
        elif from_unit == 'Btu/ft2':
            return self.to_unit(values, 'Wh/m2', from_unit), 'Wh/m2'
        else:
            return self.to_unit(values, 'kWh/m2', from_unit), 'kWh/m2'


class Radiation(EnergyIntensity):
    _min = 0
    _abbreviation = 'Esolar'


class GlobalHorizontalRadiation(Radiation):
    _abbreviation = 'GHR'


class DirectNormalRadiation(Radiation):
    _abbreviation = 'DNR'


class DiffuseHorizontalRadiation(Radiation):
    _abbreviation = 'DHR'


class DirectHorizontalRadiation(Radiation):
    _abbreviation = 'DR'


class ExtraterrestrialHorizontalRadiation(Radiation):
    _abbreviation = 'HRex'


class ExtraterrestrialDirectNormalRadiation(Radiation):
    _abbreviation = 'DNRex'
