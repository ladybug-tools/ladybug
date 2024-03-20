# coding=utf-8
from __future__ import division

import codecs
import os
import platform
import re

from .analysisperiod import AnalysisPeriod
from .designday import ASHRAEClearSky
from .designday import ASHRAETau
from .designday import DesignDay
from .designday import DryBulbCondition
from .designday import HumidityCondition
from .designday import WindCondition
from .ddy import DDY
from .dt import Date
from .location import Location

try:
    from itertools import izip as zip  # python 2
except ImportError:
    xrange = range  # python 3


class STAT(object):
    """Import data from a local .stat file.

    Args:
        file_path: Address to a local .stat file.

    Properties:
        * location
        * ashrae_climate_zone
        * koppen_climate_zone
        * extreme_cold_week
        * extreme_hot_week
        * typical_winter_week
        * typical_spring_week
        * typical_summer_week
        * typical_autumn_week
        * other_typical_weeks
        * annual_heating_design_day_996
        * annual_heating_design_day_990
        * annual_cooling_design_day_004
        * annual_cooling_design_day_010
        * monthly_cooling_design_days_100
        * monthly_cooling_design_days_050
        * monthly_cooling_design_days_020
        * monthly_cooling_design_days_004
        * monthly_db_temp_050
        * monthly_wb_temp_050
        * monthly_db_temp_range_050
        * monthly_wb_temp_range_050
        * monthly_found
        * standard_pressure_at_elev
        * monthly_wind_conditions
        * monthly_ws_avg
        * monthly_wind_dirs
        * monthly_clear_sky_conditions
        * monthly_tau_beam
        * monthly_tau_diffuse
        * file_path
    """
    # categories used for parsing text
    _months = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul',
               'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
    _wind_dirs = (0, 45, 90, 135, 180, 225, 270, 315)
    _wind_dir_names = ('North', 'NorthEast', 'East', 'SouthEast', 'South',
                       'SouthWest', 'West', 'NorthWest')
    # compiled strings for identifying data in the file
    _coord_pattern1 = re.compile(r"{([NSEW])(\s*\d*).(\s*\d*)")
    _coord_pattern2 = re.compile(r"{([NSEW])(\s*\d*) (\s*\d*)")
    _elev_pattern1 = re.compile(r"Elevation\s*[-]*\s*(\d*)m\s*(\S*)")
    _elev_pattern2 = re.compile(r"Elevation\s*[-]*\s*(\d*)\s*m\s*(\S*)")
    _timez_pattern = re.compile(r"{GMT\s*(\S*)\s*Hours}")
    _press_pattern = re.compile(r"Elevation\s*[-]*\s*(\d*)")
    _ashraecz_pattern = re.compile(r'Climate type\s"(\S*)"\s\(A')
    _koppencz_pattern = re.compile(r'Climate type\s"(\S*)"\s\(K')
    _hotweek_pattern = re.compile(r"Extreme Hot Week Period selected:"
                                  r"\s*(\w{3})\s*(\d{1,2}):\s*(\w{3})\s*(\d{1,2}),")
    _coldweek_pattern = re.compile(r"Extreme Cold Week Period selected:"
                                   r"\s*(\w{3})\s*(\d{1,2}):\s*(\w{3})\s*(\d{1,2}),")
    _typweek_pattern = re.compile(r"(\S*)\s*Typical Week Period selected:"
                                  r"\s*(\w{3})\s*(\d{1,2}):\s*(\w{3})\s*(\d{1,2}),")
    _heat_pattern = re.compile(r"Heating\s(\d.*)")
    _cool_pattern = re.compile(r"Cooling\s(\d.*)")
    _tau_beam_pattern = re.compile(r"taub \(beam\)(.*)")
    _tau_diffuse_pattern = re.compile(r"taud \(diffuse\)(.*)")
    _db_50_pattern = re.compile(r"Drybulb 5.0%(.*)")
    _wb_50_pattern = re.compile(r"Coincident Wetbulb 5.0%(.*)")
    _db_100_pattern = re.compile(r"Drybulb 10.%(.*)")
    _wb_100_pattern = re.compile(r"Coincident Wetbulb 10.%(.*)")
    _db_20_pattern = re.compile(r"Drybulb 2.0%(.*)")
    _wb_20_pattern = re.compile(r"Coincident Wetbulb 2.0%(.*)")
    _db_04_pattern = re.compile(r"Drybulb 0.4%(.*)")
    _wb_04_pattern = re.compile(r"Coincident Wetbulb 0.4%(.*)")
    _db_range_50_pattern = re.compile(r"Drybulb range - DB 5%(.*)")
    _wb_range_50_pattern = re.compile(r"Wetbulb range - DB 5%(.*)")
    _winds_pattern = re.compile(r"Monthly Statistics for Wind Speed[\s\S]*Daily Avg(.*)")
    _windd_patterns = tuple(re.compile(
        r"Monthly Wind Direction %[\s\S]*" + dir + r"\s(.*)") for dir in _wind_dir_names)

    __slots__ = (
        '_file_path', '_winter_des_day_dict', '_summer_des_day_dict',
        '_monthly_wind_dirs', '_location',
        '_ashrae_climate_zone', '_koppen_climate_zone',
        '_extreme_cold_week', '_extreme_hot_week', '_typical_weeks', '_monthly_db_50',
        '_monthly_wb_50', '_monthly_db_range_50', '_monthly_wb_range_50',
        '_monthly_db_100', '_monthly_wb_100', '_monthly_db_20', '_monthly_wb_20',
        '_monthly_db_04', '_monthly_wb_04', '_monthly_wind',
        '_stand_press_at_elev', '_monthly_tau_beam', '_monthly_tau_diffuse',
        '_header', '_body'
    )

    def __init__(self, file_path):
        """Initialize the class.
        """
        if file_path is not None:
            if not os.path.isfile(file_path):
                raise ValueError(
                    'Cannot find an stat file at {}'.format(file_path))
            if not file_path.lower().endswith('stat'):
                raise TypeError('{} is not an .stat file.'.format(file_path))
            self._file_path = os.path.normpath(file_path)

        # defaults empty state for certain parameters
        self._winter_des_day_dict = {}
        self._summer_des_day_dict = {}
        self._monthly_wind_dirs = []

        # import the data from the file
        if file_path is not None:
            self._import_data()

    @classmethod
    def from_dict(cls, data):
        """ Create Stat from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

                {
                "location": {},  # ladybug location schema
                "ashrae_climate_zone": ""5A,  # str
                "koppen_climate_zone": "Dfa", # str
                "extreme_cold_week": {},  # ladybug analysis period schema
                "extreme_hot_week": {},  # ladybug analysis period schema
                "typical_weeks": {},  # dict of ladybug analysis period schemas
                "heating_dict": {},  # dict containing heating design conditions
                "cooling_dict": {},  # dict containing cooling design conditions
                "monthly_db_50": [],  # list of 12 float values for each month
                "monthly_wb_50": [],  # list of 12 float values for each month
                "monthly_db_range_50": [],  # list of 12 float values for each month
                "monthly_wb_range_50": [],  # list of 12 float values for each month
                "monthly_db_100": [],  # list of 12 float values for each month
                "monthly_wb_100": [],  # list of 12 float values for each month
                "monthly_db_20": [],  # list of 12 float values for each month
                "monthly_wb_20": [],  # list of 12 float values for each month
                "monthly_db_04": [],  # list of 12 float values for each month
                "monthly_wb_04": [],  # list of 12 float values for each month
                "monthly_wind": [],  # list of 12 float values for each month
                "monthly_wind_dirs": [],  # matrix with 12 cols for months of the year
                                          #and 8 rows for the cardinal directions.
                "standard_pressure_at_elev": 101325,  # float value for pressure in Pa
                "monthly_tau_beam":[],  # list of 12 float values for each month
                "monthly_tau_diffuse": []  # list of 12 float values for each month
                }
        """
        # Initialize the class with all data missing
        stat_ob = cls(None)

        # Check required and optional keys
        option_keys_none = ('ashrae_climate_zone', 'koppen_climate_zone',
                            'extreme_cold_week', 'extreme_hot_week',
                            'standard_pressure_at_elev')
        option_keys_list = ('monthly_db_50', 'monthly_wb_50',
                            'monthly_db_range_50', 'monthly_wb_range_50',
                            'monthly_db_100', 'monthly_wb_100', 'monthly_db_20',
                            'monthly_wb_20', 'monthly_db_04', 'monthly_wb_04',
                            'monthly_wind', 'monthly_wind_dirs',
                            'monthly_tau_beam', 'monthly_tau_diffuse')
        option_keys_dict = ('typical_weeks', 'heating_dict', 'cooling_dict')
        assert 'location' in data, 'Required key "location" is missing!'
        for key in option_keys_none:
            if key not in data:
                data[key] = None
        for key in option_keys_list:
            if key not in data:
                data[key] = []
        for key in option_keys_dict:
            if key not in data:
                data[key] = {}

        # assign the properties of the dictionary to the stat object.
        stat_ob._location = Location.from_dict(data['location'])
        stat_ob._ashrae_climate_zone = data['ashrae_climate_zone']
        stat_ob._koppen_climate_zone = data['koppen_climate_zone']
        stat_ob._extreme_cold_week = AnalysisPeriod.from_dict(data['extreme_cold_week'])\
            if data['extreme_cold_week'] else None
        stat_ob._extreme_hot_week = AnalysisPeriod.from_dict(data['extreme_hot_week'])\
            if data['extreme_hot_week'] else None
        stat_ob._typical_weeks = {}
        for key, val in data['typical_weeks'].items():
            if isinstance(val, list):
                stat_ob._typical_weeks[key] = [AnalysisPeriod.from_dict(v) for v in val]
            else:
                stat_ob._typical_weeks[key] = AnalysisPeriod.from_dict(val)
        stat_ob._winter_des_day_dict = data['heating_dict']
        stat_ob._summer_des_day_dict = data['cooling_dict']
        stat_ob._monthly_db_50 = data['monthly_db_50']
        stat_ob._monthly_wb_50 = data['monthly_wb_50']
        stat_ob._monthly_db_range_50 = data['monthly_db_range_50']
        stat_ob._monthly_wb_range_50 = data['monthly_wb_range_50']
        stat_ob._monthly_db_100 = data['monthly_db_100']
        stat_ob._monthly_wb_100 = data['monthly_wb_100']
        stat_ob._monthly_db_20 = data['monthly_db_20']
        stat_ob._monthly_wb_20 = data['monthly_wb_20']
        stat_ob._monthly_db_04 = data['monthly_db_04']
        stat_ob._monthly_wb_04 = data['monthly_wb_04']
        stat_ob._monthly_wind = data['monthly_wind']
        stat_ob._monthly_wind_dirs = data['monthly_wind_dirs']
        stat_ob._stand_press_at_elev = data['standard_pressure_at_elev']
        stat_ob._monthly_tau_beam = data['monthly_tau_beam']
        stat_ob._monthly_tau_diffuse = data['monthly_tau_diffuse']

        return stat_ob

    @property
    def file_path(self):
        """Get the path to the stat file."""
        return self._file_path

    def _import_data(self):
        """Import data from a stat file.
        """
        # set default state to ironpython for very old ironpython (2.7.0)
        iron_python = True
        try:
            iron_python = True if platform.python_implementation() == 'IronPython' \
                else False
        except ValueError as e:
            # older versions of IronPython fail to parse version correctly
            # failed to parse IronPython sys.version: '2.7.5 (IronPython 2.7.5 (2.7.5.0)
            # on .NET 4.0.30319.42000 (64-bit))'
            if 'IronPython' in str(e):
                iron_python = True

        if iron_python:
            statwin = codecs.open(self.file_path, 'r')
        else:
            statwin = codecs.open(self.file_path, 'r', encoding='utf-8', errors='ignore')
        try:
            line = statwin.readline()
            # import header with location
            self._header = [line] + [statwin.readline() for i in xrange(9)]
            self._body = statwin.read()
        except Exception as e:
            import traceback
            raise Exception('{}\n{}'.format(e, traceback.format_exc()))
        else:

            # import location data
            loc_name = self._header[2].strip().replace('Location -- ', '')
            if ' - ' in loc_name:
                city = ' '.join(loc_name.split(' - ')[:-1])
            else:  # for US stat files it is full name separated by spaces
                city = ' '.join(loc_name.split()[:-2])
            country = loc_name.split(' ')[-1]
            source = self._header[6].strip().replace('Data Source -- ', '')
            station_id = self._header[8].strip().replace('WMO Station ', '')
            if iron_python:  # IronPython
                matches = self._coord_pattern1.findall(self._header[3])
            else:  # CPython
                matches = self._coord_pattern2.findall(self._header[3])
            lat_sign = -1 if matches[0][0] == 'S' else 1
            latitude = lat_sign * (float(matches[0][1]) + (float(matches[0][2]) / 60))
            lon_sign = -1 if matches[1][0] == 'W' else 1
            longitude = lon_sign * (float(matches[1][1]) + (float(matches[1][2]) / 60))
            time_zone = self._regex_check(self._timez_pattern, self._header[3])
            elev_matches = self._elev_pattern1.findall(self._header[4])
            if len(elev_matches) == 0:
                elev_matches = self._elev_pattern2.findall(self._header[4])
            elev_sign = -1 if elev_matches[0][-1].lower() == 'below' else 1
            elevation = elev_sign * float(elev_matches[0][0])
            self._location = Location()
            self._location.city = city
            self._location.country = country
            self._location.source = source
            self._location.station_id = station_id
            self._location.latitude = latitude
            self._location.longitude = longitude
            self._location.time_zone = time_zone
            self._location.elevation = elevation

            # pull out individual properties
            self._stand_press_at_elev = self._regex_check(
                self._press_pattern, self._header[5])
            self._ashrae_climate_zone = self._regex_check(
                self._ashraecz_pattern, self._body)
            self._koppen_climate_zone = self._regex_check(
                self._koppencz_pattern, self._body)

            # pull out extreme and seasonal weeks.
            self._extreme_hot_week = self._regex_week_parse(self._hotweek_pattern)
            self._extreme_cold_week = self._regex_week_parse(self._coldweek_pattern)
            self._typical_weeks = self._regex_typical_week_parse()

            # pull out annual design days
            winter_vals = self._regex_parse(self._heat_pattern)
            for key, val in zip(DesignDay.HEATING_KEYS, winter_vals):
                self._winter_des_day_dict[key] = val
            summer_vals = self._regex_parse(self._cool_pattern)
            for key, val in zip(DesignDay.COOLING_KEYS, summer_vals):
                self._summer_des_day_dict[key] = val

            # Pull out relevant monthly information
            self._monthly_tau_beam = self._regex_parse(self._tau_beam_pattern)
            self._monthly_tau_diffuse = self._regex_parse(self._tau_diffuse_pattern)
            self._monthly_db_50 = self._regex_parse(self._db_50_pattern)
            self._monthly_wb_50 = self._regex_parse(self._wb_50_pattern)
            self._monthly_db_100 = self._regex_parse(self._db_100_pattern)
            self._monthly_wb_100 = self._regex_parse(self._wb_100_pattern)
            self._monthly_db_20 = self._regex_parse(self._db_20_pattern)
            self._monthly_wb_20 = self._regex_parse(self._wb_20_pattern)
            self._monthly_db_04 = self._regex_parse(self._db_04_pattern)
            self._monthly_wb_04 = self._regex_parse(self._wb_04_pattern)
            self._monthly_db_range_50 = self._regex_parse(self._db_range_50_pattern)
            self._monthly_wb_range_50 = self._regex_parse(self._wb_range_50_pattern)
            self._monthly_wind = self._regex_parse(self._winds_pattern)
            for direction in self._windd_patterns:
                dirs = self._regex_parse(direction)
                if dirs != []:
                    self._monthly_wind_dirs.append(dirs)
            if self._monthly_wind_dirs == []:
                self._monthly_wind_dirs = [[0] * 12 for i in xrange(8)]

        finally:
            statwin.close()

    def _regex_check(self, regex_pattern, search_space):
        matches = regex_pattern.findall(search_space)
        if len(matches) > 0:
            try:
                return float(matches[0])
            except ValueError:
                return matches[0]
        else:
            return None

    def _regex_week(self, match):
        if len(match) == 4:
            try:
                st_mon = int(self._months.index(match[0])) + 1
                end_mon = int(self._months.index(match[2])) + 1
                st_day = int(match[1])
                end_day = int(match[3])
            except ValueError:
                return None
            return AnalysisPeriod(st_mon, st_day, 0, end_mon, end_day, 23)
        else:
            return None

    def _regex_week_parse(self, regex_pattern):
        matches = regex_pattern.findall(self._body)
        if len(matches) > 0:
            return self._regex_week(matches[0])
        else:
            return None

    def _regex_typical_week_parse(self):
        typ_weeks = {'other': []}
        matches = self._typweek_pattern.findall(self._body)
        for match in matches:
            a_per = self._regex_week(match[1:])
            if 'winter' in match[0]:
                typ_weeks['winter'] = a_per
            elif 'spring' in match[0]:
                typ_weeks['spring'] = a_per
            elif 'summer' in match[0]:
                typ_weeks['summer'] = a_per
            elif 'autumn' in match[0]:
                typ_weeks['autumn'] = a_per
            else:
                typ_weeks['other'].append(a_per)
        return typ_weeks

    def _regex_parse(self, regex_pattern):
        matches = regex_pattern.findall(self._body)
        if len(matches) > 0:
            raw_txt = matches[0].strip().split('\t')
            try:
                return [float(i) if i not in ('N', '  N_A') else None for i in raw_txt]
            except ValueError:
                return [str(i) for i in raw_txt]
        else:
            return []

    @property
    def monthly_found(self):
        if self._monthly_db_range_50 != [] and self._monthly_wb_range_50 != [] \
            and self._monthly_wind != [] \
                and self._stand_press_at_elev is not None:
            return True
        else:
            return False

    @property
    def location(self):
        """Return ladybug location object."""
        return self._location

    @property
    def ashrae_climate_zone(self):
        """Return a text string indicating the ASHRAE climate zone.

        Numbers in the zone denote average temperature (0 = Hottest; 8 = Coldest)
        Letters in the zone denote wetness (A = Humid; B = Dry; C = Marine)
        """
        return self._ashrae_climate_zone

    @property
    def koppen_climate_zone(self):
        """Return a text string indicating the Koppen climate zone.

        The Koppen climate classification is the most widely used climate
        classification system and combines average annual and monthly
        temperatures, precipitation, and the seasonality of precipitation.
        """
        return self._koppen_climate_zone

    @property
    def extreme_cold_week(self):
        """AnalysisPeriod for the coldest week within the corresponding EPW."""
        return self._extreme_cold_week

    @property
    def extreme_hot_week(self):
        """AnalysisPeriod for the hottest week within the corresponding EPW."""
        return self._extreme_hot_week

    @property
    def typical_winter_week(self):
        """AnalysisPeriod for a typical winter week within the corresponding EPW."""
        try:
            return self._typical_weeks['winter']
        except KeyError:
            return None

    @property
    def typical_spring_week(self):
        """AnalysisPeriod for a typical spring week within the corresponding EPW."""
        try:
            return self._typical_weeks['spring']
        except KeyError:
            return None

    @property
    def typical_summer_week(self):
        """AnalysisPeriod for a typical summer week within the corresponding EPW."""
        try:
            return self._typical_weeks['summer']
        except KeyError:
            return None

    @property
    def typical_autumn_week(self):
        """AnalysisPeriod for a typical autumn week within the corresponding EPW."""
        try:
            return self._typical_weeks['autumn']
        except KeyError:
            return None

    @property
    def other_typical_weeks(self):
        """List of AnalysisPeriods for typical weeks outside of the seasonal weeks."""
        return self._typical_weeks['other']

    @property
    def annual_heating_design_day_996(self):
        """A design day object representing the annual 99.6% heating design day."""
        if bool(self._winter_des_day_dict):
            return DesignDay.from_ashrae_dict_heating(
                self._winter_des_day_dict, self.location, False,
                self._stand_press_at_elev)
        else:
            return None

    @property
    def annual_heating_design_day_990(self):
        """A design day object representing the annual 99.0% heating design day."""
        if bool(self._winter_des_day_dict):
            return DesignDay.from_ashrae_dict_heating(
                self._winter_des_day_dict, self.location, True,
                self._stand_press_at_elev)
        else:
            return None

    @property
    def annual_cooling_design_day_004(self):
        """A design day object representing the annual 0.4% cooling design day."""
        if bool(self._summer_des_day_dict):
            tau = None
            month_num = int(self._summer_des_day_dict['Month'])
            if self._monthly_tau_beam != [] and self._monthly_tau_diffuse != [] \
                and self._monthly_tau_beam[month_num - 1] is not None and \
                    self._monthly_tau_diffuse[month_num - 1] is not None:
                tau = (self._monthly_tau_beam[month_num - 1],
                       self._monthly_tau_diffuse[month_num - 1])
            return DesignDay.from_ashrae_dict_cooling(
                self._summer_des_day_dict, self.location, False,
                self._stand_press_at_elev, tau)
        else:
            return None

    @property
    def annual_cooling_design_day_010(self):
        """A design day object representing the annual 1.0% cooling design day."""
        if bool(self._summer_des_day_dict):
            tau = None
            month_num = int(self._summer_des_day_dict['Month'])
            if self._monthly_tau_beam != [] and self._monthly_tau_diffuse != [] \
                and self._monthly_tau_beam[month_num - 1] is not None and \
                    self._monthly_tau_diffuse[month_num - 1] is not None:
                tau = (self._monthly_tau_beam[month_num - 1],
                       self._monthly_tau_diffuse[month_num - 1])
            return DesignDay.from_ashrae_dict_cooling(
                self._summer_des_day_dict, self.location, True,
                self._stand_press_at_elev, tau)
        else:
            return None

    @property
    def monthly_cooling_design_days_050(self):
        """A list of 12 objects representing monthly 5.0% cooling design days."""
        if not self.monthly_found or self._monthly_db_50 == [] \
                or self._monthly_wb_50 == []:
            return []
        else:
            db_conds = [DryBulbCondition(x, y) for x, y in zip(
                self._monthly_db_50, self._monthly_db_range_50)]
            hu_conds = [HumidityCondition(
                'Wetbulb', x, self._stand_press_at_elev) for x in self._monthly_wb_50]
            ws_conds = self.monthly_wind_conditions
            sky_conds = self.monthly_clear_sky_conditions
            return [DesignDay(
                'Cooling Design Day {} 5% Condns DB=>MCWB'.format(self._months[i]),
                'SummerDesignDay', self._location,
                db_conds[i], hu_conds[i], ws_conds[i], sky_conds[i])
                for i in xrange(12)]

    @property
    def monthly_cooling_design_days_100(self):
        """A list of 12 objects representing monthly 10.0% cooling design days."""
        if not self.monthly_found or self._monthly_db_100 == [] \
                or self._monthly_wb_100 == []:
            return []
        else:
            db_conds = [DryBulbCondition(x, y) for x, y in zip(
                self._monthly_db_100, self._monthly_db_range_50)]
            hu_conds = [HumidityCondition(
                'Wetbulb', x, self._stand_press_at_elev) for x in self._monthly_wb_100]
            ws_conds = self.monthly_wind_conditions
            sky_conds = self.monthly_clear_sky_conditions
            return [DesignDay(
                'Cooling Design Day {} 10% Condns DB=>MCWB'.format(self._months[i]),
                'SummerDesignDay', self._location,
                db_conds[i], hu_conds[i], ws_conds[i], sky_conds[i])
                for i in xrange(12)]

    @property
    def monthly_cooling_design_days_020(self):
        """A list of 12 objects representing monthly 2.0% cooling design days."""
        if not self.monthly_found or self._monthly_db_20 == [] \
                or self._monthly_wb_20 == []:
            return []
        else:
            db_conds = [DryBulbCondition(x, y) for x, y in zip(
                self._monthly_db_20, self._monthly_db_range_50)]
            hu_conds = [HumidityCondition(
                'Wetbulb', x, self._stand_press_at_elev) for x in self._monthly_wb_20]
            ws_conds = self.monthly_wind_conditions
            sky_conds = self.monthly_clear_sky_conditions
            return [DesignDay(
                'Cooling Design Day {} 2% Condns DB=>MCWB'.format(self._months[i]),
                'SummerDesignDay', self._location,
                db_conds[i], hu_conds[i], ws_conds[i], sky_conds[i])
                for i in xrange(12)]

    @property
    def monthly_cooling_design_days_004(self):
        """A list of 12 objects representing monthly 0.4% cooling design days."""
        if not self.monthly_found or self._monthly_db_04 == [] \
                or self._monthly_wb_04 == []:
            return []
        else:
            db_conds = [DryBulbCondition(x, y) for x, y in zip(
                self._monthly_db_04, self._monthly_db_range_50)]
            hu_conds = [HumidityCondition(
                'Wetbulb', x, self._stand_press_at_elev) for x in self._monthly_wb_04]
            ws_conds = self.monthly_wind_conditions
            sky_conds = self.monthly_clear_sky_conditions
            return [DesignDay(
                'Cooling Design Day {} 0.4% Condns DB=>MCWB'.format(self._months[i]),
                'SummerDesignDay', self._location,
                db_conds[i], hu_conds[i], ws_conds[i], sky_conds[i])
                for i in xrange(12)]

    @property
    def monthly_db_temp_050(self):
        """A list of 12 float values for monthly 5.0% dry bulb temperature."""
        return self._monthly_db_50

    @property
    def monthly_wb_temp_050(self):
        """A list of 12 float values for monthly 5.0% wet bulb temperature."""
        return self._monthly_wb_50

    @property
    def monthly_db_temp_range_050(self):
        """A list of 12 values for monthly ranges of dry bulb temperatures at 5.0%."""
        return self._monthly_db_range_50

    @property
    def monthly_wb_temp_range_050(self):
        """A list of 12 values for monthly ranges of wet bulb temperatures at 5.0%."""
        return self._monthly_wb_range_50

    @property
    def standard_pressure_at_elev(self):
        """The standard pressure on pascals at the elevation of the location."""
        return self._stand_press_at_elev

    @property
    def monthly_wind_conditions(self):
        """A list of 12 monthly wind conditions that are used on the design days."""
        return [WindCondition(x, y) for x, y in zip(
            self._monthly_wind, self.monthly_wind_dirs)]

    @property
    def monthly_ws_avg(self):
        """A list of 12 float values for monthly average wind speeds."""
        return self._monthly_wind

    @property
    def monthly_wind_dirs(self):
        """A list of prevailing wind directions for each month."""
        mwd = zip(*self._monthly_wind_dirs)
        return [self._wind_dirs[mon.index(max(mon))] for mon in mwd]

    @property
    def monthly_clear_sky_conditions(self):
        """A list of 12 monthly clear sky conditions that are used on the design days."""
        if self._monthly_tau_diffuse is [] or self._monthly_tau_beam is []:
            return [ASHRAEClearSky(Date(i, 21)) for i in xrange(1, 13)]
        md = zip(list(xrange(1, 13)), self._monthly_tau_beam, self._monthly_tau_diffuse)
        return [ASHRAETau(Date(i, 21), x, y) if x is not None
                else ASHRAEClearSky(Date(i, 21)) for i, x, y in md]

    @property
    def monthly_tau_beam(self):
        """A list of 12 float values for monthly beam optical depth.

        These values can be used to generate ASHRAE Revised Clear Skies, which
        are intended to determine peak solar load and sizing parmeters for
        HVAC systems.
        """
        return self._monthly_tau_beam

    @property
    def monthly_tau_diffuse(self):
        """Return a list of 12 float values for monthly diffuse optical depth.

        These values can be used to generate ASHRAE Revised Clear Skies, which
        are intended to determine peak solar load and sizing parmeters for
        HVAC systems.
        """
        return self._monthly_tau_diffuse

    def to_ddy(self, file_path, percentile=0.4):
        """Produce a DDY file with a heating + cooling design day from this STAT.

        If design days following the input percentile are not found in the STAT
        data, a ValueError will be raised.

        Args:
            file_path: Full file path for output ddy file.
            percentile: A number for the percentile difference from the most
                extreme conditions for the design days. Choose from 0.4 and
                1.0. (Default: 0.4).
        """
        # get the design day objects
        if percentile == 0.4:
            des_days = \
                [self.annual_heating_design_day_996, self.annual_cooling_design_day_004]
        elif percentile == 1:
            des_days = \
                [self.annual_heating_design_day_990, self.annual_cooling_design_day_010]
        else:
            raise ValueError('STAT files do not contain design days for '
                             '{}% percentile.'.format(percentile))
        if None in des_days:
            raise ValueError('The STAT file do not contain design days for '
                             '{}% percentile.'.format(percentile))
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
        If design days following the input percentile are not found in the STAT
        data, a ValueError will be raised.

        Args:
            file_path: Full file path for output ddy file.
            annual_percentile: A number for the percentile difference from the most
                extreme conditions for the design days. Choose from 0.4 and
                1.0. (Default: 0.4).
            monthly_percentile: A number between for the percentile difference from the
                most extreme conditions within each month to be used for the cooling
                design days. Choose from 10, 5, 2 or 0.04. (Default: 5).
        """
        # get the heating design day object
        if annual_percentile == 0.4:
            heating = self.annual_heating_design_day_996
        elif annual_percentile == 1:
            heating = self.annual_heating_design_day_990
        else:
            raise ValueError('STAT files do not contain heating design days for '
                             '{}% percentile.'.format(annual_percentile))
        # get the cooling design day objects
        if monthly_percentile == 5:
            cooling = self.monthly_cooling_design_days_050
        elif monthly_percentile == 10:
            cooling = self.monthly_cooling_design_days_100
        elif monthly_percentile == 2:
            cooling = self.monthly_cooling_design_days_020
        elif monthly_percentile == 0.4:
            cooling = self.monthly_cooling_design_days_004
        else:
            raise ValueError('STAT files do not contain monthly cooling design days for '
                             '{}% percentile.'.format(monthly_percentile))
        ann_eq = round(monthly_percentile / 12, 1)
        ann_eq = int(ann_eq) if int(ann_eq) == ann_eq else ann_eq
        for cd in cooling:
            cd.name = '{} ({}% Condns DB=>MWB)'.format(cd.name, ann_eq)
        # write the DDY
        des_days = [heating] + cooling
        if None in des_days:
            msg = 'heating design days for {}'.format(annual_percentile) if heating \
                is None else 'cooling design days for {}'.format(monthly_percentile)
            raise ValueError('The STAT file do not contain {}% percentile.'.format(msg))
        if not file_path.lower().endswith('.ddy'):
            file_path += '.ddy'
        ddy = DDY(self.location, des_days)
        ddy.write(file_path)
        return file_path

    def to_dict(self):
        """Convert the stat object to a dictionary."""
        def dictify_dict(base_dict):
            new_dict = {}
            for key, val in base_dict.items():
                if isinstance(val, list):
                    new_dict[key] = [v.to_dict() for v in val]
                else:
                    new_dict[key] = val.to_dict()
            return new_dict
        return {
            'location': self.location.to_dict(),
            'ashrae_climate_zone': self.ashrae_climate_zone,
            'koppen_climate_zone': self.koppen_climate_zone,
            'extreme_cold_week': self.extreme_cold_week.to_dict()
            if self.extreme_cold_week else None,
            'extreme_hot_week': self.extreme_hot_week.to_dict()
            if self.extreme_cold_week else None,
            'typical_weeks': dictify_dict(self._typical_weeks),
            'heating_dict': self._winter_des_day_dict,
            'cooling_dict': self._summer_des_day_dict,
            "monthly_db_50": self._monthly_db_50,
            "monthly_wb_50": self._monthly_wb_50,
            "monthly_db_range_50": self._monthly_db_range_50,
            "monthly_wb_range_50": self._monthly_wb_range_50,
            "monthly_db_100": self._monthly_db_100,
            "monthly_wb_100": self._monthly_wb_100,
            "monthly_db_20": self._monthly_db_20,
            "monthly_wb_20": self._monthly_wb_20,
            "monthly_db_04": self._monthly_db_04,
            "monthly_wb_04": self._monthly_wb_04,
            "monthly_wind": self._monthly_wind,
            "monthly_wind_dirs": self._monthly_wind_dirs,
            "standard_pressure_at_elev": self.standard_pressure_at_elev,
            "monthly_tau_beam": self.monthly_tau_beam,
            "monthly_tau_diffuse": self.monthly_tau_diffuse,
            "type": 'STAT'
        }

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """stat file representation."""
        return "STAT [%s]" % self.location.city
