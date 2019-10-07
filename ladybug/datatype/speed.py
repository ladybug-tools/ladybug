# coding=utf-8
"""Generic data type."""
from __future__ import division

from .base import DataTypeBase


class Speed(DataTypeBase):
    """Speed

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
        *   isSpeed
    """
    _units = ('m/s', 'mph', 'km/h', 'knot', 'ft/s')
    _si_units = ('m/s', 'km/h')
    _ip_units = ('mph', 'ft/s')
    _min = 0
    _abbreviation = 'v'

    def _m_s_to_mph(self, value):
        return value * 2.23694

    def _m_s_to_km_h(self, value):
        return value * 3.6

    def _m_s_to_knot(self, value):
        return value * 1.94384

    def _m_s_to_ft_s(self, value):
        return value * 3.28084

    def _mph_to_m_s(self, value):
        return value / 2.23694

    def _km_h_to_m_s(self, value):
        return value / 3.6

    def _knot_to_m_s(self, value):
        return value / 1.94384

    def _ft_s_to_m_s(self, value):
        return value / 3.28084

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('m/s', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        if from_unit in self.ip_units:
            return values, from_unit
        else:
            return self.to_unit(values, 'mph', from_unit), 'mph'

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        if from_unit in self.si_units:
            return values, from_unit
        else:
            return self.to_unit(values, 'm/s', from_unit), 'm/s'

    @property
    def isSpeed(self):
        """Return True."""
        return True


class WindSpeed(Speed):
    """
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
        *   isSpeed
    """
    _abbreviation = 'WS'


class AirSpeed(Speed):
    """
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
        *   isSpeed
    """
    _abbreviation = 'vair'
