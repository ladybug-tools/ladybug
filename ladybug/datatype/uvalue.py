# coding=utf-8
"""U-Value data type."""
from __future__ import division

from .base import DataTypeBase


class UValue(DataTypeBase):
    """U Value
    """
    _units = ('W/m2-K', 'Btu/h-ft2-F')
    _si_units = ('W/m2-K')
    _ip_units = ('Btu/h-ft2-F')
    _min = 0
    _abbreviation = 'Uval'

    def _W_m2K_to_Btu_hft2F(self, value):
        return value / 5.678263337

    def _Btu_hft2F_to_W_m2K(self, value):
        return value * 5.678263337

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('W/m2-K', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        if from_unit == 'Btu/h-ft2-F':
            return values, from_unit
        else:
            return self.to_unit(values, 'Btu/h-ft2-F', from_unit), 'Btu/h-ft2-F'

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        if from_unit == 'W/m2-K':
            return values, from_unit
        else:
            return self.to_unit(values, 'W/m2-K', from_unit), 'W/m2-K'


class ConvectionCoefficient(UValue):
    _abbreviation = 'hc'


class RadiantCoefficient(UValue):
    _abbreviation = 'hr'
