# coding=utf-8

import unittest
from pytest import approx
import ladybug.psychrometrics as psy


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
        assert psy.saturated_vapor_pressure(253) == approx(101.783, rel=1e-1)
        assert psy.saturated_vapor_pressure(273) == approx(604.584, rel=1e-1)
        assert psy.saturated_vapor_pressure(293) == approx(2317.545, rel=1e-1)

    def test_humid_ratio_from_db_rh(self):
        """Test humid_ratio_from_db_rh"""
        assert psy.humid_ratio_from_db_rh(17, 50) == approx(0.005949, rel=1e-3)
        assert psy.humid_ratio_from_db_rh(30, 100) == approx(0.02696, rel=1e-3)

    def test_enthalpy_from_db_hr(self):
        """Test enthalpy_from_db_hr"""
        assert psy.enthalpy_from_db_hr(20, 0.01) == approx(45.578, rel=1e-1)

    def test_wet_bulb_from_db_rh(self):
        """Test wet_bulb_from_db_rh"""
        assert psy.wet_bulb_from_db_rh(17, 50) == approx(11.412, rel=1e-1)

    def test_dew_point_from_db_rh(self):
        """Test dew_point_from_db_rh"""
        assert psy.dew_point_from_db_rh(17, 50) == approx(6.54, rel=1e-1)

    def test_rel_humid_from_db_hr(self):
        """Test rel_humid_from_db_hr"""
        assert psy.rel_humid_from_db_hr(17, 0.00594) == approx(50, rel=1e-1)
        assert psy.rel_humid_from_db_hr(30, 0.02696) == approx(100, rel=1e-1)

    def test_rel_humid_from_db_enth(self):
        """Test rel_humid_from_db_enth"""
        assert psy.rel_humid_from_db_enth(20, 50) == approx(81.228, rel=1e-1)

    def test_rel_humid_from_db_dpt(self):
        """Test rel_humid_from_db_dpt"""
        assert psy.rel_humid_from_db_dpt(17, 6.54) == approx(50, rel=1e-1)

    def test_rel_humid_from_db_wb(self):
        """Test rel_humid_from_db_wb"""
        assert psy.rel_humid_from_db_wb(17, 11.412) == approx(50, rel=1e-1)

    def test_dew_point_from_db_hr(self):
        """Test dew_point_from_db_hr"""
        assert psy.dew_point_from_db_hr(20, 0.01) == approx(14.185, rel=1e-1)

    def test_dew_point_from_db_enth(self):
        """Test dew_point_from_db_enth"""
        assert psy.dew_point_from_db_enth(20, 50) == approx(16.686, rel=1e-1)

    def test_dew_point_from_db_wb(self):
        """Test dew_point_from_db_wb"""
        assert psy.dew_point_from_db_wb(20, 10) == approx(-1.4548, rel=1e-1)

    def test_db_temp_from_enth_hr(self):
        """Test db_temp_from_enth_hr"""
        assert psy.db_temp_from_enth_hr(50, 0.01) == approx(24.297, rel=1e-1)

    def test_db_temp_from_wb_rh(self):
        """Test db_temp_from_wb_rh"""
        db, hr = psy.db_temp_from_wb_rh(20, 0)
        assert db == approx(52.74, rel=1e-1)
        assert hr == approx(0, rel=1e-1)
        db, hr = psy.db_temp_from_wb_rh(20, 100)
        assert db == approx(20, rel=1e-1)
        assert hr == approx(0.01455, rel=1e-1)


if __name__ == "__main__":
    unittest.main()
