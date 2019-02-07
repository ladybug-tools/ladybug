# coding utf-8

import unittest
import pytest

from ladybug.comfort.solarcal import outdoor_sky_heat_exch


class SolarcalTestCase(unittest.TestCase):
    """Test PMV calculation from single set of values"""

    def test_outdoor_sky_heat_exch(self):
        """Test the outdoor_sky_heat_exch function"""
        # Test typical daytime condition
        sky_exch = outdoor_sky_heat_exch(22, 380, 200, 380, 45, 135)
        assert sky_exch['s_erf'] == pytest.approx(129.239, rel=1e-2)
        assert sky_exch['s_dmrt'] == pytest.approx(29.6508, rel=1e-2)
        assert sky_exch['l_erf'] == pytest.approx(-11.6208, rel=1e-2)
        assert sky_exch['l_dmrt'] == pytest.approx(-2.6661, rel=1e-2)
        assert sky_exch['mrt'] == pytest.approx(48.9847, rel=1e-2)

        # Test typical nighttime condition
        sky_exch = outdoor_sky_heat_exch(18, 330, 0, 0, 0, 0)
        assert sky_exch['s_erf'] == pytest.approx(0, rel=1e-2)
        assert sky_exch['s_dmrt'] == pytest.approx(0, rel=1e-2)
        assert sky_exch['l_erf'] == pytest.approx(-24.792, rel=1e-2)
        assert sky_exch['l_dmrt'] == pytest.approx(-5.688, rel=1e-2)
        assert sky_exch['mrt'] == pytest.approx(12.3120, rel=1e-2)


if __name__ == "__main__":
    unittest.main()
