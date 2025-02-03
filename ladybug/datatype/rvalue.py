# coding=utf-8
"""R-Value data type."""
from __future__ import division

from .base import DataTypeBase


class RValue(DataTypeBase):
    """R Value
    """
    _units = ('K-m2/W', 'F-ft2-h/Btu', 'clo', 'm2-K/W', 'h-ft2-F/Btu')
    _si_units = ('K-m2/W', 'm2-K/W', 'clo')
    _ip_units = ('F-ft2-h/Btu', 'h-ft2-F/Btu', 'clo')
    _min = 0
    _abbreviation = 'Rval'

    def _Km2_W_to_Fft2h_Btu(self, value):
        return value * 5.678263337

    def _Km2_W_to_clo(self, value):
        return value / 0.155

    def _Km2_W_to_m2K_W(self, value):
        return value

    def _Km2_W_to_hft2F_Btu(self, value):
        return value * 5.678263337

    def _Fft2h_Btu_to_Km2_W(self, value):
        return value / 5.678263337

    def _clo_to_Km2_W(self, value):
        return value * 0.155

    def _m2K_W_to_Km2_W(self, value):
        return value

    def _hft2F_Btu_to_Km2_W(self, value):
        return value / 5.678263337

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('K-m2/W', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        if from_unit in self.ip_units:
            return values, from_unit
        else:
            return self.to_unit(values, 'F-ft2-h/Btu', from_unit), 'F-ft2-h/Btu'

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        if from_unit in self.si_units:
            return values, from_unit
        else:
            return self.to_unit(values, 'K-m2/W', from_unit), 'K-m2/W'


class ClothingInsulation(RValue):
    _abbreviation = 'Rclo'
