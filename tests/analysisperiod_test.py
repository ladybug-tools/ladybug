# coding=utf-8

from ladybug.analysisperiod import AnalysisPeriod
from ladybug.dt import DateTime

from datetime import timedelta
import unittest
import sys
if (sys.version_info >= (3, 0)):
    xrange = range


class AnalysisPeriodTestCase(unittest.TestCase):
    """Test for (analysisperiod.py)"""

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
        assert ap.is_leap_year is False
        assert len(ap.datetimes) == 8760

    def test_from_string(self):
        """Test creating analysis priod from a string."""
        ap_string = '2/21 to 3/22 between 5 to 17 @1'
        ap = AnalysisPeriod.from_analysis_period(ap_string)
        ap = AnalysisPeriod.from_string(ap_string)
        assert ap.st_hour == 5
        assert ap.end_hour == 17
        assert ap.st_month == 2
        assert ap.end_month == 3
        assert ap.st_day == 21
        assert ap.end_day == 22
        assert ap.timestep == 1

    def test_is_annual(self):
        """Test the is_annual property."""
        annual_ap = AnalysisPeriod()
        not_annual_ap = AnalysisPeriod(end_month=2)
        assert annual_ap.is_annual
        assert not not_annual_ap.is_annual

    def test_to_from_json(self):
        """Test the json methods of the AnalysisPeriod."""
        ap = AnalysisPeriod(st_month=2)
        ap_json = ap.to_json()
        rebuilt_ap = AnalysisPeriod.from_json(ap_json)
        assert rebuilt_ap.st_month == 2
        assert rebuilt_ap.to_json() == ap_json

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

    def test_moys_hoys_hoys_int(self):
        """Test the moys, hoys, and hoys_int properties."""
        ap = AnalysisPeriod(timestep=4)
        assert ap.moys[1] == 15
        assert ap.hoys[1] == 0.25
        assert ap.hoys_int[1] == 0
        assert isinstance(ap.hoys[1], float)
        assert isinstance(ap.hoys_int[1], int)
        assert len(ap.moys) == len(ap.hoys) == len(ap.hoys_int)

    def test_doys_int(self):
        """Test the doys_int property."""
        ap = AnalysisPeriod()
        ap_2 = AnalysisPeriod(st_month=2)
        assert ap.doys_int == list(xrange(1, 366))
        assert ap_2.doys_int == list(xrange(32, 366))

    def test_months_int(self):
        """Test the months_int property."""
        ap = AnalysisPeriod()
        ap_2 = AnalysisPeriod(st_month=2)
        assert ap.months_int == list(xrange(1, 13))
        assert ap_2.months_int == list(xrange(2, 13))

    def test_months_per_hour(self):
        """Test the months_per_hour property."""
        ap = AnalysisPeriod()
        ap_2 = AnalysisPeriod(st_month=2)
        ap_3 = AnalysisPeriod(st_hour=5)
        assert len(ap.months_per_hour) == 12 * 24
        assert len(ap_2.months_per_hour) == 11 * 24
        assert len(ap_3.months_per_hour) == 12 * 19

    def test_minute_intervals(self):
        """Test the minute_intervals property."""
        ap = AnalysisPeriod()
        ap_2 = AnalysisPeriod(timestep=6)
        assert ap.minute_intervals == timedelta(minutes=60)
        assert ap_2.minute_intervals == timedelta(minutes=10)

    def test_is_reversed(self):
        """Test the is_reversed property."""
        ap = AnalysisPeriod()
        ap_2 = AnalysisPeriod(st_month=6, end_month=2)
        assert not ap.is_reversed
        assert ap_2.is_reversed

    def test_is_overnight(self):
        """Test the is_overnight property."""
        ap = AnalysisPeriod()
        ap_2 = AnalysisPeriod(st_hour=20, end_hour=5)
        assert not ap.is_overnight
        assert ap_2.is_overnight

    def test_is_time_included(self):
        """Test the is_time_included method."""
        ap = AnalysisPeriod(st_month=2, end_month=6)
        assert ap.is_time_included(DateTime(5, 18, 17))
        assert not ap.is_time_included(DateTime(1, 10, 12))

    def test_duplicate(self):
        """Test the duplicate method."""
        ap = AnalysisPeriod()
        ap_2 = ap.duplicate()
        assert ap_2 == ap

    def test_0_end_hour(self):
        """Test hour 0 for end hour."""
        params = [1, 1, 1, 1, 2, 0]
        ap = AnalysisPeriod(*params)
        assert ap.end_hour == 0
        assert len(ap) == 24

if __name__ == "__main__":
    unittest.main()
