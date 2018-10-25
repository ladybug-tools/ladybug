# coding=utf-8

import unittest
import pytest
from ladybug.datatype import DryBulbTemperature
from ladybug.dt import DateTime
from ladybug.datacollection import DataCollection
from ladybug.header import Header
from ladybug.analysisperiod import AnalysisPeriod


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
        t1 = DryBulbTemperature(v1, dt1)
        t2 = DryBulbTemperature(v2, dt2)

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

    def test_interpolation(self):
        # To test an annual data collection, we will just use a range of values
        test_data = range(8760)
        ap = AnalysisPeriod()
        test_header = Header(None, None, None, ap, False)
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
