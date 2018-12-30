# coding=utf-8

import unittest
import pytest
from ladybug.datapoint import DataPoint
from ladybug.dt import DateTime
from ladybug.datacollection import DataCollection
from ladybug.header import Header
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.datatype import Temperature
from ladybug.datatype import RelativeHumidity


class DataCollectionTestCase(unittest.TestCase):
    """Test for (ladybug/datacollection.py)"""

    # preparing to test.
    def setUp(self):
        """set up."""

    def tearDown(self):
        """Nothing to tear down as nothing gets written to file."""
        pass

    def test_init(self):
        """Test the init methods to ensure self object creation"""
        # Setup Datetimes
        dt1 = DateTime(6, 21, 12, 0)
        dt2 = DateTime(9, 21, 12, 0)
        # Define temperature values
        v1 = 20
        v2 = 30
        average = (v1 + v2) / 2
        # Setup temperature datatypes
        t1 = DataPoint(v1, dt1)
        t2 = DataPoint(v2, dt2)

        with pytest.raises(Exception):
            DataCollection(3)
        with pytest.raises(Exception):
            DataCollection([t1, 2, 3, 4])

        dc1 = DataCollection([t1, t2])
        # dc_from_data_and_datetimes = \
        # DataCollection.from_data_and_datetimes([v1, v2], [dt1, dt2])
        assert dc1.datetimes == (dt1, dt2)
        assert dc1.data == [v1, v2]
        assert dc1.average_data() == average

    def test_to_unit(self):
        """Test the conversion of DataCollection units."""
        # Setup Datetimes
        vals = [20]
        dc1 = DataCollection.from_list(vals, Temperature(), 'C')
        dc2 = DataCollection.from_list(vals, Temperature(), 'F')
        dc3 = dc1.to_unit('K')
        dc4 = dc2.to_unit('K')
        assert dc1.values[0] == 20
        assert dc3.values[0] == 293.15
        assert dc2.values[0] == 20
        assert dc4.values[0] == pytest.approx(266.483, rel=1e-1)

    def test_to_ip_si(self):
        """Test the conversion of DataCollection to IP and SI units."""
        # Setup Datetimes
        vals = [20]
        dc1 = DataCollection.from_list(vals, Temperature(), 'C')
        dc2 = dc1.to_ip()
        dc3 = dc2.to_si()
        assert dc1.values[0] == 20
        assert dc2.values[0] == 68
        assert dc3.values[0] == dc1.values[0]

    def test_is_in_range(self):
        """Test the function to check whether values are in a specific range."""
        val1 = [50]
        dc1 = DataCollection.from_list(val1, Temperature(), 'C')
        assert dc1.is_in_range(0, 100) is True
        assert dc1.is_in_range(0, 30) is False

    def test_is_in_range_data_type(self):
        """Test the function to check whether values are in range for the data_type."""
        val1 = [20]
        val2 = [-300]
        val3 = [270]
        val4 = [-10]
        dc1 = DataCollection.from_list(val1, Temperature(), 'C')
        dc2 = DataCollection.from_list(val2, Temperature(), 'C')
        dc3 = DataCollection.from_list(val3, Temperature(), 'K')
        dc4 = DataCollection.from_list(val4, Temperature(), 'K')
        assert dc1.is_in_range_data_type() is True
        assert dc2.is_in_range_data_type() is False
        assert dc3.is_in_range_data_type() is True
        assert dc4.is_in_range_data_type() is False

    def test_is_in_range_epw(self):
        """Test the function to check whether values are in range for an EPW."""
        val1 = [50]
        val2 = [150]
        val3 = [0.5]
        val4 = [1.5]
        dc1 = DataCollection.from_list(val1, RelativeHumidity(), '%')
        dc2 = DataCollection.from_list(val2, RelativeHumidity(), '%')
        dc3 = DataCollection.from_list(val3, RelativeHumidity(), 'fraction')
        dc4 = DataCollection.from_list(val4, RelativeHumidity(), 'fraction')
        assert dc1.is_in_range_epw() is True
        assert dc2.is_in_range_epw() is False
        assert dc3.is_in_range_epw() is True
        assert dc4.is_in_range_epw() is False

    def test_interpolation(self):
        # To test an annual data collection, we will just use a range of values
        test_data = range(8760)
        ap = AnalysisPeriod()
        test_header = Header(
            data_type='Test Type', unit=None, analysis_period=ap, location=None)
        dc2 = DataCollection.from_data_and_analysis_period(test_data, ap, test_header)

        # check the interpolate data functions
        assert dc2.interpolate_data(2)[1] == 0.5
        assert dc2.interpolate_data(2, True)[1] == 0.25

    def test_json_methods(self):
        pass
        # I leave the test here as a TODO
        # assert dc.to_json() == dc_from_data_and_datetimes.to_json()

    def test_get_highest_values(self):
        # To test get_highest_values, a range of yearly-hour values will be used
        test_data = list(range(8760))
        test_data = [i * 5 for i in test_data]
        test_count = len(test_data)/2

        dc3 = DataCollection.from_list(lst=test_data)

        test_highest_values, test_highest_values_index = \
            dc3.get_highest_values(test_count)

        assert test_highest_values == list(reversed(test_data[4380:8760]))
        assert test_highest_values_index == list(range(8759, 4379, -1))


if __name__ == "__main__":
    unittest.main()
