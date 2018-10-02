from .location import Location
from .futil import write_to_file
from .dt import DateTime
from .header import Header
from .datacollection import DataCollection
from .datatype import DataPoint
from .analysisperiod import AnalysisPeriod
from .sunpath import Sunpath

from .skymodel import ashrae_revised_clear_sky
from .skymodel import ashrae_clear_sky

from .psychrometrics import rel_humid_from_db_dpt
from .psychrometrics import dew_point_from_db_hr
from .psychrometrics import dew_point_from_db_enth
from .psychrometrics import dew_point_from_db_wb

import math
import os
import re
import codecs
import platform

day_types = ['SummerDesignDay', 'WinterDesignDay', 'Sunday', 'Monday',
             'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Holiday',
             'CustomDay1', 'CustomDay2']
h_types = ['Wetbulb', 'Dewpoint', 'HumidityRatio', 'Enthalpy']
sky_types = ['ASHRAEClearSky', 'ASHRAETau', 'ZhangHuang', 'Schedule']
comments = ['!- Name',
            '!- Month',
            '!- Day of Month',
            '!- Day Type',
            '!- Max Dry-Bulb Temp [C]',
            '!- Daily Dry-Bulb Temp Range [C]',
            '!- Dry-Bulb Temp Range Modifier Type',
            '!- Dry-Bulb Temp Range Modifier Schedule Name',
            '!- Humidity Condition Type',
            '!- Wetbulb/Dewpoint at Max Dry-Bulb [C]',
            '!- Humidity Indicating Day Schedule Name',
            '!- Humidity Ratio at Maximum Dry-Bulb {kgWater/kgDryAir}',
            '!- Enthalpy at Maximum Dry-Bulb {J/kg}',
            '!- Daily Wet-Bulb Temperature Range [deltaC]',
            '!- Barometric Pressure [Pa]',
            '!- Wind Speed {m/s}',
            '!- Wind Direction [Degrees; N=0, S=180]',
            '!- Rain [Yes/No]',
            '!- Snow on ground [Yes/No]',
            '!- Daylight Savings Time Indicator',
            '!- Solar Model Indicator',
            '!- Beam Solar Day Schedule Name',
            '!- Diffuse Solar Day Schedule Name',
            '!- ASHRAE Clear Sky Optical Depth for Beam Irradiance (taub)',
            '!- ASHRAE Clear Sky Optical Depth for Diffuse Irradiance (taud)',
            '!- Clearness [0.0 to 1.2]']
temp_multipliers = [0.82, 0.88, 0.92, 0.95, 0.98, 1, 0.98, 0.91, 0.74,
                    0.55, 0.38, 0.23, 0.13, 0.05, 0, 0, 0.06, 0.14, 0.24,
                    0.39, 0.5, 0.59, 0.68, 0.75]


