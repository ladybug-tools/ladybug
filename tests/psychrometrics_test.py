# coding=utf-8

import unittest
from ladybug.psychrometrics import \
    saturated_vapor_pressure, \
    humid_ratio_from_db_rh, \
    enthalpy_from_db_hr, \
    wet_bulb_from_db_rh, \
    dew_point_from_db_rh, \
    rel_humid_from_db_hr, \
    rel_humid_from_db_enth, \
    rel_humid_from_db_dpt, \
    rel_humid_from_db_wb, \
    dew_point_from_db_hr, \
    dew_point_from_db_enth, \
    dew_point_from_db_wb, \
    db_temp_from_enth_hr, \
    db_temp_from_wb_rh


class PsychometricsTestCase(unittest.TestCase):
    """Test for (ladybug/psychometrics.py)"""

    # preparing to test.
    def setUp(self):
        """set up."""
        pass

    def tearDown(self):
        """Nothing to tear down as nothing gets written to file."""
        pass

    def test_saturated_vapor_pressure(self):
        """Test saturated vapor pressure function."""
        assert -0.1 < saturated_vapor_pressure(253) - 101.783 < 0.1
        assert -0.1 < saturated_vapor_pressure(273) - 604.584 < 0.1
        assert -0.1 < saturated_vapor_pressure(293) - 2317.545 < 0.1

    def test_humid_ratio_from_db_rh(self):
        """Test humid_ratio_from_db_rh"""
        assert -0.001 < humid_ratio_from_db_rh(17, 50) - 0.00594 < 0.001
        assert -0.001 < humid_ratio_from_db_rh(30, 100) - 0.02696 < 0.001

    def test_enthalpy_from_db_hr(self):
        """Test enthalpy_from_db_hr"""
        assert -0.1 < enthalpy_from_db_hr(20, 0.01) - 45.578 < 0.1

    def test_wet_bulb_from_db_rh(self):
        """Test wet_bulb_from_db_rh"""
        assert -0.1 < wet_bulb_from_db_rh(17, 50) - 11.412 < 0.1

    def test_dew_point_from_db_rh(self):
        """Test dew_point_from_db_rh"""
        assert -0.1 < dew_point_from_db_rh(17, 50) - 6.54 < 0.1

    def test_rel_humid_from_db_hr(self):
        """Test rel_humid_from_db_hr"""
        assert -0.1 < rel_humid_from_db_hr(17, 0.00594) - 50 < 0.1
        assert -0.1 < rel_humid_from_db_hr(30, 0.02696) - 100 < 0.1

    def test_rel_humid_from_db_enth(self):
        """Test rel_humid_from_db_enth"""
        assert -0.1 < rel_humid_from_db_enth(20, 50) - 81.228 < 0.1

    def test_rel_humid_from_db_dpt(self):
        """Test rel_humid_from_db_dpt"""
        assert -0.1 < rel_humid_from_db_dpt(17, 6.54) - 50 < 0.1

    def test_rel_humid_from_db_wb(self):
        """Test rel_humid_from_db_wb"""
        assert -0.1 < rel_humid_from_db_wb(17, 11.412) - 50 < 0.1

    def test_dew_point_from_db_hr(self):
        """Test dew_point_from_db_hr"""
        assert -0.1 < dew_point_from_db_hr(20, 0.01) - 14.185 < 0.1

    def test_dew_point_from_db_enth(self):
        """Test dew_point_from_db_enth"""
        assert -0.1 < dew_point_from_db_enth(20, 50) - 16.686 < 0.1

    def test_dew_point_from_db_wb(self):
        """Test dew_point_from_db_wb"""
        assert -0.1 < dew_point_from_db_wb(20, 10) + 1.4548 < 0.1

    def test_db_temp_from_enth_hr(self):
        """Test db_temp_from_enth_hr"""
        assert -0.1 < db_temp_from_enth_hr(50, 0.01) - 24.297 < 0.1

    def test_db_temp_from_wb_rh(self):
        """Test db_temp_from_wb_rh"""
        db, hr = db_temp_from_wb_rh(20, 0)
        assert -0.1 < db - 52.74 < 0.1
        assert -0.1 < hr - 0 < 0.1
        db, hr = db_temp_from_wb_rh(20, 100)
        assert -0.1 < db - 20 < 0.1
        assert -0.1 < hr - 0.01455 < 0.1


if __name__ == "__main__":
    unittest.main()
