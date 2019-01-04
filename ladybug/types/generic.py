# coding=utf-8
"""Generic data type."""
from __future__ import division

from ._base import DataTypeBase


class Unitless(DataTypeBase):
    """Type for any data without a recognizable name and no units."""
    def __init__(self, name):
        """Init Generic Type."""
        self.name = name
        self.abbreviation = name


class GenericType(DataTypeBase):
    """Type for any data without a recognizable name."""
    def __init__(self, name, unit):
        """Init Generic Type."""
        self.name = name
        self.units = [unit]
        self.abbreviation = name

    def to_ip(self, values, from_unit):
        """Return values in IP."""
        return values, from_unit

    def to_si(self, values, from_unit):
        """Return values in SI."""
        return values, from_unit


class DaysSinceLastSnowfall(DataTypeBase):
    name = 'Days Since Last Snowfall'
    abbreviation = 'DSLS'
    missing_epw = 99
