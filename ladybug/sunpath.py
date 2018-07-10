# coding=utf-8
import math
from collections import namedtuple
from .location import Location
from .dt import DateTime

import sys
if (sys.version_info > (3, 0)):
    # python 3
    from euclid3 import Vector3
    xrange = range
else:
    from euclid import Vector3

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
        longitude: The longitude of the location in degrees (Default: 0)
        time_zone: A number representing the time zone of the location you are
            constructing. This can improve the accuracy of the resulting sun
            plot.  The time zone should follow the epw convention and should be
            between -12 and +12, where 0 is at Greenwich, UK, positive values
            are to the East of Greenwich and negative values are to the West.
        north_angle: Angle to north (0-360). 90 is west and 270 is east
            (Default: 0)
        daylight_saving_period: An analysis period for daylight saving.
            (Default: None)

    Usage:

        import ladybug.sunpath as sunpath
        # initiate sunpath
        sp = sunpath.Sunpath(50)
        sun = sp.calculate_sun(1, 1, 12) # calculate sun data for Jan 1 at noon
        print(sun.azimuth, sun.altitude)
    """

    __slots__ = ('_longitude', '_latitude', 'north_angle', 'time_zone',
                 'daylight_saving_period', '_is_leap_year')
    PI = math.pi

    def __init__(self, latitude=0, longitude=0, time_zone=0, north_angle=0,
                 daylight_saving_period=None):
        """Init sunpath.

        Args:
            latitude: The latitude of the location in degrees. Values must be
                between -90 and 90. Default is set to the equator.
            longitude: The longitude of the location in degrees (Default: 0)
            time_zone: A number representing the time zone of the location you are
                constructing. This can improve the accuracy of the resulting sun
                plot.  The time zone should follow the epw convention and should be
                between -12 and +12, where 0 is at Greenwich, UK, positive values
                are to the East of Greenwich and negative values are to the West.
            north_angle: Angle to north (0-360). 90 is west and 270 is east
                (Default: 0).
            daylight_saving_period: An analysis period for daylight saving.
                (Default: None).

        """
        self.time_zone = time_zone
        self.latitude = latitude
        self.longitude = longitude
        self.north_angle = north_angle
        self.daylight_saving_period = daylight_saving_period
        self._is_leap_year = False

    @classmethod
    def from_location(cls, location, north_angle=0, daylight_saving_period=None):
        """Create a sun path from a LBlocation."""
        location = Location.from_location(location)
        return cls(location.latitude, location.longitude,
                   location.time_zone, north_angle, daylight_saving_period)

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

        # update time_zone
        if abs((value / 15.0) - self.time_zone) > 1:
            # if time_zone doesn't match the longitude update the time_zone
            self.time_zone = value / 15.0

    @property
    def is_leap_year(self):
        """Indicate is sunpath calculated for a leap year."""
        return self._is_leap_year

    @is_leap_year.setter
    def is_leap_year(self, value):
        """set sunpath to be calculated for a leap year."""
        self._is_leap_year = bool(value)

    def is_daylight_saving_hour(self, datetime):
        """Check if a datetime is a daylight saving time."""
        if not self.daylight_saving_period:
            return False
        return self.daylight_saving_period.isTimeIncluded(datetime.hoy)

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
        datetime = DateTime(month, day, *self._calculate_hour_and_minute(hour),
                            leap_year=self.is_leap_year)
        return self.calculate_sun_from_date_time(datetime, is_solar_time)

    def calculate_sun_from_hoy(self, hoy, is_solar_time=False):
        """Get Sun data for an hour of the year.

        Args:
            datetime: Ladybug datetime
            is_solar_time: A boolean to indicate if the input hour is solar time
                (Default: False).

        Returns:
            A sun object for this particular time
        """
        datetime = DateTime.from_hoy(hoy, self.is_leap_year)
        return self.calculate_sun_from_date_time(datetime, is_solar_time)

    def calculate_sun_from_date_time(self, datetime, is_solar_time=False):
        """Get Sun for an hour of the year.

        This code is originally written by Trygve Wastvedt \
         (Trygve.Wastvedt@gmail.com)
        based on (NOAA) and modified by Chris Mackey and Mostapha Roudsari

        Args:
            datetime: Ladybug datetime
            is_solar_time: A boolean to indicate if the input hour is solar time.
                (Default: False)

        Returns:
            A sun object for this particular time
        """
        # TODO(mostapha): This should be more generic and based on a method
        if datetime.year != 2016 and self.is_leap_year:
            datetime = DateTime(datetime.month, datetime.day, datetime.hour,
                                datetime.minute, True)

        sol_dec, eq_of_time = self._calculate_solar_geometry(datetime)

        hour = datetime.float_hour

        is_daylight_saving = self.is_daylight_saving_hour(datetime.hoy)

        hour = hour + 1 if self.is_daylight_saving_hour(datetime.hoy) else hour

        # minutes
        sol_time = self._calculate_solar_time(hour, eq_of_time, is_solar_time) * 60

        # degrees
        if sol_time / 4 < 0:
            hour_angle = sol_time / 4 + 180
        else:
            hour_angle = sol_time / 4 - 180

        # Degrees
        zenith = math.degrees(math.acos
                              (math.sin(self._latitude) *
                               math.sin(math.radians(sol_dec)) +
                               math.cos(self._latitude) *
                               math.cos(math.radians(sol_dec)) *
                               math.cos(math.radians(hour_angle))))

        altitude = 90 - zenith

        # Approx Atmospheric Refraction
        if altitude > 85:
            atmos_refraction = 0
        else:
            if altitude > 5:
                atmos_refraction = 58.1 / math.tan(math.radians(altitude))

                - 0.07 / (math.tan(math.radians(altitude)))**3
                + 0.000086 / (math.tan(math.radians(altitude)))**5
            else:
                if altitude > -0.575:
                    atmos_refraction = 1735

                    + altitude * (-518.2 + altitude *
                                  (103.4 + altitude *
                                   (-12.79 + altitude * 0.711)))
                else:

                    atmos_refraction = -20.772 / math.tan(
                        math.radians(altitude))

        atmos_refraction /= 3600

        altitude += atmos_refraction

        # Degrees
        if hour_angle > 0:
            azimuth = (math.degrees(
                math.acos(
                    (
                        (math.sin(self._latitude) *
                         math.cos(math.radians(zenith))) -
                        math.sin(math.radians(sol_dec))) /
                    (math.cos(self._latitude) *
                     math.sin(math.radians(zenith)))
                )
            ) + 180) % 360
        else:
            azimuth = (540 - math.degrees(math.acos((
                (math.sin(self._latitude) *
                 math.cos(math.radians(zenith))) -
                math.sin(math.radians(sol_dec))) /
                (math.cos(self._latitude) *
                 math.sin(math.radians(zenith))))
            )) % 360

        altitude = math.radians(altitude)
        azimuth = math.radians(azimuth)
        # create the sun for this hour
        return Sun(datetime, altitude, azimuth, is_solar_time, is_daylight_saving,
                   self.north_angle)

    def calculate_sunrise_sunset(self, month, day, depression=0.833,
                                 is_solar_time=False):
        """Calculate sunrise, noon and sunset.

        Return:
            A dictionary. Keys are ("sunrise", "noon", "sunset")
        """
        datetime = DateTime(month, day, hour=12, leap_year=self.is_leap_year)

        return self.calculate_sunrise_sunset_from_datetime(datetime,
                                                           depression,
                                                           is_solar_time)

    # TODO: implement solar time
    def calculate_sunrise_sunset_from_datetime(self, datetime, depression=0.833,
                                               is_solar_time=False):
        """Calculate sunrise, sunset and noon for a day of year."""
        # TODO(mostapha): This should be more generic and based on a method
        if datetime.year != 2016 and self.is_leap_year:
            datetime = DateTime(datetime.month, datetime.day, datetime.hour,
                                datetime.minute, True)
        sol_dec, eq_of_time = self._calculate_solar_geometry(datetime)
        # calculate sunrise and sunset hour
        if is_solar_time:
            noon = .5
        else:
            noon = (720 -
                    4 * math.degrees(self._longitude) -
                    eq_of_time +
                    self.time_zone * 60
                    ) / 1440.0

        try:
            sunrise_hour_angle = self._calculate_sunrise_hour_angle(
                sol_dec, depression)
        except ValueError:
            # no sun rise and sunset at this hour
            noon = 24 * noon
            return {
                "sunrise": None,
                "noon": DateTime(datetime.month, datetime.day,
                                 *self._calculate_hour_and_minute(noon),
                                 leap_year=self.is_leap_year),
                "sunset": None
            }
        else:
            sunrise = noon - sunrise_hour_angle * 4 / 1440.0
            sunset = noon + sunrise_hour_angle * 4 / 1440.0
            noon = 24 * noon
            sunrise = 24 * sunrise
            sunset = 24 * sunset

            return {
                "sunrise": DateTime(datetime.month, datetime.day,
                                    *self._calculate_hour_and_minute(sunrise),
                                    leap_year=self.is_leap_year),
                "noon": DateTime(datetime.month, datetime.day,
                                 *self._calculate_hour_and_minute(noon),
                                 leap_year=self.is_leap_year),
                "sunset": DateTime(datetime.month, datetime.day,
                                   *self._calculate_hour_and_minute(sunset),
                                   leap_year=self.is_leap_year)
            }

    def _calculate_solar_geometry(self, datetime):
        """Calculate Solar geometry for an hour of the year.

        Attributes:
            datetime: A Ladybug datetime

        Returns:
            Solar declination: Solar declination in radians
            eq_of_time: Equation of time as minutes
        """
        month = datetime.month
        day = datetime.day
        hour = datetime.hour
        minute = datetime.minute
        year = 2016 if self.is_leap_year else 2017

        def find_fraction_of_24(hour, minute):
            """
            This function calculates the fraction of the 24 hour
            the provided time represents
            1440 is total the number of minutes in a 24 hour cycle.
            args
                hour: Integer. Hour between 0 - 23
                minute: Integer. Minute between 0 - 59
            return: Float.
                The fraction of the 24 hours the provided time represents
            """
            return round((minute + hour * 60) / 1440.0, 2)

        def days_from_010119(year, month, day):
            """
            This function calculates the number of days from 01-01-1900 \
            to the provided date
            args :
                year: Integer. The year in the date
                month: Integer. The month in the date
                day: Integer. The date
            return: The number of days from 01-01-1900 to the date provided
            """

            # Making a list of years from the year 1900
            years = range(1900, year)

            def is_leap_year(year):
                """Determine whether a year is a leap year."""
                return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

            # Number of days in a year are 366 if it is a leap year
            days_in_year = []
            for item in years:
                if is_leap_year(item):
                    days_in_year.append(366)
                else:
                    days_in_year.append(365)

            # Making the total of all the days in preceding years
            days_in_precending_years = 0
            for days in days_in_year:
                days_in_precending_years += days

            if is_leap_year(year):
                month_dict = {1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30,
                              7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
            else:
                month_dict = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
                              7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}

            """Making the total of all the days in preceding months\
            in the same year"""
            keys = tuple(month_dict.keys())
            days_in_precending_months = 0
            for i in range(month - 1):
                days_in_precending_months += month_dict[keys[i]]

            return days_in_precending_years + days_in_precending_months + day + 1

        julian_day = days_from_010119(year, month, day) + 2415018.5 + \
            find_fraction_of_24(hour, minute) - (float(self.time_zone) / 24)

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

        sun_eq_of_ctr = math.sin(
            math.radians(geom_mean_anom_sun)) * \
            (1.914602 - julian_century * (0.004817 + 0.000014 * julian_century)
             ) +\
            math.sin(math.radians(2 * geom_mean_anom_sun)) * \
            (0.019993 - 0.000101 * julian_century) + \
            math.sin(math.radians(3 * geom_mean_anom_sun)) * \
            0.000289

        # degrees
        sun_true_long = geom_mean_long_sun + sun_eq_of_ctr

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

        # RADIANS
        sol_dec = math.degrees(math.asin(math.sin(math.radians(oblique_corr)) *
                                         math.sin(math.radians(sun_app_long))))

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

        hour_angle_arg = math.degrees(math.acos(
            math.cos(math.radians(90 + depression)) /
            (math.cos(math.radians(self.latitude)) * math.cos(
                math.radians(solar_dec))) -
            math.tan(math.radians(self.latitude)) *
            math.tan(math.radians(solar_dec))
        ))

        return hour_angle_arg

    def _calculate_solar_time(self, hour, eq_of_time, is_solar_time):
        """Calculate Solar time for an hour."""
        if is_solar_time:
            return hour

        return (
            (hour * 60 + eq_of_time + 4 * math.degrees(self._longitude) -
             60 * self.time_zone) % 1440) / 60

    def _calculate_solar_time_by_doy(self, hour, doy):
        """This is how radiance calculates solar time.

        This is a place holder and \
        need to be validated against calculateSolarTime.
        """
        raise NotImplementedError()
        return (0.170 * math.sin((4 * math.pi / 373) * (doy - 80)) -
                0.129 * math.sin((2 * math.pi / 355) * (doy - 8)) +
                12 * (-(15 * self.time_zone) - self.longitude) / math.pi)

    @staticmethod
    def _calculate_hour_and_minute(float_hour):
        """Calculate hour and minutes as integers from a float hour."""
        hour = int(float_hour)
        minute = int(round((float_hour - int(float_hour)) * 60))

        if minute == 60:
            return hour + 1, 0
        else:
            return hour, minute

    def draw_sunpath(self,
                     hoys=None,
                     origin=None,
                     scale=1, sun_scale=1, annual=True, rem_night=True):
        """Create sunpath geometry. \
        This method should only be used from the + libraries.

        Args:
            hoys: An optional list of hours of the year(default: None).
            origin: Sunpath origin(default: (0, 0, 0)).
            scale: Sunpath scale(default: 1).
            sun_scale: Scale for the sun spheres(default: 1).
            annual: Set to True to draw an annual sunpath.
                Otherwise a daily sunpath is drawn.
            rem_night: Remove suns which are under the horizon(night!).
        Returns:
            base_curves: A collection of curves for base plot.
            analemma_curves: A collection of analemma_curves.
            daily_curves: A collection of daily_curves.
            suns: A list of suns.
        """
        # check and make sure the call is coming from inside a plus library
        assert ladybug.isplus, \
            '"draw_sunpath" method can only be used in the [+] libraries.'
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
            ('compass_curves',
             'analemma_curves',
             'daily_curves',
             'suns',
             'sun_geos'))

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
                num_of_days = 8760 if not self.is_leap_year else 8760 + 24
                for hoy in xrange(h, num_of_days, 24):
                    thishour = self.calculate_sun_from_hoy(hoy).is_during_day
                    if thishour != prevhour:
                        if not thishour:
                            hoy -= 24
                        dt = DateTime.from_hoy(hoy, self.is_leap_year)
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
                            [self.calculate_sun(m, d, h) for m in xrange(en[0] +
                                                                         1, 13)
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
            nss = self.calculate_sunrise_sunset(dt.month, dt.day)
            dts = tuple(nss[k] for k in ('sunrise', 'noon', 'sunset'))
            if dts[0] is None:
                # circle
                yield (self.calculate_sun(dt.month, dt.day, h) for h in (0, 12,
                                                                         15)), \
                    False
            else:
                # Arc
                yield (self.calculate_sun_from_date_time(dt) for dt in dts), True


class Sun(object):
    """Sun.

    Attributes:
        datetime: A DateTime that represents the datetime for this sun_vector
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
                 '_sun_vector')
    PI = math.pi

    def __init__(self, datetime, altitude, azimuth, is_solar_time,
                 is_daylight_saving, north_angle, data=None):
        """Init sun."""
        assert hasattr(datetime, 'isDateTime'), \
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

        Sun vector faces downward(e.g. z will be negative.)
        """
        return self._sun_vector

    def _calculate_sun_vector(self):
        """Calculate sun vector for this sun."""
        z_axis = Vector3(0., 0., -1.)
        x_axis = Vector3(1., 0., 0.)
        north_vector = Vector3(0., 1., 0.)

        # rotate north vector based on azimuth, altitude, and north
        _sun_vector = north_vector \
            .rotate_around(x_axis, self.altitude_in_radians) \
            .rotate_around(z_axis, self.azimuth_in_radians) \
            .rotate_around(z_axis, math.radians(-1 * self.north_angle))

        _sun_vector.normalize()
        try:
            _sun_vector.flip()
        except AttributeError:
            # euclid3
            _sun_vector = Vector3(-1 * _sun_vector.x,
                                  -1 * _sun_vector.y,
                                  -1 * _sun_vector.z)

        self._sun_vector = _sun_vector

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
