# coding=utf-8
"""Mass flow rate data type."""
from __future__ import division

from .base import DataTypeBase
from .mass import Mass


class MassFlowRate(DataTypeBase):
    """MassFlowRate
    """
    _units = ('kg/s', 'lb/s', 'g/s', 'oz/s')
    _si_units = ('kg/s', 'g/s')
    _ip_units = ('lb/s', 'oz/s')
    _min = 0
    _abbreviation = 'dm/dt'
    _time_aggregated_type = Mass
    _time_aggregated_factor = 3600

    def _kg_s_to_lb_s(self, value):
        return value * 2.2046

    def _kg_s_to_g_s(self, value):
        return value * 1000.

    def _kg_s_to_oz_s(self, value):
        return value * 35.274

    def _lb_s_to_kg_s(self, value):
        return value / 2.20462

    def _g_s_to_kg_s(self, value):
        return value / 1000.

    def _oz_s_to_kg_s(self, value):
        return value / 35.274

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('kg/s', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        if from_unit in self.ip_units:
            return values, from_unit
        elif from_unit == 'g/s':
            return self.to_unit(values, 'oz/s', from_unit), 'oz/s'
        else:
            return self.to_unit(values, 'lb/s', from_unit), 'lb/s'

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        if from_unit in self.si_units:
            return values, from_unit
        elif from_unit == 'oz/s':
            return self.to_unit(values, 'g/s', from_unit), 'g/s'
        else:
            return self.to_unit(values, 'kg/s', from_unit), 'kg/s'
