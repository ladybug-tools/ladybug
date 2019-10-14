# coding=utf-8
"""Ladybug location."""
from __future__ import division

import re


class Location(object):
    """Ladybug Location.

    Args:
        city: Name of the city as a string.
        state: Optional state in which the city is located.
        country: Name of the country as a string.
        latitude: Location latitude between -90 and 90 (Default: 0).
        longitude: Location longitude between -180 (west) and 180 (east) (Default: 0).
        time_zone: Time zone between -12 hours (west) and 12 hours (east) (Default: 0).
        elevation: A number for elevation of the location.
        station_id: ID of the location if the location is represnting a weather station.
        source: Source of data (e.g. TMY, TMY3).

    Properties:
        * city
        * country
        * elevation
        * ep_style_location_string
        * latitude
        * longitude
        * meridian
        * source
        * state
        * station_id
        * time_zone
    """

    __slots__ = ("city", "state", "country", "_lat", "_lon", "_tz", "_elev",
                 "station_id", "source")

    def __init__(self, city=None, state=None, country=None, latitude=0, longitude=0,
                 time_zone=0, elevation=0, station_id=None, source=None):
        """Create a Ladybug location."""
        self.city = '-' if not city else str(city)
        self.state = '-' if not state else str(state)
        self.country = '-' if not country else str(country)
        self.latitude = latitude or 0
        self.longitude = longitude or 0
        self.time_zone = time_zone or 0
        self.elevation = elevation or 0
        self.station_id = None if not station_id else str(station_id)
        self.source = source

    @classmethod
    def from_dict(cls, data):
        """Create a location from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

                {
                "city": "-",
                "latitude": 0,
                "longitude": 0,
                "time_zone": 0,
                "elevation": 0
                }
        """
        optional_keys = ('city', 'state', 'country', 'latitude', 'longitude',
                         'time_zone', 'elevation', 'station_id', 'source')
        for key in optional_keys:
            if key not in data:
                data[key] = None

        return cls(data['city'], data['state'], data['country'], data['latitude'],
                   data['longitude'], data['time_zone'], data['elevation'],
                   data['station_id'], data['source'])

    @classmethod
    def from_location(cls, location):
        """Try to create a Ladybug location from a location string.

        Args:
            locationString: Location string

        Usage:

        .. code-block:: python

            l = Location.from_location(locationString)
        """
        if not location:
            return cls()
        try:
            if isinstance(location, Location):
                # Ladybug location
                return location

            elif hasattr(location, 'Latitude'):
                # Revit's location
                return cls(city=str(location.Name.replace(",", " ")),
                           latitude=location.Latitude,
                           longitude=location.Longitude)

            elif location.startswith('Site:'):
                loc, city, latitude, longitude, time_zone, elevation = \
                    [x.strip() for x in re.findall(r'\r*\n*([^\r\n]*)[,|;]',
                                                   location, re.DOTALL)]
            else:
                try:
                    city, latitude, longitude, time_zone, elevation = \
                        [key.split(":")[-1].strip()
                         for key in location.split(",")]
                except ValueError:
                    # it's just the city name
                    return cls(city=location)

            return cls(city=city, country=None, latitude=latitude,
                       longitude=longitude, time_zone=time_zone,
                       elevation=elevation)

        except Exception as e:
            raise ValueError(
                "Failed to create a Location from %s!\n%s" % (location, e))

    @property
    def isLocation(self):
        """Return Ture."""
        return True

    @property
    def latitude(self):
        """Location latitude."""
        return self._lat

    @latitude.setter
    def latitude(self, lat):
        self._lat = 0 if not lat else float(lat)
        assert -90 <= self._lat <= 90, "latitude should be between -90..90."

    @property
    def longitude(self):
        """Location longitude."""
        return self._lon

    @longitude.setter
    def longitude(self, lon):
        self._lon = 0 if not lon else float(lon)
        assert -180 <= self._lon <= 180, "longitude should be between -180..180."

    @property
    def time_zone(self):
        """Location time zone."""
        return self._tz

    @time_zone.setter
    def time_zone(self, tz):
        self._tz = 0 if not tz else float(tz)
        assert -12 <= self._tz <= 12, "Time zone should be between -12.0..12.0"

    @property
    def elevation(self):
        """Location elevation."""
        return self._elev

    @elevation.setter
    def elevation(self, elev):
        try:
            self._elev = float(elev)
        except TypeError:
            raise ValueError("Failed to convert {} to an elevation".format(elev))

    @property
    def meridian(self):
        """Location meridian west of Greenwich."""
        return -15 * self.time_zone

    def duplicate(self):
        """Duplicate location."""
        return Location(self.city, self.state, self.country,
                        self.latitude, self.longitude, self.time_zone, self.elevation,
                        self.station_id, self.source)

    @property
    def ep_style_location_string(self):
        """Return EnergyPlus's location string."""
        return "Site:Location,\n  " + \
            self.city + ',\n  ' + \
            str(self.latitude) + ',      !Latitude\n  ' + \
            str(self.longitude) + ',     !Longitude\n  ' + \
            str(self.time_zone) + ',     !Time Zone\n  ' + \
            str(self.elevation) + ';       !Elevation'

    def __str__(self):
        """Return location as a string."""
        return "%s" % (self.ep_style_location_string)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def to_dict(self):
        """Get location as a a dictionary."""
        return {
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "time_zone": self.time_zone,
            "elevation": self.elevation,
            "station_id": self.station_id,
            "source": self.source,
            "type": 'Location'
        }

    def __repr__(self):
        """Return location as a string."""
        # Tehran, lat:36, lon:34, tz:3.5, elev:54
        return "%s, lat:%.2f, lon:%.2f, tz:%.1f, elev:%.2f" % (
            self.city, self.latitude, self.longitude,
            self.time_zone, self.elevation)
