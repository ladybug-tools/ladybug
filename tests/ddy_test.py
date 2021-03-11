# coding=utf-8
from pytest import approx
import os
from ladybug.location import Location
from ladybug.dt import Date
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.designday import DesignDay
from ladybug.ddy import DDY


def test_import_ddy():
    """Test import standard ddy."""
    relative_path = './tests/assets/ddy/chicago.ddy'
    abs_path = os.path.abspath(relative_path)

    ddy_rel = DDY.from_ddy_file(relative_path)
    ddy = DDY.from_ddy_file(abs_path)

    # Test imports don't break
    assert ddy.file_path == abs_path
    assert ddy_rel.file_path == os.path.normpath(relative_path)


def test_dict_methods():
    """Test dict methods for the DDY object."""
    relative_path = './tests/assets/ddy/chicago.ddy'
    ddy = DDY.from_ddy_file(relative_path)

    ddy_dict = ddy.to_dict()
    reconstructed_ddy = DDY.from_dict(ddy_dict)
    assert ddy_dict == reconstructed_ddy.to_dict()
    for dday1, dday2 in zip(ddy.design_days, reconstructed_ddy.design_days):
        assert dday1 == dday2


def test_ddy_from_design_day():
    """Test ddy from design day method."""
    relative_path = './tests/assets/ddy/chicago_monthly.ddy'
    ddy = DDY.from_ddy_file(relative_path)
    new_ddy = DDY.from_design_day(ddy.design_days[0])
    assert ddy.location == new_ddy.location
    assert ddy.design_days[0] == new_ddy.design_days[0]


def test_write_ddy():
    """Test write ddy."""
    relative_path = './tests/assets/ddy/chicago.ddy'
    ddy = DDY.from_ddy_file(relative_path)
    new_file_path = './tests/assets/ddy/chicago_edited.ddy'
    ddy.save(new_file_path)


def test_standard_ddy_properties():
    """Test properties of a standard ddy."""
    relative_path = './tests/assets/ddy/tokyo.ddy'

    ddy = DDY.from_ddy_file(relative_path)

    # Test accuracy of import
    assert ddy.location.city == 'TOKYO HYAKURI_JPN Design_Conditions'
    assert ddy.location.latitude == approx(36.18, rel=1e-1)
    assert ddy.location.longitude == approx(140.42, rel=1e-1)
    assert ddy.location.time_zone == 9
    assert ddy.location.elevation == 35

    assert len(ddy.design_days) == 18
    for des_day in ddy.design_days:
        assert isinstance(des_day, DesignDay)
    assert len(ddy.filter_by_keyword('.4%')) == 4
    assert len(ddy.filter_by_keyword('99.6%')) == 3


def test_duplicate():
    """Test duplicate method for the DDY object."""
    relative_path = './tests/assets/ddy/chicago_monthly.ddy'
    ddy = DDY.from_ddy_file(relative_path)
    ddy_dup = ddy.duplicate()

    assert ddy is ddy
    assert ddy is not ddy_dup
    assert ddy == ddy_dup
    ddy_dup[0].dry_bulb_condition.dry_bulb_max = 40
    assert ddy != ddy_dup


def test_duplicate_design_day():
    """Test duplicate method for the DesignDay object."""
    relative_path = './tests/assets/ddy/chicago_monthly.ddy'
    ddy = DDY.from_ddy_file(relative_path)

    des_day = ddy[0]
    des_day_dup = des_day.duplicate()

    assert des_day is des_day
    assert des_day is not des_day_dup
    assert des_day == des_day_dup
    des_day_dup.dry_bulb_condition.dry_bulb_max = 40
    assert des_day != des_day_dup


