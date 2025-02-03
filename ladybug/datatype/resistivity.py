# coding=utf-8
"""Resistivity data type."""
from __future__ import division

from .base import DataTypeBase


class Resistivity(DataTypeBase):
    """Resistivity
    """
    _units = ('K-m/W', 'F-ft-h/Btu')
    _si_units = ('K-m/W',)
    _ip_units = ('F-ft-h/Btu',)
    _min = 0
    _abbreviation = 'rho'

    def _Km_W_to_Ffth_Btu(self, value):
        return value * 1.7295772056

    def _Ffth_Btu_to_Km_W(self, value):
        return value / 1.7295772056

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('K-m/W', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        if from_unit in self.ip_units:
            return values, from_unit
        else:
            return self.to_unit(values, 'F-ft-h/Btu', from_unit), 'F-ft-h/Btu'

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        if from_unit in self.si_units:
            return values, from_unit
        else:
            return self.to_unit(values, 'K-m/W', from_unit), 'K-m/W'
