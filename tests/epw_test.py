# coding=utf-8
from ladybug.epw import EPW
from ladybug.datacollection import HourlyContinuousCollection, MonthlyCollection
from ladybug.designday import DesignDay
from ladybug.analysisperiod import AnalysisPeriod

import os
import pytest


def test_import_epw():
    """Test import standard epw."""
    relative_path = './tests/assets/epw/chicago.epw'
    abs_path = os.path.abspath(relative_path)
    epw_rel = EPW(relative_path)
    epw = EPW(abs_path)

    assert epw_rel.file_path == os.path.normpath(relative_path)
    assert epw_rel.location.city == 'Chicago Ohare Intl Ap'
    assert epw.file_path == abs_path
    assert epw.location.city == 'Chicago Ohare Intl Ap'
    # Check that calling location getter only retrieves location
    assert not epw.is_data_loaded
    dbt = epw.dry_bulb_temperature
    skyt = epw.sky_temperature  # test sky temperature calculation
    assert epw.is_data_loaded
    assert len(dbt) == 8760
    assert len(skyt) == 8760
    assert epw.ashrae_climate_zone == '5A'


def test_import_tokyo_epw():
    """Test import standard epw from another location."""
    path = './tests/assets/epw/tokyo.epw'
    epw = EPW(path)
    assert not epw.is_header_loaded
    assert epw.location.city == 'Tokyo'
    assert epw.is_header_loaded
    assert not epw.is_data_loaded
    dbt = epw.dry_bulb_temperature
    assert epw.is_data_loaded
    assert len(dbt) == 8760
    assert epw.ashrae_climate_zone == '3A'


def test_import_non_utf_epw():
    """Test import of an epw with non-UTF characters."""
    path = './tests/assets/epw/mannheim.epw'
    epw = EPW(path)

    dbt = epw.dry_bulb_temperature
    skyt = epw.sky_temperature  # test sky temperature calculation
    assert epw.is_data_loaded
    assert len(dbt) == 8760
    assert len(skyt) == 8760


def test_epw_from_file_string():
    """Test initialization of EPW from a file string."""
    relative_path = './tests/assets/epw/chicago.epw'
    with open(relative_path, 'r') as epwin:
        file_contents = epwin.read()
    epw = EPW.from_file_string(file_contents)
    assert epw.is_header_loaded
    assert epw.is_data_loaded
    assert len(epw.dry_bulb_temperature) == 8760


def test_epw_from_missing_values():
    """Test initialization of EPW from missing values."""
    epw = EPW.from_missing_values()
    assert epw.is_header_loaded
    assert epw.is_data_loaded
    assert len(epw.dry_bulb_temperature) == 8760
    assert list(epw.dry_bulb_temperature.values) == [99.9] * 8760
    day_vals = epw.import_data_by_field(2)
    assert day_vals[24] == 1


def test_dict_methods():
    """Test JSON serialization methods"""
    relative_path = './tests/assets/epw/chicago.epw'
    epw = EPW(relative_path)

    epw_dict = epw.to_dict()
    rebuilt_epw = EPW.from_dict(epw_dict)
    assert epw_dict == rebuilt_epw.to_dict()


def test_file_string_methods():
    """Test serialization to/from EPW file strings"""
    relative_path = './tests/assets/epw/chicago.epw'
    epw = EPW(relative_path)

    epw_contents = epw.to_file_string()
    rebuilt_epw = EPW.from_file_string(epw_contents)
    assert epw.location == rebuilt_epw.location
    assert epw.dry_bulb_temperature == rebuilt_epw.dry_bulb_temperature


def test_invalid_epw():
    """Test the import of incorrect file type and a non-existent epw file."""
    path = './tests/assets/epw/non-existent.epw'
    with pytest.raises(Exception):
        epw = EPW(path)
        epw.location

    path = './tests/assets/stat/chicago.stat'
    with pytest.raises(Exception):
        epw = EPW(path)
        epw.location


