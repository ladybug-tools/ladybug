# coding=utf-8
"""Distance data type."""
from __future__ import division

from ._base import DataTypeBase


class Distance(DataTypeBase):
    """Distance"""
    name = 'Distance'
    units = ['m', 'ft', 'mm', 'in', 'km', 'mi', 'cm']
    min = 0
    abbreviation = 'D'

    def _m_to_ft(self, value):
        return value * 3.28084

    def _m_to_mm(self, value):
        return value * 1000

    def _m_to_in(self, value):
        return value * 39.3701

    def _m_to_km(self, value):
        return value / 1000

    def _m_to_mi(self, value):
        return value / 1609.344

    def _m_to_cm(self, value):
        return value * 100

    def _ft_to_m(self, value):
        return value / 3.28084

    def _mm_to_m(self, value):
        return value / 1000

    def _in_to_m(self, value):
        return value / 39.3701

    def _km_to_m(self, value):
        return value * 1000

    def _mi_to_m(self, value):
        return value * 1609.344

    def _cm_to_m(self, value):
        return value / 100

    def to_unit(self, values, unit, from_unit):
        """Return values in a given unit given the input from_unit."""
        return self._to_unit_base('m', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP given the input from_unit."""
        ip_units = ['ft', 'in', 'mi']
        if from_unit in ip_units:
            return values, from_unit
        elif from_unit == 'mm':
            return self.to_unit(values, 'in', from_unit), 'in'
        elif from_unit == 'km':
            return self.to_unit(values, 'mi', from_unit), 'mi'
        else:
            return self.to_unit(values, 'ft', from_unit), 'ft'

    def to_si(self, values, from_unit):
        """Return values in SI given the input from_unit."""
        si_units = ['m', 'mm', 'km', 'cm']
        if from_unit in si_units:
            return values, from_unit
        elif from_unit == 'in':
            return self.to_unit(values, 'mm', from_unit), 'mm'
        elif from_unit == 'mi':
            return self.to_unit(values, 'km', from_unit), 'km'
        else:
            return self.to_unit(values, 'm', from_unit), 'm'

    @property
    def isDistance(self):
        """Return True."""
        return True


class Visibility(Distance):
    name = 'Visibility'
    abbreviation = 'Vis'
    missing_epw = 9999


class CeilingHeight(Distance):
    name = 'Ceiling Height'
    abbreviation = 'Hciel'
    missing_epw = 99999


class PrecipitableWater(Distance):
    name = 'Precipitable Water'
    abbreviation = 'PW'
    missing_epw = 999


class SnowDepth(Distance):
    name = 'Snow Depth'
    abbreviation = 'Dsnow'
    missing_epw = 999


class LiquidPrecipitationDepth(Distance):
    name = 'Liquid Precipitation Depth'
    abbreviation = 'LPD'
    missing_epw = 999
