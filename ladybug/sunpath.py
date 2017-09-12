import math
from location import Location
from dt import DateTime
from euclid import Vector3
from collections import namedtuple

import ladybug
try:
    import sunpathplus as plus
except ImportError as e:
    if ladybug.isplus:
        raise ImportError(e)


class Sunpath(object):
    """
    Calculates sun path.

    Attributes:
        latitude: The latitude of the location in degrees. Values must be
            between -90 and 90. Default is set to the equator.
        north_angle: Angle to north (0-360). 90 is west and 270 is east
            (Default: 0)
        longitude: The longitude of the location in degrees (Default: 0)
        timezone: A number representing the time zone of the location you are
            constructing. This can improve the accuracy of the resulting sun
            plot.  The time zone should follow the epw convention and should be
            between -12 and +12, where 0 is at Greenwich, UK, positive values
            are to the East of Greenwich and negative values are to the West.
        daylight_saving_period: An analysis period for daylight saving.
            (Default: None)

    Usage:

        import ladybug.sunpath as sunpath
        # initiate sunpath
        sp = sunpath.Sunpath(50)
        sun = sp.calculate_sun(1, 1, 12) # calculate sun data for Jan 1 at noon
        print sun.azimuth, sun.altitude
    """

    __slots__ = ('_longitude', '_latitude', 'north_angle', 'timezone',
                 'daylight_saving_period')
    PI = math.pi

    def __init__(self, latitude=0, north_angle=0, longitude=0, timezone=0,
                 daylight_saving_period=None):
        """Init sunpath."""
        self.timezone = timezone
        self.latitude = latitude
        self.longitude = longitude
        self.north_angle = north_angle
        self.daylight_saving_period = daylight_saving_period

    @classmethod
    def from_location(cls, location, north_angle=0, daylight_saving_period=None):
        """Create a sun path from a LBlocation."""
        location = Location.from_location(location)
        return cls(location.latitude, north_angle, location.longitude,
                   location.timezone, daylight_saving_period)

    @property
    def latitude(self):
        """Get/set latitude in degrees."""
        return math.degrees(self._latitude)

    @latitude.setter
    def latitude(self, value):
        """Set latitude value."""
        self._latitude = math.radians(float(value))
        assert -self.PI / 2 <= self._latitude <= self.PI / 2, \
            "latitude value should be between -90..90."

    @property
    def longitude(self):
        """Get longitude in degrees."""
        return math.degrees(self._longitude)

    @longitude.setter
    def longitude(self, value):
        """Set longitude value in degrees."""
        self._longitude = math.radians(float(value))

        # update timezone
        if abs((value / 15.0) - self.timezone) > 1:
            # if timezone doesn't match the longitude update the timezone
            self.timezone = value / 15.0

    def is_daylight_saving_hour(self, datetime):
        """Check if a datetime is a daylight saving time."""
        if not self.daylight_saving_period:
            return False
        return self.daylight_saving_period.is_time_included(datetime.hoy)

    def calculate_sun(self, month, day, hour, is_solar_time=False):
        """Get Sun data for an hour of the year.

        Args:
            month: An integer between 1-12
            day: An integer between 1-31
            hour: A positive number between 0..23
            is_solar_time: A boolean to indicate if the input hour is solar time.
                (Default: False)

        Returns:
            A sun object for this particular time
        """
        datetime = DateTime(month, day, *self._calculate_hour_and_minute(hour))
        return self.calculate_sun_from_data_time(datetime, is_solar_time)

    def calculate_sun_from_hoy(self, hoy, is_solar_time=False):
        """Get Sun data for an hour of the year.

        Args:
            datetime: Ladybug datetime
            is_solar_time: A boolean to indicate if the input hour is solar time
                (Default: False).

        Returns:
            A sun object for this particular time
        """
        datetime = DateTime.from_hoy(hoy)
        return self.calculate_sun_from_data_time(datetime, is_solar_time)

    def calculate_sun_from_data_time(self, datetime, is_solar_time=False):
        """Get Sun for an hour of the year.

        This code is originally written by Trygve Wastvedt (Trygve.Wastvedt@gmail.com)
        based on (NOAA) and modified by Chris Mackey and Mostapha Roudsari

        Args:
            datetime: Ladybug datetime
            is_solar_time: A boolean to indicate if the input hour is solar time.
                (Default: False)

        Returns:
            A sun object for this particular time
        """
        sol_dec, eq_of_time = self._calculate_solar_geometry(datetime)

        hour = datetime.float_hour

        is_daylight_saving = self.is_daylight_saving_hour(datetime.hoy)

        hour = hour + 1 if self.is_daylight_saving_hour(datetime.hoy) else hour

        # hours
        sol_time = self._calculate_solar_time(hour, eq_of_time, is_solar_time)

        # degrees
        hour_angle = (sol_time * 15 + 180) if (sol_time * 15 < 0) \
            else (sol_time * 15 - 180)

        # RADIANS
        zenith = math.acos(math.sin(self._latitude) * math.sin(sol_dec) +
                           math.cos(self._latitude) * math.cos(sol_dec) *
                           math.cos(math.radians(hour_angle)))

        altitude = (math.pi / 2) - zenith

        if hour_angle == 0.0 or hour_angle == -180.0 or hour_angle == 180.0:

            azimuth = math.pi if sol_dec < self._latitude else 0.0

        else:
            azimuth = (
                (math.acos(
                    (
                        (math.sin(self._latitude) *
                         math.cos(zenith)) - math.sin(sol_dec)
                    ) /
                    (
                        math.cos(self._latitude) * math.sin(zenith)
                    )
                ) + math.pi) % (2 * math.pi)) if (hour_angle > 0) \
                else \
                (
                    (3 * math.pi -
                     math.acos(((math.sin(self._latitude) * math.cos(zenith)) -
                                math.sin(sol_dec)) /
                               (math.cos(self._latitude) * math.sin(zenith)))
                     ) % (2 * math.pi))

        # create the sun for this hour
        return Sun(datetime, altitude, azimuth, is_solar_time, is_daylight_saving,
                   self.north_angle)

    def calculate_sunrise_sunset(self, month, day, depression=0.833,
                                 is_solar_time=False):
        """Calculate sunrise, noon and sunset.

        Return:
            A dictionary. Keys are ("sunrise", "noon", "sunset")
        """
        datetime = DateTime(month, day, hour=12)

        return self.calculate_sunrise_sunset_from_date_time(datetime,
                                                            depression,
                                                            is_solar_time)

    # TODO: implement solar time
    def calculate_sunrise_sunset_from_date_time(self, datetime, depression=0.833,
                                                is_solar_time=False):
        """Calculate sunrise, sunset and noon for a day of year."""
        sol_dec, eq_of_time = self._calculate_solar_geometry(datetime)

        # calculate sunrise and sunset hour
        if is_solar_time:
            noon = .5
        else:
            noon = (720 -
                    4 * math.degrees(self._longitude) -
                    eq_of_time +
                    self.timezone * 60
                    ) / 1440.0

        try:
            sun_rise_hour_angle = self._calculate_sunrise_hour_angle(sol_dec, depression)
        except ValueError:
            # no sun rise and sunset at this hour
            noon = 24 * noon
            return {
                "sunrise": None,
                "noon": DateTime(datetime.month, datetime.day,
                                 *self._calculate_hour_and_minute(noon)),
                "sunset": None
            }
        else:
            sunrise = noon - sun_rise_hour_angle * 4 / 1440.0
            sunset = noon + sun_rise_hour_angle * 4 / 1440.0

            # convert demical hour to solar hour
            # noon = self._calculate_solar_time(24 * noon, eq_of_time, is_solar_time)
            # sunrise = self._calculate_solar_time(24 *
            #                                      sunrise, eq_of_time, is_solar_time)
            # sunset = self._calculate_solar_time(24 * sunset, eq_of_time, is_solar_time)

            noon = 24 * noon
            sunrise = 24 * sunrise
            sunset = 24 * sunset

            return {
                "sunrise": DateTime(datetime.month, datetime.day,
                                    *self._calculate_hour_and_minute(sunrise)),
                "noon": DateTime(datetime.month, datetime.day,
                                 *self._calculate_hour_and_minute(noon)),
                "sunset": DateTime(datetime.month, datetime.day,
                                   *self._calculate_hour_and_minute(sunset))
            }

    def _calculate_solar_geometry(self, datetime, year=2015):
        """Calculate Solar geometry for an hour of the year.

        Attributes:
            datetime: A Ladybug datetime

        Returns:
            Solar declination: Solar declination in radians
            eq_of_time: Equation of time as minutes
        """
        month, day, hour = datetime.month, datetime.day, datetime.float_hour

        a = 1 if (month < 3) else 0
        y = year + 4800 - a
        m = month + 12 * a - 3

        julian_day = day + math.floor((153 * m + 2) / 5) + 59

        julian_day += (hour - self.timezone) / 24.0 + 365 * y + \
            math.floor(y / 4) - math.floor(y / 100) + \
            math.floor(y / 400) - 32045.5 - 59

        julian_century = (julian_day - 2451545) / 36525

        # degrees
        geom_mean_long_sun = (280.46646 + julian_century *
                              (36000.76983 + julian_century * 0.0003032)
                              ) % 360

        # degrees
        geom_mean_anom_sun = 357.52911 + julian_century * \
            (35999.05029 - 0.0001537 * julian_century)

        eccent_orbit = 0.016708634 - julian_century * \
            (0.000042037 + 0.0000001267 * julian_century)

        sun_eq_of_ctr = math.sin(math.radians(geom_mean_anom_sun)) * \
            (1.914602 - julian_century * (0.004817 + 0.000014 * julian_century)) + \
            math.sin(math.radians(2 * geom_mean_anom_sun)) * \
            (0.019993 - 0.000101 * julian_century) + \
            math.sin(math.radians(3 * geom_mean_anom_sun)) * 0.000289

        # degrees
        sun_true_long = geom_mean_long_sun + sun_eq_of_ctr

        # AUs
        # sunTrueAnom = geom_mean_anom_sun + sun_eq_of_ctr

        # AUs
        # sunRadVector = (1.000001018 * (1 - eccent_orbit ** 2)) / \
        #     (1 + eccent_orbit * math.cos(math.radians(sunTrueLong)))

        # degrees
        sun_app_long = sun_true_long - 0.00569 - 0.00478 * \
            math.sin(math.radians(125.04 - 1934.136 * julian_century))

        # degrees
        mean_obliq_ecliptic = 23 + \
            (26 + ((21.448 - julian_century * (46.815 + julian_century *
                                               (0.00059 - julian_century *
                                                0.001813)))) / 60) / 60

        # degrees
        oblique_corr = mean_obliq_ecliptic + 0.00256 * \
            math.cos(math.radians(125.04 - 1934.136 * julian_century))

        # degrees
        # sunRightAscen = math.degrees(
        #     math.atan2(math.cos(math.radians(oblique_corr)) *
        #                math.sin(math.radians(sun_app_long)),
        #                math.cos(math.radians(sun_app_long))))

        # RADIANS
        sol_dec = math.asin(math.sin(math.radians(oblique_corr)) *
                            math.sin(math.radians(sun_app_long)))

        var_y = math.tan(math.radians(oblique_corr / 2)) * \
            math.tan(math.radians(oblique_corr / 2))

        # minutes
        eq_of_time = 4 \
            * math.degrees(
                var_y * math.sin(2 * math.radians(geom_mean_long_sun)) -
                2 * eccent_orbit * math.sin(math.radians(geom_mean_anom_sun)) +
                4 * eccent_orbit * var_y *
                math.sin(math.radians(geom_mean_anom_sun)) *
                math.cos(2 * math.radians(geom_mean_long_sun)) -
                0.5 * (var_y ** 2) *
                math.sin(4 * math.radians(geom_mean_long_sun)) -
                1.25 * (eccent_orbit ** 2) *
                math.sin(2 * math.radians(geom_mean_anom_sun))
            )

        return sol_dec, eq_of_time

    def _calculate_sunrise_hour_angle(self, solar_dec, depression=0.833):
        """Calculate hour angle for sunrise time in degrees."""
        hour_angle_arg = math.cos(math.radians(90 + depression)) \
            / (math.cos(self._latitude) * math.cos(solar_dec)) \
            - math.tan(self._latitude) * math.tan(solar_dec)

        return math.degrees(math.acos(hour_angle_arg))

    def _calculate_solar_time(self, hour, eq_of_time, is_solar_time):
        """Calculate Solar time for an hour."""
        if is_solar_time:
            return hour

        return (
            (hour * 60 + eq_of_time + 4 * math.degrees(self._longitude) -
             60 * self.timezone) % 1440) / 60

    def _calculate_solar_time_by_doy(self, hour, doy):
        """This is how radiance calculates solar time.

        This is a place holder and need to be validated against calculateSolarTime.
        """
        raise NotImplementedError()
        return (0.170 * math.sin((4 * math.pi / 373) * (doy - 80)) -
                0.129 * math.sin((2 * math.pi / 355) * (doy - 8)) +
                12 * (-(15 * self.timezone) - self.longitude) / math.pi)

    @staticmethod
    def _calculate_hour_and_minute(float_hour):
        """Calculate hour and minutes as integers from a float hour."""
        hour, minute = int(float_hour), int(round((float_hour - int(float_hour)) * 60))
        if minute == 60:
            return hour + 1, 0
        else:
            return hour, minute

    def draw_sunpath(self, hoys=None, origin=None, scale=1, sun_scale=1, annual=True,
                     rem_night=True):
        """Create sunpath geometry. This method should only be used from the + libraries.

        Args:
            hoys: An optional list of hours of the year (default: None).
            origin: Sunpath origin (default: (0, 0, 0)).
            scale: Sunpath scale (default: 1).
            sun_scale: Scale for the sun spheres (default: 1).
            annual: Set to True to draw an annual sunpath. Otherwise a daily sunpath is
                drawn.
            rem_night: Remove suns which are under the horizon (night!).
        Returns:
            base_curves: A collection of curves for base plot.
            analemma_curves: A collection of analemma_curves.
            daily_curves: A collection of daily_curves.
            suns: A list of suns.
        """
        # check and make sure the call is coming from inside a plus library
        assert ladybug.isplus, \
            '"drawSunPath" method can only be used in the [+] libraries.'
        hoys = hoys or ()
        origin = origin or (0, 0, 0)
        try:
            origin = tuple(origin)
        except TypeError as e:
            # dynamo
            try:
                origin = origin.X, origin.Y, origin.Z
            except AttributeError:
                raise TypeError(str(e))

        scale = scale or 1
        sun_scale = sun_scale or 1
        assert annual or hoys, 'For daily sunpath you need to provide at least one hour.'

        radius = 200 * scale

        # draw base circles and lines
        base_curves = plus.base_curves(origin, radius, self.north_angle)
        # draw analemma
        # calculate date times for analemma curves
        if annual:
            asuns = self._analemma_suns()
            analemma_curves = plus.analemma_curves(asuns, origin, radius)
        else:
            analemma_curves = ()

        # add sun spheres
        if hoys:
            suns = tuple(self.calculate_sun_from_hoy(hour) for hour in hoys)
        else:
            suns = ()

        if rem_night:
            suns = tuple(sun for sun in suns if sun.is_during_day)

        sun_geos = plus.sun_geometry(suns, origin, radius)

        # draw daily sunpath
        if annual:
            dts = (DateTime(m, 21) for m in xrange(1, 13))
        else:
            dts = (sun.datetime for sun in suns)

        dsuns = self._daily_suns(dts)
        daily_curves = plus.daily_curves(dsuns, origin, radius)

        SPGeo = namedtuple(
            'SunpathGeo',
            ('compassCurves', 'analemma_curves', 'daily_curves', 'suns', 'sunGeos'))

        # return outputs
        return SPGeo(base_curves, analemma_curves, daily_curves, suns, sun_geos)

    def _analemma_position(self, hour):
        """Check what the analemma position is for an hour.

        This is useful for calculating hours of analemma curves.

        Returns:
            -1 if always night,
            0 if both day and night,
            1 if always day.
        """
        # check for 21 dec and 21 jun
        low = self.calculate_sun(12, 21, hour).is_during_day
        high = self.calculate_sun(6, 21, hour).is_during_day

        if low and high:
            return 1
        elif low or high:
            return 0
        else:
            return -1

    def _analemma_suns(self):
        """Calculate times that should be used for drawing analemma_curves.

        Returns:
            A list of list of analemma suns.
        """
        for h in xrange(0, 24):
            if self._analemma_position(h) < 0:
                continue
            elif self._analemma_position(h) == 0:
                chours = []
                # this is an hour that not all the hours are day or night
                prevhour = self.latitude <= 0
                for hoy in xrange(h, 8760, 24):
                    thishour = self.calculate_sun_from_hoy(hoy).is_during_day
                    if thishour != prevhour:
                        if not thishour:
                            hoy -= 24
                        dt = DateTime.from_hoy(hoy)
                        chours.append((dt.month, dt.day, dt.hour))
                    prevhour = thishour
                tt = []
                for hcount in range(int(len(chours) / 2)):
                    st = chours[2 * hcount]
                    en = chours[2 * hcount + 1]
                    if self.latitude >= 0:
                        tt = [self.calculate_sun(*st)] + \
                            [self.calculate_sun(st[0], d, h)
                             for d in xrange(st[1] + 1, 29, 7)] + \
                            [self.calculate_sun(m, d, h)
                             for m in xrange(st[0] + 1, en[0])
                             for d in xrange(3, 29, 7)] + \
                            [self.calculate_sun(en[0], d, h)
                             for d in xrange(3, en[1], 7)] + \
                            [self.calculate_sun(*en)]
                    else:
                        tt = [self.calculate_sun(*en)] + \
                            [self.calculate_sun(en[0], d, h)
                             for d in xrange(en[1] + 1, 29, 7)] + \
                            [self.calculate_sun(m, d, h) for m in xrange(en[0] + 1, 13)
                             for d in xrange(3, 29, 7)] + \
                            [self.calculate_sun(m, d, h) for m in xrange(1, st[0])
                             for d in xrange(3, 29, 7)] + \
                            [self.calculate_sun(st[0], d, h)
                             for d in xrange(3, st[1], 7)] + \
                            [self.calculate_sun(*st)]
                    yield tt
            else:
                yield tuple(self.calculate_sun((m % 12) + 1, d, h)
                            for m in xrange(0, 13) for d in (7, 14, 21))[:-2]

    def _daily_suns(self, datetimes):
        """Get sun curve for multiple days of the year."""
        for dt in datetimes:
            # calculate sunrise sunset and noon
            nss = self.calculate_sunriseSunset(dt.month, dt.day)
            dts = tuple(nss[k] for k in ('sunrise', 'noon', 'sunset'))
            if dts[0] is None:
                # circle
                yield (self.calculate_sun(dt.month, dt.day, h) for h in (0, 12, 15)), \
                    False
            else:
                # Arc
                yield (self.calculate_sun_from_data_time(dt) for dt in dts), True


