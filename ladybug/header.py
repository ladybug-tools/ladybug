# coding=utf-8
"""Ladybug Header"""
from __future__ import division

from copy import deepcopy

from .location import Location
from .analysisperiod import AnalysisPeriod
from .datatype import DataTypes, DataTypeBase


class Header(object):
    """DataCollection header.

    Header carries meatdata for data type, unit, analysis period, and location

    Attributes:
        data_type: A DataType object or text indicating the name of a DataType.
            (e.g. Temperature) (Default: None).
        unit: data_type unit (Default: None).
        analysis_period: A Ladybug analysis period (Defualt: None)
        location: Location data as a ladybug Location or location string
            (Default: None).
    """

    __slots__ = ('_data_type', '_unit', '_analysis_period', '_location')

    def __init__(self, data_type=None, unit=None,
                 analysis_period=None, location=None):
        """Initiate Ladybug header for lists.

        Args:
            data_type: A DataType object or text indicating the name of the DataType.
                (e.g. Temperature) (Default: 'Unknown Data').
            unit: data_type unit (Default: None)
            analysis_period: A Ladybug analysis period (Defualt: None)
            location: location data as a ladybug Location or location string
                (Default: None)
        """
        data_type = data_type or 'Unknown Data'
        self.set_data_type_and_unit(data_type, unit)
        self.analysis_period = analysis_period
        self.location = location

    @classmethod
    def from_json(cls, data):
        """Create a header from a dictionary.

        Args:
            data: {
                "data_type": {}, //Type of data (e.g. Temperature)
                "unit": string,
                "analysis_period": {} // A Ladybug AnalysisPeriod
                "location": {}, // A Ladybug location
            }
        """
        # assign default values
        keys = ('data_type', 'unit', 'analysis_period', 'location')
        for key in keys:
            if key not in data:
                data[key] = None

        data_type = DataTypeBase.from_json(data['data_type'])
        ap = AnalysisPeriod.from_json(data['analysis_period'])
        location = Location.from_json(data['location'])
        return cls(data_type, data['unit'], ap, location)

    @classmethod
    def from_header(cls, header):
        """Try to generate a header from a header or a header string."""
        if hasattr(header, 'isHeader'):
            return header

        # "%s(%s)|%s|%s"
        try:
            _h = header.replace("|", "**").replace("(", "**").replace(")", "")
            return cls(*_h.split("**"))
        except Exception as e:
            raise ValueError(
                "Failed to create a Header from %s!\n%s" % (header, e))

    @property
    def data_type(self):
        """A DataType object."""
        return self._data_type

    @property
    def unit(self):
        """A text string representing an abbreviated unit."""
        return self._unit

    @property
    def analysis_period(self):
        """A AnalysisPeriod object."""
        return self._analysis_period

    @analysis_period.setter
    def analysis_period(self, ap):
        self._analysis_period = AnalysisPeriod.from_analysis_period(ap)

    @property
    def location(self):
        """A Location object."""
        return self._location

    @location.setter
    def location(self, loc):
        self._location = Location.from_location(loc)

    @property
    def isHeader(self):
        """Return True."""
        return True

    def set_data_type_and_unit(self, data_type, unit):
        """Set data_type and unit. This method should NOT be used for unit conversions.

        For unit conversions, the to_unit() method should be used on the data collection.
        """
        if hasattr(data_type, 'isDataType'):
            data_type.is_unit_acceptable(unit)
            self._data_type = data_type
        else:
            self._data_type = DataTypes.type_by_name_and_unit(data_type, unit)
        self._unit = unit if unit else None

    def duplicate(self):
        """Return a copy of the header."""
        return self.__class__(deepcopy(self.data_type), self.unit,
                              AnalysisPeriod.from_string(str(self.analysis_period)),
                              deepcopy(self.location))

    def to_tuple(self):
        """Return Ladybug header as a list."""
        return (
            self.data_type,
            self.unit,
            self.analysis_period,
            self.location
        )

    def __iter__(self):
        """Return data as tuple."""
        return self.to_tuple()

    def to_json(self):
        """Return a header as a dictionary."""
        return {'data_type': self.data_type.to_json(),
                'unit': self.unit,
                'analysis_period': self.analysis_period.to_json(),
                'location': self.location.to_json()}

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """Return Ladybug header as a string."""
        return "%s(%s)|%s|%s" % (
            repr(self.data_type), self.unit,
            self.analysis_period, repr(self.location))
