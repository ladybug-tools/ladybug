"""Ladybug location."""
import re


class Location(object):
    """Ladybug Location.

    Attributes:
        city: Name of the city as a string.
        country: Name of the country as a string.
        latitude: Location latitude between -90 and 90 (Default: 0).
        longitude: Location longitude between -180 (west) and 180 (east) (Default: 0).
        timezone: Time zone between -12 hours (west) and 12 hours (east) (Default: 0).
        elevation: A number for elevation of the location.
        stationId: Id of the location if the location is represnting a weather station.
        source: Source of data (e.g. TMY, TMY3).
    """

    __slots__ = ("city", "country", "__lat", "__lon", "__tz", "__elev",
                 "stationId", "source")

    def __init__(self, city=None, country=None, latitude=0, longitude=0,
                 timezone=0, elevation=0, stationId=None, source=None):
        """Create a Ladybug location."""
        self.city = "unknown" if not city else str(city)
        self.country = "unknown" if not country else str(country)
        self.latitude = latitude
        self.longitude = longitude
        self.timezone = timezone
        self.elevation = float(elevation)
        self.stationId = None if not stationId else str(stationId)
        self.source = source

    @classmethod
    def fromLocation(cls, location):
        """Try to create a Ladybug location from a location string.

        Args:
            locationString: Location string

        Usage:

            l = Location.fromString(locationString)
        """
        if not location:
            return cls()
        try:
            if hasattr(location, 'isLocation'):
                # Ladybug location
                return location

            elif hasattr(location, 'Latitude'):
                # Revit's location
                return cls(city=str(location.Name.replace(",", " ")),
                           latitude=location.Latitude,
                           longitude=location.Longitude)

            elif location.startswith('Site:'):
                loc, city, latitude, longitude, timezone, elevation = \
                    re.findall(r'\r*\n*([a-zA-Z0-9.:_-]*)[,|;]',
                               location,
                               re.DOTALL)
            else:
                try:
                    city, latitude, longitude, timezone, elevation = \
                        [key.split(":")[-1].strip()
                         for key in location.split(",")]
                except ValueError:
                    # it's just the city name
                    return cls(city=location)

            return cls(city=city, country=None, latitude=latitude,
                       longitude=longitude, timezone=timezone,
                       elevation=elevation)

        except Exception, e:
            raise ValueError(
                "Failed to create a Location from %s!\n%s" % (location, e))

    @property
    def isLocation(self):
        """Return Ture."""
        return True

    @property
    def latitude(self):
        """Location latitude."""
        return self.__lat

    @latitude.setter
    def latitude(self, lat):
        self.__lat = 0 if not lat else float(lat)
        assert -90 <= self.__lat <= 90, "latitude should be between -90..90."

    @property
    def longitude(self):
        """Location latitude."""
        return self.__lon

    @longitude.setter
    def longitude(self, lon):
        self.__lon = 0 if not lon else float(lon)
        assert -180 <= self.__lon <= 180, "longitude should be between -180..180."

    @property
    def timezone(self):
        """Location latitude."""
        return self.__tz

    @timezone.setter
    def timezone(self, tz):
        self.__tz = 0 if not tz else float(tz)
        assert -12 <= self.__tz <= 12, "Time zone should be between -12.0..12.0"

    @property
    def elevation(self):
        """Location latitude."""
        return self.__elev

    @elevation.setter
    def elevation(self, elev):
        try:
            self.__elev = float(elev)
        except TypeError:
            raise ValueError("Failed to convert {} to an elevation".format(elev))

    @property
    def meridian(self):
        """Location meridian west of Greenwich."""
        return -15 * self.timezone

    def duplicate(self):
        """Duplicate location."""
        return self(self.city, self.country, self.latitude, self.longitude,
                    self.timezone, self.elevation, self.stationId, self.source)

    @property
    def EPStyleLocationString(self):
        """Return EnergyPlus's location string."""
        return "Site:Location,\n" + \
            self.city + ',\n' + \
            str(self.latitude) + ',      !Latitude\n' + \
            str(self.longitude) + ',     !Longitude\n' + \
            str(self.timezone) + ',     !Time Zone\n' + \
            str(self.elevation) + ';       !Elevation'

    def __str__(self):
        """Return location as a string."""
        return "%s" % (self.EPStyleLocationString)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """Return location as a string."""
        # Tehran, lat:36, lon:34, tz:3.5, elev:54
        return "%s, lat:%.2f, lon:%.2f, tz:%.1f, elev:%.2f" % (
            self.city, self.latitude, self.longitude,
            self.timezone, self.elevation)
