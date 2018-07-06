# coding=utf-8

import unittest
import os
from ladybug.wea import Wea


class EPWTestCase(unittest.TestCase):
    """Test for (ladybug/epw.py)"""

    # preparing to test.
    def setUp(self):
        """set up."""
        pass

    def tearDown(self):
        """Nothing to tear down as nothing gets written to file."""
        pass

    def test_from_epw(self):
        """Test import from epw"""
        epw_path = './tests/epw/chicago.epw'
        wea_from_epw = Wea.from_epw_file(epw_path)

        assert wea_from_epw.location.city == 'Chicago Ohare Intl Ap'
        assert wea_from_epw.timestep == 1

    def test_from_stat(self):
        """Test import from stat"""
        stat_path = './tests/stat/chicago.stat'
        wea_from_stat = Wea.from_stat_file(stat_path)

        assert wea_from_stat.location.city == 'Chicago Ohare Intl Ap'
        assert wea_from_stat.timestep == 1

    def test_json_methods(self):
        """Test JSON serialization methods"""
        epw_path = './tests/epw/chicago.epw'
        wea = Wea.from_epw_file(epw_path)

        assert wea.to_json() == Wea.from_json(wea.to_json()).to_json()

    def test_import_epw(self):
        """Test compare import from epw and stat."""
        epw_path = './tests/epw/chicago.epw'

        wea_from_epw = Wea.from_epw_file(epw_path)

        wea_json = wea_from_epw.to_json()
        wea_from_json = Wea.from_json(wea_json)
        assert wea_from_json.direct_normal_radiation.values == \
            wea_from_epw.direct_normal_radiation.values
        assert wea_from_json.diffuse_horizontal_radiation.values == \
            wea_from_epw.diffuse_horizontal_radiation.values

    def test_import_stat(self):
        """Test compare import from epw and stat."""
        stat_path = './tests/stat/chicago.stat'
        wea_from_stat = Wea.from_stat_file(stat_path)

        wea_json = wea_from_stat.to_json()
        wea_from_json = Wea.from_json(wea_json)
        assert wea_from_json.direct_normal_radiation.values == \
            wea_from_stat.direct_normal_radiation.values
        assert wea_from_json.diffuse_horizontal_radiation.values == \
            wea_from_stat.diffuse_horizontal_radiation.values

    def test_radiation_on_surface(self):
        pass

    def test_write(self):
        pass


if __name__ == "__main__":
    unittest.main()
