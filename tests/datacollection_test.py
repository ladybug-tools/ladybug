# coding=utf-8
from __future__ import division

from ladybug._datacollectionbase import BaseCollection
from ladybug.datacollection import HourlyDiscontinuousCollection, \
    HourlyContinuousCollection, MonthlyCollection, DailyCollection, \
    MonthlyPerHourCollection
from ladybug.header import Header
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.dt import DateTime
from ladybug.datatype.generic import GenericType
from ladybug.datatype.temperature import Temperature
from ladybug.datatype.fraction import RelativeHumidity, HumidityRatio
from ladybug.datatype.energy import Energy
from ladybug.datatype.energyintensity import EnergyIntensity
from ladybug.datatype.power import Power
from ladybug.datatype.speed import Speed
from ladybug.datatype.distance import Distance

from ladybug.epw import EPW
from ladybug.psychrometrics import humid_ratio_from_db_rh

import pytest
import sys
if (sys.version_info >= (3, 0)):
    xrange = range

linspace, arange, histogram, histogram_circular = \
    BaseCollection.linspace, BaseCollection.arange, BaseCollection.histogram, \
    BaseCollection.histogram_circular


def test_init():
    """Test the init methods for base collections."""
    a_per = AnalysisPeriod(6, 21, 12, 6, 21, 13)
    dt1, dt2 = DateTime(6, 21, 12), DateTime(6, 21, 13)
    v1, v2 = 20, 25
    avg = (v1 + v2) / 2
    # Setup data collection
    dc1 = BaseCollection(Header(Temperature(), 'C', a_per), [v1, v2], [dt1, dt2])

    assert dc1.datetimes == (dt1, dt2)
    assert dc1.values == (v1, v2)
    assert dc1.average == avg
    str(dc1)  # Test the string representation of the collection
    str(dc1.header)  # Test the string representation of the header
    hash(dc1)

    dc1.header.metadata = {'type': 'Room Air Temperature'}


def test_init_incorrect():
    """Test the init methods for base collections with incorrect inputs."""
    a_per = AnalysisPeriod(6, 21, 12, 6, 21, 13)
    dt1, dt2 = DateTime(6, 21, 12), DateTime(6, 21, 13)
    v1, v2 = 20, 25
    avg = (v1 + v2) / 2

    dc1 = BaseCollection(Header(Temperature(), 'C', a_per), [v1, v2], [dt1, dt2])
    dc1 = BaseCollection(Header(Temperature(), 'C', a_per), [v1, v2], (dt1, dt2))
    dc1 = BaseCollection(Header(Temperature(), 'C', a_per), [v1, v2], xrange(2))
    assert dc1.average == avg
    with pytest.raises(Exception):
        dc1 = BaseCollection(Header(Temperature(), 'C', a_per), [v1, v2], 'te')

    with pytest.raises(Exception):
        dc1 = BaseCollection(Header(Temperature(), 'C', a_per),
                             [v1, v2], {'1': 1, '2': 2})


def test_init_hourly():
    """Test the init methods for discontinuous collections."""
    a_per = AnalysisPeriod(6, 21, 12, 6, 21, 13)
    dt1, dt2 = DateTime(6, 21, 12), DateTime(6, 21, 13)
    v1, v2 = 20, 25
    avg = (v1 + v2) / 2
    # Setup data collection
    dc1 = HourlyDiscontinuousCollection(Header(Temperature(), 'C', a_per),
                                        [v1, v2], [dt1, dt2])

    assert dc1.datetimes == (dt1, dt2)
    assert dc1.values == (v1, v2)
    assert dc1.average == avg
    assert not dc1.is_continuous
    str(dc1)  # Test the string representation of the collection
    str(dc1.header)  # Test the string representation of the header


def test_init_daily():
    """Test the init methods for daily collections."""
    a_per = AnalysisPeriod(6, 21, 0, 6, 22, 23)
    v1, v2 = 20, 25
    avg = (v1 + v2) / 2
    # Setup data collection
    dc1 = DailyCollection(Header(Temperature(), 'C', a_per),
                          [v1, v2], a_per.doys_int)

    assert dc1.datetimes == tuple(a_per.doys_int)
    assert dc1.values == (v1, v2)
    assert dc1.average == avg
    assert not dc1.is_continuous
    str(dc1)  # Test the string representation of the collection
    str(dc1.header)  # Test the string representation of the header


def test_init_monthly():
    """Test the init methods for monthly collections."""
    a_per = AnalysisPeriod(6, 1, 0, 7, 31, 23)
    v1, v2 = 20, 25
    avg = (v1 + v2) / 2
    # Setup data collection
    dc1 = MonthlyCollection(Header(Temperature(), 'C', a_per),
                            [v1, v2], a_per.months_int)

    assert dc1.datetimes == tuple(a_per.months_int)
    assert dc1.values == (v1, v2)
    assert dc1.average == avg
    assert not dc1.is_continuous
    str(dc1)  # Test the string representation of the collection
    str(dc1.header)  # Test the string representation of the header


def test_init_monthly_per_hour():
    """Test the init methods for monthly per hour collections."""
    a_per = AnalysisPeriod(6, 1, 0, 7, 31, 23)
    vals = [20] * 24 + [25] * 24
    avg = sum(vals) / 48
    # Setup data collection
    dc1 = MonthlyPerHourCollection(Header(Temperature(), 'C', a_per),
                                   vals, a_per.months_per_hour)

    assert dc1.datetimes == tuple(a_per.months_per_hour)
    assert dc1.values == tuple(vals)
    assert dc1.average == avg
    assert not dc1.is_continuous
    str(dc1)  # Test the string representation of the collection
    str(dc1.header)  # Test the string representation of the header


def test_init_continuous():
    """Test the init methods for continuous collections"""
    # Setup temperature data collection
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(xrange(8760))
    dc1 = HourlyContinuousCollection(header, values)

    assert len(dc1.datetimes) == 8760
    assert list(dc1.values) == list(xrange(8760))
    assert dc1.average == 4379.5
    assert dc1.is_continuous
    str(dc1)  # Test the string representation of the collection
    str(dc1.header)  # Test the string representation of the header
    hash(dc1)


def test_init_continuous_incorrect():
    """Test the init methods for continuous collections with incorrect values"""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(xrange(10))
    with pytest.raises(Exception):
        HourlyContinuousCollection(header, values)


def test_operators_hourly_discontinuous():
    """Test the operators for discontinuous collections."""
    a_per = AnalysisPeriod(6, 21, 12, 6, 21, 13)
    dt1, dt2 = DateTime(6, 21, 12), DateTime(6, 21, 13)
    v1, v2 = 20, 25
    dc1 = HourlyDiscontinuousCollection(Header(Temperature(), 'C', a_per),
                                        [v1, v2], [dt1, dt2])
    dc2 = HourlyDiscontinuousCollection(Header(Temperature(), 'C', a_per),
                                        [v2, v1], [dt1, dt2])

    add = dc1 + dc2
    assert isinstance(add, HourlyDiscontinuousCollection)
    assert add.values == (v1 + v2, v2 + v1)

    sub = dc1 - dc2
    assert isinstance(sub, HourlyDiscontinuousCollection)
    assert sub.values == (v1 - v2, v2 - v1)

    mul = dc1 * dc2
    assert isinstance(mul, HourlyDiscontinuousCollection)
    assert mul.values == (v1 * v2, v2 * v1)

    div = dc1 / dc2
    assert isinstance(div, HourlyDiscontinuousCollection)
    assert div.values == (v1 / v2, v2 / v1)

    add = dc1 + 2
    assert isinstance(add, HourlyDiscontinuousCollection)
    assert add.values == (v1 + 2, v2 + 2)

    sub = dc1 - 2
    assert isinstance(sub, HourlyDiscontinuousCollection)
    assert sub.values == (v1 - 2, v2 - 2)

    mul = dc1 * 2
    assert isinstance(mul, HourlyDiscontinuousCollection)
    assert mul.values == (v1 * 2, v2 * 2)

    div = dc1 / 2
    assert isinstance(div, HourlyDiscontinuousCollection)
    assert div.values == (v1 / 2, v2 / 2)

    neg = -dc1
    assert isinstance(neg, HourlyDiscontinuousCollection)
    assert neg.values == (-v1, -v2)


