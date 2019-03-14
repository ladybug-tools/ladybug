# coding=utf-8
"""Immutable versions of the Ladybug Data Collections.

Note that all of the methods or properties on an immutable collection that
return another data collection will return a collection that is mutable.

The only exceptions to this rule are:
duplicate() - which will always return an exact copy of the collection including
    its mutabiliy.
get_aligned_collection() - which follows the mutability of the starting collection
    by default but includes an parameter to override this.
to_immutable() - which clearly always returns an immutable version of the collection

Note that the to_mutable() method on the immutable collections can always be used to
get a mutable version of an immutable collection.
"""
from __future__ import division

from .datacollection import HourlyDiscontinuousCollection, HourlyContinuousCollection, \
    DailyCollection, MonthlyCollection, MonthlyPerHourCollection

from collections import Iterable


class HourlyDiscontinuousCollectionImmutable(HourlyDiscontinuousCollection):
    """Immutable Discontinous Data Collection at hourly or sub-hourly intervals."""
    _mutable = False

    @property
    def values(self):
        """The Data Collection's list of numerical values."""
        return tuple(self._values)

    @values.setter
    def values(self, values):
        try:
            self._values
            _values_set = True
        except AttributeError:
            _values_set = False

        if _values_set is False:
            self._check_values(values)
            self._values = tuple(values)
        else:
            raise AttributeError(self._mutable_message())

    def convert_to_culled_timestep(self, timestep=1):
        """This method is not available for immutable collections."""
        raise AttributeError(self._mutable_message())

    def to_mutable(self):
        """Get a mutable version of this collection."""
        return HourlyDiscontinuousCollection(self.header, self.values, self.datetimes)

    def to_immutable(self):
        """Get an immutable version of this collection."""
        return self.duplicate()

    def __setitem__(self, key, value):
        raise AttributeError(self._mutable_message())


class HourlyContinuousCollectionImmutable(HourlyContinuousCollection):
    """Immutable Continous Data Collection at hourly or sub-hourly intervals."""
    _mutable = False

    @property
    def values(self):
        """The Data Collection's list of numerical values."""
        return tuple(self._values)

    @values.setter
    def values(self, values):
        try:
            self._values
            _values_set = True
        except AttributeError:
            _values_set = False

        if _values_set is False:
            assert isinstance(values, Iterable) and not isinstance(
                values, (str, dict, bytes, bytearray)), \
                'values should be a list or tuple. Got {}'.format(type(values))
            if self.header.analysis_period.is_annual:
                a_period_len = 8760 * self.header.analysis_period.timestep
                if self.header.analysis_period.is_leap_year is True:
                    a_period_len = a_period_len + 24 * \
                        self.header.analysis_period.timestep
            else:
                a_period_len = len(self.header.analysis_period.moys)
            assert len(values) == a_period_len, \
                'Length of values does not match that expected by the '\
                'header analysis_period. {} != {}'.format(
                    len(values), a_period_len)
            self._values = tuple(values)
        else:
            raise AttributeError(self._mutable_message())

    def convert_to_culled_timestep(self, timestep=1):
        """This method is not available for immutable collections."""
        raise AttributeError(self._mutable_message())

    def to_mutable(self):
        """Get a mutable version of this collection."""
        return HourlyContinuousCollection(self.header, self.values)

    def to_immutable(self):
        """Get an immutable version of this collection."""
        return self.duplicate()

    def __setitem__(self, key, value):
        raise AttributeError(self._mutable_message())


class DailyCollectionImmutable(DailyCollection):
    """Immutable Daily Data Collection."""
    _mutable = False

    @DailyCollection.values.setter
    def values(self, values):
        try:
            self._values
            _values_set = True
        except AttributeError:
            _values_set = False

        if _values_set is False:
            self._check_values(values)
            self._values = tuple(values)
        else:
            raise AttributeError(self._mutable_message())

    def to_mutable(self):
        """Get a mutable version of this collection."""
        return DailyCollection(self.header, self.values, self.datetimes)

    def to_immutable(self):
        """Get an immutable version of this collection."""
        return self.duplicate()

    def __setitem__(self, key, value):
        raise AttributeError(self._mutable_message())


class MonthlyCollectionImmutable(MonthlyCollection):
    """Immutable Monthly Data Collection."""
    _mutable = False

    @MonthlyCollection.values.setter
    def values(self, values):
        try:
            self._values
            _values_set = True
        except AttributeError:
            _values_set = False

        if _values_set is False:
            self._check_values(values)
            self._values = tuple(values)
        else:
            raise AttributeError(self._mutable_message())

    def to_mutable(self):
        """Get a mutable version of this collection."""
        return MonthlyCollection(self.header, self.values, self.datetimes)

    def to_immutable(self):
        """Get an immutable version of this collection."""
        return self.duplicate()

    def __setitem__(self, key, value):
        raise AttributeError(self._mutable_message())


class MonthlyPerHourCollectionImmutable(MonthlyPerHourCollection):
    """Immutable Monthly Per Hour Data Collection."""
    _mutable = False

    @MonthlyPerHourCollection.values.setter
    def values(self, values):
        try:
            self._values
            _values_set = True
        except AttributeError:
            _values_set = False

        if _values_set is False:
            self._check_values(values)
            self._values = tuple(values)
        else:
            raise AttributeError(self._mutable_message())

    def to_mutable(self):
        """Get a mutable version of this collection."""
        return MonthlyPerHourCollection(self.header, self.values, self.datetimes)

    def to_immutable(self):
        """Get an immutable version of this collection."""
        return self.duplicate()

    def __setitem__(self, key, value):
        raise AttributeError(self._mutable_message())
