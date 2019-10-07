# coding=utf-8
"""Energy data type."""
from __future__ import division

from .base import DataTypeBase


class SpecificEnergy(DataTypeBase):
    """Energy

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
        *   isSpecificEnergy
    """
    _units = ('kWh/kg', 'kBtu/lb', 'Wh/kg', 'Btu/lb', 'J/kg', 'kJ/kg')
    _si_units = ('kWh/kg', 'Wh/kg', 'J/kg', 'kJ/kg')
    _ip_units = ('Btu/lb', 'kBtu/lb')
    _abbreviation = 'E/m'
    _point_in_time = False
    _cumulative = True

    def _kWh_kg_to_kBtu_lb(self, value):
        return value * 1.54772

    def _kWh_kg_to_Wh_kg(self, value):
        return value * 1000.

    def _kWh_kg_to_Btu_lb(self, value):
        return value * 1547.72

    def _kWh_kg_to_J_kg(self, value):
        return value * 3600000.

    def _kWh_kg_to_kJ_kg(self, value):
        return value * 3600.

    def _kBtu_lb_to_kWh_kg(self, value):
        return value / 1.54772

    def _Wh_kg_to_kWh_kg(self, value):
        return value / 1000.

    def _Btu_lb_to_kWh_kg(self, value):
        return value / 1547.72

    def _J_kg_to_kWh_kg(self, value):
        return value / 3600000.

    def _kJ_kg_to_kWh_kg(self, value):
        return value / 3600.

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('kWh/kg', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        if from_unit in self.ip_units:
            return values, from_unit
        elif from_unit == 'kJ/kg':
            return self.to_unit(values, 'Btu/lb', from_unit), 'Btu/lb'
        else:
            return self.to_unit(values, 'kBtu/lb', from_unit), 'kBtu/lb'

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        if from_unit in self.si_units:
            return values, from_unit
        elif from_unit == 'Btu/lb':
            return self.to_unit(values, 'kJ/kg', from_unit), 'kJ/kg'
        else:
            return self.to_unit(values, 'kWh/kg', from_unit), 'kWh/kg'

    @property
    def isSpecificEnergy(self):
        """Return True."""
        return True


class Enthalpy(SpecificEnergy):
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
        *   isSpecificEnergy
    """
    _abbreviation = 'Enth'
    _min = 0
