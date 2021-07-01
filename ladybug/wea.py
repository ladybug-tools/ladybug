# coding=utf-8
from __future__ import division

import math
import os
from copy import deepcopy

from ladybug_geometry.geometry3d.pointvector import Vector3D

from .analysisperiod import AnalysisPeriod
from .datacollection import HourlyContinuousCollection, HourlyDiscontinuousCollection
from .datatype.energyflux import Irradiance, GlobalHorizontalIrradiance, \
    DirectNormalIrradiance, DiffuseHorizontalIrradiance, DirectHorizontalIrradiance
from .datatype.illuminance import GlobalHorizontalIlluminance, \
    DirectNormalIlluminance, DiffuseHorizontalIlluminance
from .datatype.luminance import ZenithLuminance
from .dt import DateTime, Time
from .epw import EPW
from .futil import write_to_file
from .header import Header
from .location import Location
from .skymodel import ashrae_revised_clear_sky, ashrae_clear_sky, \
    zhang_huang_solar_split, estimate_illuminance_from_irradiance
from .stat import STAT
from .sunpath import Sunpath

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
    """A WEA object containing hourly or sub-hourly solar irradiance.

    This object and its corresponding .wea file type is what the Radiance gendaymtx
    function uses to generate the sky.

    Args:
        location: Ladybug location object.
        direct_normal_irradiance: A HourlyContinuousCollection or a
            HourlyDiscontinuousCollection for direct normal irradiance. The
            collection must be aligned with the diffuse_horizontal_irradiance.
        diffuse_horizontal_irradiance: A HourlyContinuousCollection or a
            HourlyDiscontinuousCollection for diffuse horizontal irradiance, The
            collection must be aligned with the direct_normal_irradiance.

    Properties:
        * location
        * direct_normal_irradiance
        * diffuse_horizontal_irradiance
        * direct_horizontal_irradiance
        * global_horizontal_irradiance
        * enforce_on_hour
        * datetimes
        * hoys
        * analysis_period
        * timestep
        * is_leap_year
        * is_continuous
        * is_annual
        * header
    """
    __slots__ = \
        ('_timestep', '_is_leap_year', '_location', 'metadata', '_enforce_on_hour',
         '_direct_normal_irradiance', '_diffuse_horizontal_irradiance')

    def __init__(
        self, location, direct_normal_irradiance, diffuse_horizontal_irradiance
    ):
        """Create a Wea object."""
        # Check that input collections are of the right type and aligned to each other
        acceptable_colls = (HourlyContinuousCollection, HourlyDiscontinuousCollection)
        for coll in (direct_normal_irradiance, diffuse_horizontal_irradiance):
            assert isinstance(coll, acceptable_colls), 'Input irradiance data for ' \
                'Wea must be an hourly data collection. Got {}.'.format(type(coll))
        assert direct_normal_irradiance.is_collection_aligned(
            diffuse_horizontal_irradiance), 'Wea direct normal and diffuse horizontal ' \
            'irradiance collections must be aligned with one another.'

        # assign the location, irradiance, metadata, timestep and leap year
        self._enforce_on_hour = False  # False by default
        self.location = location
        self._direct_normal_irradiance = direct_normal_irradiance
        self._diffuse_horizontal_irradiance = diffuse_horizontal_irradiance
        self.metadata = {'source': location.source, 'country': location.country,
                         'city': location.city}
        self._timestep = direct_normal_irradiance.header.analysis_period.timestep
        self._is_leap_year = direct_normal_irradiance.header.analysis_period.is_leap_year

    @classmethod
    def from_annual_values(
        cls, location, direct_normal_irradiance, diffuse_horizontal_irradiance,
        timestep=1, is_leap_year=False
    ):
        """Create an annual Wea from an array of irradiance values.

        Args:
            location: Ladybug location object.
            direct_normal_irradiance: An array of values for direct normal irradiance.
                The length of this list should be same as diffuse_horizontal_irradiance
                and should represent an entire year of values at the input timestep.
            diffuse_horizontal_irradiance: A HourlyContinuousCollection or a
                HourlyDiscontinuousCollection for diffuse horizontal irradiance, The
                collection must be aligned with the direct_normal_irradiance.
            timestep: An integer to set the number of time steps per hour.
                Default is 1 for one value per hour.
            is_leap_year: A boolean to indicate if values are for a leap
                year. (Default: False).
        """
        metadata = {'source': location.source, 'country': location.country,
                    'city': location.city}
        dnr, dhr = cls._get_data_collections(
            direct_normal_irradiance, diffuse_horizontal_irradiance,
            metadata, timestep, is_leap_year)
        return cls(location, dnr, dhr)

    @classmethod
    def from_dict(cls, data):
        """ Create Wea from a dictionary

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "type": "Wea",
            "location": {},  # ladybug location dictionary
            "direct_normal_irradiance": [],  # direct normal irradiance values
            "diffuse_horizontal_irradiance": [],  # diffuse horizontal irradiance values
            "timestep": 1,  # optional timestep between measurements
            "is_leap_year": False,  # optional boolean for leap year
            "datetimes": []  # array of datetime arrays; only required when not annual
            }
        """
        # check for the required keys
        required_keys = ('type', 'location', 'direct_normal_irradiance',
                         'diffuse_horizontal_irradiance')
        for key in required_keys:
            assert key in data, 'Required key "{}" is missing!'.format(key)
        assert data['type'] == 'Wea', \
            'Expected Wea dictionary. Got {}.'.format(data['type'])

        # set the optional properties
        timestep = data['timestep'] if 'timestep' in data else 1
        is_leap_year = data['is_leap_year'] if 'is_leap_year' in data else False

        # correctly interpret the datetimes to create correct analysis periods
        continuous = True
        if 'datetimes' in data and data['datetimes'] is not None:
            st_dt = DateTime.from_array(data['datetimes'][0])
            end_dt = DateTime.from_array(data['datetimes'][-1])
            if st_dt.leap_year is not is_leap_year:
                st_dt = DateTime(st_dt.month, st_dt.day, st_dt.hour, is_leap_year)
                end_dt = DateTime(end_dt.month, end_dt.day, end_dt.hour, is_leap_year)
            a_per = AnalysisPeriod.from_start_end_datetime(st_dt, end_dt, timestep)
            if a_per.st_hour != 0 or a_per.end_hour != 23:
                continuous = False
            if len(a_per) != len(data['direct_normal_irradiance']):
                a_per = AnalysisPeriod(timestep=timestep, is_leap_year=is_leap_year)
                continuous = False
        else:  # assume it is annual continuous data
            a_per = AnalysisPeriod(timestep=timestep, is_leap_year=is_leap_year)

        # serialize the location and data collections
        location = Location.from_dict(data['location'])
        dni_head = Header(DirectNormalIrradiance(), 'W/m2', a_per)
        dhi_head = Header(DiffuseHorizontalIrradiance(), 'W/m2', a_per)
        if continuous:
            dni = HourlyContinuousCollection(
                dni_head, data['direct_normal_irradiance'])
            dhi = HourlyContinuousCollection(
                dhi_head, data['diffuse_horizontal_irradiance'])
        else:
            datetimes = [DateTime.from_array(dat) for dat in data['datetimes']]
            dni = HourlyDiscontinuousCollection(
                dni_head, data['direct_normal_irradiance'], datetimes)
            dhi = HourlyDiscontinuousCollection(
                dhi_head, data['diffuse_horizontal_irradiance'], datetimes)

        return cls(location, dni, dhi)

    @classmethod
    def from_file(cls, wea_file, timestep=1, is_leap_year=False):
        """Create Wea object from a .wea file.

        Args:
            wea_file:Full path to .wea file.
            timestep: An optional integer to set the number of time steps per hour.
                Default is 1 for one value per hour. If the wea file has a time step
                smaller than an hour, adjust this input accordingly.
            is_leap_year: A boolean to indicate if values are for a leap
                year. (Default: False).
        """
        assert os.path.isfile(wea_file), 'Failed to find {}'.format(wea_file)
        with open(wea_file, readmode) as weaf:
            location = cls._parse_wea_header(weaf, wea_file)
            # parse irradiance values
            dir_norm_irr = []
            dif_horiz_irr = []
            dt_arr = []
            for line in weaf:
                vals = line.split()
                dir_norm_irr.append(float(vals[-2]))
                dif_horiz_irr.append(float(vals[-1]))
                dt_arr.append([int(vals[0]), int(vals[1]), float(vals[2])])

        # interpret datetimes to create data collections with correct analysis periods
        continuous = True
        st_dt = DateTime.from_array([dt_arr[0][0], dt_arr[0][1], int(dt_arr[0][2])])
        end_dt = DateTime.from_array([dt_arr[-1][0], dt_arr[-1][1], int(dt_arr[-1][2])])
        if st_dt.leap_year is not is_leap_year:
            st_dt = DateTime(st_dt.month, st_dt.day, st_dt.hour, is_leap_year)
            end_dt = DateTime(end_dt.month, end_dt.day, end_dt.hour, is_leap_year)
        a_per = AnalysisPeriod.from_start_end_datetime(st_dt, end_dt, timestep)
        if a_per.st_hour != 0 or a_per.end_hour != 23:  # potential continuous time slice
            continuous = False
        if len(a_per) != len(dir_norm_irr):  # true discontinuous data
            a_per = AnalysisPeriod(timestep=timestep, is_leap_year=is_leap_year)
            continuous = False

        # serialize the data collections
        metadata = {'city': location.city}
        dni_head = Header(DirectNormalIrradiance(), 'W/m2', a_per, metadata)
        dhi_head = Header(DiffuseHorizontalIrradiance(), 'W/m2', a_per, metadata)
        if continuous:
            dni = HourlyContinuousCollection(dni_head, dir_norm_irr)
            dhi = HourlyContinuousCollection(dhi_head, dif_horiz_irr)
        else:
            if timestep == 1:
                datetimes = [DateTime(d[0], d[1], int(d[2])) for d in dt_arr]
            else:
                datetimes = []
                for d in dt_arr:
                    tim = Time.from_mod(int(d[2] * 60))
                    datetimes.append(DateTime(d[0], d[1], tim.hour, tim.minute))
            dni = HourlyDiscontinuousCollection(dni_head, dir_norm_irr, datetimes)
            dhi = HourlyDiscontinuousCollection(dhi_head, dif_horiz_irr, datetimes)
            dni = dni.validate_analysis_period()
            dhi = dhi.validate_analysis_period()

        return cls(location, dni, dhi)

    @classmethod
    def from_daysim_file(cls, wea_file, timestep=1, is_leap_year=False):
        """Create Wea object from a .wea file produced by DAYSIM.

        Note that this method is only required when the .wea file generated from
        DAYSIM has a timestep greater than 1, which results in the file using
        times of day greater than 23:59. DAYSIM weas with a timestep of 1 can
        use the from_file method without issues.

        Args:
            wea_file:Full path to .wea file.
            timestep: An optional integer to set the number of time steps per hour.
                Default is 1 for one value per hour.
            is_leap_year: A boolean to indicate if values are for a leap
                year. (Default: False).
        """
        # parse in the data
        assert os.path.isfile(wea_file), 'Failed to find {}'.format(wea_file)
        with open(wea_file, readmode) as weaf:
            location = cls._parse_wea_header(weaf, wea_file)
            # parse irradiance values
            dir_norm_irr = []
            dif_horiz_irr = []
            for line in weaf:
                dirn, difh = [int(v) for v in line.split()[-2:]]
                dir_norm_irr.append(dirn)
                dif_horiz_irr.append(difh)

        # move the last half hour of data to the start of the file
        if timestep != 1:
            shift = -int(timestep / 2)
            dir_norm_irr = dir_norm_irr[shift:] + dir_norm_irr[:shift]
            dif_horiz_irr = dif_horiz_irr[shift:] + dif_horiz_irr[:shift]

        return cls.from_annual_values(
            location, dir_norm_irr, dif_horiz_irr, timestep, is_leap_year)

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
        epw = EPW(epw_file)
        direct_normal, diffuse_horizontal = \
            cls._get_data_collections(epw.direct_normal_radiation.values,
                                      epw.diffuse_horizontal_radiation.values,
                                      epw.metadata, 1, epw.is_leap_year)
        if timestep != 1:
            print("Note: timesteps greater than 1 on epw-generated Weas \n"
                  "are suitable for thermal models but are not recommended \n"
                  "for daylight models.")
            # interpolate the data
            direct_normal = direct_normal.interpolate_to_timestep(timestep)
            diffuse_horizontal = diffuse_horizontal.interpolate_to_timestep(timestep)
            # create sunpath to check if the sun is up at a given timestep
            sp = Sunpath.from_location(epw.location)
            # add correct values to the empty data collection
            for i, dt in enumerate(cls._get_datetimes(timestep, epw.is_leap_year)):
                # set irradiance values to 0 when the sun is not up
                sun = sp.calculate_sun_from_date_time(dt)
                if sun.altitude < 0:
                    direct_normal[i] = 0
                    diffuse_horizontal[i] = 0

        return cls(epw.location, direct_normal, diffuse_horizontal)

    @classmethod
    def from_stat_file(cls, statfile, timestep=1, is_leap_year=False):
        """Create an ASHRAE Revised Clear Sky Wea object from data in .stat file.

        The .stat file must have monthly sky optical depths within it in order to
        create a Wea this way.

        Args:
            statfile: Full path to the .stat file.
            timestep: An optional integer to set the number of time steps per
                hour. Default is 1 for one value per hour.
            is_leap_year: A boolean to indicate if values are for a leap
                year. (Default: False).
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
            is_leap_year: A boolean to indicate if values are for a leap
                year. (Default: False).
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

        return cls(location, direct_norm_rad, diffuse_horiz_rad)

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
            is_leap_year: A boolean to indicate if values are for a leap
                year. (Default: False).
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

        return cls(location, direct_norm_rad, diffuse_horiz_rad)

    @classmethod
    def from_zhang_huang_solar(cls, location, cloud_cover, relative_humidity,
                               dry_bulb_temperature, wind_speed,
                               atmospheric_pressure=None, use_disc=False):
        """Create a Wea object from climate data using the Zhang-Huang model.

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
            cloud_cover: A hourly continuous data collection with values for the
                fraction of the sky dome covered in clouds (0 = clear;
                1 = completely overcast).
            relative_humidity: A hourly continuous data collection with values for
                the relative humidity in percent.
            dry_bulb_temperature: A hourly continuous data collection with values
                for the dry bulb temperature in degrees Celsius.
            wind_speed: A hourly continuous data collection with values for the
                wind speed in meters per second.
            atmospheric_pressure: An optional hourly continuous data collection
                with values for the atmospheric pressure in Pa. If None, pressure
                at sea level will be used (101325 Pa). (Default: None)
            use_disc: Boolean to note whether the original DISC model as opposed to the
                newer and more accurate DIRINT model. (Default: False).
        """
        # Check that input collections are of the right type and aligned to each other
        colls = (cloud_cover, relative_humidity, dry_bulb_temperature, wind_speed)
        for coll in colls:
            assert isinstance(coll, HourlyContinuousCollection), 'Input data for Zhang' \
                '-Huang Wea must be an hourly continuous. Got {}.'.format(type(coll))
        assert cloud_cover.are_collections_aligned(colls), 'Zhang-Huang Wea input ' \
            'data collections must be aligned with one another.'

        # check atmospheric_pressure input and generate default if None
        if atmospheric_pressure is not None:
            assert cloud_cover.is_collection_aligned(atmospheric_pressure), \
                'length pf atmospheric_pressure must match the other input collections.'
            atm_pressure = atmospheric_pressure.values
        else:
            atm_pressure = [101325] * len(cloud_cover)

        # initiate sunpath based on location
        sp = Sunpath.from_location(location)
        sp.is_leap_year = cloud_cover.header.analysis_period.is_leap_year
        a_per = cloud_cover.header.analysis_period

        # calculate parameters needed for zhang-huang irradiance
        date_times = []
        altitudes = []
        doys = []
        dry_bulb_t3_hrs = []
        for count, t_date in enumerate(cloud_cover.datetimes):
            date_times.append(t_date)
            sun = sp.calculate_sun_from_date_time(t_date)
            altitudes.append(sun.altitude)
            doys.append(sun.datetime.doy)
            dry_bulb_t3_hrs.append(dry_bulb_temperature[count - (3 * a_per.timestep)])

        # calculate zhang-huang irradiance
        dir_ir, diff_ir = zhang_huang_solar_split(
            altitudes, doys, cloud_cover.values, relative_humidity.values,
            dry_bulb_temperature.values, dry_bulb_t3_hrs, wind_speed.values,
            atm_pressure, use_disc)

        # assemble the results into DataCollections
        metadata = {'source': location.source, 'country': location.country,
                    'city': location.city}
        dni_head = Header(DirectNormalIrradiance(), 'W/m2', a_per, metadata)
        dhi_head = Header(DiffuseHorizontalIrradiance(), 'W/m2', a_per, metadata)
        dni = HourlyContinuousCollection(dni_head, dir_ir)
        dhi = HourlyContinuousCollection(dhi_head, diff_ir)
        return cls(location, dni, dhi)

    @property
    def enforce_on_hour(self):
        """Get or set a boolean for whether datetimes occur on the hour.

        By default, datetimes will be on the half-hour whenever the Wea has a
        timestep of 1, which aligns best with epw data. Setting this property
        to True will force the datetimes to be on the hour. Note that this
        property has no effect when the Wea timestep is not 1.
        """
        return self._enforce_on_hour

    @enforce_on_hour.setter
    def enforce_on_hour(self, value):
        self._enforce_on_hour = bool(value)

    @property
    def datetimes(self):
        """Get the datetimes in the Wea as a tuple of datetimes."""
        if self.timestep == 1 and not self._enforce_on_hour:
            return tuple(dt.add_minute(30) for dt in
                         self.direct_normal_irradiance.datetimes)
        else:
            return self.direct_normal_irradiance.datetimes

    @property
    def hoys(self):
        """Get the hours of the year in Wea as a tuple of floats."""
        return tuple(dt.hoy for dt in self.datetimes)

    @property
    def analysis_period(self):
        """Get an AnalysisPeriod for the Wea data."""
        return self._direct_normal_irradiance.header.analysis_period

    @property
    def timestep(self):
        """Get the timesteps per hour of the Wea as an integer."""
        return self._timestep

    @property
    def is_leap_year(self):
        """Get a boolean for whether the irradiance data is for a leap year."""
        return self._is_leap_year

    @property
    def is_continuous(self):
        """Get a boolean for whether the irradiance data is continuous."""
        return isinstance(self._direct_normal_irradiance, HourlyContinuousCollection)

    @property
    def is_annual(self):
        """Get a boolean for whether the irradiance data is for an entire year."""
        return self.is_continuous and self.analysis_period.is_annual

    @property
    def header(self):
        """Get the Wea header as a string."""
        return "place %s\n" % self.location.city + \
            "latitude %.2f\n" % self.location.latitude + \
            "longitude %.2f\n" % -self.location.longitude + \
            "time_zone %d\n" % (-self.location.time_zone * 15) + \
            "site_elevation %.1f\n" % self.location.elevation + \
            "weather_data_file_units 1\n"

    @property
    def location(self):
        """Get or set a Ladybug Location object for the Wea."""
        return self._location

    @location.setter
    def location(self, value):
        assert isinstance(value, Location), \
            'Wea.location data must be a Ladybug Location. Got {}'.format(type(value))
        self._location = value

    @property
    def direct_normal_irradiance(self):
        """Get or set a hourly data collection for the direct normal irradiance."""
        return self._direct_normal_irradiance

    @direct_normal_irradiance.setter
    def direct_normal_irradiance(self, data):
        acceptable_colls = (HourlyContinuousCollection, HourlyDiscontinuousCollection)
        assert isinstance(data, acceptable_colls), 'Input irradiance data for ' \
            'Wea must be an hourly data collection. Got {}.'.format(type(data))
        assert data.is_collection_aligned(self.diffuse_horizontal_irradiance), \
            'Wea direct normal and diffuse horizontal ' \
            'irradiance collections must be aligned with one another.'
        assert isinstance(data.header.data_type, DirectNormalIrradiance), \
            'direct_normal_irradiance data type must be' \
            'DirectNormalIrradiance. Got {}'.format(type(data.header.data_type))
        self._direct_normal_irradiance = data

    @property
    def diffuse_horizontal_irradiance(self):
        """Get or set a hourly data collection for the diffuse horizontal irradiance."""
        return self._diffuse_horizontal_irradiance

    @diffuse_horizontal_irradiance.setter
    def diffuse_horizontal_irradiance(self, data):
        acceptable_colls = (HourlyContinuousCollection, HourlyDiscontinuousCollection)
        assert isinstance(data, acceptable_colls), 'Input irradiance data for ' \
            'Wea must be an hourly data collection. Got {}.'.format(type(data))
        assert data.is_collection_aligned(self.direct_normal_irradiance), \
            'Wea direct normal and diffuse horizontal ' \
            'irradiance collections must be aligned with one another.'
        assert isinstance(data.header.data_type, DiffuseHorizontalIrradiance), \
            'direct_normal_irradiance data type must be' \
            'DiffuseHorizontalIrradiance. Got {}'.format(type(data.header.data_type))
        self._diffuse_horizontal_irradiance = data

    @property
    def global_horizontal_irradiance(self):
        """Get a data collection for the global horizontal irradiance."""
        header_ghr = Header(data_type=GlobalHorizontalIrradiance(),
                            unit='W/m2',
                            analysis_period=self.analysis_period,
                            metadata=self.metadata)
        glob_horiz = []
        sp = Sunpath.from_location(self.location)
        sp.is_leap_year = self.is_leap_year
        for dt, dnr, dhr in zip(self.datetimes, self.direct_normal_irradiance,
                                self.diffuse_horizontal_irradiance):
            sun = sp.calculate_sun_from_date_time(dt)
            glob_horiz.append(dhr + dnr * math.sin(math.radians(sun.altitude)))
        return self._aligned_collection(header_ghr, glob_horiz)

    @property
    def direct_horizontal_irradiance(self):
        """Get a data collection for the direct irradiance on a horizontal surface.

        Note that this is different from the direct_normal_irradiance needed
        to construct a Wea, which is NORMAL and not HORIZONTAL.
        """
        header_dhr = Header(data_type=DirectHorizontalIrradiance(),
                            unit='W/m2',
                            analysis_period=self.analysis_period,
                            metadata=self.metadata)
        direct_horiz = []
        sp = Sunpath.from_location(self.location)
        sp.is_leap_year = self.is_leap_year
        for dt, dnr in zip(self.datetimes, self.direct_normal_irradiance):
            sun = sp.calculate_sun_from_date_time(dt)
            direct_horiz.append(dnr * math.sin(math.radians(sun.altitude)))
        return self._aligned_collection(header_dhr, direct_horiz)

    def filter_by_pattern(self, pattern):
        """Create a new filtered Wea from this Wea using a list of booleans.

        Args:
            pattern: An array of True/False values. This array should usually
                have a length matching the number of irradiance values in the Wea
                but it can also be a pattern to be repeated over the data.

        Returns:
            A new Wea filtered by the analysis period.
        """
        return Wea(
            self.location,
            self.direct_normal_irradiance.filter_by_pattern(pattern),
            self.diffuse_horizontal_irradiance.filter_by_pattern(pattern))

    def filter_by_analysis_period(self, analysis_period):
        """Create a new filtered Wea from this Wea based on an analysis period.

        Args:
           analysis period: A Ladybug analysis period.

        Returns:
            A new Wea filtered by the analysis period.
        """
        return Wea(
            self.location,
            self.direct_normal_irradiance.filter_by_analysis_period(analysis_period),
            self.diffuse_horizontal_irradiance.filter_by_analysis_period(analysis_period)
        )

    def filter_by_hoys(self, hoys):
        """Create a new filtered Wea from this Wea using a list of hours of the year.

        Args:
           hoys: A List of hours of the year 0..8759.

        Returns:
            A new Wea with filtered data.
        """
        return Wea(
            self.location,
            self.direct_normal_irradiance.filter_by_hoys(hoys),
            self.diffuse_horizontal_irradiance.filter_by_hoys(hoys))

    def filter_by_moys(self, moys):
        """Create a new filtered Wea from this Wea based on a list of minutes of the year.

        Args:
           moys: A List of minutes of the year [0..8759 * 60].

        Returns:
            A new Wea with filtered data.
        """
        return Wea(
            self.location,
            self.direct_normal_irradiance.filter_by_moys(moys),
            self.diffuse_horizontal_irradiance.filter_by_moys(moys))

    def filter_by_sun_up(self, min_altitude=0):
        """Create a new filtered Wea from this Wea based on whether the sun is up

        Args:
            min_altitude: A number for the minimum altitude above the horizon at
                which the sun is considered up in degrees. Setting this to 0 will
                filter values for all hours where the sun is physically above the
                horizon. By setting this to a negative number (eg. -6), various levels
                of twilight can be used to filter the data (eg. civil twilight).
                Positive numbers can be used to discount low sun angles (Default: 0).

        Returns:
            A new Wea with filtered data.
        """
        sp = Sunpath.from_location(self.location)
        sp.is_leap_year = self.is_leap_year
        pattern = []
        for dt in self.datetimes:
            sun = sp.calculate_sun_from_date_time(dt)
            sun_up = True if sun.altitude > min_altitude else False
            pattern.append(sun_up)
        return self.filter_by_pattern(pattern)

    def get_irradiance_value(self, month, day, hour):
        """Get direct and diffuse irradiance values for a point in time.

        Args:
            month: Integer for month of the year [1 - 12].
            day: Integer for the day of the month [1 - 31].
            hour: Float for hour of the day [0 - 23].
        """
        dt = DateTime(month, day, hour, leap_year=self.is_leap_year)
        try:
            count = int(dt.hoy * self.timestep) if self.is_annual else \
                self.direct_normal_irradiance.datetimes.index(dt)
        except ValueError as e:
            raise ValueError('Datetime {} was not found in the Wea.\n{}'.format(dt, e))
        return self.direct_normal_irradiance[count], \
            self.diffuse_horizontal_irradiance[count]

    def get_irradiance_value_for_hoy(self, hoy):
        """Get direct and diffuse irradiance values for a hoy.

        Args:
            hoy: Float for hour of the year [0 - 8759].
        """
        try:
            count = int(hoy * self.timestep) if self.is_annual else \
                self.direct_normal_irradiance.datetimes.index(DateTime.from_hoy(hoy))
        except ValueError as e:
            raise ValueError('HOY {} was not found in the Wea.\n{}'.format(hoy, e))
        return self.direct_normal_irradiance[count], \
            self.diffuse_horizontal_irradiance[count]

    def directional_irradiance(self, altitude=90, azimuth=180,
                               ground_reflectance=0.2, isotropic=True):
        """Get the irradiance components for a surface facing a given direction.

        Note this method computes unobstructed solar flux facing a given
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

            isotropic: A boolean value that sets whether an isotropic sky is
                used (as opposed to an anisotropic sky). An isotropic sky
                assumes an even distribution of diffuse irradiance across the
                sky while an anisotropic sky places more diffuse irradiance
                near the solar disc. (Default: True).

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
        dir_irr, diff_irr, ref_irr, total_irr = [], [], [], []
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
            if isotropic:
                srf_dif = dhr * ((math.sin(math.radians(altitude)) / 2) + 0.5)
            else:
                y = max(0.45, 0.55 + (0.437 * math.cos(vec_angle)) + 0.313 *
                        math.cos(vec_angle) * 0.313 * math.cos(vec_angle))
                srf_dif = dhr * (y * (
                    math.sin(math.radians(abs(90 - altitude)))) +
                    math.cos(math.radians(abs(90 - altitude))))

            # reflected irradiance on surface.
            e_glob = dhr + dnr * math.cos(math.radians(90 - sun.altitude))
            srf_ref = e_glob * ground_reflectance * (0.5 - (math.sin(
                math.radians(altitude)) / 2))

            # add it all together
            dir_irr.append(srf_dir)
            diff_irr.append(srf_dif)
            ref_irr.append(srf_ref)
            total_irr.append(srf_dir + srf_dif + srf_ref)

        # create the headers
        data_head = Header(Irradiance(), 'W/m2', self.analysis_period, self.metadata)

        # create the data collections
        direct_irradiance = self._aligned_collection(data_head, dir_irr)
        diffuse_irradiance = self._aligned_collection(data_head, diff_irr)
        reflected_irradiance = self._aligned_collection(data_head, ref_irr)
        total_irradiance = self._aligned_collection(data_head, total_irr)

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
            dew_point: A data collection of dewpoint temperature in degrees C. This
                data collection must align with the irradiance data on this object.

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
        assert dew_point.is_collection_aligned(self.direct_normal_irradiance), \
            'Input dew_point data must be aligned with the irradiance on the Wea.'

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
        gh_ill_head = Header(GlobalHorizontalIlluminance(), 'lux',
                             self.analysis_period, self.metadata)
        dn_ill_head = Header(DirectNormalIlluminance(), 'lux',
                             self.analysis_period, self.metadata)
        dh_ill_head = Header(DiffuseHorizontalIlluminance(), 'lux',
                             self.analysis_period, self.metadata)
        zen_lum_head = Header(ZenithLuminance(), 'cd/m2',
                              self.analysis_period, self.metadata)

        # create data collections to hold illuminance results
        global_horiz_ill = self._aligned_collection(gh_ill_head, gh_ill_values)
        direct_normal_ill = self._aligned_collection(dn_ill_head, dn_ill_values)
        diffuse_horizontal_ill = self._aligned_collection(dh_ill_head, dh_ill_values)
        zenith_lum = self._aligned_collection(zen_lum_head, zen_lum_values)

        return global_horiz_ill, direct_normal_ill, diffuse_horizontal_ill, zenith_lum

    def to_dict(self):
        """Get the Wea as a dictionary."""
        base = {
            'type': 'Wea',
            'location': self.location.to_dict(),
            'direct_normal_irradiance': self.direct_normal_irradiance.values,
            'diffuse_horizontal_irradiance': self.diffuse_horizontal_irradiance.values,
            'timestep': self.timestep,
            'is_leap_year': self.is_leap_year
        }
        if not self.is_annual:
            dts = self.direct_normal_irradiance.datetimes
            base['datetimes'] = [dat.to_array() for dat in dts]
        return base

    def to_file_string(self):
        """Get a text string for the entirety of the Wea file contents."""
        lines = [self.header]
        for dir_rad, dif_rad, dt in zip(self.direct_normal_irradiance,
                                        self.diffuse_horizontal_irradiance,
                                        self.datetimes):
            line = "%d %d %.3f %d %d\n" \
                % (dt.month, dt.day, dt.float_hour, dir_rad, dif_rad)
            lines.append(line)
        return ''.join(lines)

    def write(self, file_path, write_hours=False):
        """Write the Wea object to a .wea file and return the file path.

        Args:
            file_path: Text string for the path to where the .wea file should be written.
            write_hours: Boolean to note whether a .hrs file should be written
                next to the .wea file, which lists the hours of the year (hoys)
                contained within the .wea file.
        """
        # write the .wea file
        if not file_path.lower().endswith('.wea'):
            file_path += '.wea'
        file_data = self.to_file_string()
        write_to_file(file_path, file_data, True)

        # write the .hrs file if requested
        if write_hours:
            hrs_file_path = file_path[:-4] + '.hrs'
            hrs_data = ','.join(str(h) for h in self.hoys) + '\n'
            write_to_file(hrs_file_path, hrs_data, True)
        return file_path

    def duplicate(self):
        """Duplicate location."""
        return self.__copy__()

    @staticmethod
    def to_constant_value(wea_file, value=1000):
        """Convert a Wea file to have a constant value for each datetime.

        This is useful in workflows where hourly irradiance values are inconsequential
        to the analysis and one is only using the Wea as a format to pass location
        and datetime information (eg. for direct sun hours).

        Args:
            wea_file: Full path to .wea file.
            value: The direct and diffuse irradiance value that will be written
                in for all datetimes of the Wea.

        Returns:
            Text string of Wea file contents with all irradiance values replaces
            with the input value.
        """
        assert os.path.isfile(wea_file), 'Failed to find {}'.format(wea_file)
        new_lines, value = [], str(int(value))
        with open(wea_file, readmode) as weaf:
            for i in range(6):
                new_lines.append(weaf.readline())
            for line in weaf:
                vals = line.split()
                vals[-2], vals[-1] = value, value
                new_lines.append(' '.join(vals) + '\n')
        return ''.join(new_lines)

    @staticmethod
    def count_timesteps(wea_file):
        """Count the number of timesteps represented within a Wea file.

        This is useful in workflows where one needs to compute cumulative values
        over a Wea (eg. cumulative radiation).

        Args:
            wea_file: Full path to .wea file.

        Returns:
            integer for the number of timesteps in the Wea.
        """
        assert os.path.isfile(wea_file), 'Failed to find {}'.format(wea_file)
        with open(wea_file, readmode) as weaf:
            count = len(weaf.readlines()) - 6
        return count

    def _aligned_collection(self, header, values):
        """Process a header and values into a collection aligned with Wea data."""
        if self.is_continuous:
            return HourlyContinuousCollection(header, values)
        else:
            dts = self.direct_normal_irradiance.datetimes
            return HourlyDiscontinuousCollection(header, values, dts)

    @staticmethod
    def _get_datetimes(timestep, is_leap_year):
        """Get a list of annual datetimes based on timestep.

        This method should only be used for classmethods. For datetimes use
        datetimes or hoys methods.
        """
        hour_count = 8760 + 24 if is_leap_year else 8760
        adjust_time = 30 if timestep == 1 else 0
        return tuple(
            DateTime.from_moy(60.0 * count / timestep + adjust_time, is_leap_year)
            for count in xrange(hour_count * timestep)
        )

    @staticmethod
    def _get_data_collections(dnr_values, dhr_values, metadata, timestep, is_leap_year):
        """Return two annual data collections for Direct Normal, Diffuse Horizontal."""
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

    @staticmethod
    def _parse_wea_header(weaf, wea_file_name):
        """Parse the Ladybug location from a wea header given the wea file object."""
        first_line = weaf.readline()
        assert first_line.startswith('place'), 'Failed to find place in .wea header.\n' \
            '{} is not a valid wea file.'.format(wea_file_name)
        location = Location()
        location.city = ' '.join(first_line.split()[1:])
        location.latitude = float(weaf.readline().split()[-1])
        location.longitude = -float(weaf.readline().split()[-1])
        location.time_zone = -int(weaf.readline().split()[-1]) / 15
        location.elevation = float(weaf.readline().split()[-1])
        weaf.readline()  # pass line for weather data units
        return location

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __len__(self):
        return len(self.direct_normal_irradiance)

    def __getitem__(self, key):
        return self.direct_normal_irradiance[key], \
            self.diffuse_horizontal_irradiance[key]

    def __iter__(self):
        return zip(self.direct_normal_irradiance.values,
                   self.diffuse_horizontal_irradiance.values)

    def __key(self):
        return self.location, self.direct_horizontal_irradiance, \
            self.diffuse_horizontal_irradiance

    def __eq__(self, other):
        return isinstance(other, Wea) and self.__key() == other.__key()

    def __ne__(self, value):
        return not self.__eq__(value)

    def __copy__(self):
        new_wea = Wea(
            self.location.duplicate(),
            self.direct_normal_irradiance.duplicate(),
            self.diffuse_horizontal_irradiance.duplicate()
        )
        new_wea._enforce_on_hour = self._enforce_on_hour
        new_wea.metadata = deepcopy(self.metadata)
        return new_wea

    def __repr__(self):
        """Wea object representation."""
        return "WEA [%s]" % self.location.city
