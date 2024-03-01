# coding=utf-8
from __future__ import division

from .location import Location

from .dt import DateTime, Date
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
import re
import sys
if (sys.version_info > (3, 0)):
    xrange = range


class DesignDay(object):
    """An object representing design day conditions.

    Args:
        name: A text string to set the name of the design day
        day_type: Choose from 'SummerDesignDay', 'WinterDesignDay' or other
            EnergyPlus days visible under the DAY_TYPES property of this object.
        location: Location object for the design day.
        dry_bulb_condition: Ladybug DryBulbCondition object.
        humidity_condition: Ladybug HumidityCondition object.
        wind_condition: Ladybug WindCondition object.
        sky_condition: Ladybug SkyCondition object (either ASHRAEClearSky or ASHRAETau).

    Properties:
        * name
        * day_type
        * location
        * dry_bulb_condition
        * humidity_condition
        * wind_condition
        * sky_condition
        * analysis_period
        * hourly_datetimes
        * hourly_dry_bulb
        * hourly_dew_point
        * hourly_relative_humidity
        * hourly_barometric_pressure
        * hourly_wind_speed
        * hourly_wind_direction
        * hourly_solar_radiation
        * hourly_sky_cover
        * hourly_horizontal_infrared
    """
    __slots__ = ('_name', '_day_type', '_location', '_dry_bulb_condition',
                 '_humidity_condition', '_wind_condition', '_sky_condition')

    # possible day types
    DAY_TYPES = ('SummerDesignDay', 'WinterDesignDay', 'Sunday', 'Monday',
                 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Holiday',
                 'CustomDay1', 'CustomDay2')

    # keys denoting the values from which design days are derived
    # these keys and their order com from Climate Design Data of ASHRAE Handbook
    HEATING_KEYS = ('Month', 'DB996', 'DB990', 'DP996', 'HR_DP996', 'DB_DP996',
                    'DP990', 'HR_DP990', 'DB_DP990', 'WS004c', 'DB_WS004c',
                    'WS010c', 'DB_WS010c', 'WS_DB996', 'WD_DB996')
    COOLING_KEYS = ('Month', 'DBR', 'DB004', 'WB_DB004', 'DB010', 'WB_DB010',
                    'DB020', 'WB_DB020', 'WB004', 'DB_WB004', 'WB010', 'DB_WB010',
                    'WB020', 'DB_WB020', 'WS_DB004', 'WD_DB004', 'DP004',
                    'HR_DP004', 'DB_DP004', 'DP010', 'HR_DP010', 'DB_DP010',
                    'DP020', 'HR_DP020', 'DB_DP020', 'EN004', 'DB_EN004',
                    'EN010', 'DB_EN010', 'EN020', 'DB_EN020', 'Hrs_8-4_&_DB')
    EXTREME_KEYS = ('WS010', 'WS025', 'WS050', 'WBmax', 'DBmin_mean', 'DBmax_mean',
                    'DBmin_stddev', 'DBmax_stddev', 'DBmin05years', 'DBmax05years',
                    'DBmin10years', 'DBmax10years', 'DBmin20years', 'DBmax20years',
                    'DBmin50years', 'DBmax50years')

    # comments that go along with the IDF string representation of the design day
    IDF_COMMENTS = ('!- Name',
                    '!- Month',
                    '!- Day of Month',
                    '!- Day Type',
                    '!- Max Dry-Bulb Temp {C}',
                    '!- Daily Dry-Bulb Temp Range {C}',
                    '!- Dry-Bulb Temp Range Modifier Type',
                    '!- Dry-Bulb Temp Range Modifier Schedule Name',
                    '!- Humidity Condition Type',
                    '!- Wetbulb/Dewpoint at Max Dry-Bulb {C}',
                    '!- Humidity Indicating Day Schedule Name',
                    '!- Humidity Ratio at Maximum Dry-Bulb {kgWater/kgDryAir}',
                    '!- Enthalpy at Maximum Dry-Bulb {J/kg}',
                    '!- Daily Wet-Bulb Temperature Range {deltaC}',
                    '!- Barometric Pressure {Pa}',
                    '!- Wind Speed {m/s}',
                    '!- Wind Direction {Degrees; N=0, S=180}',
                    '!- Rain {Yes/No}',
                    '!- Snow on ground {Yes/No}',
                    '!- Daylight Savings Time Indicator {Yes/No}',
                    '!- Solar Model Indicator',
                    '!- Beam Solar Day Schedule Name',
                    '!- Diffuse Solar Day Schedule Name',
                    '!- ASHRAE Clear Sky Beam Optical Depth (taub)',
                    '!- ASHRAE Clear Sky Diffuse Optical Depth (taud)',
                    '!- Clearness (0.0 to 1.2)')

    def __init__(self, name, day_type, location, dry_bulb_condition, humidity_condition,
                 wind_condition, sky_condition):
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
            "type": "DesignDay",
            "name": "",  # string
            "day_type": "",  # string
            "location": {},  # optional ladybug Location dictionary
            "dry_bulb_condition": {},  # ladybug DryBulbCondition dictionary
            "humidity_condition": {},  # ladybug HumidityCondition dictionary
            "wind_condition": {},  # ladybug WindCondition dictionary
            "sky_condition": {}  # ladybug ASHRAEClearSky or ASHRAETau dictionary
            }
        """
        required_keys = ('name', 'day_type', 'dry_bulb_condition',
                         'humidity_condition', 'wind_condition', 'sky_condition')
        for key in required_keys:
            assert key in data, 'Required key "{}" is missing!'.format(key)

        if 'location' in data and data['location'] is not None:
            loc = Location.from_dict(data['location'])
        else:
            loc = Location()

        return cls(data['name'], data['day_type'], loc,
                   DryBulbCondition.from_dict(data['dry_bulb_condition']),
                   HumidityCondition.from_dict(data['humidity_condition']),
                   WindCondition.from_dict(data['wind_condition']),
                   _SkyCondition.from_dict(data['sky_condition']))

    @classmethod
    def from_idf(cls, idf_string, location):
        """Initialize from an EnergyPlus IDF string of a SizingPeriod:DesignDay.

        Args:
            idf_string: A full IDF string representing a SizingPeriod:DesignDay.
            location: A Ladybug Location object, used to interpret the sky condition
                over the course of the design day.
        """
        # format the object into a list of properties
        idf_string = idf_string.strip()
        assert idf_string.startswith('SizingPeriod:DesignDay'), 'Expected SizingPeriod' \
            ':DesignDay but received a different object: {}'.format(idf_string)
        idf_string = idf_string.replace(';', ',')
        idf_string = re.sub(r'!.*\n', '', idf_string)
        ep_fields = [e_str.strip() for e_str in idf_string.split(',')]

        # extract primary properties
        name = ep_fields[1]
        day_type = ep_fields[4]

        # extract dry bulb temperatures
        dry_bulb_condition = DryBulbCondition(
            float(ep_fields[5]), float(ep_fields[6]), ep_fields[7], ep_fields[8])

        # extract humidity conditions
        h_type = ep_fields[9]
        h_val = 0 if ep_fields[10] == '' else float(ep_fields[10])
        rain = True if len(ep_fields) > 18 and ep_fields[18].lower() == 'yes' else False
        snow = True if len(ep_fields) > 19 and ep_fields[19].lower() == 'yes' else False
        if h_type == 'HumidityRatio':
            h_val = float(ep_fields[12])
        elif h_type == 'Enthalpy':
            h_val = float(ep_fields[13])
        humidity_condition = HumidityCondition(
            h_type, h_val, float(ep_fields[15]), rain, snow, ep_fields[11])

        # extract wind conditions
        wind_condition = WindCondition(float(ep_fields[16]), float(ep_fields[17]))

        # extract the sky conditions
        date_obj = Date(int(ep_fields[2]), int(ep_fields[3]))
        dl_save = True if len(ep_fields) > 20 and ep_fields[20].lower() == 'yes' \
            else False
        if len(ep_fields) > 21:
            sky_model = ep_fields[21]
            if sky_model == 'ASHRAEClearSky':
                sky_clr = float(ep_fields[26]) if len(ep_fields) > 26 else 0
                sky_condition = ASHRAEClearSky(date_obj, sky_clr, dl_save)
            elif sky_model in ('ASHRAETau', 'ASHRAETau2017'):
                use_2017 = True if sky_model.endswith('2017') else False
                t_b = float(ep_fields[24]) if len(ep_fields) > 24 else 0
                t_d = float(ep_fields[25]) if len(ep_fields) > 25 else 0
                sky_condition = ASHRAETau(date_obj, t_b, t_d, use_2017, dl_save)
            else:
                sky_condition = _SkyCondition(date_obj, dl_save)
            if sky_model == 'Schedule':
                sky_condition.beam_schedule = ep_fields[22]
                sky_condition.diffuse_schedule = ep_fields[23]
        else:  # default of no sky condition
            sky_condition = ASHRAEClearSky(date_obj, 0, dl_save)

        return cls(name, day_type, location, dry_bulb_condition,
                   humidity_condition, wind_condition, sky_condition)

    @classmethod
    def from_design_day_properties(cls, name, day_type, location, date,
                                   dry_bulb_max, dry_bulb_range, humidity_type,
                                   humidity_value, pressure, wind_speed, wind_dir,
                                   sky_model, sky_properties):
        """Create a design day object from various key properties.

        Args:
            name: A text string to set the name of the design day
            day_type: Choose from 'SummerDesignDay', 'WinterDesignDay' or other
                EnergyPlus days
            location: Location for the design day
            date: Ladybug Date object for the design day.
            dry_bulb_max: Maximum dry bulb temperature over the design day (in C).
            dry_bulb_range: Dry bulb range over the design day (in C).
            humidity_type: Type of humidity to use. Choose from
                Wetbulb, Dewpoint, HumidityRatio, Enthalpy
            humidity_value: The value of the condition above.
            pressure: Barometric pressure in Pa.
            wind_speed: Wind speed over the design day in m/s.
            wind_dir: Wind direction over the design day in degrees.
            sky_model: Type of solar model to use. Choose from ASHRAEClearSky, ASHRAETau.
            sky_properties: A list of properties describing the sky above.
                For ASHRAEClearSky this is a single value for clearness
                For ASHRAETau, this is the tau_beam and tau_diffuse
        """
        dry_bulb_condition = DryBulbCondition(dry_bulb_max, dry_bulb_range)
        humidity_condition = HumidityCondition(
            humidity_type, humidity_value, pressure)
        wind_condition = WindCondition(wind_speed, wind_dir)
        if sky_model == 'ASHRAEClearSky':
            sky_condition = ASHRAEClearSky(date, sky_properties[0])
        elif sky_model in ('ASHRAETau', 'ASHRAETau2017'):
            use_2017 = True if sky_model.endswith('2017') else False
            sky_condition = ASHRAETau(
                date, sky_properties[0], sky_properties[-1], use_2017)
        return cls(name, day_type, location, dry_bulb_condition,
                   humidity_condition, wind_condition, sky_condition)

    @classmethod
    def from_ashrae_dict_heating(cls, ashrae_dict, location,
                                 use_990=False, pressure=None):
        """Create a heating design day object from a ASHRAE HOF dictionary.

        Args:
            ashrae_dict: A dictionary with 15 keys that match those in the
                HEATING_KEYS property of this object. Each key should
                correspond to a value.
            location: Location object for the design day
            use_990: Boolean to denote what type of design day to create
                (wether it is a 99.0% or a 99.6% design day).  Default is
                False for a 99.6% annual heating design day
            pressure: Atmospheric pressure in Pa that should be used in the
                creation of the humidity condition. Default is 101325 Pa
                for pressure at sea level.
        """
        db_key = 'DB996' if not use_990 else 'DB990'
        perc_str = '99.6' if not use_990 else '99'
        pressure = pressure if pressure is not None else 101325
        db_cond = DryBulbCondition(float(ashrae_dict[db_key]), 0)
        hu_cond = HumidityCondition('Wetbulb', float(ashrae_dict[db_key]), pressure)
        ws_cond = WindCondition(float(ashrae_dict['WS_DB996']),
                                float(ashrae_dict['WD_DB996']))
        date_obj = Date(int(ashrae_dict['Month']), 21)
        sky_cond = ASHRAEClearSky(date_obj, 0)
        name = '{} Heating Design Day {}% Condns DB'.format(location.city, perc_str)
        return cls(name, 'WinterDesignDay', location,
                   db_cond, hu_cond, ws_cond, sky_cond)

    @classmethod
    def from_ashrae_dict_cooling(cls, ashrae_dict, location,
                                 use_010=False, pressure=None, tau=None):
        """Create a heating design day object from a ASHRAE HOF dictionary.

        Args:
            ashrae_dict: A dictionary with 32 keys that match those in the
                COOLING_KEYS property of this object. Each key should
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
        db_key = 'DB004' if not use_010 else 'DB010'
        wb_key = 'WB_DB004' if not use_010 else 'WB_DB010'
        perc_str = '0.4' if not use_010 else '1'
        pressure = pressure if pressure is not None else 101325
        db_cond = DryBulbCondition(float(ashrae_dict[db_key]), float(ashrae_dict['DBR']))
        hu_cond = HumidityCondition('Wetbulb', float(ashrae_dict[wb_key]), pressure)
        ws_cond = WindCondition(float(ashrae_dict['WS_DB004']),
                                float(ashrae_dict['WD_DB004']))
        date_obj = Date(int(ashrae_dict['Month']), 21)
        if tau is not None:
            sky_cond = ASHRAETau(date_obj, tau[0], tau[1])
        else:
            sky_cond = ASHRAEClearSky(date_obj)
        name = '{} Cooling Design Day {}% Condns DB=>MWB'.format(
            location.city, perc_str)
        return cls(name, 'SummerDesignDay', location,
                   db_cond, hu_cond, ws_cond, sky_cond)

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
        assert data in self.DAY_TYPES, 'day_type {} is not' \
            ' recognized'.format(data)
        self._day_type = data

    @property
    def location(self):
        """Get or set the location."""
        return self._location

    @location.setter
    def location(self, data):
        assert isinstance(data, Location), 'Expected' \
            ' Location type. Got {}'.format(type(data))
        self._location = data

    @property
    def dry_bulb_condition(self):
        """Get or set the dry bulb conditions."""
        return self._dry_bulb_condition

    @dry_bulb_condition.setter
    def dry_bulb_condition(self, data):
        assert isinstance(data, DryBulbCondition), 'Expected' \
            ' DryBulbCondition type. Got {}'.format(type(data))
        self._dry_bulb_condition = data

    @property
    def humidity_condition(self):
        """Get or set the humidity conditions."""
        return self._humidity_condition

    @humidity_condition.setter
    def humidity_condition(self, data):
        assert isinstance(data, HumidityCondition), 'Expected' \
            ' HumidityCondition type. Got {}'.format(type(data))
        self._humidity_condition = data

    @property
    def wind_condition(self):
        """Get or set the wind conditions."""
        return self._wind_condition

    @wind_condition.setter
    def wind_condition(self, data):
        assert isinstance(data, WindCondition), 'Expected' \
            ' WindCondition type. Got {}'.format(type(data))
        self._wind_condition = data

    @property
    def sky_condition(self):
        """Get or set the sky conditions."""
        return self._sky_condition

    @sky_condition.setter
    def sky_condition(self, data):
        assert isinstance(data, _SkyCondition), 'Expected ASHRAEClearSky or' \
            ' ASHRAETau type. Got {}'.format(type(data))
        self._sky_condition = data

    @property
    def analysis_period(self):
        """Get the analysisperiod of the design day."""
        return AnalysisPeriod(
            self.sky_condition.date.month,
            self.sky_condition.date.day,
            0,
            self.sky_condition.date.month,
            self.sky_condition.date.day,
            23)

    @property
    def hourly_datetimes(self):
        """Get a list of hourly DateTime objects for the DesignDay."""
        start_moy = self.sky_condition.date.doy * 1440
        lp_yr = self.sky_condition.date.leap_year
        return tuple(DateTime.from_moy(start_moy + (i * 60), lp_yr) for i in xrange(24))

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

    def to_idf(self):
        """Get this object as an EnergyPlus IDF SizingPeriod:DesignDay string."""
        # Put together the values in the order that they exist in the ddy file
        ep_vals = [self.name,
                   self.sky_condition.date.month,
                   self.sky_condition.date.day,
                   self.day_type,
                   self.dry_bulb_condition.dry_bulb_max,
                   self.dry_bulb_condition.dry_bulb_range,
                   self.dry_bulb_condition.modifier_type,
                   self.dry_bulb_condition.modifier_schedule,
                   self.humidity_condition.humidity_type, '',
                   self.humidity_condition.schedule, '', '',
                   self.humidity_condition.wet_bulb_range,
                   self.humidity_condition.barometric_pressure,
                   self.wind_condition.wind_speed,
                   self.wind_condition.wind_direction,
                   'Yes' if self.humidity_condition.rain else 'No',
                   'Yes' if self.humidity_condition.snow_on_ground else 'No',
                   'Yes' if self.sky_condition.daylight_savings else 'No',
                   'ASHRAEClearSky',
                   self.sky_condition.beam_schedule,
                   self.sky_condition.diffuse_schedule, '', '', '']

        # assign humidity values based on the type of criteria
        if self.humidity_condition.humidity_type == 'Wetbulb' or \
                self.humidity_condition.humidity_type == 'Dewpoint':
            ep_vals[9] = self.humidity_condition.humidity_value
        elif self.humidity_condition.humidity_type == 'HumidityRatio':
            ep_vals[11] = self.humidity_condition.humidity_value
        elif self.humidity_condition.humidity_type == 'Enthalpy':
            ep_vals[12] = self.humidity_condition.humidity_value

        # assign sky condition values based on the solar model
        if isinstance(self.sky_condition, ASHRAEClearSky):
            ep_vals[25] = self.sky_condition.clearness
        if isinstance(self.sky_condition, ASHRAETau):
            ep_vals[20] = 'ASHRAETau2017' if self.sky_condition.use_2017 else 'ASHRAETau'
            ep_vals[23] = self.sky_condition.tau_b
            ep_vals[24] = self.sky_condition._tau_d
            ep_vals.pop()

        # put everything together into one string
        commented_str = ['  {},{}{}\n'.format(
            str(val), ' ' * (60 - len(str(val))), self.IDF_COMMENTS[i])
            for i, val in enumerate(ep_vals)]
        commented_str[-1] = commented_str[-1].replace(',', ';')
        commented_str.insert(0, 'SizingPeriod:DesignDay,\n')
        commented_str.append('\n')

        return ''.join(commented_str)

    def to_dict(self, include_location=True):
        """Convert the Design Day to a dictionary.

        Args:
            include_location: If True, the location dictionary will be included in the
                returned dictionary. This ensures that the sky condition contained
                in any re-serialized design day can produce accurate radiation values.
                However, this location is not necessary when exporting design days
                for energy simulation since the EPW simulated with the model already
                contains location information. Default: True.
        """
        des_day_dict = {
            'type': 'DesignDay',
            'name': self.name,
            'day_type': self.day_type,
            'dry_bulb_condition': self.dry_bulb_condition.to_dict(),
            'humidity_condition': self.humidity_condition.to_dict(),
            'wind_condition': self.wind_condition.to_dict(),
            'sky_condition': self.sky_condition.to_dict(),
            'type': 'DesignDay'
        }
        if include_location:
            des_day_dict['location'] = self.location.to_dict()
        return des_day_dict

    def _get_daily_data_collections(self, data_type, unit, values):
        """Return an empty data collection."""
        data_header = Header(data_type=data_type, unit=unit,
                             analysis_period=self.analysis_period,
                             metadata={'source': self._location.source,
                                       'country': self._location.country,
                                       'city': self._location.city})
        return HourlyContinuousCollection(data_header, values)

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __copy__(self):
        return DesignDay(
            self._name, self._day_type, self._location.duplicate(),
            self._dry_bulb_condition.duplicate(), self._humidity_condition.duplicate(),
            self._wind_condition.duplicate(), self._sky_condition.duplicate())

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self._name, self._day_type, hash(self._location),
                hash(self._dry_bulb_condition), hash(self._humidity_condition),
                hash(self._wind_condition), hash(self._sky_condition))

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, DesignDay) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        """Design day representation."""
        return "Design Day - {} [{}]".format(self.name, self._day_type)


