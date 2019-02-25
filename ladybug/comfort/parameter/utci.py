# coding=utf-8
"""Parameters for specifying acceptable thermal conditions using the UTCI model."""
from __future__ import division

from ._base import ComfortParameter


class UTCIParameter(ComfortParameter):
    """Parameters of UTCI comfort.

    Properties:
        cold_thresh:  UTCI temperature below which conditions
            represent cold stress [C]. Default: 9C.
        heat_thresh:  UTCI temperature above which conditions
            represent heat stress [C]. Default: 26C.

        extreme_cold_thresh:  UTCI temperature below which conditions
            represent extreme cold stress [C]. Default: -40C.
        very_strong_cold_thresh:  UTCI temperature below which conditions
            represent very strong cold stress [C]. Default: -27C.
        strong_cold_thresh:  UTCI temperature below which conditions
            represent strong cold stress [C]. Default: -13C.

        moderate_cold_thresh:  UTCI temperature below which conditions
            represent moderate cold stress [C]. Default: 0C.
        moderate_heat_thresh:  UTCI temperature above which conditions
            represent moderateheat stress [C]. Default: 28C.

        strong_heat_thresh:  UTCI temperature above which conditions
            represent strong heat stress [C]. Default: 32C.
        very_strong_heat_thresh:  UTCI temperature above which conditions
            represent very strong heat stress [C]. Default: 38C.
        extreme_heat_thresh:  UTCI temperature above which conditions
            represent extreme heat stress [C]. Default: 46C.
    """
    _model = 'Universal Thermal Climate Index'

    def __init__(self, cold_thresh=None, heat_thresh=None,
                 extreme_cold_thresh=None, very_strong_cold_thresh=None,
                 strong_cold_thresh=None,
                 moderate_cold_thresh=None, moderate_heat_thresh=None,
                 strong_heat_thresh=None,
                 very_strong_heat_thresh=None, extreme_heat_thresh=None):
        """Initalize UTCI Parameters.

        Args:
            cold_thresh:  UTCI temperature below which conditions
                represent cold stress [C]. Default: 9C.
            heat_thresh:  UTCI temperature above which conditions
                represent heat stress [C]. Default: 26C.
            extreme_cold_thresh:  UTCI temperature below which conditions
                represent extreme cold stress [C]. Default: -40C.
            very_strong_cold_thresh:  UTCI temperature below which conditions
                represent very strong cold stress [C]. Default: -27C.
            strong_cold_thresh:  UTCI temperature below which conditions
                represent strong cold stress [C]. Default: -13C.
            moderate_cold_thresh:  UTCI temperature below which conditions
                represent moderate cold stress [C]. Default: 0C.
            moderate_heat_thresh:  UTCI temperature above which conditions
                represent moderateheat stress [C]. Default: 28C.
            strong_heat_thresh:  UTCI temperature above which conditions
                represent strong heat stress [C]. Default: 32C.
            very_strong_heat_thresh:  UTCI temperature above which conditions
                represent very strong heat stress [C]. Default: 38C.
            extreme_heat_thresh:  UTCI temperature above which conditions
                represent extreme heat stress [C]. Default: 46C.
        """

        self._cold_thresh = cold_thresh if cold_thresh is not None else 9
        self._heat_thresh = heat_thresh if heat_thresh is not None else 26

        self._extreme_cold_thresh = \
            extreme_cold_thresh if extreme_cold_thresh is not None else -40
        self._very_strong_cold_thresh = \
            very_strong_cold_thresh if very_strong_cold_thresh is not None else -27
        self._strong_cold_thresh = \
            strong_cold_thresh if strong_cold_thresh is not None else -13

        self._moderate_cold_thresh = \
            moderate_cold_thresh if moderate_cold_thresh is not None else 0
        self._moderate_heat_thresh = \
            moderate_heat_thresh if moderate_heat_thresh is not None else 28

        self._strong_heat_thresh = \
            strong_heat_thresh if strong_heat_thresh is not None else 32
        self._very_strong_heat_thresh = \
            very_strong_heat_thresh if very_strong_heat_thresh is not None else 38
        self._extreme_heat_thresh = \
            extreme_heat_thresh if extreme_heat_thresh is not None else 46

        assert self._extreme_cold_thresh <= self._very_strong_cold_thresh, \
            'extreme_strong_cold_thresh must be <= very_strong_cold_thresh'
        assert self._very_strong_cold_thresh <= self._strong_cold_thresh, \
            'very_strong_cold_thresh must be <= strong_cold_thresh'
        assert self._strong_cold_thresh <= self._moderate_cold_thresh, \
            'strong_cold_thresh must be <= moderate_cold_thresh'
        assert self._moderate_cold_thresh <= self._cold_thresh, \
            'moderate_cold_thresh must be <= cold_thresh'
        assert self._cold_thresh <= self._heat_thresh, \
            'cold_thresh must be <= heat_thresh'
        assert self._heat_thresh <= self._moderate_heat_thresh, \
            'heat_thresh must be <= moderate_heat_thresh'
        assert self._moderate_heat_thresh <= self._strong_heat_thresh, \
            'moderate_heat_thresh must be <= strong_heat_thresh'
        assert self._strong_heat_thresh <= self._very_strong_heat_thresh, \
            'strong_heat_thresh must be <= very_strong_heat_thresh'
        assert self._very_strong_heat_thresh <= self._extreme_heat_thresh, \
            'very_strong_heat_thresh must be <= extreme_heat_thresh'

    @property
    def cold_thresh(self):
        """UTCI temperature below which conditions represent cold stress [C].

        Default: 9C.
        """
        return self._cold_thresh

    @property
    def heat_thresh(self):
        """UTCI temperature above which conditions represent heat stress [C].

        Default: 26C.
        """
        return self._heat_thresh

    @property
    def extreme_cold_thresh(self):
        """UTCI temperature below which conditions represent extreme cold stress [C].

        Default: -40C.
        """
        return self._extreme_cold_thresh

    @property
    def very_strong_cold_thresh(self):
        """UTCI temperature below which conditions represent very strong cold stress [C].

        Default: -27C.
        """
        return self._very_strong_cold_thresh

    @property
    def strong_cold_thresh(self):
        """UTCI temperature below which conditions represent strong cold stress [C].

        Default: -13C.
        """
        return self._strong_cold_thresh

    @property
    def moderate_cold_thresh(self):
        """UTCI temperature below which conditions represent moderate cold stress [C].

        Default: 0C.
        """
        return self._moderate_cold_thresh

    @property
    def moderate_heat_thresh(self):
        """UTCI temperature above which conditions represent moderate heat stress [C].

        Default: 28C.
        """
        return self._moderate_heat_thresh

    @property
    def strong_heat_thresh(self):
        """UTCI temperature above which conditions represent strong heat stress [C].

        Default: 32C.
        """
        return self._strong_heat_thresh

    @property
    def very_strong_heat_thresh(self):
        """UTCI temperature above which conditions represent very strong heat stress [C].

        Default: 38C.
        """
        return self._very_strong_heat_thresh

    @property
    def extreme_heat_thresh(self):
        """UTCI temperature above which conditions represent extreme heat stress [C].

        Default: 46C.
        """
        return self._extreme_heat_thresh

    def is_comfortable(self, utci):
        """Determine if conditions are comfortable or not.

        Values are one of the following:
            0 = uncomfortable
            1 = comfortable
        """
        return True if (utci >= self._cold_thresh
                        and utci <= self._heat_thresh) else False

    def thermal_condition(self, utci):
        """Determine whether conditions are cold, neutral or hot.

        Values are one of the following:
            -1 = cold
             0 = netural
            +1 = hot
        """
        if utci < self._cold_thresh:
            return -1
        elif utci > self._heat_thresh:
            return 1
        else:
            return 0

    def thermal_condition_low(self, utci):
        """Determine the thermal condition at a low resolution.

        Values are one of the following:
            -2 = strong/extreme cold stress
            -1 = moderate cold stress
             0 = no thermal stress
            +1 = moderate heat stress
            +2 = strong/extreme heat stress
        """
        if utci < self._strong_cold_thresh:
            return -2
        elif utci < self._cold_thresh:
            return -1
        elif utci > self._strong_heat_thresh:
            return 2
        elif utci > self._heat_thresh:
            return 1
        else:
            return 0

    def thermal_condition_medium(self, utci):
        """Determine the thermal condition at a medium resolution.

        Values are one of the following:
            -3 = very strong/extreme cold stress
            -2 = strong cold stress
            -1 = moderate cold stress
             0 = no thermal stress
            +1 = moderate heat stress
            +2 = strong heat stress
            +3 = very strong/extreme heat stress
        """
        if utci < self._very_strong_cold_thresh:
            return -3
        elif utci < self._strong_cold_thresh:
            return -2
        elif utci < self._cold_thresh:
            return -1
        elif utci > self._very_strong_heat_thresh:
            return 3
        elif utci > self._strong_heat_thresh:
            return 2
        elif utci > self._heat_thresh:
            return 1
        else:
            return 0

    def thermal_condition_high(self, utci):
        """Determine the thermal condition at a high resolution.

        Values are one of the following:
            -4 = very strong/extreme cold stress
            -3 = strong cold stress
            -2 = moderate cold stress
            -1 = slight cold stress
             0 = no thermal stress
            +1 = slight heat stress
            +2 = moderate heat stress
            +3 = strong heat stress
            +4 = very strong/extreme heat stress
        """
        if utci < self._very_strong_cold_thresh:
            return -4
        elif utci < self._strong_cold_thresh:
            return -3
        elif utci < self._moderate_cold_thresh:
            return -2
        elif utci < self._cold_thresh:
            return -1
        elif utci > self._very_strong_heat_thresh:
            return 4
        elif utci > self._strong_heat_thresh:
            return 3
        elif utci > self._moderate_heat_thresh:
            return 2
        elif utci > self._heat_thresh:
            return 1
        else:
            return 0

    def thermal_condition_very_high(self, utci):
        """Determine the thermal condition at a very high resolution.

        Values are one of the following:
            -5 = extreme cold stress
            -4 = very strong cold stress
            -3 = strong cold stress
            -2 = moderate cold stress
            -1 = slight cold stress
             0 = no thermal stress
            +1 = slight heat stress
            +2 = moderate heat stress
            +3 = strong heat stress
            +4 = very strong heat stress
            +5 = extreme heat stress
        """
        if utci < self._extreme_cold_thresh:
            return -5
        elif utci < self._very_strong_cold_thresh:
            return -4
        elif utci < self._strong_cold_thresh:
            return -3
        elif utci < self._moderate_cold_thresh:
            return -2
        elif utci < self._cold_thresh:
            return -1
        elif utci > self._extreme_heat_thresh:
            return 5
        elif utci > self._very_strong_heat_thresh:
            return 4
        elif utci > self._strong_heat_thresh:
            return 3
        elif utci > self._moderate_heat_thresh:
            return 2
        elif utci > self._heat_thresh:
            return 1
        else:
            return 0

    def original_utci_category(self, utci):
        """Determine the category according to the original UTCI assessment scale.

        Glossary of Terms for Thermal Physiology (2003).
        Journal of Thermal Biology 28, 75-106

        Values are one of the following:
            0 = extreme cold stress
            1 = very strong cold stress
            2 = strong cold stress
            3 = moderate cold stress
            4 = slight cold stress
            5 = no thermal stress
            6 = moderate heat stress
            7 = strong heat stress
            8 = strong heat stress
            9 = extreme heat stress
        """
        if utci < self._extreme_cold_thresh:
            return 0
        elif utci < self._very_strong_cold_thresh:
            return 1
        elif utci < self._strong_cold_thresh:
            return 2
        elif utci < self._moderate_cold_thresh:
            return 3
        elif utci < self._cold_thresh:
            return 4
        elif utci > self._extreme_heat_thresh:
            return 9
        elif utci > self._very_strong_heat_thresh:
            return 8
        elif utci > self._strong_heat_thresh:
            return 7
        elif utci > self._heat_thresh:
            return 6
        else:
            return 5

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """PMV comfort parameters representation."""
        return "UTCI Comfort Parameters\n Cold Threshold: {}C"\
            "\n Heat Threshold: {}C".format(
                self._cold_thresh, self._heat_thresh)
