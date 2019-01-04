# coding=utf-8
"""Generic data type."""
from __future__ import division

from ._base import DataTypeBase


class Speed(DataTypeBase):
    """Speed"""
    name = 'Speed'
    units = ['m/s', 'mph', 'km/h', 'knot', 'ft/s']
    min = 0
    abbreviation = 'v'

    def _m_s_to_mph(self, value):
        return value * 2.23694

    def _m_s_to_km_h(self, value):
        return value * 3.6

    def _m_s_to_knot(self, value):
        return value * 1.94384

    def _m_s_to_ft_s(self, value):
        return value * 3.28084

    def _mph_to_m_s(self, value):
        return value / 2.23694

    def _km_h_to_m_s(self, value):
        return value / 3.6

    def _knot_to_m_s(self, value):
        return value / 1.94384

    def _ft_s_to_m_s(self, value):
        return value / 3.28084

    def to_unit(self, values, unit, from_unit):
        """Return values in a given unit given the input from_unit."""
        return self._to_unit_base('m/s', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP units given the input from_unit."""
        ip_units = ['mph', 'ft/s']
        if from_unit in ip_units:
            return values, from_unit
        else:
            return self.to_unit(values, 'mph', from_unit), 'mph'

    def to_si(self, values, from_unit):
        """Return values in SI units given the input from_unit."""
        si_units = ['m/s', 'km/h']
        if from_unit in si_units:
            return values, from_unit
        else:
            return self.to_unit(values, 'm/s', from_unit), 'm/s'

    @property
    def isSpeed(self):
        """Return True."""
        return True


class WindSpeed(Speed):
    name = 'Wind Speed'
    abbreviation = 'WS'
    min_epw = 0
    max_epw = 40
    missing_epw = 999


class AirSpeed(Speed):
    name = 'Air Speed'
    abbreviation = 'vair'
