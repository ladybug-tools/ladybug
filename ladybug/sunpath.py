# coding=utf-8
"""Module for calculating sun positions and visualizing the sun path."""
from __future__ import division

from .location import Location
from .dt import DateTime
from .analysisperiod import AnalysisPeriod
from .compass import Compass

from ladybug_geometry.geometry3d.pointvector import Vector3D, Point3D
from ladybug_geometry.geometry3d.plane import Plane
from ladybug_geometry.geometry3d.arc import Arc3D
from ladybug_geometry.geometry3d.polyline import Polyline3D
from ladybug_geometry.geometry3d.line import LineSegment3D
from ladybug_geometry.geometry2d.pointvector import Point2D
from ladybug_geometry.geometry2d.polyline import Polyline2D

import datetime as py_datetime
import math
import sys
if (sys.version_info > (3, 0)):  # python 3
    xrange = range


class Sunpath(object):
    """Calculate sun positions and visualize the sun path

    Args:
        latitude: A number between -90 and 90 for the latitude of the location
            in degrees. (Default: 0 for the equator)
        longitude: A number between -180 and 180 for the longitude of the location
            in degrees (Default: 0 for the prime meridian)
        time_zone: A number representing the time zone of the location for the
            sun path. Typically, this value is an integer, assuming that a
            standard time zone is used but this value can also be a decimal
            for the purposes of modeling location-specific solar time.
            The time zone should follow the epw convention and should be
            between -12 and +14, where 0 is at Greenwich, UK, positive values
            are to the East of Greenwich and negative values are to the West.
            If None, this value will be set to solar time using the Sunpath's
            longitude. (Default: None).
        north_angle: A number between -360 and 360 for the counterclockwise
            difference between the North and the positive Y-axis in degrees.
            90 is West and 270 is East (Default: 0).
        daylight_saving_period: An analysis period for daylight saving time.
            If None, no daylight saving time will be used. (Default: None)

    Properties:
        * latitude
        * longitude
        * time_zone
        * north_angle
        * daylight_saving_period
        * is_leap_year

    Usage:

    .. code-block:: python

        import ladybug.sunpath as sunpath
        # initiate sunpath
        sp = sunpath.Sunpath(50)
        sun = sp.calculate_sun(1, 1, 12) # calculate sun data for Jan 1 at noon
        print(sun.azimuth, sun.altitude)
    """

    __slots__ = ('_longitude', '_latitude', '_north_angle', '_time_zone',
                 '_daylight_saving_period', '_is_leap_year')
    PI = math.pi

    def __init__(self, latitude=0, longitude=0, time_zone=None, north_angle=0,
                 daylight_saving_period=None):
        """Init sunpath.
        """
        self.latitude = latitude
        self.longitude = longitude
        self.time_zone = time_zone
        self.north_angle = north_angle
        self.daylight_saving_period = daylight_saving_period
        self._is_leap_year = False

    @classmethod
    def from_location(cls, location, north_angle=0, daylight_saving_period=None):
        """Create a sun path from a ladybug.location.Location."""
        location = Location.from_location(location)
        return cls(location.latitude, location.longitude,
                   location.time_zone, north_angle, daylight_saving_period)

    @property
    def latitude(self):
        """Get or set a number between -90 and 90 for the latitude in degrees."""
        return math.degrees(self._latitude)

    @latitude.setter
    def latitude(self, value):
        self._latitude = math.radians(float(value))
        assert -self.PI / 2 <= self._latitude <= self.PI / 2, \
            'latitude value should be between -90 and 90. Got {}.'.format(value)
        if self._latitude == self.PI / 2:  # prevent math domain errors
            self._latitude = self._latitude - 1e-9
        if self._latitude == -self.PI / 2:  # prevent math domain errors
            self._latitude = self._latitude + 1e-9

    @property
    def longitude(self):
        """Get or set a number between -180 and 180 for the longitude in degrees.

        Note that you will also likely want to update the time zone of the
        Sunpath if this value is set to something far from its original value.
        """
        return math.degrees(self._longitude)

    @longitude.setter
    def longitude(self, value):
        self._longitude = math.radians(float(value))
        assert -self.PI <= self._longitude <= self.PI, \
            'longitude value should be between -180 and 180. Got {}.'.format(value)

    @property
    def time_zone(self):
        """Get or set the time zone as a number between -12 and + 14.

        Setting this property to None will automatically set the Sunpath to use
        solar time for the Sunpath's longitude.
        """
        return self._time_zone

    @time_zone.setter
    def time_zone(self, tz):
        self._time_zone = self.longitude / 15 if tz is None else float(tz)
        assert -12 <= self._time_zone <= 14, \
            'Time zone must be between -12 and +14. Got {}.'.format(self._time_zone)

    @property
    def north_angle(self):
        """Get or set a number between -360 and 360 for the north_angle in degrees."""
        return math.degrees(self._north_angle)

    @north_angle.setter
    def north_angle(self, value):
        self._north_angle = math.radians(float(value))
        assert -self.PI * 2 <= self._north_angle <= self.PI * 2, \
            'north_angle value should be between -360 and 360. Got {}.'.format(value)

    @property
    def is_leap_year(self):
        """Get or set a boolean to indicate is sunpath calculated for a leap year."""
        return self._is_leap_year

    @is_leap_year.setter
    def is_leap_year(self, value):
        """set sunpath to be calculated for a leap year."""
        self._is_leap_year = bool(value)

    @property
    def daylight_saving_period(self):
        """Get or set an AnalysisPeriod for the daylight saving period.

        Note that the st_hour and end_hour of the AnalysisPeriod will be interpreted
        as indicating the time of day when the shift in clocks happen. So setting the
        st_hour and end_hour to 2 will ensure that the time shift happens at 2 AM on
        the dates specified. Note that this is different than how the hour inputs of
        AnalysisPeriods typically work, where the st_hour and end_hour apply to every
        day of the analysis period.

        If None, no daylight saving period will be used.
        """
        return self._daylight_saving_period

    @daylight_saving_period.setter
    def daylight_saving_period(self, value):
        if value is not None:
            assert isinstance(value, AnalysisPeriod), \
                'Daylight saving period should be an AnalysisPeriod not %s' % type(value)
        self._daylight_saving_period = value

    def is_daylight_saving_hour(self, datetime):
        """Check if a datetime is within the daylight saving time."""
        if not self.daylight_saving_period:
            return False
        if self.daylight_saving_period.is_reversed:
            return self.daylight_saving_period.end_time.moy <= datetime.moy or \
                self.daylight_saving_period.st_time.moy >= datetime.moy
        else:
            return self.daylight_saving_period.st_time.moy <= datetime.moy < \
                self.daylight_saving_period.end_time.moy

    def calculate_sun(self, month, day, hour, is_solar_time=False):
        """Get Sun data for an hour of the year.

        Args:
            month: An integer between 1 and 12.
            day: An integer between 1 and 31.
            hour: A positive number between 0 and 23. This can be a decimal value
                to yield a solar position in between hours (eg. 12.5).
            is_solar_time: A boolean to indicate if the input hour is in solar
                time. (Default: False)

        Returns:
            A sun object for the input month, day, hour.
        """
        datetime = DateTime(month, day, *self._calculate_hour_and_minute(hour),
                            leap_year=self.is_leap_year)
        return self.calculate_sun_from_date_time(datetime, is_solar_time)

    def calculate_sun_from_hoy(self, hoy, is_solar_time=False):
        """Get Sun data for an hour of the year.

        Args:
            hoy: A number for the hour of the year. This can be a decimal value
                to yield a solar position in between hours (eg. 12.5).
            is_solar_time: A boolean to indicate if the input hoy is in solar
                time. (Default: False)

        Returns:
            A sun object for the input hoy.
        """
        datetime = DateTime.from_hoy(hoy, self.is_leap_year)
        return self.calculate_sun_from_date_time(datetime, is_solar_time)

    def calculate_sun_from_moy(self, moy, is_solar_time=False):
        """Get Sun data for a minute of the year.

        Args:
            moy: An integer for the minute of the year.
            is_solar_time: A boolean to indicate if the input moy is in solar
                time. (Default: False)

        Returns:
            A sun object for the input moy.
        """
        datetime = DateTime.from_moy(moy, self.is_leap_year)
        return self.calculate_sun_from_date_time(datetime, is_solar_time)

    def calculate_sun_from_date_time(self, datetime, is_solar_time=False):
        """Get Sun for a specific datetime.

        This code is originally written by Trygve Wastvedt (Trygve.Wastvedt@gmail.com)
        based on (NOAA) and modified by Chris Mackey and Mostapha Roudsari.

        Args:
            datetime: Ladybug datetime.
            is_solar_time: A boolean to indicate if the input hour is in solar
                time. (Default: False)

        Returns:
            A sun object for the input datetime.
        """
        # TODO(mostapha): This should be more generic and based on a method
        if datetime.year != 2016 and self.is_leap_year:
            datetime = DateTime(datetime.month, datetime.day, datetime.hour,
                                datetime.minute, True)

        # compute solar geometry
        sol_dec, eq_of_time = self._calculate_solar_geometry(datetime)

        # get the correct mintue of the day for which solar position is to be computed
        try:
            hour = datetime.float_hour
        except AttributeError:  # native Python datetime; try to compute manually
            hour = datetime.hour + datetime.minute / 60.0
        is_daylight_saving = self.is_daylight_saving_hour(datetime)
        hour = hour - 1 if is_daylight_saving else hour  # spring forward!
        sol_time = self._calculate_solar_time(hour, eq_of_time, is_solar_time) * 60

        # degrees for the angle between solar noon and the current time.
        hour_angle = sol_time / 4 + 180 if sol_time < 0 else sol_time / 4 - 180

        # radians for the zenith and degrees for altitude
        zenith = math.acos(math.sin(self._latitude) * math.sin(sol_dec) +
                           math.cos(self._latitude) * math.cos(sol_dec) *
                           math.cos(math.radians(hour_angle)))
        altitude = 90 - math.degrees(zenith)

        # approx atmospheric refraction used to correct the altitude
        if altitude > 85:
            atmos_refraction = 0
        elif altitude > 5:
            atmos_refraction = 58.1 / math.tan(math.radians(altitude)) - \
                0.07 / (math.tan(math.radians(altitude))) ** 3 + \
                0.000086 / (math.tan(math.radians(altitude))) ** 5
        elif altitude > -0.575:
            atmos_refraction = 1735 + altitude * \
                (-518.2 + altitude * (103.4 + altitude * (-12.79 + altitude * 0.711)))
        else:
            atmos_refraction = -20.772 / math.tan(math.radians(altitude))

        atmos_refraction /= 3600
        altitude += atmos_refraction

        # azimuth in degrees
        az_init = ((math.sin(self._latitude) * math.cos(zenith)) - math.sin(sol_dec)) / \
            (math.cos(self._latitude) * math.sin(zenith))
        try:
            if hour_angle > 0:
                azimuth = (math.degrees(math.acos(az_init)) + 180) % 360
            else:
                azimuth = (540 - math.degrees(math.acos(az_init))) % 360
        except ValueError:  # perfect solar noon yields math domain error
            azimuth = 180

        # create the sun for this hour
        return Sun(datetime, altitude, azimuth, is_solar_time, is_daylight_saving,
                   self.north_angle)

    def calculate_sunrise_sunset(self, month, day, depression=0.5334,
                                 is_solar_time=False):
        """Calculate sunrise, noon and sunset.

        Args:
            month: Integer for the month in which sunrise and sunset are computed.
            day: Integer for the day of the month in which sunrise and sunset
                are computed.
            depression: An angle in degrees indicating the additional period
                before/after the edge of the sun has passed the horizon where
                the sun is still considered up. Setting this value to 0 will
                compute sunrise/sunset as the time when the edge of the sun begins
                to touch the horizon. Setting it to the angular diameter of the
                sun (0.5334) will compute sunrise/sunset as the time when the sun
                just finishes passing the horizon (actual sunset). Setting it
                to 0.833 will compute the apparent sunrise/sunset, accounting for
                atmospheric refraction. Setting this to 6 will compute sunrise/sunset
                as the beginning/end of civil twilight. Setting this to 12 will
                compute sunrise/sunset as the beginning/end of nautical twilight.
                Setting this to 18 will compute sunrise/sunset as the beginning/end
                of astronomical twilight. (Default: 0.5334).
            is_solar_time: A boolean to indicate if the output datetimes for sunrise,
                noon and sunset should be in solar time as opposed to the time zone
                of this Sunpath. (Default: False)

        Return:
            A dictionary. Keys are ("sunrise", "noon", "sunset"). Values are
            datetimes that correspond to these moments. Note that some values
            may be None if there is no sunrise or sunset on the specified day.
        """
        datetime = DateTime(month, day, hour=12, leap_year=self.is_leap_year)
        return self.calculate_sunrise_sunset_from_datetime(
            datetime, depression, is_solar_time)

    def calculate_sunrise_sunset_from_datetime(self, datetime, depression=0.5334,
                                               is_solar_time=False):
        """Calculate sunrise, sunset and noon for a day of year.

        Args:
            datetime: A ladybug DateTime object to indicate the month and day for
                which sunrise and sunset are computed.
            depression: An angle in degrees indicating the additional period
                before/after the edge of the sun has passed the horizon where
                the sun is still considered up. Setting this value to 0 will
                compute sunrise/sunset as the time when the edge of the sun begins
                to touch the horizon. Setting it to the angular diameter of the
                sun (0.5334) will compute sunrise/sunset as the time when the sun
                just finishes passing the horizon (actual sunset). Setting it
                to 0.833 will compute the apparent sunrise/sunset, accounting for
                atmospheric refraction. Setting this to 6 will compute sunrise/sunset
                as the beginning/end of civil twilight. Setting this to 12 will
                compute sunrise/sunset as the beginning/end of nautical twilight.
                Setting this to 18 will compute sunrise/sunset as the beginning/end
                of astronomical twilight. (Default: 0.5334).
            is_solar_time: A boolean to indicate if the output datetimes for sunrise,
                noon and sunset should be in solar time as opposed to the time zone
                of this Sunpath. (Default: False)

        Return:
            A dictionary. Keys are ("sunrise", "noon", "sunset"). Values are
            datetimes that correspond to these moments. Note that some values
            may be None if there is no sunrise or sunset on the specified day.
        """
        # TODO(mostapha): This should be more generic and based on a method
        if datetime.year != 2016 and self.is_leap_year:
            datetime = DateTime(datetime.month, datetime.day, datetime.hour,
                                datetime.minute, True)
        sol_dec, eq_of_time = self._calculate_solar_geometry(datetime)
        # calculate sunrise and sunset hour
        if is_solar_time:
            noon = .5
        else:
            noon = (720 - 4 * self.longitude - eq_of_time + self.time_zone * 60) / 1440.

        try:
            sunrise_hour_angle = self._calculate_sunrise_hour_angle(
                sol_dec, math.radians(depression))
        except ValueError:
            # no sunrise/sunset on this day (eg. arctic circle in summer/winter)
            noon = 24 * noon
            return {
                'sunrise': None,
                'noon': DateTime(datetime.month, datetime.day,
                                 *self._calculate_hour_and_minute(noon),
                                 leap_year=self.is_leap_year),
                'sunset': None
            }
        else:
            sunrise = noon - sunrise_hour_angle * 4 / 1440.0
            sunset = noon + sunrise_hour_angle * 4 / 1440.0
            noon = 24 * noon
            sunrise = 24 * sunrise
            sunset = 24 * sunset

            # compute sunrise datetime
            if sunrise >= 0:
                sunrise = DateTime(
                    datetime.month, datetime.day,
                    *self._calculate_hour_and_minute(sunrise),
                    leap_year=self.is_leap_year)
            else:  # sunrise before midnight
                sr_dt = datetime.sub_hour(24)
                hr, mn = self._calculate_hour_and_minute(sunrise)
                hr = 23 + hr
                mn = 60 + mn
                sunrise = DateTime(
                    sr_dt.month, sr_dt.day, hr, mn, leap_year=self.is_leap_year)

            # compute noon datetime
            noon = DateTime(
                datetime.month, datetime.day, *self._calculate_hour_and_minute(noon),
                leap_year=self.is_leap_year)

            # compute sunset datetime
            if sunset < 24:
                sunset = DateTime(
                    datetime.month, datetime.day,
                    *self._calculate_hour_and_minute(sunset),
                    leap_year=self.is_leap_year)
            else:  # sunset after midnight
                ss_dt = datetime.add_hour(24)
                hr, mn = self._calculate_hour_and_minute(sunset)
                hr = hr - 24
                sunset = DateTime(
                    ss_dt.month, ss_dt.day, hr, mn, leap_year=self.is_leap_year)

            return {'sunrise': sunrise, 'noon': noon, 'sunset': sunset}

    def analemma_suns(
            self, time, daytime_only=False, is_solar_time=False,
            start_month=1, end_month=12, steps_per_month=1):
        """Get an array of Suns that represent an analemma for a single time of day.

        Args:
            time: A ladybug Time object for the specific time of day to make
                the analemma.
            daytime_only: A boolean to note whether only daytime suns should
                be included in the resulting array. Note that this can
                result in a completely empty array. (Default: False)
            is_solar_time: A boolean to indicate if the output analemmas should
                be for solar hours instead of the hours of the sunpath time
                zone. (Default: False)
            start_month: An integer from 1 to 12 to set the staring month for which
                the analemma is drawn. (Default: 1).
            end_month: An integer from 1 to 12 to set the ending month for which
                the analemma is drawn. (Default: 12).
            steps_per_month: An integer to set the number of sun positions that
                will be used to represent a single month. Higher numbers will
                take more time to compute but can produce smoother-looking
                analemmas. (Default: 1).

        Returns:
            An array of suns representing an analemma for a specific time.
            Analemmas will each have 12 suns for the 12 months of the year
            if daytime_only is False.
        """
        analemma = []
        for mon in range(start_month, end_month + 1):
            if steps_per_month == 1:  # use the 21st of each month
                dat_t = DateTime(mon, 21, time.hour, time.minute)
                analemma.append(self.calculate_sun_from_date_time(dat_t, is_solar_time))
            else:
                dpm = AnalysisPeriod.NUMOFDAYSEACHMONTH[mon - 1]
                for day in range(1, dpm + 1, int(dpm / steps_per_month)):
                    dat_t = DateTime(mon, day, time.hour, time.minute)
                    dat_t_sun = self.calculate_sun_from_date_time(dat_t, is_solar_time)
                    analemma.append(dat_t_sun)
        if daytime_only:  # filter out the nighttime sun positions
            analemma = [sun for sun in analemma if sun.is_during_day]
        return analemma

    def hourly_analemma_suns(
            self, daytime_only=False, is_solar_time=False,
            start_month=1, end_month=12, steps_per_month=1):
        """Get a nested array of Suns with one sub-array for each hourly analemma.

        Args:
            daytime_only: A boolean to note whether only daytime suns should
                be included in the resulting arrays. Note that this will likely
                result in completely empty arrays for some hours. (Default: False)
            is_solar_time: A boolean to indicate if the output analemmas should
                be for solar hours instead of the hours of the sunpath time
                zone. (Default: False).
            start_month: An integer from 1 to 12 to set the staring month for which
                the analemma is drawn. (Default: 1).
            end_month: An integer from 1 to 12 to set the ending month for which
                the analemma is drawn. (Default: 12).
            steps_per_month: An integer to set the number of sun positions that
                will be used to represent a single month. Higher numbers will
                take more time to compute but can produce smoother-looking
                analemmas. (Default: 1).

        Returns:
            An array of 24 arrays with each sub-array representing an analemma.
            Analemmas will have a number of suns equal to (end_month - start_month) *
            steps_per_month. The default is 12 suns for the 12 months of the year.
        """
        analemmas = []  # list of polylines
        for hr in range(24):
            analem = []
            for mon in range(start_month, end_month + 1):
                if steps_per_month == 1:  # use the 21st of each month
                    dat = DateTime(mon, 21, hr)
                    analem.append(self.calculate_sun_from_date_time(dat, is_solar_time))
                else:
                    dpm = AnalysisPeriod.NUMOFDAYSEACHMONTH[mon - 1]
                    for day in range(1, dpm + 1, int(dpm / steps_per_month)):
                        dat = DateTime(mon, day, hr)
                        dat_sun = self.calculate_sun_from_date_time(dat, is_solar_time)
                        analem.append(dat_sun)
            analemmas.append(analem)
        if daytime_only:  # filter out the nighttime sun positions
            for i, analem in enumerate(analemmas):
                analemmas[i] = [sun for sun in analem if sun.is_during_day]
        return analemmas

    def hourly_analemma_polyline3d(
            self, origin=Point3D(), radius=100, daytime_only=True, is_solar_time=False,
            start_month=1, end_month=12, steps_per_month=1):
        """Get an array of ladybug_geometry Polyline3D for hourly analemmas.

        Args:
            origin: A ladybug_geometry Point3D to note the center of the sun path.
            radius: A number to note the radius of the sunpath.
            daytime_only: A boolean to note whether only the daytime hours should
                be represented in the output Polyline3D. (Default: True)
            is_solar_time: A boolean to indicate if the output analemmas should
                be for solar hours instead of the hours of the sunpath time
                zone. (Default: False).
            start_month: An integer from 1 to 12 to set the staring month for which
                the analemma is drawn. (Default: 1).
            end_month: An integer from 1 to 12 to set the ending month for which
                the analemma is drawn. (Default: 12).
            steps_per_month: An integer to set the number of sun positions that
                will be used to represent a single month. Higher numbers will
                take more time to compute but can produce smoother-looking
                analemmas. (Default: 1).

        Returns:
            An array of ladybug_geometry Polyline3D with at least one polyline
            for each analemma.
        """
        analemmas = []  # list of polylines
        analem_suns = self.hourly_analemma_suns(
            is_solar_time=is_solar_time, start_month=start_month, end_month=end_month,
            steps_per_month=steps_per_month)
        for analem in analem_suns:
            pts = []
            for sun in analem:
                pts.append(sun.position_3d(origin, radius))
            if start_month == 1 and end_month == 12:
                pts.append(pts[0])  # ensure that the Polyline3D is closed
            analemmas.append(Polyline3D(pts, interpolated=True))
        if not daytime_only:  # no need to further process the analemmas
            return analemmas

        # extract only the daytime portion of the analemmas
        daytime_analemmas = []
        plane_o = Plane(o=origin)
        for analem in analemmas:
            if analem.min.z > origin.z:  # fast check for analemmas above the plane
                daytime_analemmas.append(analem)
            elif analem.max.z < origin.z:  # fast check for analemmas below the plane
                pass
            else:  # split the Polylines with a plane at the input origin
                split_lines = analem.split_with_plane(plane_o)
                day_lines = []
                first_pt = None
                for pl in split_lines:
                    if isinstance(pl, Polyline3D) and pl.center.z > origin.z:
                        day_lines.append(pl)
                    elif isinstance(pl, LineSegment3D) and pl.midpoint.z > origin.z:
                        try:  # last line segment in intersection; append it to the first
                            new_pl = Polyline3D((pl.p1,) + day_lines[0].vertices, True)
                            day_lines[0] = new_pl
                        except IndexError:  # first line segment in the intersection
                            first_pt = pl.p2
                if first_pt is not None and len(day_lines) > 0:
                    new_pl = Polyline3D(day_lines[0].vertices + (first_pt,), True)
                    day_lines[0] = new_pl
                daytime_analemmas.extend(day_lines)
        return daytime_analemmas

    def hourly_analemma_polyline2d(
            self, projection='Orthographic', origin=Point2D(), radius=100,
            daytime_only=True, is_solar_time=False, start_month=1, end_month=12,
            steps_per_month=1):
        """Get an array of ladybug_geometry Polyline2D for hourly analemmas.

        Args:
            projection: Text for the name of the projection to use from the sky
                dome hemisphere to the 2D plane. (Default: 'Orthographic'). Choose
                from the following:

                * Orthographic
                * Stereographic

            origin: A ladybug_geometry Point2D to note the center of the sun path.
            radius: A number to note the radius of the sunpath.
            daytime_only: A boolean to note whether only the daytime hours should
                be represented in the output Polyline2D. (Default: True)
            is_solar_time: A boolean to indicate if the output analemmas should
                be for solar hours instead of the hours of the sunpath time
                zone. (Default: False).
            start_month: An integer from 1 to 12 to set the staring month for which
                the analemma is drawn. (Default: 1).
            end_month: An integer from 1 to 12 to set the ending month for which
                the analemma is drawn. (Default: 12).
            steps_per_month: An integer to set the number of sun positions that
                will be used to represent a single month. Higher numbers will
                take more time to compute but can produce smoother-looking
                analemmas. (Default: 1).

        Returns:
            An array of ladybug_geometry Polyline2D with at least one polyline for
            each analemma.
        """
        # compute the analemmas in 3D space
        o_3d = Point3D(origin.x, origin.y, 0)
        plines_3d = self.hourly_analemma_polyline3d(
            o_3d, radius, daytime_only, is_solar_time, start_month, end_month,
            steps_per_month)
        return self._project_polyline_to_2d(plines_3d, projection, radius, o_3d)

    def day_arc3d(self, month, day, origin=Point3D(), radius=100, daytime_only=True,
                  depression=0.5334):
        """Get a ladybug_geometry Arc3D for the path taken by the sun on a single day.

        Args:
            month: Integer for the month in which sunrise and sunset are computed.
            day: Integer for the day of the month in which sunrise and sunset
                are computed.
            origin: A ladybug_geometry Point3D to note the center of the sun path.
            radius: A number to note the radius of the sunpath.
            daytime_only: A boolean to note whether None should be returned if
                the sun never rises above the horizon on the the input day.
                For example, in the arctic circle in winter. (Default: True)
            depression: An angle in degrees indicating the additional period
                before/after the edge of the sun has passed the horizon where
                the sun is still considered up. Setting this value to 0 will
                return an arc that ends when the edge of the sun begins to
                touch the horizon. Setting it to the angular diameter of the
                sun (0.5334) will return an arc that ends right at the horizon
                (actual sunset). Setting it to 0.833 will compute the apparent
                sunrise/sunset, accounting for atmospheric refraction. Setting to
                6 will return an arc that ends at the beginning/end of civil twilight.
                Setting to 12 will return an arc that ends at the beginning/end
                of nautical twilight. Setting to 18 will return an arc that
                ends at the beginning/end of astronomical twilight. (Default: 0.5334)

        Returns:
            An Arc3D for the path of the sun taken over the course of a day. Will be
            None if daytime_only is True and the sun is completely below the horizon
            for the entire day.
        """
        # get the sunrise, noon, and sunset time
        riseset_dict = self.calculate_sunrise_sunset(month, day, depression)

        # create the arcs from the sun positions
        if riseset_dict['sunrise'] is None:  # no sunrise; add a full circle
            noon = self.calculate_sun_from_date_time(riseset_dict['noon'])
            if daytime_only and noon.sun_vector.z > 0:  # night time
                return None
            sun6am = self.calculate_sun(month, day, 6)
            sun6pm = self.calculate_sun(month, day, 18)
            pts = [sun.position_3d(origin, radius) for sun in (sun6am, noon, sun6pm)]
            return Arc3D.from_start_mid_end(pts[0], pts[1], pts[2], circle=True)
        else:  # create an arc that respects the depression
            rise_noon_set_suns = (
                self.calculate_sun_from_date_time(riseset_dict['sunrise']),
                self.calculate_sun_from_date_time(riseset_dict['noon']),
                self.calculate_sun_from_date_time(riseset_dict['sunset']))
            positions = (sun.position_3d(origin, radius) for sun in rise_noon_set_suns)
            return Arc3D.from_start_mid_end(*positions)

    def day_polyline2d(
            self, month, day, projection='Orthographic', origin=Point2D(),
            radius=100, daytime_only=True, depression=0.5334, divisions=10):
        """Get a Polyline2D for the path taken by the sun on a single day.

        Args:
            month: Integer for the month in which sunrise and sunset are computed.
            day: Integer for the day of the month in which sunrise and sunset
                are computed.
            projection: Text for the name of the projection to use from the sky
                dome hemisphere to the 2D plane. (Default: 'Orthographic'). Choose
                from the following:

                * Orthographic
                * Stereographic

            origin: A ladybug_geometry Point2D to note the center of the sun path.
            radius: A number to note the radius of the sunpath.
            daytime_only: A boolean to note whether None should be returned if
                the sun never rises above the horizon on the the input day.
                For example, in the arctic circle in winter. (Default: True)
            depression: An angle in degrees indicating the additional period
                before/after the edge of the sun has passed the horizon where
                the sun is still considered up. Setting this value to 0 will
                return an arc that ends when the edge of the sun begins to
                touch the horizon. Setting it to the angular diameter of the
                sun (0.5334) will return an arc that ends right at the horizon
                (actual sunset). Setting it to 0.833 will compute the apparent
                sunrise/sunset, accounting for atmospheric refraction. Setting to
                6 will return an arc that ends at the beginning/end of civil twilight.
                Setting to 12 will return an arc that ends at the beginning/end
                of nautical twilight. Setting to 18 will return an arc that
                ends at the beginning/end of astronomical twilight. (Default: 0.5334)

        Returns:
            A Polyline2D for the path of the sun taken over the course of a day. Will be
            None if daytime_only is True and the sun is completely below the horizon
            for the entire day.
        """
        # compute the daily arc in 3D space
        o_3d = Point3D(origin.x, origin.y, 0)
        arc_3d = self.day_arc3d(month, day, o_3d, radius, daytime_only, depression)
        if arc_3d is not None:
            pline_3d = arc_3d.to_polyline(divisions, interpolated=True)
            return self._project_polyline_to_2d([pline_3d], projection, radius, o_3d)[0]

    def monthly_day_arc3d(
            self, origin=Point3D(), radius=100, daytime_only=True, depression=0.5334):
        """Get an array of Arc3Ds for the path taken by the sun on the 21st of each month.

        Args:
            origin: A ladybug_geometry Point3D to note the center of the sun path.
            radius: A number to note the radius of the sunpath.
            daytime_only: A boolean to note whether arcs should be excluded from the
                output array if the sun never rises above the horizon on the the day.
                For example, in the arctic circle in winter. (Default: True)
            depression: An angle in degrees indicating the additional period
                before/after the edge of the sun has passed the horizon where
                the sun is still considered up. Setting this value to 0 will
                return an arc that ends when the edge of the sun begins to
                touch the horizon. Setting it to the angular diameter of the
                sun (0.5334) will return an arc that ends right at the horizon
                (actual sunset). Setting it to 0.833 will compute the apparent
                sunrise/sunset, accounting for atmospheric refraction. Setting to
                6 will return an arc that ends at the beginning/end of civil twilight.
                Setting to 12 will return an arc that ends at the beginning/end
                of nautical twilight. Setting to 18 will return an arc that
                ends at the beginning/end of astronomical twilight. (Default: 0.5334)

        Returns:
            An array of ladybug_geometry Arc3D with an arc for the 21st of each month.
        """
        day_arcs = []
        for mon in range(1, 13):
            arc = self.day_arc3d(mon, 21, origin, radius, daytime_only, depression)
            if arc is not None:
                day_arcs.append(arc)
        return day_arcs

    def monthly_day_polyline2d(
            self, projection='Orthographic', origin=Point2D(), radius=100,
            daytime_only=True, depression=0.5334, divisions=10):
        """Get an array of Polyline2Ds for the sun path on the 21st of each month.

        Args:
            projection: Text for the name of the projection to use from the sky
                dome hemisphere to the 2D plane. (Default: 'Orthographic'). Choose
                from the following:

                * Orthographic
                * Stereographic

            origin: A ladybug_geometry Point2D to note the center of the sun path.
            radius: A number to note the radius of the sunpath.
            daytime_only: A boolean to note whether arcs should be excluded from the
                output array if the sun never rises above the horizon on the the day.
                For example, in the arctic circle in winter. (Default: True)
            depression: An angle in degrees indicating the additional period
                before/after the edge of the sun has passed the horizon where
                the sun is still considered up. Setting this value to 0 will
                return an arc that ends when the edge of the sun begins to
                touch the horizon. Setting it to the angular diameter of the
                sun (0.5334) will return an arc that ends right at the horizon
                (actual sunset). Setting it to 0.833 will compute the apparent
                sunrise/sunset, accounting for atmospheric refraction. Setting to
                6 will return an arc that ends at the beginning/end of civil twilight.
                Setting to 12 will return an arc that ends at the beginning/end
                of nautical twilight. Setting to 18 will return an arc that
                ends at the beginning/end of astronomical twilight. (Default: 0.5334)
            divisions: An integer for the number of divisions to be used when
                converting the daily arcs into Polyline2Ds. (Default: 10).

        Returns:
            An array of ladybug_geometry Polyline2D with a polyline for the 21st
            of each month.
        """
        # compute the daily arcs in 3D space
        o_3d = Point3D(origin.x, origin.y, 0)
        arcs_3d = self.monthly_day_arc3d(o_3d, radius, daytime_only, depression)
        plines_3d = [arc.to_polyline(divisions, interpolated=True) for arc in arcs_3d]
        return self._project_polyline_to_2d(plines_3d, projection, radius, o_3d)

    def _calculate_solar_geometry(self, datetime):
        """Calculate parameters related to solar geometry for an hour of the year.

        Attributes:
            datetime: A Ladybug datetime

        Returns:
            A tuple with two values

            - sol_dec: Solar declination in radians. Declination is analogous to
                latitude on Earth's surface, and measures an angular displacement
                north or south from the projection of Earth's equator on the
                celestial sphere to the location of a celestial body.

            - eq_of_time: Equation of time in minutes. This is an astronomical
                term accounting for changes in the time of solar noon for a given
                location over the course of a year. Earth's elliptical orbit and
                Kepler's law of equal areas in equal times are the culprits
                behind this phenomenon.
        """
        year, month, day, hour, minute = \
            datetime.year, datetime.month, datetime.day, datetime.hour, datetime.minute

        julian_day = self._days_from_010119(year, month, day) + 2415018.5 + \
            round((minute + hour * 60) / 1440.0, 2) - (float(self.time_zone) / 24)

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

    def _calculate_sunrise_hour_angle(self, solar_dec, depression):
        """Calculate hour angle for sunrise time in degrees.

        Args:
            solar_dec: Solar declination in radians.
            depression: Depression in radians.
        """
        hour_angle_arg = math.degrees(math.acos(
            math.cos(self.PI / 2 + depression) /
            (math.cos(self._latitude) * math.cos(solar_dec)) -
            math.tan(self._latitude) * math.tan(solar_dec)
        ))

        return hour_angle_arg

    def _calculate_solar_time(self, hour, eq_of_time, is_solar_time):
        """Calculate Solar time for an hour."""
        if is_solar_time:
            return hour

        return ((hour * 60 + eq_of_time + 4 * math.degrees(self._longitude) -
                 60 * self.time_zone) % 1440) / 60

    def _calculate_solar_time_by_doy(self, hour, doy):
        """This is how radiance calculates solar time.

        This is a place holder and should be validated against _calculate_solar_time.
        """
        raise NotImplementedError()
        return (0.170 * math.sin((4 * self.PI / 373) * (doy - 80)) -
                0.129 * math.sin((2 * self.PI / 355) * (doy - 8)) +
                12 * (-(15 * self.time_zone) - self.longitude) / self.PI)

    @staticmethod
    def _calculate_hour_and_minute(float_hour):
        """Calculate hour and minutes as integers from a float hour."""
        hour = int(float_hour)
        minute = int(round((float_hour - int(float_hour)) * 60))

        if minute >= 60:
            return hour + 1, minute - 60
        else:
            return hour, minute

    @staticmethod
    def _days_from_010119(year, month, day):
        """Calculate the number of days from 01-01-1900 to the provided date.

        Args:
            year: Integer. The year in the date
            month: Integer. The month in the date
            day: Integer. The day in the date

        Returns:
            The number of days since 01-01-1900 to the provided date
        """
        def is_leap_year(year):
            """Determine whether a year is a leap year over the past centuries."""
            return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

        if year == 2017:  # fast check for the most common year used in ladybug
            days_in_preceding_years = 42734
        elif year == 2016:  # fast check for the 2nd most common year in ladybug
            days_in_preceding_years = 42368
        else:  # compute the number of days using math to figure out leap years
            years = range(1900, year)  # list of years from 1900
            # Number of days in a year are 366 if it is a leap year
            days_in_year = []
            for item in years:
                if is_leap_year(item):
                    days_in_year.append(366)
                else:
                    days_in_year.append(365)
            # Making the total of all the days in preceding years
            days_in_preceding_years = 0
            for days in days_in_year:
                days_in_preceding_years += days

        # get the total of all the days in preceding months in the same year
        month_array = AnalysisPeriod.NUMOFDAYSEACHMONTHLEAP if is_leap_year(year) \
            else AnalysisPeriod.NUMOFDAYSEACHMONTH
        days_in_preceding_months = 0
        for i in range(month - 1):
            days_in_preceding_months += month_array[i]

        return days_in_preceding_years + days_in_preceding_months + day + 1

    @staticmethod
    def _project_polyline_to_2d(plines_3d, projection, radius, origin_3d):
        """Project an array of Polyline3D into 2D space.

        Args:
            plines_3d: An array of Polyline3D to be projected to 2D space.
            projection: Text for the name of the projection to use from the sky
                dome hemisphere to the 2D plane. Choose from the following:

                * Orthographic
                * Stereographic

            origin_3d: Point3D for the origin around which projection will occur.
        """
        plines_2d = []
        if projection.title() == 'Orthographic':
            for pl in plines_3d:
                pts = [Compass.point3d_to_orthographic(pt) for pt in pl.vertices]
                plines_2d.append(Polyline2D(pts, True))
        elif projection.title() == 'Stereographic':
            for pline in plines_3d:
                pts = [Compass.point3d_to_stereographic(pt, radius, origin_3d)
                       for pt in pline.vertices]
                plines_2d.append(Polyline2D(pts, True))
        else:
            raise ValueError('Projection "{}" is not supported.'.format(projection))
        return plines_2d

    def __repr__(self):
        """Sunpath representation."""
        return "Sunpath (lat:{}, lon:{}, time zone:{})".format(
            self.latitude, self.longitude, self.time_zone)


