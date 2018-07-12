# coding=utf-8

import unittest
import pytest

from ladybug.wea import Wea
from ladybug.location import Location


class WeaTestCase(unittest.TestCase):
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
        assert wea_from_epw.direct_normal_radiation[7] == 22
        assert wea_from_epw.direct_normal_radiation[7].datetime.hour == 7
        assert wea_from_epw.direct_normal_radiation[7].datetime.minute == 30
        assert wea_from_epw.direct_normal_radiation[8] == 397
        assert wea_from_epw.direct_normal_radiation[8].datetime.hour == 8
        assert wea_from_epw.direct_normal_radiation[8].datetime.minute == 30
        # diffuse horizontal radiation
        assert wea_from_epw.diffuse_horizontal_radiation[7] == 10
        assert wea_from_epw.diffuse_horizontal_radiation[7].datetime.hour == 7
        assert wea_from_epw.diffuse_horizontal_radiation[7].datetime.minute == 30
        assert wea_from_epw.diffuse_horizontal_radiation[8] == 47
        assert wea_from_epw.diffuse_horizontal_radiation[8].datetime.hour == 8
        assert wea_from_epw.diffuse_horizontal_radiation[8].datetime.minute == 30

    def test_from_stat(self):
        """Test import from stat"""
        stat_path = './tests/stat/chicago.stat'
        wea_from_stat = Wea.from_stat_file(stat_path)

        assert wea_from_stat.location.city == 'Chicago Ohare Intl Ap'
        assert wea_from_stat.timestep == 1
        assert wea_from_stat.diffuse_horizontal_radiation[0].value == \
            pytest.approx(0, rel=1e-3)
        assert wea_from_stat.direct_normal_radiation[0].value == \
            pytest.approx(0, rel=1e-3)
        assert wea_from_stat.diffuse_horizontal_radiation[12].value == \
            pytest.approx(87.44171, rel=1e-3)
        assert wea_from_stat.direct_normal_radiation[12].value == \
            pytest.approx(810.693919, rel=1e-3)

    def test_from_clear_sky(self):
        """Test from original clear sky"""
        location = Location(
            'Chicago Ohare Intl Ap', 'USA', 41.98, -87.92, -6.0, 201.0)
        wea_from_clear_sky = Wea.from_ashrae_clear_sky(location)

        assert wea_from_clear_sky.location.city == 'Chicago Ohare Intl Ap'
        assert wea_from_clear_sky.timestep == 1
        assert wea_from_clear_sky.diffuse_horizontal_radiation[0].value == \
            pytest.approx(0, rel=1e-3)
        assert wea_from_clear_sky.direct_normal_radiation[0].value == \
            pytest.approx(0, rel=1e-3)
        assert wea_from_clear_sky.diffuse_horizontal_radiation[12].value == \
            pytest.approx(60.72258, rel=1e-3)
        assert wea_from_clear_sky.direct_normal_radiation[12].value == \
            pytest.approx(857.00439, rel=1e-3)

    def test_from_zhang_huang(self):
        """Test from zhang huang solar model"""
        location = Location(
            'Chicago Ohare Intl Ap', 'USA', 41.98, -87.92, -6.0, 201.0)

        cc = [0.5] * 8760
        rh = [50] * 8760
        dbt = [20] * 8760
        ws = [2] * 8760
        wea_from_zh = Wea.from_zhang_huang_solar_model(location, cc, rh, dbt, ws)

        assert wea_from_zh.location.city == 'Chicago Ohare Intl Ap'
        assert wea_from_zh.timestep == 1
        assert wea_from_zh.global_horizontal_radiation[0].value == \
            pytest.approx(0, rel=1e-3)
        assert wea_from_zh.global_horizontal_radiation[12].value == \
            pytest.approx(281.97887, rel=1e-3)
        # TODO: Add checks for direct normal and diffuse once perez split is finished

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

    def test_global_horizontal(self):
        """Test the global horizontal radiation on method."""
        stat_path = './tests/stat/chicago.stat'
        wea_from_stat = Wea.from_stat_file(stat_path)

        diffuse_horiz_rad = wea_from_stat.diffuse_horizontal_radiation
        direct_horiz_rad = wea_from_stat.direct_horizontal_radiation
        glob_horiz_rad = wea_from_stat.global_horizontal_radiation

        assert [x.value for x in glob_horiz_rad] == pytest.approx(
            [x + y for x, y in zip(diffuse_horiz_rad, direct_horiz_rad)], rel=1e-3)

    def test_directional_radiation(self):
        """Test the directinal radiation method."""
        stat_path = './tests/stat/chicago.stat'
        wea_from_stat = Wea.from_stat_file(stat_path)

        srf_total, srf_direct, srf_diffuse, srf_reflect = \
            wea_from_stat.directional_radiation(90)
        diffuse_horiz_rad = wea_from_stat.diffuse_horizontal_radiation
        direct_horiz_rad = wea_from_stat.direct_horizontal_radiation
        glob_horiz_rad = wea_from_stat.global_horizontal_radiation

        assert [x.value for x in srf_total] == pytest.approx(
            [x.value for x in glob_horiz_rad], rel=1e-3)
        assert [x.value for x in srf_direct] == pytest.approx(
            [x.value for x in direct_horiz_rad], rel=1e-3)
        assert [x.value for x in srf_diffuse] == pytest.approx(
            [x.value for x in diffuse_horiz_rad], rel=1e-3)
        assert [x.value for x in srf_reflect] == pytest.approx(
            [0] * 8760, rel=1e-3)

    def test_leap_year(self):
        """Test clear sky with leap year."""
        location = Location(
            'Chicago Ohare Intl Ap', 'USA', 41.98, -87.92, -6.0, 201.0)
        wea = Wea.from_ashrae_clear_sky(location, is_leap_year=True)

        assert wea.diffuse_horizontal_radiation[1416].datetime.month == 2
        assert wea.diffuse_horizontal_radiation[1416].datetime.day == 29
        assert wea.diffuse_horizontal_radiation[1416].datetime.hour == 0
        assert wea.diffuse_horizontal_radiation[1416].datetime.minute == 30

        assert wea.diffuse_horizontal_radiation[1416 + 12].datetime.month == 2
        assert wea.diffuse_horizontal_radiation[1416 + 12].datetime.day == 29
        assert wea.diffuse_horizontal_radiation[1416 + 12].datetime.hour == 12
        assert wea.diffuse_horizontal_radiation[1416 + 12].datetime.minute == 30


if __name__ == "__main__":
    unittest.main()
