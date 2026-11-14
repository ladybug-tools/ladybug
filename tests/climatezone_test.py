# coding=utf-8
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.climatezone import ashrae_climate_zone
from ladybug.datacollection import HourlyContinuousCollection
from ladybug.datatype.temperature import Temperature
from ladybug.header import Header

import pytest


def _hourly_temperatures(temperature, unit='C', analysis_period=None):
    analysis_period = analysis_period or AnalysisPeriod()
    values = [temperature] * len(analysis_period.datetimes)
    header = Header(Temperature(), unit, analysis_period)
    return HourlyContinuousCollection(header, values)


@pytest.mark.parametrize(('temperature', 'expected_zone'), [
    (35, '1A'),
    (20, '2A'),
    (17, '3A'),
    (12, '4A'),
    (5, '6A'),
    (-1, '7'),
    (-5, '8')
])
def test_ashrae_climate_zone_degree_day_ranges(temperature, expected_zone):
    assert ashrae_climate_zone(_hourly_temperatures(temperature)) == expected_zone


def test_ashrae_climate_zone_dry_and_humid_subzones():
    temperatures = _hourly_temperatures(20)

    assert ashrae_climate_zone(temperatures, annual_precipitation=0) == '2B'
    assert ashrae_climate_zone(temperatures, annual_precipitation=540) == '2A'
    assert ashrae_climate_zone(temperatures, annual_precipitation=600) == '2A'


def test_ashrae_climate_zone_c_subzone_from_monthly_temperatures():
    monthly_temperatures = [4] * 7 + [15] * 5
    values = []
    for month, temperature in enumerate(monthly_temperatures, 1):
        days = AnalysisPeriod.NUMOFDAYSEACHMONTH[month - 1]
        values.extend([temperature] * (days * 24))

    temperatures = HourlyContinuousCollection(
        Header(Temperature(), 'C', AnalysisPeriod()), values)
    assert ashrae_climate_zone(temperatures) == '5C'


def test_ashrae_climate_zone_converts_units_before_classification():
    assert ashrae_climate_zone(_hourly_temperatures(68, 'F')) == '2A'


def test_ashrae_climate_zone_classifies_zone_3c():
    assert ashrae_climate_zone(_hourly_temperatures(15)) == '3C'


def test_ashrae_climate_zone_rejects_non_hourly_continuous_data():
    with pytest.raises(AssertionError, match='HourlyContinuousCollection'):
        ashrae_climate_zone([])


def test_ashrae_climate_zone_requires_annual_hourly_data():
    non_annual = AnalysisPeriod(1, 1, 0, 1, 2, 23)
    with pytest.raises(AssertionError, match='must be annual'):
        ashrae_climate_zone(_hourly_temperatures(20, analysis_period=non_annual))

    subhourly = AnalysisPeriod(timestep=2)
    with pytest.raises(AssertionError, match='timestep of 1'):
        ashrae_climate_zone(_hourly_temperatures(20, analysis_period=subhourly))
