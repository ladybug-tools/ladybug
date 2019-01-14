# coding utf-8

import unittest
import pytest

from ladybug.comfort.standard.pmv import PMVParameters

from ladybug.comfort.pmv import pmv
from ladybug.comfort.pmv import fanger_pmv
from ladybug.comfort.pmv import pierce_set


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
        set = pierce_set(19, 23, 0.5, 60, 1.5, 0.4)
        assert set == pytest.approx(18.8911, rel=1e-2)

    def test_pmv(self):
        result = pmv(19, 23, 0.5, 60, 1.5, 0.4)
        assert result['pmv'] == pytest.approx(-1.6745, rel=1e-2)
        assert round(result['ppd']) == pytest.approx(60.382974, rel=1e-2)
        assert result['set'] == pytest.approx(18.8911, rel=1e-2)

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
