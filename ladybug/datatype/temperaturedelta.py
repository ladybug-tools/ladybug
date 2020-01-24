# coding=utf-8
"""Temperature Delta data type."""
from __future__ import division

from .base import DataTypeBase


class TemperatureDelta(DataTypeBase):
    """TemperatureDelta
    """
    _units = ('C', 'F', 'K')
    _si_units = ('C', 'K')
    _ip_units = ('F')
    _abbreviation = 'DeltaT'

    def _C_to_F(self, value):
        return value * 9. / 5.

    def _C_to_K(self, value):
        return value

    def _F_to_C(self, value):
        return value * (5. / 9.)

    def _K_to_C(self, value):
        return value

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('C', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        if from_unit == 'F':
            return values, from_unit
        else:
            return self.to_unit(values, 'F', from_unit), 'F'

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        if from_unit == 'C' or from_unit == 'K':
            return values, from_unit
        else:
            return self.to_unit(values, 'C', from_unit), 'C'


class AirTemperatureDelta(TemperatureDelta):
    _abbreviation = 'DeltaTair'


class RadiantTemperatureDelta(TemperatureDelta):
    _abbreviation = 'DeltaTrad'


class OperativeTemperatureDelta(TemperatureDelta):
    _abbreviation = 'DeltaTo'
