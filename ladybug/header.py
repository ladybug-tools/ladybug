"""Ladybug Header.

Header is useful for creating list of ladybug data.
"""
from .location import Location
from .analysisperiod import AnalysisPeriod


class Header(object):
    """Ladybug header.

    Header carries data for location, data type, unit and analysis period

    Attributes:
        location: location data as a ladybug Location or location string
            (Default: None).
        dataType: Type of data (e.g. Temperature) (Default: None).
        unit: dataType unit (Default: None).
        analysisPeriod: A Ladybug analysis period (Defualt: None)
    """

    def __init__(self, location=None, dataType=None, unit=None, analysisPeriod=None):
        """Initiate Ladybug header for lists."""
        self.location = Location.fromLocation(location)
        self.dataType = dataType if dataType else None
        self.unit = unit if unit else None
        self.analysisPeriod = AnalysisPeriod.fromAnalysisPeriod(analysisPeriod)

    @classmethod
    def fromHeader(cls, header):
        """Try to generate a header from a header or a header string."""
        if hasattr(header, 'isHeader'):
            return header

        # "%s|%s(%s)|%s"
        try:
            _h = header.replace("|", "**").replace("(", "**").replace(")", "")
            return cls(*_h.split("**"))
        except Exception, e:
            raise ValueError(
                "Failed to create a Header from %s!\n%s" % (header, e))

    @property
    def isHeader(self):
        """Return True."""
        return True

    def duplicate(self):
        """Duplicate header."""
        return self.__class__(self.location, self.dataType, self.unit,
                              self.analysisPeriod)

    def toTuple(self):
        """Return Ladybug header as a list."""
        return (
            self.location,
            self.dataType,
            self.unit,
            self.analysisPeriod
        )

    def __iter__(self):
        """Return data as tuple."""
        return self.toTuple()

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """Return Ladybug header as a string."""
        return "%s|%s(%s)|%s" % (
            repr(self.location), self.dataType, self.unit, self.analysisPeriod)
