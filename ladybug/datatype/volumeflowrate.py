# coding=utf-8
"""Volume Flow Rate data type."""
from __future__ import division

from .base import DataTypeBase
from .volume import Volume
from .volumeflowrateintensity import VolumeFlowRateIntensity


class VolumeFlowRate(DataTypeBase):
    """Volume Flow Rate
    """
    _units = ('m3/s', 'ft3/s', 'L/s', 'cfm', 'gpm', 'mL/s', 'fl oz/s', 'L/h', 'gph')
    _si_units = ('m3/s', 'L/s', 'mL/s', 'L/h')
    _ip_units = ('ft3/s', 'cfm', 'gpm', 'fl oz/s', 'gph')
    _min = 0
    _abbreviation = 'dV/dt'
    _normalized_type = VolumeFlowRateIntensity

    def _m3_s_to_ft3_s(self, value):
        return value * 35.3147

    def _m3_s_to_L_s(self, value):
        return value * 1000.

    def _m3_s_to_cfm(self, value):
        return value * 2118.88

    def _m3_s_to_gpm(self, value):
        return value * 15850.3231

    def _m3_s_to_mL_s(self, value):
        return value * 1000000.

    def _m3_s_to_floz_s(self, value):
        return value * 33814.

    def _m3_s_to_L_h(self, value):
        return value * 3600000.

    def _m3_s_to_gph(self, value):
        return value * 951019.

    def _ft3_s_to_m3_s(self, value):
        return value / 35.3147

    def _L_s_to_m3_s(self, value):
        return value / 1000.

    def _cfm_to_m3_s(self, value):
        return value / 2118.88

    def _gpm_to_m3_s(self, value):
        return value / 15850.3231

    def _mL_s_to_m3_s(self, value):
        return value / 1000000.

    def _floz_s_to_m3_s(self, value):
        return value / 33814.

    def _L_h_to_m3_s(self, value):
        return value / 3600000.

    def _gph_to_m3_s(self, value):
        return value / 951019.

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('m3/s', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        if from_unit in self.ip_units:
            return values, from_unit
        elif from_unit == 'L/s':
            return self.to_unit(values, 'cfm', from_unit), 'cfm'
        elif from_unit == 'mL/s':
            return self.to_unit(values, 'fl oz/s', from_unit), 'fl oz/s'
        elif from_unit == 'L/h':
            return self.to_unit(values, 'gph', from_unit), 'gph'
        else:
            return self.to_unit(values, 'ft3/s', from_unit), 'ft3/s'

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        if from_unit in self.si_units:
            return values, from_unit
        elif from_unit == 'cfm':
            return self.to_unit(values, 'L/s', from_unit), 'L/s'
        elif from_unit == 'fl oz/s':
            return self.to_unit(values, 'mL/s', from_unit), 'mL/s'
        elif from_unit == 'gph':
            return self.to_unit(values, 'L/h', from_unit), 'L/h'
        else:
            return self.to_unit(values, 'm3/s', from_unit), 'm3/s'