class DryBulbCondition(object):
    """Represents dry bulb conditions on a design day.

    Args:
        dry_bulb_max: The maximum dry bulb temperature on the design day [C].
        dry_bulb_range: The difference between min and max temperatures on the
            design day [C].
        modifier_type: Optional string for the type of modifier used to estimate
            temperature at a given timestep. Choose from the following:
            'DefaultMultipliers', 'MultiplierSchedule', 'DifferenceSchedule',
            'TemperatureProfileSchedule'. Default: 'DefaultMultipliers'
        modifier_schedule: Optional text string for the name of the modifier
            schedule. Should be an empty string unless 'MultiplierSchedule' is
            selected as the modifier_type.

    Properties:
        * dry_bulb_max
        * dry_bulb_range
        * modifier_type
        * modifier_schedule
        * hourly_values
    """
    __slots__ = ('_dry_bulb_max', '_dry_bulb_range', 'modifier_type',
                 'modifier_schedule')
    HOURLY_MULTIPLIERS = (0.82, 0.88, 0.92, 0.95, 0.98, 1, 0.98, 0.91, 0.74, 0.55,
                          0.38, 0.23, 0.13, 0.05, 0, 0, 0.06, 0.14, 0.24, 0.39, 0.5,
                          0.59, 0.68, 0.75)

    def __init__(self, dry_bulb_max, dry_bulb_range,
                 modifier_type='DefaultMultipliers', modifier_schedule=''):
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
            "type": "DryBulbCondition",
            "dry_bulb_max": 0.0,  # float
            "dry_bulb_range": 0.0  # float
            }
        """
        # check required keys
        required_keys = ('dry_bulb_max', 'dry_bulb_range')
        for key in required_keys:
            assert key in data, 'Required key "{}" is missing!'.format(key)

        # set defaults for optional keys
        mod_type = data['modifier_type'] if 'modifier_type' in data \
            else 'DefaultMultipliers'
        mod_schedule = data['modifier_schedule'] if 'modifier_schedule' in data else ''

        return cls(data['dry_bulb_max'], data['dry_bulb_range'], mod_type, mod_schedule)

    @property
    def hourly_values(self):
        """Get a list of temperature values for each hour over the design day."""
        return [self._dry_bulb_max - self._dry_bulb_range * x for
                x in self.HOURLY_MULTIPLIERS]

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

    def to_dict(self):
        """Convert the Dry Bulb Condition to a dictionary."""
        return {
            'type': 'DryBulbCondition',
            'dry_bulb_max': self.dry_bulb_max,
            'dry_bulb_range': self.dry_bulb_range
        }

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __copy__(self):
        return DryBulbCondition(self._dry_bulb_max, self._dry_bulb_range,
                                self.modifier_type, self.modifier_schedule)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self._dry_bulb_max, self._dry_bulb_range,
                self.modifier_type, self.modifier_schedule)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, DryBulbCondition) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        """Dry bulb condition representation."""
        return "Dry Bulb Condition [Max: {}, Range: {}]".format(
            str(self._dry_bulb_max), str(self._dry_bulb_range))


class HumidityCondition(object):
    """Represents humidity and precipitation conditions on the design day.

    Args:
        humidity_type: Choose from: Wetbulb, Dewpoint, HumidityRatio, Enthalpy
        humidity_value: The value correcponding to the humidity_type
        barometric_pressure: Default is to use pressure at sea level
        rain: Boolean to indicate rain on the design day. Default: False.
        snow_on_ground: Boolean to indicate snow on the design day. Default: False.
        schedule: Optional humidity schedule
        wet_bulb_range: Optional wet bulb temperature range

    Properties:
        * humidity_type
        * humidity_value
        * barometric_pressure
        * rain
        * snow_on_ground
        * schedule
        * wet_bulb_range
        * hourly_pressure
    """
    __slots__ = ('_humidity_type', '_humidity_value', '_barometric_pressure',
                 '_rain', '_snow_on_ground', 'schedule', 'wet_bulb_range')
    HUMIDITY_TYPES = ('Wetbulb', 'Dewpoint', 'HumidityRatio', 'Enthalpy')

    def __init__(self, humidity_type, humidity_value, barometric_pressure=101325,
                 rain=False, snow_on_ground=False, schedule='', wet_bulb_range=''):
        self.humidity_type = humidity_type
        self.humidity_value = humidity_value
        self.barometric_pressure = barometric_pressure
        self.rain = rain
        self.snow_on_ground = snow_on_ground
        self.schedule = schedule
        self.wet_bulb_range = wet_bulb_range

    @classmethod
    def from_dict(cls, data):
        """Create a Humidity Condition from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "type": "HumidityCondition",
            "humidity_type": "",  # string
            "humidity_value": 0.0,  # float
            "barometric_pressure": 0.0,  # float
            "rain": False,  # bool
            "snow_on_ground": False  # bool
            }
        """
        # check required keys
        required_keys = ('humidity_type', 'humidity_value')
        for key in required_keys:
            assert key in data, 'Required key "{}" is missing!'.format(key)

        # set defaults for optional keys
        press = data['barometric_pressure'] if 'barometric_pressure' in data else 101325
        rain = data['rain'] if 'rain' in data else False
        snow_on_ground = data['snow_on_ground'] if 'snow_on_ground' in data else False
        sched = data['schedule'] if 'schedule' in data else ''
        wet_bulb_range = data['wet_bulb_range'] if 'wet_bulb_range' in data else ''

        return cls(data['humidity_type'], data['humidity_value'], press,
                   rain, snow_on_ground, sched, wet_bulb_range)

    @property
    def humidity_type(self):
        """Get or set the humidity condition type."""
        return self._humidity_type

    @humidity_type.setter
    def humidity_type(self, data):
        assert data in self.HUMIDITY_TYPES, 'humidity_type {} is not' \
            ' recognized'.format(data)
        self._humidity_type = data

    @property
    def humidity_value(self):
        """Get or set the value of the humidity."""
        return self._humidity_value

    @humidity_value.setter
    def humidity_value(self, data):
        assert isinstance(data, (float, int)), 'humidity_value must be a' \
            ' number. Got {}'.format(type(data))
        self._humidity_value = data

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
    def rain(self):
        """Get or set a boolean for the presence of rain."""
        return self._rain

    @rain.setter
    def rain(self, data):
        self._rain = bool(data)

    @property
    def snow_on_ground(self):
        """Get or set a boolean for the presence of snow on the ground."""
        return self._snow_on_ground

    @snow_on_ground.setter
    def snow_on_ground(self, data):
        self._snow_on_ground = bool(data)

    @property
    def hourly_pressure(self):
        """Get a list of barometric pressures for each hour over the design day."""
        return [self._barometric_pressure] * 24

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
        if self._humidity_type == 'Dewpoint':
            return self._humidity_value
        elif self._humidity_type == 'Wetbulb':
            return dew_point_from_db_wb(
                db, self._humidity_value, self._barometric_pressure)
        elif self._humidity_type == 'HumidityRatio':
            return dew_point_from_db_hr(
                db, self._humidity_value, self._barometric_pressure)
        elif self._humidity_type == 'Enthalpy':
            return dew_point_from_db_enth(
                db, self._humidity_value / 1000, self._barometric_pressure)

    def to_dict(self):
        """Convert the Humidity Condition to a dictionary."""
        return {
            'type': 'HumidityCondition',
            'humidity_type': self.humidity_type,
            'humidity_value': self.humidity_value,
            'barometric_pressure': self.barometric_pressure,
            'rain': self.rain,
            'snow_on_ground': self.snow_on_ground
        }

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __copy__(self):
        return HumidityCondition(
            self._humidity_type, self._humidity_value, self._barometric_pressure,
            self._rain, self._snow_on_ground, self.schedule, self.wet_bulb_range)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self._humidity_type, self._humidity_value, self._barometric_pressure,
                self._rain, self._snow_on_ground, self.schedule, self.wet_bulb_range)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, HumidityCondition) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        """Humidity condition representation."""
        return "HumidityCondition [{}: {}]".format(
            self._humidity_type, str(self._humidity_value))


class WindCondition(object):
    """Represents wind conditions on the design day.

    Args:
        wind_speed: Wind speed on the design day [m/s].
        wind_direction: Wind direction on the design day [degrees]. Default: 0

    Properties:
        * wind_speed
        * wind_direction
        * hourly_values
        * hourly_wind_dirs
    """
    __slots__ = ('_wind_speed', '_wind_direction')

    def __init__(self, wind_speed, wind_direction=0):
        """Initialize the class."""
        self.wind_speed = wind_speed
        self.wind_direction = wind_direction

    @classmethod
    def from_dict(cls, data):
        """Create a Wind Condition from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "type": "WindCondition",
            "wind_speed": 3.0,  # float
            "wind_direction": 0.0  # float
            }
        """
        # check required and optional keys
        assert 'wind_speed' in data, 'Required key "wind_speed" is missing!'

        # set defaults for the optional keys
        wind_direction = data['wind_direction'] if 'wind_direction' in data else 0

        return cls(data['wind_speed'], wind_direction)

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

    def to_dict(self):
        """Convert the Wind Condition to a dictionary."""
        return {
            'type': 'WindCondition',
            'wind_speed': self.wind_speed,
            'wind_direction': self.wind_direction
        }

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __copy__(self):
        return WindCondition(self._wind_speed, self._wind_direction)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self._wind_speed, self._wind_direction)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, WindCondition) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        """Wind condition representation."""
        return "WindCondition [Speed: {}; Dir: {}]".format(
            self.wind_speed, self.wind_direction)


class _SkyCondition(object):
    """An object representing a sky on the design day.

    This is a base class for all solar models and the class of the specific desired
    solar model should typically be used instead of this one.

    Args:
        date: Ladybug Date object for the day of the year on which the design
            day occurs.
        daylight_savings: Boolean to indicate whether daylight savings
            time is active. Default: False
        beam_schedule: Schedule name for beam irradiance. Should be an empty
            string unless the solar model is 'Schedule'.
        diffuse_schedule: Schedule name for diffuse irradiance. Should be an
            empty string unless solar model is 'Schedule'.

    Properties:
        * date
        * daylight_savings
        * beam_schedule
        * diffuse_schedule
        * hourly_sky_cover
    """
    __slots__ = ('_date', '_daylight_savings', 'beam_schedule', 'diffuse_schedule')
    SOLAR_MODELS = ('ASHRAEClearSky', 'ASHRAETau', 'ZhangHuang', 'Schedule')

    def __init__(self, date, daylight_savings=False, beam_schedule='',
                 diffuse_schedule=''):
        self.date = date
        self.daylight_savings = daylight_savings
        self.beam_schedule = beam_schedule
        self.diffuse_schedule = diffuse_schedule

    @classmethod
    def from_dict(cls, data):
        """Create a Sky Condition from a dictionary.

        Args:
            data: A python dictionary in the following format.

        .. code-block:: python

            {
            "type": "SkyCondition",
            "date": [7, 21],
            "daylight_savings": False  # bool
            }
        """
        # process more detailed solar models into their respective classes
        if data['type'] == 'ASHRAEClearSky':
            return ASHRAEClearSky.from_dict(data)
        if data['type'] == 'ASHRAETau':
            return ASHRAETau.from_dict(data)

        # check required keys
        assert 'date' in data, 'Required key "date" is missing!'

        # assign defaults for optional keys
        dl_save = data['daylight_savings'] if 'daylight_savings' \
            in data else False
        beam_schedule = data['beam_schedule'] if 'beam_schedule' in data else ''
        diffuse_schedule = data['diffuse_schedule'] if 'diffuse_schedule' in data else ''

        return cls(Date.from_array(data['date']), dl_save, beam_schedule,
                   diffuse_schedule)

    @property
    def date(self):
        """Get or set a Ladybug Date object for the date of the design day."""
        return self._date

    @date.setter
    def date(self, data):
        assert isinstance(data, Date), 'DesignDay.sky_condition.date must be a' \
            ' Ladybug Date object. Got {}'.format(type(data))
        self._date = data

    @property
    def daylight_savings(self):
        """Get or set a boolean to indicate whether daylight savings time is active."""
        return self._daylight_savings

    @daylight_savings.setter
    def daylight_savings(self, data):
        self._daylight_savings = bool(data)

    @property
    def hourly_sky_cover(self):
        """Get a lists of hourly sky cover values in tenths."""
        return [0] * 24

    def to_dict(self):
        """Convert the Sky Condition to a dictionary."""
        return {
            'type': 'SkyCondition',
            'date': self.date.to_array(),
            'daylight_savings': self.daylight_savings,
            'beam_schedule': self.beam_schedule,
            'diffuse_schedule': self.diffuse_schedule
        }

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def _get_datetimes(self, timestep=1):
        """List of datetimes based on design day date and timestep.

        Note that these datetimes are always in standard time in order to be used
        for solar positions. In other words, they correct from daylight savings time.
        """
        start_moy = self._date.doy * 1440  # convert doy to moy
        if self._daylight_savings:  # spring time forward! (or move the sun back)
            start_moy = start_moy - 60
        if timestep == 1:
            start_moy = start_moy + 30
        num_moys = 24 * timestep
        lp_yr = self._date.leap_year
        return tuple(DateTime.from_moy(start_moy + (i * (1 / timestep) * 60), lp_yr)
                     for i in xrange(num_moys))

    @staticmethod
    def _check_analysis_period(analysis_period):
        """Check an AnalysisPeriod to be sure that it's suitable for a design day."""
        assert isinstance(analysis_period, AnalysisPeriod), 'Expected' \
            ' AnalysisPeriod type. Got {}'.format(type(analysis_period))
        assert analysis_period.st_month == analysis_period.end_month and \
            analysis_period.st_day == analysis_period.end_day and \
            analysis_period.st_hour == 0 and analysis_period.end_hour == 23, \
            'analysis_period "{}" does not represent a single day'.format(
                analysis_period)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __copy__(self):
        return _SkyCondition(self._date, self._daylight_savings, self.beam_schedule,
                             self.diffuse_schedule)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (hash(self._date), self._daylight_savings, self.beam_schedule,
                self.diffuse_schedule)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, _SkyCondition) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        """Sky condition representation."""
        return 'SkyCondition [{}]'.format(self._date)


