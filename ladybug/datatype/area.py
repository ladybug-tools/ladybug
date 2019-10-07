# coding=utf-8
"""Area data type."""
from __future__ import division

from .base import DataTypeBase


class Area(DataTypeBase):
    """Area

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
        *   isArea
        *   isDataType
"""
    _units = ('m2', 'ft2', 'mm2', 'in2', 'km2', 'mi2', 'cm2', 'ha', 'acre')
    _si_units = ('m2', 'mm2', 'km2', 'cm2', 'ha')
    _ip_units = ('ft2', 'in2', 'mi2', 'acre')
    _min = 0
    _abbreviation = 'A'

    def _m2_to_ft2(self, value):
        return value * 10.7639

    def _m2_to_mm2(self, value):
        return value * 1000000.

    def _m2_to_in2(self, value):
        return value * 1550.

    def _m2_to_km2(self, value):
        return value / 1000000.

    def _m2_to_mi2(self, value):
        return value / 2590000.

    def _m2_to_cm2(self, value):
        return value * 10000.

    def _m2_to_ha(self, value):
        return value / 10000.

    def _m2_to_acre(self, value):
        return value / 4046.86

    def _ft2_to_m2(self, value):
        return value / 10.7639

    def _mm2_to_m2(self, value):
        return value / 1000000.

    def _in2_to_m2(self, value):
        return value / 1550.

    def _km2_to_m2(self, value):
        return value * 1000000.

    def _mi2_to_m2(self, value):
        return value * 2590000.

    def _cm2_to_m2(self, value):
        return value / 10000.

    def _ha_to_m2(self, value):
        return value * 10000.

    def _acre_to_m2(self, value):
        return value * 4046.86

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('m2', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        if from_unit in self.ip_units:
            return values, from_unit
        elif from_unit == 'mm2' or from_unit == 'cm2':
            return self.to_unit(values, 'in2', from_unit), 'in2'
        elif from_unit == 'km2':
            return self.to_unit(values, 'mi2', from_unit), 'mi2'
        elif from_unit == 'ha':
            return self.to_unit(values, 'acre', from_unit), 'acre'
        else:
            return self.to_unit(values, 'ft2', from_unit), 'ft2'

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        if from_unit in self.si_units:
            return values, from_unit
        elif from_unit == 'in2':
            return self.to_unit(values, 'mm2', from_unit), 'mm2'
        elif from_unit == 'mi2':
            return self.to_unit(values, 'km2', from_unit), 'km2'
        elif from_unit == 'acre':
            return self.to_unit(values, 'ha', from_unit), 'ha'
        else:
            return self.to_unit(values, 'm2', from_unit), 'm2'

    @property
    def isArea(self):
        """Return True."""
        return True
