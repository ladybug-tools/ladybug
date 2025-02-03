# coding=utf-8
"""Conductance data type."""
from __future__ import division

from .base import DataTypeBase


class Conductance(DataTypeBase):
    """Conductance
    """
    _units = ('W/K', 'Btu/h-F')
    _si_units = ('W/K')
    _ip_units = ('Btu/h-F')
    _min = 0
    _abbreviation = 'G'

    def _W_K_to_Btu_hF(self, value):
        return value / 0.5271751322

    def _Btu_hF_to_W_K(self, value):
        return value * 0.5271751322

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('W/K', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        if from_unit == 'Btu/h-F':
            return values, from_unit
        else:
            return self.to_unit(values, 'Btu/h-F', from_unit), 'Btu/h-F'

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        if from_unit == 'W/K':
            return values, from_unit
        else:
            return self.to_unit(values, 'W/K', from_unit), 'W/K'
