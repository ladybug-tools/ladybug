# coding=utf-8
"""Volume data type."""
from __future__ import division

from ._base import DataTypeBase


class Volume(DataTypeBase):
    """Volume"""
    name = 'Volume'
    units = ['m3', 'ft3', 'mm3', 'in3', 'km3', 'mi3', 'L', 'mL', 'gal', 'fl oz']
    min = 0
    abbreviation = 'V'

    def _m3_to_ft3(self, value):
        return value * 35.3147

    def _m3_to_mm3(self, value):
        return value * 1e+9

    def _m3_to_in3(self, value):
        return value * 61023.7

    def _m3_to_km3(self, value):
        return value / 1e+9

    def _m3_to_mi3(self, value):
        return value / 4.168e+9

    def _m3_to_L(self, value):
        return value * 1000

    def _m3_to_mL(self, value):
        return value * 1000000

    def _m3_to_gal(self, value):
        return value * 264.172

    def _m3_to_floz(self, value):
        return value * 33814

    def _ft3_to_m3(self, value):
        return value / 35.3147

    def _mm3_to_m3(self, value):
        return value / 1e+9

    def _in3_to_m3(self, value):
        return value / 61023.7

    def _km3_to_m3(self, value):
        return value * 1e+9

    def _mi3_to_m3(self, value):
        return value * 4.168e+9

    def _L_to_m3(self, value):
        return value / 1000

    def _mL_to_m3(self, value):
        return value / 1000000

    def _gal_to_m3(self, value):
        return value / 264.172

    def _floz_to_m3(self, value):
        return value / 33814

    def to_unit(self, values, unit, from_unit):
        """Return values in a given unit given the input from_unit."""
        return self._to_unit_base('m3', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP given the input from_unit."""
        ip_units = ['ft3', 'in3', 'mi3', 'gal', 'fl oz']
        if from_unit in ip_units:
            return values, from_unit
        elif from_unit == 'mL' or from_unit == 'mm3':
            return self.to_unit(values, 'fl oz', from_unit), 'fl oz'
        elif from_unit == 'km3':
            return self.to_unit(values, 'mi3', from_unit), 'mi3'
        elif from_unit == 'L':
            return self.to_unit(values, 'gal', from_unit), 'gal'
        else:
            return self.to_unit(values, 'ft3', from_unit), 'ft3'

    def to_si(self, values, from_unit):
        """Return values in SI given the input from_unit."""
        si_units = ['m3', 'mm3', 'km3', 'L', 'mL']
        if from_unit in si_units:
            return values, from_unit
        elif from_unit == 'in3' or from_unit == 'fl oz':
            return self.to_unit(values, 'mL', from_unit), 'mL'
        elif from_unit == 'mi3':
            return self.to_unit(values, 'km3', from_unit), 'km3'
        elif from_unit == 'gal':
            return self.to_unit(values, 'L', from_unit), 'L'
        else:
            return self.to_unit(values, 'm3', from_unit), 'm3'

    @property
    def isVolume(self):
        """Return True."""
        return True