def test_operators_hourly_continuous():
    """Test the operators for discontinuous collections."""
    v1 = 20
    vals = [v1] * 24
    a_per = AnalysisPeriod(6, 21, 0, 6, 21, 23)
    # Setup data collection
    dc1 = HourlyContinuousCollection(Header(Temperature(), 'C', a_per), vals)
    dc2 = HourlyContinuousCollection(Header(Temperature(), 'C', a_per), vals)

    add = dc1 + dc2
    assert isinstance(add, HourlyContinuousCollection)
    assert add[0] == v1 + v1

    sub = dc1 - dc2
    assert isinstance(sub, HourlyContinuousCollection)
    assert sub[0] == v1 - v1

    mul = dc1 * dc2
    assert isinstance(mul, HourlyContinuousCollection)
    assert mul[0] == v1 * v1

    div = dc1 / dc2
    assert isinstance(div, HourlyContinuousCollection)
    assert div[0] == v1 / v1

    add = dc1 + 2
    assert isinstance(add, HourlyContinuousCollection)
    assert add[0] == v1 + 2

    sub = dc1 - 2
    assert isinstance(sub, HourlyContinuousCollection)
    assert sub[0] == v1 - 2

    mul = dc1 * 2
    assert isinstance(mul, HourlyContinuousCollection)
    assert mul[0] == v1 * 2

    div = dc1 / 2
    assert isinstance(div, HourlyContinuousCollection)
    assert div[0] == v1 / 2

    neg = -dc1
    assert isinstance(neg, HourlyContinuousCollection)
    assert neg[0] == -v1


def test_setting_values():
    """Test the methods for setting values on the data collection"""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(xrange(8760))
    dc = HourlyDiscontinuousCollection(header, values,
                                       header.analysis_period.datetimes)
    # test the contains and reversed methods
    assert 10 in dc
    assert list(reversed(dc)) == list(reversed(values))

    # test setting individual values
    assert dc[0] == 0
    dc[0] = 10
    assert dc[0] == 10

    # try setting the whole list of values
    val_rev = list(reversed(values))
    dc.values = val_rev
    assert dc[0] == 8759

    # make sure that people can't change the values without changing datetimes
    with pytest.raises(Exception):
        dc.values.append(10)


def test_setting_values_continuous():
    """Test the methods for setting values on the continuous data collection"""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(xrange(8760))
    dc = HourlyContinuousCollection(header, values)

    # try setting the whole list of values
    assert dc[0] == 0
    val_rev = list(reversed(values))
    dc.values = val_rev
    assert dc[0] == 8759

    # make sure that people can't change the number of values
    with pytest.raises(Exception):
        dc.values.append(10)


def test_validate_a_period_hourly():
    """Test the validate_analysis_period method for discontinuous collections."""
    a_per = AnalysisPeriod(6, 21, 0, 6, 21, 23)
    dt1, dt2 = DateTime(6, 21, 12), DateTime(6, 21, 13)
    v1, v2 = 20, 25

    # Test that the validate method correctly sorts reversed datetimes.
    dc1 = HourlyDiscontinuousCollection(Header(Temperature(), 'C', a_per),
                                        [v1, v2], [dt2, dt1])
    dc1_new = dc1.validate_analysis_period()
    assert not dc1.validated_a_period
    assert dc1_new.validated_a_period
    assert dc1.datetimes == (dt2, dt1)
    assert dc1_new.datetimes == (dt1, dt2)

    # Test that the validate method correctly updates analysis_period range.
    a_per_2 = AnalysisPeriod(6, 20, 15, 6, 20, 23)
    dc1 = HourlyDiscontinuousCollection(Header(Temperature(), 'C', a_per_2),
                                        [v1, v2], [dt1, dt2])
    dc1_new = dc1.validate_analysis_period()
    assert not dc1.validated_a_period
    assert dc1_new.validated_a_period
    assert dc1.header.analysis_period == a_per_2
    assert dc1_new.header.analysis_period == AnalysisPeriod(
        6, 20, 12, 6, 21, 23)

    # Test that the validate method with reversed analysis_periods.
    a_per_3 = AnalysisPeriod(6, 20, 15, 2, 20, 23)
    dt5 = DateTime(1, 21, 12)
    dc1 = HourlyDiscontinuousCollection(Header(Temperature(), 'C', a_per_3),
                                        [v1, v2, v2], [dt1, dt2, dt5])
    dc1_new = dc1.validate_analysis_period()
    assert dc1_new.header.analysis_period == AnalysisPeriod(
        6, 20, 12, 2, 20, 23)
    dc1 = HourlyDiscontinuousCollection(Header(Temperature(), 'C', a_per_3),
                                        [v1, v2], [dt1, dt2])
    dc1_new = dc1.validate_analysis_period()
    assert dc1_new.header.analysis_period == AnalysisPeriod(
        6, 20, 12, 2, 20, 23)
    dc1 = HourlyDiscontinuousCollection(Header(Temperature(), 'C', a_per_3),
                                        [v1, v2], [dt5, DateTime(1, 21, 15)])
    dc1_new = dc1.validate_analysis_period()
    assert dc1_new.header.analysis_period == AnalysisPeriod(
        6, 20, 12, 2, 20, 23)

    # Test that the validate method correctly updates timestep.
    dt3 = DateTime(6, 21, 12, 30)
    dc1 = HourlyDiscontinuousCollection(Header(Temperature(), 'C', a_per),
                                        [v1, v2, v2], [dt1, dt3, dt2])
    dc1_new = dc1.validate_analysis_period()
    assert not dc1.validated_a_period
    assert dc1_new.validated_a_period
    assert dc1.header.analysis_period.timestep == 1
    assert dc1_new.header.analysis_period.timestep == 2

    # Test that the validate method correctly identifies leap years.
    dt4 = DateTime(2, 29, 12, leap_year=True)
    dc1 = HourlyDiscontinuousCollection(Header(Temperature(), 'C', a_per),
                                        [v1, v2, v2], [dt1, dt4, dt2])
    dc1_new = dc1.validate_analysis_period()
    assert not dc1.validated_a_period
    assert dc1_new.validated_a_period
    assert not dc1.header.analysis_period.is_leap_year
    assert dc1_new.header.analysis_period.is_leap_year

    # Test that duplicated datetimes are caught
    dc1 = HourlyDiscontinuousCollection(Header(Temperature(), 'C', a_per),
                                        [v1, v2], [dt1, dt1])
    with pytest.raises(Exception):
        dc1_new = dc1.validate_analysis_period()