def test_import_data():
    """Test the imported data properties."""
    relative_path = './tests/assets/epw/chicago.epw'
    epw = EPW(relative_path)
    assert isinstance(epw.years, HourlyContinuousCollection)
    assert isinstance(epw.dry_bulb_temperature, HourlyContinuousCollection)
    assert isinstance(epw.dew_point_temperature, HourlyContinuousCollection)
    assert isinstance(epw.relative_humidity, HourlyContinuousCollection)
    assert isinstance(epw.atmospheric_station_pressure, HourlyContinuousCollection)
    assert isinstance(epw.extraterrestrial_horizontal_radiation, HourlyContinuousCollection)
    assert isinstance(epw.extraterrestrial_direct_normal_radiation, HourlyContinuousCollection)
    assert isinstance(epw.horizontal_infrared_radiation_intensity, HourlyContinuousCollection)
    assert isinstance(epw.global_horizontal_radiation, HourlyContinuousCollection)
    assert isinstance(epw.direct_normal_radiation, HourlyContinuousCollection)
    assert isinstance(epw.diffuse_horizontal_radiation, HourlyContinuousCollection)
    assert isinstance(epw.global_horizontal_illuminance, HourlyContinuousCollection)
    assert isinstance(epw.direct_normal_illuminance, HourlyContinuousCollection)
    assert isinstance(epw.diffuse_horizontal_illuminance, HourlyContinuousCollection)
    assert isinstance(epw.zenith_luminance, HourlyContinuousCollection)
    assert isinstance(epw.wind_direction, HourlyContinuousCollection)
    assert isinstance(epw.wind_speed, HourlyContinuousCollection)
    assert isinstance(epw.total_sky_cover, HourlyContinuousCollection)
    assert isinstance(epw.opaque_sky_cover, HourlyContinuousCollection)
    assert isinstance(epw.visibility, HourlyContinuousCollection)
    assert isinstance(epw.ceiling_height, HourlyContinuousCollection)
    assert isinstance(epw.present_weather_observation, HourlyContinuousCollection)
    assert isinstance(epw.present_weather_codes, HourlyContinuousCollection)
    assert isinstance(epw.precipitable_water, HourlyContinuousCollection)
    assert isinstance(epw.aerosol_optical_depth, HourlyContinuousCollection)
    assert isinstance(epw.snow_depth, HourlyContinuousCollection)
    assert isinstance(epw.days_since_last_snowfall, HourlyContinuousCollection)
    assert isinstance(epw.albedo, HourlyContinuousCollection)
    assert isinstance(epw.liquid_precipitation_depth, HourlyContinuousCollection)
    assert isinstance(epw.liquid_precipitation_quantity, HourlyContinuousCollection)
    assert isinstance(epw.sky_temperature, HourlyContinuousCollection)


def test_convert_to_ip():
    """Test the method that converts the data to IP units."""
    relative_path = './tests/assets/epw/chicago.epw'
    epw = EPW(relative_path)

    assert epw.dry_bulb_temperature.header.unit == 'C'
    assert epw.dry_bulb_temperature.values[0] == -6.1
    epw.convert_to_ip()
    assert epw.dry_bulb_temperature.header.unit == 'F'
    assert epw.dry_bulb_temperature.values[0] == pytest.approx(21.02, rel=1e-2)
    epw.convert_to_si()
    assert epw.dry_bulb_temperature.header.unit == 'C'
    assert epw.dry_bulb_temperature.values[0] == pytest.approx(-6.1, rel=1e-5)


def test_set_data():
    """Test the ability to set the data of any of the epw hourly data."""
    relative_path = './tests/assets/epw/chicago.epw'
    epw = EPW(relative_path)
    epw.dry_bulb_temperature[12] = 20
    assert epw.dry_bulb_temperature[12] == 20
    epw.dry_bulb_temperature.values = list(range(8760))
    assert epw.dry_bulb_temperature.values == tuple(range(8760))

    # Test if the set data is not annual
    with pytest.raises(Exception):
        epw.dry_bulb_temperature = list(range(365))


def test_import_design_conditions():
    """Test the functions that import design conditions."""
    relative_path = './tests/assets/epw/chicago.epw'
    epw = EPW(relative_path)
    assert isinstance(epw.heating_design_condition_dictionary, dict)
    assert len(epw.heating_design_condition_dictionary.keys()) == 15
    assert isinstance(epw.cooling_design_condition_dictionary, dict)
    assert len(epw.cooling_design_condition_dictionary.keys()) == 32
    assert isinstance(epw.extreme_design_condition_dictionary, dict)
    assert len(epw.extreme_design_condition_dictionary.keys()) == 16


def test_set_design_conditions():
    """Test the functions that set design conditions."""
    relative_path = './tests/assets/epw/chicago.epw'
    epw = EPW(relative_path)

    heat_dict = dict(epw.heating_design_condition_dictionary)
    heat_dict['DB996'] = -25
    epw.heating_design_condition_dictionary = heat_dict
    assert epw.heating_design_condition_dictionary['DB996'] == -25

    # Check for when the dictionary has a missing key
    wrong_dict = dict(heat_dict)
    del wrong_dict['DB996']
    with pytest.raises(Exception):
        epw.heating_design_condition_dictionary = wrong_dict

    # Check for when the wrong type is assigned
    heat_list = list(epw.heating_design_condition_dictionary.keys())
    with pytest.raises(Exception):
        epw.heating_design_condition_dictionary = heat_list

    cool_dict = dict(epw.cooling_design_condition_dictionary)
    cool_dict['DB004'] = 40
    epw.cooling_design_condition_dictionary = cool_dict
    assert epw.cooling_design_condition_dictionary['DB004'] == 40

    extremes_dict = dict(epw.extreme_design_condition_dictionary)
    extremes_dict['WS010'] = 20
    epw.extreme_design_condition_dictionary = extremes_dict
    assert epw.extreme_design_condition_dictionary['WS010'] == 20


