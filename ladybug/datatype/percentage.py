# coding=utf-8
"""Percentage data type."""
from __future__ import division

from .base import DataTypeBase


class Percentage(DataTypeBase):
    """Percentage"""
    _units = ('%', 'fraction', 'tenths', 'thousandths', 'okta')
    _si_units = ('%', 'fraction', 'tenths', 'thousandths', 'okta')
    _ip_units = ('%', 'fraction', 'tenths', 'thousandths', 'okta')
    _abbreviation = 'Pct'

    def _pct_to_fraction(self, value):
        return value / 100.

    def _pct_to_tenths(self, value):
        return value / 10.

    def _pct_to_thousandths(self, value):
        return value * 10.

    def _pct_to_okta(self, value):
        return value / 12.5

    def _fraction_to_pct(self, value):
        return value * 100.

    def _tenths_to_pct(self, value):
        return value * 10.

    def _thousandths_to_pct(self, value):
        return value / 10.

    def _okta_to_pct(self, value):
        return value * 12.5

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('%', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        return values, from_unit

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        return values, from_unit

    @property
    def isPercentage(self):
        """Return True."""
        return True


class PercentagePeopleDissatisfied(Percentage):
    _min = 0
    _max = 100
    _abbreviation = 'PPD'


class RelativeHumidity(Percentage):
    _min = 0
    _abbreviation = 'RH'
    _min_epw = 0
    _max_epw = 110
    _missing_epw = 999


class HumidityRatio(Percentage):
    _min = 0
    _max = 100
    _abbreviation = 'HR'


class TotalSkyCover(Percentage):
    # (used if Horizontal IR Intensity missing)
    _min = 0
    _max = 100
    _abbreviation = 'CC'
    _min_epw = 0
    _max_epw = 100
    _missing_epw = 99


class OpaqueSkyCover(Percentage):
    # (used if Horizontal IR Intensity missing)
    _min = 0
    _max = 100
    _abbreviation = 'OSC'
    _min_epw = 0
    _max_epw = 100
    _missing_epw = 99


class AerosolOpticalDepth(Percentage):
    _min = 0
    _max = 100
    _abbreviation = 'AOD'
    _min_epw = 0
    _max_epw = 100
    _missing_epw = 0.999


class Albedo(Percentage):
    _min = 0
    _max = 100
    _abbreviation = 'a'
    _min_epw = 0
    _max_epw = 100
    _missing_epw = 0.999


class LiquidPrecipitationQuantity(Percentage):
    _min = 0
    _abbreviation = 'LPQ'
    _min_epw = 0
    _max_epw = 100
    _missing_epw = 99
