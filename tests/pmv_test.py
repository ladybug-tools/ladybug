# coding utf-8

import unittest
import pytest

from ladybug.comfort.standard.pmv import PMVParameters

from ladybug.comfort.pmv import pmv, fanger_pmv, pierce_set, ppd_from_pmv, \
    pmv_from_ppd, calc_missing_pmv_input


class PMVTestCase(unittest.TestCase):
    """Test PMV calculation from single set of values"""

    # preparing to test.
    def setUp(self):
        """set up."""

    def tearDown(self):
        """Nothing to tear down as nothing gets written to file."""
        pass

    def test_fanger_pmv(self):
        """Test the fanger_pmv function"""
        pmv_comf, ppd, hl = fanger_pmv(19, 23, 0.1, 60, 1.5, 0.4)
        assert pmv_comf == pytest.approx(-0.680633, rel=1e-2)
        assert ppd == pytest.approx(14.7373, rel=1e-2)

    def test_pierce_set(self):
        """Test the pierce_set function"""
        set = pierce_set(19, 23, 0.5, 60, 1.5, 0.4)
        assert set == pytest.approx(18.8911, rel=1e-2)

    def test_pmv(self):
        """Test the pmv function"""
        result = pmv(19, 23, 0.5, 60, 1.5, 0.4)
        assert result['pmv'] == pytest.approx(-1.6745, rel=1e-2)
        assert round(result['ppd']) == pytest.approx(60.382974, rel=1e-2)
        assert result['set'] == pytest.approx(18.8911, rel=1e-2)

    def test_ppd_from_pmv(self):
        """Test the ppd_from_pmv function"""
        ppd = ppd_from_pmv(-0.5)
        assert ppd == pytest.approx(10, rel=1e-1)
        ppd = ppd_from_pmv(-1)
        assert ppd == pytest.approx(26, rel=1e-1)

    def test_pmv_from_ppd(self):
        """Test the pmv_from_ppd function"""
        pmv_lower, pmv_upper = pmv_from_ppd(10)
        assert pmv_lower == pytest.approx(-0.5, rel=1e-1)
        assert pmv_upper == pytest.approx(0.5, rel=1e-1)
        pmv_lower, pmv_upper = pmv_from_ppd(26)
        assert pmv_lower == pytest.approx(-1, rel=1e-1)
        assert pmv_upper == pytest.approx(1, rel=1e-1)

    def test_calc_missing_pmv_input(self):
        """Test the calc_missing_pmv_input function"""
        input_1 = {'ta': None, 'tr': 20, 'vel': 0.05, 'rh': 50,
                   'met': 1.2, 'clo': 0.75, 'wme': 0}
        input_2 = {'ta': 20, 'tr': None, 'vel': 0.05, 'rh': 50,
                   'met': 1.2, 'clo': 0.75, 'wme': 0}
        input_3 = {'ta': 22, 'tr': 22, 'vel': None, 'rh': 50,
                   'met': 1.2, 'clo': 0.75, 'wme': 0}
        input_4 = {'ta': 20, 'tr': 20, 'vel': 0.05, 'rh': None,
                   'met': 1.2, 'clo': 0.75, 'wme': 0}
        input_5 = {'ta': 20, 'tr': 20, 'vel': 0.05, 'rh': 50,
                   'met': None, 'clo': 0.75, 'wme': 0}
        input_6 = {'ta': 20, 'tr': 20, 'vel': 0.05, 'rh': 50,
                   'met': 1.2, 'clo': None, 'wme': 0}
        input_7 = {'ta': 20, 'tr': 20, 'vel': 0.05, 'rh': 50,
                   'met': 1.4, 'clo': 0.75, 'wme': None}
        updated_input_1 = calc_missing_pmv_input(-1, input_1)
        updated_input_2 = calc_missing_pmv_input(-1, input_2)
        updated_input_3 = calc_missing_pmv_input(-1, input_3, up_bound=1)
        updated_input_4 = calc_missing_pmv_input(-1, input_4)
        updated_input_5 = calc_missing_pmv_input(-1, input_5, up_bound=1)
        updated_input_6 = calc_missing_pmv_input(-1, input_6, up_bound=1)
        updated_input_7 = calc_missing_pmv_input(-1, input_7, up_bound=1)
        assert updated_input_1['ta'] == pytest.approx(18.529, rel=1e-1)
        assert updated_input_2['tr'] == pytest.approx(17.912, rel=1e-1)
        assert updated_input_3['vel'] == pytest.approx(0.720, rel=1e-1)
        assert updated_input_4['rh'] == pytest.approx(7.0, rel=1e-1)
        assert updated_input_5['met'] == pytest.approx(1.1234, rel=1e-2)
        assert updated_input_6['clo'] == pytest.approx(0.6546, rel=1e-2)
        assert updated_input_7['wme'] == pytest.approx(0.3577, rel=1e-2)

    def test_pmv_parameters(self):
        """Test PMVParameters."""
        ppd_comfort_thresh = 20
        humid_ratio_up = 0.012
        humid_ratio_low = 0.004
        still_air_thresh = 0.2

        pmv_comf = PMVParameters(
            ppd_comfort_thresh, humid_ratio_up, humid_ratio_low, still_air_thresh)

        assert pmv_comf.ppd_comfort_thresh == ppd_comfort_thresh
        assert pmv_comf.humid_ratio_upper == humid_ratio_up
        assert pmv_comf.humid_ratio_lower == humid_ratio_low
        assert pmv_comf.still_air_threshold == still_air_thresh

    def test_pmv_parameters_invalid(self):
        """Test PMVParameters for invalid inputs."""
        ppd_comfort_thresh = 110
        humid_ratio_up = 12
        humid_ratio_low = -1
        still_air_thresh = -1

        with pytest.raises(AssertionError):
            PMVParameters(ppd_comfort_thresh=ppd_comfort_thresh)
        with pytest.raises(AssertionError):
            PMVParameters(humid_ratio_upper=humid_ratio_up)
        with pytest.raises(AssertionError):
            PMVParameters(humid_ratio_lower=humid_ratio_low)
        with pytest.raises(AssertionError):
            PMVParameters(still_air_threshold=still_air_thresh)

    def test_comfort_check(self):
        """Test comfort check on PMVParameters."""
        pmv_comf = PMVParameters()
        comf_test = pmv_comf.is_comfortable(13, 0.01)
        assert comf_test is False
        comf_test = pmv_comf.is_comfortable(7, 0.01)
        assert comf_test is True

    def test_thermal_condition_check(self):
        """Test the thermal condition check on PMVParameters."""
        pmv_comf = PMVParameters()
        condition_test = pmv_comf.thermal_condition(-1, 20)
        assert condition_test == -1
        condition_test = pmv_comf.thermal_condition(0, 5)
        assert condition_test == 0

    def test_discomfort_reason_check(self):
        """Test the thermal condition check on PMVParameters."""
        pmv_comf = PMVParameters()
        condition_test = pmv_comf.discomfort_reason(-1, 20, 0.01)
        assert condition_test == -1
        condition_test = pmv_comf.discomfort_reason(0, 5, 0.01)
        assert condition_test == 0


if __name__ == "__main__":
    unittest.main()
