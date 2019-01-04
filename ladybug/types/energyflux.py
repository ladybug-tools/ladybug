# coding=utf-8
"""Energy flux data type."""
from __future__ import division

from ._base import DataTypeBase


class EnergyFlux(DataTypeBase):
    """Energy Flux"""
    name = 'Energy Flux'
    units = ['W/m2', 'Btu/h-ft2', 'kW/m2', 'kBtu/h-ft2', 'W/ft2', 'met']
    abbreviation = 'J'
    point_in_time = False

    def _W_m2_to_Btu_hft2(self, value):
        return value / 3.15459075

    def _W_m2_to_kW_m2(self, value):
        return value / 1000

    def _W_m2_to_kBtu_hft2(self, value):
        return value / 3154.59075

    def _W_m2_to_W_ft2(self, value):
        return value / 10.7639

    def _W_m2_to_met(self, value):
        return value / 58.2

    def _Btu_hft2_to_W_m2(self, value):
        return value * 3.15459075

    def _kW_m2_to_W_m2(self, value):
        return value * 1000

    def _kBtu_hft2_to_W_m2(self, value):
        return value * 3154.59075

    def _W_ft2_to_W_m2(self, value):
        return value * 10.7639

    def _met_to_W_m2(self, value):
        return value * 58.2

    def to_unit(self, values, unit, from_unit):
        """Return values in a given unit given the input from_unit."""
        return self._to_unit_base('W/m2', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP given the input from_unit."""
        ip_units = ['Btu/h-ft2', 'kBtu/h-ft2']
        if from_unit in ip_units or from_unit == 'met':
            return values, from_unit
        elif from_unit == 'kW/m2':
            return self.to_unit(values, 'kBtu/h-ft2', from_unit), 'kBtu/h-ft2'
        else:
            return self.to_unit(values, 'Btu/h-ft2', from_unit), 'Btu/h-ft2'

    def to_si(self, values, from_unit):
        """Return values in SI given the input from_unit."""
        si_units = ['W/m2', 'kW/m2']
        if from_unit in si_units or from_unit == 'met':
            return values, from_unit
        elif from_unit == 'kBtu/h-ft2':
            return self.to_unit(values, 'kW/m2', from_unit), 'kW/m2'
        else:
            return self.to_unit(values, 'W/m2', from_unit), 'W/m2'

    @property
    def isEnergyFlux(self):
        """Return True."""
        return True


class MetabolicRate(EnergyFlux):
    name = 'Metabolic Rate'
    abbreviation = 'MetR'
    unit_descr = '1 = Seated, \n1.2 = Standing, \n2 = Walking'


class Irradiance(EnergyFlux):
    name = 'Irradiance'
    min = 0
    abbreviation = 'Qsolar'
    min_epw = 0
    missing_epw = 9999

    @property
    def isIrradiance(self):
        """Return True."""
        return True


class GlobalHorizontalIrradiance(Irradiance):
    name = 'Global Horizontal Irradiance'
    abbreviation = 'GHIr'


class DirectNormalIrradiance(Irradiance):
    name = 'Direct Normal Irradiance'
    abbreviation = 'DNIr'


class DiffuseHorizontalIrradiance(Irradiance):
    name = 'Diffuse Horizontal Irradiance'
    abbreviation = 'DHIr'


class DirectHorizontalIrradiance(Irradiance):
    name = 'Direct Horizontal Irradiance'
    abbreviation = 'DHIr'


class HorizontalInfraredRadiationIntensity(Irradiance):
    name = 'Horizontal Infrared Radiation Intensity'
    abbreviation = 'HIr'
    point_in_time = True
