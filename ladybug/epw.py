# coding=utf-8
from __future__ import division

import os
import math

from ladybug_geometry.geometry2d.pointvector import Vector2D

from .dt import Date
from .analysisperiod import AnalysisPeriod
from .datacollection import HourlyContinuousCollection
from .datacollection import MonthlyCollection
from .datatype import angle, distance, energyflux, energyintensity, generic, \
    illuminance, luminance, fraction, pressure, speed, temperature
from .designday import DesignDay
from .ddy import DDY
from .futil import write_to_file
from .header import Header
from .location import Location
from .climatezone import ashrae_climate_zone
from .skymodel import calc_sky_temperature
from .psychrometrics import rel_humid_from_db_dpt, wet_bulb_from_db_rh

readmode = 'rb'
try:
    from itertools import izip as zip  # python 2
except ImportError:
    xrange = range  # python 3
    readmode = 'r'


class EPW(object):
    """An EPW object containing all of the data of an .epw file.

    Most of the data available in the EPW will be accessible through objects
    that house various properties (eg. Location). All timeseries data sets are
    represented as HourlyContinuousCollection objects with values and datetimes
    corresponding to those in the EPW file.

    In order to handle the fact that EPW values run from 1:00 on Jan 1 to
    midnight of the following year, all timeseries data will have the ending
    value moved to the start of the hourly data collection upon import from
    the .epw file to an EPW object. This ensures that the datetimes of the data
    collections align with the times listed in the .epw file. This also allows
    the use of "true" datetimes in the hourly data collections, which start from
    0:00 rather than ending with 24:00. When saving the data from a EPW object
    back to an .epw file, the start date time at 0:00 on Jan 1 will be moved to
    the end of the file, ensuring imported .epw files can be saved back to their
    original state without any loss of data.

    The only exceptions to this movement of the last datetime are the timeseries
    data sets for radiation and illuminance. These data sets are left as they are
    when imported/exported to/from the .epw file given that they are meant to
    be an accumulation or average over the previous hour in the .epw file.
    Accordingly, such values can be thought of as an accumulation or average over
    the following hour when they are found within an hourly data collection of
    an EPW object. So the radiation with the 12:00 datetime in the hourly data
    collection represents the accumulated radiation in between 12:00 and 13:00.

    Args:
        file_path: Local file address to an .epw file.

    Properties:
        * location
        * annual_heating_design_day_996
        * annual_heating_design_day_990
        * annual_cooling_design_day_004
        * annual_cooling_design_day_010
        * heating_design_condition_dictionary
        * cooling_design_condition_dictionary
        * extreme_design_condition_dictionary
        * extreme_hot_weeks
        * extreme_cold_weeks
        * typical_weeks
        * ashrae_climate_zone
        * monthly_ground_temperature
        * header

        * years
        * dry_bulb_temperature
        * dew_point_temperature
        * relative_humidity
        * atmospheric_station_pressure
        * extraterrestrial_horizontal_radiation
        * extraterrestrial_direct_normal_radiation
        * horizontal_infrared_radiation_intensity
        * global_horizontal_radiation
        * direct_normal_radiation
        * diffuse_horizontal_radiation
        * global_horizontal_illuminance
        * direct_normal_illuminance
        * diffuse_horizontal_illuminance
        * zenith_luminance
        * wind_direction
        * wind_speed
        * total_sky_cover
        * opaque_sky_cover
        * visibility
        * ceiling_height
        * present_weather_observation
        * present_weather_codes
        * precipitable_water
        * aerosol_optical_depth
        * snow_depth
        * days_since_last_snowfall
        * albedo
        * liquid_precipitation_depth
        * liquid_precipitation_quantity
        * sky_temperature
    """
    __slots__ = ('_file_path', '_is_header_loaded', '_is_data_loaded', '_is_ip',
                 '_data', '_metadata', '_location',
                 '_heating_dict', '_cooling_dict', '_extremes_dict',
                 '_extreme_hot_weeks', '_extreme_cold_weeks', '_typical_weeks',
                 '_monthly_ground_temps', '_is_leap_year', 'daylight_savings_start',
                 'daylight_savings_end', '_num_of_fields', 'comments_1', 'comments_2')

    def __init__(self, file_path):
        """Initialize an EPW object from from a local .epw file.
        """
        self._file_path = os.path.normpath(file_path) if file_path is not None else None
        self._is_header_loaded = False
        self._is_data_loaded = False
        self._is_ip = False  # track if collections have been converted to IP

        # placeholders for the EPW data that will be imported
        self._data = []
        self._metadata = {}
        self._heating_dict = {}
        self._cooling_dict = {}
        self._extremes_dict = {}
        self._extreme_hot_weeks = {}
        self._extreme_cold_weeks = {}
        self._typical_weeks = {}
        self._monthly_ground_temps = {}
        self._is_leap_year = False
        self.daylight_savings_start = '0'
        self.daylight_savings_end = '0'
        self.comments_1 = ''
        self.comments_2 = ''
        self._num_of_fields = 35  # it is 35 for TMY3 files

    @classmethod
    def from_file_string(cls, file_contents):
        """Initialize an EPW object from a string containing all EPW file contents.

        This classmethod is intended for workflows where ladybug does not have
        access to a file system (eg. within a web browser).

        Args:
            file_contents: A text string for the entirety of the EPW file contents.
        """
        # Initialize the class with all data missing and split the file contents
        epw_obj = cls(None)
        all_lines = file_contents.split('\n')

        # parse the EPW header from the file contents
        epw_obj._import_location(all_lines[0])
        epw_obj._import_header(all_lines[:8])

        # import the body of the data to the object
        epw_obj._import_body(all_lines[8:-1])
        return epw_obj

    @classmethod
    def from_missing_values(cls, is_leap_year=False):
        """Initialize an EPW object with all data missing or empty.

        Note that this classmethod is intended for workflows where one plans
        to set all of the data within the EPW object.  The EPW file written
        out from the use of this method is not simulate-abe or useful since
        all hourly data slots just possess the missing value for that data
        type. To obtain a EPW that is simulate-able in EnergyPlus, one must
        at least set the following properties:

        * location
        * dry_bulb_temperature
        * dew_point_temperature
        * relative_humidity
        * atmospheric_station_pressure
        * direct_normal_radiation
        * diffuse_horizontal_radiation
        * wind_direction
        * wind_speed
        * total_sky_cover
        * opaque_sky_cover or horizontal_infrared_radiation_intensity

        Args:
            is_leap_year: A boolean to set whether the EPW object is for a leap year.

        Usage:

        .. code-block:: python

            from ladybug.epw import EPW
            from ladybug.location import Location
            epw = EPW.from_missing_values()
            epw.location = Location('Denver Golden','CO','USA',39.74,-105.18,-7.0,1829.0)
            epw.dry_bulb_temperature.values = [20] * 8760
        """
        # Initialize the class with all data missing
        epw_obj = cls(None)
        epw_obj._is_leap_year = is_leap_year
        epw_obj._location = Location()

        # create an annual analysis period
        analysis_period = AnalysisPeriod(is_leap_year=is_leap_year)

        # create headers and an empty list for each field in epw file
        headers = []
        for field_number in xrange(epw_obj._num_of_fields):
            field = EPWFields.field_by_number(field_number)
            header = Header(data_type=field.name, unit=field.unit,
                            analysis_period=analysis_period)
            headers.append(header)
            epw_obj._data.append([])

        # fill in missing datetime values and uncertainty flags.
        uncertainty = '?9?9?9?9E0?9?9?9?9?9?9?9?9?9?9?9?9?9?9?9*9*9?9?9?9'
        for dt in analysis_period.datetimes:
            if dt.hour != 0:
                hr, dy = dt.hour, dt.day
            else:
                hr = 24
                try:
                    dt = dt.sub_hour(24)
                    dy = dt.day
                except ValueError:  # negative datetime for the year; it's 31 Dec
                    dy = 31
            epw_obj._data[0].append(dt.year)
            epw_obj._data[1].append(dt.month)
            epw_obj._data[2].append(dy)
            epw_obj._data[3].append(hr)
            epw_obj._data[4].append(0)
            epw_obj._data[5].append(uncertainty)

        # generate missing hourly data
        calc_length = len(analysis_period.datetimes)
        for field_number in xrange(6, epw_obj._num_of_fields):
            field = EPWFields.field_by_number(field_number)
            mis_val = field.missing if field.missing is not None else 0
            for dt in xrange(calc_length):
                epw_obj._data[field_number].append(mis_val)

        # finally, build the data collection objects from the headers and data
        for i in xrange(epw_obj._num_of_fields):
            epw_obj._data[i] = HourlyContinuousCollection(headers[i], epw_obj._data[i])

        epw_obj._is_header_loaded = True
        epw_obj._is_data_loaded = True
        return epw_obj

    @classmethod
    def from_dict(cls, data):
        """ Create EPW from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

                {
                "location": {} ,  # ladybug location schema
                "data_collections": [],  # list of hourly annual hourly data collection
                    # schemas for each of the 35 fields within the EPW file.
                "metadata": {},  # dict of metadata assigned to all data collections
                "heating_dict": {},  # dict containing heating design conditions
                "cooling_dict": {},  # dict containing cooling design conditions
                "extremes_dict": {},  # dict containing extreme design conditions
                "extreme_hot_weeks": {},  # dict with values of week-long ladybug
                    # analysis period schemas signifying extreme hot weeks.
                "extreme_cold_weeks": {},  # dict with values of week-long ladybug
                    # analysis period schemas signifying extreme cold weeks.
                "typical_weeks": {},  # dict with values of week-long ladybug
                    # analysis period schemas signifying typical weeks.
                "monthly_ground_temps": {},  # dict with keys as floats signifying
                    # depths in meters below ground and values of monthly
                    # collection schema
                "is_ip": False  # Boolean // denote whether the data is in IP units
                "is_leap_year": False  # Boolean, denote whether data is for
                                       # a leap year
                "daylight_savings_start": 0,  # signify when daylight savings starts
                                              # or 0 for no daylight savings
                "daylight_savings_end" 0,  # signify when daylight savings ends
                                           # or 0 for no daylight savings
                "comments_1": ""  # String, epw comments
                "comments_2": ""  # String, epw comments
                }
        """
        # Initialize the class with all data missing
        epw_obj = cls(None)
        epw_obj._is_header_loaded = True
        epw_obj._is_data_loaded = True

        # Check required and optional keys
        required_keys = ('location', 'data_collections')
        option_keys_dict = ('metadata', 'heating_dict', 'cooling_dict',
                            'extremes_dict', 'extreme_hot_weeks', 'extreme_cold_weeks',
                            'typical_weeks', 'monthly_ground_temps')
        for key in required_keys:
            assert key in data, 'Required key "{}" is missing!'.format(key)
        assert len(data['data_collections']) == epw_obj._num_of_fields, \
            'The number of data_collections must be {}. Got {}.'.format(
                epw_obj._num_of_fields, len(data['data_collections']))
        for key in option_keys_dict:
            if key not in data:
                data[key] = {}

        # Set the required properties of the EPW object.
        epw_obj._location = Location.from_dict(data['location'])
        epw_obj._data = [HourlyContinuousCollection.from_dict(dc)
                         for dc in data['data_collections']]
        if 'is_leap_year' in data:
            epw_obj._is_leap_year = data['is_leap_year']
        if 'is_ip' in data:
            epw_obj._is_ip = data['is_ip']

        # Check that the required properties all make sense.
        for dc in epw_obj._data:
            assert isinstance(dc, HourlyContinuousCollection), 'data_collections must ' \
                'be of HourlyContinuousCollection schema. Got {}'.format(type(dc))
            assert dc.header.analysis_period.is_annual, 'data_collections ' \
                'analysis_period must be annual.'
            assert dc.header.analysis_period.is_leap_year == epw_obj._is_leap_year, \
                'data_collections is_leap_year is not aligned with that of the EPW.'

        # Set all of the header properties if they exist in the dictionary.
        epw_obj._metadata = data['metadata']
        epw_obj.heating_design_condition_dictionary = data['heating_dict']
        epw_obj.cooling_design_condition_dictionary = data['cooling_dict']
        epw_obj.extreme_design_condition_dictionary = data['extremes_dict']

        def _dedict(parent_dict, obj):
            new_dict = {}
            for key, val in parent_dict.items():
                new_dict[key] = obj.from_dict(val)
            return new_dict
        epw_obj.extreme_hot_weeks = _dedict(data['extreme_hot_weeks'], AnalysisPeriod)
        epw_obj.extreme_cold_weeks = _dedict(data['extreme_cold_weeks'], AnalysisPeriod)
        epw_obj.typical_weeks = _dedict(data['typical_weeks'], AnalysisPeriod)
        epw_obj.monthly_ground_temperature = _dedict(
            data['monthly_ground_temps'], MonthlyCollection)

        if 'daylight_savings_start' in data:
            epw_obj.daylight_savings_start = data['daylight_savings_start']
        if 'daylight_savings_end' in data:
            epw_obj.daylight_savings_end = data['daylight_savings_end']
        if 'comments_1' in data:
            epw_obj.comments_1 = data['comments_1']
        if 'comments_2' in data:
            epw_obj.comments_2 = data['comments_2']

        return epw_obj

    def _import_data(self, import_header_only=False):
        """Import data from an epw file.

        Hourly data will be saved in self.data and the various header data
        will be saved in the properties above.
        """
        # perform checks on the file before opening it.
        assert os.path.isfile(self._file_path), 'Cannot find an epw file at {}'.format(
            self._file_path)
        assert self._file_path.lower().endswith('epw'), '{} is not an .epw file. \n' \
            'It does not possess the .epw file extension.'.format(self._file_path)

        try:
            with open(self._file_path, readmode) as epwin:
                # import the header data to the object
                line = epwin.readline()
                original_header_load = bool(self._is_header_loaded)
                if not self._is_header_loaded:
                    self._import_location(line)
                    header_lines = [line] + [epwin.readline() for i in xrange(7)]
                    self._import_header(header_lines)
                if import_header_only:
                    return

                # import the body of the data to the object
                if original_header_load:
                    for _ in xrange(7):
                        epwin.readline()
                body_lines = []
                while line:
                    line = epwin.readline()
                    body_lines.append(line)
                del body_lines[-1]  # last line is a blank space
                self._import_body(body_lines)
        except UnicodeDecodeError:  # let's hope it's just latin characters
            # TODO: do a better job of trying to sense the encoding
            with open(self._file_path, readmode, errors='ignore') as epwin:
                # import the header data to the object
                line = epwin.readline()
                original_header_load = bool(self._is_header_loaded)
                if not self._is_header_loaded:
                    self._import_location(line)
                    header_lines = [line] + [epwin.readline() for i in xrange(7)]
                    self._import_header(header_lines)
                if import_header_only:
                    return

                # import the body of the data to the object
                if original_header_load:
                    for _ in xrange(7):
                        epwin.readline()
                body_lines = []
                while line:
                    line = epwin.readline()
                    body_lines.append(line)
                del body_lines[-1]  # last line is a blank space
                self._import_body(body_lines)

    def _import_location(self, line):
        """Set the EPW location from the first line of the EPW.

        Here's an example.
        LOCATION,Denver Golden Nr,CO,USA,TMY3,724666,39.74,-105.18,-7.0,1829.0
        """
        # import location data
        location_data = line.strip().split(',')
        self._location = Location()
        self._location.city = location_data[1].replace('\\', ' ') \
            .replace('/', ' ')
        self._location.state = location_data[2]
        self._location.country = location_data[3]
        self._location.source = location_data[4]
        self._location.station_id = location_data[5]
        self._location.latitude = location_data[6]
        self._location.longitude = location_data[7]
        self._location.time_zone = location_data[8]
        self._location.elevation = location_data[9]

        # assemble a dictionary of metadata
        self._metadata = {
            'source': self._location.source,
            'country': self._location.country,
            'city': self._location.city,
            'time-zone': self._location.time_zone
        }

    def _import_header(self, header_lines):
        """Set EPW design days, typical weeks, and ground temperatures from header lines.
        """
        # parse the heating, cooling and extreme design conditions.
        dday_data = header_lines[1].strip().split(',')
        if len(dday_data) >= 2 and int(dday_data[1]) == 1:
            if dday_data[4] == 'Heating':
                for key, val in zip(DesignDay.HEATING_KEYS, dday_data[5:20]):
                    self._heating_dict[key] = val
            if dday_data[20] == 'Cooling':
                for key, val in zip(DesignDay.COOLING_KEYS, dday_data[21:53]):
                    self._cooling_dict[key] = val
            if dday_data[53] == 'Extremes':
                for key, val in zip(DesignDay.EXTREME_KEYS, dday_data[54:70]):
                    self._extremes_dict[key] = val

        # parse typical and extreme periods into analysis periods.
        week_data = header_lines[2].split(',')
        num_weeks = int(week_data[1]) if len(week_data) >= 2 \
            and week_data[1] != '' else 0
        st_ind = 2
        for _ in xrange(num_weeks):
            week_dat = week_data[st_ind:st_ind + 4]
            st_ind += 4
            st = [int(num) for num in week_dat[2].split('/')]
            end = [int(num) for num in week_dat[3].split('/')]
            if len(st) == 3:
                a_per = AnalysisPeriod(st[1], st[2], 0, end[1], end[2], 23)
            elif len(st) == 2:
                a_per = AnalysisPeriod(st[0], st[1], 0, end[0], end[1], 23)
            if 'Max' in week_dat[0] and week_dat[1] == 'Extreme':
                self._extreme_hot_weeks[week_dat[0]] = a_per
            elif 'Min' in week_dat[0] and week_dat[1] == 'Extreme':
                self._extreme_cold_weeks[week_dat[0]] = a_per
            elif week_dat[1] == 'Typical':
                self._typical_weeks[week_dat[0]] = a_per

        # parse the monthly ground temperatures in the header.
        grnd_data = header_lines[3].strip().split(',')
        num_depths = int(grnd_data[1]) if len(grnd_data) >= 2 \
            and grnd_data[1] != '' else 0
        st_ind = 2
        for _ in xrange(num_depths):
            header_meta = dict(self._metadata)  # copying the metadata dictionary
            header_meta['depth'] = float(grnd_data[st_ind])
            header_meta['soil conductivity'] = grnd_data[st_ind + 1]
            header_meta['soil density'] = grnd_data[st_ind + 2]
            header_meta['soil specific heat'] = grnd_data[st_ind + 3]
            grnd_header = Header(temperature.GroundTemperature(), 'C',
                                 AnalysisPeriod(), header_meta)
            grnd_vals = [float(x) for x in grnd_data[st_ind + 4: st_ind + 16]]
            self._monthly_ground_temps[float(grnd_data[st_ind])] = \
                MonthlyCollection(grnd_header, grnd_vals, list(xrange(12)))
            st_ind += 16

        # parse leap year, daylight savings and comments.
        leap_dl_sav = header_lines[4].strip().split(',')
        self._is_leap_year = True if leap_dl_sav[1] == 'Yes' else False
        self.daylight_savings_start = leap_dl_sav[2]
        self.daylight_savings_end = leap_dl_sav[3]
        comments_1 = header_lines[5].strip().split(',')
        if len(comments_1) > 0:
            self.comments_1 = ','.join(comments_1[1:])
        comments_2 = header_lines[6].strip().split(',')
        if len(comments_2) > 0:
            self.comments_2 = ','.join(comments_2[1:])

        self._is_header_loaded = True

    def _import_body(self, body_lines):
        """Set all of the EPW data collections by parsing from the body lines."""
        # get the number of fields and make an annual analysis period
        self._num_of_fields = min(len(body_lines[0].strip().split(',')), 35)
        analysis_period = AnalysisPeriod(is_leap_year=self.is_leap_year)

        # create headers and an empty list for each field in epw file
        headers = []
        for field_number in xrange(self._num_of_fields):
            field = EPWFields.field_by_number(field_number)
            header = Header(data_type=field.name, unit=field.unit,
                            analysis_period=analysis_period,
                            metadata=dict(self._metadata))
            headers.append(header)
            self._data.append([])

        # parse the hourly data
        msg_template = 'Failed to parse EPW data for field "{}" at index {}.\n{}'
        for x, line in enumerate(body_lines):
            l_strip = line.strip()
            if not l_strip:  # blank line
                continue
            data = l_strip.split(',')
            for field_number in xrange(self._num_of_fields):
                value_type = EPWFields.field_by_number(field_number).value_type
                try:
                    value = value_type(data[field_number])
                except ValueError as e:
                    # failed to cast the data to the correct type
                    if value_type != int:  # possibly an int to convert to float first
                        msg = msg_template.format(headers[field_number].data_type, x, e)
                        raise ValueError(msg)
                    try:
                        value = int(round(float(data[field_number])))
                    except ValueError:
                        msg = msg_template.format(headers[field_number].data_type, x, e)
                        raise ValueError(msg)
                self._data[field_number].append(value)

        # if the first value is at 1 AM, move last item to start position
        for field_number in xrange(self._num_of_fields):
            point_in_time = headers[field_number].data_type.point_in_time
            if point_in_time:
                # move the last hour to first position
                last_hour = self._data[field_number].pop()
                self._data[field_number].insert(0, last_hour)

        # finally, build the data collection objects from the headers and data
        for i in xrange(self._num_of_fields):
            self._data[i] = HourlyContinuousCollection(headers[i], self._data[i])
        self._is_data_loaded = True

    @property
    def file_path(self):
        """Get path to epw file."""
        return self._file_path

    @property
    def is_header_loaded(self):
        """Return True if location data is loaded."""
        return self._is_header_loaded

    @property
    def is_data_loaded(self):
        """Return True if weather data is loaded."""
        return self._is_data_loaded

    @property
    def is_ip(self):
        """Returns True if the data collections of this file are in IP units."""
        return self._is_ip

    @property
    def location(self):
        """Return location data."""
        self._load_header_check()
        return self._location

    @location.setter
    def location(self, loc):
        self._load_header_check()
        assert isinstance(loc, Location), 'location' \
            'must be a Location object. Got {}.'.format(type(loc))
        self._location = loc

    @property
    def metadata(self):
        """Dictionary of metadata written to DataCollection headers.

        Keys typically include "source", "country", and "city").
        """
        self._load_header_check()
        return self._metadata

    @metadata.setter
    def metadata(self, meta_d):
        self._load_header_check()
        assert isinstance(meta_d, dict), 'metadata' \
            'must be a dictionary. Got {}.'.format(type(meta_d))
        self._metadata = meta_d
        for coll in self._data:
            coll.header._metadata = meta_d

    @property
    def annual_heating_design_day_996(self):
        """A design day object representing the annual 99.6% heating design day."""
        self._load_header_check()
        if bool(self._heating_dict):
            avg_press = self.atmospheric_station_pressure.average
            avg_press = None if avg_press == 999999 else avg_press
            return DesignDay.from_ashrae_dict_heating(
                self._heating_dict, self.location, False, avg_press)
        else:
            return None

    @property
    def annual_heating_design_day_990(self):
        """A design day object representing the annual 99.0% heating design day."""
        self._load_header_check()
        if bool(self._heating_dict):
            avg_press = self.atmospheric_station_pressure.average
            avg_press = None if avg_press == 999999 else avg_press
            return DesignDay.from_ashrae_dict_heating(
                self._heating_dict, self.location, True, avg_press)
        else:
            return None

    @property
    def annual_cooling_design_day_004(self):
        """A design day object representing the annual 0.4% cooling design day."""
        self._load_header_check()
        if bool(self._cooling_dict):
            avg_press = self.atmospheric_station_pressure.average
            avg_press = None if avg_press == 999999 else avg_press
            return DesignDay.from_ashrae_dict_cooling(
                self._cooling_dict, self.location, False, avg_press)
        else:
            return None

    @property
    def annual_cooling_design_day_010(self):
        """A design day object representing the annual 1.0% cooling design day."""
        self._load_header_check()
        if bool(self._cooling_dict):
            avg_press = self.atmospheric_station_pressure.average
            avg_press = None if avg_press == 999999 else avg_press
            return DesignDay.from_ashrae_dict_cooling(
                self._cooling_dict, self.location, True, avg_press)
        else:
            return None

    @property
    def heating_design_condition_dictionary(self):
        """Dictionary with ASHRAE HOF Climate Design Data for heating conditions."""
        self._load_header_check()
        return self._heating_dict

    @heating_design_condition_dictionary.setter
    def heating_design_condition_dictionary(self, des_dict):
        self._load_header_check()
        self._des_dict_check(des_dict, DesignDay.HEATING_KEYS,
                             'heating_design_condition_dictionary')
        self._heating_dict = des_dict

    @property
    def cooling_design_condition_dictionary(self):
        """Dictionary with ASHRAE HOF Climate Design Data for cooling conditions."""
        self._load_header_check()
        return self._cooling_dict

    @cooling_design_condition_dictionary.setter
    def cooling_design_condition_dictionary(self, des_dict):
        self._load_header_check()
        self._des_dict_check(des_dict, DesignDay.COOLING_KEYS,
                             'cooling_design_condition_dictionary')
        self._cooling_dict = des_dict

    @property
    def extreme_design_condition_dictionary(self):
        """Dictionary with ASHRAE HOF Climate Design Data for extreme conditions."""
        self._load_header_check()
        return self._extremes_dict

    @extreme_design_condition_dictionary.setter
    def extreme_design_condition_dictionary(self, des_dict):
        self._load_header_check()
        self._des_dict_check(des_dict, DesignDay.EXTREME_KEYS,
                             'extreme_design_condition_dictionary')
        self._extremes_dict = des_dict

    @property
    def extreme_cold_weeks(self):
        """A dictionary with AnalysisPeriods for the coldest weeks within the EPW."""
        self._load_header_check()
        self._extreme_cold_weeks.values()
        return self._extreme_cold_weeks

    @extreme_cold_weeks.setter
    def extreme_cold_weeks(self, data):
        self._load_header_check()
        self._weeks_check(data, 'extreme_cold_weeks')
        self._extreme_cold_weeks = dict(data)

    @property
    def extreme_hot_weeks(self):
        """A dictionary with AnalysisPeriods for the hottest week within the EPW."""
        self._load_header_check()
        return self._extreme_hot_weeks

    @extreme_hot_weeks.setter
    def extreme_hot_weeks(self, data):
        self._load_header_check()
        self._weeks_check(data, 'extreme_hot_weeks')
        self._extreme_hot_weeks = data

    @property
    def typical_weeks(self):
        """A dictionary with AnalysisPeriods for the typical weeks within the EPW."""
        self._load_header_check()
        return self._typical_weeks

    @typical_weeks.setter
    def typical_weeks(self, data):
        self._load_header_check()
        self._weeks_check(data, 'typical_weeks')
        self._typical_weeks = data

    @property
    def ashrae_climate_zone(self):
        """Text for the ASHRAE climate zone, estimated from the dry bulb temperature.

        Note that all climate zones that should have a "B" will have an "A" for
        this property because EPW files almost never have correct precipitation
        data. If accurate precipitation data is available from another source, the
        ashrae_climate_zone method in the climatezone module should be used instead.
        """
        return ashrae_climate_zone(self.dry_bulb_temperature)

    @property
    def monthly_ground_temperature(self):
        """Return a dictionary of Monthly Data collections.

        The keys of this dictionary are the depths at which each set
        of temperatures occurs."""
        self._load_header_check()
        return self._monthly_ground_temps

    @monthly_ground_temperature.setter
    def monthly_ground_temperature(self, data):
        self._load_header_check()
        assert isinstance(data, dict), 'monthly_ground_temperature' \
            ' must be an OrderedDict. Got {}.'.format(type(data))
        if bool(data):
            for val in data.values():
                assert isinstance(val, MonthlyCollection), 'monthly_ground_temperature' \
                    ' must contain MonthlyCollection objects. Got {}.'.format(type(val))
        self._monthly_ground_temps = data

    @property
    def is_leap_year(self):
        """Boolean to denote whether the EPW is a leap year or not."""
        self._load_header_check()
        return self._is_leap_year

    def _load_header_check(self):
        """Check if data is loaded and, if not load it."""
        if not self.is_header_loaded:
            self._import_data(import_header_only=True)

    def _des_dict_check(self, des_dict, req_keys, cond_name):
        """Check if an input design condition dictionary is acceptable."""
        assert isinstance(des_dict, dict), '{}' \
            ' must be a dictionary. Got {}.'.format(cond_name, type(des_dict))
        if bool(des_dict):
            input_keys = list(des_dict.keys())
            for key in req_keys:
                assert key in input_keys, 'Required key "{}" was not found in ' \
                    '{}'.format(key, cond_name)

    def _weeks_check(self, data, week_type):
        """Check if input for the typical/extreme weeks of the header is correct."""
        assert isinstance(data, dict), '{}' \
            ' must be an OrderedDict. Got {}.'.format(week_type, type(data))
        if bool(data):
            for val in data.values():
                assert isinstance(val, AnalysisPeriod), '{} dictionary must contain' \
                    ' AnalysisPeriod objects. Got {}.'.format(week_type, type(val))
                assert len(val.doys_int) == 7, '{} AnalysisPeriod must be for'\
                    ' a week.  Got AnalysisPeriod for {} days.'.format(
                        week_type, type(val))

    @property
    def header(self):
        """A list of text representing the full header (the first 8 lines) of the EPW."""
        self._load_header_check()
        loc = self.location
        loc_str = 'LOCATION,{},{},{},{},{},{},{},{},{}\n'.format(
            loc.city, loc.state, loc.country, loc.source, loc.station_id, loc.latitude,
            loc.longitude, loc.time_zone, loc.elevation)
        winter_found = bool(self._heating_dict)
        summer_found = bool(self._cooling_dict)
        extreme_found = bool(self._extremes_dict)
        if winter_found and summer_found and extreme_found:
            des_str = 'DESIGN CONDITIONS,1,Climate Design Data 2009 ASHRAE Handbook,,'
            des_str = des_str + 'Heating,{},Cooling,{},Extremes,{}\n'.format(
                ','.join([self._heating_dict[key] for key in DesignDay.HEATING_KEYS]),
                ','.join([self._cooling_dict[key] for key in DesignDay.COOLING_KEYS]),
                ','.join([self._extremes_dict[key] for key in DesignDay.EXTREME_KEYS]))
        else:
            des_str = 'DESIGN CONDITIONS,0\n'
        weeks = []
        if bool(self.extreme_hot_weeks):
            for wk_name, a_per in self.extreme_hot_weeks.items():
                weeks.append(self._format_week(wk_name, 'Extreme', a_per))
        if bool(self.extreme_cold_weeks):
            for wk_name, a_per in self.extreme_cold_weeks.items():
                weeks.append(self._format_week(wk_name, 'Extreme', a_per))
        if bool(self.typical_weeks):
            for wk_name in sorted(self.typical_weeks.keys()):
                a_per = self.typical_weeks[wk_name]
                weeks.append(self._format_week(wk_name, 'Typical', a_per))
        week_str = 'TYPICAL/EXTREME PERIODS,{},{}\n'.format(len(weeks), ','.join(weeks))
        grnd_st = 'GROUND TEMPERATURES,{}'.format(len(self._monthly_ground_temps.keys()))
        for depth in sorted(self._monthly_ground_temps.keys()):
            grnd_st = grnd_st + ',{},{}'.format(
                depth, self._format_ground_temp(self._monthly_ground_temps[depth]))
        grnd_st = grnd_st + '\n'
        leap_yr = 'Yes' if self._is_leap_year else 'No'
        leap_str = 'HOLIDAYS/DAYLIGHT SAVINGS,{},{},{},0\n'.format(
            leap_yr, self.daylight_savings_start, self.daylight_savings_end)
        c_str1 = 'COMMENTS 1,{}\n'.format(self.comments_1)
        c_str2 = 'COMMENTS 2,{}\n'.format(self.comments_2)
        data_str = 'DATA PERIODS,1,1,Data,Sunday, 1/ 1,12/31\n'
        return [loc_str, des_str, week_str, grnd_st, leap_str, c_str1, c_str2, data_str]

    def _format_week(self, name, type, a_per):
        """Format an AnalysisPeriod into string for the EPW header."""
        return '{},{},{}/{},{}/{}'.format(name, type, a_per.st_month, a_per.st_day,
                                          a_per.end_month, a_per.end_day)

    def _format_ground_temp(self, data_c):
        """Format monthly ground data collection into string for the EPW header."""
        monthly_str = '{},{},{},{}'.format(
            data_c.header.metadata['soil conductivity'],
            data_c.header.metadata['soil density'],
            data_c.header.metadata['soil specific heat'],
            ','.join(['%.2f' % x for x in data_c.values]))
        return monthly_str

    def _get_data_by_field(self, field_number):
        """Return a data field by field number.

        This is a useful method to get the values for fields that Ladybug
        currently doesn't import by default. You can find list of fields by typing
        EPWFields.fields

        Args:
            field_number: a value between 0 to 34 for different available epw fields.

        Returns:
            An annual Ladybug list
        """
        if not self.is_data_loaded:
            self._import_data()

        # check input data
        if not 0 <= field_number < self._num_of_fields:
            raise ValueError("Field number should be between 0-%d" % self._num_of_fields)

        return self._data[field_number]

    def import_data_by_field(self, field_number):
        """Return an annual data collection for any field_number in epw file.

        This is useful to get data for fields that the EPW object currently doesn't
        have properties for (eg. Uncertainty Flags). You can find list of fields
        by using EPWFields.fields.

        Args:
            field_number: A value between 0 to 34 for different available epw fields.

                *   0 Year
                *   1 Month
                *   2 Day
                *   3 Hour
                *   4 Minute
                *   5 Uncertainty Flags
                *   6 Dry Bulb Temperature
                *   7 Dew Point Temperature
                *   8 Relative Humidity
                *   9 Atmospheric Station Pressure
                *   10 Extraterrestrial Horizontal Radiation
                *   11 Extraterrestrial Direct Normal Radiation
                *   12 Horizontal Infrared Radiation Intensity
                *   13 Global Horizontal Radiation
                *   14 Direct Normal Radiation
                *   15 Diffuse Horizontal Radiation
                *   16 Global Horizontal Illuminance
                *   17 Direct Normal Illuminance
                *   18 Diffuse Horizontal Illuminance
                *   19 Zenith Luminance
                *   20 Wind Direction
                *   21 Wind Speed
                *   22 Total Sky Cover
                *   23 Opaque Sky Cover
                *   24 Visibility
                *   25 Ceiling Height
                *   26 Present Weather Observation
                *   27 Present Weather Codes
                *   28 Precipitable Water
                *   29 Aerosol Optical Depth
                *   30 Snow Depth
                *   31 Days Since Last Snowfall
                *   32 Albedo
                *   33 Liquid Precipitation Depth
                *   34 Liquid Precipitation Quantity

        Returns:
            An annual Ladybug list
        """
        return self._get_data_by_field(field_number)

    @property
    def years(self):
        """Return years as a Ladybug Data Collection."""
        return self._get_data_by_field(0)

    @property
    def dry_bulb_temperature(self):
        """Return annual Dry Bulb Temperature as a Ladybug Data Collection.

        This is the dry bulb temperature in C at the time indicated. Note that
        this is a full numeric field (i.e. 23.6) and not an integer representation
        with tenths. Valid values range from -70C to 70 C. Missing value for this
        field is 99.9.
        """
        return self._get_data_by_field(6)

    @property
    def dew_point_temperature(self):
        u"""Return annual Dew Point Temperature as a Ladybug Data Collection.

        This is the dew point temperature in C at the time indicated. Note that this is
        a full numeric field (i.e. 23.6) and not an integer representation with tenths.
        Valid values range from -70 C to 70 C. Missing value for this field is 99.9
        """
        return self._get_data_by_field(7)

    @property
    def relative_humidity(self):
        u"""Return annual Relative Humidity as a Ladybug Data Collection.

        This is the Relative Humidity in percent at the time indicated. Valid values
        range from 0% to 110%. Missing value for this field is 999.
        """
        return self._get_data_by_field(8)

    @property
    def atmospheric_station_pressure(self):
        """Return annual Atmospheric Station Pressure as a Ladybug Data Collection.

        This is the station pressure in Pa at the time indicated. Valid values range
        from 31,000 to 120,000. (These values were chosen from the standard barometric
        pressure for all elevations of the World). Missing value for this field is 999999
        """
        return self._get_data_by_field(9)

    @property
    def extraterrestrial_horizontal_radiation(self):
        """Return annual Extraterrestrial Horizontal Radiation as a Ladybug Data Collection.

        This is the Extraterrestrial Horizontal Radiation in Wh/m2. It is not currently
        used in EnergyPlus calculations. It should have a minimum value of 0; missing
        value for this field is 9999.
        """
        return self._get_data_by_field(10)

    @property
    def extraterrestrial_direct_normal_radiation(self):
        """Return annual Extraterrestrial Direct Normal Radiation as a Ladybug Data Collection.

        This is the Extraterrestrial Direct Normal Radiation in Wh/m2. (Amount of solar
        radiation in Wh/m2 received on a surface normal to the rays of the sun at the top
        of the atmosphere during the number of minutes preceding the time indicated).
        It is not currently used in EnergyPlus calculations. It should have a minimum
        value of 0; missing value for this field is 9999.
        """
        return self._get_data_by_field(11)

    @property
    def horizontal_infrared_radiation_intensity(self):
        """Return annual Horizontal Infrared Radiation Intensity as a Ladybug Data Collection.

        This is the Horizontal Infrared Radiation Intensity in W/m2. If it is missing,
        it is calculated from the Opaque Sky Cover field as shown in the following
        explanation. It should have a minimum value of 0; missing value for this field
        is 9999.
        """
        return self._get_data_by_field(12)

    @property
    def global_horizontal_radiation(self):
        """Return annual Global Horizontal Radiation as a Ladybug Data Collection.

        This is the Global Horizontal Radiation in Wh/m2. (Total amount of direct and
        diffuse solar radiation in Wh/m2 received on a horizontal surface during the
        number of minutes preceding the time indicated.) It is not currently used in
        EnergyPlus calculations. It should have a minimum value of 0; missing value
        for this field is 9999.
        """
        return self._get_data_by_field(13)

    @property
    def direct_normal_radiation(self):
        """Return annual Direct Normal Radiation as a Ladybug Data Collection.

        This is the Direct Normal Radiation in Wh/m2. (Amount of solar radiation in
        Wh/m2 received directly from the solar disk on a surface perpendicular to the
        sun's rays, during the number of minutes preceding the time indicated.) If the
        field is missing ( >= 9999) or invalid ( < 0), it is set to 0. Counts of such
        missing values are totaled and presented at the end of the runperiod.
        """
        return self._get_data_by_field(14)

    @property
    def diffuse_horizontal_radiation(self):
        """Return annual Diffuse Horizontal Radiation as a Ladybug Data Collection.

        This is the Diffuse Horizontal Radiation in Wh/m2. (Amount of solar radiation in
        Wh/m2 received from the sky (excluding the solar disk) on a horizontal surface
        during the number of minutes preceding the time indicated.) If the field is
        missing ( >= 9999) or invalid ( < 0), it is set to 0. Counts of such missing
        values are totaled and presented at the end of the runperiod
        """
        return self._get_data_by_field(15)

    @property
    def global_horizontal_illuminance(self):
        """Return annual Global Horizontal Illuminance as a Ladybug Data Collection.

        This is the Global Horizontal Illuminance in lux. (Average total amount of
        direct and diffuse illuminance in hundreds of lux received on a horizontal
        surface during the number of minutes preceding the time indicated.) It is not
        currently used in EnergyPlus calculations. It should have a minimum value of 0;
        missing value for this field is 999999 and will be considered missing if greater
        than or equal to 999900.
        """
        return self._get_data_by_field(16)

    @property
    def direct_normal_illuminance(self):
        """Return annual Direct Normal Illuminance as a Ladybug Data Collection.

        This is the Direct Normal Illuminance in lux. (Average amount of illuminance in
        hundreds of lux received directly from the solar disk on a surface perpendicular
        to the sun's rays, during the number of minutes preceding the time indicated.)
        It is not currently used in EnergyPlus calculations. It should have a minimum
        value of 0; missing value for this field is 999999 and will be considered missing
        if greater than or equal to 999900.
        """
        return self._get_data_by_field(17)

    @property
    def diffuse_horizontal_illuminance(self):
        """Return annual Diffuse Horizontal Illuminance as a Ladybug Data Collection.

        This is the Diffuse Horizontal Illuminance in lux. (Average amount of illuminance
        in hundreds of lux received from the sky (excluding the solar disk) on a
        horizontal surface during the number of minutes preceding the time indicated.)
        It is not currently used in EnergyPlus calculations. It should have a minimum
        value of 0; missing value for this field is 999999 and will be considered missing
        if greater than or equal to 999900.
        """
        return self._get_data_by_field(18)

    @property
    def zenith_luminance(self):
        """Return annual Zenith Luminance as a Ladybug Data Collection.

        This is the Zenith Illuminance in Cd/m2. (Average amount of luminance at
        the sky's zenith in tens of Cd/m2 during the number of minutes preceding
        the time indicated.) It is not currently used in EnergyPlus calculations.
        It should have a minimum value of 0; missing value for this field is 9999.
        """
        return self._get_data_by_field(19)

    @property
    def wind_direction(self):
        """Return annual Wind Direction as a Ladybug Data Collection.

        This is the Wind Direction in degrees where the convention is that North=0.0,
        East=90.0, South=180.0, West=270.0. (Wind direction in degrees at the time
        indicated. If calm, direction equals zero.) Values can range from 0 to 360.
        Missing value is 999.
        """
        return self._get_data_by_field(20)

    @property
    def wind_speed(self):
        """Return annual Wind Speed as a Ladybug Data Collection.

        This is the wind speed in m/sec. (Wind speed at time indicated.) Values can
        range from 0 to 40. Missing value is 999.
        """
        return self._get_data_by_field(21)

    @property
    def total_sky_cover(self):
        """Return annual Total Sky Cover as a Ladybug Data Collection.

        This is the value for total sky cover (tenths of coverage). (i.e. 1 is 1/10
        covered. 10 is total coverage). (Amount of sky dome in tenths covered by clouds
        or obscuring phenomena at the hour indicated at the time indicated.) Minimum
        value is 0; maximum value is 10; missing value is 99.
        """
        return self._get_data_by_field(22)

    @property
    def opaque_sky_cover(self):
        """Return annual Opaque Sky Cover as a Ladybug Data Collection.

        This is the value for opaque sky cover (tenths of coverage). (i.e. 1 is 1/10
        covered. 10 is total coverage). (Amount of sky dome in tenths covered by
        clouds or obscuring phenomena that prevent observing the sky or higher cloud
        layers at the time indicated.) This is not used unless the field for Horizontal
        Infrared Radiation Intensity is missing and then it is used to calculate
        Horizontal Infrared Radiation Intensity. Minimum value is 0; maximum value is
        10; missing value is 99.
        """
        return self._get_data_by_field(23)

    @property
    def visibility(self):
        """Return annual Visibility as a Ladybug Data Collection.

        This is the value for visibility in km. (Horizontal visibility at the time
        indicated.) It is not currently used in EnergyPlus calculations. Missing
        value is 9999.
        """
        return self._get_data_by_field(24)

    @property
    def ceiling_height(self):
        """Return annual Ceiling Height as a Ladybug Data Collection.

        This is the value for ceiling height in m. (77777 is unlimited ceiling height.
        88888 is cirroform ceiling.) It is not currently used in EnergyPlus calculations.
        Missing value is 99999
        """
        return self._get_data_by_field(25)

    @property
    def present_weather_observation(self):
        """Return annual Present Weather Observation as a Ladybug Data Collection.

        If the value of the field is 0, then the observed weather codes are taken from
        the following field. If the value of the field is 9, then "missing" weather is
        assumed. Since the primary use of these fields (Present Weather Observation and
        Present Weather Codes) is for rain/wet surfaces, a missing observation field or
        a missing weather code implies no rain.
        """
        return self._get_data_by_field(26)

    @property
    def present_weather_codes(self):
        """Return annual Present Weather Codes as a Ladybug Data Collection.

        The present weather codes field is assumed to follow the TMY2 conventions for
        this field. Note that though this field may be represented as numeric (e.g. in
        the CSV format), it is really a text field of 9 single digits. This convention
        along with values for each "column" (left to right) is presented in Table 16.
        Note that some formats (e.g. TMY) does not follow this convention - as much as
        possible, the present weather codes are converted to this convention during
        WeatherConverter processing. Also note that the most important fields are those
        representing liquid precipitation - where the surfaces of the building would be
        wet. EnergyPlus uses "Snow Depth" to determine if snow is on the ground.
        """
        return self._get_data_by_field(27)

    @property
    def precipitable_water(self):
        """Return annual Precipitable Water as a Ladybug Data Collection.

        This is the value for Precipitable Water in mm. (This is not rain - rain is
        inferred from the PresWeathObs field but a better result is from the Liquid
        Precipitation Depth field). It is not currently used in EnergyPlus calculations
        (primarily due to the unreliability of the reporting of this value). Missing
        value is 999.
        """
        return self._get_data_by_field(28)

    @property
    def aerosol_optical_depth(self):
        """Return annual Aerosol Optical Depth as a Ladybug Data Collection.

        This is the value for Aerosol Optical Depth in thousandths. It is not currently
        used in EnergyPlus calculations. Missing value is .999.
        """
        return self._get_data_by_field(29)

    @property
    def snow_depth(self):
        """Return annual Snow Depth as a Ladybug Data Collection.

        This is the value for Snow Depth in cm. This field is used to tell when snow
        is on the ground and, thus, the ground reflectance may change. Missing value
        is 999.
        """
        return self._get_data_by_field(30)

    @property
    def days_since_last_snowfall(self):
        """Return annual Days Since Last Snow Fall as a Ladybug Data Collection.

        This is the value for Days Since Last Snowfall. It is not currently used in
        EnergyPlus calculations. Missing value is 99.
        """
        return self._get_data_by_field(31)

    @property
    def albedo(self):
        """Return annual Albedo values as a Ladybug Data Collection.

        The ratio (unitless) of reflected solar irradiance to global horizontal
        irradiance. It is not currently used in EnergyPlus.
        """
        return self._get_data_by_field(32)

    @property
    def liquid_precipitation_depth(self):
        """Return annual liquid precipitation depth as a Ladybug Data Collection.

        The amount of liquid precipitation (mm) observed at the indicated time for the
        period indicated in the liquid precipitation quantity field. If this value is
        not missing, then it is used and overrides the "precipitation" flag as rainfall.
        Conversely, if the precipitation flag shows rain and this field is missing or
        zero, it is set to 1.5 (mm).
        """
        return self._get_data_by_field(33)

    @property
    def liquid_precipitation_quantity(self):
        """Return annual Liquid Precipitation Quantity as a Ladybug Data Collection.

        The period of accumulation (hr) for the liquid precipitation depth field.
        It is not currently used in EnergyPlus.
        """
        return self._get_data_by_field(34)

    @property
    def sky_temperature(self):
        """Return annual Sky Temperature as a Ladybug Data Collection.

        This value in degrees Celsius is derived from the Horizontal Infrared
        Radiation Intensity in Wh/m2. It represents the long wave radiant
        temperature of the sky
        Read more at: https://bigladdersoftware.com/epx/docs/9-6/engineering-reference/\
climate-calculations.html#energyplus-sky-temperature-calculation
        """
        # create sky temperature header
        sky_temp_header = Header(data_type=temperature.SkyTemperature(), unit='C',
                                 analysis_period=AnalysisPeriod(),
                                 metadata=self._metadata)

        # calculate sy temperature for each hour
        horiz_ir = self._get_data_by_field(12).values
        sky_temp_data = [calc_sky_temperature(hir) for hir in horiz_ir]
        return HourlyContinuousCollection(sky_temp_header, sky_temp_data)

    def approximate_design_day(self, day_type='SummerDesignDay', percentile=0.4):
        """Get a DesignDay object derived from percentile analysis of annual EPW data.

        Note that this method is only intended to be used when there are no design
        days in any DDY files associated with the EPW and the EPW's values for
        annual_heating_design_day or annual_cooling_design_day properties are None.

        The approximated design days produced by this method tend to be less
        accurate than these other sources, which are usually derived from multiple
        years of climate data instead of only one year. Information on the error
        introduced by using only one year of data to create design days can be
        found in AHSRAE HOF 2013, Chapter 14, pg 14.

        Args:
            day_type: Text for the type of design day to be produced. Choose from.

                * SummerDesignDay
                * WinterDesignDay

            percentile: A number between 0 and 50 for the percentile difference
                from the most extreme conditions within the EPW to be used for
                the design day. Typical values are 0.4 and 1.0. (Default: 0.4).
        """
        # get values used for both winter and summer design days
        avg_pres = self.atmospheric_station_pressure.average
        pressure = round(avg_pres) if avg_pres != 999999 else 101325
        avg_mon_temp = self.dry_bulb_temperature.average_monthly()
        hr_count = int(87.6 * percentile * 2)
        per_name = int(percentile) if int(percentile) == percentile else percentile

        if day_type == 'WinterDesignDay':  # create winter design day criteria
            # get temperature at percentile and indices of coldest hours
            temp = self.dry_bulb_temperature.percentile(percentile)
            _, indices = self.dry_bulb_temperature.lowest_values(hr_count)
            # get average wind speed and direction at coldest hours
            wind_speed = round(sum(self.wind_speed[i] for i in indices) / hr_count, 1)
            rel_dirs = [math.radians(self.wind_direction[i]) for i in indices]
            avg_dir = Vector2D.circular_mean(rel_dirs)
            wind_dir = int(math.degrees(avg_dir))
            wind_dir = wind_dir + 360 if wind_dir < 0 else wind_dir
            # get the date as the 21st of the coldest month
            date_obj = Date(avg_mon_temp.lowest_values(1)[1][0] + 1, 21)
            # return the design day object
            day_name = '{} Heating Design Day {}% Condns DB'.format(
                self.location.city, 100 - per_name)
            return DesignDay.from_design_day_properties(
                day_name, day_type, self.location, date_obj, temp, 0,
                'Wetbulb', temp, pressure, wind_speed, wind_dir,
                'ASHRAEClearSky', [0.0])
        elif day_type == 'SummerDesignDay':  # create summer design day criteria
            # get temperature at percentile and indices of hottest hours
            temp = self.dry_bulb_temperature.percentile(100 - percentile)
            _, indices = self.dry_bulb_temperature.highest_values(hr_count)
            # get average humidity, wind speed and direction at hottest hours
            dew_pt = sum(self.dew_point_temperature[i] for i in indices) / hr_count
            rh = rel_humid_from_db_dpt(temp, dew_pt)
            wb_temp = round(wet_bulb_from_db_rh(temp, rh, pressure), 1)
            wind_speed = round(sum(self.wind_speed[i] for i in indices) / hr_count, 1)
            rel_dirs = [math.radians(self.wind_direction[i]) for i in indices]
            avg_dir = Vector2D.circular_mean(rel_dirs)
            wind_dir = int(math.degrees(avg_dir))
            wind_dir = wind_dir + 360 if wind_dir < 0 else wind_dir
            # get the date as the 21st of the hottest month
            date_obj = Date(avg_mon_temp.highest_values(1)[1][0] + 1, 21)
            # compute the daily range of temperature from the days of the hottest month
            hot_mon_db = self.dry_bulb_temperature.filter_by_analysis_period(
                AnalysisPeriod(st_month=date_obj.month, end_month=date_obj.month))
            temp_ranges = []
            for day in hot_mon_db.group_by_day().values():
                if day != []:
                    temp_ranges.append(max(day) - min(day))
            temp_range = round(sum(temp_ranges) / len(temp_ranges), 1)
            # return the design day object
            day_name = '{} Cooling Design Day {}% Condns DB=>MWB'.format(
                self.location.city, per_name)
            return DesignDay.from_design_day_properties(
                day_name, day_type, self.location, date_obj, temp, temp_range,
                'Wetbulb', wb_temp, pressure, wind_speed, wind_dir,
                'ASHRAEClearSky', [1.0])
        else:
            raise ValueError(
                'Unrecognized design day type "{}".\nChoose from: "SummerDesignDay", '
                '"WinterDesignDay"'.format(day_type))

    def best_available_design_days(self, percentile=0.4):
        """Get the best available sensible heating + cooling design days from this EPW.

        This method will first check if there is a heating or cooling design day
        that meets the input percentile within the EPW itself. If None is
        found, the heating and cooling design days will be derived from analysis
        of the annual data within the EPW, which is usually less accurate.

        Args:
            percentile: A number between 0 and 50 for the percentile difference
                from the most extreme conditions within the EPW to be used for
                the design day. Typical values are 0.4 and 1.0. (Default: 0.4).

        Returns:
            A tuple with two design day objects. The first is the heating design
            day and the second is the cooling design day.
        """
        # get the heating design day
        if percentile == 0.4 and self.annual_heating_design_day_996 is not None:
            heating = self.annual_heating_design_day_996
        elif percentile == 1 and self.annual_heating_design_day_990 is not None:
            heating = self.annual_heating_design_day_990
        else:
            heating = self.approximate_design_day('WinterDesignDay', percentile)
        # get the cooling design day
        if percentile == 0.4 and self.annual_cooling_design_day_004 is not None:
            cooling = self.annual_cooling_design_day_004
        elif percentile == 1 and self.annual_cooling_design_day_010 is not None:
            cooling = self.annual_cooling_design_day_010
        else:
            cooling = self.approximate_design_day('SummerDesignDay', percentile)
        return heating, cooling

    def monthly_cooling_design_days(self, percentile=5):
        """Get a list of 12 monthly cooling design days from this EPW.

        Note that these design days are always derived from analysis of the annual
        data within the EPW, which is usually less accurate than the monthly
        design days available via a STAT or DDY file. However, such data is not
        always availabe in these files and so this method gives a means of

        Args:
            percentile: A number between 0 and 50 for the percentile difference
                from the most extreme conditions within each month to be used for
                the design day. Typical values are 10, 5, 2, and 0.4. Note that
                5% aligns with an annual precentile of 0.4%. (Default: 5).

        Returns:
            A list with 12 design day objects. These represent cooling design
            days ranging from January to December.
        """
        # get values used across all cooling design days
        avg_pres = self.atmospheric_station_pressure.average
        pressure = round(avg_pres) if avg_pres != 999999 else 101325
        per_name = int(percentile) if int(percentile) == percentile else percentile

        # loop through the months and create the design days
        design_days = []
        for month in range(1, 13):
            aper = AnalysisPeriod(st_month=month, end_month=month)
            # get temperature at percentile and indices of hottest hours
            db_temp = self.dry_bulb_temperature.filter_by_analysis_period(aper)
            hr_count = int((len(db_temp) * percentile * 2) / 100)
            temp = db_temp.percentile(100 - percentile)
            _, indices = db_temp.highest_values(hr_count)
            # get average humidity, wind speed and direction at hottest hours
            dp_temp = self.dew_point_temperature.filter_by_analysis_period(aper)
            dew_pt = sum(dp_temp[i] for i in indices) / hr_count
            rh = rel_humid_from_db_dpt(temp, dew_pt)
            wb_temp = round(wet_bulb_from_db_rh(temp, rh, pressure), 1)
            w_speed = self.wind_speed.filter_by_analysis_period(aper)
            wind_speed = round(sum(w_speed[i] for i in indices) / hr_count, 1)
            w_dir = self.wind_direction.filter_by_analysis_period(aper)
            rel_dirs = [math.radians(w_dir[i]) for i in indices]
            avg_dir = Vector2D.circular_mean(rel_dirs)
            wind_dir = int(math.degrees(avg_dir))
            wind_dir = wind_dir + 360 if wind_dir < 0 else wind_dir
            # compute the daily range of temperature from the days of the hottest month
            temp_ranges = []
            for day in db_temp.group_by_day().values():
                if day != []:
                    temp_ranges.append(max(day) - min(day))
            temp_range = round(sum(temp_ranges) / len(temp_ranges), 1)
            # return the design day object
            day_name = '{} {} {}% Condns DB=>MCWB'.format(
                self.location.city, aper.MONTHNAMES[month], per_name)
            m_d_day = DesignDay.from_design_day_properties(
                day_name, 'SummerDesignDay', self.location, Date(month, 21),
                temp, temp_range, 'Wetbulb', wb_temp, pressure, wind_speed, wind_dir,
                'ASHRAEClearSky', [1.0])
            design_days.append(m_d_day)
        return design_days

    def convert_to_ip(self):
        """Convert all Data Collections of this EPW object to IP units.

        This is useful when one knows that all graphics produced from this
        EPW should be in Imperial units."""
        if not self.is_data_loaded:
            self._import_data()
        if not self.is_ip:
            for coll in self._data:
                coll.convert_to_ip()
        self._is_ip = True

    def convert_to_si(self):
        """Convert all Data Collections of this EPW object to SI units.

        This is useful when one needs to convert the EPW back to SI units
        from imperial units for processes like computing thermal comfort
        from EPW data."""
        if not self.is_data_loaded:
            self._import_data()
        if self.is_ip:
            for coll in self._data:
                coll.convert_to_si()
        self._is_ip = False

    def to_ddy(self, file_path, percentile=0.4):
        """Produce a DDY file with a heating + cooling design day from this EPW.

        This method will first check if there is a heating or cooling design day
        that meets the input percentile within the EPW itself. If None is
        found, the heating and cooling design days will be derived from analysis
        of the annual data within the EPW, which is usually less accurate.

        Args:
            file_path: Full file path for output ddy file.
            percentile: A number between 0 and 50 for the percentile difference
                from the most extreme conditions within the EPW to be used for
                the design day. Typical values are 0.4 and 1.0. (Default: 0.4).
        """
        # get the design day objects
        des_days = self.best_available_design_days(percentile)
        # write the DDY
        if not file_path.lower().endswith('.ddy'):
            file_path += '.ddy'
        ddy = DDY(self.location, des_days)
        ddy.write(file_path)
        return file_path

    def to_ddy_monthly_cooling(
            self, file_path, annual_percentile=0.4, monthly_percentile=5):
        """Produce a DDY file with 1 heating and 12 cooling design days.

        The heating design day represents a cold and completely dark day whereas
        the cooling design days represent the warmest conditions in each month.
        This type of DDY file is useful when the peak cooling might not be driven
        by warm outdoor temperatures but instead by the highest-intensity
        solar condition, which may not coincide with the highest temperature.

        Args:
            file_path: Full file path for output ddy file.
            annual_percentile: A number between 0 and 50 for the percentile difference
                from the most extreme annual conditions within the EPW to be used for
                the heating design day. Typical values are 0.4 and 1.0. (Default: 0.4).
            monthly_percentile: A number between 0 and 50 for the percentile difference
                from the most extreme conditions within each month to be used for the
                cooling design days. Typical values are 10, 5, 2, and 0.4. (Default: 5).
        """
        # get the heating design day object
        if annual_percentile == 0.4 and self.annual_heating_design_day_996 is not None:
            heating = self.annual_heating_design_day_996
        elif annual_percentile == 1 and self.annual_heating_design_day_990 is not None:
            heating = self.annual_heating_design_day_990
        else:
            heating = self.approximate_design_day('WinterDesignDay', annual_percentile)
        # get the cooling design day objects
        cooling = self.monthly_cooling_design_days(monthly_percentile)
        ann_eq = round(monthly_percentile / 12, 1)
        ann_eq = int(ann_eq) if int(ann_eq) == ann_eq else ann_eq
        for cd in cooling:
            cd.name = '{} ({}% Condns DB=>MWB)'.format(cd.name, ann_eq)
        # write the DDY
        des_days = [heating] + cooling
        if not file_path.lower().endswith('.ddy'):
            file_path += '.ddy'
        ddy = DDY(self.location, des_days)
        ddy.write(file_path)
        return file_path

    def to_wea(self, file_path, hoys=None):
        """Write an wea file from the epw file.

        WEA carries radiation values from epw. Gendaymtx uses these values to
        generate the sky. For an annual analysis it is identical to using epw2wea.

        Args:
            file_path: Full file path for output file.
            hoys: List of hours of the year. Default is 0-8759.
        """
        hoys = hoys or xrange(len(self.direct_normal_radiation.datetimes))
        if not file_path.lower().endswith('.wea'):
            file_path += '.wea'

        originally_ip = False
        if self.is_ip:
            self.convert_to_si()
            originally_ip = True

        # write header
        lines = [self._get_wea_header()]
        # write values
        datetimes = self.direct_normal_radiation.datetimes
        for hoy in hoys:
            dir_rad = self.direct_normal_radiation[hoy]
            dif_rad = self.diffuse_horizontal_radiation[hoy]
            line = "%d %d %.3f %d %d\n" \
                % (datetimes[hoy].month,
                   datetimes[hoy].day,
                   datetimes[hoy].hour + 0.5,
                   dir_rad, dif_rad)
            lines.append(line)

        file_data = ''.join(lines)
        write_to_file(file_path, file_data, True)

        if originally_ip:
            self.convert_to_ip()

        return file_path

    def _get_wea_header(self):
        return "place %s\n" % self.location.city + \
            "latitude %.2f\n" % self.location.latitude + \
            "longitude %.2f\n" % -self.location.longitude + \
            "time_zone %d\n" % (-self.location.time_zone * 15) + \
            "site_elevation %.1f\n" % self.location.elevation + \
            "weather_data_file_units 1\n"

    def to_dict(self):
        """Convert the EPW to a dictionary."""
        # load data if it's not loaded
        if not self.is_data_loaded:
            self._import_data()

        def dictify_dict(base_dict):
            new_dict = {}
            for key, val in base_dict.items():
                new_dict[key] = val.to_dict()
            return new_dict
        hot_wks = dictify_dict(self.extreme_hot_weeks)
        cold_wks = dictify_dict(self.extreme_cold_weeks)
        typ_wks = dictify_dict(self.typical_weeks)
        grnd_temps = dictify_dict(self.monthly_ground_temperature)
        return {
            'location': self.location.to_dict(),
            'data_collections': [dc.to_dict() for dc in self._data],
            'metadata': self.metadata,
            'heating_dict': self.heating_design_condition_dictionary,
            'cooling_dict': self.cooling_design_condition_dictionary,
            'extremes_dict': self.extreme_design_condition_dictionary,
            'extreme_hot_weeks': hot_wks,
            'extreme_cold_weeks': cold_wks,
            'typical_weeks': typ_wks,
            "monthly_ground_temps": grnd_temps,
            "is_ip": self._is_ip,
            "is_leap_year": self.is_leap_year,
            "daylight_savings_start": self.daylight_savings_start,
            "daylight_savings_end": self.daylight_savings_end,
            "comments_1": self.comments_1,
            "comments_2": self.comments_2,
            "type": 'EPW'
        }

    def to_file_string(self):
        """Get a text string for the entirety of the EPW file contents."""
        # load data if it's  not loaded convert to SI if it is in IP
        if not self.is_data_loaded:
            self._import_data()
        originally_ip = False
        if self.is_ip:
            self.convert_to_si()
            originally_ip = True

        # write the file
        lines = self.header
        try:
            # if the first value is at 1AM, move first item to end position
            for field in xrange(0, self._num_of_fields):
                point_in_time = self._data[field].header.data_type.point_in_time
                if point_in_time:
                    first_hour = self._data[field]._values.pop(0)
                    self._data[field]._values.append(first_hour)

            annual_a_per = AnalysisPeriod(is_leap_year=self.is_leap_year)
            for hour in xrange(0, len(annual_a_per.datetimes)):
                line = []
                for field in xrange(0, self._num_of_fields):
                    line.append(str(self._data[field]._values[hour]))
                lines.append(",".join(line) + "\n")
        except IndexError:
            length_error_msg = 'Data length is not for a full year and cannot be ' + \
                'saved as an EPW file.'
            raise ValueError(length_error_msg)
        finally:  # move last item to start position for fields on the hour
            for field in xrange(0, self._num_of_fields):
                point_in_time = self._data[field].header.data_type.point_in_time
                if point_in_time:
                    last_hour = self._data[field]._values.pop()
                    self._data[field]._values.insert(0, last_hour)

        if originally_ip:  # put back the object as it was
            self.convert_to_ip()
        return ''.join(lines)

    def write(self, file_path):
        """Write EPW object as an .epw file and return the file path.

        Args:
            file_path: Text for the full path to where the .epw file will be written.
        """
        if not file_path.lower().endswith('.epw'):
            file_path += '.epw'
        file_data = self.to_file_string()
        write_to_file(file_path, file_data, True)
        return file_data

    def save(self, file_path):
        """Write EPW object as a file.

        Args:
            file_path: Text for the full path to where the file will be written.
        """
        file_data = self.to_file_string()
        write_to_file(file_path, file_data, True)
        return file_data

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """EPW representation."""
        return "EPW file Data for [%s]" % self.location.city


