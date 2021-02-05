# coding=utf-8
"""Specific Energy data type."""
from __future__ import division

from .base import DataTypeBase


class SpecificEnergy(DataTypeBase):
    """Specific Energy"""
    _units = ('kWh/kg', 'kBtu/lb', 'Wh/kg', 'Btu/lb', 'J/kg', 'kJ/kg')
    _si_units = ('kWh/kg', 'Wh/kg', 'J/kg', 'kJ/kg')
    _ip_units = ('Btu/lb', 'kBtu/lb')
    _abbreviation = 'E/m'
    _point_in_time = False
    _cumulative = True

    def _kWh_kg_to_kBtu_lb(self, value):
        return value * 1.54772

    def _kWh_kg_to_Wh_kg(self, value):
        return value * 1000.

    def _kWh_kg_to_Btu_lb(self, value):
        return value * 1547.72

    def _kWh_kg_to_J_kg(self, value):
        return value * 3600000.

    def _kWh_kg_to_kJ_kg(self, value):
        return value * 3600.

    def _kBtu_lb_to_kWh_kg(self, value):
        return value / 1.54772

    def _Wh_kg_to_kWh_kg(self, value):
        return value / 1000.

    def _Btu_lb_to_kWh_kg(self, value):
        return value / 1547.72

    def _J_kg_to_kWh_kg(self, value):
        return value / 3600000.

    def _kJ_kg_to_kWh_kg(self, value):
        return value / 3600.

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('kWh/kg', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        if from_unit in self.ip_units:
            return values, from_unit
        elif from_unit == 'kJ/kg':
            return self.to_unit(values, 'Btu/lb', from_unit), 'Btu/lb'
        else:
            return self.to_unit(values, 'kBtu/lb', from_unit), 'kBtu/lb'

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        if from_unit in self.si_units:
            return values, from_unit
        elif from_unit == 'Btu/lb':
            return self.to_unit(values, 'kJ/kg', from_unit), 'kJ/kg'
        else:
            return self.to_unit(values, 'kWh/kg', from_unit), 'kWh/kg'


class Enthalpy(SpecificEnergy):
    _abbreviation = 'Enth'
    _min = 0