def test_import_design_days():
    """Test the functions that import design days."""
    relative_path = './tests/assets/epw/chicago.epw'
    epw = EPW(relative_path)
    assert isinstance(epw.annual_heating_design_day_996, DesignDay)
    assert epw.annual_heating_design_day_996.dry_bulb_condition.dry_bulb_max == -20.0
    assert isinstance(epw.annual_heating_design_day_990, DesignDay)
    assert epw.annual_heating_design_day_990.dry_bulb_condition.dry_bulb_max == -16.6
    assert isinstance(epw.annual_cooling_design_day_004, DesignDay)
    assert epw.annual_cooling_design_day_004.dry_bulb_condition.dry_bulb_max == 33.3
    assert isinstance(epw.annual_cooling_design_day_010, DesignDay)
    assert epw.annual_cooling_design_day_010.dry_bulb_condition.dry_bulb_max == 31.6


def test_import_extreme_weeks():
    """Test the functions that import the extreme weeks."""
    relative_path = './tests/assets/epw/chicago.epw'
    epw = EPW(relative_path)
    ext_cold = list(epw.extreme_cold_weeks.values())[0]
    ext_hot = list(epw.extreme_hot_weeks.values())[0]
    assert isinstance(ext_cold, AnalysisPeriod)
    assert len(ext_cold.doys_int) == 7
    assert (ext_cold.st_month, ext_cold.st_day, ext_cold.end_month,
            ext_cold.end_day) == (1, 27, 2, 2)
    assert isinstance(ext_hot, AnalysisPeriod)
    assert len(ext_hot.doys_int) == 7
    assert (ext_hot.st_month, ext_hot.st_day, ext_hot.end_month,
            ext_hot.end_day) == (7, 13, 7, 19)


def test_import_typical_weeks():
    """Test the functions that import the typical weeks."""
    relative_path = './tests/assets/epw/chicago.epw'
    epw = EPW(relative_path)
    typ_weeks = list(epw.typical_weeks.values())
    assert len(typ_weeks) == 4
    for week in typ_weeks:
        assert isinstance(week, AnalysisPeriod)
        assert len(week.doys_int) == 7


def test_set_extreme_typical_weeks():
    """Test the functions that set the extreme  and typical weeks."""
    relative_path = './tests/assets/epw/chicago.epw'
    epw = EPW(relative_path)
    a_per_cold = AnalysisPeriod(1, 1, 0, 1, 7, 23)
    a_per_hot = AnalysisPeriod(7, 1, 0, 7, 7, 23)
    a_per_typ = AnalysisPeriod(5, 1, 0, 5, 7, 23)
    epw.extreme_cold_weeks = {'Extreme Cold Week': a_per_cold}
    epw.extreme_hot_weeks = {'Extreme Hot Week': a_per_hot}
    epw.typical_weeks = {'Typical Week': a_per_typ}
    assert list(epw.extreme_cold_weeks.values())[0] == a_per_cold
    assert list(epw.extreme_hot_weeks.values())[0] == a_per_hot
    assert list(epw.typical_weeks.values())[0] == a_per_typ

    # Test one someone sets an analysis_period longer than a week.
    a_per_wrong = AnalysisPeriod(1, 1, 0, 1, 6, 23)
    with pytest.raises(Exception):
        epw.extreme_cold_weeks = {'Extreme Cold Week': a_per_wrong}

    # Test when someone sets the wrong type of data
    with pytest.raises(Exception):
        epw.extreme_cold_weeks = a_per_cold


def test_import_ground_temperatures():
    """Test the functions that import ground temperature."""
    relative_path = './tests/assets/epw/chicago.epw'
    epw = EPW(relative_path)
    assert len(epw.monthly_ground_temperature.keys()) == 3
    assert tuple(epw.monthly_ground_temperature.keys()) == (0.5, 2.0, 4.0)
    assert isinstance(epw.monthly_ground_temperature[0.5], MonthlyCollection)
    assert epw.monthly_ground_temperature[0.5].values == \
        (-1.89, -3.06, -0.99, 2.23, 10.68, 17.2,
         21.6, 22.94, 20.66, 15.6, 8.83, 2.56)
    assert epw.monthly_ground_temperature[2].values == \
        (2.39, 0.31, 0.74, 2.45, 8.1, 13.21,
         17.3, 19.5, 19.03, 16.16, 11.5, 6.56)
    assert epw.monthly_ground_temperature[4].values == \
        (5.93, 3.8, 3.34, 3.98, 7.18, 10.62,
         13.78, 15.98, 16.49, 15.25, 12.51, 9.17)


