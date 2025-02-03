# coding=utf-8
"""Specific Heat Capacity data type."""
from __future__ import division

from .base import DataTypeBase


class SpecificHeatCapacity(DataTypeBase):
    """Specific Heat Capacity"""
    _units = ('J/kg-K', 'Btu/lb-F', 'kWh/kg-K', 'kBtu/lb-F', 'kJ/kg-K')
    _si_units = ('J/kg-K', 'kWh/kg-K', 'kJ/kg-K')
    _ip_units = ('Btu/lb-F', 'kBtu/lb-F')
    _min = 0
    _abbreviation = 'c'

    def _J_kgK_to_Btu_lbF(self, value):
        return value / 4186.8

    def _J_kgK_to_kWh_kgK(self, value):
        return value / 3600000.

    def _J_kgK_to_kBtu_lbF(self, value):
        return value / 4186800.

    def _J_kgK_to_kJ_kgK(self, value):
        return value / 1000.

    def _Btu_lbF_to_J_kgK(self, value):
        return value * 4186.8

    def _kWh_kgK_to_J_kgK(self, value):
        return value * 3600000.

    def _kBtu_lbF_to_J_kgK(self, value):
        return value * 4186800.

    def _kJ_kgK_to_J_kgK(self, value):
        return value * 1000.

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('J/kg-K', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        if from_unit in self.ip_units:
            return values, from_unit
        elif from_unit == 'kWh/kg-K':
            return self.to_unit(values, 'kBtu/lb-F', from_unit), 'kBtu/lb-F'
        else:
            return self.to_unit(values, 'Btu/lb-F', from_unit), 'Btu/lb-F'

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        if from_unit in self.si_units:
            return values, from_unit
        elif from_unit == 'kBtu/lb-F':
            return self.to_unit(values, 'kWh/kg-K', from_unit), 'kWh/kg-K'
        else:
            return self.to_unit(values, 'J/kg-K', from_unit), 'J/kg-K'
