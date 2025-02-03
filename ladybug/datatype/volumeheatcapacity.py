# coding=utf-8
"""Volumetric Heat Capacity data type."""
from __future__ import division

from .base import DataTypeBase


class VolumetricHeatCapacity(DataTypeBase):
    """Volumetric Heat Capacity"""
    _units = ('J/m3-K', 'Btu/ft3-F', 'kWh/m3-K', 'kBtu/ft3-F', 'kJ/m3-K', 'MJ/m3-K')
    _si_units = ('J/m3-K', 'kWh/m3-K', 'kJ/m3-K', 'MJ/m3-K')
    _ip_units = ('Btu/ft3-F', 'kBtu/ft3-F')
    _min = 0
    _abbreviation = 'c'

    def _J_m3K_to_Btu_ft3F(self, value):
        return value / 67066.1

    def _J_m3K_to_kWh_m3K(self, value):
        return value / 3600000.

    def _J_m3K_to_kBtu_ft3F(self, value):
        return value / 67066100.

    def _J_m3K_to_kJ_m3K(self, value):
        return value / 1000.

    def _J_m3K_to_MJ_m3K(self, value):
        return value / 1000000.

    def _Btu_ft3F_to_J_m3K(self, value):
        return value * 67066.1

    def _kWh_m3K_to_J_m3K(self, value):
        return value * 3600000.

    def _kBtu_ft3F_to_J_m3K(self, value):
        return value * 67066100.

    def _kJ_m3K_to_J_m3K(self, value):
        return value * 1000.

    def _MJ_m3K_to_J_m3K(self, value):
        return value * 1000000.

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('J/m3-K', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        if from_unit in self.ip_units:
            return values, from_unit
        elif from_unit == 'kWh/m3-K':
            return self.to_unit(values, 'kBtu/ft3-F', from_unit), 'kBtu/ft3-F'
        else:
            return self.to_unit(values, 'Btu/ft3-F', from_unit), 'Btu/ft3-F'

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        if from_unit in self.si_units:
            return values, from_unit
        elif from_unit == 'kBtu/ft3-F':
            return self.to_unit(values, 'kWh/m3-K', from_unit), 'kWh/m3-K'
        else:
            return self.to_unit(values, 'J/m3-K', from_unit), 'J/m3-K'
