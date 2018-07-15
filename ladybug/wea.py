# coding=utf-8
"""Wea weather file."""
from .epw import EPW
from .stat import Stat
from .location import Location
from .dt import DateTime
from .header import Header
from .datacollection import DataCollection
from .datatype import DataPoint
from .analysisperiod import AnalysisPeriod
from .sunpath import Sunpath
from .euclid import Vector3

import math
try:
    from itertools import izip as zip
except ImportError:
    # python 3
    xrange = range


class Wea(object):
    """An annual WEA object containing solar radiation.

    Attributes:
        location: Ladybug location object.
        direct_normal_radiation: An annual DataCollection of direct normal radiation
            values.
        diffuse_horizontal_radiation: An annual DataCollection of diffuse horizontal
            radiation values for every hourly timestep of the year.
        timestep: An optional integer to set the number of time steps per hour.
            Default is 1 for one value per hour.
        is_leap_year: A boolean to indicate if values are representing a leap year.
            Default is False.
    """

    def __init__(self, location, direct_normal_radiation,
                 diffuse_horizontal_radiation, timestep=1, is_leap_year=False):
        """Create a wea object."""
        timestep = timestep or 1
        self._timestep = timestep
        self._is_leap_year = is_leap_year
        assert isinstance(timestep, int), 'timestep must be an' \
            ' integer. Got {}'.format(type(timestep))

        self.location = location
        self.direct_normal_radiation = direct_normal_radiation
        self.diffuse_horizontal_radiation = diffuse_horizontal_radiation

    @classmethod
    def from_values(cls, location, direct_normal_radiation,
                    diffuse_horizontal_radiation, timestep=1, is_leap_year=False):
        """Create wea from a list of radiation values.

        This method converts input lists to DataCollection.
        """
        dnr, dhr = cls._get_empty_data_collections(location, timestep, is_leap_year)
        dts = cls._get_datetimes(timestep, is_leap_year)
        for dir_norm, diff_horiz, dt in zip(direct_normal_radiation,
                                            diffuse_horizontal_radiation, dts):
            dnr.append(DataPoint(dir_norm, dt, 'SI', 'Direct Normal Radiation'))
            dhr.append(DataPoint(diff_horiz, dt, 'SI', 'Diffuse Horizontal Radiation'))
        return cls(location, direct_normal_radiation, diffuse_horizontal_radiation,
                   timestep, is_leap_year)

    @classmethod
    def from_json(cls, data):
        """ Create Wea from json file
            {
            "location": {} , // ladybug location schema
            "direct_normal_radiation": [], // List of hourly direct normal
                radiation data points
            "diffuse_horizontal_radiation": [], // List of hourly diffuse
                horizontal radiation data points
            "timestep": float //timestep between measurements, default is 1
            }
        """
        required_keys = ('location', 'direct_normal_radiation',
                         'diffuse_horizontal_radiation')
        optional_keys = ('timestep', 'is_leap_year')

        for key in required_keys:
            assert key in data, 'Required key "{}" is missing!'.format(key)

        for key in optional_keys:
            if key not in data:
                data[key] = None

        location = Location.from_json(data['location'])
        direct_normal_radiation = \
            DataCollection.from_json(data['direct_normal_radiation'])
        diffuse_horizontal_radiation = \
            DataCollection.from_json(data['diffuse_horizontal_radiation'])
        timestep = data['timestep']
        is_leap_year = data['is_leap_year']

        return cls(location, direct_normal_radiation,
                   diffuse_horizontal_radiation, timestep, is_leap_year)

    @classmethod
    def from_epw_file(cls, epwfile, timestep=1):
        """Create a wea object using the solar radiation values in an epw file.

        Args:
            epwfile: Full path to epw weather file.
            timestep: An optional integer to set the number of time steps per hour.
                Default is 1 for one value per hour. Note that this input
                will only do a linear interpolation over the data in the EPW
                file.  While such linear interpolations are suitable for most
                thermal simulations, where thermal lag "smooths over" the effect
                of momentary increases in solar energy, it is not recommended
                for daylight simulations, where momentary increases in solar
                energy can mean the difference between glare and visual comfort.
        """
        epw = EPW(epwfile)
        direct_normal = epw.direct_normal_radiation
        diffuse_horizontal = epw.diffuse_horizontal_radiation
        if timestep is not 1:
            print ("Note: timesteps greater than 1 on epw-generated Wea's \n" +
                   "are suitable for thermal models but are not recommended \n" +
                   "for daylight models.")
            direct_normal = direct_normal.interpolate_data(timestep, True)
            diffuse_horizontal = diffuse_horizontal.interpolate_data(timestep, True)
        else:
            # add half an hour to datetime to put sun in the middle of the hour
            for dnr in direct_normal:
                dnr.datetime = dnr.datetime.add_minute(30)
            for dhr in diffuse_horizontal:
                dhr.datetime = dhr.datetime.add_minute(30)

        # epw file is always for 8760 hours
        is_leap_year = False
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
                Default is False.
        """
        stat = Stat(statfile)

        # check to be sure the stat file does not have missing tau values
        def check_missing(opt_data, data_name):
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
                Default is False.
        """
        # create sunpath and get altitude at every timestep of the year
        sp = Sunpath.from_location(location)
        sp.is_leap_year = is_leap_year
        altitudes = []
        months = []
        dates = cls._get_datetimes(timestep, is_leap_year)
        for t_date in dates:
            sun = sp.calculate_sun_from_date_time(t_date)
            months.append(sun.datetime.month - 1)
            altitudes.append(sun.altitude)

        # calculate hourly air mass between top of the atmosphere and earth
        air_masses = []
        for alt in altitudes:
            air_mass = 0
            if alt > 0:
                air_mass = 1 / (math.sin(math.radians(alt)) +
                                (0.50572 * math.pow((6.07995 + alt), -1.6364)))
            air_masses.append(air_mass)

        # calculate monthly air mass exponents.
        beam_epxs = []
        diffuse_exps = []
        for count, tb in enumerate(monthly_tau_beam):
            td = monthly_tau_diffuse[count]
            ab = 1.219 - (0.043 * tb) - (0.151 * td) - (0.204 * tb * td)
            ad = 0.202 + (0.852 * tb) - (0.007 * td) - (0.357 * tb * td)
            beam_epxs.append(ab)
            diffuse_exps.append(ad)

        # compute the clear sky radiation values
        direct_norm_rad, diffuse_horiz_rad = \
            cls._get_empty_data_collections(location, timestep, is_leap_year)

        for i, air_mass in enumerate(air_masses):
            alt = altitudes[i]
            if alt > 0:
                m = months[i]
                e_beam = (1415 * math.exp(-monthly_tau_beam[m] * math.pow(
                    air_mass, beam_epxs[m]))) / timestep
                e_diff = (1415 * math.exp(-monthly_tau_diffuse[m] * math.pow(
                    air_mass, diffuse_exps[m]))) / timestep
                direct_norm_rad.append(
                    DataPoint(e_beam, dates[i], 'SI', 'Direct Normal Radiation'))
                diffuse_horiz_rad.append(
                    DataPoint(e_diff, dates[i], 'SI', 'Diffuse Horizontal Radiation'))
            else:
                direct_norm_rad.append(
                    DataPoint(0, dates[i], 'SI', 'Direct Normal Radiation'))
                diffuse_horiz_rad.append(
                    DataPoint(0, dates[i], 'SI', 'Diffuse Horizontal Radiation'))

        return cls(location, direct_norm_rad, diffuse_horiz_rad, timestep, is_leap_year)

    @classmethod
    def from_ashrae_clear_sky(cls, location, sky_clearness=1, timestep=1,
                              is_leap_year=False):
        """Create a wea object representing an original ASHRAE Clear Sky.

        The original ASHRAE Clear Sky is intended to determine peak solar load
        and sizing parmeters for HVAC systems.  It is not the sky model
        currently recommended by ASHRAE since it usually overestimates the
        amount of solar radiation in comparison to the newer ASHRAE Revised
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
                Default is False.
        """
        # parameters that approximate clear conditions across the planet
        # apparent solar irradiation at air mass m = 0
        monthly_a = [1202, 1187, 1164, 1130, 1106, 1092, 1093, 1107, 1136,
                     1166, 1190, 1204]
        # atmospheric extinction coefficient
        monthly_b = [0.141, 0.142, 0.149, 0.164, 0.177, 0.185, 0.186, 0.182,
                     0.165, 0.152, 0.144, 0.141]

        # create sunpath and get altitude at every timestep of the year
        sp = Sunpath.from_location(location)
        sp.is_leap_year = is_leap_year
        altitudes = []
        months = []
        dates = cls._get_datetimes(timestep, is_leap_year)
        for t_date in dates:
            sun = sp.calculate_sun_from_date_time(t_date)
            months.append(sun.datetime.month - 1)
            altitudes.append(sun.altitude)

        # compute hourly direct normal and diffuse horizontal radiation
        direct_norm_rad, diffuse_horiz_rad = \
            cls._get_empty_data_collections(location, timestep, is_leap_year)

        for i, alt in enumerate(altitudes):
            if alt > 0:
                try:
                    dir_norm = monthly_a[months[i]] / (math.exp(
                        monthly_b[months[i]] / (math.sin(math.radians(alt)))))
                    diff_horiz = 0.17 * dir_norm * math.sin(math.radians(alt))
                    dir_norm = (dir_norm * sky_clearness) / timestep
                    diff_horiz = (diff_horiz * sky_clearness) / timestep
                    direct_norm_rad.append(DataPoint(
                        dir_norm, dates[i], 'SI', 'Direct Normal Radiation'))
                    diffuse_horiz_rad.append(DataPoint(
                        diff_horiz, dates[i], 'SI', 'Diffuse Horizontal Radiation'))
                except OverflowError:
                    # very small altitude values
                    direct_norm_rad.append(
                        DataPoint(0, dates[i], 'SI', 'Direct Normal Radiation'))
                    diffuse_horiz_rad.append(
                        DataPoint(0, dates[i], 'SI', 'Diffuse Horizontal Radiation'))
            else:
                direct_norm_rad.append(
                    DataPoint(0, dates[i], 'SI', 'Direct Normal Radiation'))
                diffuse_horiz_rad.append(
                    DataPoint(0, dates[i], 'SI', 'Diffuse Horizontal Radiation'))

        return cls(location, direct_norm_rad, diffuse_horiz_rad, timestep, is_leap_year)

    # TODO: Split golbal into direct and diffuse using Perez method.
    # Right now, I use an old inaccurate method.
    @classmethod
    def from_zhang_huang_solar_model(cls, location, cloud_cover,
                                     relative_humidity, dry_bulb_temperature,
                                     wind_speed, timestep=1, is_leap_year=False):
        """Create a wea object from climate data using the Zhang-Huang model.

        The Zhang-Huang solar model was developed to estimate solar
        radiation for weather stations that lack such values, which are
        typically colleted with a pyranometer. Using total cloud cover,
        dry-bulb temperature, relative humidity, and wind speed as
        inputs the Zhang-Huang estimates global horizontal radiation
        by means of a regression model across these variables.
        For more information on the Zhang-Huang model, see the
        EnergyPlus Engineering Reference:
        https://bigladdersoftware.com/epx/docs/8-7/engineering-reference/climate-calculations.html#zhang-huang-solar-model

        Args:
            location: Ladybug location object.
            cloud_cover: A list of annual float values between 0 and 1
                that represent the fraction of the sky dome covered
                in clouds (0 = clear; 1 = completely overcast)
            cloud_cover: A list of annual float values between 0 and 1
                that represent the fraction of the sky dome covered
                in clouds (0 = clear; 1 = completely overcast)
            relative_humidity: A list of annual float values between
                0 and 100 that represent the relative humidity in percent.
            dry_bulb_temperature: A list of annual float values that
                represent the dry bulb temperature in degrees Celcius.
            wind_speed: A list of annual float values that
                represent the wind speed in meters per second.
            timestep: An optional integer to set the number of time steps per
                hour. Default is 1 for one value per hour.
            is_leap_year: A boolean to indicate if values are representing a leap year.
                Default is False.
        """
        # check input data
        assert len(cloud_cover) == len(relative_humidity) == \
            len(dry_bulb_temperature) == len(wind_speed), \
            'lengths of input climate data must match.'
        assert len(cloud_cover) / timestep == cls.day_count(is_leap_year), \
            'input climate data must be annual.'
        assert isinstance(timestep, int), 'timestep must be an' \
            ' integer. Got {}'.format(type(timestep))

        # solar model regression constants
        c0, c1, c2, c3, c4, c5, d_coeff, k_coeff = 0.5598, 0.4982, \
            -0.6762, 0.02842, -0.00317, 0.014, -17.853, 0.843

        # extraterrestrial solar constant (W/m2)
        irr0 = 1355

        # initiate sunpath based on location
        sp = Sunpath.from_location(location)
        sp.is_leap_year = is_leap_year

        # calculate zhang-huang radiation
        direct_norm_rad, diffuse_horiz_rad = \
            cls._get_empty_data_collections(location, timestep, is_leap_year)

        for count, t_date in enumerate(cls._get_datetimes(timestep, is_leap_year)):
            # start assuming night time
            glob_ir = 0
            dir_ir = 0
            diff_ir = 0

            # calculate sun altitude
            sun = sp.calculate_sun_from_date_time(t_date)
            alt = sun.altitude

            if alt > 0:
                # get sin of the altitude
                sin_alt = math.sin(math.radians(alt))

                # get the values at each timestep
                cc, rh, n_temp, n3_temp, w_spd = cloud_cover[count] / 10.0, \
                    relative_humidity[count], dry_bulb_temperature[count], \
                    dry_bulb_temperature[count - (3 * timestep)], wind_speed[count]

                # calculate zhang-huang global radiation
                glob_ir = ((irr0 * sin_alt *
                            (c0 + (c1 * cc) + (c2 * cc**2) +
                             (c3 * (n_temp - n3_temp)) +
                             (c4 * rh) + (c5 * w_spd))) + d_coeff) / k_coeff
                if glob_ir < 0:
                    glob_ir = 0
                else:
                    # calculate direct and diffuse solar
                    k_t = glob_ir / (irr0 * sin_alt)
                    k_tc = 0.4268 + (0.1934 * sin_alt)
                    if k_t >= k_tc:
                        k_ds = k_t - ((1.107 + (0.03569 * sin_alt) +
                                       (1.681 * sin_alt**2)) * (1 - k_t)**2)
                    else:
                        k_ds = (3.996 - (3.862 * sin_alt) +
                                (1.540 * sin_alt**2)) * k_t**3
                    diff_ir = (irr0 * sin_alt * (k_t - k_ds)) / (1 - k_ds)
                    dir_horiz_ir = (irr0 * sin_alt * k_ds * (1 - k_t)) / (1 - k_ds)
                    dir_ir = dir_horiz_ir / math.sin(math.radians(alt))

            direct_norm_rad.append(DataPoint(
                dir_ir, t_date, 'SI', 'Direct Normal Radiation'))
            diffuse_horiz_rad.append(DataPoint(
                diff_ir, t_date, 'SI', 'Diffuse Horizontal Radiation'))

        return cls(location, direct_norm_rad, diffuse_horiz_rad, timestep, is_leap_year)

    @property
    def isWea(self):
        """Return True."""
        return True

    @property
    def hoys(self):
        """Hours of the year in wea file."""
        return tuple(data.datetime.hoy for data in self.direct_normal_radiation)

    @property
    def datetimes(self):
        """Datetimes in wea file."""
        return tuple(data.datetime for data in self.direct_normal_radiation)

    @property
    def timestep(self):
        """Return the timestep."""
        return self._timestep

    @property
    def direct_normal_radiation(self):
        """Get or set the direct normal radiation."""
        return self._direct_normal_radiation

    @direct_normal_radiation.setter
    def direct_normal_radiation(self, data):
        assert len(data) / self.timestep == self.day_count(self.is_leap_year), \
            'direct_normal_radiation data must be annual.'
        assert isinstance(data, DataCollection), \
            'direct_normal_radiation data must be a data collection.'
        self._direct_normal_radiation = data
        self._is_global_computed = False

    @property
    def diffuse_horizontal_radiation(self):
        """Get or set the diffuse horizontal radiation."""
        return self._diffuse_horizontal_radiation

    @diffuse_horizontal_radiation.setter
    def diffuse_horizontal_radiation(self, data):
        assert len(data) / self.timestep == self.day_count(self.is_leap_year), \
            'diffuse_horizontal_radiation data must be annual.'
        assert isinstance(data, DataCollection), \
            'diffuse_horizontal_radiation data must be a data collection.'
        self._diffuse_horizontal_radiation = data
        self._is_global_computed = False

    @property
    def global_horizontal_radiation(self):
        """Returns the global horizontal radiation at each timestep."""
        analysis_period = AnalysisPeriod(timestep=self.timestep,
                                         is_leap_year=self.is_leap_year)
        header_ghr = Header(location=self.location,
                            analysis_period=analysis_period,
                            data_type='Global Horizontal Radiation',
                            unit='Wh/m2')
        global_horizontal_rad = DataCollection(header=header_ghr)
        is_leap_year = self.is_leap_year
        sp = Sunpath.from_location(self.location)
        sp.is_leap_year = is_leap_year
        for dnr, dhr in zip(self.direct_normal_radiation,
                            self.diffuse_horizontal_radiation):
            sun = sp.calculate_sun_from_date_time(dnr.datetime)
            glob_h = dhr + dnr * math.sin(math.radians(sun.altitude))
            global_horizontal_rad.append(
                DataPoint(glob_h, dnr.datetime, 'SI', 'Global Horizontal Radiation'))
        return global_horizontal_rad

    @property
    def direct_horizontal_radiation(self):
        """Returns the direct radiation on a horizontal surface at each timestep.

        Note that this is different from the direct_normal_radiation needed
        to construct a Wea, which is NORMAL and not HORIZONTAL."""
        analysis_period = AnalysisPeriod(timestep=self.timestep,
                                         is_leap_year=self.is_leap_year)
        header_dhr = Header(location=self.location,
                            analysis_period=analysis_period,
                            data_type='Direct Horizontal Radiation',
                            unit='Wh/m2')
        direct_horizontal_rad = DataCollection(header=header_dhr)
        is_leap_year = self.is_leap_year
        sp = Sunpath.from_location(self.location)
        sp.is_leap_year = is_leap_year
        for dnr in self.direct_normal_radiation:
            sun = sp.calculate_sun_from_date_time(dnr.datetime)
            dir_h = dnr * math.sin(math.radians(sun.altitude))
            direct_horizontal_rad.append(
                DataPoint(dir_h, dnr.datetime, 'SI', 'Direct Horizontal Radiation'))
        return direct_horizontal_rad

    @property
    def is_leap_year(self):
        """Return the timestep."""
        return self._is_leap_year

    @staticmethod
    def day_count(is_leap_year):
        """Number of days in this Wea file.

        Keep in mind that wea file is an annual file but this value will be different
        for a leap year
        """
        return 8760 + 24 if is_leap_year else 8760

    @staticmethod
    def _get_datetimes(timestep, is_leap_year):
        """List of datetimes based on timestep.

        This method should only be used for classmethods. For datetimes use datetiems or
        hoys methods.
        """
        day_count = 8760 + 24 if is_leap_year else 8760
        adjust_time = 30 if timestep == 1 else 0
        return tuple(
            DateTime.from_moy(60.0 * count / timestep + adjust_time, is_leap_year)
            for count in xrange(day_count * timestep)
        )

    @staticmethod
    def _get_empty_data_collections(location, timestep, is_leap_year):
        """Return two empty data collection.

        Direct Normal Radiation, Diffuse Horizontal Radiation
        """
        analysis_period = AnalysisPeriod(timestep=timestep, is_leap_year=is_leap_year)
        header_dnr = Header(location=location,
                            analysis_period=analysis_period,
                            data_type='Direct Normal Radiation',
                            unit='Wh/m2')
        direct_norm_rad = DataCollection(header=header_dnr)
        header_dhr = Header(location=location,
                            analysis_period=analysis_period,
                            data_type='Diffuse Horizontal Radiation',
                            unit='Wh/m2')
        diffuse_horiz_rad = DataCollection(header=header_dhr)

        return direct_norm_rad, diffuse_horiz_rad

    def get_radiation_values(self, month, day, hour):
        """Get direct and diffuse radiation values for a point in time."""
        dt = DateTime(month, day, hour, leap_year=self.is_leap_year)
        count = int(dt.hoy * self.timestep)
        return self.direct_normal_radiation[count], \
            self.diffuse_horizontal_radiation[count]

    def get_radiation_values_for_hoy(self, hoy):
        """Get direct and diffuse radiation values for an hoy."""
        count = int(hoy * self.timestep)
        return self.direct_normal_radiation[count], \
            self.diffuse_horizontal_radiation[count]

    def directional_radiation(self, altitude=90, azimuth=180,
                              ground_reflectance=0.2, isotrophic=True):
        """Returns the radiation components facing a given altitude and azimuth.

        This method computes unobstructed solar flux facing a given
        altitude and azimuth. The default is set to return the golbal horizontal
        radiation, assuming an altitude facing straight up (90 degrees).

        Args:
            altitude: A number between -90 and 90 that represents the
                altitude at which radiation is being evaluated in degrees.
            azimuth: A number between 0 and 360 that represents the
                azimuth at wich radiation is being evaluated in degrees.
            ground_reflectance: A number between 0 and 1 that represents the
                reflectance of the ground. Default is set to 0.2.
            isotrophic: A boolean value that sets whether an istotrophic sky is
                used (as opposed to an anisotrophic sky). An isotrophic sky
                assummes an even distribution of diffuse radiation across the
                sky while an anisotrophic sky places more diffuse radiation
                near the solar disc. Default is set to True for isotrophic

        Returns:
            total_radiation: A list of total solar radiation at each timestep.
            direct_radiation: A list of direct solar radiation at each timestep.
            diffuse_radiation: A list of diffuse sky solar radiation
                at each timestep.
            reflected_radiation: A list of ground reflected solar radiation
                at each timestep.
        """
        # function to convert polar coordinates to xyz.
        def pol2cart(phi, theta):
            mult = math.cos(theta)
            x = math.sin(phi) * mult
            y = math.cos(phi) * mult
            z = math.sin(theta)
            return Vector3(x, y, z)

        # convert the altitude and azimuth to a normal vector
        normal = pol2cart(math.radians(azimuth), math.radians(altitude))

        # create sunpath and get altitude at every timestep of the year
        direct_radiation = []
        diffuse_radiation = []
        reflected_radiation = []
        total_radiation = []
        sp = Sunpath.from_location(self.location)
        sp.is_leap_year = self.is_leap_year
        for dnr, dhr in zip(self.direct_normal_radiation,
                            self.diffuse_horizontal_radiation):
            dt = dnr.datetime
            sun = sp.calculate_sun_from_date_time(dt)
            sun_vec = pol2cart(math.radians(sun.azimuth),
                               math.radians(sun.altitude))
            vec_angle = sun_vec.angle(normal)

            # direct radiation on surface
            srf_dir = 0
            if sun.altitude > 0 and vec_angle < math.pi / 2:
                srf_dir = dnr * math.cos(vec_angle)

            # diffuse radiation on surface
            if isotrophic is True:
                srf_dif = dhr * ((math.sin(math.radians(altitude)) / 2) + 0.5)
            else:
                y = max(0.45, 0.55 + (0.437 * math.cos(vec_angle)) + 0.313 *
                        math.cos(vec_angle) * 0.313 * math.cos(vec_angle))
                srf_dif = self.dhr * (y * (
                    math.sin(math.radians(abs(90 - altitude)))) +
                    math.cos(math.radians(abs(90 - altitude))))

            # reflected radiation on surface.
            e_glob = dhr + dnr * math.cos(math.radians(90 - sun.altitude))
            srf_ref = e_glob * ground_reflectance * (0.5 - (math.sin(
                math.radians(altitude)) / 2))

            # add it all together
            direct_radiation.append(
                DataPoint(srf_dir, dt, 'SI', 'Radiation'))
            diffuse_radiation.append(
                DataPoint(srf_dif, dt, 'SI', 'Radiation'))
            reflected_radiation.append(
                DataPoint(srf_ref, dt, 'SI', 'Radiation'))
            total_radiation.append(
                DataPoint(srf_dir + srf_dif + srf_ref, dt, 'SI', 'Radiation'))

        return total_radiation, direct_radiation, \
            diffuse_radiation, reflected_radiation

    @property
    def header(self):
        """Wea header."""
        return "place %s\n" % self.location.city + \
            "latitude %.2f\n" % self.location.latitude + \
            "longitude %.2f\n" % -self.location.longitude + \
            "time_zone %d\n" % (-self.location.time_zone * 15) + \
            "site_elevation %.1f\n" % self.location.elevation + \
            "weather_data_file_units 1\n"

    def to_json(self):
        """Write Wea to json file
            {
            "location": {} , // ladybug location schema
            "direct_normal_radiation": (), // Tuple of hourly direct normal
                radiation
            "diffuse_horizontal_radiation": (), // Tuple of hourly diffuse
                horizontal radiation
            "timestep": float //timestep between measurements, default is 1
            }
        """
        return {
            'location': self.location.to_json(),
            'direct_normal_radiation':
                self.direct_normal_radiation.to_json(),
            'diffuse_horizontal_radiation':
                self.diffuse_horizontal_radiation.to_json(),
            'timestep': self.timestep,
            'is_leap_year': self.is_leap_year
        }

    def write(self, file_path, hoys=None, write_hours=False):
        """Write the wea file.

        WEA carries radiation values from epw and is what gendaymtx uses to
        generate the sky.
        """
        # generate hoys in wea file based on timestep
        full_wea = False
        if not hoys:
            hoys = self.hoys
            full_wea = True

        with open(file_path, "wb") as wea_file:
            # write header
            wea_file.write(self.header)
            if full_wea:
                # there is no input user for hoys, write it for all the hours
                # write values
                for dir_rad, dif_rad in zip(self.direct_normal_radiation,
                                            self.diffuse_horizontal_radiation):
                    dt = dir_rad.datetime
                    line = "%d %d %.3f %d %d\n" \
                        % (dt.month, dt.day, dt.float_hour, dir_rad, dif_rad)
                    wea_file.write(line)
            else:
                # output wea based on user request
                for hoy in hoys:
                    try:
                        dir_rad, dif_rad = self.get_radiation_values_for_hoy(hoy)
                    except IndexError:
                        print('Warn: Wea data for {} is not available!'.format(dt))
                        continue

                    dt = dir_rad.datetime
                    line = "%d %d %.3f %d %d\n" \
                        % (dt.month, dt.day, dt.float_hour, dir_rad, dif_rad)

                    wea_file.write(line)

        if write_hours:
            with open(file_path[:-4] + '.hrs', 'wb') as outf:
                outf.write(','.join(str(h) for h in hoys) + '\n')

        return file_path

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """epw file representation."""
        return "WEA [%s]" % self.location.city