def test_monthly_ddy_properties():
    """Test properties of a monthly ddy."""
    relative_path = './tests/assets/ddy/chicago_monthly.ddy'
    ddy = DDY.from_ddy_file(relative_path)

    # Test accuracy of import
    assert ddy.location.city == 'Chicago Ohare Intl Ap'
    assert ddy.location.latitude == approx(41.96, rel=1e-1)
    assert ddy.location.longitude == approx(-87.92, rel=1e-1)
    assert ddy.location.time_zone == -6
    assert ddy.location.elevation == 201

    assert len(ddy.design_days) == 12
    for des_day in ddy.design_days:
        assert isinstance(des_day, DesignDay)
        assert des_day.day_type == 'SummerDesignDay'


def test_design_day_from_properties():
    """Test hourly data properties of a standard ddy."""
    location = Location('Test City', '-', 'USA', 34.20, -118.35, -8, 226)
    a_period = AnalysisPeriod(12, 21, 0, 12, 21, 23)
    date = Date(12, 21)
    des_day = DesignDay.from_design_day_properties(
        'Test Day', 'WinterDesignDay', location, date, 3.9, 0,
        'Wetbulb', 3.9, 98639, 0.8, 330, 'ASHRAEClearSky', [0])
    assert des_day.location == location
    new_period = des_day.analysis_period
    assert new_period.st_month == a_period.st_month
    assert new_period.st_day == a_period.st_day
    assert new_period.st_hour == a_period.st_hour
    assert new_period.end_month == a_period.end_month
    assert new_period.end_day == a_period.end_day
    assert new_period.end_hour == a_period.end_hour


def test_design_day_hourly_data():
    """Test hourly data properties of a standard ddy."""
    location = Location('Test City', '-', 'USA', 34.20, -118.35, -8, 226)
    date = Date(8, 21)
    des_day = DesignDay.from_design_day_properties(
        'Test Day', 'SummerDesignDay', location, date, 36.8, 13.2,
        'Wetbulb', 20.5, 98639, 3.9, 170, 'ASHRAETau', [0.436, 2.106])
    # dry bulb values
    db_data_collect = des_day.hourly_dry_bulb
    assert db_data_collect[5] == approx(23.6, rel=1e-1)
    assert db_data_collect[14] == approx(36.8, rel=1e-1)

    # dew point values
    dpt_data_collect = des_day.hourly_dew_point
    assert dpt_data_collect[0] == approx(11.296, rel=1e-1)
    assert dpt_data_collect[-1] == approx(11.296, rel=1e-1)

    # relative humidity values
    rh_data_collect = des_day.hourly_relative_humidity
    assert rh_data_collect[5] == approx(45.896, rel=1e-1)
    assert rh_data_collect[14] == approx(21.508, rel=1e-1)

    # barometric pressure values
    bp_data_collect = des_day.hourly_barometric_pressure
    assert bp_data_collect[0] == approx(98639, rel=1e-1)
    assert bp_data_collect[-1] == approx(98639, rel=1e-1)

    # wind speed values
    ws_data_collect = des_day.hourly_wind_speed
    assert -0.1 < ws_data_collect[0] - 3.9 < 0.1
    assert -0.1 < ws_data_collect[-1] - 3.9 < 0.1

    # wind direction values
    wd_data_collect = des_day.hourly_wind_direction
    assert wd_data_collect[0] == approx(170, rel=1e-1)
    assert wd_data_collect[-1] == approx(170, rel=1e-1)

    # radiation values
    direct_normal_rad, diffuse_horizontal_rad, global_horizontal_rad = \
        des_day.hourly_solar_radiation
    assert direct_normal_rad[0] == 0
    assert direct_normal_rad[11] == approx(891.46, rel=1e-1)
    assert diffuse_horizontal_rad[0] == 0
    assert diffuse_horizontal_rad[11] == approx(165.32, rel=1e-1)
    assert global_horizontal_rad[0] == 0
    assert global_horizontal_rad[11] == approx(985.05, rel=1e-1)

    # sky cover values
    sc_data_collect = des_day.hourly_sky_cover

    # sky cover values
    hi_data_collect = des_day.hourly_horizontal_infrared
