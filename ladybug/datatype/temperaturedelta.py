# coding=utf-8
"""Temperature Delta data type."""
from __future__ import division

from .base import DataTypeBase
from .temperaturetime import TemperatureTime


class TemperatureDelta(DataTypeBase):
    """TemperatureDelta
    """
    _units = ('dC', 'dF', 'dK')
    _si_units = ('dC', 'dK')
    _ip_units = ('dF')
    _abbreviation = 'DeltaT'
    _time_aggregated_type = TemperatureTime
    _time_aggregated_factor = 1. / 24.

    def _dC_to_dF(self, value):
        return value * 9. / 5.

    def _dC_to_dK(self, value):
        return value

    def _dF_to_dC(self, value):
        return value * (5. / 9.)

    def _dK_to_dC(self, value):
        return value

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('dC', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        if from_unit == 'dF':
            return values, from_unit
        else:
            return self.to_unit(values, 'dF', from_unit), 'dF'

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        if from_unit == 'dC' or from_unit == 'dK':
            return values, from_unit
        else:
            return self.to_unit(values, 'dC', from_unit), 'dC'


class AirTemperatureDelta(TemperatureDelta):
    _abbreviation = 'DeltaTair'


class RadiantTemperatureDelta(TemperatureDelta):
    _abbreviation = 'DeltaTrad'


class OperativeTemperatureDelta(TemperatureDelta):
    _abbreviation = 'DeltaTo'
