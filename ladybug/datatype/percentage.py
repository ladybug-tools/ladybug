# coding=utf-8
"""Percentage data type."""
from __future__ import division

from .base import DataTypeBase


class Percentage(DataTypeBase):
    """Percentage"""
    _units = ('%', 'fraction', 'tenths', 'thousandths')
    _si_units = ('%', 'fraction', 'tenths', 'thousandths')
    _ip_units = ('%', 'fraction', 'tenths', 'thousandths')
    _abbreviation = 'Pct'

    def _pct_to_fraction(self, value):
        return value / 100.

    def _pct_to_tenths(self, value):
        return value / 10.

    def _pct_to_thousandths(self, value):
        return value * 10.

    def _fraction_to_pct(self, value):
        return value * 100.

    def _tenths_to_pct(self, value):
        return value * 10.

    def _thousandths_to_pct(self, value):
        return value / 10.

    def to_unit(self, values, unit, from_unit):
        """Return values in a given unit given the input from_unit."""
        return self._to_unit_base('%', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP given the input from_unit."""
        return values, from_unit

    def to_si(self, values, from_unit):
        """Return values in SI given the input from_unit."""
        return values, from_unit

    @property
    def isPercentage(self):
        """Return True."""
        return True


class PercentagePeopleDissatisfied(Percentage):
    _min = 0
    _max = 100
    _abbreviation = 'PPD'


class ThermalComfort(Percentage):
    _min = 0
    _max = 100
    _abbreviation = 'TC'
    _unit_descr = '1 = comfortable, 0 = uncomfortable'


class RelativeHumidity(Percentage):
    _min = 0
    _abbreviation = 'RH'
    _min_epw = 0
    _max_epw = 110
    _missing_epw = 999


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
