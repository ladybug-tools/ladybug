# coding=utf-8
"""Pressure data type."""
from __future__ import division

from .base import DataTypeBase


class Pressure(DataTypeBase):
    """Pressure
    """
    _units = ('Pa', 'inHg', 'atm', 'bar', 'Torr', 'psi', 'inH2O')
    _si_units = ('Pa', 'bar')
    _ip_units = ('inHg', 'psi', 'inH2O')
    _abbreviation = 'P'
    _point_in_time = False

    def _Pa_to_inHg(self, value):
        return value * 0.0002953

    def _Pa_to_atm(self, value):
        return value / 101325.

    def _Pa_to_bar(self, value):
        return value / 100000.

    def _Pa_to_Torr(self, value):
        return value * 0.00750062

    def _Pa_to_psi(self, value):
        return value * 0.000145038

    def _Pa_to_inH2O(self, value):
        return value * 0.00401865

    def _inHg_to_Pa(self, value):
        return value / 0.0002953

    def _atm_to_Pa(self, value):
        return value * 101325.

    def _bar_to_Pa(self, value):
        return value * 100000.

    def _Torr_to_Pa(self, value):
        return value / 0.00750062

    def _psi_to_Pa(self, value):
        return value / 0.000145038

    def _inH2O_to_Pa(self, value):
        return value / 0.00401865

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('Pa', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        if from_unit in self.ip_units:
            return values, from_unit
        else:
            return self.to_unit(values, 'inHg', from_unit), 'inHg'

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        if from_unit in self.si_units:
            return values, from_unit
        else:
            return self.to_unit(values, 'Pa', from_unit), 'Pa'


class AtmosphericStationPressure(Pressure):
    _min = 0
    _abbreviation = 'Patm'
