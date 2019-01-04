# coding=utf-8
"""Percentage data type."""
from __future__ import division

from ._base import DataTypeBase


class Percentage(DataTypeBase):
    """Percentage"""
    name = 'Percentage'
    units = ['%', 'fraction', 'tenths', 'thousandths']
    abbreviation = 'Pct'

    def _pct_to_fraction(self, value):
        return value / 100

    def _pct_to_tenths(self, value):
        return value / 10

    def _pct_to_thousandths(self, value):
        return value * 10

    def _fraction_to_pct(self, value):
        return value * 100

    def _tenths_to_pct(self, value):
        return value * 10

    def _thousandths_to_pct(self, value):
        return value / 10

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
    name = 'Percentage People Dissatisfied'
    min = 0
    max = 100
    abbreviation = 'PPD'


class ThermalComfort(Percentage):
    name = 'Thermal Comfort'
    min = 0
    max = 100
    abbreviation = 'TC'
    unit_descr = '1 = comfortable, 0 = uncomfortable'


class RelativeHumidity(Percentage):
    name = 'Relative Humidity'
    min = 0
    abbreviation = 'RH'
    min_epw = 0
    max_epw = 110
    missing_epw = 999


class TotalSkyCover(Percentage):
    # (used if Horizontal IR Intensity missing)
    name = 'Total Sky Cover'
    min = 0
    max = 100
    abbreviation = 'CC'
    min_epw = 0
    max_epw = 100
    missing_epw = 99


class OpaqueSkyCover(Percentage):
    # (used if Horizontal IR Intensity missing)
    name = 'Opaque Sky Cover'
    min = 0
    max = 100
    abbreviation = 'OSC'
    min_epw = 0
    max_epw = 100
    missing_epw = 99


class AerosolOpticalDepth(Percentage):
    name = 'Aerosol Optical Depth'
    min = 0
    max = 100
    abbreviation = 'AOD'
    min_epw = 0
    max_epw = 100
    missing_epw = 0.999


class Albedo(Percentage):
    name = 'Albedo'
    min = 0
    max = 100
    abbreviation = 'a'
    min_epw = 0
    max_epw = 100
    missing_epw = 0.999


class LiquidPrecipitationQuantity(Percentage):
    name = 'LiquidPrecipitationQuantity'
    min = 0
    abbreviation = 'LPQ'
    min_epw = 0
    max_epw = 100
    missing_epw = 99
