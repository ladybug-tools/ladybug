# coding utf-8

import unittest
import pytest

from ladybug.comfort.standard.utci import UTCIParameters

from ladybug.comfort.utci import utci, calc_missing_utci_input


class PMVTestCase(unittest.TestCase):
    """Test PMV calculation from single set of values"""

    # preparing to test.
    def setUp(self):
        """set up."""

    def tearDown(self):
        """Nothing to tear down as nothing gets written to file."""
        pass

    def test_utci(self):
        """Test the utci function"""
        assert utci(20, 20, 3, 50) == pytest.approx(16.24224, rel=1e-2)
        assert utci(30, 30, 0.5, 90) == pytest.approx(35.511294, rel=1e-2)

    def test_calc_missing_utci_input(self):
        """Test the calc_missing_pmv_input function"""
        input_1 = {'ta': None, 'tr': 20, 'vel': 0.5, 'rh': 50}
        input_2 = {'ta': 20, 'tr': None, 'vel': 0.5, 'rh': 50}
        input_3 = {'ta': 22, 'tr': 22, 'vel': None, 'rh': 50}
        input_4 = {'ta': 20, 'tr': 20, 'vel': 0.5, 'rh': None}
        updated_input_1 = calc_missing_utci_input(25, input_1)
        updated_input_2 = calc_missing_utci_input(25, input_2)
        updated_input_3 = calc_missing_utci_input(15, input_3, up_bound=1)
        updated_input_4 = calc_missing_utci_input(22, input_4)
        assert updated_input_1['ta'] == pytest.approx(26.9827, rel=1e-2)
        assert updated_input_2['tr'] == pytest.approx(36.3803, rel=1e-2)
        assert updated_input_3['vel'] == pytest.approx(5.77514, rel=1e-2)
        assert updated_input_4['rh'] == pytest.approx(90.388989, rel=1e-2)

    def test_utci_parameters(self):
        """Test UTCI Parameters."""
        cold_thresh = 8
        heat_thresh = 27
        extreme_cold_thresh = -41
        very_strong_cold_thresh = -28
        strong_cold_thresh = -14
        moderate_cold_thresh = -1
        moderate_heat_thresh = 29
        strong_heat_thresh = 33
        very_strong_heat_thresh = 39
        extreme_heat_thresh = 47

        utci_comf = UTCIParameters(
            cold_thresh, heat_thresh, extreme_cold_thresh, very_strong_cold_thresh,
            strong_cold_thresh, moderate_cold_thresh, moderate_heat_thresh,
            strong_heat_thresh, very_strong_heat_thresh, extreme_heat_thresh)

        assert utci_comf.cold_thresh == cold_thresh
        assert utci_comf.heat_thresh == heat_thresh
        assert utci_comf.extreme_cold_thresh == extreme_cold_thresh
        assert utci_comf.very_strong_cold_thresh == very_strong_cold_thresh
        assert utci_comf.strong_cold_thresh == strong_cold_thresh
        assert utci_comf.moderate_cold_thresh == moderate_cold_thresh
        assert utci_comf.moderate_heat_thresh == moderate_heat_thresh
        assert utci_comf.strong_heat_thresh == strong_heat_thresh
        assert utci_comf.very_strong_heat_thresh == very_strong_heat_thresh
        assert utci_comf.extreme_heat_thresh == extreme_heat_thresh

    def test_utci_parameters_invalid(self):
        """Test UTCI Parameters for invalid inputs."""
        cold_thresh = 30
        heat_thresh = 8

        with pytest.raises(AssertionError):
            UTCIParameters(cold_thresh=cold_thresh)
        with pytest.raises(AssertionError):
            UTCIParameters(heat_thresh=heat_thresh)

    def test_comfort_check(self):
        """Test comfort check on UTCI Parameters."""
        utci_comf = UTCIParameters()
        comf_test = utci_comf.is_comfortable(5)
        assert comf_test is False
        comf_test = utci_comf.is_comfortable(22)
        assert comf_test is True

    def test_thermal_condition_check(self):
        """Test the thermal condition check on UTCI Parameters."""
        utci_comf = UTCIParameters()
        condition_test = utci_comf.thermal_condition(5)
        assert condition_test == -1
        condition_test = utci_comf.thermal_condition(22)
        assert condition_test == 0
        condition_test = utci_comf.thermal_condition(32)
        assert condition_test == 1

    def test_thermal_condition_low_check(self):
        """Test the thermal condition check on UTCI Parameters."""
        utci_comf = UTCIParameters()
        condition_test = utci_comf.thermal_condition_low(-15)
        assert condition_test == -2
        condition_test = utci_comf.thermal_condition_low(5)
        assert condition_test == -1
        condition_test = utci_comf.thermal_condition_low(22)
        assert condition_test == 0
        condition_test = utci_comf.thermal_condition_low(30)
        assert condition_test == 1
        condition_test = utci_comf.thermal_condition_low(36)
        assert condition_test == 2

    def test_thermal_condition_medium_check(self):
        """Test the thermal condition check on UTCI Parameters."""
        utci_comf = UTCIParameters()
        condition_test = utci_comf.thermal_condition_medium(-30)
        assert condition_test == -3
        condition_test = utci_comf.thermal_condition_medium(-15)
        assert condition_test == -2
        condition_test = utci_comf.thermal_condition_medium(5)
        assert condition_test == -1
        condition_test = utci_comf.thermal_condition_medium(22)
        assert condition_test == 0
        condition_test = utci_comf.thermal_condition_medium(30)
        assert condition_test == 1
        condition_test = utci_comf.thermal_condition_medium(36)
        assert condition_test == 2
        condition_test = utci_comf.thermal_condition_medium(40)
        assert condition_test == 3

    def test_thermal_condition_high_check(self):
        """Test the thermal condition check on UTCI Parameters."""
        utci_comf = UTCIParameters()
        condition_test = utci_comf.thermal_condition_high(-30)
        assert condition_test == -4
        condition_test = utci_comf.thermal_condition_high(-18)
        assert condition_test == -3
        condition_test = utci_comf.thermal_condition_high(-8)
        assert condition_test == -2
        condition_test = utci_comf.thermal_condition_high(5)
        assert condition_test == -1
        condition_test = utci_comf.thermal_condition_high(22)
        assert condition_test == 0
        condition_test = utci_comf.thermal_condition_high(27)
        assert condition_test == 1
        condition_test = utci_comf.thermal_condition_high(30)
        assert condition_test == 2
        condition_test = utci_comf.thermal_condition_high(36)
        assert condition_test == 3
        condition_test = utci_comf.thermal_condition_high(40)
        assert condition_test == 4

    def test_thermal_condition_very_high_check(self):
        """Test the thermal condition check on UTCI Parameters."""
        utci_comf = UTCIParameters()
        condition_test = utci_comf.thermal_condition_very_high(-50)
        assert condition_test == -5
        condition_test = utci_comf.thermal_condition_very_high(-30)
        assert condition_test == -4
        condition_test = utci_comf.thermal_condition_very_high(-18)
        assert condition_test == -3
        condition_test = utci_comf.thermal_condition_very_high(-8)
        assert condition_test == -2
        condition_test = utci_comf.thermal_condition_very_high(5)
        assert condition_test == -1
        condition_test = utci_comf.thermal_condition_very_high(22)
        assert condition_test == 0
        condition_test = utci_comf.thermal_condition_very_high(27)
        assert condition_test == 1
        condition_test = utci_comf.thermal_condition_very_high(30)
        assert condition_test == 2
        condition_test = utci_comf.thermal_condition_very_high(36)
        assert condition_test == 3
        condition_test = utci_comf.thermal_condition_very_high(40)
        assert condition_test == 4
        condition_test = utci_comf.thermal_condition_very_high(50)
        assert condition_test == 5


if __name__ == "__main__":
    unittest.main()