class Ddy(object):
    """Import data from a local .ddy file.

    properties:
        location: A Ladybug location object
        design_days: A list of the design days in the ddy file.
        file_path: Optional file path into which ddy file can be written.
    """
    # TODO: set the default file path to use the ladybug default folder.
    def __init__(self, location, design_days=[], file_path=None):
        """Initalize the class."""
        self.location = location
        self.design_days = design_days
        self.file_path = file_path or 'C:\\ladybug\\unnamed.ddy'

    @classmethod
    def from_ddy_file(cls, file_path):
        """Initalize from a ddy file object from an existing ddy file.

        args:
            file_path: A full string to the .ddy file.
        """
        # defaults
        location = None
        design_days = []

        # check that the file is there
        if not os.path.isfile(file_path):
            raise ValueError(
                'Cannot find an ddy file at {}'.format(file_path))

        # check the python version and open the file
        try:
            iron_python = True if platform.python_implementation() == 'IronPython' \
                else False
        except Exception:
            iron_python = True

        if iron_python:
            ddywin = codecs.open(file_path, 'r')
        else:
            ddywin = codecs.open(file_path, 'r', encoding='utf-8', errors='ignore')

        try:
            ddytxt = ddywin.read()
            location_format = re.compile(
                r"(Site:Location,(.|\n)*?((;\s*!)|(;\s*\n)|(;\n)))")
            design_day_format = re.compile(
                r"(SizingPeriod:DesignDay,(.|\n)*?((;\s*!)|(;\s*\n)|(;\n)))")
            location_matches = location_format.findall(ddytxt)
            des_day_matches = design_day_format.findall(ddytxt)
        except Exception as e:
            import traceback
            raise Exception('{}\n{}'.format(e, traceback.format_exc()))
        else:
            # build design day and location objects
            location = Location.from_location(location_matches[0][0])
            design_days = [DesignDay.from_ep_string(
                match[0], location) for match in des_day_matches]
        finally:
            ddywin.close()

        return cls(location, design_days, file_path)

    @classmethod
    def from_design_day(cls, design_day):
        """Initalize from a ddy file object from a ladybug design day object.
        """
        return cls(design_day.location, [design_day])

    def save(self, folder=None, file_name=None):
        """Save ddy object as a .ddy file."""
        # check file_path
        if not folder:
            folder = self.folder
        if not file_name:
            file_name = os.path.splitext(self.file_name)[0] + '_modified.ddy'
        full_path = os.path.join(folder, file_name)

        # write all data into the file
        # write the file
        data = self.location.ep_style_location_string + '\n\n'
        for d_day in self.design_days:
            data = data + d_day.ep_style_string + '\n\n'
        write_to_file(full_path, data, True)

    def filter_by_keyword(self, keyword):
        """Return a list of ddys that have a certain keyword in their name.

        This is useful for selecting out design days from a ddy file that are
        for a specific type of condition (for example, .4% cooling design days)
        """
        filtered_days = []
        for des_day in self.design_days:
            if keyword in des_day.name:
                filtered_days.append(des_day)
        return filtered_days

    @property
    def file_path(self):
        """Get or set path to ddy file."""
        return self._file_path

    @property
    def folder(self):
        """Get ddy file folder."""
        return self._folder

    @property
    def file_name(self):
        """Get ddy file name."""
        return self._file_name

    @file_path.setter
    def file_path(self, ddy_file_path):
        self._file_path = os.path.normpath(ddy_file_path)

        if not ddy_file_path.lower().endswith('.ddy'):
            self._file_path = self._file_path + '.ddy'

        self._folder, self._file_name = os.path.split(self.file_path)

    @property
    def location(self):
        """Get or set the location."""
        return self._location

    @location.setter
    def location(self, data):
        assert hasattr(data, 'isLocation'), 'Expected' \
            ' Location type. Got {}'.format(str(data))
        self._location = data

    @property
    def design_days(self):
        """Get or set the design_days."""
        return self._design_days

    @design_days.setter
    def design_days(self, data):
        assert isinstance(data, list), 'Expected' \
            ' a list of design days. Got {}'.format(str(data))
        for item in data:
            assert hasattr(item, 'isDesignDay'), 'Expected' \
                ' DesignDay type. Got {}'.format(str(item))
        self._design_days = data
        for dd in self._design_days:
            dd.location = self._location

    @property
    def isDdy(self):
        """Return True."""
        return True

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """Ddy object representation."""
        return "Ddy File - {} [# days: {}]".format(
            self.location.city, str(len(self._design_days)))


