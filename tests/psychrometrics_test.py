# coding=utf-8
from ladybug.psychrometrics import humid_ratio_from_db_rh, enthalpy_from_db_hr, \
    wet_bulb_from_db_rh, dew_point_from_db_rh, rel_humid_from_db_hr, \
    rel_humid_from_db_enth, rel_humid_from_db_dpt, rel_humid_from_db_wb, \
    dew_point_from_db_hr, dew_point_from_db_enth, dew_point_from_db_wb, \
    db_temp_from_enth_hr, db_temp_from_rh_hr, db_temp_and_hr_from_wb_rh, \
    dew_point_from_db_rh_fast, wet_bulb_from_db_rh_fast, wet_bulb_from_db_hr

import pytest


def test_humid_ratio_from_db_rh():
    """Test the accuracy of the humid_ratio_from_db_rh function."""
    assert humid_ratio_from_db_rh(30, 0) == pytest.approx(0, rel=1e-3)
    assert humid_ratio_from_db_rh(30, 50) == pytest.approx(0.013314, rel=1e-3)
    assert humid_ratio_from_db_rh(30, 100) == pytest.approx(0.02721, rel=1e-3)
    assert humid_ratio_from_db_rh(20, 0) == pytest.approx(0, rel=1e-3)
    assert humid_ratio_from_db_rh(20, 50) == pytest.approx(0.00726, rel=1e-3)
    assert humid_ratio_from_db_rh(20, 100) == pytest.approx(0.014698, rel=1e-3)
    assert humid_ratio_from_db_rh(-20, 0) == pytest.approx(0, rel=1e-3)
    assert humid_ratio_from_db_rh(-20, 50) == pytest.approx(0.0003173, rel=1e-3)
    assert humid_ratio_from_db_rh(-20, 100) == pytest.approx(0.00063508, rel=1e-3)


def test_enthalpy_from_db_hr():
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


def test_dew_point_from_db_rh():
    """Test the accuracy of the dew_point_from_db_rh function."""
    assert dew_point_from_db_rh(30, 0) == pytest.approx(-273.15, rel=1e-3)
    assert dew_point_from_db_rh(30, 50) == pytest.approx(18.4466, rel=1e-3)
    assert dew_point_from_db_rh(30, 100) == pytest.approx(30, rel=1e-3)
    assert dew_point_from_db_rh(20, 0) == pytest.approx(-273.15, rel=1e-3)
    assert dew_point_from_db_rh(20, 50) == pytest.approx(9.27239, rel=1e-3)
    assert dew_point_from_db_rh(20, 100) == pytest.approx(20, rel=1e-3)
    assert dew_point_from_db_rh(-20, 0) == pytest.approx(-273.15, rel=1e-3)
    assert dew_point_from_db_rh(-20, 50) == pytest.approx(-27.0217, rel=1e-3)
    assert dew_point_from_db_rh(-20, 100) == pytest.approx(-20, rel=1e-3)

    assert dew_point_from_db_rh(180, 10) == pytest.approx(99.6844, rel=1e-3)
    assert dew_point_from_db_rh(180, 50) == pytest.approx(151.9373, rel=1e-3)
    assert dew_point_from_db_rh(180, 100) == pytest.approx(180, rel=1e-3)
    assert dew_point_from_db_rh(-80, 10) == pytest.approx(-93.065214, rel=1e-3)
    assert dew_point_from_db_rh(-80, 50) == pytest.approx(-84.125, rel=1e-3)
    assert dew_point_from_db_rh(-80, 100) == pytest.approx(-80, rel=1e-3)