def test_validate_a_period_daily():
    """Test the validate_a_period methods for daily collections."""
    a_per = AnalysisPeriod(6, 21, 0, 6, 22, 23)
    v1, v2 = 20, 25
    dt1, dt2 = 172, 173

    # Test that the validate method correctly sorts reversed datetimes.
    dc1 = DailyCollection(Header(Temperature(), 'C', a_per),
                          [v1, v2], [dt2, dt1])
    dc1_new = dc1.validate_analysis_period()
    assert not dc1.validated_a_period
    assert dc1_new.validated_a_period
    assert dc1.datetimes == (dt2, dt1)
    assert dc1_new.datetimes == (dt1, dt2)

    # Test that the validate method correctly updates analysis_period range.
    a_per_2 = AnalysisPeriod(6, 20, 0, 6, 20, 23)
    dc1 = DailyCollection(Header(Temperature(), 'C', a_per_2),
                          [v1, v2], [dt1, dt2])
    dc1_new = dc1.validate_analysis_period()
    assert not dc1.validated_a_period
    assert dc1_new.validated_a_period
    assert dc1.header.analysis_period == a_per_2
    assert dc1_new.header.analysis_period == AnalysisPeriod(
        6, 20, 0, 6, 22, 23)

    # Test that the validate method with reversed analysis_periods.
    a_per_3 = AnalysisPeriod(6, 20, 0, 2, 20, 23)
    dt5 = 21
    dc1 = DailyCollection(Header(Temperature(), 'C', a_per_3),
                          [v1, v2, v2], [dt1, dt2, dt5])
    dc1_new = dc1.validate_analysis_period()
    assert dc1_new.header.analysis_period == a_per_3
    dc1 = DailyCollection(Header(Temperature(), 'C', a_per_3),
                          [v1, v2], [dt1, dt2])
    dc1_new = dc1.validate_analysis_period()
    assert dc1_new.header.analysis_period == a_per_3
    dc1 = DailyCollection(Header(Temperature(), 'C', a_per_3),
                          [v1, v2], [dt5, 22])
    dc1_new = dc1.validate_analysis_period()
    assert dc1_new.header.analysis_period == a_per_3
    dc1 = DailyCollection(Header(Temperature(), 'C', a_per_3),
                          [v1, v2], [dt5, 60])
    dc1_new = dc1.validate_analysis_period()
    assert dc1_new.header.analysis_period == AnalysisPeriod()

    # Test that the validate method correctly identifies leap years.
    dc1 = DailyCollection(Header(Temperature(), 'C', a_per),
                          [v1, v2, v2], [dt1, dt2, 366])
    dc1_new = dc1.validate_analysis_period()
    assert not dc1.validated_a_period
    assert dc1_new.validated_a_period
    assert not dc1.header.analysis_period.is_leap_year
    assert dc1_new.header.analysis_period.is_leap_year

    # Test that duplicated datetimes are caught
    dc1 = DailyCollection(Header(Temperature(), 'C', a_per),
                          [v1, v2], [dt1, dt1])
    with pytest.raises(Exception):
        dc1_new = dc1.validate_analysis_period()


def test_validate_a_period_monthly():
    """Test the validate_a_period methods for monthly collections."""
    a_per = AnalysisPeriod(6, 1, 0, 7, 1, 23)
    v1, v2 = 20, 25
    dt1, dt2 = 6, 7

    # Test that the validate method correctly sorts reversed datetimes.
    dc1 = MonthlyCollection(Header(Temperature(), 'C', a_per),
                            [v1, v2], [dt2, dt1])
    dc1_new = dc1.validate_analysis_period()
    assert not dc1.validated_a_period
    assert dc1_new.validated_a_period
    assert dc1.datetimes == (dt2, dt1)
    assert dc1_new.datetimes == (dt1, dt2)

    # Test that the validate method correctly updates analysis_period range.
    a_per_2 = AnalysisPeriod(6, 1, 0, 6, 1, 23)
    dc1 = MonthlyCollection(Header(Temperature(), 'C', a_per_2),
                            [v1, v2], [dt1, dt2])
    dc1_new = dc1.validate_analysis_period()
    assert not dc1.validated_a_period
    assert dc1_new.validated_a_period
    assert dc1.header.analysis_period == a_per_2
    assert dc1_new.header.analysis_period == AnalysisPeriod(
        6, 1, 0, 7, 31, 23)

    # Test that the validate method with reversed analysis_periods.
    a_per_3 = AnalysisPeriod(6, 1, 0, 2, 28, 23)
    dt5 = 1
    dc1 = MonthlyCollection(Header(Temperature(), 'C', a_per_3),
                            [v1, v2, v2], [dt5, dt1, dt2])
    dc1_new = dc1.validate_analysis_period()
    assert dc1_new.header.analysis_period == a_per_3
    assert dc1_new.datetimes == (dt1, dt2, dt5)
    dc1 = MonthlyCollection(Header(Temperature(), 'C', a_per_3),
                            [v1, v2], [dt1, dt2])
    dc1_new = dc1.validate_analysis_period()
    assert dc1_new.header.analysis_period == a_per_3
    assert dc1_new.datetimes == (dt1, dt2)
    dc1 = MonthlyCollection(Header(Temperature(), 'C', a_per_3),
                            [v1, v2], [dt5, 2])
    dc1_new = dc1.validate_analysis_period()
    assert dc1_new.datetimes == (dt5, 2)
    assert dc1_new.header.analysis_period == a_per_3
    dc1 = MonthlyCollection(Header(Temperature(), 'C', a_per_3),
                            [v1, v2], [dt5, 4])
    dc1_new = dc1.validate_analysis_period()
    assert dc1_new.header.analysis_period == AnalysisPeriod()
    assert dc1_new.datetimes == (dt5, 4)

    # Test that duplicated datetimes are caught
    dc1 = MonthlyCollection(Header(Temperature(), 'C', a_per),
                            [v1, v2], [dt1, dt1])
    with pytest.raises(Exception):
        dc1_new = dc1.validate_analysis_period()


def test_validate_a_period_monthly_per_hour():
    """Test validate_a_period for monthly_per_hour collections."""
    a_per = AnalysisPeriod(6, 1, 0, 7, 1, 23)
    v1, v2 = 20, 25
    dt1, dt2 = (6, 12), (7, 13)

    # Test that the validate method correctly sorts reversed datetimes.
    dc1 = MonthlyPerHourCollection(Header(Temperature(), 'C', a_per),
                                   [v1, v2], [dt2, dt1])
    dc1_new = dc1.validate_analysis_period()
    assert not dc1.validated_a_period
    assert dc1_new.validated_a_period
    assert dc1.datetimes == (dt2, dt1)
    assert dc1_new.datetimes == (dt1, dt2)

    # Test that the validate method correctly updates analysis_period range.
    a_per_2 = AnalysisPeriod(6, 1, 15, 6, 1, 23)
    dc1 = MonthlyPerHourCollection(Header(Temperature(), 'C', a_per_2),
                                   [v1, v2], [dt1, dt2])
    dc1_new = dc1.validate_analysis_period()
    assert not dc1.validated_a_period
    assert dc1_new.validated_a_period
    assert dc1.header.analysis_period == a_per_2
    assert dc1_new.header.analysis_period == AnalysisPeriod(
        6, 1, 12, 7, 31, 23)

    # Test that the validate method with reversed analysis_periods.
    a_per_3 = AnalysisPeriod(6, 1, 0, 2, 28, 23)
    dt5 = (1, 15)
    dc1 = MonthlyPerHourCollection(Header(Temperature(), 'C', a_per_3),
                                   [v1, v2, v2], [dt5, dt1, dt2])
    dc1_new = dc1.validate_analysis_period()
    assert dc1_new.header.analysis_period == a_per_3
    assert dc1_new.datetimes == (dt1, dt2, dt5)
    dc1 = MonthlyPerHourCollection(Header(Temperature(), 'C', a_per_3),
                                   [v1, v2], [dt1, dt2])
    dc1_new = dc1.validate_analysis_period()
    assert dc1_new.header.analysis_period == a_per_3
    assert dc1_new.datetimes == (dt1, dt2)
    dc1 = MonthlyPerHourCollection(Header(Temperature(), 'C', a_per_3),
                                   [v1, v2], [dt5, (2, 12)])
    dc1_new = dc1.validate_analysis_period()
    assert dc1_new.datetimes == (dt5, (2, 12))
    assert dc1_new.header.analysis_period == a_per_3
    dc1 = MonthlyPerHourCollection(Header(Temperature(), 'C', a_per_3),
                                   [v1, v2], [dt5, (4, 12)])
    dc1_new = dc1.validate_analysis_period()
    assert dc1_new.header.analysis_period == AnalysisPeriod()
    assert dc1_new.datetimes == (dt5, (4, 12))

    # Test that duplicated datetimes are caught
    dc1 = MonthlyPerHourCollection(Header(Temperature(), 'C', a_per),
                                   [v1, v2], [dt1, dt1])
    with pytest.raises(Exception):
        dc1_new = dc1.validate_analysis_period()


def test_bounds():
    """Test the bounds method."""
    header1 = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(xrange(8760))
    dc1 = HourlyContinuousCollection(header1, values)
    min, max = dc1.bounds
    assert min == 0
    assert max == 8759


def test_min_max():
    """Test the min and max methods."""
    header1 = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(xrange(10, 8770))
    dc = HourlyContinuousCollection(header1, values)
    assert dc.min == 10
    assert dc.max == 8769


