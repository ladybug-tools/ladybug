# coding=utf-8
"""Luminance data type."""
from __future__ import division

from ._base import DataTypeBase


class Luminance(DataTypeBase):
    """Luminance"""
    name = 'Luminance'
    units = ['cd/m2', 'cd/ft2']
    min = 0
    abbreviation = 'Lv'
    point_in_time = False
    min_epw = 0
    missing_epw = 9999  # note will be missing if >= 999900

    def _cd_m2_to_cd_ft2(self, value):
        return value / 10.7639

    def _cd_ft2_to_cd_m2(self, value):
        return value * 10.7639

    def to_unit(self, values, unit, from_unit):
        """Return values in a given unit given the input from_unit."""
        return self._to_unit_base('cd/m2', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in cd/ft2 given the input from_unit."""
        if from_unit == 'cd/ft2':
            return values, from_unit
        else:
            return self.to_unit(values, 'cd/ft2', from_unit), 'cd/ft2'

    def to_si(self, values, from_unit):
        """Return values in cd/m2 given the input from_unit."""
        if from_unit == 'cd/m2':
            return values, from_unit
        else:
            return self.to_unit(values, 'cd/m2', from_unit), 'cd/m2'

    @property
    def isLuminance(self):
        """Return True."""
        return True


class ZenithLuminance(Luminance):
    name = 'Zenith Luminance'
    abbreviation = 'ZL'