def test_wet_bulb_from_db_rh():
    """Test the accuracy of the wet_bulb_from_db_rh function."""
    assert wet_bulb_from_db_rh(30, 0) == pytest.approx(10.49804, rel=1e-3)
    assert wet_bulb_from_db_rh(30, 50) == pytest.approx(22.011934, rel=1e-3)
    assert wet_bulb_from_db_rh(30, 100) == pytest.approx(30.0, rel=1e-3)
    assert wet_bulb_from_db_rh(20, 0) == pytest.approx(5.865, rel=1e-3)
    assert wet_bulb_from_db_rh(20, 50) == pytest.approx(13.7562, rel=1e-3)
    assert wet_bulb_from_db_rh(20, 100) == pytest.approx(20, rel=1e-3)
    assert wet_bulb_from_db_rh(-20, 0) == pytest.approx(-21.5142, rel=1e-3)
    assert wet_bulb_from_db_rh(-20, 50) == pytest.approx(-20.7405, rel=1e-3)
    assert wet_bulb_from_db_rh(-20, 100) == pytest.approx(-20, rel=1e-3)


def test_wet_bulb_from_db_hr():
    """Test the accuracy of the wet_bulb_from_db_hr function."""
    assert wet_bulb_from_db_hr(30, 0.01) == pytest.approx(19.622532, rel=1e-3)
    assert wet_bulb_from_db_hr(20, 0.005) == pytest.approx(11.54350508, rel=1e-3)


def test_rel_humid_from_db_hr():
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


def test_rel_humid_from_db_enth():
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


def test_rel_humid_from_db_dpt():
    """Test the accuracy of the rel_humid_from_db_dpt function."""
    assert rel_humid_from_db_dpt(30, 18.45805) == pytest.approx(50, rel=1e-2)
    assert rel_humid_from_db_dpt(30, 30) == pytest.approx(100, rel=1e-2)
    assert rel_humid_from_db_dpt(20, 9.270086) == pytest.approx(50, rel=1e-2)
    assert rel_humid_from_db_dpt(20, 20) == pytest.approx(100, rel=1e-2)
    assert rel_humid_from_db_dpt(-20, -27.0215503) == pytest.approx(50, rel=1e-2)
    assert rel_humid_from_db_dpt(-20, -20) == pytest.approx(100, rel=1e-2)


def test_rel_humid_from_db_wb():
    """Test the accuracy of the rel_humid_from_db_wb function."""
    assert rel_humid_from_db_wb(30, 10.4980) < 1
    assert rel_humid_from_db_wb(30, 22.01193) == pytest.approx(50, rel=1e-2)
    assert rel_humid_from_db_wb(30, 30.0) == pytest.approx(100, rel=1e-2)
    assert rel_humid_from_db_wb(20, 5.8649597) < 1
    assert rel_humid_from_db_wb(20, 13.756197) == pytest.approx(50, rel=1e-1)
    assert rel_humid_from_db_wb(20, 20) == pytest.approx(100, rel=1e-2)
    assert rel_humid_from_db_wb(-20, -21.51420288086) < 1
    assert 45 < rel_humid_from_db_wb(-20, -20.74057642) < 55
    assert rel_humid_from_db_wb(-20, -20) == pytest.approx(100, rel=1e-2)


def test_dew_point_from_db_hr():
    """Test the accuracy of the dew_point_from_db_hr function."""
    assert dew_point_from_db_hr(30, 0.015) == pytest.approx(20.330675, rel=1e-3)
    assert dew_point_from_db_hr(20, 0.01) == pytest.approx(14.0418, rel=1e-3)
    assert dew_point_from_db_hr(-20, 0.0003) == pytest.approx(-27.5661, rel=1e-3)


def test_dew_point_from_db_enth():
    """Test the accuracy of the dew_point_from_db_enth function."""
    assert dew_point_from_db_enth(30, 64.18544) == pytest.approx(18.43351, rel=1e-2)
    assert dew_point_from_db_enth(20, 38.547332) == pytest.approx(9.2678, rel=1e-2)
    assert dew_point_from_db_enth(-20, 0) == -20
    assert dew_point_from_db_enth(-20, 255.6121, reference_temp=-273.15) == pytest.approx(-27.01307, rel=1e-2)


