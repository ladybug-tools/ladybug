# coding=utf-8
"""Luminance data type."""
from __future__ import division

from .base import DataTypeBase


class Luminance(DataTypeBase):
    """Luminance
    """
    _units = ('cd/m2', 'cd/ft2')
    _si_units = ('cd/m2')
    _ip_units = ('cd/ft2')
    _min = 0
    _abbreviation = 'Lv'
    _point_in_time = False

    def _cd_m2_to_cd_ft2(self, value):
        return value / 10.7639

    def _cd_ft2_to_cd_m2(self, value):
        return value * 10.7639

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('cd/m2', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        if from_unit == 'cd/ft2':
            return values, from_unit
        else:
            return self.to_unit(values, 'cd/ft2', from_unit), 'cd/ft2'

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        if from_unit == 'cd/m2':
            return values, from_unit
        else:
            return self.to_unit(values, 'cd/m2', from_unit), 'cd/m2'


class ZenithLuminance(Luminance):
    _abbreviation = 'ZL'
