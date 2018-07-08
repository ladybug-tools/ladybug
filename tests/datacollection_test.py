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
        assert dc1.values == [v1, v2]
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


if __name__ == "__main__":
    unittest.main()
