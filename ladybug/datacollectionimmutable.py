# coding=utf-8
"""Immutable versions of the Ladybug Data Collections.

Note that all of the methods or properties on an immutable collection that
return another data collection will return a collection that is mutable.

The only exceptions to this rule are:

*   duplicate() - which will always return an exact copy of the collection including
    its mutabiliy.

*   get_aligned_collection() - which follows the mutability of the starting collection
    by default but includes an parameter to override this.

*   to_immutable() - which clearly always returns an immutable version of the collection

Note that the to_mutable() method on the immutable collections can always be used to
get a mutable version of an immutable collection.
"""
from __future__ import division

from .datacollection import HourlyDiscontinuousCollection, HourlyContinuousCollection, \
    DailyCollection, MonthlyCollection, MonthlyPerHourCollection


class _ImmutableCollectionBase(object):
    """Base class for all immutable Data Collections."""
    _mutable = False

    @property
    def values(self):
        """The Data Collection's list of numerical values."""
        return self._values

    @values.setter
    def values(self, values):
        if hasattr(self, '_values'):
            raise AttributeError(self._mutable_message)
        self._check_values(values)
        self._values = tuple(values)

    @property
    def _mutable_message(self):
        return 'values are immutable for {}.\nUse to_mutable() method to get a ' \
            'mutable version of this collection.'.format(self.__class__.__name__)

    def to_immutable(self):
        """Get an immutable version of this collection."""
        return self.duplicate()

    def __setitem__(self, key, value):
        raise AttributeError(self._mutable_message)


class HourlyDiscontinuousCollectionImmutable(
        _ImmutableCollectionBase, HourlyDiscontinuousCollection):
    """Immutable Discontinous Data Collection at hourly or sub-hourly intervals."""

    def convert_to_culled_timestep(self, timestep=1):
        """This method is not available for immutable collections."""
        raise AttributeError(self._mutable_message)

    def to_mutable(self):
        """Get a mutable version of this collection."""
        return HourlyDiscontinuousCollection(self.header, self.values, self.datetimes)


class HourlyContinuousCollectionImmutable(
        _ImmutableCollectionBase, HourlyContinuousCollection):
    """Immutable Continous Data Collection at hourly or sub-hourly intervals."""

    def convert_to_culled_timestep(self, timestep=1):
        """This method is not available for immutable collections."""
        raise AttributeError(self._mutable_message)

    def to_mutable(self):
        """Get a mutable version of this collection."""
        return HourlyContinuousCollection(self.header, self.values)


class DailyCollectionImmutable(
        _ImmutableCollectionBase, DailyCollection):
    """Immutable Daily Data Collection."""

    def to_mutable(self):
        """Get a mutable version of this collection."""
        return DailyCollection(self.header, self.values, self.datetimes)


class MonthlyCollectionImmutable(
        _ImmutableCollectionBase, MonthlyCollection):
    """Immutable Monthly Data Collection."""

    def to_mutable(self):
        """Get a mutable version of this collection."""
        return MonthlyCollection(self.header, self.values, self.datetimes)


class MonthlyPerHourCollectionImmutable(
        _ImmutableCollectionBase, MonthlyPerHourCollection):
    """Immutable Monthly Per Hour Data Collection."""

    def to_mutable(self):
        """Get a mutable version of this collection."""
        return MonthlyPerHourCollection(self.header, self.values, self.datetimes)