def test_average_median():
    """Test the average and median methods."""
    header1 = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(xrange(8760))
    dc = HourlyContinuousCollection(header1, values)
    assert dc.average == dc.median == 4379.5
    dc[0] = -10000
    assert dc.average == pytest.approx(4378.35844, rel=1e-3)
    assert dc.median == 4379.5


def test_total():
    """Test the total method."""
    header1 = Header(Temperature(), 'C', AnalysisPeriod())
    values = [1] * 8760
    dc = HourlyContinuousCollection(header1, values)
    assert dc.total == 8760


def test_to_unit():
    """Test the conversion of DataCollection units."""
    header1 = Header(Temperature(), 'C', AnalysisPeriod())
    header2 = Header(Temperature(), 'F', AnalysisPeriod())
    values = [20] * 8760
    dc1 = HourlyContinuousCollection(header1, values)
    dc2 = HourlyContinuousCollection(header2, values)
    dc3 = dc1.to_unit('K')
    dc4 = dc2.to_unit('K')
    assert dc1.values[0] == 20
    assert dc3.values[0] == 293.15
    assert dc2.values[0] == 20
    assert dc4.values[0] == pytest.approx(266.483, rel=1e-1)


def test_to_time_aggregated():
    """Test the conversion of DataCollection to time aggregated."""
    header1 = Header(Power(), 'W', AnalysisPeriod())
    header2 = Header(Speed(), 'm/s', AnalysisPeriod())
    values = [20] * 8760
    dc1 = HourlyContinuousCollection(header1, values)
    dc2 = HourlyContinuousCollection(header2, values)
    dc3 = dc1.to_time_aggregated()
    dc4 = dc2.to_time_aggregated()
    assert isinstance(dc3.header.data_type, Energy)
    assert dc3.header.unit == 'kWh'
    assert isinstance(dc4.header.data_type, Distance)
    assert dc4.header.unit == 'm'


def test_to_time_rate_of_change():
    """Test the conversion of DataCollection to time rate of change."""
    header1 = Header(Energy(), 'kWh', AnalysisPeriod())
    header2 = Header(Distance(), 'm', AnalysisPeriod())
    values = [20] * 8760
    dc1 = HourlyContinuousCollection(header1, values)
    dc2 = HourlyContinuousCollection(header2, values)
    dc3 = dc1.to_time_rate_of_change()
    dc4 = dc2.to_time_rate_of_change()
    assert isinstance(dc3.header.data_type, Power)
    assert dc3.header.unit == 'W'
    assert isinstance(dc4.header.data_type, Speed)
    assert dc4.header.unit == 'm/s'


def test_to_ip_si():
    """Test the conversion of DataCollection to IP and SI units."""
    header1 = Header(Temperature(), 'C', AnalysisPeriod())
    values = [20] * 8760
    dc1 = HourlyContinuousCollection(header1, values)
    dc2 = dc1.to_ip()
    dc3 = dc2.to_si()
    assert dc1.values[0] == 20
    assert dc2.values[0] == 68
    assert dc3.values[0] == dc1.values[0]


def test_highest_values():
    header = Header(Temperature(), 'C', AnalysisPeriod())
    test_data = list(xrange(8760))
    test_count = len(test_data)/2
    dc3 = HourlyContinuousCollection(header, test_data)

    test_highest_values, test_highest_values_index = \
        dc3.highest_values(test_count)

    assert test_highest_values == list(reversed(test_data[4380:8760]))
    assert test_highest_values_index == list(xrange(8759, 4379, -1))


def test_lowest_values():
    header = Header(Temperature(), 'C', AnalysisPeriod())
    test_data = [50] * 8760
    test_count = len(test_data)/2
    dc3 = HourlyContinuousCollection(header, test_data)

    test_lowest_values, test_lowest_values_index = \
        dc3.lowest_values(test_count)

    assert test_lowest_values == list(test_data[0:4380])
    assert test_lowest_values_index == list(xrange(0, 4380))


def test_percentile():
    """Test the percentile method."""
    header1 = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(xrange(8760))
    dc = HourlyContinuousCollection(header1, values)

    assert dc.percentile(0) == 0
    assert dc.percentile(25) == 2189.75
    assert dc.percentile(50) == 4379.5
    assert dc.percentile(75) == 6569.25
    assert dc.percentile(100) == 8759

    with pytest.raises(Exception):
        dc.percentile(-10)
    with pytest.raises(Exception):
        dc.percentile(110)


def test_filter_by_conditional_statement():
    """Test filter by conditional statement."""
    a_per = AnalysisPeriod(end_month=1, end_day=2)
    header1 = Header(Temperature(), 'C', a_per)
    values = list(xrange(48))
    dc1 = HourlyDiscontinuousCollection(header1, values, a_per.datetimes)

    dc2 = dc1.filter_by_conditional_statement('a > 23')
    assert len(dc2) == 24
    for d in dc2.values:
        assert d > 23


def test_filter_by_conditional_statement_continuous():
    """Test filter by conditional statement."""
    header1 = Header(Temperature(), 'C', AnalysisPeriod(end_month=1, end_day=2))
    values = list(xrange(48))
    dc1 = HourlyContinuousCollection(header1, values)

    dc2 = dc1.filter_by_conditional_statement('a > 23')
    assert len(dc2) == 24
    for d in dc2.values:
        assert d > 23
    assert not isinstance(dc2, HourlyContinuousCollection)


def test_filter_by_pattern():
    """Test filter by pattern."""
    a_per = AnalysisPeriod(end_month=1, end_day=2)
    header1 = Header(Temperature(), 'C', a_per)
    values = list(xrange(48))
    dc1 = HourlyDiscontinuousCollection(header1, values, a_per.datetimes)

    dc2 = dc1.filter_by_pattern([True, False] * 24)
    assert len(dc2) == 24


def test_filter_by_pattern_continuous():
    """Test filter by pattern."""
    header1 = Header(Temperature(), 'C', AnalysisPeriod(end_month=1, end_day=2))
    values = list(xrange(48))
    dc1 = HourlyContinuousCollection(header1, values)

    dc2 = dc1.filter_by_pattern([True, False] * 24)
    assert len(dc2) == 24
    assert not isinstance(dc2, HourlyContinuousCollection)


def test_filter_by_analysis_period_sub_hourly():
    """Test filtering by analysis period on sub-hourly continuous collection."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(range(8760))
    dc1 = HourlyContinuousCollection(header, values)
    dc2 = dc1.interpolate_to_timestep(4)

    dc3 = dc2.filter_by_analysis_period(
        AnalysisPeriod(st_month=7, end_month=7, timestep=4))
    assert len(dc3) == 2976
    dc4 = dc2.filter_by_analysis_period(
        AnalysisPeriod(st_hour=9, end_hour=17, timestep=4))
    assert len(dc4) == 12045


def test_filter_by_analysis_period_hourly():
    """Test filtering by analysis period on hourly discontinuous collection."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(xrange(8760))
    dc = HourlyDiscontinuousCollection(header, values,
                                       header.analysis_period.datetimes)
    dc = dc.validate_analysis_period()
    a_per = AnalysisPeriod(st_month=3, end_month=3)
    filt_dc = dc.filter_by_analysis_period(a_per)
    assert len(filt_dc) == 31 * 24
    assert filt_dc.header.analysis_period == a_per
    assert filt_dc.datetimes[0] == DateTime(3, 1, 0)
    assert filt_dc.datetimes[-1] == DateTime(3, 31, 23)


def test_filter_by_analysis_period_daily():
    """Test filtering by analysis period on daily collection."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(xrange(365))
    dc = DailyCollection(header, values, AnalysisPeriod().doys_int)
    dc = dc.validate_analysis_period()
    a_per = AnalysisPeriod(st_month=3, end_month=4, end_day=30)
    filt_dc = dc.filter_by_analysis_period(a_per)
    assert len(filt_dc) == 31 + 30
    assert filt_dc.header.analysis_period == a_per
    assert filt_dc.datetimes[0] == 31 + 28 + 1
    assert filt_dc.datetimes[-1] == 31 + 28 + 31 + 30


def test_filter_by_analysis_period_monthly():
    """Test filtering by analysis period on monthly collection."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(xrange(12))
    dc = MonthlyCollection(header, values, AnalysisPeriod().months_int)
    a_per = AnalysisPeriod(st_month=3, end_month=6)
    filt_dc = dc.filter_by_analysis_period(a_per)
    assert len(filt_dc) == 4
    assert filt_dc.header.analysis_period == a_per
    assert filt_dc.datetimes[0] == 3
    assert filt_dc.datetimes[-1] == 6