class Sun(object):
    """An object representing a single Sun.

    Args:
        datetime: A DateTime that represents the datetime for this sun_vector
        altitude: Solar Altitude in degrees.
        azimuth: Solar Azimuth in degrees.
        is_solar_time: Boolean indicating if the datetime represents a solar time.
        is_daylight_saving: A Boolean indicating if the datetime is calculated
            for a daylight saving period
        north_angle: North angle of the sunpath in degrees. This is only used to
            adjust the sun_vector and does not affect the sun altitude or azimuth.

    Properties:
        * datetime
        * north_angle
        * hoy
        * altitude
        * azimuth
        * altitude_in_radians
        * azimuth_in_radians
        * is_solar_time
        * is_daylight_saving
        * data
        * is_during_day
        * sun_vector
        * sun_vector_reversed
    """

    __slots__ = ('_datetime', '_altitude', '_azimuth', '_is_solar_time',
                 '_is_daylight_saving', '_north_angle', '_data',
                 '_sun_vector', '_sun_vector_reversed')
    PI = math.pi

    def __init__(self, datetime, altitude, azimuth, is_solar_time,
                 is_daylight_saving, north_angle, data=None):
        """Init sun."""
        assert isinstance(datetime, py_datetime.datetime), \
            'datetime must be a DateTime (not {})'.format(type(datetime))
        self._datetime = datetime  # read-only

        assert -90 <= altitude <= 90, \
            'altitude({}) must be between {} and {}.' \
            .format(altitude, -self.PI, self.PI)
        self._altitude = altitude  # read-only

        assert -360 <= azimuth <= 360, \
            'azimuth({}) should be between {} and {}.' \
            .format(azimuth, -self.PI, self.PI)
        self._azimuth = azimuth  # read-only

        self._is_solar_time = is_solar_time
        self._is_daylight_saving = is_daylight_saving
        self._north_angle = north_angle
        self.data = data  # place holder for metadata

        self._sun_vector, self._sun_vector_reversed = self._calculate_sun_vector()

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
        return self._altitude

    @property
    def azimuth(self):
        """Return solar azimuth in degrees.

        This value is the same regardless of what the north_angle is.
        """
        return self._azimuth

    @property
    def azimuth_from_y_axis(self):
        """Return solar azimuth in degrees with respect to the Y-axis of the scene.

        This value will change as the north_angle is changed.
        """
        angle = self._azimuth - self._north_angle
        if angle > 360:
            return angle - 360
        elif angle < 0:
            return angle + 360
        return angle

    @property
    def altitude_in_radians(self):
        """Return solar altitude in radians."""
        return math.radians(self._altitude)

    @property
    def azimuth_in_radians(self):
        """Return solar azimuth in radians."""
        return math.radians(self._azimuth)

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
        """Get or set metadata to this sun position.

        No particular data type is enforced for this metadata but a dictionary
        is recommended so that it can be extended for multiple properties.
        """
        return self._data

    @data.setter
    def data(self, d):
        self._data = d

    @property
    def is_during_day(self):
        """Boolean to note if this sun position is during day."""
        # sun vector is flipped to look to the center
        return self.sun_vector.z <= 0

    @property
    def sun_vector(self):
        """A ladybug_geometry Vector3D representing the vector for this sun.

        Note that daytime sun vectors point downward (z will be negative).
        """
        return self._sun_vector

    @property
    def sun_vector_reversed(self):
        """A ladybug_geometry Vector3D representing the reversed vector for this sun.

        Daytime sun_vector_reversed point upward (z will be positive).
        """
        return self._sun_vector_reversed

    def position_3d(self, origin=Point3D(), radius=100):
        """Get a Point3D for the position of this sun on a sunpath.

        Args:
            origin: A ladybug_geometry Point3D to note the center of the sun path.
            radius: A number to note the radius of the sunpath.

        Returns:
            A Point3D for the position of this sun on a sunpath.
        """
        return Point3D(self.sun_vector_reversed.x * radius + origin.x,
                       self.sun_vector_reversed.y * radius + origin.y,
                       self.sun_vector_reversed.z * radius + origin.z)

    def position_2d(self, projection='Orthographic', origin=Point2D(), radius=100):
        """Get a Point2D for the position of this sun on a sunpath.

        Args:
            projection: Text for the name of the projection to use from the sky
                dome hemisphere to the 2D plane. (Default: 'Orthographic'). Choose
                from the following:

                * Orthographic
                * Stereographic

            origin: A ladybug_geometry Point2D to note the center of the sun path.
            radius: A number to note the radius of the sunpath.

        Returns:
            A Point2D for the position of this sun on a sunpath.
        """
        o_3d = Point3D(origin.x, origin.y, 0)
        if projection.title() == 'Orthographic':
            return Compass.point3d_to_orthographic(self.position_3d(o_3d, radius))
        elif projection.title() == 'Stereographic':
            return Compass.point3d_to_stereographic(
                self.position_3d(o_3d, radius), radius, o_3d)
        else:
            raise ValueError('Projection "{}" is not supported.'.format(projection))

    def _calculate_sun_vector(self):
        """Calculate sun vector for this sun."""
        x_axis = Vector3D(1., 0., 0.)
        north_vector = Vector3D(0., 1., 0.)

        # rotate north vector based on azimuth, altitude, and north
        _sun_vector_reversed = north_vector \
            .rotate(x_axis, self.altitude_in_radians) \
            .rotate_xy(-self.azimuth_in_radians)
        if self.north_angle != 0:
            _sun_vector_reversed = _sun_vector_reversed.rotate_xy(
                math.radians(self.north_angle))

        # reverse the vector
        _sun_vector = _sun_vector_reversed.reverse()
        return _sun_vector, _sun_vector_reversed

    def ToString(self):
        """Overwrite .NET ToString method."""
        return self.__repr__()

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.datetime, self.altitude, self.azimuth, self.is_solar_time,
                self.is_daylight_saving, self.north_angle)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, Sun) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        """Sun representation."""
        return "Sun at {} (x:{}, y:{}, z:{})".format(
            self.datetime,
            self.sun_vector.x,
            self.sun_vector.y,
            self.sun_vector.z
        )
