# coding=utf-8
"""Ladybug Header.

Header is useful for creating list of ladybug data.
"""
from .location import Location
from .analysisperiod import AnalysisPeriod
from .datatypenew import DataTypes
from .datatypenew import DataTypeBase


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

    __slots__ = ('data_type', 'unit', 'analysis_period', 'location')

    def __init__(self, data_type, unit=None,
                 analysis_period=None, location=None):
        """Initiate Ladybug header for lists.

        Args:
            data_type: A DataType object or text indicating the name of a DataType.
                (e.g. Temperature) (Default: None).
            unit: data_type unit (Default: None)
            analysis_period: A Ladybug analysis period (Defualt: None)
            location: location data as a ladybug Location or location string
                (Default: None)
        """
        if hasattr(data_type, 'isDataType'):
            data_type.is_unit_acceptable(unit)
            self.data_type = data_type
        else:
            self.data_type = DataTypes.type_by_name_and_unit(data_type, unit)
        self.unit = unit if unit else None
        self.analysis_period = AnalysisPeriod.from_analysis_period(analysis_period)
        self.location = Location.from_location(location)

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
    def isHeader(self):
        """Return True."""
        return True

    def duplicate(self):
        """Duplicate header."""
        return self.__class__(self.data_type, self.unit, self.analysis_period,
                              self.location)

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
