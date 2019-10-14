# coding=utf-8
from __future__ import division

from .location import Location
from .futil import write_to_file
from .dt import DateTime
from .header import Header
from .analysisperiod import AnalysisPeriod
from .datacollection import HourlyContinuousCollection
from .sunpath import Sunpath

from .datatype import angle, energyflux, energyintensity, \
    fraction, pressure, speed, temperature

from .skymodel import ashrae_revised_clear_sky, \
    ashrae_clear_sky, calc_horizontal_infrared

from .psychrometrics import rel_humid_from_db_dpt, dew_point_from_db_hr, \
    dew_point_from_db_enth, dew_point_from_db_wb

import math
import os
import re
import codecs
import platform
import sys
if (sys.version_info > (3, 0)):
    xrange = range


class DDY(object):
    """A DDY object containing all of the data of a .ddy file.

    Args:
        location: A Ladybug location object
        design_days: A list of the design days in the ddy file.

    Properties:
        * file_locatiom
        * location
        * design_days
    """
    _location_format = re.compile(
        r"(Site:Location,(.|\n)*?((;\s*!)|(;\s*\n)|(;\n)))")
    _design_day_format = re.compile(
        r"(SizingPeriod:DesignDay,(.|\n)*?((;\s*!)|(;\s*\n)|(;\n)))")

    def __init__(self, location, design_days):
        """Initalize the class."""
        assert hasattr(location, 'isLocation'), 'Expected' \
            ' Location type. Got {}'.format(type(location))

        self._location = location
        self.design_days = design_days
        self._file_path = None

    @classmethod
    def from_dict(cls, data):
        """Create a DDY from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "location": {}  # ladybug Location schema,
            "design_days": []  # list of ladybug DesignDay schemas
            }
        """
        required_keys = ('location', 'design_days')
        for key in required_keys:
            assert key in data, 'Required key "{}" is missing!'.format(key)

        return cls(Location.from_dict(data['location']),
                   [DesignDay.from_dict(des_day) for des_day in data['design_days']])

    @classmethod
    def from_ddy_file(cls, file_path):
        """Initalize from a ddy file object from an existing ddy file.

        Args:
            file_path: A string representing a complete path to the .ddy file.
        """
        # check that the file is there
        if not os.path.isfile(file_path):
            raise ValueError(
                'Cannot find a .ddy file at {}'.format(file_path))
        if not file_path.lower().endswith('.ddy'):
            raise ValueError(
                'DDY file does not have a .ddy extension.')

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
            location_matches = cls._location_format.findall(ddytxt)
            des_day_matches = cls._design_day_format.findall(ddytxt)
        except Exception as e:
            import traceback
            raise Exception('{}\n{}'.format(e, traceback.format_exc()))
        else:
            # check to be sure location was found
            assert len(location_matches) > 0, 'No location objects found ' \
                'in .ddy file.'

            # build design day and location objects
            location = Location.from_location(location_matches[0][0])
            design_days = [DesignDay.from_ep_string(
                match[0], location) for match in des_day_matches]
        finally:
            ddywin.close()

        cls_ = cls(location, design_days)
        cls_._file_path = os.path.normpath(file_path)
        return cls_

    @classmethod
    def from_design_day(cls, design_day):
        """Initalize from a ddy file object from a ladybug design day object.

        Args:
            design_day: A Ladybug DesignDay object.
        """
        return cls(design_day.location, [design_day])

    def save(self, file_path):
        """Save ddy object as a .ddy file.

        Args:
            file_path: A string representing the path to write the ddy file to.
        """
        # write all data into the file
        # write the file
        data = self.location.ep_style_location_string + '\n\n'
        for d_day in self.design_days:
            data = data + d_day.ep_style_string + '\n\n'
        write_to_file(file_path, data, True)

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
        """Return the current ddy ddy file."""
        return self._file_path

    @property
    def location(self):
        """Get or set the location."""
        return self._location

    @location.setter
    def location(self, data):
        assert hasattr(data, 'isLocation'), 'Expected' \
            ' Location type. Got {}'.format(type(data))
        self._location = data
        for dd in self._design_days:
            if dd.location != self._location:
                dd.location = self._location
                print('Updating location of {} to {}.'.format(dd, self._location))

    @property
    def design_days(self):
        """Get or set the design_days."""
        return self._design_days

    @design_days.setter
    def design_days(self, data):
        assert isinstance(data, list), 'Expected' \
            ' a list of design days. Got {}'.format(type(data))
        for item in data:
            assert hasattr(item, 'isDesignDay'), 'Expected' \
                ' DesignDay type. Got {}'.format(type(item))
        self._design_days = data
        for dd in self._design_days:
            if dd.location != self._location:
                dd.location = self._location
                print('Updating location of {} to {}.'.format(dd, self._location))

    @property
    def isDdy(self):
        """Return True."""
        return True

    def to_dict(self):
        """Convert the Design Day to a dictionary."""
        return {
            'location': self.location.to_dict(),
            'design_days': [des_d.to_dict() for des_d in self.design_days],
            'type': 'DDY'
        }

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

    Args:
        name: A text string to set the name of the design day
        day_type: Choose from 'SummerDesignDay', 'WinterDesignDay' or other
            EnergyPlus days visible under the day_types property of this object.
        location: Location object for the design day
        dry_bulb_condition: Ladyubug DryBulbCondition object
        humidity_condition: Ladyubug HumidityCondition object
        wind_condition: Ladyubug WindCondition object
        sky_condition: Ladybug SkyCondition object

    Properties:
        * name
        * day_type
        * location
        * dry_bulb_condition
        * hourly_barometric_pressure
        * hourly_datetimes
        * hourly_dew_point
        * hourly_dry_bulb
        * hourly_horizontal_infrared
        * hourly_relative_humidity
        * hourly_sky_cover
        * hourly_solar_radiation
        * hourly_wind_direction
        * hourly_wind_speed
        * humidity_condition
        * name
        * sky_condition
        * wind_condition
    """
    # possible day types
    day_types = ('SummerDesignDay', 'WinterDesignDay', 'Sunday', 'Monday',
                 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Holiday',
                 'CustomDay1', 'CustomDay2')

    # keys denoting the values from which design days are derived
    # these keys and their order com from Climate Design Data of ASHRAE Handbook
    heating_keys = ('Month', 'DB996', 'DB990', 'DP996', 'HR_DP996', 'DB_DP996',
                    'DP990', 'HR_DP990', 'DB_DP990', 'WS004c', 'DB_WS004c',
                    'WS010c', 'DB_WS010c', 'WS_DB996', 'WD_DB996')
    cooling_keys = ('Month', 'DBR', 'DB004', 'WB_DB004', 'DB010', 'WB_DB010',
                    'DB020', 'WB_DB020', 'WB004', 'DB_WB004', 'WB010', 'DB_WB010',
                    'WB020', 'DB_WB020', 'WS_DB004', 'WD_DB004', 'DP004',
                    'HR_DP004', 'DB_DP004', 'DP010', 'HR_DP010', 'DB_DP010',
                    'DP020', 'HR_DP020', 'DB_DP020', 'EN004', 'DB_EN004',
                    'EN010', 'DB_EN010', 'EN020', 'DB_EN020', 'Hrs_8-4_&_DB')
    extreme_keys = ('WS010', 'WS025', 'WS050', 'WBmax', 'DBmin_mean', 'DBmax_mean',
                    'DBmin_stddev', 'DBmax_stddev', 'DBmin05years', 'DBmax05years',
                    'DBmin10years', 'DBmax10years', 'DBmin20years', 'DBmax20years',
                    'DBmin50years', 'DBmax50years')

    # comments that go along with the EP string representation of the design day
    comments = ('!- Name',
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
                '!- Clearness [0.0 to 1.2]')

    def __init__(self, name, day_type, location,
                 dry_bulb_condition, humidity_condition,
                 wind_condition, sky_condition):
        """Initalize the class
        """
        self.name = str(name)
        self.day_type = day_type
        self.location = location
        self.dry_bulb_condition = dry_bulb_condition
        self.humidity_condition = humidity_condition
        self.wind_condition = wind_condition
        self.sky_condition = sky_condition

    @classmethod
    def from_dict(cls, data):
        """Create a Design Day from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "name": "",  # string
            "day_type": "",  # string
            "location": {},  # ladybug Location schema
            "dry_bulb_condition": {},  # ladybug DryBulbCondition schema
            "humidity_condition": {},  # ladybug HumidityCondition schema
            "wind_condition": {},  # ladybug WindCondition schema
            "sky_condition": {}  # ladybug SkyCondition schema
            }
        """
        required_keys = ('name', 'day_type', 'location', 'dry_bulb_condition',
                         'humidity_condition', 'wind_condition', 'sky_condition')
        for key in required_keys:
            assert key in data, 'Required key "{}" is missing!'.format(key)

        return cls(data['name'], data['day_type'], Location.from_dict(data['location']),
                   DryBulbCondition.from_dict(data['dry_bulb_condition']),
                   HumidityCondition.from_dict(data['humidity_condition']),
                   WindCondition.from_dict(data['wind_condition']),
                   SkyCondition.from_dict(data['sky_condition']))

    @classmethod
    def from_ep_string(cls, ep_string, location):
        """Initalize from an EnergyPlus string of a SizingPeriod:DesignDay.

        Args:
            ep_string: A full string representing a SizingPeriod:DesignDay.
        """
        # format the object into a list of properties
        ep_string = ep_string.strip()
        if '\n' in ep_string:
            ep_lines = ep_string.split('\n')
        else:
            ep_lines = ep_string.split('\r')
        lines = [l.split('!')[0].strip().replace(',', '') for l in ep_lines]

        # check to be sure that we have a valid ddy object
        assert len(lines) == 27 or len(lines) == 26, "Number " \
            "of lines of text [{}] does not correspond" \
            " to an EP Design Day [26 or 27]".format(
                len(lines))
        lines[-1] = lines[-1].split(';')[0]

        # extract primary properties
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

    @classmethod
    def from_ashrae_dict_heating(cls, ashrae_dict, location,
                                 use_990=False, pressure=None):
        """Create a heating design day object from a ASHRAE HOF dictionary.

        Args:
            ashrae_dict: A dictionary with 15 keys that match those in the
                heating_keys property of this object. Each key should
                correspond to a value.
            location: Location object for the design day
            use_990: Boolean to denote what type of design day to create
                (wether it is a 99.0% or a 99.6% design day).  Default is
                False for a 99.6% annual heating design day
            pressure: Atmospheric pressure in Pa that should be used in the
                creation of the humidity condition. Default is 101325 Pa
                for pressure at sea level.
        """
        db_key = 'DB996' if use_990 is False else 'DB990'
        perc_str = '99.6' if use_990 is False else '99.0'
        pressure = pressure if pressure is not None else 101325
        db_cond = DryBulbCondition(float(ashrae_dict[db_key]), 0)
        hu_cond = HumidityCondition('Wetbulb', float(ashrae_dict[db_key]), pressure)
        ws_cond = WindCondition(float(ashrae_dict['WS_DB996']),
                                float(ashrae_dict['WD_DB996']))
        sky_cond = OriginalClearSkyCondition(int(ashrae_dict['Month']), 21, 0)
        name = '{}% Heating Design Day for {}'.format(perc_str, location.city)
        return cls(name, 'WinterDesignDay', location,
                   db_cond, hu_cond, ws_cond, sky_cond)

    @classmethod
    def from_ashrae_dict_cooling(cls, ashrae_dict, location,
                                 use_010=False, pressure=None, tau=None):
        """Create a heating design day object from a ASHRAE HOF dictionary.

        Args:
            ashrae_dict: A dictionary with 32 keys that match those in the
                cooling_keys property of this object. Each key should
                correspond to a value.
            location: Location object for the design day
            use_010: Boolean to denote what type of design day to create
                (wether it is a 1.0% or a 0.4% design day).  Default is
                False for a 0.4% annual cooling design day
            pressure: Atmospheric pressure in Pa that should be used in the
                creation of the humidity condition. Default is 101325 Pa
                for pressure at sea level.
            tau: Optional tuple containing two values, which will set the
                sky condition to be a revised ASHRAE clear sky (Tau model).
                The first item of the tuple should be the tau beam value
                and the second is for the tau diffuse value.  Default is
                None, which will default to the original ASHRAE Clear Sky.
        """
        db_key = 'DB004' if use_010 is False else 'DB010'
        wb_key = 'WB_DB004' if use_010 is False else 'WB_DB010'
        perc_str = '0.4' if use_010 is False else '1.0'
        pressure = pressure if pressure is not None else 101325
        db_cond = DryBulbCondition(float(ashrae_dict[db_key]), float(ashrae_dict['DBR']))
        hu_cond = HumidityCondition('Wetbulb', float(ashrae_dict[wb_key]), pressure)
        ws_cond = WindCondition(float(ashrae_dict['WS_DB004']),
                                float(ashrae_dict['WD_DB004']))
        month_num = int(ashrae_dict['Month'])
        if tau is not None:
            sky_cond = RevisedClearSkyCondition(month_num, 21, tau[0], tau[1])
        else:
            sky_cond = OriginalClearSkyCondition(month_num, 21)
        name = '{}% Cooling Design Day for {}'.format(perc_str, location.city)
        return cls(name, 'SummerDesignDay', location,
                   db_cond, hu_cond, ws_cond, sky_cond)

    @property
    def ep_style_string(self):
        """Serialize object to an EnerygPlus SizingPeriod:DesignDay.

        Returns:
            ep_string -- A full string representing a SizingPeriod:DesignDay.
        """
        # Put together the values in the order that they exist in the ddy file
        ep_vals = [self.name,
                   self.sky_condition.month,
                   self.sky_condition.day_of_month,
                   self.day_type,
                   self.dry_bulb_condition.dry_bulb_max,
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
        comented_str = ['  {},{}{}\n'.format(
            str(val), ' ' * (60 - len(str(val))), self.comments[i])
                        for i, val in enumerate(ep_vals)]
        comented_str[-1] = comented_str[-1].replace(',', ';')
        comented_str.insert(0, 'SizingPeriod:DesignDay,\n')
        comented_str.append('\n')

        return ''.join(comented_str)

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
        assert data in self.day_types, 'day_type {} is not' \
            ' recognized'.format(data)
        self._day_type = data

    @property
    def location(self):
        """Get or set the location."""
        return self._location

    @location.setter
    def location(self, data):
        assert hasattr(data, 'isLocation'), 'Expected' \
            ' Location type. Got {}'.format(type(data))
        self._location = data

    @property
    def dry_bulb_condition(self):
        """Get or set the dry bulb conditions."""
        return self._dry_bulb_condition

    @dry_bulb_condition.setter
    def dry_bulb_condition(self, data):
        assert hasattr(data, 'isDryBulbCondition'), 'Expected' \
            ' DryBulbCondition type. Got {}'.format(type(data))
        self._dry_bulb_condition = data

    @property
    def humidity_condition(self):
        """Get or set the humidity conditions."""
        return self._humidity_condition

    @humidity_condition.setter
    def humidity_condition(self, data):
        assert hasattr(data, 'isHumidityCondition'), 'Expected' \
            ' HumidityCondition type. Got {}'.format(type(data))
        self._humidity_condition = data

    @property
    def wind_condition(self):
        """Get or set the wind conditions."""
        return self._wind_condition

    @wind_condition.setter
    def wind_condition(self, data):
        assert hasattr(data, 'isWindCondition'), 'Expected' \
            ' WindCondition type. Got {}'.format(type(data))
        self._wind_condition = data

    @property
    def sky_condition(self):
        """Get or set the sky conditions."""
        return self._sky_condition

    @sky_condition.setter
    def sky_condition(self, data):
        assert hasattr(data, 'isSkyCondition'), 'Expected' \
            ' SkyCondition type. Got {}'.format(type(data))
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
    def hourly_dry_bulb(self):
        """A data collection containing hourly dry bulb temperature over they day."""
        return self._get_daily_data_collections(
            temperature.DryBulbTemperature(), 'C',
            self._dry_bulb_condition.hourly_values)

    @property
    def hourly_dew_point(self):
        """A data collection containing hourly dew points over they day."""
        dpt_data = self._humidity_condition.hourly_dew_point_values(
            self._dry_bulb_condition)
        return self._get_daily_data_collections(
            temperature.DewPointTemperature(), 'C', dpt_data)

    @property
    def hourly_relative_humidity(self):
        """A data collection containing hourly relative humidity over they day."""
        dpt_data = self._humidity_condition.hourly_dew_point_values(
            self._dry_bulb_condition)
        rh_data = [rel_humid_from_db_dpt(x, y) for x, y in zip(
            self._dry_bulb_condition.hourly_values, dpt_data)]
        return self._get_daily_data_collections(
            fraction.RelativeHumidity(), '%', rh_data)

    @property
    def hourly_barometric_pressure(self):
        """A data collection containing hourly barometric pressures over they day."""
        return self._get_daily_data_collections(
            pressure.AtmosphericStationPressure(), 'Pa',
            self._humidity_condition.hourly_pressure)

    @property
    def hourly_wind_speed(self):
        """A data collection containing hourly wind speeds over they day."""
        return self._get_daily_data_collections(
            speed.WindSpeed(), 'm/s', self._wind_condition.hourly_values)

    @property
    def hourly_wind_direction(self):
        """A data collection containing hourly wind directions over they day."""
        return self._get_daily_data_collections(
            angle.WindDirection(), 'degrees', self._wind_condition.hourly_wind_dirs)

    @property
    def hourly_solar_radiation(self):
        """Three data collections containing hourly direct normal, diffuse horizontal,
        and global horizontal radiation.
        """
        dir_norm, diff_horiz, glob_horiz = \
            self._sky_condition.radiation_values(self._location)

        dir_norm_data = self._get_daily_data_collections(
            energyintensity.DirectNormalRadiation(), 'Wh/m2', dir_norm)
        diff_horiz_data = self._get_daily_data_collections(
            energyintensity.DiffuseHorizontalRadiation(), 'Wh/m2', diff_horiz)
        glob_horiz_data = self._get_daily_data_collections(
            energyintensity.GlobalHorizontalRadiation(), 'Wh/m2', glob_horiz)

        return dir_norm_data, diff_horiz_data, glob_horiz_data

    @property
    def hourly_sky_cover(self):
        """A data collection containing hourly sky cover values in tenths."""
        return self._get_daily_data_collections(
            fraction.TotalSkyCover(), 'tenths', self._sky_condition.hourly_sky_cover)

    @property
    def hourly_horizontal_infrared(self):
        """A data collection containing hourly horizontal infrared intensity in W/m2.
        """
        sky_cover = self._sky_condition.hourly_sky_cover
        db_temp = self._dry_bulb_condition.hourly_values
        dp_temp = self._humidity_condition.hourly_dew_point_values(
            self._dry_bulb_condition)

        horiz_ir = []
        for i in xrange(len(sky_cover)):
            horiz_ir.append(
                calc_horizontal_infrared(sky_cover[i], db_temp[i], dp_temp[i]))

        return self._get_daily_data_collections(
            energyflux.HorizontalInfraredRadiationIntensity(), 'W/m2', horiz_ir)

    def _get_daily_data_collections(self, data_type, unit, values):
        """Return an empty data collection."""
        data_header = Header(data_type=data_type, unit=unit,
                             analysis_period=self.analysis_period,
                             metadata={'source': self._location.source,
                                       'country': self._location.country,
                                       'city': self._location.city})
        return HourlyContinuousCollection(data_header, values)

    @property
    def isDesignDay(self):
        """Return True."""
        return True

    def to_dict(self):
        """Convert the Design Day to a dictionary."""
        return {
            'name': self.name,
            'day_type': self.day_type,
            'location': self.location.to_dict(),
            'dry_bulb_condition': self.dry_bulb_condition.to_dict(),
            'humidity_condition': self.humidity_condition.to_dict(),
            'wind_condition': self.wind_condition.to_dict(),
            'sky_condition': self.sky_condition.to_dict(),
            'type': 'DesignDay'
        }

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """Design day representation."""
        return "Design Day - {} [{}]".format(
            self.name, self._day_type)


class DryBulbCondition(object):
    """Represents dry bulb conditions on a design day.

    Args:
        dry_bulb_max: The maximum dry bulb temperature on the design day [C].
        dry_bulb_range: The difference between mina dn max temperatures on the
            design day [C].
        modifier_type: Text string for the type of modifier used to estimate
            temperature at a given timestep. Choose from the following:
            'DefaultMultipliers', 'MultiplierSchedule', 'DifferenceSchedule',
            'TemperatureProfileSchedule'. Default: 'DefaultMultipliers'
        modifier_schedule: Optional text string for the name of the modifier
            schedule. Should be an empty string unless 'MultiplierSchedule' is
            selected as the modifier_type.

    Properties:
        * dry_bulb_max
        * dry_bulb_range
        * hourly_values
        * temp_multipliers
    """
    def __init__(self, dry_bulb_max, dry_bulb_range,
                 modifier_type='DefaultMultipliers', modifier_schedule=''):
        """Initalize the class."""
        self.dry_bulb_max = dry_bulb_max
        self.dry_bulb_range = dry_bulb_range
        self.modifier_type = str(modifier_type)
        self.modifier_schedule = str(modifier_schedule)

    @classmethod
    def from_dict(cls, data):
        """Create a Dry Bulb Condition from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "dry_bulb_max": 0.0  # float,
            "dry_bulb_range": 0.0  # float,
            "modifier_type": ""  # string,
            "modifier_schedule": ""  # string
            }
        """
        # Check required and optional keys
        required_keys = ('dry_bulb_max', 'dry_bulb_range')
        optional_keys = {'modifier_type': 'DefaultMultipliers',
                         'modifier_schedule': ''}
        for key in required_keys:
            assert key in data, 'Required key "{}" is missing!'.format(key)
        for key, val in optional_keys.items():
            if key not in data:
                data[key] = val

        return cls(data['dry_bulb_max'], data['dry_bulb_range'], data['modifier_type'],
                   data['modifier_schedule'])

    @property
    def hourly_values(self):
        """A list of temperature values for each hour over the design day."""
        return [self._dry_bulb_max - self._dry_bulb_range * x for
                x in self.temp_multipliers]

    @property
    def dry_bulb_max(self):
        """Get or set the max dry bulb temperature."""
        return self._dry_bulb_max

    @dry_bulb_max.setter
    def dry_bulb_max(self, data):
        assert isinstance(data, (float, int)), 'dry_bulb_max must be a' \
            ' number. Got {}'.format(type(data))
        self._dry_bulb_max = data

    @property
    def dry_bulb_range(self):
        """Get or set the dry bulb range over the day."""
        return self._dry_bulb_range

    @dry_bulb_range.setter
    def dry_bulb_range(self, data):
        assert isinstance(data, (float, int)), 'dry_bulb_range must be a' \
            ' number. Got {}'.format(type(data))
        assert data >= 0, 'dry_bulb_range must be greater than or equal to' \
            ' zero. Got {}'.format(data)
        self._dry_bulb_range = data

    @property
    def temp_multipliers(self):
        """Fractional multipliers for temperature change over the design day."""
        return (0.82, 0.88, 0.92, 0.95, 0.98, 1, 0.98, 0.91, 0.74, 0.55,
                0.38, 0.23, 0.13, 0.05, 0, 0, 0.06, 0.14, 0.24, 0.39, 0.5,
                0.59, 0.68, 0.75)

    @property
    def isDryBulbCondition(self):
        """Return True."""
        return True

    def to_dict(self):
        """Convert the Dry Bulb Condition to a dictionary."""
        return {
            'dry_bulb_max': self.dry_bulb_max,
            'dry_bulb_range': self.dry_bulb_range,
            'modifier_type': self.modifier_type,
            'modifier_schedule': self.modifier_schedule,
            'type': 'DryBulbCondition'
        }

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """dry bulb condition representation."""
        return "Dry Bulb Condition [Max: {}, Range: {}]".format(
            str(self._dry_bulb_max), str(self._dry_bulb_range))


class HumidityCondition(object):
    """Represents humidity conditions on the design day.

    Args:
        hum_type: Choose from
            Wetbulb, Dewpoint, HumidityRatio, Enthalpy
        hum_value: The value of the condition above
        barometric_pressure: Default is to use pressure at sea level
        schedule: Optional humidity schedule
        wet_bulb_range: Optional wet bulb temperature range

    Properties:
        * hum_type
        * hum_value
        * barometric_pressure
        * schedule
        * wet_bulb_range
        * hourly_pressure
        * humid_types
    """
    def __init__(self, hum_type, hum_value, barometric_pressure=101325,
                 schedule='', wet_bulb_range=''):
        """Initalize the class."""
        self.hum_type = hum_type
        self.hum_value = hum_value
        self.barometric_pressure = barometric_pressure
        self.schedule = schedule
        self.wet_bulb_range = wet_bulb_range

    @classmethod
    def from_dict(cls, data):
        """Create a Humidity Condition from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "hum_type": ""  # string,
            "hum_value": 0.0  # float,
            "barometric_pressure": 0.0  # float,
            "schedule": {}  # string,
            "wet_bulb_range": ""  # string
            }
        """
        # Check required and optional keys
        required_keys = ('hum_type', 'hum_value')
        optional_keys = {'barometric_pressure': 101325,
                         'schedule': '', 'wet_bulb_range': ''}
        for key in required_keys:
            assert key in data, 'Required key "{}" is missing!'.format(key)
        for key, val in optional_keys.items():
            if key not in data:
                data[key] = val

        return cls(data['hum_type'], data['hum_value'], data['barometric_pressure'],
                   data['schedule'], data['wet_bulb_range'])

    def hourly_dew_point_values(self, dry_bulb_condition):
        """Get a list of dew points (C) at each hour over the design day.

        Args:
            dry_bulb_condition: The dry bulb condition for the day.
        """
        hourly_dew_point = []
        max_dpt = self.dew_point(dry_bulb_condition.dry_bulb_max)
        for db in dry_bulb_condition.hourly_values:
            if db >= max_dpt:
                hourly_dew_point.append(max_dpt)
            else:
                hourly_dew_point.append(db)
        return hourly_dew_point

    def dew_point(self, db):
        """Get the dew point (C), which is constant throughout the day (except at saturation).

        Args:
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
        return [self._barometric_pressure] * 24

    @property
    def hum_type(self):
        """Get or set the humidity condition type."""
        return self._hum_type

    @hum_type.setter
    def hum_type(self, data):
        assert data in self.humid_types, 'hum_type {} is not' \
            ' recognized'.format(data)
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
    def humid_types(self):
        """Types of humidity conditions."""
        return ('Wetbulb', 'Dewpoint', 'HumidityRatio', 'Enthalpy')

    @property
    def isHumidityCondition(self):
        """Return True."""
        return True

    def to_dict(self):
        """Convert the Humidity Condition to a dictionary."""
        return {
            'hum_type': self.hum_type,
            'hum_value': self.hum_value,
            'barometric_pressure': self.barometric_pressure,
            'schedule': self.schedule,
            'wet_bulb_range': self.wet_bulb_range,
            'type': 'HumidityCondition'
        }

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """humidity condition representation."""
        return "HumidityCondition [{}: {}]".format(
            self._hum_type, str(self._hum_value))


