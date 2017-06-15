# coding=utf-8

import unittest
from ladybug.epw import EPW


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

# # epw
# epwData = EPW("C:\EnergyPlusV8-3-0\WeatherData\USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw")

# analysisPeriod = AnalysisPeriod.fromAnalysisPeriod(None)
#
# # print epwData.location
# data = epwData.dryBulbTemperature.filterByAnalysisPeriod(analysisPeriod).values()
# print len(data) == 8760

# print DateTime.fromMoy(1395 + 47).moy
# ap = AnalysisPeriod(stMonth=1, stDay=31, stHour=21, \
#                     endMonth=2, endDay=1, endHour=10, timestep=4)
#
# dewTemp = epwData.dewPointTemperature.filterByAnalysisPeriod(ap)

# print dewTemp[0], dewTemp[1], dewTemp[-2], dewTemp[-1]

# ap = AnalysisPeriod(stMonth=1, stDay=1, stHour=0, \
#                      endMonth=1, endDay=31, endHour=23, timestep=3)
#
# dewTemp.filterByAnalysisPeriod(ap).values(header=True)
# print len(dewTemp) == 31 * 24 + 1