class Sun(object):
    """Sun.

    Attributes:
        datetime: A DateTime that represents the datetime for this sunVector
        altitude: Solar Altitude in **radians**
        azimuth: Solar Azimuth in **radians**
        is_solar_time: A Boolean that indicates if datetime represents the solar
            time.
        is_daylight_saving: A Boolean that indicates if datetime is calculated
            for Daylight saving period
        north_angle: North angle of the sunpath in Degrees. This will be only
            used to calculate the solar vector.
    """

    __slots__ = ('_datetime', '_altitude', '_azimuth', '_is_solar_time',
                 '_is_daylight_saving', '_north_angle', '_hourlyData', '_data',
                 '_sunVector')
    PI = math.pi

    def __init__(self, datetime, altitude, azimuth, is_solar_time,
                 is_daylight_saving, north_angle, data=None):
        """Init sun."""
        assert hasattr(datetime, 'is_date_time'), \
            "datetime must be a DateTime (not {})".format(type(datetime))
        self._datetime = datetime  # read-only

        assert -self.PI <= altitude <= self.PI, \
            "altitude({}) must be between {} and {}." \
            .format(altitude, -self.PI, self.PI)

        self._altitude = altitude  # read-only

        assert -2 * self.PI <= azimuth <= 2 * self.PI, \
            "azimuth({}) should be between {} and {}." \
            .format(azimuth, -self.PI, self.PI)

        self._azimuth = azimuth  # read-only
        self._is_solar_time = is_solar_time
        self._is_daylight_saving = is_daylight_saving
        # useful to calculate sun vector - sun angle is in degrees
        self._north_angle = north_angle
        self.data = data  # Place holder for hourly data

        self._calculate_sun_vector()

    @property
    def datetime(self):
        """Return datetime."""
        return self._datetime

    @property
    def north_angle(self):
        """Return north angle for +YAxis."""
        return self._north_angle

    @property
    def hoy(self):
        """Return Hour of the year."""
        return self._datetime.hoy

    @property
    def altitude(self):
        """Return solar altitude in degrees."""
        return math.degrees(self._altitude)

    @property
    def azimuth(self):
        """Return solar azimuth in degrees."""
        return math.degrees(self._azimuth)

    @property
    def altitude_in_radians(self):
        """Return solar altitude in radians."""
        return self._altitude

    @property
    def azimuth_in_radians(self):
        """Return solar azimuth in radians."""
        return self._azimuth

    @property
    def is_solar_time(self):
        """Return a Boolean that indicates is datetime is solar time."""
        return self._is_solar_time

    @property
    def is_daylight_saving(self):
        """Return a Boolean that indicates is datetime is solar time."""
        return self._is_daylight_saving

    @property
    def data(self):
        """Get or set data to this sun position."""
        return self._data

    @data.setter
    def data(self, d):
        self._data = d

    @property
    def is_during_day(self):
        """Check if this sun position is during day."""
        # sun vector is flipped to look to the center
        return self.sun_vector.z <= 0

    @property
    def sun_vector(self):
        """Sun vector for this sun.

        Sun vector faces downward (e.g. z will be negative.)
        """
        return self._sunVector

    def _calculate_sun_vector(self):
        """Calculate sun vector for this sun."""
        z_axis = Vector3(0., 0., -1.)
        x_axis = Vector3(1., 0., 0.)
        north_vector = Vector3(0., 1., 0.)

        # rotate north vector based on azimuth, altitude, and north
        _sunvector = north_vector \
            .rotate_around(x_axis, self.altitude_in_radians) \
            .rotate_around(z_axis, self.azimuth_in_radians) \
            .rotate_around(z_axis, math.radians(-1 * self.north_angle))

        _sunvector.normalize().flip()

        self._sunVector = _sunvector

    def ToString(self):
        """Overwrite .NET ToString method."""
        return self.__repr__()

    def __repr__(self):
        """Sun representation."""
        # sun at datetime (X, Y, Z)
        return "Sun at {} (x:{}, y:{}, z:{})".format(
            self.datetime,
            self.sun_vector.x,
            self.sun_vector.y,
            self.sun_vector.z
        )