class WindCondition(object):
    """Represents wind and rain conditions on the design day.

    Args:
        wind_speed: Wind speed on the design day [m/s].
        wind_direction: Wind direction on the design day [degrees]. Default: 0
        rain: Boolean to indicate rain on the design day. Default: False.
        snow_on_ground: Boolean to indicate snow on the design day. Default: False.

    Properties:
        * wind_speed
        * wind_direction
        * rain
        * snow_on_ground
        * hourly_values
        * hourly_wind_dirs
    """
    def __init__(self, wind_speed, wind_direction=0,
                 rain=False, snow_on_ground=False):
        """Initalize the class."""
        self.wind_speed = wind_speed
        self.wind_direction = wind_direction
        self.rain = rain
        self.snow_on_ground = snow_on_ground

    @classmethod
    def from_dict(cls, data):
        """Create a Wind Condition from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "wind_speed": 0.0  # float,
            "wind_direction": 0.0  # float,
            "rain": False  # bool,
            "snow_on_ground": False  # bool
            }
        """
        # Check required and optional keys
        optional_keys = {'wind_direction': 0, 'rain': False, 'snow_on_ground': False}
        assert 'wind_speed' in data, 'Required key "wind_speed" is missing!'
        for key, val in optional_keys.items():
            if key not in data:
                data[key] = val

        return cls(data['wind_speed'], data['wind_direction'], data['rain'],
                   data['snow_on_ground'])

    @property
    def hourly_values(self):
        """A list of wind speed values for each hour over the design day."""
        return [self._wind_speed] * 24

    @property
    def hourly_wind_dirs(self):
        """A list of wind directions for each hour over the design day."""
        return [self._wind_direction] * 24

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
            ' 0 and 360'.format(data)
        self._wind_direction = data

    @property
    def rain(self):
        """Get or set the presence of rain."""
        return self._rain

    @rain.setter
    def rain(self, data):
        if isinstance(data, bool):
            if data is True:
                data = 'Yes'
            else:
                data = 'No'
        self._rain = data

    @property
    def snow_on_ground(self):
        """Get or set the presence of snow on the ground."""
        return self._snow_on_ground

    @snow_on_ground.setter
    def snow_on_ground(self, data):
        if isinstance(data, bool):
            if data is True:
                data = 'Yes'
            else:
                data = 'No'
        self._snow_on_ground = data

    @property
    def isWindCondition(self):
        """Return True."""
        return True

    def to_dict(self):
        """Convert the Wind Condition to a dictionary."""
        return {
            'wind_speed': self.wind_speed,
            'wind_direction': self.wind_direction,
            'rain': self.rain,
            'snow_on_ground': self.snow_on_ground,
            'type': 'WindCondition'
        }

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """wind condition representation."""
        return "WindCondition [Speed: {}; Dir: {}]".format(
            str(self._wind_speed), str(self._wind_direction))


