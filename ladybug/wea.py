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
        direct_normal_radiation: A list of direct normal radiation values for
            every hourly timestep of the year.
        diffuse_horizontal_radiation: A list of diffuse horizontal radiation
            values for every hourly timestep of the year.
        timestep: An optional integer to set the number of time steps per hour.
            Default is 1 for one value per hour.
    """

    def __init__(self, location, direct_normal_radiation,
                 diffuse_horizontal_radiation, timestep=1):
        """Create a wea object."""
        timestep = timestep or 1
        self._timestep = timestep
        assert isinstance(timestep, int), 'timestep must be an' \
            ' integer. Got {}'.format(type(timestep))

        self.location = location
        self.direct_normal_radiation = direct_normal_radiation
        self.diffuse_horizontal_radiation = diffuse_horizontal_radiation

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
        optional_keys = ('timestep',)

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

        return cls(location, direct_normal_radiation,
                   diffuse_horizontal_radiation, timestep)

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

        return cls(epw.location, direct_normal, diffuse_horizontal,
                   timestep)

    @classmethod
    def from_stat_file(cls, statfile, timestep=1):
        """Create an ASHRAE Revised Clear Sky wea object from the monthly sky
        optical depths in a .stat file.

        Args:
            statfile: Full path to the .stat file.
            timestep: An optional integer to set the number of time steps per
                hour. Default is 1 for one value per hour.
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
                                                 stat.monthly_tau_diffuse, timestep)

    @classmethod
    def from_ashrae_revised_clear_sky(cls, location, monthly_tau_beam,
                                      monthly_tau_diffuse, timestep=1):
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
        """
        # create sunpath and get altitude at every timestep of the year
        sp = Sunpath.from_location(location)
        altitudes = []
        months = []
        dates = []
        for h in xrange(8760 * timestep):
            if timestep == 1:
                t_date = DateTime.from_moy((h * 60) + 30)
            else:
                t_date = DateTime.from_moy((h / float(timestep)) * 60)
            sun = sp.calculate_sun_from_date_time(t_date)
            dates.append(sun.datetime)
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
            cls._get_data_collections(location, timestep)

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

        return cls(location, direct_norm_rad, diffuse_horiz_rad, timestep)

    @classmethod
    def from_ashrae_clear_sky(cls, location, sky_clearness=1, timestep=1):
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
        altitudes = []
        months = []
        dates = []
        for h in xrange(8760 * timestep):
            if timestep == 1:
                t_date = DateTime.from_moy((h * 60) + 30)
            else:
                t_date = DateTime.from_moy((h / float(timestep)) * 60)
            sun = sp.calculate_sun_from_date_time(t_date)
            dates.append(sun.datetime)
            months.append(sun.datetime.month - 1)
            altitudes.append(sun.altitude)

        # compute hourly direct normal and diffuse horizontal radiation
        direct_norm_rad, diffuse_horiz_rad = \
            cls._get_data_collections(location, timestep)

        for i, alt in enumerate(altitudes):
            if alt > 0.1:
                dir_norm = monthly_a[months[i]] / (math.exp(
                    monthly_b[months[i]] / (math.sin(math.radians(alt)))))
                diff_horiz = 0.17 * dir_norm * math.sin(math.radians(alt))
                dir_norm = (dir_norm * sky_clearness) / timestep
                diff_horiz = (diff_horiz * sky_clearness) / timestep
                direct_norm_rad.append(DataPoint(
                    dir_norm, dates[i], 'SI', 'Direct Normal Radiation'))
                diffuse_horiz_rad.append(DataPoint(
                    diff_horiz, dates[i], 'SI', 'Diffuse Horizontal Radiation'))
            else:
                direct_norm_rad.append(
                    DataPoint(0, dates[i], 'SI', 'Direct Normal Radiation'))
                diffuse_horiz_rad.append(
                    DataPoint(0, dates[i], 'SI', 'Diffuse Horizontal Radiation'))

        return cls(location, direct_norm_rad, diffuse_horiz_rad, timestep)

    # TODO: Split golbal into direct and diffuse using Perez method.
    # Right now, I use an old inaccurate method.
    @classmethod
    def from_zhang_huang_solar_model(cls, location, cloud_cover,
                                     relative_humidity, dry_bulb_temperature,
                                     wind_speed, timestep=1):
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
        """
        # check input data
        assert len(cloud_cover) == len(relative_humidity) == \
            len(dry_bulb_temperature) == len(wind_speed), \
            'lengths of input climate data must match.'
        assert len(cloud_cover) / timestep == 8760, \
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

        # calculate zhang-huang radiation
        direct_norm_rad, diffuse_horiz_rad = [], []
        for i in xrange(8760 * timestep):
            # start assuming night time
            glob_ir = 0
            dir_ir = 0
            diff_ir = 0

            # calculate sun altitude
            t_date = DateTime.from_moy(((i / float(timestep)) * 60) + 30)
            sun = sp.calculate_sun_from_date_time(t_date)
            alt = sun.altitude

            if alt > 0.1:
                # get sin of the altitude
                sin_alt = math.sin(math.radians(alt))

                # get the values at each timestep
                cc, rh, n_temp, n3_temp, w_spd = cloud_cover[i] / 10, \
                    relative_humidity[i], dry_bulb_temperature[i], \
                    dry_bulb_temperature[i - (3 * timestep)], wind_speed[i]

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
                dir_ir, sun.datetime, 'SI', 'Direct Normal Radiation'))
            diffuse_horiz_rad.append(DataPoint(
                diff_ir, sun.datetime, 'SI', 'Diffuse Horizontal Radiation'))

        return cls(location, direct_norm_rad, diffuse_horiz_rad, timestep)

    @property
    def isWea(self):
        """Return True."""
        return True

    @property
    def hoys(self):
        """Hours of the year in wea file."""
        return AnalysisPeriod(timestep=self.timestep).hoys

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
        assert len(data) / self.timestep == 8760, \
            'direct_normal_radiation data must be annual.'
        self._direct_normal_radiation = data
        self._is_global_computed = False

    @property
    def diffuse_horizontal_radiation(self):
        """Get or set the diffuse horizontal radiation."""
        return self._diffuse_horizontal_radiation

    @diffuse_horizontal_radiation.setter
    def diffuse_horizontal_radiation(self, data):
        assert len(data) / self.timestep == 8760, \
            'diffuse_horizontal_radiation data must be annual.'
        self._diffuse_horizontal_radiation = data
        self._is_global_computed = False

    @property
    def global_horizontal_radiation(self):
        """Returns the global horizontal radiation at each timestep."""
        global_horizontal_rad = []
        sp = Sunpath.from_location(self.location)
        for h in xrange(8760 * self.timestep):
            if self.timestep == 1:
                t_date = DateTime.from_moy((h * 60) + 30)
            else:
                t_date = DateTime.from_moy((h / float(self.timestep)) * 60)
            sun = sp.calculate_sun_from_date_time(t_date)
            date_t = sun.datetime
            glob_h = self.diffuse_horizontal_radiation[h] + \
                self.direct_normal_radiation[h] * math.sin(
                    math.radians(sun.altitude))
            global_horizontal_rad.append(
                DataPoint(glob_h, date_t, 'SI', 'Global Horizontal Radiation'))
        return global_horizontal_rad

    @property
    def direct_horizontal_radiation(self):
        """Returns the direct radiation on a horizontal surface at each timestep.

        Note that this is different from the direct_normal_radiation needed
        to construct a Wea, which is NORMAL and not HORIZONTAL."""
        direct_horizontal_rad = []
        sp = Sunpath.from_location(self.location)
        for h in xrange(8760 * self.timestep):
            if self.timestep == 1:
                t_date = DateTime.from_moy((h * 60) + 30)
            else:
                t_date = DateTime.from_moy((h / float(self.timestep)) * 60)
            sun = sp.calculate_sun_from_date_time(t_date)
            date_t = sun.datetime
            dir_h = self.direct_normal_radiation[h] * math.sin(
                math.radians(sun.altitude))
            direct_horizontal_rad.append(
                DataPoint(dir_h, date_t, 'SI', 'Direct Horizontal Radiation'))
        return direct_horizontal_rad

    @staticmethod
    def _get_data_collections(location, timestep):
        """Return two empty data collection.

        Direct Normal Radiation, Diffuse Horizontal Radiation
        """
        analysis_period = AnalysisPeriod(timestep=timestep)
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
        dt = DateTime(month, day, hour)
        hoy = int(dt.hoy * self.timestep)
        return self.direct_normal_radiation[hoy], self.diffuse_horizontal_radiation[hoy]

    def get_radiation_values_for_hoy(self, hoy):
        """Get direct and diffuse radiation values for an hoy."""
        hoy = int(hoy * self.timestep)
        return self.direct_normal_radiation[hoy], self.diffuse_horizontal_radiation[hoy]

    def radiation_on_surface(self, surface_altitude=90, surface_azimuth=180,
                             ground_reflectance=0.2, isotrophic=True):
        """Returns the total radiation falling on a surface at each timestep.

        This method computes solar radiation on an unobstructed surface with
        the input surface_altitude and surface_azimuth. The default is set to
        return the golbal horizontal radiation, assuming a surface altitude
        facing straight up (90 degrees).

        Args:
            surface_altitude: A number between -90 and 90 that represents the
                altitude that the surface is facing in degrees.
            surface_azimuth: A number between 0 and 360 that represents the
                azimuth that the surface is facing in degrees.
            ground_reflectance: A number between 0 and 1 that represents the
                reflectance of the ground. Default is set to 0.2.
            isotrophic: A boolean value that sets whether an istotrophic sky is
                used (as opposed to an anisotrophic sky). An isotrophic sky
                assummes an even distribution of diffuse radiation across the
                sky while an anisotrophic sky places more diffuse radiation
                near the solar disc. Default is set to True for isotrophic

        Returns:
            surface_total_radiation: A list of total solar radiation on the
                surface at each timestep.
            surface_direct_radiation: A list of direct solar radiation on the
                surface at each timestep.
            surface_diffuse_radiation: A list of diffuse sky solar radiation on
                the surface at each timestep.
            surface_reflected_radiation: A list of ground reflected solar
                radiation on the surface at each timestep.
        """
        # function to convert polar coordinates to xyz.
        def pol2cart(phi, theta):
            mult = math.cos(theta)
            x = math.sin(phi) * mult
            y = math.cos(phi) * mult
            z = math.sin(theta)
            return Vector3(x, y, z)

        # convert the surface altitude and azimuth to a normal vector
        surface_norm = pol2cart(math.radians(surface_azimuth),
                                math.radians(surface_altitude))

        # create sunpath and get altitude at every timestep of the year
        surface_direct_radiation = []
        surface_diffuse_radiation = []
        surface_reflected_radiation = []
        surface_total_radiation = []
        sp = Sunpath.from_location(self.location)
        for h in xrange(8760 * self.timestep):
            if self.timestep == 1:
                t_date = DateTime.from_moy((h * 60) + 30)
            else:
                t_date = DateTime.from_moy((h / float(self.timestep)) * 60)
            sun = sp.calculate_sun_from_date_time(t_date)
            date_t = sun.datetime
            sun_vec = pol2cart(math.radians(sun.azimuth),
                               math.radians(sun.altitude))
            vec_angle = sun_vec.angle(surface_norm)

            # direct radiation on surface
            srf_dir = 0
            if sun.altitude > 0 and vec_angle < math.pi / 2:
                srf_dir = self.direct_normal_radiation[h] * math.cos(vec_angle)

            # diffuse radiation on surface
            if isotrophic is True:
                srf_dif = self.diffuse_horizontal_radiation[h] * ((math.sin(
                    math.radians(surface_altitude)) / 2) + 0.5)
            else:
                y = max(0.45, 0.55 + (0.437 * math.cos(vec_angle)) + 0.313 *
                        math.cos(vec_angle) * 0.313 * math.cos(vec_angle))
                srf_dif = self.diffuse_horizontal_radiation[h] * (y * (
                    math.sin(math.radians(abs(90 - surface_altitude)))) +
                    math.cos(math.radians(abs(90 - surface_altitude))))

            # reflected radiation on surface.
            e_glob = self.diffuse_horizontal_radiation[h] + \
                self.direct_normal_radiation[h] * math.cos(
                    math.radians(90 - sun.altitude))
            srf_ref = e_glob * ground_reflectance * (0.5 - (math.sin(
                math.radians(surface_altitude)) / 2))

            # add it all together
            surface_direct_radiation.append(
                DataPoint(srf_dir, date_t, 'SI', 'Radiation'))
            surface_diffuse_radiation.append(
                DataPoint(srf_dif, date_t, 'SI', 'Radiation'))
            surface_reflected_radiation.append(
                DataPoint(srf_ref, date_t, 'SI', 'Radiation'))
            surface_total_radiation.append(
                DataPoint(srf_dir + srf_dif + srf_ref, date_t, 'SI', 'Radiation'))

        return surface_total_radiation, surface_direct_radiation, \
            surface_diffuse_radiation, surface_reflected_radiation

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
            'timestep': self.timestep
        }

    def write(self, file_path, hoys=None, write_hours=False):
        """Write the wea file.

        WEA carries radiation values from epw and is what gendaymtx uses to
        generate the sky.
        """
        # generate hoys in wea file based on timestep
        hoys_wea = self.hoys
        full_wea = False

        if not hoys:
            hoys = hoys_wea
            full_wea = True

        if self.timestep == 1:
            dts = (DateTime.from_hoy(h + 0.5) for h in hoys)
        else:
            dts = (DateTime.from_hoy(h) for h in hoys)

        with open(file_path, "wb") as weaFile:
            # write header
            weaFile.write(self.header)
            if self.timestep == 1:
                # not the whole year
                for dt, hoy in zip(dts, hoys):
                    dir_rad = self.direct_normal_radiation[int(hoy)]
                    dif_rad = self.diffuse_horizontal_radiation[int(hoy)]
                    line = "%d %d %.3f %d %d\n" \
                        % (dt.month, dt.day, dt.hour + 0.5, dir_rad, dif_rad)

                    weaFile.write(line)
            elif full_wea:
                # there is no input user for hoys, write it for all the hours
                # write values
                for dt, dir_rad, dif_rad in zip(
                    dts, self.direct_normal_radiation,
                        self.diffuse_horizontal_radiation):
                    line = "%d %d %.3f %d %d\n" \
                        % (dt.month, dt.day, dt.float_hour, dir_rad, dif_rad)
                    weaFile.write(line)
            else:
                # output wea hoys based on user request
                hoys_set = set(hoys_wea)
                # write values
                for dt, dir_rad, dif_rad in zip(
                        dts, self.direct_normal_radiation,
                        self.diffuse_horizontal_radiation):
                    if dt.hoy not in hoys_set:
                        print('Warn: Wea data for {} is not available!'.format(dt))
                        continue
                    line = "%d %d %.3f %d %d\n" \
                        % (dt.month, dt.day, dt.float_hour, dir_rad, dif_rad)

                    weaFile.write(line)

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
