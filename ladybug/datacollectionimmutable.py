# coding=utf-8
"""Immutable versions of the Ladybug Data Collections.

Note that all of the methods or properties on an immutable collection that
return another data collection will return a collection that is mutable.

The only exceptions to this rule are:

*   duplicate() - which will always return an exact copy of the collection including
    its mutability.

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
    __slots__ = ()
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

    def convert_to_unit(self, unit):
        """Not available for immutable collections; use to_unit() instead."""
        raise AttributeError(self._mutable_message)

    def convert_to_ip(self):
        """Not available for immutable collections; use to_ip() instead."""
        raise AttributeError(self._mutable_message)

    def convert_to_si(self):
        """Not available for immutable collections; use to_si() instead."""
        raise AttributeError(self._mutable_message)

    def to_unit(self, unit):
        new_data_c = self.to_mutable()
        new_data_c.convert_to_unit(unit)
        return new_data_c

    def to_ip(self):
        new_data_c = self.to_mutable()
        new_data_c.convert_to_ip()
        return new_data_c

    def to_si(self):
        new_data_c = self.to_mutable()
        new_data_c.convert_to_si()
        return new_data_c

    def to_immutable(self):
        """Get an immutable version of this collection."""
        return self.duplicate()

    def duplicate(self):
        """Get a copy of this Data Collection."""
        collection = self.__class__(
            self.header.duplicate(), self._values, self.datetimes)
        collection._validated_a_period = self._validated_a_period
        return collection

    def __setitem__(self, key, value):
        raise AttributeError(self._mutable_message)


class HourlyDiscontinuousCollectionImmutable(
        _ImmutableCollectionBase, HourlyDiscontinuousCollection):
    """Immutable Discontinuous Data Collection at hourly or sub-hourly intervals."""
    __slots__ = ()

    @property
    def mutable_class(self):
        """Get the immutable class for this type of data collection."""
        return HourlyDiscontinuousCollection

    def convert_to_culled_timestep(self, timestep=1):
        """This method is not available for immutable collections."""
        raise AttributeError(self._mutable_message)

    def to_mutable(self):
        """Get a mutable version of this collection."""
        new_obj = HourlyDiscontinuousCollection(
            self.header.duplicate(), self.values, self.datetimes)
        new_obj._validated_a_period = self._validated_a_period
        return new_obj


class HourlyContinuousCollectionImmutable(
        _ImmutableCollectionBase, HourlyContinuousCollection):
    """Immutable Continuous Data Collection at hourly or sub-hourly intervals."""
    __slots__ = ()

    @property
    def mutable_class(self):
        """Get the immutable class for this type of data collection."""
        return HourlyContinuousCollection

    def convert_to_culled_timestep(self, timestep=1):
        """This method is not available for immutable collections."""
        raise AttributeError(self._mutable_message)

    def to_mutable(self):
        """Get a mutable version of this collection."""
        new_obj = HourlyContinuousCollection(self.header.duplicate(), self.values)
        new_obj._validated_a_period = self._validated_a_period
        return new_obj

    def duplicate(self):
        """Return a copy of the current Data Collection."""
        return self.__class__(self.header.duplicate(), self._values)


class DailyCollectionImmutable(
        _ImmutableCollectionBase, DailyCollection):
    """Immutable Daily Data Collection."""
    __slots__ = ()

    @property
    def mutable_class(self):
        """Get the immutable class for this type of data collection."""
        return DailyCollection

    def to_mutable(self):
        """Get a mutable version of this collection."""
        new_obj = DailyCollection(
            self.header.duplicate(), self.values, self.datetimes)
        new_obj._validated_a_period = self._validated_a_period
        return new_obj


class MonthlyCollectionImmutable(
        _ImmutableCollectionBase, MonthlyCollection):
    """Immutable Monthly Data Collection."""
    __slots__ = ()

    @property
    def mutable_class(self):
        """Get the immutable class for this type of data collection."""
        return MonthlyCollection

    def to_mutable(self):
        """Get a mutable version of this collection."""
        new_obj = MonthlyCollection(
            self.header.duplicate(), self.values, self.datetimes)
        new_obj._validated_a_period = self._validated_a_period
        return new_obj


class MonthlyPerHourCollectionImmutable(
        _ImmutableCollectionBase, MonthlyPerHourCollection):
    """Immutable Monthly Per Hour Data Collection."""
    __slots__ = ()

    @property
    def mutable_class(self):
        """Get the immutable class for this type of data collection."""
        return MonthlyPerHourCollection

    def to_mutable(self):
        """Get a mutable version of this collection."""
        new_obj = MonthlyPerHourCollection(
            self.header.duplicate(), self.values, self.datetimes)
        new_obj._validated_a_period = self._validated_a_period
        return new_obj
