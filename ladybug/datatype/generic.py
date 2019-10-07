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

    Properties:
        *   name: The full name of the data type as a string.
        *   units: A list of all accetpable units of the data type as abbreviated text.
            The first item of the list should be the standard SI unit.
            The second item of the list should be the stadard IP unit (if it exists).
            The rest of the list can be any other acceptable units.
            (eg. [C, F, K])
        *   si_units: A list of acceptable SI units.
        *   ip_units: A list of acceptable IP units.
        *   min: Lower limit for the data type, values below which should be physically
            or mathematically impossible. (Default: -inf)
        *   max: Upper limit for the data type, values above which should be physically
            or mathematically impossible. (Default: +inf)
        *   abbreviation: An optional abbreviation for the data type as text.
            (eg. 'UTCI' for Universal Thermal Climate Index).
            This can also be a letter that represents the data type in a formula.
            (eg. 'A' for Area; 'P' for Pressure)
        *   unit_descr: An optional dictionary describing categories that the numerical
            values of the units relate to. For example:
            {-1: 'Cold', 0: 'Neutral', +1: 'Hot'}
            {0: 'False', 1: 'True'}
        *   point_in_time: Boolean to note whether the data type represents conditions
            at a single instant in time (True) as opposed to being an average or
            accumulation over time (False) when it is found in hourly lists of data.
            (True Examples: Temperature, WindSpeed)
            (False Examples: Energy, Radiation, Illuminance)
        *   cumulative: Boolean to tell whether the data type can be cumulative when it
            is represented over time (True) or it can only be averaged over time
            to be meaningful (False). Note that cumulative cannot be True
            when point_in_time is also True.
            (False Examples: Temperature, Irradiance, Illuminance)
            (True Examples: Energy, Radiation)
        *   isDataType
    """
    def __init__(self, name, unit, min=float('-inf'), max=float('+inf'),
                 abbreviation=None, unit_descr=None, point_in_time=True,
                 cumulative=False):
        """Initalize Generic Type.
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
        if point_in_time is True:
            assert cumulative is False, 'cumulative cannot be True when ' \
                'point_in_time is also True.'

        self._name = name
        self._units = [unit]
        self._min = min
        self._max = max
        self._abbreviation = abbreviation if abbreviation is not None else name
        self._unit_descr = unit_descr
        self._point_in_time = point_in_time
        self._cumulative = cumulative

    def to_ip(self, values, from_unit):
        """Return values in IP and the units to which the values have been converted."""
        return values, from_unit

    def to_si(self, values, from_unit):
        """Return values in SI and the units to which the values have been converted."""
        return values, from_unit
