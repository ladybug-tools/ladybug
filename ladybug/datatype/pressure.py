# coding=utf-8
"""Generic data type."""
from __future__ import division

from .base import DataTypeBase


class Pressure(DataTypeBase):
    """Pressure

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
        *   isPressure
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

    @property
    def isPressure(self):
        """Return True."""
        return True


class AtmosphericStationPressure(Pressure):
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
        *   isPressure
    """
    _min = 0
    _abbreviation = 'Patm'