class SkyCondition(object):
    """An object representing a sky on the design day.

    Args:
        solar_model: Text for the name of the solar model to use. Choose from the
            following: 'ASHRAEClearSky', 'ASHRAETau', 'ZhangHuang', 'Schedule'
        month: Month in which the design day occurs.
        day_of_month: Day of the month on which the design day occurs.
        daylight_savings_indicator: Text ('Yes' or 'No'), for whether daylight savings
            time is active. Default: 'No'
        beam_shced: Schedule name for beam irradiance. Shoulb be an empty string unless
            solar_model is 'Schedule'.
        diff_sched: Schedule name for diffuse irradiance. Shoulb be an empty string
            unless solar_model is 'Schedule'.

    Properties:
        * month
        * day_of_month
        * hourly_sky_cover
        * sky_types
        * solar_model
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

    @classmethod
    def from_dict(cls, data):
        """Create a Sky Condition from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "solar_model": ""  # string,
            "month": 1  # int,
            "day_of_month": 1  # int,
            "daylight_savings_indicator": "No"  # string // "Yes" or "No"
            }
        """
        # Check required and optional keys
        required_keys = ('solar_model', 'month', 'day_of_month')
        for key in required_keys:
            assert key in data, 'Required key "{}" is missing!'.format(key)

        if data['solar_model'] == 'ASHRAEClearSky':
            return OriginalClearSkyCondition.from_dict(data)
        if data['solar_model'] == 'ASHRAETau':
            return RevisedClearSkyCondition.from_dict(data)

        if 'daylight_savings_indicator' not in data:
            data['daylight_savings_indicator'] = 'No'
        optional_keys = ('beam_shced', 'diff_sched')
        for key in optional_keys:
            if key not in data:
                data[key] = ''

        return cls(data['month'], data['day_of_month'], data['clearness'],
                   data['daylight_savings_indicator'],
                   data['beam_shced'], data['diff_sched'])

    @property
    def solar_model(self):
        """Get or set the type of solar model."""
        return self._solar_model

    @solar_model.setter
    def solar_model(self, data):
        assert data in self.sky_types, 'solar_model {} is not' \
            ' recognized as a valid solar model type'.format(data)
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
            ' 1 and 12'.format(data)
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
            ' 1 and 31'.format(data)
        self._day_of_month = data

    @property
    def hourly_sky_cover(self):
        """Lists of sky cover values in tenths.
        """
        return [0] * 24

    def _get_datetimes(self, timestep=1):
        """List of datetimes based on design day date and timestep."""
        start_moy = DateTime(self._month, self._day_of_month).moy
        if timestep == 1:
            start_moy = start_moy + 30
        num_moys = 24 * timestep
        return tuple(
            DateTime.from_moy(start_moy + (i * (1 / timestep) * 60))
            for i in xrange(num_moys)
        )

    @property
    def sky_types(self):
        """A list of possible sky types that can be associated with design days."""
        return ('ASHRAEClearSky', 'ASHRAETau', 'ZhangHuang', 'Schedule')

    @property
    def isSkyCondition(self):
        """Return True."""
        return True

    def to_dict(self):
        """Convert the Sky Condition to a dictionary."""
        return {
            'solar_model': self.solar_model,
            'month': self.month,
            'day_of_month': self.day_of_month,
            'daylight_savings_indicator': self.daylight_savings_indicator,
            'beam_shced': self.beam_shced,
            'diff_sched': self.diff_sched,
            'type': 'SkyCondition'
        }

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """sky condition representation."""
        return "SkyCondition {} [Month: {}, Day: {}]".format(
            self._solar_model, str(self._month), str(self._day_of_month))


class OriginalClearSkyCondition(SkyCondition):
    """An object representing an original ASHRAE Clear Sky.

    Args:
        month: Month in which the design day occurs.
        day_of_month: Day of the month on which the design day occurs.
        clearness: Value between 0 and 1.2 that will get multiplied by the model's
            irradinace to correct for factors like elevation.
        daylight_savings_indicator: Text ('Yes' or 'No'), for whether daylight savings
            time is active. Default: 'No'

    Properties:
        * month
        * day_of_month
        * clearness
        * daylight_savings_indicator
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

    @classmethod
    def from_dict(cls, data):
        """Create a Sky Condition from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "solar_model": ""  # string,
            "month": 1  # int,
            "day_of_month": 1  # int,
            "clearness": 0.0  # float,
            "daylight_savings_indicator": "No"  # string // "Yes" or "No"
            }
        """
        # Check required and optional keys
        required_keys = ('solar_model', 'month', 'day_of_month', 'clearness')
        for key in required_keys:
            assert key in data, 'Required key "{}" is missing!'.format(key)
        if 'daylight_savings_indicator' not in data:
            data['daylight_savings_indicator'] = 'No'

        return cls(data['month'], data['day_of_month'], data['clearness'],
                   data['daylight_savings_indicator'])

    @property
    def clearness(self):
        """Get or set the sky clearness."""
        return self._clearness

    @clearness.setter
    def clearness(self, data):
        assert isinstance(data, (float, int)), 'clearness must be a' \
            ' number. Got {}'.format(type(data))
        assert 0 <= data <= 1.2, 'clearness {} is not between' \
            ' 0 and 1.2'.format(data)
        self._clearness = data

    @property
    def hourly_sky_cover(self):
        """Lists of sky cover values in tenths.
        """
        if self._clearness > 1:
            cover = 0
        else:
            cover = (1 - self._clearness) * 10
        return [cover] * 24

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

    def to_dict(self):
        """Convert the Sky Condition to a dictionary."""
        return {
            'solar_model': self.solar_model,
            'month': self.month,
            'day_of_month': self.day_of_month,
            'clearness': self.clearness,
            'daylight_savings_indicator': self.daylight_savings_indicator,
            'type': 'OriginalClearSkyCondition'
        }


