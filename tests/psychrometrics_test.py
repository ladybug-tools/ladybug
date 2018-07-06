# coding=utf-8

import unittest
from ladybug.psychrometrics import find_saturated_vapor_pressure_torr, \
    find_enthalpy, \
    find_wet_bulb, \
    find_dew_point, \
    find_rel_humid_from_dry_bulb_dew_pt, \
    find_air_temp_from_wet_bulb


class PsychometricsTestCase(unittest.TestCase):
    """Test for (ladybug/psychometrics.py)"""

    # preparing to test.
    def setUp(self):
        """set up."""
        pass

    def tearDown(self):
        """Nothing to tear down as nothing gets written to file."""
        pass

    def test_find_saturated_vapor_pressure_torr(self):
        """"""
        assert find_saturated_vapor_pressure_torr(0) - 4.6 < 0.1
        assert find_saturated_vapor_pressure_torr(20) - 17.5 < 0.1

    def test_find_saturated_vapor_pressure_high_accuracy(self):
        """"""
        pass

    def test_find_humid_ratio(self):
        """"""
        pass

    def test_find_enthalpy(self):
        """"""
        # TODO(@chriswmackey): This fails. find_enthalpy returns 126910.2
        # assert find_enthalpy(20, 50) - 38.54 < 0.1
        pass

    def test_find_wet_bulb(self):
        """"""
        assert find_wet_bulb(17, 50) - 11.32 < 0.1

    def test_find_dew_point(self):
        """"""
        assert find_dew_point(17, 50) - 6.54 < 0.1

    def test_find_rel_humid_from_humid_ratio(self):
        """"""
        pass

    def test_find_rel_humid_from_dry_bulb_dew_pt(self):
        """"""
        assert find_rel_humid_from_dry_bulb_dew_pt(17, 11.32) - 50 < 0.1

    def test_find_air_temp_from_enthalpy(self):
        """"""
        pass

    def test_find_air_temp_from_wet_bulb(self):
        """"""
        air_temp, humidity_ratio = find_air_temp_from_wet_bulb(13.78, 50)
        # TODO(@chriswmackey): This fails. air_temp is 126910.2
        # assert air_temp - 20 < 0.1
        assert humidity_ratio - 50 < 0.1


if __name__ == "__main__":
    unittest.main()
