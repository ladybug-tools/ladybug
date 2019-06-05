# coding=utf-8

from ladybug.psychrometrics import humid_ratio_from_db_rh, enthalpy_from_db_hr, \
    wet_bulb_from_db_rh, dew_point_from_db_rh, rel_humid_from_db_hr, \
    rel_humid_from_db_enth, rel_humid_from_db_dpt, rel_humid_from_db_wb, \
    dew_point_from_db_hr, dew_point_from_db_enth, dew_point_from_db_wb, \
    db_temp_from_enth_hr, db_temp_from_wb_rh, dew_point_from_db_rh_high_accuracy

import unittest
import pytest


class PsychrometricsTestCase(unittest.TestCase):
    """Test for (ladybug/psychrometrics.py)"""

    def test_humid_ratio_from_db_rh(self):
        """Test the accuracy of the humid_ratio_from_db_rh function."""
        assert humid_ratio_from_db_rh(30, 0) == pytest.approx(0, rel=1e-3)
        assert humid_ratio_from_db_rh(30, 50) == pytest.approx(0.013314041476, rel=1e-3)
        assert humid_ratio_from_db_rh(30, 100) == pytest.approx(0.027210538714, rel=1e-3)
        assert humid_ratio_from_db_rh(20, 0) == pytest.approx(0, rel=1e-3)
        assert humid_ratio_from_db_rh(20, 50) == pytest.approx(0.00726350220, rel=1e-3)
        assert humid_ratio_from_db_rh(20, 100) == pytest.approx(0.0146986527, rel=1e-3)
        assert humid_ratio_from_db_rh(-20, 0) == pytest.approx(0, rel=1e-3)
        assert humid_ratio_from_db_rh(-20, 50) == pytest.approx(0.0003173788667, rel=1e-3)
        assert humid_ratio_from_db_rh(-20, 100) == pytest.approx(0.000635081792, rel=1e-3)

    def test_enthalpy_from_db_hr(self):
        """Test the accuracy of the enthalpy_from_db_hr function."""
        assert enthalpy_from_db_hr(30, 0) == pytest.approx(30.18, rel=1e-3)
        assert enthalpy_from_db_hr(30, 0.0133) == pytest.approx(64.18544, rel=1e-3)
        assert enthalpy_from_db_hr(30, 0.02721) == pytest.approx(99.750528, rel=1e-3)
        assert enthalpy_from_db_hr(20, 0) == pytest.approx(20.12, rel=1e-3)
        assert enthalpy_from_db_hr(20, 0.00726) == pytest.approx(38.547332, rel=1e-3)
        assert enthalpy_from_db_hr(20, 0.01469) == pytest.approx(57.406158, rel=1e-3)
        assert enthalpy_from_db_hr(-20, 0) == pytest.approx(0, rel=1e-3)
        assert enthalpy_from_db_hr(-20, 0.00031738) == pytest.approx(0, rel=1e-3)
        assert enthalpy_from_db_hr(-20, 0.000635) == pytest.approx(0, rel=1e-3)
        assert enthalpy_from_db_hr(-20, 0, -273.15) == pytest.approx(254.66889, rel=1e-3)
        assert enthalpy_from_db_hr(-20, 0.00031738, -273.15) == pytest.approx(255.6121, rel=1e-3)
        assert enthalpy_from_db_hr(-20, 0.000635, -273.15) == pytest.approx(256.556, rel=1e-3)

    def test_wet_bulb_from_db_rh(self):
        """Test the accuracy of the wet_bulb_from_db_rh function."""
        assert wet_bulb_from_db_rh(30, 0) == pytest.approx(10.871, rel=1e-3)
        assert wet_bulb_from_db_rh(30, 50) == pytest.approx(22.144, rel=1e-3)
        assert wet_bulb_from_db_rh(30, 100) == pytest.approx(29.0, rel=1e-3)
        assert wet_bulb_from_db_rh(20, 0) == pytest.approx(6.07, rel=1e-3)
        assert wet_bulb_from_db_rh(20, 50) == pytest.approx(13.88, rel=1e-3)
        assert wet_bulb_from_db_rh(20, 100) == pytest.approx(20, rel=1e-3)
        assert wet_bulb_from_db_rh(-20, 0) == pytest.approx(-21.69, rel=1e-3)
        assert wet_bulb_from_db_rh(-20, 50) == pytest.approx(-20.84, rel=1e-3)
        assert wet_bulb_from_db_rh(-20, 100) == pytest.approx(-20, rel=1e-3)

    def test_dew_point_from_db_rh(self):
        """Test the accuracy of the dew_point_from_db_rh function."""
        assert dew_point_from_db_rh(30, 0) == pytest.approx(-273.15, rel=1e-3)
        assert dew_point_from_db_rh(30, 50) == pytest.approx(18.45805, rel=1e-3)
        assert dew_point_from_db_rh(30, 100) == pytest.approx(30, rel=1e-3)
        assert dew_point_from_db_rh(20, 0) == pytest.approx(-273.15, rel=1e-3)
        assert dew_point_from_db_rh(20, 50) == pytest.approx(9.270086, rel=1e-3)
        assert dew_point_from_db_rh(20, 100) == pytest.approx(20, rel=1e-3)
        assert dew_point_from_db_rh(-20, 0) == pytest.approx(-273.15, rel=1e-3)
        assert dew_point_from_db_rh(-20, 50) == pytest.approx(-27.76753, rel=1e-3)
        assert dew_point_from_db_rh(-20, 100) == pytest.approx(-20, rel=1e-3)

    def test_rel_humid_from_db_hr(self):
        """Test the accuracy of the rel_humid_from_db_hr function."""
        assert rel_humid_from_db_hr(30, 0) == pytest.approx(0, rel=1e-2)
        assert rel_humid_from_db_hr(30, 0.0133) == pytest.approx(50, rel=1e-2)
        assert rel_humid_from_db_hr(30, 0.02721) == pytest.approx(100, rel=1e-2)
        assert rel_humid_from_db_hr(20, 0) == pytest.approx(0, rel=1e-2)
        assert rel_humid_from_db_hr(20, 0.00726) == pytest.approx(50, rel=1e-2)
        assert rel_humid_from_db_hr(20, 0.01469) == pytest.approx(100, rel=1e-2)
        assert rel_humid_from_db_hr(-20, 0) == pytest.approx(0, rel=1e-2)
        assert rel_humid_from_db_hr(-20, 0.00031738) == pytest.approx(50, rel=1e-2)
        assert rel_humid_from_db_hr(-20, 0.000635) == pytest.approx(100, rel=1e-2)

    def test_rel_humid_from_db_enth(self):
        """Test the accuracy of the rel_humid_from_db_enth function."""
        assert rel_humid_from_db_enth(30, 30.18) == pytest.approx(0, rel=1e-2)
        assert rel_humid_from_db_enth(30, 64.18544) == pytest.approx(50, rel=1e-2)
        assert rel_humid_from_db_enth(30, 99.750528) == pytest.approx(100, rel=1e-2)
        assert rel_humid_from_db_enth(20, 20.12) == pytest.approx(0, rel=1e-2)
        assert rel_humid_from_db_enth(20, 38.547332) == pytest.approx(50, rel=1e-2)
        assert rel_humid_from_db_enth(20, 57.406158) == pytest.approx(100, rel=1e-2)
        assert rel_humid_from_db_enth(-20, 0) > 100
        assert rel_humid_from_db_enth(-20, 255.6121, reference_temp=-273.15) == pytest.approx(50., rel=1e-2)
        assert rel_humid_from_db_enth(-20, 256.556, reference_temp=-273.15) == pytest.approx(100., rel=1e-2)


    def test_rel_humid_from_db_dpt(self):
        """Test the accuracy of the rel_humid_from_db_dpt function."""
        assert rel_humid_from_db_dpt(30, 18.45805) == pytest.approx(50, rel=1e-2)
        assert rel_humid_from_db_dpt(30, 30) == pytest.approx(100, rel=1e-2)
        assert rel_humid_from_db_dpt(20, 9.270086) == pytest.approx(50, rel=1e-2)
        assert rel_humid_from_db_dpt(20, 20) == pytest.approx(100, rel=1e-2)
        assert rel_humid_from_db_dpt(-20, -27.0215503) == pytest.approx(50, rel=1e-2)
        assert rel_humid_from_db_dpt(-20, -20) == pytest.approx(100, rel=1e-2)

    def test_rel_humid_from_db_wb(self):
        """Test the accuracy of the rel_humid_from_db_wb function."""
        assert rel_humid_from_db_wb(30, 10.871) < 1
        assert rel_humid_from_db_wb(30, 22.144) == pytest.approx(50, rel=1e-2)
        assert rel_humid_from_db_wb(30, 29.0) > 90
        assert rel_humid_from_db_wb(20, 6.07) < 1
        assert rel_humid_from_db_wb(20, 13.88) == pytest.approx(50, rel=1e-2)
        assert rel_humid_from_db_wb(20, 20) == pytest.approx(100, rel=1e-2)
        assert rel_humid_from_db_wb(-20, -21.69) < 1
        assert 30 < rel_humid_from_db_wb(-20, -20.84) < 70
        assert rel_humid_from_db_wb(-20, -20) == pytest.approx(100, rel=1e-2)

    def test_dew_point_from_db_hr(self):
        """Test the accuracy of the dew_point_from_db_hr function."""
        assert dew_point_from_db_hr(30, 0.015) == pytest.approx(20.330675, rel=1e-3)
        assert dew_point_from_db_hr(20, 0.01) == pytest.approx(14.0418, rel=1e-3)
        assert dew_point_from_db_hr(-20, 0.0003) == pytest.approx(-28.37464, rel=1e-3)

    def test_dew_point_from_db_enth(self):
        """Test the accuracy of the dew_point_from_db_enth function."""
        assert dew_point_from_db_enth(30, 64.18544) == pytest.approx(18.441586, rel=1e-2)
        assert dew_point_from_db_enth(20, 38.547332) == pytest.approx(9.263014, rel=1e-2)
        assert dew_point_from_db_enth(-20, 0) > -20
        assert dew_point_from_db_enth(-20, 255.6121, reference_temp=-273.15) == pytest.approx(-27.76758, rel=1e-2)

    def test_dew_point_from_db_wb(self):
        """Test the accuracy of the dew_point_from_db_wb function."""
        assert dew_point_from_db_wb(30, 22.144) == pytest.approx(18.593726, rel=1e-3)
        assert dew_point_from_db_wb(20, 13.88) == pytest.approx(9.35052249, rel=1e-3)
        assert dew_point_from_db_wb(-20, -20.84) == pytest.approx(-30.775566, rel=1e-3)

    def test_db_temp_from_enth_hr(self):
        """Test the accuracy of the db_temp_from_enth_hr function."""
        assert db_temp_from_enth_hr(60, 0.015) == pytest.approx(21.66899, rel=1e-3)
        assert db_temp_from_enth_hr(60, 0.01) == pytest.approx(34.0169, rel=1e-3)
        assert db_temp_from_enth_hr(30, 0.005) == pytest.approx(17.166, rel=1e-3)

    def test_db_temp_from_wb_rh(self):
        """Test the accuracy of the db_temp_from_wb_rh function."""
        assert db_temp_from_wb_rh(30, 100)[1] == pytest.approx(0.0272105, rel=1e-3)
        assert db_temp_from_wb_rh(20, 100)[1] == pytest.approx(0.0146986, rel=1e-3)
        assert db_temp_from_wb_rh(-20, 100)[1] == pytest.approx(0.00063508, rel=1e-3)
        assert db_temp_from_wb_rh(20, 0)[0] == pytest.approx(53.05368, rel=1e-3)
        assert db_temp_from_wb_rh(10, 0)[0] == pytest.approx(27.16106, rel=1e-3)
        assert db_temp_from_wb_rh(-20, 0)[0] == pytest.approx(-18.5718, rel=1e-3)

    def test_dew_point_from_db_rh_high_accuracy(self):
        """Test the accuracy of the dew_point_from_db_rh_high_accuracy function."""
        assert dew_point_from_db_rh_high_accuracy(180, 10) == pytest.approx(99.6844, rel=1e-3)
        assert dew_point_from_db_rh_high_accuracy(180, 50) == pytest.approx(151.9373, rel=1e-3)
        assert dew_point_from_db_rh_high_accuracy(180, 100) == pytest.approx(180, rel=1e-3)
        assert dew_point_from_db_rh_high_accuracy(-80, 10) == pytest.approx(-93.065214, rel=1e-3)
        assert dew_point_from_db_rh_high_accuracy(-80, 50) == pytest.approx(-84.125, rel=1e-3)
        assert dew_point_from_db_rh_high_accuracy(-80, 100) == pytest.approx(-80, rel=1e-3)


if __name__ == "__main__":
    unittest.main()