# TODO: add a property for hourly horizontal infrared radiation.
class DesignDay(object):
    """An object representing design day conditions.

    properties:
        name: A text string to set the name of the design day
        day_type: Choose from 'SummerDesignDay', 'WinterDesignDay' or other
            EnergyPlus days
        location: Location for the design day
        dry_bulb_condition: Ladyubug DryBulbCondition object
        humidity_condition: Ladyubug HumidityCondition object
        wind_condition: Ladyubug WindCondition object
        sky_condition: Ladybug SkyCondition object
    """

    def __init__(self, name, day_type, location, dry_bulb_condition, humidity_condition,
                 wind_condition, sky_condition):
        """Initalize the class."""
        self.name = str(name)
        self.day_type = day_type
        self.location = location
        self.dry_bulb_condition = dry_bulb_condition
        self.humidity_condition = humidity_condition
        self.wind_condition = wind_condition
        self.sky_condition = sky_condition

    @classmethod
    def from_ep_string(cls, ep_string, location):
        """Initalize from an EnergyPlus string of a SizingPeriod:DesignDay.

        args:
            ep_string: A full string representing a SizingPeriod:DesignDay.
        """
        # format the object into a list of properties
        ep_lines = ep_string.split('\n')
        lines = [l.split('!')[0].strip().replace(',', '') for l in ep_lines]

        # check to be sure that we have a valid ddy object
        assert len(lines) == 27 or len(lines) == 26, "Number " \
            "of lines of text [{}] does not correspond" \
            " to an EP Design Day [26 or 27]".format(
                len(lines))

        # extract primary properties
        lines[-1] = lines[-1].split(';')[0]
        name = lines[1]
        day_type = lines[4]

        # extract dry bulb temperatures
        dry_bulb_condition = DryBulbCondition(
            float(lines[5]), float(lines[6]), lines[7], lines[8])

        # extract humidity conditions
        h_type = lines[9]
        h_val = 0 if lines[10] == '' else float(lines[10])
        if h_type == 'HumidityRatio':
            h_val = float(lines[12])
        elif h_type == 'Enthalpy':
            h_val = float(lines[13])
        humidity_condition = HumidityCondition(
            h_type, h_val, float(lines[15]), lines[11])

        # extract wind conditions
        wind_condition = WindCondition(
            float(lines[16]), float(lines[17]), lines[18], lines[19])

        # extract the sky conditions
        sky_model = lines[21]
        if sky_model == 'ASHRAEClearSky':
            sky_condition = OriginalClearSkyCondition(
                int(lines[2]), int(lines[3]), float(lines[26]), lines[20])
        elif sky_model == 'ASHRAETau':
            sky_condition = RevisedClearSkyCondition(
                int(lines[2]), int(lines[3]), float(lines[24]),
                float(lines[25]), lines[20])
        else:
            sky_condition = SkyCondition(
                sky_model, int(lines[2]), int(lines[3]), lines[20])
        if sky_model == 'Schedule':
            sky_condition.beam_shced = lines[22]
            sky_condition.diff_shced = lines[23]

        return cls(name, day_type, location, dry_bulb_condition,
                   humidity_condition, wind_condition, sky_condition)

    @classmethod
    def from_design_day_properties(cls, name, day_type, location, analysis_period,
                                   dry_bulb_max, dry_bulb_range, humidity_type,
                                   humidity_value, barometric_p, wind_speed, wind_dir,
                                   sky_model, sky_properties):
        """Create a design day object from various key properties.

        Args:
            name: A text string to set the name of the design day
            day_type: Choose from 'SummerDesignDay', 'WinterDesignDay' or other
                EnergyPlus days
            location: Location for the design day
            analysis_period: Analysis period for the design day
            dry_bulb_max: Maximum dry bulb temperature over the design day (in C).
            dry_bulb_range: Dry bulb range over the design day (in C).
            humidity_type: Type of humidity to use. Choose from
                Wetbulb, Dewpoint, HumidityRatio, Enthalpy
            humidity_value: The value of the condition above.
            barometric_p: Barometric pressure in Pa.
            wind_speed: Wind speed over the design day in m/s.
            wind_dir: Wind direction over the design day in degrees.
            sky_model: Type of solar model to use.  Choose from
                ASHRAEClearSky, ASHRAETau
            sky_properties: A list of properties describing the sky above.
                For ASHRAEClearSky this is a single value for clearness
                For ASHRAETau, this is the tau_beam and tau_diffuse
        """
        dry_bulb_condition = DryBulbCondition(
            dry_bulb_max, dry_bulb_range)
        humidity_condition = HumidityCondition(
            humidity_type, humidity_value, barometric_p)
        wind_condition = WindCondition(
            wind_speed, wind_dir)
        if sky_model == 'ASHRAEClearSky':
            sky_condition = OriginalClearSkyCondition.from_analysis_period(
                analysis_period, sky_properties[0])
        elif sky_model == 'ASHRAETau':
            sky_condition = RevisedClearSkyCondition.from_analysis_period(
                analysis_period, sky_properties[0], sky_properties[-1])
        return cls(name, day_type, location, dry_bulb_condition,
                   humidity_condition, wind_condition, sky_condition)

    @property
    def ep_style_string(self):
        """Serialize object to an EnerygPlus SizingPeriod:DesignDay.

        returns:
            ep_string: A full string representing a SizingPeriod:DesignDay.
        """
        # Put together the values in the order that they exist in the ddy file
        ep_vals = [self.name,
                   self.sky_condition.month,
                   self.sky_condition.day_of_month,
                   self.day_type,
                   self.dry_bulb_condition.max_dry_bulb,
                   self.dry_bulb_condition.dry_bulb_range,
                   self.dry_bulb_condition.modifier_type,
                   self.dry_bulb_condition.modifier_schedule,
                   self.humidity_condition.hum_type, '',
                   self.humidity_condition.schedule, '', '',
                   self.humidity_condition.wet_bulb_range,
                   self.humidity_condition.barometric_pressure,
                   self.wind_condition.wind_speed,
                   self.wind_condition.wind_direction,
                   self.wind_condition.rain,
                   self.wind_condition.snow_on_ground,
                   self.sky_condition.daylight_savings_indicator,
                   self.sky_condition.solar_model,
                   self.sky_condition.beam_shced,
                   self.sky_condition.diff_sched, '', '', '']

        # assign humidity values based on the type of criteria
        if self.humidity_condition.hum_type == 'Wetbulb' or \
                self.humidity_condition.hum_type == 'Dewpoint':
                    ep_vals[9] = self.humidity_condition.hum_value
        elif self.humidity_condition.hum_type == 'HumidityRatio':
            ep_vals[11] = self.humidity_condition.hum_value
        elif self.humidity_condition.hum_type == 'Enthalpy':
            ep_vals[12] = self.humidity_condition.hum_value

        # assign sky condition values based on the solar model
        if self.sky_condition.solar_model == 'ASHRAEClearSky':
            ep_vals[25] = self.sky_condition.clearness
        if self.sky_condition.solar_model == 'ASHRAETau':
            ep_vals[23] = self.sky_condition.tau_b
            ep_vals[24] = self.sky_condition._tau_d
            ep_vals.pop()

        # put everything together into one string
        ep_string = ' SizingPeriod:DesignDay,\n'
        separator = ','
        for i, val in enumerate(ep_vals):
            if i == len(ep_vals) - 1:
                separator = ';'
            spacer = ' ' * (60 - len(str(val)))
            ep_string = ep_string + '  ' + str(val) + separator + \
                spacer + comments[i] + '\n'

        return ep_string

    @property
    def name(self):
        """Get or set the name."""
        return self._name

    @name.setter
    def name(self, data):
        assert isinstance(data, str), 'Design day name must be' \
            ' text. Got {}'.format(type(data))
        self._name = data

    @property
    def day_type(self):
        """Get or set the type of design day."""
        return self._day_type

    @day_type.setter
    def day_type(self, data):
        assert data in day_types, 'day_type {} is not' \
            ' recognized'.format(str(data))
        self._day_type = data

    @property
    def location(self):
        """Get or set the location."""
        return self._location

    @location.setter
    def location(self, data):
        assert hasattr(data, 'isLocation'), 'Expected' \
            ' isLocation type. Got {}'.format(str(data))
        self._location = data

    @property
    def dry_bulb_condition(self):
        """Get or set the dry bulb conditions."""
        return self._dry_bulb_condition

    @dry_bulb_condition.setter
    def dry_bulb_condition(self, data):
        assert hasattr(data, 'isDryBulbCondition'), 'Expected' \
            ' DryBulbCondition type. Got {}'.format(str(data))
        self._dry_bulb_condition = data

    @property
    def humidity_condition(self):
        """Get or set the humidity conditions."""
        return self._humidity_condition

    @humidity_condition.setter
    def humidity_condition(self, data):
        assert hasattr(data, 'isHumidityCondition'), 'Expected' \
            ' HumidityCondition type. Got {}'.format(str(data))
        self._humidity_condition = data

    @property
    def wind_condition(self):
        """Get or set the wind conditions."""
        return self._wind_condition

    @wind_condition.setter
    def wind_condition(self, data):
        assert hasattr(data, 'isWindCondition'), 'Expected' \
            ' WindCondition type. Got {}'.format(str(data))
        self._wind_condition = data

    @property
    def sky_condition(self):
        """Get or set the sky conditions."""
        return self._sky_condition

    @sky_condition.setter
    def sky_condition(self, data):
        assert hasattr(data, 'isSkyCondition'), 'Expected' \
            ' SkyCondition type. Got {}'.format(str(data))
        self._sky_condition = data

    @property
    def analysis_period(self):
        """The analysisperiod of the design day."""
        return AnalysisPeriod(
            self.sky_condition.month,
            self.sky_condition.day_of_month,
            0,
            self.sky_condition.month,
            self.sky_condition.day_of_month,
            23)

    @property
    def hourly_datetimes(self):
        return self._sky_condition._get_datetimes()

    @property
    def hourly_dry_bulb_data(self):
        """A data collection containing hourly dry bulb temperature over they day."""
        date_times = self.hourly_datetimes
        hourly_data = [DataPoint(
            x, date_times[i], 'SI', 'Dry Bulb Temperature')
                       for i, x in enumerate(
                           self._dry_bulb_condition.hourly_values)]
        return self._get_daily_data_collections(
            'Dry Bulb Temperature', 'C', hourly_data)

    @property
    def hourly_dew_point_data(self):
        """A data collection containing hourly dew points over they day."""
        date_times = self.hourly_datetimes
        hourly_data = [DataPoint(
            x, date_times[i], 'SI', 'Dew Point Temperature')
                       for i, x in enumerate(
                           self._humidity_condition.hourly_dew_point_values(
                               self._dry_bulb_condition))]
        return self._get_daily_data_collections(
            'Dew Point Temperature', 'C', hourly_data)

    @property
    def hourly_relative_humidity_data(self):
        """A data collection containing hourly relative humidity over they day."""
        date_times = self.hourly_datetimes
        dpt_data = self._humidity_condition.hourly_dew_point_values(
            self._dry_bulb_condition)
        rh_data = [rel_humid_from_db_dpt(x, y) for x, y in zip(
            self._dry_bulb_condition.hourly_values, dpt_data)]
        hourly_data = [DataPoint(
            x, date_times[i], 'SI', 'Relative Humidity')
                       for i, x in enumerate(rh_data)]
        return self._get_daily_data_collections(
            'Relative Humidity', '%', hourly_data)

    @property
    def hourly_barometric_pressure_data(self):
        """A data collection containing hourly barometric pressures over they day."""
        date_times = self.hourly_datetimes
        hourly_data = [DataPoint(
            x, date_times[i], 'SI', 'Atmospheric Station Pressure')
                       for i, x in enumerate(
                           self._humidity_condition.hourly_pressure)]
        return self._get_daily_data_collections(
            'Atmospheric Station Pressure', 'Pa', hourly_data)

    @property
    def hourly_wind_speed_data(self):
        """A data collection containing hourly wind speeds over they day."""
        date_times = self.hourly_datetimes
        hourly_data = [DataPoint(
            x, date_times[i], 'SI', 'Wind Speed')
                       for i, x in enumerate(
                           self._wind_condition.hourly_values)]
        return self._get_daily_data_collections(
            'Wind Speed', 'm/s', hourly_data)

    @property
    def hourly_wind_direction_data(self):
        """A data collection containing hourly wind directions over they day."""
        date_times = self.hourly_datetimes
        hourly_data = [DataPoint(
            x, date_times[i], 'SI', 'Wind Direction')
                       for i, x in enumerate(
                           self._wind_condition.hourly_wind_dirs)]
        return self._get_daily_data_collections(
            'Wind Direction', 'degrees', hourly_data)

    @property
    def hourly_solar_radiation_data(self):
        """Three data collections containing hourly direct normal, diffuse horizontal,
        and global horizontal radiation.
        """
        date_times = self.hourly_datetimes
        dir_norm, diff_horiz, glob_horiz = \
            self._sky_condition.radiation_values(self._location)
        dir_norm_data = [DataPoint(
            x, date_times[i], 'SI', 'Direct Normal Radiation')
                         for i, x in enumerate(dir_norm)]
        dir_norm_collect = self._get_daily_data_collections(
            'Direct Normal Radiation', 'Wh/m2', dir_norm_data)
        diff_horiz_data = [DataPoint(
            x, date_times[i], 'SI', 'Diffuse Horizontal Radiation')
                           for i, x in enumerate(diff_horiz)]
        diff_horiz_collect = self._get_daily_data_collections(
            'Diffuse Horizontal Radiation', 'Wh/m2', diff_horiz_data)
        glob_horiz_data = [DataPoint(
            x, date_times[i], 'SI', 'Global Horizontal Radiation')
                           for i, x in enumerate(glob_horiz)]
        glob_horiz_collect = self._get_daily_data_collections(
            'Global Horizontal Radiation', 'Wh/m2', glob_horiz_data)

        return dir_norm_collect, diff_horiz_collect, glob_horiz_collect

    def _get_daily_data_collections(self, data_type, unit, data=None):
        """Return an empty data collection.
        """
        data_header = Header(self._location, data_type, unit, self.analysis_period)
        return DataCollection(data=data, header=data_header)

    @property
    def isDesignDay(self):
        """Return True."""
        return True

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """Design day representation."""
        return "Design Day - {} [{}]".format(
            self.name, self._day_type)


