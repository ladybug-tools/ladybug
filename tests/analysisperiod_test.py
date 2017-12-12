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
        self.assertEqual(ap.st_hour, 0)
        self.assertEqual(ap.end_hour, 23)
        self.assertEqual(ap.st_month, 1)
        self.assertEqual(ap.end_month, 12)
        self.assertEqual(ap.st_day, 1)
        self.assertEqual(ap.end_day, 31)
        self.assertEqual(ap.timestep, 1)
        self.assertTrue(len(ap.datetimes) == 8760)
        self.assertTrue(len(ap.datetimes) == 8760)

    def test_from_string(self):
        """Test creating analysis priod from a string."""
        ap_string = '2/21 to 3/22 between 5 to 17 @1'
        ap = AnalysisPeriod.from_string(ap_string)
        self.assertEqual(ap.st_hour, 5)
        self.assertEqual(ap.end_hour, 17)
        self.assertEqual(ap.st_month, 2)
        self.assertEqual(ap.end_month, 3)
        self.assertEqual(ap.st_day, 21)
        self.assertEqual(ap.end_day, 22)
        self.assertEqual(ap.timestep, 1)

    def test_is_annual(self):
        annual_ap = AnalysisPeriod()
        not_annual_ap = AnalysisPeriod(end_month=2)
        self.assertTrue(annual_ap.is_annual)
        self.assertFalse(not_annual_ap.is_annual)

    def test_include_last_hour(self):
        """Test that analysis period includes the last hour.

        see:
        https://github.com/ladybug-tools/ladybug-dynamo/issues/12#issuecomment-224125154
        """
        ap = AnalysisPeriod(7, 21, 9, 7, 21, 15, 4)
        last_hour = ap.datetimes[-1]
        self.assertEqual(last_hour.hour, 15)
        self.assertEqual(last_hour.minute, 0)
        self.assertEqual(len(ap), 25)


if __name__ == "__main__":
    unittest.main()
