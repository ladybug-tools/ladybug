# coding=utf-8

import unittest
from ladybug.analysisperiod import AnalysisPeriod


# class AnalysisPeriodTestCase(unittest.TestCase):
#     """Test for (honeybee/radiance/command/epw2wea.py)"""
#
#     # preparing to test.
#     def setUp(self):
#         """set up."""
#         pass
#
#     def tearDown(self):
#         """Nothing to tear down as nothing gets written to file."""
#         pass
#
#     def test_default_values(self):
#         """Test if the command correctly creates a wea file name as output."""
#         self.assertEqual(self.epw2Wea.outputWeaFile, self.testWea)
#
#
# if __name__ == "__main__":
#     unittest.main()

# # AnalysisPeriod
# ap = AnalysisPeriod()
# dates = ap.datetimes
# print len(dates) == 8760
# hoys = ap.HOYs
# print len(hoys) == 8760
#
# app = AnalysisPeriod.fromAnalysisPeriod(ap)
# print str(app) == "1/1 to 12/31 between 0 to 23 @1"
#
# anp = AnalysisPeriod.fromAnalysisPeriod(str(app))
# print anp
#
# ap = AnalysisPeriod(endMonth=2, endDay=31)
# print ap.endTime.day == 28 and ap.endTime.month == 2

# ap = AnalysisPeriod(stHour=8, endHour=15, endMonth=2, timestep=4)
# print ap.datetimes[1].hour == 8
# print ap.datetimes[1].minute == 15
#
# print ap.datetimes[-1].hour == 15
# print ap.datetimes[-1].minute == 45