class DryBulbCondition(object):
    """Represents dry bulb conditions on a design day.

    attributes:
        max_dry_bulb
        dry_bulb_range
        modifier_type
        modifier_schedule
    """
    def __init__(self, max_dry_bulb, dry_bulb_range,
                 modifier_type='DefaultMultipliers', modifier_schedule=''):
        """Initalize the class."""
        self.max_dry_bulb = max_dry_bulb
        self.dry_bulb_range = dry_bulb_range
        self.modifier_type = str(modifier_type)
        self.modifier_schedule = str(modifier_schedule)

    @property
    def hourly_values(self):
        """A list of temperature values for each hour over the design day."""
        return [self._max_dry_bulb - self._dry_bulb_range * x for
                x in temp_multipliers]

    @property
    def max_dry_bulb(self):
        """Get or set the max dry bulb temperature."""
        return self._max_dry_bulb

    @max_dry_bulb.setter
    def max_dry_bulb(self, data):
        assert isinstance(data, (float, int)), 'max_dry_bulb must be an' \
            ' number. Got {}'.format(type(data))
        self._max_dry_bulb = data

    @property
    def dry_bulb_range(self):
        """Get or set the dry bulb range over the day."""
        return self._dry_bulb_range

    @dry_bulb_range.setter
    def dry_bulb_range(self, data):
        assert isinstance(data, (float, int)), 'dry_bulb_range must be a' \
            ' number. Got {}'.format(type(data))
        assert data >= 0, 'dry_bulb_range must be greater than or equal to' \
            ' zero. Got {}'.format(str(data))
        self._dry_bulb_range = data

    @property
    def isDryBulbCondition(self):
        """Return True."""
        return True

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """dry bulb condition representation."""
        return "Dry Bulb Condition [Max: {}, Range: {}]".format(
            str(self._max_dry_bulb), str(self._dry_bulb_range))


