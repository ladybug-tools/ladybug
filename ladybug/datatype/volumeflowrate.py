# coding=utf-8
"""Generic data type."""
from __future__ import division

from .base import DataTypeBase


class VolumeFlowRate(DataTypeBase):
    """Volume Flow Rate

    Properties:
        *   name: The full name of the data type as a string.
        *   units: A list of all accetpable units of the data type as abbreviated text.
            The first item of the list should be the standard SI unit.
            The second item of the list should be the stadard IP unit (if it exists).
            The rest of the list can be any other acceptable units.
            (eg. [C, F, K])
        *   si_units: A list of acceptable SI units.
        *   ip_units: A list of acceptable IP units.
        *   min: Lower limit for the data type, values below which should be physically
            or mathematically impossible. (Default: -inf)
        *   max: Upper limit for the data type, values above which should be physically
            or mathematically impossible. (Default: +inf)
        *   abbreviation: An optional abbreviation for the data type as text.
            (eg. 'UTCI' for Universal Thermal Climate Index).
            This can also be a letter that represents the data type in a formula.
            (eg. 'A' for Area; 'P' for Pressure)
        *   unit_descr: An optional dictionary describing categories that the numerical
            values of the units relate to. For example:
            {-1: 'Cold', 0: 'Neutral', +1: 'Hot'}
            {0: 'False', 1: 'True'}
        *   point_in_time: Boolean to note whether the data type represents conditions
            at a single instant in time (True) as opposed to being an average or
            accumulation over time (False) when it is found in hourly lists of data.
            (True Examples: Temperature, WindSpeed)
            (False Examples: Energy, Radiation, Illuminance)
        *   cumulative: Boolean to tell whether the data type can be cumulative when it
            is represented over time (True) or it can only be averaged over time
            to be meaningful (False). Note that cumulative cannot be True
            when point_in_time is also True.
            (False Examples: Temperature, Irradiance, Illuminance)
            (True Examples: Energy, Radiation)
        *   isDataType
        *   isFlowRate
    """
    _units = ('m3/s', 'ft3/s', 'L/s', 'cfm', 'gpm', 'mL/s', 'fl oz/s')
    _si_units = ('m3/s', 'L/s', 'mL/s')
    _ip_units = ('ft3/s', 'cfm', 'gpm', 'fl oz/s')
    _min = 0
    _abbreviation = 'dV/dt'

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
        else:
            return self.to_unit(values, 'm3/s', from_unit), 'm3/s'

    @property
    def isFlowRate(self):
        """Return True."""
        return True
