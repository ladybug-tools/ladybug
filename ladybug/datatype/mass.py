# coding=utf-8
"""Mass data type."""
from __future__ import division

from .base import DataTypeBase


class Mass(DataTypeBase):
    """Mass
    """
    _units = ('kg', 'lb', 'g', 'tonne', 'ton', 'oz')
    _si_units = ('kg', 'g', 'tonne')
    _ip_units = ('lb', 'ton')
    _min = 0
    _cumulative = True
    _abbreviation = 'm'

    def _kg_to_lb(self, value):
        return value * 2.20462

    def _kg_to_g(self, value):
        return value * 1000.

    def _kg_to_tonne(self, value):
        return value / 1000.

    def _kg_to_ton(self, value):
        return value / 907.185

    def _kg_to_oz(self, value):
        return value * 35.274

    def _lb_to_kg(self, value):
        return value / 2.20462

    def _g_to_kg(self, value):
        return value / 1000.

    def _tonne_to_kg(self, value):
        return value * 1000.

    def _ton_to_kg(self, value):
        return value * 907.185

    def _oz_to_kg(self, value):
        return value / 35.274

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('kg', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        if from_unit in self.ip_units:
            return values, from_unit
        elif from_unit == 'tonne':
            return self.to_unit(values, 'ton', from_unit), 'ton'
        else:
            return self.to_unit(values, 'lb', from_unit), 'lb'

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        if from_unit in self.si_units:
            return values, from_unit
        elif from_unit == 'ton':
            return self.to_unit(values, 'tonne', from_unit), 'tonne'
        else:
            return self.to_unit(values, 'kg', from_unit), 'kg'