class HumidityCondition(object):
    """Represents humidity conditions on the design day.

    attributes:
        hum_type: Choose from
            Wetbulb, Dewpoint, HumidityRatio, Enthalpy
        hum_value: The value of the condition above
        barometric_pressure: Default is to use pressure at sea level
        schedule: Optional humidity schedule
        wet_bulb_range: Optional wet bulb temperature range
    """
    def __init__(self, hum_type, hum_value, barometric_pressure=101325,
                 schedule='', wet_bulb_range=''):
        """Initalize the class."""
        self.hum_type = hum_type
        self.hum_value = hum_value
        self.barometric_pressure = barometric_pressure
        self.schedule = schedule
        self.wet_bulb_range = wet_bulb_range

    def hourly_dew_point_values(self, dry_bulb_condition):
        """Get a list of dew points (C) at each hour over the design day.

        args:
            dry_bulb_condition: The dry bulb condition for the day.
        """
        hourly_dew_point = []
        max_dpt = self.dew_point(dry_bulb_condition.max_dry_bulb)
        for db in dry_bulb_condition.hourly_values:
            if db >= max_dpt:
                hourly_dew_point.append(max_dpt)
            else:
                hourly_dew_point.append(db)
        return hourly_dew_point

    def dew_point(self, db):
        """Get the dew point (C), which is constant throughout the day (except at saturation).

        args:
            db: The maximum dry bulb temperature over the day.
        """
        if self._hum_type == 'Dewpoint':
            return self._hum_value
        elif self._hum_type == 'Wetbulb':
            return dew_point_from_db_wb(
                db, self._hum_value, self._barometric_pressure)
        elif self._hum_type == 'HumidityRatio':
            return dew_point_from_db_hr(
                db, self._hum_value, self._barometric_pressure)
        elif self._hum_type == 'Enthalpy':
            return dew_point_from_db_enth(
                db, self._hum_value / 1000,  self._barometric_pressure)

    @property
    def hourly_pressure(self):
        """A list of barometric pressures for each hour over the design day."""
        return [self._barometric_pressure for x in temp_multipliers]

    @property
    def hum_type(self):
        """Get or set the humidity condition type."""
        return self._hum_type

    @hum_type.setter
    def hum_type(self, data):
        assert data in h_types, 'hum_type {} is not' \
            ' recognized'.format(str(data))
        self._hum_type = data

    @property
    def hum_value(self):
        """Get or set the value of the humidity."""
        return self._hum_value

    @hum_value.setter
    def hum_value(self, data):
        assert isinstance(data, (float, int)), 'hum_value must be a' \
            ' number. Got {}'.format(type(data))
        self._hum_value = data

    @property
    def barometric_pressure(self):
        """Get or set the value of the barometric pressure."""
        return self._barometric_pressure

    @barometric_pressure.setter
    def barometric_pressure(self, data):
        assert isinstance(data, (float, int)), 'barometric_pressure must be a' \
            ' number. Got {}'.format(type(data))
        self._barometric_pressure = data

    @property
    def isHumidityCondition(self):
        """Return True."""
        return True

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """humidity condition representation."""
        return "HumidityCondition [{}: {}]".format(
            self._hum_type, str(self._hum_value))


