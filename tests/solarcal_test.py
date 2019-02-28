# coding utf-8

from ladybug.comfort.solarcal import outdoor_sky_heat_exch, indoor_sky_heat_exch, \
    shortwave_from_horiz_solar, mrt_delta_from_erf, erf_from_mrt_delta, \
    get_projection_factor, get_projection_factor_simple, \
    sharp_from_solar_and_body_azimuth, body_solar_flux_from_parts, \
    body_solar_flux_from_horiz_parts
from ladybug.comfort.parameter.solarcal import SolarCalParameter
from ladybug.wea import Wea
from ladybug.sunpath import Sunpath

import unittest
import pytest
import sys
if (sys.version_info > (3, 0)):
    xrange = range


class SolarcalTestCase(unittest.TestCase):
    """Test Solarcal functions"""

    def test_outdoor_sky_heat_exch(self):
        """Test the outdoor_sky_heat_exch function"""
        # Test typical daytime condition
        sky_exch = outdoor_sky_heat_exch(22, 380, 200, 380, 45)
        assert sky_exch['s_erf'] == pytest.approx(129.239, rel=1e-2)
        assert sky_exch['s_dmrt'] == pytest.approx(29.6508, rel=1e-2)
        assert sky_exch['l_erf'] == pytest.approx(-11.6208, rel=1e-2)
        assert sky_exch['l_dmrt'] == pytest.approx(-2.6661, rel=1e-2)
        assert sky_exch['mrt'] == pytest.approx(48.9847, rel=1e-2)

        # Test typical nighttime condition
        sky_exch = outdoor_sky_heat_exch(18, 330, 0, 0, 0)
        assert sky_exch['s_erf'] == pytest.approx(0, rel=1e-2)
        assert sky_exch['s_dmrt'] == pytest.approx(0, rel=1e-2)
        assert sky_exch['l_erf'] == pytest.approx(-24.792, rel=1e-2)
        assert sky_exch['l_dmrt'] == pytest.approx(-5.688, rel=1e-2)
        assert sky_exch['mrt'] == pytest.approx(12.3120, rel=1e-2)

    def test_indoor_sky_heat_exch(self):
        """Test the indoor_sky_heat_exch function"""
        # Test typical daytime condition
        sky_exch = indoor_sky_heat_exch(22, 200, 380, 45, 0.5, 0.5)
        assert sky_exch['erf'] == pytest.approx(59.2852, rel=1e-2)
        assert sky_exch['dmrt'] == pytest.approx(14.168, rel=1e-2)
        assert sky_exch['mrt'] == pytest.approx(36.168, rel=1e-2)

        # Test typical nighttime condition
        sky_exch = indoor_sky_heat_exch(22, 0, 0, 0, 0.5, 0.5)
        assert sky_exch['erf'] == pytest.approx(0, rel=1e-2)
        assert sky_exch['dmrt'] == pytest.approx(0, rel=1e-2)
        assert sky_exch['mrt'] == pytest.approx(22, rel=1e-2)

    def test_shortwave_from_horiz_solar(self):
        """Test the shortwave_from_horiz_solar function."""
        # Test typical daytime noon condition
        sky_exch = shortwave_from_horiz_solar(22, 144, 850, 72)
        assert sky_exch['erf'] == pytest.approx(168.7179, rel=1e-2)
        assert sky_exch['dmrt'] == pytest.approx(38.7083, rel=1e-2)
        assert sky_exch['mrt'] == pytest.approx(60.7083, rel=1e-2)

        # Test typical daytime condition
        sky_exch = shortwave_from_horiz_solar(22, 120, 500, 45)
        assert sky_exch['erf'] == pytest.approx(157.33914, rel=1e-2)
        assert sky_exch['dmrt'] == pytest.approx(36.09772, rel=1e-2)
        assert sky_exch['mrt'] == pytest.approx(58.09772, rel=1e-2)

        # Test typical daytime low angle condition
        sky_exch = shortwave_from_horiz_solar(22, 10, 55, 15)
        assert sky_exch['erf'] == pytest.approx(41.61606, rel=1e-2)
        assert sky_exch['dmrt'] == pytest.approx(9.547814, rel=1e-2)
        assert sky_exch['mrt'] == pytest.approx(31.547814, rel=1e-2)

        # Test typical nighttime condition
        sky_exch = shortwave_from_horiz_solar(18, 0, 0, 0, 0.5)
        assert sky_exch['erf'] == pytest.approx(0, rel=1e-2)
        assert sky_exch['dmrt'] == pytest.approx(0, rel=1e-2)
        assert sky_exch['mrt'] == pytest.approx(18, rel=1e-2)

    def test_body_dir_from_dir_normal(self):
        """Test body_solar_flux_from_parts gainst its horizontal counterpart."""
        wea_obj = Wea.from_epw_file('./tests/epw/chicago.epw')
        diff_hr = wea_obj.diffuse_horizontal_irradiance.values
        dir_nr = wea_obj.direct_normal_irradiance.values
        dir_hr = wea_obj.direct_horizontal_irradiance.values
        dts = wea_obj.datetimes
        sp = Sunpath.from_location(wea_obj.location)

        for i in xrange(8760):
            sun = sp.calculate_sun_from_date_time(dts[i])
            alt, az = sun.altitude, sun.azimuth
            sharp = sharp_from_solar_and_body_azimuth(az, 180)
            sflux1 = body_solar_flux_from_parts(diff_hr[i], dir_nr[i], alt, sharp)
            sflux2 = body_solar_flux_from_horiz_parts(diff_hr[i], dir_hr[i], alt, sharp)
            assert sflux1 == pytest.approx(sflux2, rel=1e-2)

    def test_mrt_delta_from_erf(self):
        """Test the mrt_delta_from_erf function."""
        dmrt1 = mrt_delta_from_erf(100)
        dmrt2 = mrt_delta_from_erf(0)
        dmrt3 = mrt_delta_from_erf(-100)

        assert dmrt1 == abs(dmrt3) == pytest.approx(22.94262, rel=1e-2)
        assert dmrt2 == 0

    def test_erf_from_mrt_delta(self):
        """Test the erf_from_mrt_delta function."""
        erf1 = erf_from_mrt_delta(22.94262050611421)
        erf2 = erf_from_mrt_delta(0)
        erf3 = erf_from_mrt_delta(-22.94262050611421)

        assert erf1 == abs(erf3) == pytest.approx(100, rel=1e-2)
        assert erf2 == 0

    def test_sharp_from_solar_and_body_azimuth(self):
        """Test the sharp_from_solar_and_body_azimuth function."""
        assert sharp_from_solar_and_body_azimuth(0, 0) == 0
        assert sharp_from_solar_and_body_azimuth(180, 180) == 0
        assert sharp_from_solar_and_body_azimuth(0, 90) == 90
        assert sharp_from_solar_and_body_azimuth(360, 90) == 90
        assert sharp_from_solar_and_body_azimuth(270, 90) == 180
        assert sharp_from_solar_and_body_azimuth(360, 180) == 180
        assert sharp_from_solar_and_body_azimuth(360, 270) == 90
        assert sharp_from_solar_and_body_azimuth(0, 270) == 90
        assert sharp_from_solar_and_body_azimuth(90, 270) == 180

    def test_projection_factors(self):
        """Test the projection factor functions against one another."""
        for posture in ('standing', 'seated', 'supine'):
            for alt in list(xrange(1, 90, 10)) + [90]:
                for sharp in xrange(0, 190, 10):
                    pf1 = get_projection_factor(alt, sharp, posture)
                    pf2 = get_projection_factor_simple(alt, sharp, posture)
                    assert pf1 == pytest.approx(pf2, rel=0.1)

    def test_projection_factors_incorrect(self):
        """Test the projection factor functions with incorrect inputs."""
        with pytest.raises(Exception):
            get_projection_factor(25, 0, 'Standing')  # incorrect capitalization
        with pytest.raises(Exception):
            get_projection_factor(100, 0, 'standing')  # incorrect altitude
        with pytest.raises(Exception):
            get_projection_factor_simple(25, 0, 'Standing')  # incorrect capitalization
        with pytest.raises(Exception):
            get_projection_factor_simple(100, 0, 'standing')  # incorrect altitude

    def test_solarcal_parameter_init(self):
        """Test the initialization of the SolarCalParameter object."""
        posture = 'seated'
        sharp = 180
        absorptivity = 0.8
        emissivity = 0.97
        solarcal_par = SolarCalParameter(posture=posture,
                                         sharp=sharp,
                                         body_absorptivity=absorptivity,
                                         body_emissivity=emissivity)
        assert solarcal_par.posture == posture
        assert solarcal_par.sharp == sharp
        assert solarcal_par.body_azimuth is None
        assert solarcal_par.body_absorptivity == absorptivity
        assert solarcal_par.body_emissivity == emissivity

    def test_solarcal_parameter_default(self):
        """Test the default SolarCalParameter properties."""
        solarcal_par = SolarCalParameter()
        str(solarcal_par)  # test casting the parameters to a string
        assert solarcal_par.posture == 'standing'
        assert solarcal_par.sharp == 135
        assert solarcal_par.body_azimuth is None
        assert solarcal_par.body_absorptivity == 0.7
        assert solarcal_par.body_emissivity == 0.95
        solarcal_par.acceptable_postures  # test that the acceptable postures are there

    def test_solarcal_parameter_incorrect(self):
        """Test incorrect SolarCalParameter properties."""
        with pytest.raises(Exception):
            SolarCalParameter(posture='seated',
                              sharp=180,
                              body_azimuth=135,  # both sharp and azimuth
                              body_absorptivity=0.8,
                              body_emissivity=0.97)
        with pytest.raises(Exception):
            SolarCalParameter(posture='disco pose')  # incorrect posture
        with pytest.raises(Exception):
            SolarCalParameter(sharp=270)  # incorrect sharp
        with pytest.raises(Exception):
            SolarCalParameter(body_azimuth=-45)  # incorrect body_azimuth
        with pytest.raises(Exception):
            SolarCalParameter(body_absorptivity=60)  # incorrect body_absorptivity
        with pytest.raises(Exception):
            SolarCalParameter(body_emissivity=97)  # incorrect body_emissivity


if __name__ == "__main__":
    unittest.main()
