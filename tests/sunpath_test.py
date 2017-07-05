# coding=utf-8

import unittest
from ladybug.location import Location
from ladybug.sunpath import Sunpath

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

# test sunpath
# test defualt inputs
sunpath = Sunpath()
sun = sunpath.calculateSun(month=12, day=21, hour=23)

print round(sun.sunVector.x, 2) == 0.23
print round(sun.sunVector.y, 2) == 0.40
print round(sun.sunVector.z, 2) == 0.89

# test sunpath from location
l = Location()
sunpath = Sunpath.fromLocation(l)
sun = sunpath.calculateSun(month=12, day=21, hour=23)
print round(sun.sunVector.x, 2) == 0.23
print round(sun.sunVector.y, 2) == 0.40
print round(sun.sunVector.z, 2) == 0.89
