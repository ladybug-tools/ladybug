# coding=utf-8
"""Speed data type."""
from __future__ import division

from .base import DataTypeBase
from .distance import Distance


class Speed(DataTypeBase):
    """Speed
    """
    _units = ('m/s', 'mph', 'km/h', 'knot', 'ft/s')
    _si_units = ('m/s', 'km/h')
    _ip_units = ('mph', 'ft/s')
    _min = 0
    _abbreviation = 'v'
    _time_aggregated_type = Distance
    _time_aggregated_factor = 3600

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
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('m/s', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        if from_unit in self.ip_units:
            return values, from_unit
        else:
            return self.to_unit(values, 'mph', from_unit), 'mph'

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        if from_unit in self.si_units:
            return values, from_unit
        else:
            return self.to_unit(values, 'm/s', from_unit), 'm/s'


class WindSpeed(Speed):
    _abbreviation = 'WS'


class AirSpeed(Speed):
    _abbreviation = 'vair'
