# coding=utf-8
from __future__ import division

from .epw import EPW
from .stat import STAT
from .location import Location
from .dt import DateTime
from .header import Header
from .datacollection import HourlyContinuousCollection
from .analysisperiod import AnalysisPeriod
from .sunpath import Sunpath
from .futil import write_to_file

from .datatype.energyflux import Irradiance, GlobalHorizontalIrradiance, \
    DirectNormalIrradiance, DiffuseHorizontalIrradiance, DirectHorizontalIrradiance
from .datatype.illuminance import GlobalHorizontalIlluminance, \
    DirectNormalIlluminance, DiffuseHorizontalIlluminance
from .datatype.luminance import ZenithLuminance

from .skymodel import ashrae_revised_clear_sky, ashrae_clear_sky, \
    zhang_huang_solar_split, estimate_illuminance_from_irradiance

from ladybug_geometry.geometry3d.pointvector import Vector3D

import math
import os
import warnings

try:  # python 2
    from itertools import izip as zip
    readmode = 'rb'
    writemode = 'wb'
except ImportError:  # python 3
    xrange = range
    readmode = 'r'
    writemode = 'w'
    xrange = range


class Wea(object):
    """An annual WEA object containing solar irradiance.

    Args:
        location: Ladybug location object.
        direct_normal_irradiance: An annual data collection of direct normal irradiance
            values for every timestep of the year.
        diffuse_horizontal_irradiance: An annual data collection of diffuse horizontal
            irradiance values for every timestep of the year.
        timestep: An integer to set the number of time steps per hour.
            Default is 1 for one value per hour.
        is_leap_year: A boolean to indicate if values are representing a leap year.
            Default: False.

    Properties:
        * datetimes
        * direct_normal_irradiance
        * diffuse_horizontal_irradiance
        * direct_horizontal_irradiance
        * global_horizontal_irradiance
        * header
        * hoys
        * timestep
        * is_leap_year
    """

    def __init__(self, location, direct_normal_irradiance,
                 diffuse_horizontal_irradiance, timestep=1, is_leap_year=False):
        """Create a wea object."""
        timestep = timestep or 1
        self._timestep = timestep
        self._is_leap_year = is_leap_year
        assert isinstance(timestep, int), 'timestep must be an' \
            ' integer. Got {}'.format(type(timestep))

        self.location = location
        self.direct_normal_irradiance = direct_normal_irradiance
        self.diffuse_horizontal_irradiance = diffuse_horizontal_irradiance
        self.metadata = {'source': location.source, 'country': location.country,
                         'city': location.city}

    @classmethod
    def from_values(cls, location, direct_normal_irradiance,
                    diffuse_horizontal_irradiance, timestep=1, is_leap_year=False):
        """Create wea from a list of irradiance values.

        This method converts input lists to data collection.
        """
        err_message = 'For timestep %d, %d number of data for %s is expected. ' \
            '%d is provided.'
        if len(direct_normal_irradiance) % cls.hour_count(is_leap_year) == 0:
            # add extra information to err_message
            err_message = err_message + ' Did you forget to set the timestep to %d?' \
                % (len(direct_normal_irradiance) / cls.hour_count(is_leap_year))

        assert len(direct_normal_irradiance) / \
            timestep == cls.hour_count(is_leap_year), \
            err_message % (timestep, timestep * cls.hour_count(is_leap_year),
                           'direct normal irradiance', len(
                               direct_normal_irradiance))

        assert len(diffuse_horizontal_irradiance) / timestep == \
            cls.hour_count(is_leap_year), \
            err_message % (timestep, timestep * cls.hour_count(is_leap_year),
                           'diffuse_horizontal_irradiance', len(
                               direct_normal_irradiance))

        metadata = {'source': location.source, 'country': location.country,
                    'city': location.city}
        dnr, dhr = cls._get_data_collections(
            direct_normal_irradiance, diffuse_horizontal_irradiance,
            metadata, timestep, is_leap_year)
        return cls(location, dnr, dhr, timestep, is_leap_year)

    @classmethod
    def from_dict(cls, data):
        """ Create Wea from a dictionary

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "location": {},  # ladybug location schema
            "direct_normal_irradiance": [],  # List of hourly direct normal
                                             # irradiance data points
            "diffuse_horizontal_irradiance": [],  # List of hourly diffuse
                                                  # horizontal irradiance data points
            "timestep": 1.0  # timestep between measurements, default is 1
            }
        """
        required_keys = ('location', 'direct_normal_irradiance',
                         'diffuse_horizontal_irradiance')
        optional_keys = ('timestep', 'is_leap_year')

        for key in required_keys:
            assert key in data, 'Required key "{}" is missing!'.format(key)

        for key in optional_keys:
            if key not in data:
                data[key] = None

        location = Location.from_dict(data['location'])
        direct_normal_irradiance = \
            HourlyContinuousCollection.from_dict(data['direct_normal_irradiance'])
        diffuse_horizontal_irradiance = \
            HourlyContinuousCollection.from_dict(data['diffuse_horizontal_irradiance'])
        timestep = data['timestep']
        is_leap_year = data['is_leap_year']

        return cls(location, direct_normal_irradiance,
                   diffuse_horizontal_irradiance, timestep, is_leap_year)

    @classmethod
    def from_file(cls, wea_file, timestep=1, is_leap_year=False):
        """Create wea object from a wea file.

        Args:
            wea_file:Full path to wea file.
            timestep: An optional integer to set the number of time steps per hour.
                Default is 1 for one value per hour. If the wea file has a time step
                smaller than an hour adjust this input accordingly.
            is_leap_year: A boolean to indicate if values are representing a leap year.
                Default: False.
        """
        assert os.path.isfile(wea_file), 'Failed to find {}'.format(wea_file)
        location = Location()
        with open(wea_file, readmode) as weaf:
            first_line = weaf.readline()
            assert first_line.startswith('place'), \
                'Failed to find place in header. ' \
                '{} is not a valid wea file.'.format(wea_file)
            location.city = ' '.join(first_line.split()[1:])
            # parse header
            location.latitude = float(weaf.readline().split()[-1])
            location.longitude = -float(weaf.readline().split()[-1])
            location.time_zone = -int(weaf.readline().split()[-1]) / 15
            location.elevation = float(weaf.readline().split()[-1])
            weaf.readline()  # pass line for weather data units

            # parse irradiance values
            direct_normal_irradiance = []
            diffuse_horizontal_irradiance = []
            for line in weaf:
                dirn, difh = [int(v) for v in line.split()[-2:]]
                direct_normal_irradiance.append(dirn)
                diffuse_horizontal_irradiance.append(difh)

        return cls.from_values(location, direct_normal_irradiance,
                               diffuse_horizontal_irradiance, timestep, is_leap_year)

    @classmethod
    def from_epw_file(cls, epw_file, timestep=1):
        """Create a wea object using the solar irradiance values in an epw file.

        Args:
            epw_file: Full path to epw weather file.
            timestep: An optional integer to set the number of time steps per hour.
                Default is 1 for one value per hour. Note that this input
                will only do a linear interpolation over the data in the EPW
                file.  While such linear interpolations are suitable for most
                thermal simulations, where thermal lag "smooths over" the effect
                of momentary increases in solar energy, it is not recommended
                for daylight simulations, where momentary increases in solar
                energy can mean the difference between glare and visual comfort.
        """
        is_leap_year = False  # epw file is always for 8760 hours

        epw = EPW(epw_file)
        direct_normal, diffuse_horizontal = \
            cls._get_data_collections(epw.direct_normal_radiation.values,
                                      epw.diffuse_horizontal_radiation.values,
                                      epw.metadata, 1, is_leap_year)
        if timestep != 1:
            warnings.warn("Note: timesteps greater than 1 on epw-generated Wea's \n"
                "are suitable for thermal models but are not recommended \n"
                "for daylight models.")
            # interpolate the data
            direct_normal = direct_normal.interpolate_to_timestep(timestep)
            diffuse_horizontal = diffuse_horizontal.interpolate_to_timestep(timestep)
            # create sunpath to check if the sun is up at a given timestep
            sp = Sunpath.from_location(epw.location)
            # add correct values to the emply data collection
            for i, dt in enumerate(cls._get_datetimes(timestep, is_leap_year)):
                # set irradiance values to 0 when the sun is not up
                sun = sp.calculate_sun_from_date_time(dt)
                if sun.altitude < 0:
                    direct_normal[i] = 0
                    diffuse_horizontal[i] = 0

        return cls(epw.location, direct_normal, diffuse_horizontal,
                   timestep, is_leap_year)

    @classmethod
    def from_stat_file(cls, statfile, timestep=1, is_leap_year=False):
        """Create an ASHRAE Revised Clear Sky wea object from the monthly sky
        optical depths in a .stat file.

        Args:
            statfile: Full path to the .stat file.
            timestep: An optional integer to set the number of time steps per
                hour. Default is 1 for one value per hour.
            is_leap_year: A boolean to indicate if values are representing a leap year.
                Default: False.
        """
        stat = STAT(statfile)

        # check to be sure the stat file does not have missing tau values
        def check_missing(opt_data, data_name):
            if opt_data == []:
                raise ValueError('Stat file contains no optical data.')
            for i, x in enumerate(opt_data):
                if x is None:
                    raise ValueError(
                        'Missing optical depth data for {} at month {}'.format(
                            data_name, i)
                    )
        check_missing(stat.monthly_tau_beam, 'monthly_tau_beam')
        check_missing(stat.monthly_tau_diffuse, 'monthly_tau_diffuse')

        return cls.from_ashrae_revised_clear_sky(stat.location, stat.monthly_tau_beam,
                                                 stat.monthly_tau_diffuse, timestep,
                                                 is_leap_year)

    @classmethod
    def from_ashrae_revised_clear_sky(cls, location, monthly_tau_beam,
                                      monthly_tau_diffuse, timestep=1,
                                      is_leap_year=False):
        """Create a wea object representing an ASHRAE Revised Clear Sky ("Tau Model")

        ASHRAE Revised Clear Skies are intended to determine peak solar load
        and sizing parmeters for HVAC systems.  The revised clear sky is
        currently the default recommended sky model used to autosize HVAC
        systems in EnergyPlus. For more information on the ASHRAE Revised Clear
        Sky model, see the EnergyPlus Engineering Reference:
        https://bigladdersoftware.com/epx/docs/8-9/engineering-reference/climate-calculations.html

        Args:
            location: Ladybug location object.
            monthly_tau_beam: A list of 12 float values indicating the beam
                optical depth of the sky at each month of the year.
            monthly_tau_diffuse: A list of 12 float values indicating the
                diffuse optical depth of the sky at each month of the year.
            timestep: An optional integer to set the number of time steps per
                hour. Default is 1 for one value per hour.
            is_leap_year: A boolean to indicate if values are representing a leap year.
                Default: False.
        """
        # extract metadata
        metadata = {'source': location.source, 'country': location.country,
                    'city': location.city}

        # create sunpath and get altitude at every timestep of the year
        sp = Sunpath.from_location(location)
        sp.is_leap_year = is_leap_year
        altitudes = [[] for i in range(12)]
        dates = cls._get_datetimes(timestep, is_leap_year)
        for t_date in dates:
            sun = sp.calculate_sun_from_date_time(t_date)
            altitudes[sun.datetime.month - 1].append(sun.altitude)

        # run all of the months through the ashrae_revised_clear_sky model
        direct_norm, diffuse_horiz = [], []
        for i_mon, alt_list in enumerate(altitudes):
            dir_norm_rad, dif_horiz_rad = ashrae_revised_clear_sky(
                alt_list, monthly_tau_beam[i_mon], monthly_tau_diffuse[i_mon])
            direct_norm.extend(dir_norm_rad)
            diffuse_horiz.extend(dif_horiz_rad)

        direct_norm_rad, diffuse_horiz_rad = \
            cls._get_data_collections(direct_norm, diffuse_horiz,
                                      metadata, timestep, is_leap_year)

        return cls(location, direct_norm_rad, diffuse_horiz_rad, timestep, is_leap_year)

    @classmethod
    def from_ashrae_clear_sky(cls, location, sky_clearness=1, timestep=1,
                              is_leap_year=False):
        """Create a wea object representing an original ASHRAE Clear Sky.

        The original ASHRAE Clear Sky is intended to determine peak solar load
        and sizing parmeters for HVAC systems.  It is not the sky model
        currently recommended by ASHRAE since it usually overestimates the
        amount of solar irradiance in comparison to the newer ASHRAE Revised
        Clear Sky ("Tau Model"). However, the original model here is still
        useful for cases where monthly optical depth values are not known. For
        more information on the ASHRAE Clear Sky model, see the EnergyPlus
        Engineering Reference:
        https://bigladdersoftware.com/epx/docs/8-9/engineering-reference/climate-calculations.html

        Args:
            location: Ladybug location object.
            sky_clearness: A factor that will be multiplied by the output of
                the model. This is to help account for locations where clear,
                dry skies predominate (e.g., at high elevations) or,
                conversely, where hazy and humid conditions are frequent. See
                Threlkeld and Jordan (1958) for recommended values. Typical
                values range from 0.95 to 1.05 and are usually never more
                than 1.2. Default is set to 1.0.
            timestep: An optional integer to set the number of time steps per
                hour. Default is 1 for one value per hour.
            is_leap_year: A boolean to indicate if values are representing a leap year.
                Default: False.
        """
        # extract metadata
        metadata = {'source': location.source, 'country': location.country,
                    'city': location.city}

        # create sunpath and get altitude at every timestep of the year
        sp = Sunpath.from_location(location)
        sp.is_leap_year = is_leap_year
        altitudes = [[] for i in range(12)]
        dates = cls._get_datetimes(timestep, is_leap_year)
        for t_date in dates:
            sun = sp.calculate_sun_from_date_time(t_date)
            altitudes[sun.datetime.month - 1].append(sun.altitude)

        # compute hourly direct normal and diffuse horizontal irradiance
        direct_norm, diffuse_horiz = [], []
        for i_mon, alt_list in enumerate(altitudes):
            dir_norm_rad, dif_horiz_rad = ashrae_clear_sky(
                alt_list, i_mon + 1, sky_clearness)
            direct_norm.extend(dir_norm_rad)
            diffuse_horiz.extend(dif_horiz_rad)

        direct_norm_rad, diffuse_horiz_rad = \
            cls._get_data_collections(direct_norm, diffuse_horiz,
                                      metadata, timestep, is_leap_year)

        return cls(location, direct_norm_rad, diffuse_horiz_rad, timestep, is_leap_year)

    @classmethod
    def from_zhang_huang_solar(cls, location, cloud_cover,
                               relative_humidity, dry_bulb_temperature,
                               wind_speed, atmospheric_pressure=None,
                               timestep=1, is_leap_year=False, use_disc=False):
        """Create a wea object from climate data using the Zhang-Huang model.

        The Zhang-Huang solar model was developed to estimate solar
        irradiance for weather stations that lack such values, which are
        typically colleted with a pyranometer. Using total cloud cover,
        dry-bulb temperature, relative humidity, and wind speed as
        inputs the Zhang-Huang estimates global horizontal irradiance
        by means of a regression model across these variables.
        For more information on the Zhang-Huang model, see the
        EnergyPlus Engineering Reference:
        https://bigladdersoftware.com/epx/docs/8-7/engineering-reference/climate-calculations.html#zhang-huang-solar-model

        Args:
            location: Ladybug location object.
            cloud_cover: A list of annual float values between 0 and 1
                that represent the fraction of the sky dome covered
                in clouds (0 = clear; 1 = completely overcast)
            relative_humidity: A list of annual float values between
                0 and 100 that represent the relative humidity in percent.
            dry_bulb_temperature: A list of annual float values that
                represent the dry bulb temperature in degrees Celsius.
            wind_speed: A list of annual float values that
                represent the wind speed in meters per second.
            atmospheric_pressure: An optional list of float values that
                represent the atmospheric pressure in Pa.  If None or
                left blank, pressure at sea level will be used (101325 Pa).
            timestep: An optional integer to set the number of time steps per
                hour. Default is 1 for one value per hour.
            is_leap_year: A boolean to indicate if values are representing a leap year.
                Default: False.
            use_disc: Set to True to use the original DISC model as opposed to the
                newer and more accurate DIRINT model. Default: False.
        """
        # check input data
        assert len(cloud_cover) == len(relative_humidity) == \
            len(dry_bulb_temperature) == len(wind_speed), \
            'lengths of input climate data must match.'
        assert len(cloud_cover) / timestep == cls.hour_count(is_leap_year), \
            'input climate data must be annual.'
        assert isinstance(timestep, int), 'timestep must be an' \
            ' integer. Got {}'.format(type(timestep))
        if atmospheric_pressure is not None:
            assert len(atmospheric_pressure) == len(cloud_cover), \
                'length pf atmospheric_pressure must match the other input lists.'
        else:
            atmospheric_pressure = [101325] * cls.hour_count(is_leap_year) * timestep

        # initiate sunpath based on location
        sp = Sunpath.from_location(location)
        sp.is_leap_year = is_leap_year

        # calculate parameters needed for zhang-huang irradiance
        date_times = []
        altitudes = []
        doys = []
        dry_bulb_t3_hrs = []
        for count, t_date in enumerate(cls._get_datetimes(timestep, is_leap_year)):
            date_times.append(t_date)
            sun = sp.calculate_sun_from_date_time(t_date)
            altitudes.append(sun.altitude)
            doys.append(sun.datetime.doy)
            dry_bulb_t3_hrs.append(dry_bulb_temperature[count - (3 * timestep)])

        # calculate zhang-huang irradiance
        dir_ir, diff_ir = zhang_huang_solar_split(altitudes, doys, cloud_cover,
                                                  relative_humidity,
                                                  dry_bulb_temperature,
                                                  dry_bulb_t3_hrs, wind_speed,
                                                  atmospheric_pressure, use_disc)

        # assemble the results into DataCollections
        metadata = {'source': location.source, 'country': location.country,
                    'city': location.city}
        direct_norm_rad, diffuse_horiz_rad = \
            cls._get_data_collections(dir_ir, diff_ir, metadata, timestep, is_leap_year)

        return cls(location, direct_norm_rad, diffuse_horiz_rad, timestep, is_leap_year)

    @property
    def header(self):
        """Wea header."""
        return "place %s\n" % self.location.city + \
            "latitude %.2f\n" % self.location.latitude + \
            "longitude %.2f\n" % -self.location.longitude + \
            "time_zone %d\n" % (-self.location.time_zone * 15) + \
            "site_elevation %.1f\n" % self.location.elevation + \
            "weather_data_file_units 1\n"

    @property
    def hoys(self):
        """Hours of the year in wea file."""
        return tuple(dt.hoy for dt in self.datetimes)

    @property
    def datetimes(self):
        """Datetimes in wea file."""
        if self.timestep == 1:
            return tuple(dt.add_minute(30) for dt in
                         self.direct_normal_irradiance.datetimes)
        else:
            return self.direct_normal_irradiance.datetimes

    @property
    def timestep(self):
        """Return the timestep."""
        return self._timestep

    @property
    def direct_normal_irradiance(self):
        """Get or set the direct normal irradiance."""
        return self._direct_normal_irradiance

    @direct_normal_irradiance.setter
    def direct_normal_irradiance(self, data):
        assert isinstance(data, HourlyContinuousCollection), \
            'direct_normal_irradiance data must be an ' \
            'HourlyContinuousCollection. Got {}'.format(type(data))
        assert len(data) / self.timestep == self.hour_count(self.is_leap_year), \
            'direct_normal_irradiance data must be annual.'
        assert isinstance(data.header.data_type, DirectNormalIrradiance), \
            'direct_normal_irradiance data type must be' \
            'DirectNormalIrradiance. Got {}'.format(type(data.header.data_type))
        self._direct_normal_irradiance = data

    @property
    def diffuse_horizontal_irradiance(self):
        """Get or set the diffuse horizontal irradiance."""
        return self._diffuse_horizontal_irradiance

    @diffuse_horizontal_irradiance.setter
    def diffuse_horizontal_irradiance(self, data):
        assert isinstance(data, HourlyContinuousCollection), \
            'diffuse_horizontal_irradiance data must be an ' \
            'HourlyContinuousCollection. Got {}'.format(type(data))
        assert len(data) / self.timestep == self.hour_count(self.is_leap_year), \
            'diffuse_horizontal_irradiance data must be annual.'
        assert isinstance(data.header.data_type, DiffuseHorizontalIrradiance), \
            'direct_normal_irradiance data type must be' \
            'DiffuseHorizontalIrradiance. Got {}'.format(type(data.header.data_type))
        self._diffuse_horizontal_irradiance = data

    @property
    def global_horizontal_irradiance(self):
        """Returns the global horizontal irradiance at each timestep."""
        analysis_period = AnalysisPeriod(timestep=self.timestep,
                                         is_leap_year=self.is_leap_year)
        header_ghr = Header(data_type=GlobalHorizontalIrradiance(),
                            unit='W/m2',
                            analysis_period=analysis_period,
                            metadata=self.metadata)
        glob_horiz = []
        sp = Sunpath.from_location(self.location)
        sp.is_leap_year = self.is_leap_year
        for dt, dnr, dhr in zip(self.datetimes, self.direct_normal_irradiance,
                                self.diffuse_horizontal_irradiance):
            sun = sp.calculate_sun_from_date_time(dt)
            glob_horiz.append(dhr + dnr * math.sin(math.radians(sun.altitude)))
        return HourlyContinuousCollection(header_ghr, glob_horiz)

    @property
    def direct_horizontal_irradiance(self):
        """Returns the direct irradiance on a horizontal surface at each timestep.

        Note that this is different from the direct_normal_irradiance needed
        to construct a Wea, which is NORMAL and not HORIZONTAL."""
        analysis_period = AnalysisPeriod(timestep=self.timestep,
                                         is_leap_year=self.is_leap_year)
        header_dhr = Header(data_type=DirectHorizontalIrradiance(),
                            unit='W/m2',
                            analysis_period=analysis_period,
                            metadata=self.metadata)
        direct_horiz = []
        sp = Sunpath.from_location(self.location)
        sp.is_leap_year = self.is_leap_year
        for dt, dnr in zip(self.datetimes, self.direct_normal_irradiance):
            sun = sp.calculate_sun_from_date_time(dt)
            direct_horiz.append(dnr * math.sin(math.radians(sun.altitude)))
        return HourlyContinuousCollection(header_dhr, direct_horiz)

    @property
    def is_leap_year(self):
        """Return the timestep."""
        return self._is_leap_year

    @staticmethod
    def hour_count(is_leap_year):
        """Number of hours in this Wea file.

        Keep in mind that wea file is an annual file but this value will be different
        for a leap year
        """
        return 8760 + 24 if is_leap_year else 8760

    def get_irradiance_value(self, month, day, hour):
        """Get direct and diffuse irradiance values for a point in time."""
        dt = DateTime(month, day, hour, leap_year=self.is_leap_year)
        count = int(dt.hoy * self.timestep)
        return self.direct_normal_irradiance[count], \
            self.diffuse_horizontal_irradiance[count]

    def get_irradiance_value_for_hoy(self, hoy):
        """Get direct and diffuse irradiance values for an hoy."""
        count = int(hoy * self.timestep)
        return self.direct_normal_irradiance[count], \
            self.diffuse_horizontal_irradiance[count]

    def directional_irradiance(self, altitude=90, azimuth=180,
                               ground_reflectance=0.2, isotrophic=True):
        """Returns the irradiance components facing a given altitude and azimuth.

        This method computes unobstructed solar flux facing a given
        altitude and azimuth. The default is set to return the global horizontal
        irradiance, assuming an altitude facing straight up (90 degrees).

        Args:
            altitude: A number between -90 and 90 that represents the
                altitude at which irradiance is being evaluated in degrees.
            azimuth: A number between 0 and 360 that represents the
                azimuth at which irradiance is being evaluated in degrees.
            ground_reflectance: A number between 0 and 1 that represents the
                reflectance of the ground. Default is set to 0.2. Some
                common ground reflectances are:
                *   urban: 0.18
                *   grass: 0.20
                *   fresh grass: 0.26
                *   soil: 0.17
                *   sand: 0.40
                *   snow: 0.65
                *   fresh_snow: 0.75
                *   asphalt: 0.12
                *   concrete: 0.30
                *   sea: 0.06
            isotrophic: A boolean value that sets whether an isotropic sky is
                used (as opposed to an anisotropic sky). An isotrophic sky
                assumes an even distribution of diffuse irradiance across the
                sky while an anisotropic sky places more diffuse irradiance
                near the solar disc. Default is set to True for isotrophic

        Returns:
            A tuple of four elements

            -   total_irradiance: A data collection of total solar irradiance.

            -   direct_irradiance: A data collection of direct solar irradiance.

            -   diffuse_irradiance: A data collection of diffuse sky solar irradiance.

            -   reflected_irradiance: A data collection of ground reflected solar
                irradiance.
        """
        # function to convert polar coordinates to xyz.
        def pol2cart(phi, theta):
            mult = math.cos(theta)
            x = math.sin(phi) * mult
            y = math.cos(phi) * mult
            z = math.sin(theta)
            return Vector3D(x, y, z)

        # convert the altitude and azimuth to a normal vector
        normal = pol2cart(math.radians(azimuth), math.radians(altitude))

        # create sunpath and get altitude at every timestep of the year
        direct_irr, diffuse_irr, reflected_irr, total_irr = [], [], [], []
        sp = Sunpath.from_location(self.location)
        sp.is_leap_year = self.is_leap_year
        for dt, dnr, dhr in zip(self.datetimes, self.direct_normal_irradiance,
                                self.diffuse_horizontal_irradiance):
            sun = sp.calculate_sun_from_date_time(dt)
            sun_vec = pol2cart(math.radians(sun.azimuth),
                               math.radians(sun.altitude))
            vec_angle = sun_vec.angle(normal)

            # direct irradiance on surface
            srf_dir = 0
            if sun.altitude > 0 and vec_angle < math.pi / 2:
                srf_dir = dnr * math.cos(vec_angle)

            # diffuse irradiance on surface
            if isotrophic:
                srf_dif = dhr * ((math.sin(math.radians(altitude)) / 2) + 0.5)
            else:
                y = max(0.45, 0.55 + (0.437 * math.cos(vec_angle)) + 0.313 *
                        math.cos(vec_angle) * 0.313 * math.cos(vec_angle))
                srf_dif = self.dhr * (y * (
                    math.sin(math.radians(abs(90 - altitude)))) +
                    math.cos(math.radians(abs(90 - altitude))))

            # reflected irradiance on surface.
            e_glob = dhr + dnr * math.cos(math.radians(90 - sun.altitude))
            srf_ref = e_glob * ground_reflectance * (0.5 - (math.sin(
                math.radians(altitude)) / 2))

            # add it all together
            direct_irr.append(srf_dir)
            diffuse_irr.append(srf_dif)
            reflected_irr.append(srf_ref)
            total_irr.append(srf_dir + srf_dif + srf_ref)

        # create the headers
        a_per = AnalysisPeriod(timestep=self.timestep, is_leap_year=self.is_leap_year)
        direct_hea = diffuse_hea = reflected_hea = total_hea = \
            Header(Irradiance(), 'W/m2', a_per, self.metadata)

        # create the data collections
        direct_irradiance = HourlyContinuousCollection(direct_hea, direct_irr)
        diffuse_irradiance = HourlyContinuousCollection(diffuse_hea, diffuse_irr)
        reflected_irradiance = HourlyContinuousCollection(reflected_hea, reflected_irr)
        total_irradiance = HourlyContinuousCollection(total_hea, total_irr)

        return total_irradiance, direct_irradiance, \
            diffuse_irradiance, reflected_irradiance

    def estimate_illuminance_components(self, dew_point):
        """Get estimated direct, diffuse, and global illuminance from this Wea.

        Note that this method should only be used when there are no measured
        illuminance values that correspond to this Wea's irradiance values.
        Because the illuminance components calculated here are simply estimated
        using a model by Perez [1], they are not as accurate as true measured values.

        Note:
            [1] Perez R. (1990). 'Modeling Daylight Availability and Irradiance
            Components from Direct and Global Irradiance'. Solar Energy.
            Vol. 44. No. 5, pp. 271-289. USA.

        Args:
            dew_point: An annual hourly data collection of dewpoint temperature
                in degrees C. The timestep of this data collection and the presence
                or lack of a leap year must align with this Wea.

        Returns:
            A tuple with four elements

            -   global_horiz_ill: Data collection of Global Horizontal Illuminance
                in lux.

            -   direct_normal_ill: Data collection of Direct Normal Illuminance in lux.

            -   diffuse_horizontal_ill: Data collection of  Diffuse Horizontal
                Illuminance in lux.

            -   zenith_lum: Data collection of Zenith Luminance in lux.
        """
        # check the dew_point input
        assert len(dew_point) == self.hour_count(self.is_leap_year) * self.timestep, \
            'Input dew_point data must be annual hourly and align with the irradiance' \
            ' on the Wea.'

        # calculate illuminance values
        sp = Sunpath.from_location(self.location)
        sp.is_leap_year = self.is_leap_year
        gh_ill_values, dn_ill_values, dh_ill_values, zen_lum_values = [], [], [], []
        for dt, dp, ghi, dni, dhi in zip(
                self.datetimes, dew_point, self.global_horizontal_irradiance,
                self.direct_normal_irradiance, self.diffuse_horizontal_irradiance):
            alt = sp.calculate_sun_from_date_time(dt).altitude
            gh, dn, dh, z = estimate_illuminance_from_irradiance(alt, ghi, dni, dhi, dp)
            gh_ill_values.append(gh)
            dn_ill_values.append(dn)
            dh_ill_values.append(dh)
            zen_lum_values.append(z)

        # create data collection headers for the results
        analysis_period = AnalysisPeriod(timestep=self.timestep,
                                         is_leap_year=self.is_leap_year)
        gh_ill_head = Header(data_type=GlobalHorizontalIlluminance(), unit='lux',
                             analysis_period=analysis_period, metadata=self.metadata)
        dn_ill_head = Header(data_type=DirectNormalIlluminance(), unit='lux',
                             analysis_period=analysis_period, metadata=self.metadata)
        dh_ill_head = Header(data_type=DiffuseHorizontalIlluminance(), unit='lux',
                             analysis_period=analysis_period, metadata=self.metadata)
        zen_lum_head = Header(data_type=ZenithLuminance(), unit='cd/m2',
                              analysis_period=analysis_period, metadata=self.metadata)

        # create data collections to hold illuminance results
        global_horiz_ill = HourlyContinuousCollection(gh_ill_head, gh_ill_values)
        direct_normal_ill = HourlyContinuousCollection(dn_ill_head, dn_ill_values)
        diffuse_horizontal_ill = HourlyContinuousCollection(dh_ill_head, dh_ill_values)
        zenith_lum = HourlyContinuousCollection(zen_lum_head, zen_lum_values)

        return global_horiz_ill, direct_normal_ill, diffuse_horizontal_ill, zenith_lum

    def to_dict(self):
        """Get the Wea as a dictionary."""
        return {
            'location': self.location.to_dict(),
            'direct_normal_irradiance':
                self.direct_normal_irradiance.to_dict(),
            'diffuse_horizontal_irradiance':
                self.diffuse_horizontal_irradiance.to_dict(),
            'timestep': self.timestep,
            'is_leap_year': self.is_leap_year,
            'type': 'Wea'
        }

    def write(self, file_path, hoys=None, write_hours=False):
        """Write the wea file.

        WEA carries irradiance values from epw and is what gendaymtx uses to
        generate the sky.
        """
        if not file_path.lower().endswith('.wea'):
            file_path += '.wea'
        is_leap_year = self.is_leap_year
        # generate hoys in wea file based on timestep
        full_wea = False
        if not hoys:
            hoys = self.hoys
            full_wea = True

        # write header
        lines = [self.header]
        if full_wea:
            # there is no user input for hoys, write it for all the hours
            for dir_rad, dif_rad, dt in zip(self.direct_normal_irradiance,
                                            self.diffuse_horizontal_irradiance,
                                            self.datetimes):
                line = "%d %d %.3f %d %d\n" \
                    % (dt.month, dt.day, dt.float_hour, dir_rad, dif_rad)
                lines.append(line)
        else:
            # output wea based on user request
            for hoy in hoys:
                try:
                    dir_rad, dif_rad = self.get_irradiance_value_for_hoy(hoy)
                except IndexError:
                    warnings.warn('Wea data for {} is not available!'.format(dt))
                    continue

                dt = DateTime.from_hoy(hoy, is_leap_year)
                dt = dt.add_minute(30) if self.timestep == 1 else dt
                line = "%d %d %.3f %d %d\n" \
                    % (dt.month, dt.day, dt.float_hour, dir_rad, dif_rad)

                lines.append(line)
        file_data = ''.join(lines)
        write_to_file(file_path, file_data, True)

        if write_hours:
            hrs_file_path = file_path[:-4] + '.hrs'
            hrs_data = ','.join(str(h) for h in hoys) + '\n'
            write_to_file(hrs_file_path, hrs_data, True)

        return file_path

    @staticmethod
    def _get_datetimes(timestep, is_leap_year):
        """List of datetimes based on timestep.

        This method should only be used for classmethods. For datetimes use datetiems or
        hoys methods.
        """
        hour_count = 8760 + 24 if is_leap_year else 8760
        adjust_time = 30 if timestep == 1 else 0
        return tuple(
            DateTime.from_moy(60.0 * count / timestep + adjust_time, is_leap_year)
            for count in xrange(hour_count * timestep)
        )

    @staticmethod
    def _get_data_collections(dnr_values, dhr_values, metadata, timestep, is_leap_year):
        """Return two data collections for Direct Normal, Diffuse Horizontal."""
        analysis_period = AnalysisPeriod(timestep=timestep, is_leap_year=is_leap_year)
        dnr_header = Header(data_type=DirectNormalIrradiance(),
                            unit='W/m2',
                            analysis_period=analysis_period,
                            metadata=metadata)
        direct_norm_rad = HourlyContinuousCollection(dnr_header, dnr_values)
        dhr_header = Header(data_type=DiffuseHorizontalIrradiance(),
                            unit='W/m2',
                            analysis_period=analysis_period,
                            metadata=metadata)
        diffuse_horiz_rad = HourlyContinuousCollection(dhr_header, dhr_values)

        return direct_norm_rad, diffuse_horiz_rad

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """epw file representation."""
        return "WEA [%s]" % self.location.city
