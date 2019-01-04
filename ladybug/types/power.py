# coding=utf-8
"""Generic data type."""
from __future__ import division

from ._base import DataTypeBase


class Power(DataTypeBase):
    """Power"""
    name = 'Power'
    units = ['W', 'Btu/h', 'kW', 'kBtu/h', 'TR', 'hp']
    abbreviation = 'Q'
    point_in_time = False

    def _W_to_Btu_h(self, value):
        return value * 3.41214

    def _W_to_kW(self, value):
        return value / 1000

    def _W_to_kBtu_h(self, value):
        return value * 0.00341214

    def _W_to_TR(self, value):
        return value / 3516.85

    def _W_to_hp(self, value):
        return value / 745.7

    def _Btu_h_to_W(self, value):
        return value / 3.41214

    def _kW_to_W(self, value):
        return value * 1000

    def _kBtu_h_to_W(self, value):
        return value / 0.00341214

    def _TR_to_W(self, value):
        return value * 3516.85

    def _hp_to_W(self, value):
        return value * 745.7

    def to_unit(self, values, unit, from_unit):
        """Return values in a given unit given the input from_unit."""
        return self._to_unit_base('W', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP given the input from_unit."""
        ip_units = ['Btu/h', 'kBtu/h', 'TR', 'hp']
        if from_unit in ip_units:
            return values, from_unit
        elif from_unit == 'kW':
            return self.to_unit(values, 'kBtu/h', from_unit), 'kBtu/h'
        else:
            return self.to_unit(values, 'Btu/h', from_unit), 'Btu/h'

    def to_si(self, values, from_unit):
        """Return values in SI given the input from_unit."""
        si_units = ['kW', 'W']
        if from_unit in si_units:
            return values, from_unit
        elif from_unit == 'kBtu/h':
            return self.to_unit(values, 'kW', from_unit), 'kW'
        else:
            return self.to_unit(values, 'W', from_unit), 'W'

    @property
    def isPower(self):
        """Return True."""
        return True