def test_dew_point_from_db_wb():
    """Test the accuracy of the dew_point_from_db_wb function."""
    assert dew_point_from_db_wb(30, 22.144) == pytest.approx(18.593726, rel=1e-3)
    assert dew_point_from_db_wb(20, 13.88) == pytest.approx(9.35052249, rel=1e-3)
    assert dew_point_from_db_wb(-20, -20.84) == pytest.approx(-29.78065, rel=1e-3)


def test_db_temp_from_enth_hr():
    """Test the accuracy of the db_temp_from_enth_hr function."""
    assert db_temp_from_enth_hr(60, 0.015) == pytest.approx(21.74775, rel=1e-3)
    assert db_temp_from_enth_hr(60, 0.01) == pytest.approx(34.1499, rel=1e-3)
    assert db_temp_from_enth_hr(30, 0.005) == pytest.approx(17.23136, rel=1e-3)


def test_db_temp_from_rh_hr():
    """Test the accuracy of the db_temp_from_rh_hr function."""
    assert db_temp_from_rh_hr(100, 0.3) == pytest.approx(71.365, rel=1e-3)


def test_db_temp_and_hr_from_wb_rh():
    """Test the accuracy of the db_temp_and_hr_from_wb_rh function."""
    t, hr = db_temp_and_hr_from_wb_rh(20, 100)
    assert t == pytest.approx(20.0, rel=1e-3)
    assert hr == pytest.approx(0.01469, rel=1e-3)
    t, hr = db_temp_and_hr_from_wb_rh(20, 0)
    assert t == pytest.approx(53.04558, rel=1e-3)
    assert hr == pytest.approx(0.0, rel=1e-3)


def test_dew_point_from_db_rh_fast():
    """Test the accuracy of the dew_point_from_db_rh_fast function."""
    assert dew_point_from_db_rh_fast(30, 0) == pytest.approx(-273.15, rel=1e-3)
    assert dew_point_from_db_rh_fast(30, 50) == pytest.approx(18.45805, rel=1e-3)
    assert dew_point_from_db_rh_fast(30, 100) == pytest.approx(30, rel=1e-3)
    assert dew_point_from_db_rh_fast(20, 0) == pytest.approx(-273.15, rel=1e-3)
    assert dew_point_from_db_rh_fast(20, 50) == pytest.approx(9.270086, rel=1e-3)
    assert dew_point_from_db_rh_fast(20, 100) == pytest.approx(20, rel=1e-3)
    assert dew_point_from_db_rh_fast(-20, 0) == pytest.approx(-273.15, rel=1e-3)
    assert dew_point_from_db_rh_fast(-20, 50) == pytest.approx(-27.76753, rel=1e-3)
    assert dew_point_from_db_rh_fast(-20, 100) == pytest.approx(-20, rel=1e-3)


def test_wet_bulb_from_db_rh_fast():
    """Test the accuracy of the wet_bulb_from_db_rh_fast function."""
    assert wet_bulb_from_db_rh_fast(30, 0) == pytest.approx(10.871, rel=1e-3)
    assert wet_bulb_from_db_rh_fast(30, 50) == pytest.approx(22.144, rel=1e-3)
    assert wet_bulb_from_db_rh_fast(30, 100) == pytest.approx(29.0, rel=1e-3)
    assert wet_bulb_from_db_rh_fast(20, 0) == pytest.approx(6.07, rel=1e-3)
    assert wet_bulb_from_db_rh_fast(20, 50) == pytest.approx(13.88, rel=1e-3)
    assert wet_bulb_from_db_rh_fast(20, 100) == pytest.approx(20, rel=1e-3)
    assert wet_bulb_from_db_rh_fast(-20, 0) == pytest.approx(-21.69, rel=1e-3)
    assert wet_bulb_from_db_rh_fast(-20, 50) == pytest.approx(-20.84, rel=1e-3)
    assert wet_bulb_from_db_rh_fast(-20, 100) == pytest.approx(-20, rel=1e-3)
