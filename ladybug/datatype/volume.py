# coding=utf-8
"""Volume data type."""
from __future__ import division

from .base import DataTypeBase


class Volume(DataTypeBase):
    """Volume

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
        *   isVolume
    """
    _units = ('m3', 'ft3', 'mm3', 'in3', 'km3', 'mi3', 'L', 'mL', 'gal', 'fl oz')
    _si_units = ('m3', 'mm3', 'km3', 'L', 'mL')
    _ip_units = ('ft3', 'in3', 'mi3', 'gal', 'fl oz')
    _min = 0
    _abbreviation = 'V'

    def _m3_to_ft3(self, value):
        return value * 35.3147

    def _m3_to_mm3(self, value):
        return value * 1e+9

    def _m3_to_in3(self, value):
        return value * 61023.7

    def _m3_to_km3(self, value):
        return value / 1e+9

    def _m3_to_mi3(self, value):
        return value / 4.168e+9

    def _m3_to_L(self, value):
        return value * 1000.

    def _m3_to_mL(self, value):
        return value * 1000000.

    def _m3_to_gal(self, value):
        return value * 264.172

    def _m3_to_floz(self, value):
        return value * 33814.

    def _ft3_to_m3(self, value):
        return value / 35.3147

    def _mm3_to_m3(self, value):
        return value / 1e+9

    def _in3_to_m3(self, value):
        return value / 61023.7

    def _km3_to_m3(self, value):
        return value * 1e+9

    def _mi3_to_m3(self, value):
        return value * 4.168e+9

    def _L_to_m3(self, value):
        return value / 1000.

    def _mL_to_m3(self, value):
        return value / 1000000.

    def _gal_to_m3(self, value):
        return value / 264.172

    def _floz_to_m3(self, value):
        return value / 33814.

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('m3', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        if from_unit in self.ip_units:
            return values, from_unit
        elif from_unit == 'mL' or from_unit == 'mm3':
            return self.to_unit(values, 'fl oz', from_unit), 'fl oz'
        elif from_unit == 'km3':
            return self.to_unit(values, 'mi3', from_unit), 'mi3'
        elif from_unit == 'L':
            return self.to_unit(values, 'gal', from_unit), 'gal'
        else:
            return self.to_unit(values, 'ft3', from_unit), 'ft3'

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        if from_unit in self.si_units:
            return values, from_unit
        elif from_unit == 'in3' or from_unit == 'fl oz':
            return self.to_unit(values, 'mL', from_unit), 'mL'
        elif from_unit == 'mi3':
            return self.to_unit(values, 'km3', from_unit), 'km3'
        elif from_unit == 'gal':
            return self.to_unit(values, 'L', from_unit), 'L'
        else:
            return self.to_unit(values, 'm3', from_unit), 'm3'

    @property
    def isVolume(self):
        """Return True."""
        return True
