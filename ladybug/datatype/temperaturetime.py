# coding=utf-8
"""Temperature-Time data type."""
from __future__ import division

from .base import DataTypeBase


class TemperatureTime(DataTypeBase):
    """Temperature-Time
    """
    _units = ('degC-days', 'degF-days', 'degC-hours', 'degF-hours')
    _si_units = ('degC-days', 'degC-hours')
    _ip_units = ('degF-days', 'degF-hours')
    _cumulative = True
    _abbreviation = 'degTime'

    def _degCdays_to_degFdays(self, value):
        return value * 9. / 5.

    def _degCdays_to_degChours(self, value):
        return value * 24.

    def _degCdays_to_degFhours(self, value):
        return value * 24. * 9. / 5.

    def _degFdays_to_degCdays(self, value):
        return value * 5. / 9.

    def _degChours_to_degCdays(self, value):
        return value / 24.

    def _degFhours_to_degCdays(self, value):
        return (value / 24.) * 5. / 9.

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('degC-days', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        if from_unit in self._ip_units:
            return values, from_unit
        elif from_unit == 'degC-hours':
            return self.to_unit(values, 'degF-hours', from_unit), 'degF-hours'
        else:
            return self.to_unit(values, 'degF-days', from_unit), 'degF-days'

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        if from_unit in self._si_units:
            return values, from_unit
        elif from_unit == 'degF-hours':
            return self.to_unit(values, 'degC-hours', from_unit), 'degC-hours'
        else:
            return self.to_unit(values, 'degC-days', from_unit), 'degC-days'


class CoolingDegreeTime(TemperatureTime):
    _abbreviation = 'coolTime'


class HeatingDegreeTime(TemperatureTime):
    _abbreviation = 'heatTime'
