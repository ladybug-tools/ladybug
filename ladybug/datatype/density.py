# coding=utf-8
"""Density data type."""
from __future__ import division

from .base import DataTypeBase


class Density(DataTypeBase):
    """Density
    """
    _units = ('kg/m3', 'lb/ft3', 'g/cm3', 'oz/in3')
    _si_units = ('kg/m3', 'g/cm3')
    _ip_units = ('lb/ft3', 'oz/in3')
    _min = 0
    _abbreviation = 'rho'

    def _kg_m3_to_lb_ft3(self, value):
        return value * 0.062428

    def _kg_m3_to_g_cm3(self, value):
        return value * 0.001

    def _kg_m3_to_oz_in3(self, value):
        return value * 0.000578037

    def _lb_ft3_to_kg_m3(self, value):
        return value / 0.062428

    def _g_cm3_to_kg_m3(self, value):
        return value / 0.001

    def _oz_in3_to_kg_m3(self, value):
        return value / 0.000578037

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('kg/m3', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        if from_unit in self.ip_units:
            return values, from_unit
        elif from_unit == 'g/cm3':
            return self.to_unit(values, 'oz/in3', from_unit), 'oz/in3'
        else:
            return self.to_unit(values, 'lb/ft3', from_unit), 'lb/ft3'

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        if from_unit in self.si_units:
            return values, from_unit
        elif from_unit == 'oz/in3':
            return self.to_unit(values, 'g/cm3', from_unit), 'g/cm3'
        else:
            return self.to_unit(values, 'kg/m3', from_unit), 'kg/m3'
