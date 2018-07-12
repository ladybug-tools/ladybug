# coding=utf-8

import unittest
from ladybug.analysisperiod import AnalysisPeriod


class AnalysisPeriodTestCase(unittest.TestCase):
    """Test for (analysisperiod.py)"""

    # preparing to test.
    def setUp(self):
        """set up."""
        pass

    def tearDown(self):
        """Nothing to tear down as nothing gets written to file."""
        pass

    def test_default_values(self):
        """Test the default values."""
        ap = AnalysisPeriod()
        assert ap.st_hour == 0
        assert ap.end_hour == 23
        assert ap.st_month == 1
        assert ap.end_month == 12
        assert ap.st_day == 1
        assert ap.end_day == 31
        assert ap.timestep == 1
        assert len(ap.datetimes) == 8760

    def test_from_string(self):
        """Test creating analysis priod from a string."""
        ap_string = '2/21 to 3/22 between 5 to 17 @1'
        ap = AnalysisPeriod.from_string(ap_string)
        assert ap.st_hour == 5
        assert ap.end_hour == 17
        assert ap.st_month == 2
        assert ap.end_month == 3
        assert ap.st_day == 21
        assert ap.end_day == 22
        assert ap.timestep == 1

    def test_is_annual(self):
        annual_ap = AnalysisPeriod()
        not_annual_ap = AnalysisPeriod(end_month=2)
        assert annual_ap.is_annual
        assert not not_annual_ap.is_annual

    def test_include_last_hour(self):
        """Test that analysis period includes the last hour.

        see:
        https://github.com/ladybug-tools/ladybug-dynamo/issues/12#issuecomment-224125154
        """
        ap = AnalysisPeriod(7, 21, 9, 7, 21, 15, 4)
        last_hour = ap.datetimes[-1]
        assert last_hour.hour == 15
        assert last_hour.minute == 0
        assert len(ap) == 25

    def test_default_values_leap_year(self):
        """Test the default values."""
        ap = AnalysisPeriod(is_leap_year=True)
        assert ap.st_hour == 0
        assert ap.end_hour == 23
        assert ap.st_month == 1
        assert ap.end_month == 12
        assert ap.st_day == 1
        assert ap.end_day == 31
        assert ap.timestep == 1
        assert len(ap.datetimes) == 8784

    def test_from_string_leap_year(self):
        """Test creating analysis priod from a string."""
        ap_string = '2/21 to 3/22 between 5 to 17 @1*'
        ap = AnalysisPeriod.from_string(ap_string)
        assert ap.st_hour == 5
        assert ap.end_hour == 17
        assert ap.st_month == 2
        assert ap.end_month == 3
        assert ap.st_day == 21
        assert ap.end_day == 22
        assert ap.timestep == 1

    def test_is_annual_leap_year(self):
        annual_ap = AnalysisPeriod(is_leap_year=True)
        not_annual_ap = AnalysisPeriod(end_month=2, is_leap_year=True)
        assert annual_ap.is_annual
        assert not not_annual_ap.is_annual


if __name__ == "__main__":
    unittest.main()