class RevisedClearSkyCondition(SkyCondition):
    """An object representing an ASHRAE Revised Clear Sky (Tau model).

    Args:
        month: Month in which the design day occurs.
        day_of_month: Day of the month on which the design day occurs.
        tau_b: Value for the 'beam' term in the Tau model. Typically
            found in .stat files.
        tau_d: Value for the 'diffuse' term in the Tau model. Typically
            found in .stat files.
        daylight_savings_indicator: Text ('Yes' or 'No'), for whether daylight savings
            time is active. Default: 'No'

    Properties:
        * day_of_month
        * hourly_sky_cover
        * month
        * sky_types
        * solar_model
        * tau_b
        * tau_d
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

    @classmethod
    def from_dict(cls, data):
        """Create a Sky Condition from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "solar_model": ""  # string,
            "month": 1  # int,
            "day_of_month": 1  # int,
            "tau_b": 0.0  # float,
            "tau_d": 0.0  # float,
            "daylight_savings_indicator": "No"  #string // "Yes" or "No"
            }
        """
        # Check required and optional keys
        required_keys = ('solar_model', 'month', 'day_of_month', 'tau_b', 'tau_d')
        for key in required_keys:
            assert key in data, 'Required key "{}" is missing!'.format(key)
        if 'daylight_savings_indicator' not in data:
            data['daylight_savings_indicator'] = 'No'

        return cls(data['month'], data['day_of_month'], data['tau_b'], data['tau_d'],
                   data['daylight_savings_indicator'])

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

    def to_dict(self):
        """Convert the Sky Condition to a dictionary."""
        return {
            'solar_model': self.solar_model,
            'month': self.month,
            'day_of_month': self.day_of_month,
            'tau_b': self.tau_b,
            'tau_d': self.tau_d,
            'daylight_savings_indicator': self.daylight_savings_indicator,
            'type': 'RevisedClearSkyCondition'
        }


def _check_analysis_period(analysis_period):
    assert hasattr(analysis_period, 'isAnalysisPeriod'), 'Expected' \
        ' AnalysisPeriod type. Got {}'.format(type(analysis_period))
    assert analysis_period.st_month == analysis_period.end_month and \
        analysis_period.st_day == analysis_period.end_day and \
        analysis_period.st_hour == 0 and analysis_period.end_hour == 23, \
        'analysis_period "{}" does not represent a single day'.format(
            analysis_period)
