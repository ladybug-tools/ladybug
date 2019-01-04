# coding=utf-8
"""Generic data type."""
from __future__ import division

from ._base import DataTypeBase


class Mass(DataTypeBase):
    """Mass"""
    name = 'Mass'
    units = ['kg', 'lb', 'g', 'tonne', 'ton', 'oz']
    min = 0
    abbreviation = 'm'

    def _kg_to_lb(self, value):
        return value * 2.20462

    def _kg_to_g(self, value):
        return value * 1000

    def _kg_to_tonne(self, value):
        return value / 1000

    def _kg_to_ton(self, value):
        return value / 907.185

    def _kg_to_oz(self, value):
        return value * 35.274

    def _lb_to_kg(self, value):
        return value / 2.20462

    def _g_to_kg(self, value):
        return value / 1000

    def _tonne_to_kg(self, value):
        return value * 1000

    def _ton_to_kg(self, value):
        return value * 907.185

    def _oz_to_kg(self, value):
        return value / 35.274

    def to_unit(self, values, unit, from_unit):
        """Return values in a given unit given the input from_unit."""
        return self._to_unit_base('kg', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP given the input from_unit."""
        ip_units = ['lb', 'ton']
        if from_unit in ip_units:
            return values, from_unit
        elif from_unit == 'tonne':
            return self.to_unit(values, 'ton', from_unit), 'ton'
        else:
            return self.to_unit(values, 'lb', from_unit), 'lb'

    def to_si(self, values, from_unit):
        """Return values in SI given the input from_unit."""
        si_units = ['kg', 'g', 'tonne']
        if from_unit in si_units:
            return values, from_unit
        elif from_unit == 'ton':
            return self.to_unit(values, 'tonne', from_unit), 'tonne'
        else:
            return self.to_unit(values, 'kg', from_unit), 'kg'

    @property
    def isMass(self):
        """Return True."""
        return True
