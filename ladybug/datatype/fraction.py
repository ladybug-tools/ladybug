# coding=utf-8
"""Fraction data type."""
from __future__ import division

from .base import DataTypeBase


class Fraction(DataTypeBase):
    """Fraction
    """
    _units = ('fraction', '%', 'tenths', 'thousandths', 'okta')
    _si_units = ('fraction', '%', 'tenths', 'thousandths', 'okta')
    _ip_units = ('fraction', '%', 'tenths', 'thousandths', 'okta')
    _abbreviation = 'Pct'

    def _fraction_to_pct(self, value):
        return value * 100.

    def _fraction_to_tenths(self, value):
        return value * 10.

    def _fraction_to_thousandths(self, value):
        return value * 1000.

    def _fraction_to_okta(self, value):
        return value * 12.5

    def _pct_to_fraction(self, value):
        return value / 100.

    def _tenths_to_fraction(self, value):
        return value / 10.

    def _thousandths_to_fraction(self, value):
        return value / 1000.

    def _okta_to_fraction(self, value):
        return value / 12.5

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('fraction', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        return values, from_unit

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        return values, from_unit


class PercentagePeopleDissatisfied(Fraction):
    _min = 0
    _max = 1
    _abbreviation = 'PPD'


class RelativeHumidity(Fraction):
    _min = 0
    _abbreviation = 'RH'


class HumidityRatio(Fraction):
    _min = 0
    _max = 1
    _abbreviation = 'HR'


class TotalSkyCover(Fraction):
    # (used if Horizontal IR Intensity missing)
    _min = 0
    _max = 1
    _abbreviation = 'CC'


class OpaqueSkyCover(Fraction):
    # (used if Horizontal IR Intensity missing)
    _min = 0
    _max = 1
    _abbreviation = 'OSC'


class AerosolOpticalDepth(Fraction):
    _min = 0
    _max = 1
    _abbreviation = 'AOD'


class Albedo(Fraction):
    _min = 0
    _max = 1
    _abbreviation = 'a'


class LiquidPrecipitationQuantity(Fraction):
    _min = 0
    _abbreviation = 'LPQ'