def test_filter_by_analysis_period_monthly_per_hour():
    """Test filtering by analysis period on monthly per hour collection."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(xrange(12 * 24))
    dc = MonthlyPerHourCollection(header, values, AnalysisPeriod().months_per_hour)
    a_per = AnalysisPeriod(st_month=3, end_month=4, end_day=30)
    filt_dc = dc.filter_by_analysis_period(a_per)
    assert len(filt_dc) == 2 * 24
    assert filt_dc.header.analysis_period == a_per
    assert filt_dc.datetimes[0] == (3, 0, 0)
    assert filt_dc.datetimes[-1] == (4, 23, 0)


def test_filter_by_analysis_period_continuous():
    """Test filtering by analysis period on hourly continuous collection."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(xrange(8760))
    dc = HourlyContinuousCollection(header, values)
    a_per = AnalysisPeriod(st_month=3, end_month=3)
    filt_dc = dc.filter_by_analysis_period(a_per)
    assert len(filt_dc) == 31 * 24
    assert filt_dc.header.analysis_period == a_per
    assert filt_dc.datetimes[0] == DateTime(3, 1, 0)
    assert filt_dc.datetimes[-1] == DateTime(3, 31, 23)
    assert isinstance(filt_dc, HourlyContinuousCollection)


def test_filter_by_analysis_period_continuous_reversed():
    """Test filtering by reversed analysis period on hourly continuous collection."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(xrange(8760))
    dc = HourlyContinuousCollection(header, values)
    a_per = AnalysisPeriod(st_month=12, end_month=3)
    filt_dc = dc.filter_by_analysis_period(a_per)
    assert len(filt_dc) == (31 + 31 + 28 + 31) * 24
    assert filt_dc.header.analysis_period == a_per
    assert filt_dc.datetimes[0] == DateTime(12, 1, 0)
    assert filt_dc.datetimes[-1] == DateTime(3, 31, 23)
    assert isinstance(filt_dc, HourlyContinuousCollection)


def test_filter_by_analysis_period_continuous_hour_subset():
    """Test filtering hour subset analysis period on hourly continuous collection."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(xrange(8760))
    dc = HourlyContinuousCollection(header, values)
    a_per = AnalysisPeriod(3, 2, 9, 3, 8, 17)
    filt_dc = dc.filter_by_analysis_period(a_per)
    assert len(filt_dc) == 7 * 9
    assert filt_dc.header.analysis_period == a_per
    assert filt_dc.datetimes[0] == DateTime(3, 2, 9)
    assert filt_dc.datetimes[-1] == DateTime(3, 8, 17)
    assert not isinstance(filt_dc, HourlyContinuousCollection)


def test_filter_by_analysis_period_continuous_large():
    """Test filtering large analysis period on hourly continuous collection."""
    header = Header(Temperature(), 'C', AnalysisPeriod(st_month=3, end_month=3))
    values = list(xrange(24 * 31))
    dc = HourlyContinuousCollection(header, values)
    a_per = AnalysisPeriod(st_hour=9, end_hour=17)
    filt_dc = dc.filter_by_analysis_period(a_per)
    assert len(filt_dc) == 31 * 9
    assert filt_dc.header.analysis_period == AnalysisPeriod(3, 1, 9, 3, 31, 17)
    assert filt_dc.datetimes[0] == DateTime(3, 1, 9)
    assert filt_dc.datetimes[-1] == DateTime(3, 31, 17)
    assert not isinstance(filt_dc, HourlyContinuousCollection)


def test_filter_by_hoys():
    """Test filter_by_hoys method."""
    a_per = AnalysisPeriod(st_month=3, end_month=3)
    header = Header(Temperature(), 'C', a_per)
    values = list(xrange(24 * 31))
    dc = HourlyDiscontinuousCollection(header, values, a_per.datetimes)
    hoys = AnalysisPeriod(st_hour=9, end_hour=17).hoys
    filt_dc = dc.filter_by_hoys(hoys)
    assert len(filt_dc) == 31 * 9
    assert filt_dc.datetimes[0] == DateTime(3, 1, 9)
    assert filt_dc.datetimes[-1] == DateTime(3, 31, 17)


def test_filter_by_hoys_continuous():
    """Test filter_by_hoys method."""
    header = Header(Temperature(), 'C', AnalysisPeriod(st_month=3, end_month=3))
    values = list(xrange(24 * 31))
    dc = HourlyContinuousCollection(header, values)
    hoys = AnalysisPeriod(st_hour=9, end_hour=17).hoys
    filt_dc = dc.filter_by_hoys(hoys)
    assert len(filt_dc) == 31 * 9
    assert filt_dc.datetimes[0] == DateTime(3, 1, 9)
    assert filt_dc.datetimes[-1] == DateTime(3, 31, 17)
    assert not isinstance(filt_dc, HourlyContinuousCollection)


def test_average_daily():
    """Test the average daily method."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(xrange(8760))
    dc = HourlyContinuousCollection(header, values)
    new_dc = dc.average_daily()
    assert isinstance(new_dc, DailyCollection)
    assert len(new_dc) == 365
    assert new_dc.datetimes[0] == 1
    assert new_dc.datetimes[-1] == 365
    assert new_dc.is_continuous
    for i, val in dc.group_by_day().items():
        assert new_dc[i - 1] == sum(val) / len(val)


def test_total_daily():
    """Test the total daily method."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(xrange(8760))
    dc = HourlyContinuousCollection(header, values)
    new_dc = dc.total_daily()
    assert isinstance(new_dc, DailyCollection)
    assert len(new_dc) == 365
    assert new_dc.datetimes[0] == 1
    assert new_dc.datetimes[-1] == 365
    assert new_dc.is_continuous
    for i, val in dc.group_by_day().items():
        assert new_dc[i - 1] == sum(val)


def test_percentile_daily():
    """Test the percentile daily method."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(xrange(24)) * 365
    dc = HourlyContinuousCollection(header, values)
    new_dc = dc.percentile_daily(25)
    assert isinstance(new_dc, DailyCollection)
    assert len(new_dc) == 365
    assert new_dc.datetimes[0] == 1
    assert new_dc.datetimes[-1] == 365
    assert new_dc.is_continuous
    for i, val in dc.group_by_day().items():
        assert new_dc[i - 1] == 5.75


def test_average_monthly():
    """Test the average monthly method."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(xrange(8760))
    dc = HourlyContinuousCollection(header, values)
    new_dc = dc.average_monthly()
    assert isinstance(new_dc, MonthlyCollection)
    assert len(new_dc) == 12
    assert new_dc.datetimes[0] == 1
    assert new_dc.datetimes[-1] == 12
    assert new_dc.is_continuous
    for i, val in dc.group_by_month().items():
        assert new_dc[i - 1] == sum(val) / len(val)


def test_total_monthly():
    """Test the total monthly method."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(xrange(8760))
    dc = HourlyContinuousCollection(header, values)
    new_dc = dc.total_monthly()
    assert isinstance(new_dc, MonthlyCollection)
    assert len(new_dc) == 12
    assert new_dc.datetimes[0] == 1
    assert new_dc.datetimes[-1] == 12
    assert new_dc.is_continuous
    for i, val in dc.group_by_month().items():
        assert new_dc[i - 1] == sum(val)


def test_percentile_monthly():
    """Test the percentile monthly method."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = [50] * 8760
    dc = HourlyContinuousCollection(header, values)
    new_dc = dc.percentile_monthly(25)
    assert isinstance(new_dc, MonthlyCollection)
    assert len(new_dc) == 12
    assert new_dc.datetimes[0] == 1
    assert new_dc.datetimes[-1] == 12
    assert new_dc.is_continuous
    for i, val in dc.group_by_month().items():
        assert new_dc[i - 1] == 50


