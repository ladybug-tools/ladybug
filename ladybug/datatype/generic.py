# coding=utf-8
"""Generic data type."""
from __future__ import division

from .base import DataTypeBase


class GenericType(DataTypeBase):
    """Type for any data type that is not currently implemented.

    Args:
        name: A name for the data type as a string.
        unit: A unit for the data type as a string.
        min: Optional lower limit for the data type, values below which should be
            physically or mathematically impossible. (Default: -inf)
        max: Optional upper limit for the data type, values above which should be
            physically or mathematically impossible. (Default: +inf)
        abbreviation: An optional abbreviation for the data type as text.
        unit_descr: An optional dictionary describing categories that the numerical
            values of the units relate to. For example:
            {-1: 'Cold', 0: 'Neutral', +1: 'Hot'}
            {0: 'False', 1: 'True'}
        point_in_time: Boolean to note whether the data type represents conditions
            at a single instant in time (True) as opposed to being an average or
            accumulation over time (False) when it is found in hourly lists of data.
            (Default: True)
        cumulative: Boolean to tell whether the data type can be cumulative when it
            is represented over time (True) or it can only be averaged over time
            to be meaningful (False). Note that cumulative cannot be True
            when point_in_time is also True. (Default: False)
    """
    def __init__(self, name, unit, min=float('-inf'), max=float('+inf'),
                 abbreviation=None, unit_descr=None, point_in_time=True,
                 cumulative=False):
        """Initialize Generic Type.
        """
        assert isinstance(name, str), 'name must be a string. Got {}.'.format(type(name))
        assert isinstance(unit, str), 'unit must be a string. Got {}.'.format(type(unit))
        assert isinstance(min, (float, int)), 'min must be a number. ' \
            'Got {}.'.format(type(min))
        assert isinstance(max, (float, int)), 'max must be a number. ' \
            'Got {}.'.format(type(max))
        if abbreviation is not None:
            assert isinstance(abbreviation, str), 'abbreviation must be a ' \
                'string. Got {}.'.format(type(abbreviation))
        if unit_descr is not None:
            assert isinstance(unit_descr, dict), 'unit_descr must be a ' \
                'dictionary. Got {}.'.format(type(unit_descr))
        assert isinstance(point_in_time, bool), 'point_in_time must be a ' \
            'boolean. Got {}.'.format(type(point_in_time))
        assert isinstance(cumulative, bool), 'cumulative must be a ' \
            'boolean. Got {}.'.format(type(cumulative))
        if point_in_time:
            assert not cumulative, 'cumulative cannot be True when ' \
                'point_in_time is also True.'

        self._name = name
        self._units = [unit]
        self._min = min
        self._max = max
        self._abbreviation = abbreviation if abbreviation is not None else name
        self._unit_descr = unit_descr
        self._point_in_time = point_in_time
        self._cumulative = cumulative

    @classmethod
    def from_string(cls, data_type_string):
        """Create a Generic data type from a string.

        Args:
            data: A data type string.
        """
        props = data_type_string.split(' | ')
        return cls(*props)

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        return values, from_unit

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        return values, from_unit

    def to_dict(self):
        """Get Generic data type as a dictionary."""
        return {
            'type': 'DataTypeBase',
            'name': self.name,
            'data_type': self.__class__.__name__,
            'base_unit': self.units[0],
            'min': self._min,
            'max': self._max,
            'abbreviation': self._abbreviation,
            'unit_descr': self._unit_descr,
            'point_in_time': self._point_in_time,
            'cumulative': self._cumulative
        }

    def to_string(self):
        """Get data type as a string."""
        return '{} | {} | {} | {} | {} | {} | {} | {}'.format(
            self.name, self.units[0], self._min, self._max, self._abbreviation,
            self._unit_descr, self._point_in_time, self._cumulative)