class WindCondition(object):
    """Represents wind and rain conditions on the design day.

    attributes:
        wind_speed
        wind_direction
        rain
        snow_on_ground
    """
    def __init__(self, wind_speed, wind_direction=0,
                 rain='No', snow_on_ground='No'):
        """Initalize the class."""
        self.wind_speed = wind_speed
        self.wind_direction = wind_direction
        self.rain = rain
        self.snow_on_ground = snow_on_ground

    @property
    def hourly_values(self):
        """A list of wind speed values for each hour over the design day."""
        return [self._wind_speed for i in range(24)]

    @property
    def hourly_wind_dirs(self):
        """A list of wind directions for each hour over the design day."""
        return [self._wind_direction for i in range(24)]

    @property
    def wind_speed(self):
        """Get or set the wind speed."""
        return self._wind_speed

    @wind_speed.setter
    def wind_speed(self, data):
        assert isinstance(data, (float, int)), 'wind_speed must be a' \
            ' number. Got {}'.format(type(data))
        self._wind_speed = data

    @property
    def wind_direction(self):
        """Get or set the wind direction."""
        return self._wind_direction

    @wind_direction.setter
    def wind_direction(self, data):
        assert isinstance(data, (float, int)), 'wind_direction must be a' \
            ' number. Got {}'.format(type(data))
        assert 0 <= data <= 360, 'wind_direction {} is not between' \
            ' 0 and 360'.format(str(data))
        self._wind_direction = data

    @property
    def isWindCondition(self):
        """Return True."""
        return True

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """wind condition representation."""
        return "WindCondition [Speed: {}; Dir: {}]".format(
            str(self._wind_speed), str(self._wind_direction))


