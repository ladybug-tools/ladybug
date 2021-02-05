# coding=utf-8
"""Volume Flow Rate Intensity data type."""
from __future__ import division

from .base import DataTypeBase


class VolumeFlowRateIntensity(DataTypeBase):
    """Volume Flow Rate Intensity
    """
    _units = ('m3/s-m2', 'ft3/s-ft2', 'L/s-m2', 'cfm/ft2', 'L/h-m2', 'gph/ft2')
    _si_units = ('m3/s-m2', 'L/s-m2', 'L/h-m2')
    _ip_units = ('ft3/s-ft2', 'cfm/ft2', 'gph/ft2')
    _min = 0
    _abbreviation = 'dV/dt-A'

    def _m3_sm2_to_ft3_sft2(self, value):
        return value * 3.28084

    def _m3_sm2_to_L_sm2(self, value):
        return value * 1000.

    def _m3_sm2_to_cfm_ft2(self, value):
        return value * 196.85

    def _m3_sm2_to_L_hm2(self, value):
        return value * 3600000.

    def _m3_sm2_to_gph_ft2(self, value):
        return value * 88352.5923

    def _ft3_sft2_to_m3_sm2(self, value):
        return value / 3.28084

    def _L_sm2_to_m3_sm2(self, value):
        return value / 1000.

    def _cfm_ft2_to_m3_sm2(self, value):
        return value / 196.85

    def _L_hm2_to_m3_sm2(self, value):
        return value / 3600000.

    def _gph_ft2_to_m3_sm2(self, value):
        return value / 88352.5923

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('m3/s-m2', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        if from_unit in self.ip_units:
            return values, from_unit
        elif from_unit == 'L/s-m2':
            return self.to_unit(values, 'cfm/ft2', from_unit), 'cfm/ft2'
        elif from_unit == 'L/h-m2':
            return self.to_unit(values, 'gph/ft2', from_unit), 'gph/ft2'
        else:
            return self.to_unit(values, 'ft3/s-ft2', from_unit), 'ft3/s-ft2'

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        if from_unit in self.si_units:
            return values, from_unit
        elif from_unit == 'cfm/ft2':
            return self.to_unit(values, 'L/s-m2', from_unit), 'L/s-m2'
        elif from_unit == 'gph/ft2':
            return self.to_unit(values, 'L/h-m2', from_unit), 'L/h-m2'
        else:
            return self.to_unit(values, 'm3/s-m2', from_unit), 'm3/s-m2'