class ASHRAEClearSky(_SkyCondition):
    """An object representing an original ASHRAE Clear Sky.

    Args:
        date: Ladybug Date object for the day of the year on which the design
            day occurs.
        clearness: Value between 0 and 1.2 that will get multiplied by the model's
            irradiance to correct for factors like elevation.
        daylight_savings: Boolean to indicate whether daylight savings
            time is active. Default: False.

    Properties:
        * date
        * clearness
        * daylight_savings
    """
    __slots__ = ('_clearness',)

    def __init__(self, date, clearness=1, daylight_savings=False):
        _SkyCondition.__init__(self, date, daylight_savings)
        self.clearness = clearness

    @classmethod
    def from_analysis_period(cls, analysis_period, clearness=1, daylight_savings=False):
        """"Initialize a ASHRAEClearSky from an analysis_period"""
        cls._check_analysis_period(analysis_period)
        st_dt = analysis_period.st_time
        return cls(Date(st_dt.month, st_dt.day, st_dt.leap_year), clearness,
                   daylight_savings)

    @classmethod
    def from_dict(cls, data):
        """Create an ASHRAEClearSky condition from a dictionary.

        Args:
            data: A python dictionary in the following format.

        .. code-block:: python

            {
            "type": "ASHRAEClearSky"
            "date": [7, 21],
            "clearness": 0.0  # float,
            "daylight_savings": False  # bool
            }
        """
        # check required and optional keys
        required_keys = ('type', 'date', 'clearness')
        for key in required_keys:
            assert key in data, 'Required key "{}" is missing!'.format(key)

        # assign defaults for optional keys
        dl_save = data['daylight_savings'] if 'daylight_savings' \
            in data else False

        return cls(Date.from_array(data['date']), data['clearness'], dl_save)

    @property
    def clearness(self):
        """Get or set the sky clearness."""
        return self._clearness

    @clearness.setter
    def clearness(self, data):
        assert isinstance(data, (float, int)), 'clearness must be a' \
            ' number. Got {}'.format(type(data))
        assert 0 <= data <= 1.2, 'clearness {} is not between 0 and 1.2'.format(data)
        self._clearness = data

    @property
    def hourly_sky_cover(self):
        """Lists of sky cover values in tenths."""
        cover = 0 if self._clearness > 1 else (1 - self._clearness) * 10
        return [cover] * 24

    def radiation_values(self, location, timestep=1):
        """Get arrays of direct, diffuse, and global radiation at each timestep."""
        # create sunpath and get altitude at every timestep of the design day
        sp = Sunpath.from_location(location)
        altitudes = []
        dates = self._get_datetimes(timestep)
        for t_date in dates:
            sun = sp.calculate_sun_from_date_time(t_date)
            altitudes.append(sun.altitude)
        dir_norm, diff_horiz = ashrae_clear_sky(
            altitudes, self._date.month, self._clearness)
        glob_horiz = [dhr + dnr * math.sin(math.radians(alt)) for
                      alt, dnr, dhr in zip(altitudes, dir_norm, diff_horiz)]
        return dir_norm, diff_horiz, glob_horiz

    def to_dict(self):
        """Convert the ASHRAEClearSky to a dictionary."""
        return {
            'type': 'ASHRAEClearSky',
            'date': self.date.to_array(),
            'clearness': self.clearness,
            'daylight_savings': self.daylight_savings,
        }

    def __copy__(self):
        return ASHRAEClearSky(self._date, self._clearness, self._daylight_savings)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (hash(self._date), self._clearness, self._daylight_savings)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, ASHRAEClearSky) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        """sky condition representation."""
        return 'ASHRAEClearSky [{}]'.format(self._date)


