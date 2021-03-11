# coding=utf-8
from ladybug.sql import SQLiteResult, ZoneSize, ComponentSize

from ladybug.datatype.energy import Energy
from ladybug.datatype.temperature import Temperature
from ladybug.dt import DateTime
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.location import Location
from ladybug.datacollection import HourlyContinuousCollection, DailyCollection, \
    MonthlyCollection


def test_sqlite_init():
    """Test the initialization of SQLiteResult and basic properties."""
    sql_path = './tests/assets/sql/eplusout_hourly.sql'
    sql_obj = SQLiteResult(sql_path)
    str(sql_obj)  # test the string representation

    assert sql_obj.reporting_frequency == 'Hourly'
    assert isinstance(sql_obj.file_path, str)
    assert isinstance(sql_obj.location, Location)
    assert sql_obj.location.latitude == 42.37

    all_output = sql_obj.available_outputs
    assert len(all_output) == 8
    assert 'Zone Operative Temperature' in all_output
    assert 'Zone Lights Electric Energy' in all_output
    assert 'Zone Electric Equipment Electric Energy' in all_output
    assert 'Zone Air Relative Humidity' in all_output
    assert 'Zone Ideal Loads Supply Air Total Cooling Energy' in all_output
    assert 'Zone Mean Radiant Temperature' in all_output
    assert 'Zone Ideal Loads Supply Air Total Heating Energy' in all_output


def test_available_results_info():
    """Test the available_results_info property."""
    sql_path = './tests/assets/sql/eplusout_hourly.sql'
    sql_obj = SQLiteResult(sql_path)

    assert len(sql_obj.available_outputs_info) == 8
    assert all(isinstance(obj, dict) for obj in sql_obj.available_outputs_info)
    for outp in sql_obj.available_outputs_info:
        if outp['output_name'] == 'Zone Mean Radiant Temperature':
            assert outp['object_type'] == 'Zone'
            assert outp['units'] == 'C'
            assert str(outp['data_type']) == 'Temperature'


def test_sqlite_run_period():
    """Test the run_period property of SQLiteResult."""
    sql_path = './tests/assets/sql/eplusout_hourly.sql'
    sql_obj = SQLiteResult(sql_path)

    assert len(sql_obj.run_periods) == 1
    assert isinstance(sql_obj.run_periods[0], AnalysisPeriod)
    assert sql_obj.run_periods[0].st_month == 1
    assert sql_obj.run_periods[0].st_day == 6
    assert sql_obj.run_periods[0].end_month == 1
    assert sql_obj.run_periods[0].end_day == 12
    assert len(sql_obj.run_period_names) == 1
    assert sql_obj.run_period_names[0] == 'CUSTOMRUNPERIOD'

    sql_path = './tests/assets/sql/eplusout_design_days.sql'
    sql_obj = SQLiteResult(sql_path)
    assert len(sql_obj.run_periods) == 7
    assert len(sql_obj.run_period_names) == 7
    assert len(sql_obj.run_period_indices) == 7
    assert 'BOSTON LOGAN INTL ARPT ANN' in sql_obj.run_period_names[0]


def test_sqlite_zone_sizing():
    """Test the properties and methods related to zone sizes."""
    sql_path = './tests/assets/sql/eplusout_hourly.sql'
    sql_obj = SQLiteResult(sql_path)

    cool_sizes = sql_obj.zone_cooling_sizes
    heat_sizes = sql_obj.zone_heating_sizes

    assert len(cool_sizes) == 7
    assert len(heat_sizes) == 7

    for size_obj in cool_sizes:
        assert isinstance(size_obj, ZoneSize)
        assert isinstance(size_obj.zone_name, str)
        assert size_obj.load_type == 'Cooling'
        assert isinstance(size_obj.calculated_design_load, float)
        assert isinstance(size_obj.final_design_load, float)
        assert isinstance(size_obj.calculated_design_flow, float)
        assert isinstance(size_obj.final_design_flow, float)
        assert size_obj.design_day_name == 'BOSTON LOGAN INTL ARPT ANN CLG .4% CONDNS DB=>MWB'
        assert isinstance(size_obj.peak_date_time, DateTime)
        assert isinstance(size_obj.peak_temperature, float)
        assert isinstance(size_obj.peak_humidity_ratio, float)
        assert isinstance(size_obj.peak_outdoor_air_flow, float)
        size_dict = size_obj.to_dict()
        new_size = ZoneSize.from_dict(size_dict)
        assert new_size.to_dict() == size_dict

    for size_obj in heat_sizes:
        assert size_obj.load_type == 'Heating'
        assert size_obj.design_day_name == 'BOSTON LOGAN INTL ARPT ANN HTG 99.6% CONDNS DB'


