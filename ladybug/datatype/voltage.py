# coding=utf-8
"""Voltage data type."""
from __future__ import division

from .base import DataTypeBase


class Voltage(DataTypeBase):
    """Voltage
    """
    _units = ('V', 'kV')
    _si_units = ('V', 'kV')
    _ip_units = ('V', 'kV')
    _abbreviation = 'V'

    def _V_to_kV(self, value):
        return value / 1000.

    def _kV_to_V(self, value):
        return value * 1000.

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('V', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        return values, from_unit

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        return values, from_unit
