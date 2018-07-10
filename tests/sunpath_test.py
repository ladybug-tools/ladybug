# coding=utf-8

import unittest
from ladybug.location import Location
from ladybug.sunpath import Sunpath
from ladybug.dt import DateTime


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
        assert sunpath.latitude == -33.87
        assert sunpath.longitude == 151.22
        assert sunpath.time_zone == 10

    def test_vs_noaa_new_york(self):
        nyc = Location('New_York', 'USA', latitude=40.72, longitude=-74.02,
                       time_zone=-5)
        sp = Sunpath.from_location(nyc)
        sun = sp.calculate_sun(month=9, day=15, hour=11.0)
        assert round(sun.altitude, 2) == 50.35
        assert round(sun.azimuth, 2) == 159.72

    def test_vs_noaa_sydney(self):
        sydney = Location('Sydney', 'AUS', latitude=-33.87, longitude=151.22,
                          time_zone=10)
        sp = Sunpath.from_location(sydney)
        sun = sp.calculate_sun(month=11, day=15, hour=11.0)
        assert round(sun.altitude, 2) == 72.26
        assert round(sun.azimuth, 2) == 32.37

    def test_sunrise_sunset(self):
        pass

    def test_solar_hour(self):
        pass

    def test_daylight_saving(self):
        nyc = Location('New_York', 'USA', latitude=40.72, longitude=-74.02,
                       time_zone=-5)
        sp = Sunpath.from_location(nyc)
        dt1 = DateTime(6, 21, 12, 0)
        dt2 = DateTime(12, 21, 12, 0)
        # TODO(mostapha): This is not implemented yet
        # assert sp.is_daylight_saving_hour(dt1) is True
        assert sp.is_daylight_saving_hour(dt1) is False
        assert sp.is_daylight_saving_hour(dt2) is False

    def test_leap_year(self):
        nyc = Location('New_York', 'USA', latitude=40.72, longitude=-74.02,
                       time_zone=-5)
        sp = Sunpath.from_location(nyc)
        sp.is_leap_year = True
        sun = sp.calculate_sun(month=2, day=29, hour=11.0)
        assert sun.datetime == DateTime(2, 29, 11, leap_year=True)
        assert sun.datetime.year == 2016
        assert sun.datetime.month == 2
        assert sun.datetime.day == 29
        assert sun.datetime.hour == 11


if __name__ == "__main__":
    unittest.main()
