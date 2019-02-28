# coding=utf-8
"""Parameters for specifying acceptable thermal conditions using the Adaptive model."""
from __future__ import division

from ._base import ComfortParameter
from ..adaptive import neutral_temperature_conditioned, \
    ashrae55_neutral_offset_from_ppd, en15251_neutral_offset_from_comfort_class


class AdaptiveParameter(ComfortParameter):
    """Parameters of Adaptive comfort.

    Properties:
        ashrae55_or_en15251
        neutral_offset
        avg_month_or_running_mean
        discrete_or_continuous_air_speed
        cold_prevail_temp_limit
        conditioning
        standard
        prevailing_temperture_method
        minimum_operative
    """
    _model = 'Adaptive'

    def __init__(self, ashrae55_or_en15251=None, neutral_offset=None,
                 avg_month_or_running_mean=None, discrete_or_continuous_air_speed=None,
                 cold_prevail_temp_limit=None, conditioning=None):
        """Initalize Adaptive Parameters.

        Args:
            ashrae55_or_en15251: A boolean to note whether to use the ASHRAE-55 neutral
                temperature function (True) or the EN-15251 function (False).
                Note that this input will also determine default values for many of
                the other properties of this object.
            neutral_offset:  The number of degrees Celcius from the neutral temperature
                where the input operative temperature is considered acceptable.
                The default is 2.5C when the neutral temperature function is ASHRAE-55
                and 3C when the neutral temperature function is EN-15251.
                You may want to use the set_neutral_offset_from_ppd() or the
                set_neutral_offset_from_comfort_class() methods on this object to set
                this value using ppd from the ASHRAE-55 standard or comfort classes
                from the EN-15251 standard respectively.
            avg_month_or_running_mean: A boolean to note whether the prevailing outdoor
                temperature is computed from the average monthly temperature (True) or
                a weighted running mean of the last week (False).  The default is True
                when the neutral temperature function is ASHRAE-55 and False when the
                neutral temperature function is EN-15251.
            discrete_or_continuous_air_speed: A boolean to note whether discrete
                categories should be used to assess the effect of elevated air speed
                (True) or whether a continuous function should be used (False).
                The default is True when the neutral temperature function is ASHRAE-55
                and False when the neutral temperature function is EN-15251.
            cold_prevail_temp_limit: A number indicating the prevailing outdoor
                temperature below which acceptable indoor operative temperatures
                flatline. The default is 10C when the neutral temperature function is
                ASHRAE-55 and 15C when the neutral temperature function is EN-15251.
                This number cannot be greater than 22C and cannot be less than 10C.
            conditioning: A number between 0 and 1 that represents how "conditioned" vs.
                "free-running" the building is.
                    0 = free-running (completely passive with no air conditioning)
                    1 = conditioned (no operable windows and fully air conditioned)
                The default is 0 since both the ASHRAE-55 and EN-15251 standards forbid
                the use of adaptive comfort methods when a cooling system is active.
        """
        # get the standard
        self._standard = ashrae55_or_en15251 if ashrae55_or_en15251 is not None else True
        assert isinstance(self._standard, bool), 'ashrae55_or_en15251 must be '\
            'a boolean. Got {}'.format(type(self._standard))

        # set defaults based on the standard
        if self._standard is True:
            default_neutral_offset = 2.5
            default_prevail_method = True
            default_air_speed_method = True
            default_cold_prevail_temp_limit = 10
        else:
            default_neutral_offset = 3
            default_prevail_method = False
            default_air_speed_method = False
            default_cold_prevail_temp_limit = 15

        # assign properties based on defaults and input
        self._prevail_method = avg_month_or_running_mean if \
            avg_month_or_running_mean is not None else default_prevail_method
        self._air_speed_method = discrete_or_continuous_air_speed if \
            discrete_or_continuous_air_speed is not None else default_air_speed_method
        self._cold_prevail_temp_limit = cold_prevail_temp_limit if \
            cold_prevail_temp_limit is not None else default_cold_prevail_temp_limit
        self._conditioning = conditioning if conditioning is not None else 0

        # perform range checks on the inputs
        assert 10 <= self._cold_prevail_temp_limit <= 22, \
            'cold_prevail_temp_limit must be between 10 and 22. Got {}'.format(
                self._cold_prevail_temp_limit)
        assert 0 <= self._conditioning <= 1, \
            'conditioning must be between 0 and 1. Got {}'.format(self._conditioning)

        # assign the neutral tempreature offset
        self.neutral_offset = neutral_offset if \
            neutral_offset is not None else default_neutral_offset

    @property
    def ashrae55_or_en15251(self):
        """A boolean to note whether to use the ASHRAE-55 neutral temperature
        function (True) or the EN-15251 function (False)."""
        return self._standard

    @property
    def neutral_offset(self):
        """The degrees Celcius from the neutral temperature where the operative
        temperature is considered acceptable."""
        return self._neutral_offset

    @neutral_offset.setter
    def neutral_offset(self, offset):
        assert 0 < offset <= 10, \
            'neutral_offset must be between 0 and 10 C. Got {}'.format(offset)
        self._neutral_offset = offset
        self._calc_min_operative_temperature()

    @property
    def avg_month_or_running_mean(self):
        """Boolean noting whether prevailing outdoor temperature is computed from the
        average monthly temperature (True) or a weighted running mean (False)."""
        return self._prevail_method

    @property
    def discrete_or_continuous_air_speed(self):
        """Boolean noting whether discrete categories are used to assess elevated
        air speed (True) or whether a continuous function is used (False)."""
        return self._air_speed_method

    @property
    def cold_prevail_temp_limit(self):
        """The prevailing outdoor temperature below which acceptable indoor
        operative temperatures flatline. [C]"""
        return self._cold_prevail_temp_limit

    @property
    def conditioning(self):
        """A decimal noting how conditioned(1) vs. free-running(0) the building is."""
        return self._conditioning

    @property
    def standard(self):
        """Text denoting the standard.

        Either 'ASHRAE-55' or 'EN-15251'
        """
        if self._standard is True:
            return 'ASHRAE-55'
        else:
            return 'EN-15251'

    @property
    def prevailing_temperture_method(self):
        """Text denoting previaling temperature method.

        Either 'Averaged Monthly' or 'Running Mean'.
        """
        if self._prevail_method is True:
            return 'Averaged Monthly'
        else:
            return 'Running Mean'

    @property
    def air_speed_method(self):
        """Text denoting the type of function used for the cooling effect of air speed.

        Either 'Discrete' or 'Continuous'.
        """
        if self._air_speed_method is True:
            return 'Discrete'
        else:
            return 'Continuous'

    @property
    def minimum_operative(self):
        """Operative Temperature in C below which conditions cannot be comfortable."""
        return self._min_operative

    def set_neutral_offset_from_ppd(self, ppd):
        """Set the offset from neutral temperature given the ASHRAE-55 PPD limit."""
        self.neutral_offset = ashrae55_neutral_offset_from_ppd(ppd)

    def set_neutral_offset_from_comfort_class(self, comfort_class):
        """Set the offset from neutral temperature given the EN-15251 comfort class."""
        self.neutral_offset = en15251_neutral_offset_from_comfort_class(comfort_class)

    def is_comfortable(self, comfort_result):
        """Determine if conditions are comfortable or not.

        Values are one of the following:
            0 = uncomfortable
            1 = comfortable

        Args:
            comfort_result: An adaptive comfort result dictionary from the
                adaptive_comfort_ashrae55 or adaptive_comfort_en15251 functions.
        """
        return True if (comfort_result['to'] >= self._min_operative and
                        comfort_result['deg_comf'] >= -self.neutral_offset and
                        comfort_result['deg_comf'] <= self.neutral_offset +
                        comfort_result['ce']) else False

    def thermal_condition(self, comfort_result):
        """Determine whether conditions are cold, neutral or hot.

        Values are one of the following:
            -1 = cold
             0 = netural
            +1 = hot
        """
        if self.is_comfortable(comfort_result) is False:
            return 1 if comfort_result['deg_comf'] > 0 else -1
        else:
            return 0

    def _calc_min_operative_temperature(self):
        """Set operative temperature below which conditions cannot be comfortable."""
        self._min_operative = neutral_temperature_conditioned(
            self._cold_prevail_temp_limit, self._conditioning, self.standard) \
            - self._neutral_offset

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """Adaptive comfort parameters representation."""
        return "Adaptive Comfort Parameters\n Standard: {}\n Neutral Offset: {}"\
            "\n Prevailing Temperture Method: {}\n Air Speed Method: {}"\
            "\n Cold Prevailing Temperature Limit: {}\n Conditioning Level: {}".format(
                self.standard, self.neutral_offset, self.prevailing_temperture_method,
                self.air_speed_method, self.cold_prevail_temp_limit, self.conditioning)
