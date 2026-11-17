# coding=utf-8
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.datautil import (
    collections_from_csv, collections_from_json, collections_from_pkl,
    collections_to_csv, collections_to_json, collections_to_pkl
)
from ladybug.datacollection import (
    DailyCollection, HourlyContinuousCollection, HourlyDiscontinuousCollection,
    MonthlyCollection, MonthlyPerHourCollection
)
from ladybug.datatype.temperature import Temperature
from ladybug.dt import DateTime
from ladybug.header import Header

import pytest


def _collection_samples():
    temp = Temperature()
    hourly_ap = AnalysisPeriod(1, 1, 0, 1, 1, 23)
    daily_ap = AnalysisPeriod(1, 1, 0, 1, 2, 23)
    monthly_ap = AnalysisPeriod(1, 1, 0, 2, 28, 23)

    return [
        HourlyContinuousCollection(
            Header(temp, 'C', hourly_ap), list(range(24))),
        HourlyDiscontinuousCollection(
            Header(temp, 'C', hourly_ap), [1, 2],
            [DateTime(1, 1, 0), DateTime(1, 1, 23)]),
        DailyCollection(Header(temp, 'C', daily_ap), [1, 2], [1, 2]),
        MonthlyCollection(Header(temp, 'C', monthly_ap), [1, 2], [1, 2]),
        MonthlyPerHourCollection(
            Header(temp, 'C', hourly_ap), [1, 2], [(1, 0, 0), (1, 23, 0)])
    ]


def _assert_same_collections(actual, expected):
    assert len(actual) == len(expected)
    for result, original in zip(actual, expected):
        assert type(result) is type(original)
        assert result.values == original.values
        assert result.datetime_strings == original.datetime_strings
        assert result.header.to_dict() == original.header.to_dict()


def test_collections_to_from_json_round_trip(tmp_path):
    collections = _collection_samples()
    output_folder = tmp_path / 'json'
    path = collections_to_json(collections, str(output_folder), 'weather')

    assert path.endswith('weather.json')
    _assert_same_collections(collections_from_json(path), collections)


def test_collections_to_from_pkl_round_trip(tmp_path):
    collections = _collection_samples()
    output_folder = tmp_path / 'pkl'
    path = collections_to_pkl(collections, str(output_folder), 'weather')

    assert path.endswith('weather.pkl')
    _assert_same_collections(collections_from_pkl(path), collections)


def test_collections_to_from_csv_round_trip(tmp_path):
    for collection in _collection_samples():
        output_folder = tmp_path / 'csv'
        path = collections_to_csv([collection], str(output_folder), 'weather')

        assert path.endswith('weather.csv')
        _assert_same_collections(
            collections_from_csv(path), [collection])


def test_collections_to_from_csv_round_trip_multiple_aligned_collections(tmp_path):
    analysis_period = AnalysisPeriod(1, 1, 0, 1, 1, 23)
    first = HourlyContinuousCollection(
        Header(Temperature(), 'C', analysis_period), list(range(24)))
    second = HourlyContinuousCollection(
        Header(Temperature(), 'C', analysis_period), list(range(24, 48)))
    collections = [first, second]

    path = collections_to_csv(collections, str(tmp_path / 'aligned'), 'aligned')
    _assert_same_collections(collections_from_csv(path), collections)


def test_collections_from_json_rejects_unknown_collection_type(tmp_path):
    path = tmp_path / 'unknown.json'
    path.write_text('[{"type": "Unknown"}]', encoding='utf-8')

    with pytest.raises(ValueError, match='Unrecognized data collection type'):
        collections_from_json(str(path))
