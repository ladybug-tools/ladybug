# coding=utf-8
"""Energy flux data type."""
from __future__ import division

from .base import DataTypeBase
from .energyintensity import EnergyIntensity, Radiation, GlobalHorizontalRadiation, \
    DirectNormalRadiation, DiffuseHorizontalRadiation, DirectHorizontalRadiation


class EnergyFlux(DataTypeBase):
    """Energy Flux
    """
    _units = ('W/m2', 'Btu/h-ft2', 'kW/m2', 'kBtu/h-ft2', 'W/ft2', 'met')
    _si_units = ('W/m2', 'kW/m2')
    _ip_units = ('Btu/h-ft2', 'kBtu/h-ft2')
    _abbreviation = 'J'
    _point_in_time = False
    _time_aggregated_type = EnergyIntensity
    _time_aggregated_factor = 0.001

    def _W_m2_to_Btu_hft2(self, value):
        return value / 3.15459075

    def _W_m2_to_kW_m2(self, value):
        return value / 1000.

    def _W_m2_to_kBtu_hft2(self, value):
        return value / 3154.59075

    def _W_m2_to_W_ft2(self, value):
        return value / 10.7639

    def _W_m2_to_met(self, value):
        return value / 58.2

    def _Btu_hft2_to_W_m2(self, value):
        return value * 3.15459075

    def _kW_m2_to_W_m2(self, value):
        return value * 1000.

    def _kBtu_hft2_to_W_m2(self, value):
        return value * 3154.59075

    def _W_ft2_to_W_m2(self, value):
        return value * 10.7639

    def _met_to_W_m2(self, value):
        return value * 58.2

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('W/m2', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        if from_unit in self.ip_units or from_unit == 'met':
            return values, from_unit
        elif from_unit == 'kW/m2':
            return self.to_unit(values, 'kBtu/h-ft2', from_unit), 'kBtu/h-ft2'
        else:
            return self.to_unit(values, 'Btu/h-ft2', from_unit), 'Btu/h-ft2'

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        if from_unit in self.si_units or from_unit == 'met':
            return values, from_unit
        elif from_unit == 'kBtu/h-ft2':
            return self.to_unit(values, 'kW/m2', from_unit), 'kW/m2'
        else:
            return self.to_unit(values, 'W/m2', from_unit), 'W/m2'


class MetabolicRate(EnergyFlux):
    _min = 0
    _abbreviation = 'MetR'


class EffectiveRadiantField(EnergyFlux):
    _abbreviation = 'ERF'


class Irradiance(EnergyFlux):
    _min = 0
    _abbreviation = 'Qsolar'
    _time_aggregated_type = Radiation


class GlobalHorizontalIrradiance(Irradiance):
    _abbreviation = 'GHIr'
    _time_aggregated_type = GlobalHorizontalRadiation


class DirectNormalIrradiance(Irradiance):
    _abbreviation = 'DNIr'
    _time_aggregated_type = DirectNormalRadiation


class DiffuseHorizontalIrradiance(Irradiance):
    _abbreviation = 'DHIr'
    _time_aggregated_type = DiffuseHorizontalRadiation


class DirectHorizontalIrradiance(Irradiance):
    _abbreviation = 'DHIr'
    _time_aggregated_type = DirectHorizontalRadiation


class HorizontalInfraredRadiationIntensity(Irradiance):
    _abbreviation = 'HIr'
    _point_in_time = True
