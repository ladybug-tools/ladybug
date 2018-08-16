from .location import Location

import os
import re
import codecs
import platform

h_types = ['Wetbulb', 'Dewpoint', 'HumidityRatio', 'Enthalpy',
           'RelativeHumiditySchedule', 'WetBulbProfileMultiplierSchedule',
           'WetBulbProfileDifferenceSchedule',
           'WetBulbProfileDefaultMultipliers']

class Ddy(object):
    """Import data from a local .ddy file.

    args:
        file_path: Local file address to a .stat file.

    properties:
        location: A Ladybug location object
        design_days: A list of the design days in the ddy file.
    """

class DesignDay(object):
    """Represents design day conditions.

    properties:
        name
        day_type
        dry_bulb_condition
        humidity_condition
        wind_condition
        sky_condition
    """

    def __init__(self, name, day_type, dry_bulb_condition, humidity_condition,
                 wind_condition, sky_condition):
        """Initalize the class."""
        self.name = name
        self.day_type = day_type



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
    def isDryBulbCondition(self):
        """Return Ture."""
        return True

    @property
    def max_dry_bulb(self):
        """Return the max dry bulb temperature."""
        return self._max_dry_bulb

    @max_dry_bulb.setter
    def max_dry_bulb(self, data):
        assert isinstance(data, (float, int)), 'max_dry_bulb must be an' \
            ' number. Got {}'.format(type(data))
        self._max_dry_bulb = data

    @property
    def dry_bulb_range(self):
        """Return the dry bulb range over the day."""
        return self._dry_bulb_range

    @dry_bulb_range.setter
    def dry_bulb_range(self, data):
        assert isinstance(data, (float, int)), 'dry_bulb_range must be a' \
            ' number. Got {}'.format(type(data))
        self._dry_bulb_range = data

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """stat file representation."""
        return "DryBulbCondition [%s]" % str(max_dry_bulb)


class HumidityCondition(object):
    """Represents humidity conditions on the design day.

    attributes:
        humidity_condition_type: Choose from
            Wetbulb, Dewpoint, HumidityRatio, Enthalpy
        condition_value: The value of the condition above
        barometric_pressure: Default is to use pressure at sea level
    """
    def __init__(self, humidity_condition_type, condition_value,
                 barometric_pressure=101325):
        """Initalize the class."""
        self.humidity_condition_type = humidity_condition_type
        self.condition_value = condition_value
        self.barometric_pressure = barometric_pressure

    @property
    def isHumidityCondition(self):
        """Return Ture."""
        return True

    @property
    def humidity_condition_type(self):
        """Return the humidity condition type."""
        return self._humidity_condition_type

    @humidity_condition_type.setter
    def humidity_condition_type(self, data):
        assert data in h_types, 'humidity_condition_type {} is not' \
            ' recognized'.format(str(data))
        self._max_dry_bulb = data

    @property
    def condition_value(self):
        """Return the value of the humidity."""
        return self._condition_value

    @condition_value.setter
    def condition_valuee(self, data):
        assert isinstance(data, (float, int)), 'condition_value must be a' \
            ' number. Got {}'.format(type(data))
        self._condition_value = data

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """stat file representation."""
        return "HumidityCondition [{}: {}]".format(
            self._humidity_condition_type,str(self._condition_value))


class WindCondition(object):
    """Represents wind and rain conditions on the design day.

    properties:
        wind_speed
        wind_direction
        rain
        snow_on_ground
    """

class _SkyCondition(object):
    """An object representing a sky on the design day.

    properties:
        solar_model
        month
        day_of_month
        daylight_savings_indicator
    """

class OriginalClearSkyCondition(_DesignDaySky):
    """An object representing an ASHRAE Clear Sky.

    properties:
        clearness
    """

class RevisedClearSkyCondition(_DesignDaySky):
    """An object representing an ASHRAE Clear Sky.

    properties:
        tau_b
        tau_d
    """
