# coding=utf-8

import unittest
from ladybug.location import Location
from ladybug.sunpath import Sunpath


class SunpathTestCase(unittest.TestCase):
    """Test for (ladybug/sunpath.py)"""

    # preparing to test.
    def setUp(self):
        """set up."""
        pass

    def tearDown(self):
        """Nothing to tear down as nothing gets written to file."""
        pass

    def test_from_location(self):
        sydney = Location('Sydney', 'AUS', latitude=-33.87, longitude=151.22,
                          time_zone=10)
        sunpath = Sunpath.from_location(sydney)
        self.assertEqual(sunpath.latitude, -33.87)
        self.assertEqual(sunpath.longitude, 151.22)
        self.assertEqual(sunpath.time_zone, 10)

    def test_vs_noaa_new_york(self):
        nyc = Location('New_York', 'USA', latitude=40.72, longitude=-74.02,
                       time_zone=-5)
        sp = Sunpath.from_location(nyc)
        sun = sp.calculate_sun(month=9, day=15, hour=11.0)
        self.assertEqual(round(sun.altitude, 2), 50.35)
        self.assertEqual(round(sun.azimuth, 2), 159.72)

    def test_vs_noaa_sydney(self):
        sydney = Location('Sydney', 'AUS', latitude=-33.87, longitude=151.22,
                          time_zone=10)
        sp = Sunpath.from_location(sydney)
        sun = sp.calculate_sun(month=11, day=15, hour=11.0)
        self.assertEqual(round(sun.altitude, 2), 72.26)
        self.assertEqual(round(sun.azimuth, 2), 32.37)

    def test_sunrise_sunset(self):
        pass

    def test_solar_hour(self):
        pass

    def test_daylight_saving(self):
        pass


if __name__ == "__main__":
    unittest.main()
