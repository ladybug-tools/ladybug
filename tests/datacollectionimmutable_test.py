# coding=utf-8
from __future__ import division

from ladybug.datacollection import HourlyDiscontinuousCollection, \
    HourlyContinuousCollection, MonthlyCollection, DailyCollection, \
    MonthlyPerHourCollection
from ladybug.datacollectionimmutable import HourlyDiscontinuousCollectionImmutable, \
    HourlyContinuousCollectionImmutable, MonthlyCollectionImmutable, \
    DailyCollectionImmutable, MonthlyPerHourCollectionImmutable
from ladybug.header import Header
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.dt import DateTime
from ladybug.datatype.temperature import Temperature
from ladybug.datatype.fraction import RelativeHumidity

import pytest
import sys
if (sys.version_info >= (3, 0)):
    xrange = range


def test_hourly():
    """Test the dicontinuous collections."""
    a_per = AnalysisPeriod(6, 21, 12, 6, 21, 13)
    dt1, dt2 = DateTime(6, 21, 12), DateTime(6, 21, 13)
    v1, v2 = 20, 25
    dc1 = HourlyDiscontinuousCollectionImmutable(
        Header(Temperature(), 'C', a_per), [v1, v2], [dt1, dt2])
    assert dc1.datetimes == (dt1, dt2)
    assert dc1.values == (v1, v2)
    assert not dc1.is_mutable
    with pytest.raises(AttributeError):
        dc1[0] = 18
    with pytest.raises(AttributeError):
        dc1.values = [18, 24]
    with pytest.raises(Exception):
        dc1.values.append(10)
    with pytest.raises(AttributeError):
        dc2 = dc1.convert_to_culled_timestep(1)

    dc2 = dc1.to_mutable()
    assert isinstance(dc2, HourlyDiscontinuousCollection)
    assert dc2.is_mutable
    dc2[0] = 18
    assert dc2[0] == 18
    dc2.values = [18, 24]
    assert dc2.values == (18, 24)
    with pytest.raises(Exception):
        dc2.values.append(10)  # make sure that we can still not append

    dc3 = dc2.to_immutable()
    assert isinstance(dc3, HourlyDiscontinuousCollectionImmutable)
    assert not dc3.is_mutable

    dc4 = dc3.to_immutable()
    assert isinstance(dc4, HourlyDiscontinuousCollectionImmutable)
    assert not dc4.is_mutable


def test_init_continuous():
    """Test the init methods for continuous collections"""
    # Setup temperature data collection
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(xrange(8760))
    dc1 = HourlyContinuousCollectionImmutable(header, values)
    assert len(dc1.datetimes) == 8760
    assert list(dc1.values) == list(xrange(8760))
    assert not dc1.is_mutable
    with pytest.raises(AttributeError):
        dc1[0] = 18
    with pytest.raises(AttributeError):
        dc1.values = [24] * 8760
    with pytest.raises(Exception):
        dc1.values.append(10)
    with pytest.raises(AttributeError):
        dc2 = dc1.convert_to_culled_timestep(1)

    dc2 = dc1.to_mutable()
    assert isinstance(dc2, HourlyContinuousCollection)
    assert dc2.is_mutable
    dc2[0] = 18
    assert dc2[0] == 18
    dc2.values = [24] * 8760
    assert dc2.values == tuple([24] * 8760)
    with pytest.raises(Exception):
        dc2.values.append(10)  # make sure that we can still not append

    dc3 = dc2.to_immutable()
    assert isinstance(dc3, HourlyContinuousCollectionImmutable)
    assert not dc3.is_mutable

    dc4 = dc3.to_immutable()
    assert isinstance(dc4, HourlyContinuousCollectionImmutable)
    assert not dc4.is_mutable


def _make_collection(kind):
    """Get a mutable Celsius temperature collection of the requested kind."""
    a_per = AnalysisPeriod(6, 21, 12, 6, 21, 13)
    day_per = AnalysisPeriod(6, 21, 0, 6, 22, 23)
    mon_per = AnalysisPeriod(6, 1, 0, 7, 31, 23)
    builders = {
        'discontinuous': lambda: HourlyDiscontinuousCollection(
            Header(Temperature(), 'C', a_per), [20, 25],
            [DateTime(6, 21, 12), DateTime(6, 21, 13)]),
        'continuous': lambda: HourlyContinuousCollection(
            Header(Temperature(), 'C', AnalysisPeriod(end_month=1, end_day=1)),
            [20] * 24),
        'daily': lambda: DailyCollection(
            Header(Temperature(), 'C', day_per), [20, 25], day_per.doys_int),
        'monthly': lambda: MonthlyCollection(
            Header(Temperature(), 'C', mon_per), [20, 25], mon_per.months_int),
        'monthly_per_hour': lambda: MonthlyPerHourCollection(
            Header(Temperature(), 'C', mon_per), [20] * 24 + [25] * 24,
            mon_per.months_per_hour)
    }
    return builders[kind]()


