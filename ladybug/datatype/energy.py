# coding=utf-8
"""Energy data type."""
from __future__ import division

from .base import DataTypeBase
from .energyintensity import EnergyIntensity


class Energy(DataTypeBase):
    """Energy
    """
    _units = ('kWh', 'kBtu', 'Wh', 'Btu', 'MMBtu', 'J', 'kJ', 'MJ', 'GJ',
              'therm', 'cal', 'kcal')
    _si_units = ('kWh', 'Wh', 'J', 'kJ', 'MJ', 'GJ')
    _ip_units = ('kBtu', 'Btu', 'MMBtu', 'therm')
    _abbreviation = 'E'
    _point_in_time = False
    _cumulative = True
    _normalized_type = EnergyIntensity

    def _kWh_to_kBtu(self, value):
        return value * 3.41214

    def _kWh_to_Wh(self, value):
        return value * 1000.

    def _kWh_to_Btu(self, value):
        return value * 3412.14

    def _kWh_to_MMBtu(self, value):
        return value * 0.00341214

    def _kWh_to_J(self, value):
        return value * 3600000.

    def _kWh_to_kJ(self, value):
        return value * 3600.

    def _kWh_to_MJ(self, value):
        return value * 3.6

    def _kWh_to_GJ(self, value):
        return value * 0.0036

    def _kWh_to_therm(self, value):
        return value * 0.0341214

    def _kWh_to_cal(self, value):
        return value * 860421.

    def _kWh_to_kcal(self, value):
        return value * 860.421

    def _kBtu_to_kWh(self, value):
        return value / 3.41214

    def _Wh_to_kWh(self, value):
        return value / 1000.

    def _Btu_to_kWh(self, value):
        return value / 3412.14

    def _MMBtu_to_kWh(self, value):
        return value / 0.00341214

    def _J_to_kWh(self, value):
        return value / 3600000.

    def _kJ_to_kWh(self, value):
        return value / 3600.

    def _MJ_to_kWh(self, value):
        return value / 3.6

    def _GJ_to_kWh(self, value):
        return value / 0.0036

    def _therm_to_kWh(self, value):
        return value / 0.0341214

    def _cal_to_kWh(self, value):
        return value / 860421.

    def _kcal_to_kWh(self, value):
        return value / 860.421

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('kWh', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        if from_unit in self.ip_units:
            return values, from_unit
        elif from_unit == 'Wh':
            return self.to_unit(values, 'Btu', from_unit), 'Btu'
        else:
            return self.to_unit(values, 'kBtu', from_unit), 'kBtu'

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        if from_unit in self.si_units:
            return values, from_unit
        elif from_unit == 'Btu':
            return self.to_unit(values, 'Wh', from_unit), 'Wh'
        else:
            return self.to_unit(values, 'kWh', from_unit), 'kWh'