# TODO: add support for zhang huang solar model in sky condition object.
class SkyCondition(object):
    """An object representing a sky on the design day.

    attributes:
        solar_model
        month
        day_of_month
        daylight_savings_indicator
    """
    def __init__(self, solar_model, month, day_of_month,
                 daylight_savings_indicator='No',
                 beam_shced='', diff_sched=''):
        """Initalize the class."""
        self.solar_model = solar_model
        self.month = month
        self.day_of_month = day_of_month
        self.daylight_savings_indicator = daylight_savings_indicator
        self.beam_shced = beam_shced
        self.diff_sched = diff_sched

    @property
    def solar_model(self):
        """Get or set the type of solar model."""
        return self._solar_model

    @solar_model.setter
    def solar_model(self, data):
        assert data in sky_types, 'solar_model {} is not' \
            ' recognized'.format(str(data))
        self._solar_model = data

    @property
    def month(self):
        """Get or set the month of the design day."""
        return self._month

    @month.setter
    def month(self, data):
        assert isinstance(data, int), 'month must be a' \
            ' integer. Got {}'.format(type(data))
        assert 1 <= data <= 12, 'month {} is not between' \
            ' 1 and 12'.format(str(data))
        self._month = data

    @property
    def day_of_month(self):
        """Get or set the day of the month of the design day."""
        return self._day_of_month

    @day_of_month.setter
    def day_of_month(self, data):
        assert isinstance(data, int), 'day_of_month must be a' \
            ' integer. Got {}'.format(type(data))
        assert 1 <= data <= 31, 'day_of_month {} is not between' \
            ' 1 and 31'.format(str(data))
        self._day_of_month = data

    def _get_datetimes(self, timestep=1):
        """List of datetimes based on design day date and timestep."""
        start_moy = DateTime(self._month, self._day_of_month).moy
        if timestep == 1:
            start_moy = start_moy + 30
        num_moys = 24 * timestep
        return tuple(
            DateTime.from_moy(start_moy + (i * (1 / timestep) * 60))
            for i in range(num_moys)
        )

    @property
    def isSkyCondition(self):
        """Return True."""
        return True

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """sky condition representation."""
        return "SkyCondition {} [Month: {}, Day: {}]".format(
            self._solar_model, str(self._month), str(self._day_of_month))


