# coding=utf-8
"""Current data type."""
from __future__ import division

from .base import DataTypeBase


class Current(DataTypeBase):
    """Current
    """
    _units = ('A', 'mA')
    _si_units = ('A', 'mA')
    _ip_units = ('A', 'mA')
    _abbreviation = 'I'

    def _A_to_mA(self, value):
        return value * 1000.

    def _mA_to_A(self, value):
        return value / 1000.

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('A', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        return values, from_unit

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        return values, from_unit
