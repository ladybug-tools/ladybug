# coding=utf-8
"""R-Value data type."""
from __future__ import division

from .base import DataTypeBase


class RValue(DataTypeBase):
    """R Value
    """
    _units = ('m2-K/W', 'h-ft2-F/Btu', 'clo')
    _si_units = ('m2-K/W', 'clo')
    _ip_units = ('h-ft2-F/Btu', 'clo')
    _min = 0
    _abbreviation = 'Rval'

    def _m2K_W_to_hft2F_Btu(self, value):
        return value * 5.678263337

    def _m2K_W_to_clo(self, value):
        return value / 0.155

    def _hft2F_Btu_to_m2K_W(self, value):
        return value / 5.678263337

    def _clo_to_m2K_W(self, value):
        return value * 0.155

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('m2-K/W', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        if from_unit in self.ip_units:
            return values, from_unit
        else:
            return self.to_unit(values, 'h-ft2-F/Btu', from_unit), 'h-ft2-F/Btu'

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        if from_unit in self.si_units:
            return values, from_unit
        else:
            return self.to_unit(values, 'm2-K/W', from_unit), 'm2-K/W'


class ClothingInsulation(RValue):
    _abbreviation = 'Rclo'
    _unit_descr = {0: 'No Clothing', 0.5: 'T-shirt + Shorts', 1: '3-piece Suit'}