class EPWFields(object):
    """EPW weather file fields.

    Read more at https://bigladdersoftware.com/epx/docs/9-6/auxiliary-programs/\
energyplus-weather-file-epw-data-dictionary.html
    """

    _fields = {
        0: {'name': generic.GenericType('Year', 'yr'),
            'type': int,
            'unit': 'yr'
            },

        1: {'name': generic.GenericType('Month', 'mon'),
            'type': int,
            'unit': 'mon'
            },

        2: {'name': generic.GenericType('Day', 'day'),
            'type': int,
            'unit': 'day'
            },

        3: {'name': generic.GenericType('Hour', 'hr'),
            'type': int,
            'unit': 'hr'
            },

        4: {'name': generic.GenericType('Minute', 'min'),
            'type': int,
            'unit': 'min'
            },

        5: {'name': generic.GenericType('Uncertainty Flags', 'flag'),
            'type': str,
            'unit': 'flag'
            },

        6: {'name': temperature.DryBulbTemperature(),
            'type': float,
            'unit': 'C',
            'min': -70,
            'max': 70,
            'missing': 99.9
            },

        7: {'name': temperature.DewPointTemperature(),
            'type': float,
            'unit': 'C',
            'min': -70,
            'max': 70,
            'missing': 99.9
            },

        8: {'name': fraction.RelativeHumidity(),
            'type': int,
            'unit': '%',
            'missing': 999,
            'min': 0,
            'max': 110
            },

        9: {'name': pressure.AtmosphericStationPressure(),
            'type': int,
            'unit': 'Pa',
            'missing': 999999,
            'min': 31000,
            'max': 120000
            },

        10: {'name': energyintensity.ExtraterrestrialHorizontalRadiation(),
             'type': int,
             'unit': 'Wh/m2',
             'missing': 9999,
             'min': 0
             },

        11: {'name': energyintensity.ExtraterrestrialDirectNormalRadiation(),
             'type': int,
             'unit': 'Wh/m2',
             'missing': 9999,
             'min': 0
             },

        12: {'name': energyflux.HorizontalInfraredRadiationIntensity(),
             'type': int,
             'unit': 'W/m2',
             'missing': 9999,
             'min': 0
             },

        13: {'name': energyintensity.GlobalHorizontalRadiation(),
             'type': int,
             'unit': 'Wh/m2',
             'missing': 9999,
             'min': 0
             },

        14: {'name': energyintensity.DirectNormalRadiation(),
             'type': int,
             'unit': 'Wh/m2',
             'missing': 9999,
             'min': 0
             },

        15: {'name': energyintensity.DiffuseHorizontalRadiation(),
             'type': int,
             'unit': 'Wh/m2',
             'missing': 9999,
             'min': 0
             },

        16: {'name': illuminance.GlobalHorizontalIlluminance(),
             'type': int,
             'unit': 'lux',
             'missing': 999999,  # will be missing if >= 999900
             'min': 0
             },

        17: {'name': illuminance.DirectNormalIlluminance(),
             'type': int,
             'unit': 'lux',
             'missing': 999999,  # will be missing if >= 999900
             'min': 0
             },

        18: {'name': illuminance.DiffuseHorizontalIlluminance(),
             'type': int,
             'unit': 'lux',
             'missing': 999999,  # will be missing if >= 999900
             'min': 0
             },

        19: {'name': luminance.ZenithLuminance(),
             'type': int,
             'unit': 'cd/m2',
             'missing': 9999,  # will be missing if >= 9999
             'min': 0
             },

        20: {'name': angle.WindDirection(),
             'type': int,
             'unit': 'degrees',
             'missing': 999,
             'min': 0,
             'max': 360
             },

        21: {'name': speed.WindSpeed(),
             'type': float,
             'unit': 'm/s',
             'missing': 999,
             'min': 0,
             'max': 40
             },

        22: {'name': fraction.TotalSkyCover(),  # used if Horizontal IR is missing
             'type': int,
             'unit': 'tenths',
             'missing': 99,
             'min': 0,
             'max': 10
             },

        23: {'name': fraction.OpaqueSkyCover(),  # used if Horizontal IR is missing
             'type': int,
             'unit': 'tenths',
             'missing': 99
             },

        24: {'name': distance.Visibility(),
             'type': float,
             'unit': 'km',
             'missing': 9999
             },

        25: {'name': distance.CeilingHeight(),
             'type': int,
             'unit': 'm',
             'missing': 99999
             },

        26: {'name': generic.GenericType(name='Present Weather Observation',
                                         unit='observation'),
             'type': int,
             'unit': 'observation',
             'missing': 9
             },

        27: {'name': generic.GenericType(name='Present Weather Codes', unit='codes'),
             'type': int,
             'unit': 'codes',
             'missing': 999999999
             },

        28: {'name': distance.PrecipitableWater(),
             'type': int,
             'unit': 'mm',
             'missing': 999
             },

        29: {'name': fraction.AerosolOpticalDepth(),
             'type': float,
             'unit': 'fraction',
             'missing': 999
             },

        30: {'name': distance.SnowDepth(),
             'type': int,
             'unit': 'cm',
             'missing': 999
             },

        31: {'name': generic.GenericType(name='Days Since Last Snowfall', unit='day'),
             'type': int,
             'unit': 'day',
             'missing': 99
             },

        32: {'name': fraction.Albedo(),
             'type': float,
             'unit': 'fraction',
             'missing': 999
             },

        33: {'name': distance.LiquidPrecipitationDepth(),
             'type': float,
             'unit': 'mm',
             'missing': 999
             },

        34: {'name': fraction.LiquidPrecipitationQuantity(),
             'type': float,
             'unit': 'fraction',
             'missing': 99
             }
    }

    @classmethod
    def field_by_number(cls, field_number):
        """Return an EPWField based on field number.

        *   0 Year
        *   1 Month
        *   2 Day
        *   3 Hour
        *   4 Minute
        *   5 -
        *   6 Dry Bulb Temperature
        *   7 Dew Point Temperature
        *   8 Relative Humidity
        *   9 Atmospheric Station Pressure
        *   10 Extraterrestrial Horizontal Radiation
        *   11 Extraterrestrial Direct Normal Radiation
        *   12 Horizontal Infrared Radiation Intensity
        *   13 Global Horizontal Radiation
        *   14 Direct Normal Radiation
        *   15 Diffuse Horizontal Radiation
        *   16 Global Horizontal Illuminance
        *   17 Direct Normal Illuminance
        *   18 Diffuse Horizontal Illuminance
        *   19 Zenith Luminance
        *   20 Wind Direction
        *   21 Wind Speed
        *   22 Total Sky Cover
        *   23 Opaque Sky Cover
        *   24 Visibility
        *   25 Ceiling Height
        *   26 Present Weather Observation
        *   27 Present Weather Codes
        *   28 Precipitable Water
        *   29 Aerosol Optical Depth
        *   30 Snow Depth
        *   31 Days Since Last Snowfall
        *   32 Albedo
        *   33 Liquid Precipitation Depth
        *   34 Liquid Precipitation Quantity
        """
        return EPWField(cls._fields[field_number])

    def __repr__(self):
        """EPW fields representation."""
        fields = (
            '{}: {}'.format(key, value['name'])
            for key, value in self._fields.items()
        )

        return '\n'.join(fields)


class EPWField(object):
    """An EPW field.

    Args:
        name: Name of the field.
        value_type: field value type (e.g. int, float, str)
        unit: Field unit.
        missing: Missing value for the data type in EPW files.
    """
    __slots__ = ('name', 'value_type', 'unit', 'missing')

    def __init__(self, field_dict):
        self.name = field_dict['name']
        self.value_type = field_dict['type']
        if 'unit' in field_dict:
            self.unit = field_dict['unit']
        else:
            self.unit = None
        if 'missing' in field_dict:
            self.missing = field_dict['missing']
        else:
            self.missing = None
