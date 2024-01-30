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
        time_zone: Time zone between -12 hours (west) and +14 hours (east). If None,
            the time zone will be an estimated integer value derived from the
            longitude in accordance with solar time (Default: None).
        elevation: A number for elevation of the location in meters. (Default: 0).
        station_id: ID of the location if the location is representing a weather station.
        source: Source of data (e.g. TMY, TMY3).

    Properties:
        * city
        * country
        * elevation
        * latitude
        * longitude
        * meridian
        * source
        * state
        * station_id
        * time_zone
        * is_default
    """

    __slots__ = ('city', 'state', 'country', '_lat', '_lon', '_tz', '_elev',
                 'station_id', 'source')

    def __init__(self, city=None, state=None, country=None, latitude=0, longitude=0,
                 time_zone=None, elevation=0, station_id=None, source=None):
        """Create a Ladybug location."""
        self.city = '-' if not city else str(city)
        self.state = '-' if not state else str(state)
        self.country = '-' if not country else str(country)
        self.latitude = latitude or 0
        self.longitude = longitude or 0
        self.time_zone = time_zone
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
        auto_dict = {'type': 'Autocalculate'}
        for key in optional_keys:
            if key not in data or data[key] == auto_dict:
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
                return cls.from_idf(location)
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

    @classmethod
    def from_idf(cls, idf_string):
        """Create a Ladybug location from an EnergyPlus IDF string.

        Args:
            idf_string: A full IDF string representing a Site:Location.
        """
        # format the object into a list of properties
        idf_string = idf_string.strip()
        assert idf_string.startswith('Site:Location'), 'Expected Site' \
            ':Location but received a different object: {}'.format(idf_string)
        idf_string = idf_string.replace(';', ',')
        idf_string = re.sub(r'!.*\n', '', idf_string)
        ep_fields = [e_str.strip() for e_str in idf_string.split(',')]
        ep_fields.pop(0)  # remove the EnergyPlus object name
        return cls(city=ep_fields[0], latitude=ep_fields[1], longitude=ep_fields[2],
                   time_zone=ep_fields[3], elevation=ep_fields[4])

    @property
    def latitude(self):
        """Get or set the location latitude in degrees."""
        return self._lat

    @latitude.setter
    def latitude(self, lat):
        self._lat = 0 if not lat else float(lat)
        assert -90 <= self._lat <= 90, \
            'latitude must be between -90 and 90. Got {}.'.format(self._lat)

    @property
    def longitude(self):
        """Get or set the location longitude in degrees."""
        return self._lon

    @longitude.setter
    def longitude(self, lon):
        self._lon = 0 if not lon else float(lon)
        assert -180 <= self._lon <= 180, \
            'longitude must be between -180 and 180. Got {}.'.format(self._lon)

    @property
    def time_zone(self):
        """Get or set the location time zone as a number between -12 and +14."""
        return self._tz

    @time_zone.setter
    def time_zone(self, tz):
        self._tz = round(self._lon / 15) if tz is None else float(tz)
        assert -12 <= self._tz <= 14, \
            'Time zone must be between -12 and +14 Got {}.'.format(self._tz)

    @property
    def elevation(self):
        """Get or set a number for the location elevation in meters."""
        return self._elev

    @elevation.setter
    def elevation(self, elev):
        try:
            self._elev = float(elev)
        except TypeError:
            raise ValueError("Failed to convert {} to an elevation".format(elev))

    @property
    def meridian(self):
        """Get a number between -180 and +180 for the meridian west of Greenwich."""
        return -15 * self.time_zone

    @property
    def is_default(self):
        """Get a boolean for whether the Location properties are defaulted."""
        return self.latitude == 0 and self.longitude == 0 and self.elevation == 0

    def duplicate(self):
        """Duplicate location."""
        return self.__copy__()

    def to_idf(self):
        """Get the Location as an EnergyPlus IDF string."""
        return "Site:Location,\n  " + \
            self.city + ',\n  ' + \
            str(self.latitude) + ',      !Latitude\n  ' + \
            str(self.longitude) + ',     !Longitude\n  ' + \
            str(self.time_zone) + ',     !Time Zone\n  ' + \
            str(self.elevation) + ';       !Elevation'

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

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __copy__(self):
        return Location(self.city, self.state, self.country,
                        self.latitude, self.longitude, self.time_zone, self.elevation,
                        self.station_id, self.source)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.city, self.state, self.country, self.latitude, self.longitude,
                self.time_zone, self.elevation, self.station_id, self.source)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, Location) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        """Return location as a string."""
        return "%s" % (self.to_idf())

    def __repr__(self):
        """Return location as a string."""
        # Tehran, lat:36, lon:34, tz:3.5, elev:54
        return "%s, lat:%.2f, lon:%.2f, tz:%.1f, elev:%.2f" % (
            self.city, self.latitude, self.longitude,
            self.time_zone, self.elevation)
