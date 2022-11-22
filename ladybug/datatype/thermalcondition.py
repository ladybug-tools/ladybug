# coding=utf-8
"""Thermal condition data type."""
from __future__ import division

from .base import DataTypeBase


class ThermalCondition(DataTypeBase):
    """Thermal Condition
    """
    _units = ('condition', 'PMV')
    _si_units = ('condition', 'PMV')
    _ip_units = ('condition', 'PMV')
    _min = -1
    _max = 1
    _abbreviation = 'Tcond'
    _unit_descr = {-1: 'Cold', 0: 'Neutral', 1: 'Hot'}

    def _condition_to_PMV(self, value):
        return value

    def _PMV_to_condition(self, value):
        return value

    def to_unit(self, values, unit, from_unit):
        """Return values converted to the unit given the input from_unit."""
        return self._to_unit_base('condition', values, unit, from_unit)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        return values, from_unit

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        return values, from_unit


class PredictedMeanVote(ThermalCondition):
    _min = float('-inf')
    _max = float('+inf')
    _abbreviation = 'PMV'
    _unit_descr = {-3: 'Cold', -2: 'Cool', -1: 'Slightly Cool', 0: 'Neutral',
                   1: 'Slightly Warm', 2: 'Warm', 3: 'Hot'}


class ThermalComfort(ThermalCondition):
    _min = 0
    _max = 1
    _abbreviation = 'TC'
    _unit_descr = {1: 'Comfortable', 0: 'Uncomfortable'}


class DiscomfortReason(ThermalCondition):
    _min = -2
    _max = 2
    _abbreviation = 'RDiscomf'
    _unit_descr = {-2: 'Too Dry', -1: 'Too Cold', 0: 'Comfortable',
                   1: 'Too Hot', 2: 'Too Humid'}


class ThermalConditionFivePoint(ThermalCondition):
    _min = -2
    _max = 2
    _abbreviation = 'Tcond-5'
    _unit_descr = {-2: 'Strong Cold', -1: 'Moderate Cold',
                   0: 'No Thermal Stress', 1: 'Moderate Heat', 2: 'Strong Heat'}


class ThermalConditionSevenPoint(ThermalCondition):
    _min = -3
    _max = 3
    _abbreviation = 'Tcond-7'
    _unit_descr = {-3: 'Extreme Cold', -2: 'Strong Cold',
                   -1: 'Moderate Cold', 0: 'No Thermal Stress', 1: 'Moderate Heat',
                   2: 'Strong Heat', 3: 'Extreme Heat'}


class ThermalConditionNinePoint(ThermalCondition):
    _min = -4
    _max = 4
    _abbreviation = 'Tcond-9'
    _unit_descr = {-4: 'Extreme Cold', -3: 'Strong Cold',
                   -2: 'Moderate Cold', -1: 'Slight Cold', 0: 'No Thermal Stress',
                   1: 'Slight Heat', 2: 'Moderate Heat', 3: 'Strong Heat',
                   4: 'Extreme Heat'}


class ThermalConditionElevenPoint(ThermalCondition):
    _min = -5
    _max = 5
    _abbreviation = 'Tcond-11'
    _unit_descr = {-5: 'Extreme Cold', -4: 'Very Strong Cold', -3: 'Strong Cold',
                   -2: 'Moderate Cold', -1: 'Slight Cold', 0: 'No Thermal Stress',
                   1: 'Slight Heat', 2: 'Moderate Heat', 3: 'Strong Heat',
                   4: 'Very Strong Heat', 5: 'Extreme Heat'}


class UTCICategory(ThermalCondition):
    _min = 0
    _max = 9
    _abbreviation = 'UTCIcond'
    _unit_descr = {0: 'Extreme Cold Stress', 1: 'Very Strong Cold Stress',
                   2: 'Strong Cold Stress', 3: 'Moderate Cold Stress',
                   4: 'Slight Cold Stress', 5: 'No Thermal Stress',
                   6: 'Moderate Heat Stress', 7: 'Strong Heat Stress',
                   8: 'Strong Heat Stress', 9: 'Extreme Heat Stress'}


class CoreTemperatureCategory(ThermalCondition):
    _min = -2
    _max = 2
    _abbreviation = 'TCcond'
    _unit_descr = {-2: 'Hypothermia', -1: 'Cold',
                   0: 'Normal', 1: 'Hot', 2: 'Hyperthermia'}