def test_average_monthly_on_daily_collection():
    """Test the average monthly method."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(xrange(365))
    dc = DailyCollection(header, values, AnalysisPeriod().doys_int)
    new_dc = dc.average_monthly()
    assert isinstance(new_dc, MonthlyCollection)
    assert len(new_dc) == 12
    assert new_dc.datetimes[0] == 1
    assert new_dc.datetimes[-1] == 12
    for i, val in dc.group_by_month().items():
        assert new_dc[i - 1] == sum(val) / len(val)


def test_total_monthly_on_daily_collection():
    """Test the total monthly method."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(xrange(365))
    dc = DailyCollection(header, values, AnalysisPeriod().doys_int)
    new_dc = dc.total_monthly()
    assert isinstance(new_dc, MonthlyCollection)
    assert len(new_dc) == 12
    assert new_dc.datetimes[0] == 1
    assert new_dc.datetimes[-1] == 12
    for i, val in dc.group_by_month().items():
        assert new_dc[i - 1] == sum(val)


def test_percentile_monthly_on_daily_collection():
    """Test the percentile monthly method."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(xrange(365))
    dc = DailyCollection(header, values, AnalysisPeriod().doys_int)
    new_dc = dc.percentile_monthly(25)
    assert isinstance(new_dc, MonthlyCollection)
    assert len(new_dc) == 12
    assert new_dc.datetimes[0] == 1
    assert new_dc.datetimes[-1] == 12


def test_average_monthly_per_hour():
    """Test the average monthly per hour method."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(xrange(8760))
    dc = HourlyContinuousCollection(header, values)
    new_dc = dc.average_monthly_per_hour()
    assert isinstance(new_dc, MonthlyPerHourCollection)
    assert len(new_dc) == 12 * 24
    assert new_dc.datetimes[0] == (1, 0, 0)
    assert new_dc.datetimes[-1] == (12, 23, 0)
    assert new_dc.is_continuous
    for i, val in enumerate(dc.group_by_month_per_hour().values()):
        assert new_dc[i] == sum(val) / len(val)


def test_total_monthly_per_hour():
    """Test the total monthly per hour method."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(xrange(8760))
    dc = HourlyContinuousCollection(header, values)
    new_dc = dc.total_monthly_per_hour()
    assert isinstance(new_dc, MonthlyPerHourCollection)
    assert len(new_dc) == 12 * 24
    assert new_dc.datetimes[0] == (1, 0, 0)
    assert new_dc.datetimes[-1] == (12, 23, 0)
    assert new_dc.is_continuous
    for i, val in enumerate(dc.group_by_month_per_hour().values()):
        assert new_dc[i] == sum(val)


def test_percentile_monthly_per_hour():
    """Test the percentile monthly per hour method."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(xrange(24)) * 365
    dc = HourlyContinuousCollection(header, values)
    new_dc = dc.percentile_monthly_per_hour(25)
    assert isinstance(new_dc, MonthlyPerHourCollection)
    assert len(new_dc) == 12 * 24
    assert new_dc.datetimes[0] == (1, 0, 0)
    assert new_dc.datetimes[-1] == (12, 23, 0)
    assert new_dc.is_continuous
    pct_vals = list(xrange(24)) * 12
    for i, val in enumerate(pct_vals):
        assert new_dc[i] == val


def test_group_by_day_discontinuous():
    """Test the group by day method for discontinuous collections."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(xrange(8760))
    dc = HourlyDiscontinuousCollection(header, values, AnalysisPeriod().datetimes)
    day_dict = dc.group_by_day()
    assert list(day_dict.keys()) == list(xrange(1, 366))
    for val in day_dict.values():
        assert len(val) == 24


def test_group_by_month_discontinuous():
    """Test the group by month method for discontinuous collections."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(xrange(8760))
    dc = HourlyDiscontinuousCollection(header, values, AnalysisPeriod().datetimes)
    day_dict = dc.group_by_month()
    assert list(day_dict.keys()) == list(xrange(1, 13))
    days_per_month = AnalysisPeriod().NUMOFDAYSEACHMONTH
    for i, val in enumerate(day_dict.values()):
        assert len(val) == 24 * days_per_month[i]


def test_interpolate_holes():
    """Test the interpolate holes method on the discontinuous collection."""
    a_per = AnalysisPeriod(6, 21, 0, 6, 21, 23)
    dt1, dt2 = DateTime(6, 21, 12), DateTime(6, 21, 14)
    v1, v2 = 20, 25
    dc1 = HourlyDiscontinuousCollection(Header(Temperature(), 'C', a_per),
                                        [v1, v2], [dt1, dt2])
    with pytest.raises(Exception):
        interp_coll1 = dc1.interpolate_holes()
    dc2 = dc1.validate_analysis_period()
    interp_coll1 = dc2.interpolate_holes()
    assert isinstance(interp_coll1, HourlyContinuousCollection)
    assert len(interp_coll1.values) == 24
    assert interp_coll1[0] == 20
    assert interp_coll1[12] == 20
    assert interp_coll1[13] == 22.5
    assert interp_coll1[14] == 25
    assert interp_coll1[23] == 25

    values = list(xrange(24))
    test_header = Header(GenericType('Test Type', 'test'), 'test',
                         AnalysisPeriod(end_month=1, end_day=1))
    dc3 = HourlyContinuousCollection(test_header, values)
    interp_coll2 = dc3.interpolate_holes()
    assert isinstance(interp_coll2, HourlyContinuousCollection)
    assert len(interp_coll2.values) == 24


def test_cull_to_timestep():
    """Test the test_cull_to_timestep method on the discontinuous collection."""
    a_per = AnalysisPeriod(6, 21, 0, 6, 21, 23)
    dt1, dt2, dt3 = DateTime(6, 21, 12), DateTime(6, 21, 13), DateTime(6, 21, 12, 30)
    v1, v2 = 20, 25
    dc1 = HourlyDiscontinuousCollection(Header(Temperature(), 'C', a_per),
                                        [v1, v2, v2], [dt1, dt3, dt2])
    dc1_new = dc1.validate_analysis_period()
    dc2_new = dc1.cull_to_timestep()
    assert dc1_new.header.analysis_period.timestep == 2
    assert dc2_new.header.analysis_period.timestep == 1
    assert len(dc1_new.values) == 3
    assert len(dc2_new.values) == 2

    dc1_new.convert_to_culled_timestep()
    assert dc1_new.header.analysis_period.timestep == 1
    assert len(dc1_new.values) == 2


def test_interpolate_to_timestep():
    """Test the interpolation method on the continuous collection."""
    values = list(xrange(24))
    test_header = Header(GenericType('Test Type', 'test'), 'test',
                         AnalysisPeriod(end_month=1, end_day=1))
    dc2 = HourlyContinuousCollection(test_header, values)

    # check the interpolate data functions
    interp_coll1 = dc2.interpolate_to_timestep(2)
    interp_coll2 = dc2.interpolate_to_timestep(2, True)
    assert interp_coll1[1] == 0.5
    assert interp_coll2[1] == 0.25
    assert 'Minute' in interp_coll1.timestep_text


def test_is_collection_aligned():
    """Test the test_is_collection_aligned method for discontinuous collections."""
    header = Header(Temperature(), 'C', AnalysisPeriod(end_month=1, end_day=1))
    header3 = Header(Temperature(), 'C', AnalysisPeriod(end_month=1, end_day=2))
    header4 = Header(Temperature(), 'C', AnalysisPeriod(
        st_day=2, end_month=1, end_day=2))
    header5 = Header(Temperature(), 'C', AnalysisPeriod(end_month=1, end_day=24))
    values1 = list(xrange(24))
    values2 = [12] * 24
    values3 = [12] * 48
    dc1 = HourlyDiscontinuousCollection(header, values1,
                                        header.analysis_period.datetimes)
    dc2 = HourlyDiscontinuousCollection(header, values2,
                                        header.analysis_period.datetimes)
    dc3 = HourlyDiscontinuousCollection(header3, values3,
                                        header3.analysis_period.datetimes)
    dc4 = HourlyDiscontinuousCollection(header4, values1,
                                        header4.analysis_period.datetimes)
    dc5 = DailyCollection(header5, values1, header5.analysis_period.doys_int)

    assert dc1.is_collection_aligned(dc2)
    assert dc2.is_collection_aligned(dc1)
    assert not dc1.is_collection_aligned(dc3)
    assert not dc3.is_collection_aligned(dc1)
    assert not dc1.is_collection_aligned(dc4)
    assert not dc4.is_collection_aligned(dc1)
    assert not dc1.is_collection_aligned(dc5)
    assert not dc5.is_collection_aligned(dc1)

    assert HourlyDiscontinuousCollection.are_collections_aligned([dc1, dc2])
    assert not HourlyDiscontinuousCollection.are_collections_aligned(
        [dc1, dc2, dc3], False)


