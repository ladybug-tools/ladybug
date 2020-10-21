# coding=utf-8
"""Time data type."""
from __future__ import division

from .base import DataTypeBase


class Time(DataTypeBase):
    """Time"""
    _units = ('hr', 'min', 'sec', 'day')
    _si_units = ('hr', 'min', 'sec', 'day')
    _ip_units = ('hr', 'min', 'sec', 'day')
    _cumulative = True
    _abbreviation = 't'

    def _hr_to_min(self, value):
        return value * 60.

    def _hr_to_sec(self, value):
        return value * 3600.

    def _hr_to_day(self, value):
        return value / 24.

    def _min_to_hr(self, value):
        return value / 60.

    def _sec_to_hr(self, value):
        return value / 3600.

    def _day_to_hr(self, value):
        return value * 24.

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('hr', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        return values, from_unit

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        return values, from_unit