class ASHRAETau(_SkyCondition):
    """An object representing an ASHRAE Revised Clear Sky (Tau model).

    Args:
        date: Ladybug Date object for the day of the year on which the design
            day occurs.
        tau_b: Value for the beam optical depths. Typically found in .stat files.
        tau_d: Value for the diffuse optical depth. Typically found in .stat files.
        use_2017: A boolean to indicate whether the version of the ASHRAE Tau
                model that should be the revised version published in 2017 (True)
                or the original one published in 2009 (False). (Default: False).
        daylight_savings: Boolean to indicate whether daylight savings
            time is active. (Default: False).

    Properties:
        * date
        * tau_b
        * tau_d
        * use_2017
        * daylight_savings
        * hourly_sky_cover
    """
    __slots__ = ('_tau_b', '_tau_d', '_use_2017')

    def __init__(self, date, tau_b, tau_d, use_2017=False, daylight_savings=False):
        _SkyCondition.__init__(self, date, daylight_savings)
        self.tau_b = tau_b
        self.tau_d = tau_d
        self.use_2017 = use_2017

    @classmethod
    def from_analysis_period(cls, analysis_period, tau_b, tau_d, use_2017=False,
                             daylight_savings=False):
        """"Initialize a ASHRAETau sky condition from an analysis_period"""
        cls._check_analysis_period(analysis_period)
        st_dt = analysis_period.st_time
        return cls(Date(st_dt.month, st_dt.day, st_dt.leap_year),
                   tau_b, tau_d, use_2017, daylight_savings)

    @classmethod
    def from_dict(cls, data):
        """Create a ASHRAETau sky condition from a dictionary.

        Args:
            data: A python dictionary in the following format.

        .. code-block:: python

            {
            "type": "ASHRAETau",
            "date": [7, 21],
            "tau_b": 0.0,  # float
            "tau_d": 0.0,  # float
            "use_2017": True,  # boolean for whether the 2017 model is used
            "daylight_savings": False  # bool
            }
        """
        # check required keys
        required_keys = ('date', 'tau_b', 'tau_d')
        for key in required_keys:
            assert key in data, 'Required key "{}" is missing!'.format(key)

        # assign defaults for optional keys
        use_2017 = data['use_2017'] if 'use_2017' in data else False
        dl_save = data['daylight_savings'] if 'daylight_savings' \
            in data else False

        return cls(Date.from_array(data['date']),
                   data['tau_b'], data['tau_d'], use_2017, dl_save)

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

    @property
    def use_2017(self):
        """Boolean for whether the version of the 2017 version of the ASHRAE Tau is used.
        """
        return self._use_2017

    @use_2017.setter
    def use_2017(self, value):
        self._use_2017 = bool(value)

    def radiation_values(self, location, timestep=1):
        """Gat arrays of direct, diffuse, and global radiation at each timestep."""
        # create sunpath and get altitude at every timestep of the design day
        sp = Sunpath.from_location(location)
        altitudes = []
        dates = self._get_datetimes(timestep)
        for t_date in dates:
            sun = sp.calculate_sun_from_date_time(t_date)
            altitudes.append(sun.altitude)
        dir_norm, diff_horiz = ashrae_revised_clear_sky(
            altitudes, self._tau_b, self._tau_d, self._use_2017)
        glob_horiz = [dhr + dnr * math.sin(math.radians(alt)) for
                      alt, dnr, dhr in zip(altitudes, dir_norm, diff_horiz)]
        return dir_norm, diff_horiz, glob_horiz

    def to_dict(self):
        """Convert the Sky Condition to a dictionary."""
        return {
            'type': 'ASHRAETau',
            'date': self.date.to_array(),
            'tau_b': self.tau_b,
            'tau_d': self.tau_d,
            'use_2017': self.use_2017,
            'daylight_savings': self.daylight_savings
        }

    def __copy__(self):
        return ASHRAETau(self._date, self._tau_b, self._tau_d, self._use_2017,
                         self._daylight_savings)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (hash(self._date), self._tau_b, self._tau_d, self._use_2017,
                self._daylight_savings)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, ASHRAETau) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        """sky condition representation."""
        return 'ASHRAETau [{}]'.format(self._date)
