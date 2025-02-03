# coding=utf-8
"""Resistance data type."""
from __future__ import division

from .base import DataTypeBase


class Resistance(DataTypeBase):
    """Resistance
    """
    _units = ('K/W', 'F-h/Btu')
    _si_units = ('K/W',)
    _ip_units = ('F-h/Btu',)
    _min = 0
    _abbreviation = 'R'

    def _K_W_to_Fh_Btu(self, value):
        return value * 0.5271751322

    def _Fh_Btu_to_K_W(self, value):
        return value / 0.5271751322

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('K/W', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        if from_unit in self.ip_units:
            return values, from_unit
        else:
            return self.to_unit(values, 'F-h/Btu', from_unit), 'F-h/Btu'

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        if from_unit in self.si_units:
            return values, from_unit
        else:
            return self.to_unit(values, 'K/W', from_unit), 'K/W'