class OriginalClearSkyCondition(SkyCondition):
    """An object representing an original ASHRAE Clear Sky.

    attributes:
        month
        day_of_month
        clearness
        daylight_savings_indicator
    """
    def __init__(self, month, day_of_month, clearness=1,
                 daylight_savings_indicator='No'):
        """Init class."""
        self.clearness = clearness
        SkyCondition.__init__(self, 'ASHRAEClearSky', month, day_of_month,
                              daylight_savings_indicator)

    @classmethod
    def from_analysis_period(cls, analysis_period, clearness=1,
                             daylight_savings_indicator='No'):
        """"Initialize a OriginalClearSkyCondition from an analysis_period"""
        _check_analysis_period(analysis_period)
        return cls(analysis_period.st_month, analysis_period.st_day, clearness,
                   daylight_savings_indicator)

    @property
    def clearness(self):
        """Get or set the sky clearness."""
        return self._clearness

    @clearness.setter
    def clearness(self, data):
        assert isinstance(data, (float, int)), 'clearness must be a' \
            ' number. Got {}'.format(type(data))
        assert 0 <= data <= 1.2, 'clearness {} is not between' \
            ' 0 and 1.2'.format(str(data))
        self._clearness = data

    def radiation_values(self, location, timestep=1):
        """Lists of driect normal, diffuse horiz, and global horiz rad at each timestep.
        """
        # create sunpath and get altitude at every timestep of the design day
        sp = Sunpath.from_location(location)
        altitudes = []
        dates = self._get_datetimes(timestep)
        for t_date in dates:
            sun = sp.calculate_sun_from_date_time(t_date)
            altitudes.append(sun.altitude)
        dir_norm, diff_horiz = ashrae_clear_sky(
            altitudes, self._month, self._clearness)
        glob_horiz = [dhr + dnr * math.sin(math.radians(alt)) for
                      alt, dnr, dhr in zip(altitudes, dir_norm, diff_horiz)]
        return dir_norm, diff_horiz, glob_horiz


class RevisedClearSkyCondition(SkyCondition):
    """An object representing an ASHRAE Revised Clear Sky (Tau model).

    attributes:
        month
        day_of_month
        tau_b
        tau_d
        daylight_savings_indicator
    """
    def __init__(self, month, day_of_month, tau_b, tau_d,
                 daylight_savings_indicator='No'):
        """Init class."""
        self.tau_b = tau_b
        self.tau_d = tau_d
        SkyCondition.__init__(self, 'ASHRAETau', month, day_of_month,
                              daylight_savings_indicator)

    @classmethod
    def from_analysis_period(cls, analysis_period, tau_b, tau_d,
                             daylight_savings_indicator='No'):
        """"Initialize a RevisedClearSkyCondition from an analysis_period"""
        _check_analysis_period(analysis_period)
        return cls(analysis_period.st_month, analysis_period.st_day, tau_b, tau_d,
                   daylight_savings_indicator)

    @property
    def tau_b(self):
        """Get or set the beam optical sky depth."""
        return self._tau_b

    @tau_b.setter
    def tau_b(self, data):
        assert isinstance(data, (float, int)), 'tau_b must be a' \
            ' number. Got {}'.format(type(data))
        self._tau_b = data

    @property
    def tau_d(self):
        """Get or set the diffuse optical sky depth."""
        return self._tau_d

    @tau_d.setter
    def tau_d(self, data):
        assert isinstance(data, (float, int)), 'tau_d must be a' \
            ' number. Got {}'.format(type(data))
        self._tau_d = data

    def radiation_values(self, location, timestep=1):
        """Lists of driect normal, diffuse horiz, and global horiz rad at each timestep.
        """
        # create sunpath and get altitude at every timestep of the design day
        sp = Sunpath.from_location(location)
        altitudes = []
        dates = self._get_datetimes(timestep)
        for t_date in dates:
            sun = sp.calculate_sun_from_date_time(t_date)
            altitudes.append(sun.altitude)
        dir_norm, diff_horiz = ashrae_revised_clear_sky(
            altitudes, self._tau_b, self._tau_d)
        glob_horiz = [dhr + dnr * math.sin(math.radians(alt)) for
                      alt, dnr, dhr in zip(altitudes, dir_norm, diff_horiz)]
        return dir_norm, diff_horiz, glob_horiz


def _check_analysis_period(analysis_period):
    assert hasattr(analysis_period, 'isAnalysisPeriod'), 'Expected' \
        ' AnalysisPeriod type. Got {}'.format(str(analysis_period))
    assert analysis_period.st_month == analysis_period.end_month and \
        analysis_period.st_day == analysis_period.end_day and \
        analysis_period.st_hour == 0 and analysis_period.end_hour == 23, \
        'analysis_period "{}" does not represent a single day'.format(
            str(analysis_period))