def test_sqlite_component_sizing():
    """Test the properties and methods related to component sizes."""
    sql_path = './tests/assets/sql/eplusout_hourly.sql'
    sql_obj = SQLiteResult(sql_path)

    comp_sizes = sql_obj.component_sizes
    comp_size_type = sql_obj.component_sizes_by_type('ZoneHVAC:IdealLoadsAirSystem')
    comp_types = sql_obj.component_types

    assert len(comp_sizes) == 7
    assert len(comp_size_type) == 7
    assert comp_types == ['ZoneHVAC:IdealLoadsAirSystem']

    for size_obj in comp_sizes:
        assert isinstance(size_obj, ComponentSize)
        assert size_obj.component_type == 'ZoneHVAC:IdealLoadsAirSystem'
        assert isinstance(size_obj.component_name, str)
        assert all(isinstance(desc, str) for desc in size_obj.descriptions)
        assert all(isinstance(prop, str) for prop in size_obj.properties)
        assert all(isinstance(val, float) for val in size_obj.values)
        assert all(isinstance(unit, str) for unit in size_obj.units)
        assert isinstance(size_obj.properties_dict, dict)
        assert len(size_obj.properties_dict) == 4
        size_dict = size_obj.to_dict()
        new_size = ComponentSize.from_dict(size_dict)
        assert new_size.to_dict() == size_dict


def test_sqlite_sizing_odd():
    """Test the properties and methods related to zone sizes with an odd SQL file."""
    sql_path = './tests/assets/sql/eplusout_odd_zonesize.sql'
    sql_obj = SQLiteResult(sql_path)

    cool_sizes = sql_obj.zone_cooling_sizes
    heat_sizes = sql_obj.zone_heating_sizes
    assert len(cool_sizes) == 2
    assert len(heat_sizes) == 2

    comp_sizes = sql_obj.component_sizes
    comp_size_type = sql_obj.component_sizes_by_type('ZoneHVAC:IdealLoadsAirSystem')
    comp_types = sql_obj.component_types

    assert len(comp_sizes) == 2
    assert len(comp_size_type) == 2
    assert comp_types == ['ZoneHVAC:IdealLoadsAirSystem']


def test_sqlite_data_collections_by_output_name():
    """Test the data_collections_by_output_name method."""
    sql_path = './tests/assets/sql/eplusout_hourly.sql'
    sql_obj = SQLiteResult(sql_path)

    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Lights Electric Energy')
    assert len(data_colls) == 7
    for coll in data_colls:
        assert isinstance(coll, HourlyContinuousCollection)
        assert len(coll) == len(coll.header.analysis_period.hoys)
        assert isinstance(coll.header.data_type, Energy)
        assert coll.header.unit == 'kWh'

    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Mean Radiant Temperature')
    for coll in data_colls:
        assert isinstance(coll, HourlyContinuousCollection)
        assert len(coll) == len(coll.header.analysis_period.hoys)
        assert isinstance(coll.header.data_type, Temperature)
        assert coll.header.unit == 'C'

    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Electric Equipment Electric Energy')
    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Mean Air Temperature')
    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Air Relative Humidity')
    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Ideal Loads Supply Air Total Heating Energy')
    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Ideal Loads Supply Air Total Cooling Energy')


def test_sqlite_data_collections_by_output_name_single():
    """Test the data_collections_by_output_name method with a single data."""
    sql_path = './tests/assets/sql/eplusout_openstudio_error.sql'
    sql_obj = SQLiteResult(sql_path)

    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Lights Electric Energy')
    assert len(data_colls) == 1
    for coll in data_colls:
        assert isinstance(coll, HourlyContinuousCollection)
        assert len(coll) == len(coll.header.analysis_period.hoys)
        assert isinstance(coll.header.data_type, Energy)
        assert coll.header.unit == 'kWh'