def test_set_ground_temperatures():
    """Test the functions that set ground temperature."""
    relative_path = './tests/assets/epw/chicago.epw'
    epw = EPW(relative_path)
    grnd_dict = dict(epw.monthly_ground_temperature)
    grnd_dict[0.5].values = list(range(12))
    epw.monthly_ground_temperature = grnd_dict
    assert epw.monthly_ground_temperature[0.5].values == tuple(range(12))

    # test when the type is not a monthly collection.
    grnd_dict = dict(epw.monthly_ground_temperature)
    grnd_dict[0.5] = list(range(12))
    with pytest.raises(Exception):
        epw.monthly_ground_temperature = grnd_dict


def test_epw_header():
    """Check that the process of parsing the EPW header hasn't changed it."""
    relative_path = './tests/assets/epw/chicago.epw'
    epw = EPW(relative_path)

    with open(relative_path, 'r') as epwin:
        header_lines = [epwin.readline() for i in range(8)]

    for i in range(len(epw.header)):
        line1, line2 = epw.header[i], header_lines[i]
        if i in (0, 1, 4, 5, 6, 7):
            # These lines should match exactly
            assert line1.rstrip() == line2.rstrip()
        elif i in (2, 3):
            # The order of data in these lines can change and  spaces can get deleted
            assert len(line1.split(',')) == len(line2.split(','))


def test_write_epw():
    """Test save epw_rel."""
    path = './tests/assets/epw/tokyo.epw'
    epw = EPW(path)

    modified_path = './tests/assets/epw/tokyo_modified.epw'
    epw.write(modified_path)
    assert os.path.isfile(modified_path)
    assert os.stat(modified_path).st_size > 1
    os.remove(modified_path)


def test_write_epw_from_missing_values():
    """Test import custom epw with wrong types."""
    epw = EPW.from_missing_values()
    file_path = './tests/assets/epw/missing.epw'
    epw.write(file_path)
    assert os.path.isfile(file_path)
    assert os.stat(file_path).st_size > 1
    os.remove(file_path)


def test_write_converted_epw():
    """Test that the saved EPW always has SI units."""
    relative_path = './tests/assets/epw/chicago.epw'
    epw = EPW(relative_path)
    epw.convert_to_ip()
    modified_path = './tests/assets/epw/chicago_modified.epw'
    epw.write(modified_path)
    assert epw.dry_bulb_temperature.header.unit == 'F'
    assert epw.dry_bulb_temperature.values[0] == pytest.approx(21.02, rel=1e-2)

    new_epw = EPW(modified_path)
    assert new_epw.dry_bulb_temperature.header.unit == 'C'
    assert new_epw.dry_bulb_temperature.values[0] == pytest.approx(-6.1, rel=1e-5)
    os.remove(modified_path)


def test_to_ddy():
    """Test to_ddy."""
    path = './tests/assets/epw/chicago.epw'
    epw = EPW(path)

    ddy_path = './tests/assets/epw/chicago_epw.ddy'
    epw.to_ddy(ddy_path)
    assert os.path.isfile(ddy_path)
    assert os.stat(ddy_path).st_size > 1
    os.remove(ddy_path)

    ddy_path = './tests/assets/epw/chicago_epw_02.ddy'
    epw.to_ddy(ddy_path, 2)
    assert os.path.isfile(ddy_path)
    assert os.stat(ddy_path).st_size > 1
    os.remove(ddy_path)


def test_to_wea():
    """Test to_wea."""
    path = './tests/assets/epw/chicago.epw'
    epw = EPW(path)
    wea_path = './tests/assets/wea/chicago_epw.wea'
    epw.to_wea(wea_path)
    assert os.path.isfile(wea_path)
    assert os.stat(wea_path).st_size > 1

    # check the order of the data in the file
    with open(wea_path) as wea_f:
        line = wea_f.readlines()
        assert float(line[6].split(' ')[-2]) == epw.direct_normal_radiation[0]
        assert float(line[6].split(' ')[-1]) == epw.diffuse_horizontal_radiation[0]
        assert float(line[17].split(' ')[-2]) == epw.direct_normal_radiation[11]
        assert float(line[17].split(' ')[-1]) == epw.diffuse_horizontal_radiation[11]

    os.remove(wea_path)
