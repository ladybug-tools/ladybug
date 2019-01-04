# coding=utf-8
"""Area data type."""
from __future__ import division

from ._base import DataTypeBase


class Area(DataTypeBase):
    """Area"""
    name = 'Area'
    units = ['m2', 'ft2', 'mm2', 'in2', 'km2', 'mi2', 'cm2', 'ha', 'acre']
    min = 0
    abbreviation = 'A'

    def _m2_to_ft2(self, value):
        return value * 10.7639

    def _m2_to_mm2(self, value):
        return value * 1000000

    def _m2_to_in2(self, value):
        return value * 1550

    def _m2_to_km2(self, value):
        return value / 1000000

    def _m2_to_mi2(self, value):
        return value / 2590000

    def _m2_to_cm2(self, value):
        return value * 10000

    def _m2_to_ha(self, value):
        return value / 10000

    def _m2_to_acre(self, value):
        return value / 4046.86

    def _ft2_to_m2(self, value):
        return value / 10.7639

    def _mm2_to_m2(self, value):
        return value / 1000000

    def _in2_to_m2(self, value):
        return value / 1550

    def _km2_to_m2(self, value):
        return value * 1000000

    def _mi2_to_m2(self, value):
        return value * 2590000

    def _cm2_to_m2(self, value):
        return value / 10000

    def _ha_to_m2(self, value):
        return value * 10000

    def _acre_to_m2(self, value):
        return value * 4046.86

    def to_unit(self, values, unit, from_unit):
        """Return values in a given unit given the input from_unit."""
        return self._to_unit_base('m2', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP given the input from_unit."""
        ip_units = ['ft2', 'in2', 'mi2', 'acre']
        if from_unit in ip_units:
            return values, from_unit
        elif from_unit == 'mm2' or from_unit == 'cm2':
            return self.to_unit(values, 'in2', from_unit), 'in2'
        elif from_unit == 'km2':
            return self.to_unit(values, 'mi2', from_unit), 'mi2'
        elif from_unit == 'ha':
            return self.to_unit(values, 'acre', from_unit), 'acre'
        else:
            return self.to_unit(values, 'ft2', from_unit), 'ft2'

    def to_si(self, values, from_unit):
        """Return values in SI given the input from_unit."""
        si_units = ['m2', 'mm2', 'km2', 'cm2', 'ha']
        if from_unit in si_units:
            return values, from_unit
        elif from_unit == 'in2':
            return self.to_unit(values, 'mm2', from_unit), 'mm2'
        elif from_unit == 'mi2':
            return self.to_unit(values, 'km2', from_unit), 'km2'
        elif from_unit == 'acre':
            return self.to_unit(values, 'ha', from_unit), 'ha'
        else:
            return self.to_unit(values, 'm2', from_unit), 'm2'

    @property
    def isArea(self):
        """Return True."""
        return True
