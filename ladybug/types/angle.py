# coding=utf-8
"""Generic data type."""
from __future__ import division

from ._base import DataTypeBase

import math
PI = math.pi


class Angle(DataTypeBase):
    """Angle"""
    name = 'Angle'
    units = ['degrees', 'radians']
    abbreviation = 'theta'

    def _degrees_to_radians(self, value):
        return (value * PI) / 180

    def _radians_to_degrees(self, value):
        return (value / PI) * 180

    def to_unit(self, values, unit, from_unit):
        """Return values in a given unit given the input from_unit."""
        return self._to_unit_base('degrees', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP."""
        return values, from_unit

    def to_si(self, values, from_unit):
        """Return values in SI."""
        return values, from_unit

    @property
    def isAngle(self):
        """Return True."""
        return True


class WindDirection(Angle):
    name = 'Wind Direction'
    abbreviation = 'WD'
    min_epw = 0
    max_epw = 360
    missing_epw = 999
