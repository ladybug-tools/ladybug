# coding=utf-8
"""Thermal condition data type."""
from __future__ import division

from .base import DataTypeBase


class ThermalCondition(DataTypeBase):
    """Thermal Condition"""
    _units = ('condition', 'PMV')
    _si_units = ('condition', 'PMV')
    _ip_units = ('condition', 'PMV')
    _abbreviation = 'Tcond'
    _unit_descr = '-1 = Cold, 0 = Neutral, +1 = Hot'

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

    @property
    def isThermalCondition(self):
        """Return True."""
        return True


class PredictedMeanVote(ThermalCondition):
    _abbreviation = 'PMV'
    _unit_descr = '-3 = Cold, -2 = Cool, -1 = Slightly Cool, \n' \
        '0 = Neutral, \n' \
        '+1 = Slightly Warm, +2 = Warm, +3 = Hot'


class DiscomfortReason(ThermalCondition):
    _abbreviation = 'RDiscomf'
    _unit_descr = '-2 = Too Dry, -1 = Too Cold, \n' \
        '0 = Comfortable, \n' \
        '+1 = Too Hot, +2 = Too Humid'


class ThermalConditionFivePoint(ThermalCondition):
    _abbreviation = 'Tcond-5'
    _unit_descr = '-2 = Strong/Extreme Cold, -1 = Moderate Cold, \n' \
        '0 = No Thermal Stress, \n' \
        '+1 = Moderate Heat, +2 = Strong/Extreme Heat'


class ThermalConditionSevenPoint(ThermalCondition):
    _abbreviation = 'Tcond-7'
    _unit_descr = '-3 = Very Strong/Extreme Cold, ' \
        '-2 = Strong Cold, -1 = Moderate Cold, \n' \
        '0 = No Thermal Stress, \n' \
        '+1 = Moderate Heat, +2 = Strong Heat, ' \
        '+3 = Very Strong/Extreme Heat'


class ThermalConditionNinePoint(ThermalCondition):
    _abbreviation = 'Tcond-9'
    _unit_descr = '-4 = Very Strong/Extreme Cold, ' \
        '-3 = Strong Cold, -2 = Moderate Cold, -1 = Slight Cold, \n' \
        '0 = No Thermal Stress, \n' \
        '+1 = Slight Heat, +2 = Moderate Heat, +3 = Strong Heat, '\
        '+4 = Very Strong/Extreme Heat'


class ThermalConditionElevenPoint(ThermalCondition):
    _abbreviation = 'Tcond-11'
    _unit_descr = '-5 = Extreme Cold, -4 = Very Strong Cold, ' \
        '-3 = Strong Cold, -2 = Moderate Cold, -1 = Slight Cold, \n' \
        '0 = No Thermal Stress, \n' \
        '+1 = Slight Heat, +2 = Moderate Heat, +3 = Strong Heat, ' \
        '+4 = Very Strong Heat, +5 = Extreme Heat'


class UTCICategory(ThermalCondition):
    _abbreviation = 'UTCIcond'
    _unit_descr = '0 = extreme cold stress' \
        '1 = very strong cold stress' \
        '2 = strong cold stress' \
        '3 = moderate cold stress' \
        '4 = slight cold stress' \
        '5 = no thermal stress' \
        '6 = moderate heat stress' \
        '7 = strong heat stress' \
        '8 = strong heat stress' \
        '9 = extreme heat stress'
