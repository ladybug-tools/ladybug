# coding=utf-8
"""Generic data type."""
from __future__ import division

from .base import DataTypeBase


class GenericType(DataTypeBase):
    """Type for any data type that is not currently implemented."""
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

    @property
    def isGeneric(self):
        """Return True."""
        return True
