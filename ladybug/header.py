# coding=utf-8
"""Ladybug Header"""
from __future__ import division

from copy import deepcopy

from .analysisperiod import AnalysisPeriod
from .datatype.base import DataTypeBase


class Header(object):
    """DataCollection header.

    Header carries meatdata for DataCollections including data type, unit
    and analysis period.

    Args:
        data_type: A DataType object. (e.g. Temperature)
        unit: data_type unit (e.g. 'C').
        analysis_period: A Ladybug AnalysisPeriod object.
        metadata: Optional dictionary of additional metadata,
            containing information such as 'source', 'city', or 'zone'.

    Properties:
        * data_type
        * unit
        * analysis_period
        * metadata
    """

    __slots__ = ('_data_type', '_unit', '_analysis_period', '_metadata')

    def __init__(self, data_type, unit, analysis_period, metadata=None):
        """Initiate Ladybug header for lists.
        """
        assert isinstance(data_type, DataTypeBase), \
            'data_type must be a Ladybug DataType. Got {}'.format(type(data_type))
        data_type.is_unit_acceptable(unit)
        assert isinstance(analysis_period, AnalysisPeriod), \
            'analysis_period must be a Ladybug AnalysisPeriod. Got {}'.format(
                type(analysis_period))
        if metadata is not None:
            assert isinstance(metadata, dict), \
                'metadata must be a dictionary. Got {}'.format(type(metadata))

        self._data_type = data_type
        self._unit = unit
        self._analysis_period = analysis_period
        self.metadata = metadata

    @classmethod
    def from_dict(cls, data):
        """Create a header from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

                {
                "data_type": {},  # Type of data (e.g. Temperature)
                "unit": "",  # string
                "analysis_period": {},  # A Ladybug AnalysisPeriod
                "metadata": {}  # A dictionary of metadata
                }
        """
        # assign default values
        assert 'data_type' in data, 'Required Header key "data_type" is missing!'
        assert 'unit' in data, 'Required Header key "unit" is missing!'
        assert 'analysis_period' in data, \
            'Required Header key "analysis_period" is missing!'

        data_type = DataTypeBase.from_dict(data['data_type'])
        ap = AnalysisPeriod.from_dict(data['analysis_period'])
        metadata = data['metadata'] if 'metadata' in data else None
        return cls(data_type, data['unit'], ap, metadata)

    @property
    def data_type(self):
        """Get a DataType object."""
        return self._data_type

    @property
    def unit(self):
        """Get a text string representing an abbreviated unit (eg. 'C')."""
        return self._unit

    @property
    def analysis_period(self):
        """Get an AnalysisPeriod object."""
        return self._analysis_period

    @property
    def metadata(self):
        """Get or set a dictionary of metadata associated with the Header."""
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        if value is not None:
            assert isinstance(value, dict), \
                'Expected dictionary for Header metadata. Got {}.'.format(type(value))
        self._metadata = value or {}

    def duplicate(self):
        """Return a copy of the header."""
        return self.__copy__()

    def __copy__(self):
        a_per = self.analysis_period.duplicate() if self.analysis_period else None
        return self.__class__(self.data_type, self.unit, a_per, deepcopy(self.metadata))

    def to_tuple(self):
        """Return Ladybug header as a list."""
        return (
            self.data_type,
            self.unit,
            self.analysis_period,
            self.metadata
        )

    def __iter__(self):
        """Return data as tuple."""
        return iter(self.to_tuple())

    def to_dict(self):
        """Return a header as a dictionary."""
        a_per = self.analysis_period.to_dict() if self.analysis_period else None
        return {
            'data_type': self.data_type.to_dict(),
            'unit': self.unit,
            'analysis_period': a_per,
            'metadata': self.metadata,
            'type': 'Header',
        }

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __key(self):
        return (str(self.data_type), self.unit, self.analysis_period)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, Header) and self.__key() == other.__key() and \
            self.metadata == other.metadata

    def __ne__(self, value):
        return not self.__eq__(value)

    def __repr__(self):
        """Return Ladybug header as a string."""
        a_per = self.analysis_period if self.analysis_period else ''
        if self.metadata != {}:
            meta_str = '\n'.join(['{}: {}'.format(key, val)
                                  for key, val in self.metadata.items()])
            return "{} ({})\n{}\n{}".format(
                self.data_type, self.unit, a_per, meta_str)
        else:
            return "{} ({})\n{}".format(
                self.data_type, self.unit, a_per)