def test_is_collection_aligned_continuous():
    """Test the test_is_collection_aligned method for continuous collections."""
    header = Header(Temperature(), 'C', AnalysisPeriod(end_month=1, end_day=1))
    header3 = Header(Temperature(), 'C', AnalysisPeriod(end_month=1, end_day=2))
    values1 = list(xrange(24))
    values2 = [12] * 24
    values3 = [12] * 48
    dc1 = HourlyContinuousCollection(header, values1)
    dc2 = HourlyContinuousCollection(header, values2)
    dc3 = HourlyContinuousCollection(header3, values3)

    assert dc1.is_collection_aligned(dc2)
    assert dc2.is_collection_aligned(dc1)
    assert not dc1.is_collection_aligned(dc3)
    assert not dc3.is_collection_aligned(dc1)

    assert HourlyContinuousCollection.are_collections_aligned([dc1, dc2])
    assert not HourlyContinuousCollection.are_collections_aligned(
        [dc1, dc2, dc3], False)


def test_get_aligned_collection():
    """Test the method for getting an aligned discontinuous collection."""
    header = Header(Temperature(), 'C', AnalysisPeriod(end_month=1, end_day=1))
    values = list(xrange(24))
    dc1 = HourlyDiscontinuousCollection(header, values,
                                        header.analysis_period.datetimes)
    dc2 = dc1.get_aligned_collection(50)
    assert dc1.header.data_type.name == dc2.header.data_type.name
    assert dc1.header.unit == dc2.header.unit
    assert dc1.header.analysis_period == dc2.header.analysis_period
    assert dc1.header.metadata == dc2.header.metadata
    assert dc1.datetimes == dc2.datetimes
    assert len(dc1.values) == len(dc2.values)
    assert dc2.values == tuple([50] * 24)

    dc3 = dc1.get_aligned_collection(50, RelativeHumidity(), '%')
    assert dc3.header.data_type.name == 'Relative Humidity'
    assert dc3.header.unit == '%'


def test_get_aligned_collection_continuous():
    """Test the method for getting an aligned continuous collection."""
    header = Header(Temperature(), 'C', AnalysisPeriod(end_month=1, end_day=1))
    values = list(xrange(24))
    dc1 = HourlyContinuousCollection(header, values)
    dc2 = dc1.get_aligned_collection(50)
    assert dc1.header.data_type.name == dc2.header.data_type.name
    assert dc1.header.unit == dc2.header.unit
    assert dc1.header.analysis_period == dc2.header.analysis_period
    assert dc1.header.metadata == dc2.header.metadata
    assert len(dc1.values) == len(dc2.values)
    assert dc2.values == tuple([50] * 24)

    dc3 = dc1.get_aligned_collection(50, RelativeHumidity(), '%')
    assert dc3.header.data_type.name == 'Relative Humidity'
    assert dc3.header.unit == '%'


def test_compute_function_aligned():
    """Test the method for computing functions with aligned collections."""
    epw_file_path = './tests/assets/epw/chicago.epw'
    chicago_epw = EPW(epw_file_path)
    pressure_at_chicago = 95000
    hr_inputs = [chicago_epw.dry_bulb_temperature,
                 chicago_epw.relative_humidity,
                 pressure_at_chicago]
    humid_ratio = HourlyContinuousCollection.compute_function_aligned(
        humid_ratio_from_db_rh, hr_inputs, HumidityRatio(), 'fraction')
    assert isinstance(humid_ratio, HourlyContinuousCollection)
    assert len(humid_ratio.values) == 8760
    for i, val in enumerate(humid_ratio.values):
        assert val == humid_ratio_from_db_rh(chicago_epw.dry_bulb_temperature[i],
                                             chicago_epw.relative_humidity[i],
                                             pressure_at_chicago)

    hr_inputs = [20, 70, pressure_at_chicago]
    humid_ratio = HourlyContinuousCollection.compute_function_aligned(
        humid_ratio_from_db_rh, hr_inputs, HumidityRatio(), 'fraction')
    assert isinstance(humid_ratio, float)
    assert humid_ratio == humid_ratio_from_db_rh(20, 70, pressure_at_chicago)


def test_duplicate():
    """Test the duplicate method on the discontinuous collections."""
    header = Header(Temperature(), 'C', AnalysisPeriod(end_month=1, end_day=1))
    values = list(xrange(24))
    dc1 = HourlyDiscontinuousCollection(header, values,
                                        header.analysis_period.datetimes)
    dc2 = dc1.duplicate()
    assert dc1.header.data_type.name == dc2.header.data_type.name
    assert dc1.header.unit == dc2.header.unit
    assert dc1.header.analysis_period == dc2.header.analysis_period
    assert dc1.header.metadata == dc2.header.metadata
    assert dc1.values == dc2.values
    assert dc1.datetimes == dc2.datetimes


def test_duplicate_continuous():
    """Test the duplicate method on the continuous collection."""
    header = Header(Temperature(), 'C', AnalysisPeriod(end_month=1, end_day=1))
    values = list(xrange(24))
    dc1 = HourlyContinuousCollection(header, values)
    dc2 = dc1.duplicate()
    assert dc1.header.data_type.name == dc2.header.data_type.name
    assert dc1.header.unit == dc2.header.unit
    assert dc1.header.analysis_period == dc2.header.analysis_period
    assert dc1.header.metadata == dc2.header.metadata
    assert dc1.values == dc2.values


def test_dict_methods():
    """Test the to/from dict methods for discontinuous collections."""
    header = Header(Temperature(), 'C', AnalysisPeriod(end_month=1, end_day=1))
    values = list(xrange(24))
    dc = HourlyDiscontinuousCollection(header, values,
                                       header.analysis_period.datetimes)
    dc_dict = dc.to_dict()
    reconstruced_dc = HourlyDiscontinuousCollection.from_dict(dc_dict)
    assert dc_dict == reconstruced_dc.to_dict()


def test_dict_methods_continuous():
    """Test the to/from dict methods for continuous collection."""
    header = Header(Temperature(), 'C', AnalysisPeriod(end_month=1, end_day=1))
    values = list(xrange(24))
    dc = HourlyContinuousCollection(header, values)
    dc_dict = dc.to_dict()
    reconstruced_dc = HourlyContinuousCollection.from_dict(dc_dict)

    assert dc_dict == reconstruced_dc.to_dict()


def test_filter_collections_by_statement():
    """Test the method to filter collections by conditional statement."""
    header = Header(Temperature(), 'C', AnalysisPeriod(end_month=1, end_day=1))
    values1 = list(xrange(24))
    values2 = [12] * 24
    values3 = list(xrange(12, 36))
    dc1 = HourlyContinuousCollection(header, values1)
    dc2 = HourlyContinuousCollection(header, values2)
    dc3 = HourlyContinuousCollection(header, values3)

    filt_coll = HourlyContinuousCollection.filter_collections_by_statement(
        [dc1, dc2, dc3], 'a >= 12 and c <= 30')

    assert len(filt_coll) == 3
    assert len(filt_coll[0]) == len(filt_coll[1]) == len(filt_coll[2]) == 7
    assert filt_coll[0].values == (12, 13, 14, 15, 16, 17, 18)
    assert filt_coll[1].values == (12, 12, 12, 12, 12, 12, 12)
    assert filt_coll[2].values == (24, 25, 26, 27, 28, 29, 30)
    assert isinstance(filt_coll[0], HourlyDiscontinuousCollection)