def test_sqlite_data_collections_by_output_names():
    """Test the data_collections_by_output_name method with multiple names."""
    sql_path = './tests/assets/sql/eplusout_hourly.sql'
    sql_obj = SQLiteResult(sql_path)

    data_colls = sql_obj.data_collections_by_output_name(
        ('Zone Lights Electric Energy', 'Zone Mean Radiant Temperature'))
    assert len(data_colls) == 14
    for coll in data_colls:
        assert isinstance(coll, HourlyContinuousCollection)
        assert len(coll) == len(coll.header.analysis_period.hoys)
        assert isinstance(coll.header.data_type, (Energy, Temperature))

    data_colls = sql_obj.data_collections_by_output_name(
        ('Zone Lights Electric Energy',))
    assert len(data_colls) == 7


def test_sqlite_data_collections_by_output_name_openstudio():
    """Test the data_collections_by_output_name method with openstudio values."""
    sql_path = './tests/assets/sql/eplusout_openstudio.sql'
    sql_obj = SQLiteResult(sql_path)

    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Lights Electric Energy')
    for coll in data_colls:
        assert isinstance(coll, HourlyContinuousCollection)
        assert len(coll) == len(coll.header.analysis_period.hoys)
        assert isinstance(coll.header.data_type, Energy)
        assert coll.header.unit == 'kWh'

    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Electric Equipment Electric Energy')
    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Ideal Loads Supply Air Total Heating Energy')
    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Ideal Loads Supply Air Total Cooling Energy')


def test_sqlite_data_collections_by_output_name_timestep():
    """Test the data_collections_by_output_name method with timestep values."""
    sql_path = './tests/assets/sql/eplusout_timestep.sql'
    sql_obj = SQLiteResult(sql_path)

    assert sql_obj.reporting_frequency == 6
    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Lights Electric Energy')
    for coll in data_colls:
        assert isinstance(coll, HourlyContinuousCollection)
        assert len(coll) == 7 * 24 * 6


def test_sqlite_data_collections_by_output_name_daily():
    """Test the data_collections_by_output_name method with daily values."""
    sql_path = './tests/assets/sql/eplusout_daily.sql'
    sql_obj = SQLiteResult(sql_path)

    assert sql_obj.reporting_frequency == 'Daily'
    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Lights Electric Energy')
    for coll in data_colls:
        assert isinstance(coll, DailyCollection)
        assert coll.header.analysis_period.is_annual
        assert len(coll) == 365


def test_sqlite_data_collections_by_output_name_monthly():
    """Test the data_collections_by_output_name method with monthly values."""
    sql_path = './tests/assets/sql/eplusout_monthly.sql'
    sql_obj = SQLiteResult(sql_path)

    assert sql_obj.reporting_frequency == 'Monthly'
    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Lights Electric Energy')
    for coll in data_colls:
        assert isinstance(coll, MonthlyCollection)
        assert coll.header.analysis_period.is_annual
        assert len(coll) == 12


def test_sqlite_data_collections_by_output_name_design_day():
    """Test the data_collections_by_output_name method with several design day results."""
    sql_path = './tests/assets/sql/eplusout_design_days.sql'
    sql_obj = SQLiteResult(sql_path)

    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Lights Electric Energy')
    assert len(data_colls) == 49
    for coll in data_colls:
        assert isinstance(coll, HourlyContinuousCollection)
        assert len(coll) == 24


def test_sqlite_data_collections_by_output_name_dday_runperiod():
    """Test the data_collections_by_output_name method with several design day results."""
    sql_path = './tests/assets/sql/eplusout_dday_runper.sql'
    sql_obj = SQLiteResult(sql_path)

    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Lights Electric Energy')
    assert len(data_colls) == 56
    for coll in data_colls[:49]:
        assert isinstance(coll, HourlyContinuousCollection)
        assert len(coll) == 24
    for coll in data_colls[49:]:
        assert isinstance(coll, HourlyContinuousCollection)
        assert len(coll) == 744


def test_sqlite_tabular_data():
    """Test the tabular_data_by_name method."""
    sql_path = './tests/assets/sql/eplusout_monthly.sql'
    sql_obj = SQLiteResult(sql_path)

    data = sql_obj.tabular_data_by_name('Utility Use Per Conditioned Floor Area')
    assert len(data) == 4
    assert len(data['Lighting']) == 6
    col_names = sql_obj.tabular_column_names('Utility Use Per Conditioned Floor Area')
    assert len(col_names) == 6
    assert 'Electricity Intensity' in col_names[0]
