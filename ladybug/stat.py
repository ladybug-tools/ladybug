from .location import Location
from .designday import DesignDay
from .designday import DryBulbCondition
from .designday import HumidityCondition
from .designday import WindCondition
from .designday import RevisedClearSkyCondition
from .designday import OriginalClearSkyCondition

import os
import re
import codecs
import platform


class STAT(object):
    """Import data from a local .stat file.

    args:
        file_path: Local file address to a .stat file.

    properties:
        location
        ashrae_climate_zone
        koppen_climate_zone
        monthly_tau_beam
        monthly_tau_diffuse
    """

    def __init__(self, file_path):
        """Initalize the class."""
        self.file_path = file_path

        # defaults in case some climate parameters are unclassifiable
        self._header = None
        self._location = None
        self._stand_press_at_elev = None
        self._ashrae_climate_zone = None
        self._koppen_climate_zone = None
        self._winter_des_day_dict = {}
        self._summer_des_day_dict = {}
        self._monthly_db_04 = []
        self._monthly_wb_04 = []
        self._monthly_db_20 = []
        self._monthly_wb_20 = []
        self._monthly_db_50 = []
        self._monthly_wb_50 = []
        self._monthly_db_100 = []
        self._monthly_wb_100 = []
        self._monthly_db_range_50 = []
        self._monthly_wb_range_50 = []
        self._monthly_wind = []
        self._monthly_wind_dirs = []
        self._monthly_tau_beam = []
        self._monthly_tau_diffuse = []

        # import the data from the file
        self._import_data()

    @property
    def file_path(self):
        """Get or set path to stat file."""
        return self._file_path

    @property
    def folder(self):
        """Get stat file folder."""
        return self._folder

    @property
    def file_name(self):
        """Get stat file name."""
        return self._file_name

    @file_path.setter
    def file_path(self, stat_file_path):
        self._file_path = os.path.normpath(stat_file_path)

        if not os.path.isfile(self._file_path):
            raise ValueError(
                'Cannot find an stat file at {}'.format(self._file_path))

        if not stat_file_path.lower().endswith('stat'):
            raise TypeError(stat_file_path + ' is not an .stat file.')

        self._folder, self._file_name = os.path.split(self.file_path)

    # TODO: import extreme and seasonal weeks
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
            self._header = [line] + [statwin.readline() for i in range(9)]
            self._body = statwin.read()
        except Exception as e:
            import traceback
            raise Exception('{}\n{}'.format(e, traceback.format_exc()))
        else:
            # import location data
            loc_name = self._header[2].strip().replace('Location -- ', '')
            if ' - ' in loc_name:
                city = ' '.join(loc_name.split(' - ')[:-1])
            else:
                # for US stat files it is full name separated by spaces
                # Chicago Ohare Intl Ap IL USA
                city = ' '.join(loc_name.split()[:-2])

            country = loc_name.split(' ')[-1]
            source = self._header[6].strip().replace('Data Source -- ', '')
            station_id = self._header[8].strip().replace('WMO Station ', '')
            if iron_python:
                # IronPython
                coord_pattern = re.compile(r"{([NSEW])(\s*\d*)deg(\s*\d*)'}")
                matches = coord_pattern.findall(self._header[3].replace('\xb0', 'deg'))
            else:
                # CPython
                coord_pattern = re.compile(r"{([NSEW])(\s*\d*) (\s*\d*)'}")
                matches = coord_pattern.findall(self._header[3])
            lat_sign = -1 if matches[0][0] == 'S' else 1
            latitude = lat_sign * (float(matches[0][1]) + (float(matches[0][2]) / 60))
            lon_sign = -1 if matches[1][0] == 'W' else 1
            longitude = lon_sign * (float(matches[1][1]) + (float(matches[1][2]) / 60))
            tz_pattern = re.compile(r"{GMT\s*(\S*)\s*Hours}")
            time_zone = float(tz_pattern.findall(self._header[3])[0])
            elev_pattern = re.compile(r"Elevation\s*[-]*\s*(\d*)m\s*(\S*)")
            elev_matches = elev_pattern.findall(self._header[4])
            elev_sign = -1 if elev_matches[0][-1].lower() == 'below' else 1
            elevation = elev_sign * float(elev_matches[0][0])
            press_pattern = re.compile(r"Elevation\s*[-]*\s*(\d*)Pa")
            self._stand_press_at_elev = float(press_pattern.findall(self._header[5])[0])

            self._location = Location()
            self._location.city = city
            self._location.country = country
            self._location.source = source
            self._location.station_id = station_id
            self._location.latitude = latitude
            self._location.longitude = longitude
            self._location.time_zone = time_zone
            self._location.elevation = elevation

            # Pull out climate zone classifications
            a_clim_mat = re.compile(r'Climate type\s"(\S*)"\s\(A').findall(self._body)
            if len(a_clim_mat) > 0:
                self._ashrae_climate_zone = a_clim_mat[0]
            k_clim_mat = re.compile(r'Climate type\s"(\S*)"\s\(K').findall(self._body)
            if len(k_clim_mat) > 0:
                self._koppen_climate_zone = k_clim_mat[0]

            # Pull out annual design days
            winter_keys = self._regex_parse(r"Design Stat	Coldest(.*)", False)
            winter_vals = self._regex_parse(r"Heating(.*)")
            for key, val in zip(winter_keys, winter_vals):
                self._winter_des_day_dict[key] = val
            summer_keys = self._regex_parse(r"Design Stat	Hottest(.*)", False)
            summer_vals = self._regex_parse(r"Cooling(.*)")
            for key, val in zip(summer_keys, summer_vals):
                self._summer_des_day_dict[key] = val

            # Pull out relevant monthly information
            self._monthly_tau_beam = self._regex_parse(r"taub \(beam\)(.*)")
            self._monthly_tau_diffuse = self._regex_parse(r"taud \(diffuse\)(.*)")
            self._monthly_db_50 = self._regex_parse(r"Drybulb 5.0%(.*)")
            self._monthly_wb_50 = self._regex_parse(r"Coincident Wetbulb 5.0%(.*)")
            self._monthly_db_100 = self._regex_parse(r"Drybulb 10.%(.*)")
            self._monthly_wb_100 = self._regex_parse(r"Coincident Wetbulb 10.%(.*)")
            self._monthly_db_20 = self._regex_parse(r"Drybulb 2.0%(.*)")
            self._monthly_wb_20 = self._regex_parse(r"Coincident Wetbulb 2.0%(.*)")
            self._monthly_db_04 = self._regex_parse(r"Drybulb 0.4%(.*)")
            self._monthly_wb_04 = self._regex_parse(r"Coincident Wetbulb 0.4%(.*)")
            self._monthly_db_range_50 = self._regex_parse(r"Drybulb range - DB 5%(.*)")
            self._monthly_wb_range_50 = self._regex_parse(r"Wetbulb range - DB 5%(.*)")
            self._monthly_wind = self._regex_parse(
                r"Monthly Statistics for Wind Speed[\s\S]*Daily Avg(.*)")
            for direction in self._wind_dir_names:
                re_string = r"Monthly Wind Direction %[\s\S]*" + direction + r"\s(.*)"
                self._monthly_wind_dirs.append(self._regex_parse(re_string))
        finally:
            statwin.close()

    def _regex_parse(self, regex_str, numbr=True):
        pattern = re.compile(regex_str)
        matches = pattern.findall(self._body)
        if len(matches) > 0:
            raw_txt = matches[0].strip().split('\t')
            if numbr is True:
                return [float(i) if 'N' not in i else None for i in raw_txt]
            else:
                return [str(i) for i in raw_txt]
        else:
            return []

    @property
    def header(self):
        """Return stat file header."""
        return self._header

    @property
    def location(self):
        """Return ladybug location object."""
        return self._location

    @property
    def ashrae_climate_zone(self):
        """Return a text string indicating the ASHRAE climate zone.

        ASHRAE climate zones are frequently used to make suggestions for
        heating and cooling systems and correspond to recommendations for
        insulation levels of a building.
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

    def _winter_des_day_conds(self, db_key, ws_key, wd_key):
        """Returns winter design day conditions given keys for the winter dictionary
        """
        db_cond = DryBulbCondition(
            float(self._winter_des_day_dict[db_key]), 0)
        hu_cond = HumidityCondition(
            'Wetbulb', float(self._winter_des_day_dict[db_key]),
            self._stand_press_at_elev)
        ws_cond = WindCondition(
            float(self._winter_des_day_dict[ws_key]),
            float(self._winter_des_day_dict[wd_key]))
        sky_cond = OriginalClearSkyCondition(
            int(self._winter_des_day_dict['Month']), 21, 0)
        return db_cond, hu_cond, ws_cond, sky_cond

    def _summer_des_day_conds(self, db_key, dbr_key, wb_key, ws_key, wd_key):
        """Returns summer design day conditions given keys for the summer dictionary
        """
        db_cond = DryBulbCondition(
            float(self._summer_des_day_dict[db_key]),
            float(self._summer_des_day_dict[dbr_key]))
        hu_cond = HumidityCondition(
            'Wetbulb', float(self._summer_des_day_dict[wb_key]),
            self._stand_press_at_elev)
        ws_cond = WindCondition(
            float(self._summer_des_day_dict[ws_key]),
            float(self._summer_des_day_dict[wd_key]))
        month_num = int(self._summer_des_day_dict['Month'])
        if self._monthly_tau_beam != [] and self._monthly_tau_diffuse != []:
            sky_cond = RevisedClearSkyCondition(
                month_num, 21, self._monthly_tau_beam[month_num - 1],
                self._monthly_tau_diffuse[month_num - 1])
        else:
            sky_cond = OriginalClearSkyCondition(month_num, 21, 0)
        return db_cond, hu_cond, ws_cond, sky_cond

    @property
    def annual_heating_design_day_996(self):
        """A design day object representing the annual 99.6% heating design day.
        """
        if self._winter_des_day_dict == {}:
            return None
        else:
            db_cond, hu_cond, ws_cond, sky_cond = self._winter_des_day_conds(
                'DB996', 'WS_DB996', 'WD_DB996')
            return DesignDay(
                '99.6% Heating Design Day for {}'.format(self._location.city),
                'WinterDesignDay', self._location, db_cond, hu_cond, ws_cond, sky_cond)

    @property
    def annual_heating_design_day_990(self):
        """A design day object representing the annual 99.0% heating design day.
        """
        if self._winter_des_day_dict == {}:
            return None
        else:
            db_cond, hu_cond, ws_cond, sky_cond = self._winter_des_day_conds(
                'DB990', 'WS_DB996', 'WD_DB996')
            return DesignDay(
                '99.0% Heating Design Day for {}'.format(self._location.city),
                'WinterDesignDay', self._location, db_cond, hu_cond, ws_cond, sky_cond)

    @property
    def annual_cooling_design_day_004(self):
        """A design day object representing the annual 0.4% cooling design day.
        """
        if self._summer_des_day_dict == {}:
            return None
        else:
            db_cond, hu_cond, ws_cond, sky_cond = self._summer_des_day_conds(
                'DB004', 'DBR', 'WB_DB004', 'WS_DB004', 'WD_DB004')
            return DesignDay(
                '0.4% Cooling Design Day for {}'.format(self._location.city),
                'SummerDesignDay', self._location, db_cond, hu_cond, ws_cond, sky_cond)

    @property
    def annual_cooling_design_day_010(self):
        """A design day object representing the annual 1.0% cooling design day.
        """
        if self._summer_des_day_dict == {}:
            return None
        else:
            db_cond, hu_cond, ws_cond, sky_cond = self._summer_des_day_conds(
                'DB010', 'DBR', 'WB_DB010', 'WS_DB004', 'WD_DB004')
            return DesignDay(
                '1.0% Cooling Design Day for {}'.format(self._location.city),
                'SummerDesignDay', self._location, db_cond, hu_cond, ws_cond, sky_cond)

    @property
    def monthly_cooling_design_days_050(self):
        """A list of 12 objects representing monthly 5.0% cooling design days.
        """
        db_conds = [DryBulbCondition(x, y) for x, y in zip(
            self._monthly_db_50, self._monthly_db_range_50)]
        hu_conds = [HumidityCondition(
            'Wetbulb', x, self._stand_press_at_elev) for x in self._monthly_wb_50]
        ws_conds = self.monthly_wind_conditions
        sky_conds = self.monthly_clear_sky_conditions
        return [DesignDay(
            '5% Cooling Design Day for {}'.format(self._months[i]), 'SummerDesignDay',
            self._location, db_conds[i], hu_conds[i], ws_conds[i], sky_conds[i])
                       for i in range(12)]

    @property
    def monthly_cooling_design_days_100(self):
        """A list of 12 objects representing monthly 10.0% cooling design days.
        """
        db_conds = [DryBulbCondition(x, y) for x, y in zip(
            self._monthly_db_100, self._monthly_db_range_50)]
        hu_conds = [HumidityCondition(
            'Wetbulb', x, self._stand_press_at_elev) for x in self._monthly_wb_100]
        ws_conds = self.monthly_wind_conditions
        sky_conds = self.monthly_clear_sky_conditions
        return [DesignDay(
            '10% Cooling Design Day for {}'.format(self._months[i]), 'SummerDesignDay',
            self._location, db_conds[i], hu_conds[i], ws_conds[i], sky_conds[i])
                       for i in range(12)]

    @property
    def monthly_cooling_design_days_020(self):
        """A list of 12 objects representing monthly 2.0% cooling design days.
        """
        db_conds = [DryBulbCondition(x, y) for x, y in zip(
            self._monthly_db_20, self._monthly_db_range_50)]
        hu_conds = [HumidityCondition(
            'Wetbulb', x, self._stand_press_at_elev) for x in self._monthly_wb_20]
        ws_conds = self.monthly_wind_conditions
        sky_conds = self.monthly_clear_sky_conditions
        return [DesignDay(
            '2% Cooling Design Day for {}'.format(self._months[i]), 'SummerDesignDay',
            self._location, db_conds[i], hu_conds[i], ws_conds[i], sky_conds[i])
                       for i in range(12)]

    @property
    def monthly_cooling_design_days_004(self):
        """A list of 12 objects representing monthly 0.4% cooling design days.
        """
        db_conds = [DryBulbCondition(x, y) for x, y in zip(
            self._monthly_db_04, self._monthly_db_range_50)]
        hu_conds = [HumidityCondition(
            'Wetbulb', x, self._stand_press_at_elev) for x in self._monthly_wb_04]
        ws_conds = self.monthly_wind_conditions
        sky_conds = self.monthly_clear_sky_conditions
        return [DesignDay(
            '0.4% Cooling Design Day for {}'.format(self._months[i]), 'SummerDesignDay',
            self._location, db_conds[i], hu_conds[i], ws_conds[i], sky_conds[i])
                       for i in range(12)]

    @property
    def monthly_db_temp_050(self):
        """A list of 12 float values for monthly 5.0% dry bulb temperature.
        """
        return self._monthly_db_50

    @property
    def monthly_wb_temp_050(self):
        """A list of 12 float values for monthly 5.0% wet bulb temperature.
        """
        return self._monthly_wb_50

    @property
    def monthly_db_temp_range_050(self):
        """A list of 12 values for monthly ranges of dry bulb temperatures at 5.0%.
        """
        return self._monthly_db_range_50

    @property
    def monthly_wb_temp_range_050(self):
        """A list of 12 values for monthly ranges of wet bulb temperatures at 5.0%.
        """
        return self._monthly_wb_range_50

    @property
    def standard_pressure_at_elev(self):
        """The standard pressure on pascals at the elevation of the location.
        """
        return self._stand_press_at_elev

    @property
    def monthly_wind_conditions(self):
        """A list of 12 monthly wind conditions that are used on the design days.
        """
        return [WindCondition(x, y) for x, y in zip(
            self._monthly_wind, self.monthly_wind_dirs)]

    @property
    def monthly_ws_avg(self):
        """A list of 12 float values for monthly average wind speeds.
        """
        return self._monthly_wind

    @property
    def monthly_wind_dirs(self):
        """A list of prevailing wind directions for each month.
        """
        mwd = zip(*self._monthly_wind_dirs)
        return [self._wind_dirs[mon.index(max(mon))] for mon in mwd]

    @property
    def monthly_clear_sky_conditions(self):
        """A list of 12 monthly clear sky conditions that are used on the design days.
        """
        if self._monthly_tau_diffuse is [] or self._monthly_tau_beam is []:
            return [OriginalClearSkyCondition(i, 21) for i in range(1, 13)]
        return [RevisedClearSkyCondition(i, 21, x, y) for i, x, y in zip(
            range(1, 13), self._monthly_tau_beam, self._monthly_tau_diffuse)]

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

    @property
    def _months(self):
        return ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul',
                'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    @property
    def _wind_dirs(self):
        return [0, 45, 90, 135, 180, 225, 270, 315]

    @property
    def _wind_dir_names(self):
        return ['North', 'NorthEast', 'East', 'SouthEast', 'South',
                'SouthWest', 'West', 'NorthWest']

    @property
    def isStat(self):
        """Return True."""
        return True

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """stat file representation."""
        return "STAT [%s]" % self.location.city
