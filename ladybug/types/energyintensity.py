# coding=utf-8
"""Energy intensity data type."""
from __future__ import division

from ._base import DataTypeBase


class EnergyIntensity(DataTypeBase):
    """Energy Intensity"""
    name = 'Energy Intensity'
    units = ['kWh/m2', 'kBtu/ft2', 'Wh/m2', 'Btu/ft2']
    abbreviation = 'EUI'
    point_in_time = False
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


class Radiation(EnergyIntensity):
    name = 'Radiation'
    min = 0
    abbreviation = 'Esolar'
    min_epw = 0
    missing_epw = 9999

    @property
    def isRadiation(self):
        """Return True."""
        return True


class GlobalHorizontalRadiation(Radiation):
    name = 'Global Horizontal Radiation'
    abbreviation = 'GHR'


class DirectNormalRadiation(Radiation):
    name = 'Direct Normal Radiation'
    abbreviation = 'DNR'


class DiffuseHorizontalRadiation(Radiation):
    name = 'Diffuse Horizontal Radiation'
    abbreviation = 'DHR'


class DirectHorizontalRadiation(Radiation):
    name = 'Direct Horizontal Radiation'
    abbreviation = 'DR'


class ExtraterrestrialHorizontalRadiation(Radiation):
    name = 'Extraterrestrial Horizontal Radiation'
    abbreviation = 'HRex'


class ExtraterrestrialDirectNormalRadiation(Radiation):
    name = 'Extraterrestrial Direct Normal Radiation'
    abbreviation = 'DNRex'
