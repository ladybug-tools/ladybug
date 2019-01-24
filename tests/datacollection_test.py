# coding=utf-8
from __future__ import division

from ladybug.dt import DateTime
from ladybug.datacollection import HourlyDiscontinuousCollection, \
    HourlyContinuousCollection, MonthlyCollection, DailyCollection, \
    MonthlyPerHourCollection
from ladybug.header import Header
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.datatype.generic import GenericType
from ladybug.datatype.temperature import Temperature
from ladybug.datatype.percentage import RelativeHumidity

import unittest
import pytest
import sys
if (sys.version_info >= (3, 0)):
    xrange = range


class DataCollectionTestCase(unittest.TestCase):
    """Test for (ladybug/datacollection.py)"""

    # preparing to test.
    def setUp(self):
        """set up."""

    def tearDown(self):
        """Nothing to tear down as nothing gets written to file."""
        pass

    def test_init(self):
        """Test the init methods for dicontinuous collections."""
        # setup AnalysisPeriod
        a_per = AnalysisPeriod(6, 21, 12, 6, 21, 13)
        # Setup Datetimes
        dt1 = DateTime(6, 21, 12)
        dt2 = DateTime(6, 21, 13)
        # Define temperature values
        v1 = 20
        v2 = 25
        avg = (v1 + v2) / 2
        # Setup temperature data collection
        dc1 = HourlyDiscontinuousCollection(Header(Temperature(), 'C', a_per),
                                            [v1, v2], [dt1, dt2])

        assert dc1.datetimes == (dt1, dt2)
        assert dc1.values == (v1, v2)
        assert dc1.average == avg

    def test_init_continuous(self):
        """Test the init methods for continuous collections"""
        # Setup temperature data collection
        header = Header(Temperature(), 'C', AnalysisPeriod())
        values = list(xrange(8760))
        dc1 = HourlyContinuousCollection(header, values)

        assert len(dc1.datetimes) == 8760
        assert list(dc1.values) == list(xrange(8760))
        assert dc1.average == 4379.5

    def test_init_continuous_incorrect(self):
        """Test the init methods for continuous collections with incorrect values"""
        header = Header(Temperature(), 'C', AnalysisPeriod())
        values = list(xrange(10))
        with pytest.raises(Exception):
            HourlyContinuousCollection(header, values)

    def test_setting_values(self):
        """Test the methods for setting values on the data collection"""
        header = Header(Temperature(), 'C', AnalysisPeriod())
        values = list(xrange(8760))
        dc = HourlyDiscontinuousCollection(header, values,
                                           header.analysis_period.datetimes)
        # test setting individual values
        assert dc[0] == 0
        dc[0] = 10
        assert dc[0] == 10

        val_rev = list(reversed(values))
        dc.values = val_rev
        assert dc[0] == 8759

    def test_setting_values_continuous(self):
        """Test the methods for setting values on the continuous data collection"""
        header = Header(Temperature(), 'C', AnalysisPeriod())
        values = list(xrange(8760))
        dc = HourlyContinuousCollection(header, values)
        assert dc[0] == 0
        val_rev = list(reversed(values))
        dc.values = val_rev
        assert dc[0] == 8759

    def test_bounds(self):
        """Test the bounds method."""
        header1 = Header(Temperature(), 'C', AnalysisPeriod())
        values = list(xrange(8760))
        dc1 = HourlyContinuousCollection(header1, values)
        min, max = dc1.bounds
        assert min == 0
        assert max == 8759

    def test_min_max(self):
        """Test the min and max methods."""
        header1 = Header(Temperature(), 'C', AnalysisPeriod())
        values = list(xrange(10, 8770))
        dc = HourlyContinuousCollection(header1, values)
        assert dc.min == 10
        assert dc.max == 8769

    def test_average_median(self):
        """Test the average and median methods."""
        header1 = Header(Temperature(), 'C', AnalysisPeriod())
        values = list(xrange(8760))
        dc = HourlyContinuousCollection(header1, values)
        assert dc.average == dc.median == 4379.5
        dc[0] = -10000
        assert dc.average == pytest.approx(4378.35844, rel=1e-3)
        assert dc.median == 4379.5

    def test_total(self):
        """Test the total method."""
        header1 = Header(Temperature(), 'C', AnalysisPeriod())
        values = [1] * 8760
        dc = HourlyContinuousCollection(header1, values)
        assert dc.total == 8760

    def test_to_unit(self):
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

    def test_to_ip_si(self):
        """Test the conversion of DataCollection to IP and SI units."""
        header1 = Header(Temperature(), 'C', AnalysisPeriod())
        values = [20] * 8760
        dc1 = HourlyContinuousCollection(header1, values)
        dc2 = dc1.to_ip()
        dc3 = dc2.to_si()
        assert dc1.values[0] == 20
        assert dc2.values[0] == 68
        assert dc3.values[0] == dc1.values[0]

    def test_get_highest_values(self):
        header = Header(Temperature(), 'C', AnalysisPeriod())
        test_data = list(xrange(8760))
        test_count = len(test_data)/2
        dc3 = HourlyContinuousCollection(header, test_data)

        test_highest_values, test_highest_values_index = \
            dc3.get_highest_values(test_count)

        assert test_highest_values == list(reversed(test_data[4380:8760]))
        assert test_highest_values_index == list(xrange(8759, 4379, -1))

    def test_get_percentile(self):
        """Test the get_percentile method."""
        header1 = Header(Temperature(), 'C', AnalysisPeriod())
        values = list(xrange(8760))
        dc = HourlyContinuousCollection(header1, values)

        assert dc.get_percentile(0) == 0
        assert dc.get_percentile(25) == 2189.75
        assert dc.get_percentile(50) == 4379.5
        assert dc.get_percentile(75) == 6569.25
        assert dc.get_percentile(100) == 8759

        with pytest.raises(Exception):
            dc.get_percentile(-10)
        with pytest.raises(Exception):
            dc.get_percentile(110)

    def test_is_in_range_data_type(self):
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
        assert dc1._is_in_data_type_range(raise_exception=False) is True
        assert dc2._is_in_data_type_range(raise_exception=False) is False
        assert dc3._is_in_data_type_range(raise_exception=False) is True
        assert dc4._is_in_data_type_range(raise_exception=False) is False

    def test_is_in_range_epw(self):
        """Test the function to check whether values are in range for an EPW."""
        header1 = Header(RelativeHumidity(), '%', AnalysisPeriod())
        header2 = Header(RelativeHumidity(), 'fraction', AnalysisPeriod())
        val1 = [50] * 8760
        val2 = [150] * 8760
        val3 = [0.5] * 8760
        val4 = [1.5] * 8760
        dc1 = HourlyContinuousCollection(header1, val1)
        dc2 = HourlyContinuousCollection(header1, val2)
        dc3 = HourlyContinuousCollection(header2, val3)
        dc4 = HourlyContinuousCollection(header2, val4)
        assert dc1._is_in_epw_range(raise_exception=False) is True
        assert dc2._is_in_epw_range(raise_exception=False) is False
        assert dc3._is_in_epw_range(raise_exception=False) is True
        assert dc4._is_in_epw_range(raise_exception=False) is False

    def test_interpolation(self):
        # To test an annual data collection, we will just use a range of values
        values = list(xrange(24))
        test_header = Header(GenericType('Test Type', 'test'), 'test',
                             AnalysisPeriod(end_month=1, end_day=1))
        dc2 = HourlyContinuousCollection(test_header, values)

        # check the interpolate data functions
        interp_coll1 = dc2.interpolate_data(2)
        interp_coll2 = dc2.interpolate_data(2, True)
        assert interp_coll1[1] == 0.5
        assert interp_coll2[1] == 0.25

    def test_json_methods(self):
        header = Header(Temperature(), 'C', AnalysisPeriod(end_month=1, end_day=1))
        values = list(xrange(24))
        dc = HourlyContinuousCollection(header, values)
        dc_json = dc.to_json()
        reconstruced_dc = HourlyContinuousCollection.from_json(dc_json)

        assert dc_json == reconstruced_dc.to_json()


if __name__ == "__main__":
    unittest.main()