COLLECTION_KINDS = \
    ('discontinuous', 'continuous', 'daily', 'monthly', 'monthly_per_hour')


@pytest.mark.parametrize('kind', COLLECTION_KINDS)
def test_mutable_immutable_conversion_does_not_share_header(kind):
    """Converting between mutable and immutable must give each its own header."""
    source = _make_collection(kind)
    immutable = source.to_immutable()
    assert immutable.header is not source.header
    assert immutable.to_mutable().header is not immutable.header
    assert source.to_mutable().header is not source.header


@pytest.mark.parametrize('kind', COLLECTION_KINDS)
def test_unit_conversion_on_immutable_collection(kind):
    """In-place conversion is blocked; to_* returns a converted mutable copy."""
    source = _make_collection(kind)
    immutable = source.to_immutable()

    with pytest.raises(AttributeError):
        immutable.convert_to_ip()
    with pytest.raises(AttributeError):
        immutable.convert_to_si()
    with pytest.raises(AttributeError):
        immutable.convert_to_unit('F')

    converted = immutable.to_ip()
    assert type(converted) is type(source)
    assert converted.is_mutable
    assert converted.header.unit == 'F'
    assert converted.values[0] == pytest.approx(68)
    assert immutable.to_si().is_mutable
    assert immutable.to_unit('F').header.unit == 'F'
    assert immutable.header.unit == 'C'
    assert immutable.values[0] == 20
    assert source.header.unit == 'C'
    assert source.values[0] == 20

    source.convert_to_ip()
    assert immutable.header.unit == 'C'


@pytest.mark.parametrize('kind', COLLECTION_KINDS)
def test_mutable_and_immutable_classes_point_at_each_other(kind):
    """Each mutable class and its immutable counterpart must name one another."""
    source = _make_collection(kind)
    immutable = source.to_immutable()
    assert source.mutable_class is type(source)
    assert source.immutable_class is type(immutable)
    assert immutable.mutable_class is type(source)
    assert immutable.immutable_class is type(immutable)


@pytest.mark.parametrize('kind', COLLECTION_KINDS)
def test_get_aligned_collection_mutability(kind):
    """get_aligned_collection honors mutable= from a mutable or immutable start."""
    source = _make_collection(kind)
    immutable = source.to_immutable()
    for start in (source, immutable):
        assert type(start.get_aligned_collection(5)) is type(start)
        assert type(start.get_aligned_collection(5, mutable=False)) is type(immutable)
        aligned = start.get_aligned_collection(5, mutable=True)
        assert type(aligned) is type(source)
        assert aligned.is_mutable
        assert set(aligned.values) == {5}


def test_daily():
    """Test the daily collections."""
    a_per = AnalysisPeriod(6, 21, 0, 6, 22, 23)
    v1, v2 = 20, 25
    dc1 = DailyCollectionImmutable(
        Header(Temperature(), 'C', a_per), [v1, v2], a_per.doys_int)
    assert dc1.datetimes == tuple(a_per.doys_int)
    assert dc1.values == (v1, v2)
    assert not dc1.is_mutable
    with pytest.raises(AttributeError):
        dc1[0] = 18
    with pytest.raises(AttributeError):
        dc1.values = [18, 24]
    with pytest.raises(Exception):
        dc1.values.append(10)

    dc2 = dc1.to_mutable()
    assert isinstance(dc2, DailyCollection)
    assert dc2.is_mutable
    dc2[0] = 18
    assert dc2[0] == 18
    dc2.values = [18, 24]
    assert dc2.values == (18, 24)
    with pytest.raises(Exception):
        dc2.values.append(10)  # make sure that we can still not append

    dc3 = dc2.to_immutable()
    assert isinstance(dc3, DailyCollectionImmutable)
    assert not dc3.is_mutable

    dc4 = dc3.to_immutable()
    assert isinstance(dc4, DailyCollectionImmutable)
    assert not dc4.is_mutable


