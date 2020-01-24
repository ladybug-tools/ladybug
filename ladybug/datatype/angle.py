# coding=utf-8
"""Generic data type."""
from __future__ import division

from .base import DataTypeBase

import math
PI = math.pi


class Angle(DataTypeBase):
    """Angle
    """
    _units = ('degrees', 'radians')
    _si_units = ('degrees', 'radians')
    _ip_units = ('degrees', 'radians')
    _abbreviation = 'theta'

    def _degrees_to_radians(self, value):
        return (value * PI) / 180.

    def _radians_to_degrees(self, value):
        return (value / PI) * 180.

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('degrees', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        return values, from_unit

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        return values, from_unit


class WindDirection(Angle):
    _name = 'Wind Direction'
    _abbreviation = 'WD'
