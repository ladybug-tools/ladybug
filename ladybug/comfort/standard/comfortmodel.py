# coding=utf-8
"""Comfort standard base objects."""


class ComfortModel(object):
    """Thermal comfort Model base class."""

    def __init__(self):
        self._calc_length = 0
        self._is_computed = True

    @property
    def isComfortModel(self):
        """Return True."""
        return True


class ComfortParameter(object):
    """Thermal comfort paremeter base class."""

    @property
    def isComfortParameter(self):
        """Return True."""
        return True