def test_monthly():
    """Test the monthly collections."""
    a_per = AnalysisPeriod(6, 1, 0, 7, 31, 23)
    v1, v2 = 20, 25
    dc1 = MonthlyCollectionImmutable(
        Header(Temperature(), 'C', a_per), [v1, v2], a_per.months_int)

    assert dc1.datetimes == tuple(a_per.months_int)
    assert dc1.values == (v1, v2)
    assert not dc1.is_mutable
    with pytest.raises(AttributeError):
        dc1[0] = 18
    with pytest.raises(AttributeError):
        dc1.values = [18, 24]
    with pytest.raises(Exception):
        dc1.values.append(10)

    dc2 = dc1.to_mutable()
    assert isinstance(dc2, MonthlyCollection)
    assert dc2.is_mutable
    dc2[0] = 18
    assert dc2[0] == 18
    dc2.values = [18, 24]
    assert dc2.values == (18, 24)
    with pytest.raises(Exception):
        dc2.values.append(10)  # make sure that we can still not append

    dc3 = dc2.to_immutable()
    assert isinstance(dc3, MonthlyCollectionImmutable)
    assert not dc3.is_mutable

    dc4 = dc3.to_immutable()
    assert isinstance(dc4, MonthlyCollectionImmutable)
    assert not dc4.is_mutable


def test_monthly_per_hour():
    """Test the monthly per hour collections."""
    a_per = AnalysisPeriod(6, 1, 0, 7, 31, 23)
    vals = [20] * 24 + [25] * 24
    dc1 = MonthlyPerHourCollectionImmutable(
        Header(Temperature(), 'C', a_per), vals, a_per.months_per_hour)
    assert dc1.datetimes == tuple(a_per.months_per_hour)
    assert dc1.values == tuple(vals)
    assert not dc1.is_mutable
    with pytest.raises(AttributeError):
        dc1[0] = 18
    with pytest.raises(AttributeError):
        dc1.values = range(48)
    with pytest.raises(Exception):
        dc1.values.append(10)

    dc2 = dc1.to_mutable()
    assert isinstance(dc2, MonthlyPerHourCollection)
    assert dc2.is_mutable
    dc2[0] = 18
    assert dc2[0] == 18
    dc2.values = range(48)
    assert dc2.values == tuple(range(48))
    with pytest.raises(Exception):
        dc2.values.append(10)  # make sure that we can still not append

    dc3 = dc2.to_immutable()
    assert isinstance(dc3, MonthlyPerHourCollectionImmutable)
    assert not dc3.is_mutable

    dc4 = dc3.to_immutable()
    assert isinstance(dc4, MonthlyPerHourCollectionImmutable)
    assert not dc4.is_mutable


def test_get_aligned_collection():
    """Test the method for getting an aligned discontinuous collection."""
    header = Header(Temperature(), 'C', AnalysisPeriod(end_month=1, end_day=1))
    values = list(xrange(24))
    dc1 = HourlyDiscontinuousCollection(header, values,
                                        header.analysis_period.datetimes)
    dc2 = dc1.get_aligned_collection(50, RelativeHumidity(), '%')
    assert dc2.header.data_type.name == 'Relative Humidity'
    assert dc2.header.unit == '%'
    assert isinstance(dc2, HourlyDiscontinuousCollection)
    assert dc2.is_mutable

    dc3 = dc1.get_aligned_collection(50, RelativeHumidity(), '%', mutable=False)
    assert dc3.header.data_type.name == 'Relative Humidity'
    assert dc3.header.unit == '%'
    assert isinstance(dc3, HourlyDiscontinuousCollectionImmutable)
    assert not dc3.is_mutable

    dc4 = dc1.get_aligned_collection(50, RelativeHumidity(), '%', mutable=True)
    assert dc4.header.data_type.name == 'Relative Humidity'
    assert dc4.header.unit == '%'
    assert isinstance(dc4, HourlyDiscontinuousCollection)
    assert dc4.is_mutable


def test_get_aligned_collection_continuous():
    """Test the method for getting an aligned continuous collection."""
    header = Header(Temperature(), 'C', AnalysisPeriod(end_month=1, end_day=1))
    values = list(xrange(24))
    dc1 = HourlyContinuousCollection(header, values)
    dc2 = dc1.get_aligned_collection(50, RelativeHumidity(), '%')
    assert dc2.header.data_type.name == 'Relative Humidity'
    assert dc2.header.unit == '%'
    assert isinstance(dc2, HourlyContinuousCollection)
    assert dc2.is_mutable

    dc3 = dc1.get_aligned_collection(50, RelativeHumidity(), '%', mutable=False)
    assert dc3.header.data_type.name == 'Relative Humidity'
    assert dc3.header.unit == '%'
    assert isinstance(dc3, HourlyContinuousCollectionImmutable)
    assert not dc3.is_mutable

    dc4 = dc1.get_aligned_collection(50, RelativeHumidity(), '%', mutable=True)
    assert dc4.header.data_type.name == 'Relative Humidity'
    assert dc4.header.unit == '%'
    assert isinstance(dc4, HourlyContinuousCollection)
    assert dc4.is_mutable
