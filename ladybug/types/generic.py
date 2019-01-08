# coding=utf-8
"""Generic data type."""
from __future__ import division

from ._base import DataTypeBase


class Unitless(DataTypeBase):
    """Type for any data without a recognizable name and no units."""
    def __init__(self, name):
        """Init Generic Type."""
        self._name = name
        self._abbreviation = name


class GenericType(DataTypeBase):
    """Type for any data without a recognizable name."""
    def __init__(self, name, unit):
        """Init Generic Type."""
        self._name = name
        self._units = [unit]
        self._abbreviation = name

    def to_ip(self, values, from_unit):
        """Return values in IP."""
        return values, from_unit

    def to_si(self, values, from_unit):
        """Return values in SI."""
        return values, from_unit
