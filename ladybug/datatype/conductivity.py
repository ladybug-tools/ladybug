# coding=utf-8
"""Conductivity data type."""
from __future__ import division

from .base import DataTypeBase


class Conductivity(DataTypeBase):
    """Conductivity
    """
    _units = ('W/m-K', 'Btu/h-ft-F', 'cal/s-cm-C')
    _si_units = ('W/m-K',)
    _ip_units = ('Btu/h-ft-F',)
    _min = 0
    _abbreviation = 'k'

    def _W_mK_to_Btu_hftF(self, value):
        return value / 1.7295772056

    def _Btu_hftF_to_W_mK(self, value):
        return value * 1.7295772056

    def _W_mK_to_cal_scmC(self, value):
        return value / 418.4

    def _cal_scmC_to_W_mK(self, value):
        return value * 418.4

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('W/m-K', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        if from_unit == 'Btu/h-ft-F':
            return values, from_unit
        else:
            return self.to_unit(values, 'Btu/h-ft-F', from_unit), 'Btu/h-ft-F'

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        if from_unit == 'W/m-K':
            return values, from_unit
        else:
            return self.to_unit(values, 'W/m-K', from_unit), 'W/m-K'
