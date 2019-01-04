# coding=utf-8
"""Illuminance data type."""
from __future__ import division

from ._base import DataTypeBase


class Illuminance(DataTypeBase):
    """Illuminance"""
    name = 'Illuminance'
    units = ['lux', 'fc']
    min = 0
    abbreviation = 'Ev'
    point_in_time = False
    min_epw = 0
    missing_epw = 999999  # note will be missing if >= 999900

    def _lux_to_fc(self, value):
        return value / 10.7639

    def _fc_to_lux(self, value):
        return value * 10.7639

    def to_unit(self, values, unit, from_unit):
        """Return values in a given unit given the input from_unit."""
        return self._to_unit_base('lux', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in fc given the input from_unit."""
        if from_unit == 'fc':
            return values, from_unit
        else:
            return self.to_unit(values, 'fc', from_unit), 'fc'

    def to_si(self, values, from_unit):
        """Return values in lux given the input from_unit."""
        if from_unit == 'lux':
            return values, from_unit
        else:
            return self.to_unit(values, 'lux', from_unit), 'lux'

    @property
    def isIlluminance(self):
        """Return True."""
        return True


class GlobalHorizontalIlluminance(Illuminance):
    name = 'Global Horizontal Illuminance'
    abbreviation = 'GHI'


class DirectNormalIlluminance(Illuminance):
    name = 'Direct Normal Illuminance'
    abbreviation = 'DNI'


class DiffuseHorizontalIlluminance(Illuminance):
    name = 'Diffuse Horizontal Illuminance'
    abbreviation = 'DHI'