def test_is_in_range_data_type():
    """Test the function to check whether values are in range for the data_type."""
    header1 = Header(Temperature(), 'C', AnalysisPeriod())
    header2 = Header(Temperature(), 'K', AnalysisPeriod())
    val1 = [20] * 8760
    val2 = [-300] * 8760
    val3 = [270] * 8760
    val4 = [-10] * 8760
    dc1 = HourlyContinuousCollection(header1, val1)
    dc2 = HourlyContinuousCollection(header1, val2)
    dc3 = HourlyContinuousCollection(header2, val3)
    dc4 = HourlyContinuousCollection(header2, val4)
    assert dc1.is_in_data_type_range(raise_exception=False)
    assert not dc2.is_in_data_type_range(raise_exception=False)
    assert dc3.is_in_data_type_range(raise_exception=False)
    assert not dc4.is_in_data_type_range(raise_exception=False)


def test_linspace():
    """Test the generation of bin array from bin range and num"""

    # Base case
    bin_arr = linspace(0, 360, 0)
    assert [] == bin_arr, bin_arr

    bin_arr = linspace(0, 360, 1)
    assert [0] == bin_arr, bin_arr

    bin_arr = linspace(0, 360, 2)
    assert [0, 360.0] == bin_arr, bin_arr

    bin_arr = linspace(0, 360, 4)
    assert [0.0, 120.0, 240.0, 360.0] == bin_arr, bin_arr

    bin_arr = linspace(0, 360, 5)
    assert [0.0, 90.0, 180.0, 270.0, 360.0] == bin_arr, bin_arr

    # Start from non zero
    bin_arr = linspace(180, 360, 4)
    assert [180.0, 240.0, 300.0, 360.0] == bin_arr, bin_arr

    # Start from non zero, w/ floats
    bin_arr = linspace(180., 360., 4)
    assert [180., 240.0, 300.0, 360.0] == bin_arr, bin_arr


def test_arange():
    """Test arange function."""

    # Basic
    r = arange(0, 10, 1)
    r = list(r)
    cr = list(range(10))
    assert len(r) == len(cr)
    for cv, v in zip(cr, r):
        assert abs(cv - v) < 1e-10

    # Fraction 1
    r = list(arange(0, 1, 0.1))
    cr = [0., 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    assert len(r) == len(cr)
    for cv, v in zip(cr, r):
        assert abs(cv - v) < 1e-10

    # Fraction 2
    r = list(arange(-0.55, 3, 0.0532))
    cr = [-0.55, -0.4968, -0.4436, -0.3904, -0.3372, -0.284, -0.2308,
          -0.1776, -0.1244, -0.0712, -0.018,  0.0352,  0.0884,  0.1416,
          0.1948,  0.248,  0.3012,  0.3544,  0.4076,  0.4608,  0.514,
          0.5672,  0.6204,  0.6736,  0.7268,  0.78,  0.8332,  0.8864,
          0.9396,  0.9928,  1.046,  1.0992,  1.1524,  1.2056,  1.2588,
          1.312,  1.3652,  1.4184,  1.4716,  1.5248,  1.578,  1.6312,
          1.6844,  1.7376,  1.7908,  1.844,  1.8972,  1.9504,  2.0036,
          2.0568,  2.11,  2.1632,  2.2164,  2.2696,  2.3228,  2.376,
          2.4292,  2.4824,  2.5356,  2.5888,  2.642,  2.6952,  2.7484,
          2.8016,  2.8548,  2.908,  2.9612]
    assert len(r) == len(cr)
    for cv, v in zip(cr, r):
        assert abs(cv - v) < 1e-10

    # Equal
    r = list(arange(10, 10, 1))
    assert len(r) == 0

    # Neg step
    r = list(arange(1, 0, -0.1))
    cr = [1., 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]
    assert len(r) == len(cr)
    for cv, v in zip(cr, r):
        assert abs(cv - v) < 1e-10

    # Neg start
    r = list(arange(-10, 0, 1))
    cr = [-10,  -9,  -8,  -7,  -6,  -5,  -4,  -3,  -2,  -1]
    assert len(r) == len(cr)
    for cv, v in zip(cr, r):
        assert abs(cv - v) < 1e-10

    # Neg stop
    r = list(arange(0, -10, -1))
    cr = [-i for i in range(10)]
    assert len(r) == len(cr)
    for cv, v in zip(cr, r):
        assert abs(cv - v) < 1e-10


def test_histogram():
    """Test the windrose histogram."""

    # Test simple 2 div
    bin_arr = linspace(0, 2, 3)
    assert bin_arr == [0, 1, 2]
    vals = [0, 0, 0, 1, 1, 1, 2, 2]
    hist = histogram(vals, bin_arr)
    assert hist == [[0, 0, 0], [1, 1, 1]]

    # Test out of bounds with 3 divisions
    bin_arr = linspace(0, 3, 4)
    vals = [0, 0, 0, 1, 1, 1, 2, 2]
    hist = histogram(vals, bin_arr)
    assert hist == [[0, 0, 0], [1, 1, 1], [2, 2]]

    # Test out of bounds with 2 divisions
    bin_arr = linspace(-3, 3, 3)
    vals = [-1, -2, 10, 0, 0, 0, 1, 1, 1, 2, 2, 34]
    hist = histogram(vals, bin_arr)
    assert hist == [[-2, -1], [0, 0, 0, 1, 1, 1, 2, 2]], hist

    # Test edge bounds
    bin_arr = linspace(0, 3, 3)
    vals = [0, 0, 0, 1, 1, 1, 2, 2, 3, 3]
    hist = histogram(vals, bin_arr)
    assert hist == [[0, 0, 0, 1, 1, 1], [2, 2]], hist

    # Test edge bounds 2
    hist = histogram([0, 0, 0.9, 1, 1.5, 1.99, 2, 3], (0, 1, 2, 3))
    assert hist == [[0, 0, 0.9], [1, 1.5, 1.99], [2]], hist


def test_histogram_circular():
    """Test the windrose histogram_circular data."""
    # # Test out of bounds with 3 divisions
    # bin_arr = linspace(-2, 2, 3)
    # assert bin_arr == [-2, 0, 2], bin_arr
    # vals = [-2, -1, 0, 0, 0, 1, 1, 1, 2, 2]
    # hist = histogram_circular(vals, bin_arr)
    # assert hist == [[-2, -1], [0, 0, 0, 1, 1, 1]], hist

    # Test North case
    bin_arr = [315, 345, 15, 45]
    vals = [315, 330, 331, 345, 350, 360, 0, 1, 16, 30, 44, 45]
    keys = list(range(len(vals)))
    chk_hist = [[315, 330, 331],      # 315 - 345
                [0, 0, 1, 345, 350],  # 345 - 15
                [16, 30, 44]]         # 15  - 45

    vals = [val % 360 for val in vals]

    hist = histogram_circular(
        zip(vals, keys), bin_arr, hist_range=(0, 360), key=lambda k: k[0])

    hist = [[_h[0] for _h in h] for h in hist]

    for chkh, h in zip(chk_hist, hist):
        for _chkh, _h in zip(chkh, h):
            assert _chkh == pytest.approx(_h, abs=1e-10)


def test_normalize_by_area():
    """Test the normalize_by_area method."""
    a_per = AnalysisPeriod(6, 21, 12, 6, 21, 13)
    dt1, dt2 = DateTime(6, 21, 12), DateTime(6, 21, 13)
    v1, v2 = 20, 25
    dc1 = HourlyDiscontinuousCollection(Header(Energy(), 'kWh', a_per, {'type': 'Energy'}),
                                        [v1, v2], [dt1, dt2])

    dc2 = dc1.normalize_by_area(5., 'm2')
    assert dc2.datetimes == (dt1, dt2)
    assert dc2.values == (v1 / 5., v2 / 5.)
    assert isinstance(dc2.header.data_type, EnergyIntensity)
    assert dc2.header.unit == 'kWh/m2'
    assert dc2.header.metadata['type'] == 'Energy Intensity'
