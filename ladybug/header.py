"""Ladybug Header.

Header is useful for creating list of ladybug data.
"""
from .location import Location
from .analysisperiod import AnalysisPeriod


class Header(object):
    """data collection header.

    Header carries data for location, data type, unit and analysis period

    Attributes:
        location: location data as a ladybug Location or location string
            (Default: None).
        data_type: Type of data (e.g. Temperature) (Default: None).
        unit: data_type unit (Default: None).
        analysis_period: A Ladybug analysis period (Defualt: None)
    """

    def __init__(self, location=None, data_type=None, unit=None, analysis_period=None):
        """Initiate Ladybug header for lists.

        Args:
            location: location data as a ladybug Location or location string
                (Default: None).
            data_type: Type of data (e.g. Temperature) (Default: None).
            unit: data_type unit (Default: None).
            analysis_period: A Ladybug analysis period (Defualt: None)
        """
        self.location = Location.from_location(location)
        self.data_type = data_type if data_type else None
        self.unit = unit if unit else None
        self.analysis_period = AnalysisPeriod.from_analysis_period(analysis_period)

    @classmethod
    def from_header(cls, header):
        """Try to generate a header from a header or a header string."""
        if hasattr(header, 'isHeader'):
            return header

        # "%s|%s(%s)|%s"
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
        return self.__class__(self.location, self.data_type, self.unit,
                              self.analysis_period)

    def to_tuple(self):
        """Return Ladybug header as a list."""
        return (
            self.location,
            self.data_type,
            self.unit,
            self.analysis_period
        )

    def __iter__(self):
        """Return data as tuple."""
        return self.to_tuple()

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """Return Ladybug header as a string."""
        return "%s|%s(%s)|%s" % (
            repr(self.location), self.data_type, self.unit, self.analysis_period)
