# coding=utf-8

import unittest
from ladybug.location import Location


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

# # test for location
# # create default location
# l = Location()
# print l
#
# # set values
# l.city = "Tehran"
# l.latitude = 10
# l.longitude = -10
# l.timezone = +5
# l.elevation = 1200
#
# print l
#
# # import from epw file
# _epwFile = 'C:\EnergyPlusV8-3-0\WeatherData\USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw'
# epwData = EPW(_epwFile)
# l = epwData.location
# print "\n"
# print l.city == "San Francisco Intl Ap"
# print l.latitude == 37.62
# print l.longitude == -122.4
# print l.timezone == -8
# print l.elevation == 2
#
# # check different import options
# l1 = Location.fromLocation(epwData.location)
# l2 = Location.fromLocation(str(epwData.location))
# l3 = Location.fromLocation(repr(epwData.location))
#
# print l1, "\n_____\n",l2 , "\n_____\n", l3
