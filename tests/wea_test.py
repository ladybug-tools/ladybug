# coding=utf-8

import unittest
import pytest

from ladybug.wea import Wea


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

    def test_from_stat(self):
        """Test import from stat"""
        stat_path = './tests/stat/chicago.stat'
        wea_from_stat = Wea.from_stat_file(stat_path)

        assert wea_from_stat.location.city == 'Chicago Ohare Intl Ap'
        assert wea_from_stat.timestep == 1

    def test_from_clear_sky(self):
        """Test from original clear sky"""
        stat_path = './tests/stat/chicago.stat'
        wea_from_stat = Wea.from_stat_file(stat_path)
        location = wea_from_stat.location
        wea_from_clear_sky = Wea.from_ashrae_clear_sky(location)

        assert wea_from_clear_sky.location.city == 'Chicago Ohare Intl Ap'
        assert wea_from_clear_sky.timestep == 1

    def test_from_zhang_huang(self):
        """Test from zhang huang solar model"""
        stat_path = './tests/stat/chicago.stat'
        wea_from_stat = Wea.from_stat_file(stat_path)
        location = wea_from_stat.location

        cc = [0.5] * 8760
        rh = [50] * 8760
        dbt = [20] * 8760
        ws = [2] * 8760
        wea_from_zh = Wea.from_zhang_huang_solar_model(location, cc, rh, dbt, ws)

        assert wea_from_zh.location.city == 'Chicago Ohare Intl Ap'
        assert wea_from_zh.timestep == 1
        # TODO: Add checks for the values produced by the model

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

    def test_radiation_on_surface(self):
        """Test the radiation on surface method."""
        stat_path = './tests/stat/chicago.stat'
        wea_from_stat = Wea.from_stat_file(stat_path)

        srf_total, srf_direct, srf_diffuse, srf_reflect = \
            wea_from_stat.radiation_on_surface(90)
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

    def test_write(self):
        pass


if __name__ == "__main__":
    unittest.main()
