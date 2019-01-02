# coding utf-8

import unittest
import pytest

from ladybug.comfort.pmv import PMVComfortParameters

from ladybug.comfort.utility.pmv import pmv
from ladybug.comfort.utility.pmv import pmv_fanger
from ladybug.comfort.utility.pmv import pierce_set


class PMVTestCase(unittest.TestCase):
    """Test PMV calculation from single set of values"""

    # preparing to test.
    def setUp(self):
        """set up."""

    def tearDown(self):
        """Nothing to tear down as nothing gets written to file."""
        pass

    def test_pmv_fanger_utility(self):
        """Test the pmv_fanger utility function"""
        pmv_comf, ppd = pmv_fanger(19, 23, 0.5, 60, 1.5, 0.4)

        assert pmv_comf == pytest.approx(-1.74, rel=1e-2)
        assert round(ppd) == 64

    def test_pierce_set_utility(self):
        set = pierce_set(19, 23, 0.5, 60, 1.5, 0.4)

        assert set == pytest.approx(-18.7, rel=1e-1)

    def test_pmv_utility(self):
        result = pmv(19, 23, 0.5, 60, 1.5, 0.4)

        assert result['pmv'] == pytest.approx(-1.74, rel=1e-2)
        assert round(result['ppd']) == 64
        assert result['set'] == pytest.approx(-18.7, rel=1e-1)

    def test_pmv_comfort_parameters(self):
        """Test PMVComfortParameters."""
        ppd_comfort_thresh = 20
        humid_ratio_up = 0.012
        humid_ratio_low = 0.004
        still_air_thresh = 0.2

        pmv_comf = PMVComfortParameters(
            ppd_comfort_thresh, humid_ratio_up, humid_ratio_low, still_air_thresh)

        assert pmv_comf.ppd_comfort_thresh == ppd_comfort_thresh
        assert pmv_comf.humid_ratio_up == humid_ratio_up
        assert pmv_comf.humid_ratio_low == humid_ratio_low
        assert pmv_comf.still_air_threshold == still_air_thresh
