# coding utf-8

import unittest
import pytest

from ladybug.comfort.parameter.adaptive import AdaptiveParameter

from ladybug.comfort.adaptive import adaptive_comfort_ashrae55, adaptive_comfort_en15251,\
    ashrae55_neutral_offset_from_ppd, en15251_neutral_offset_from_comfort_class, \
    weighted_running_mean_hourly, weighted_running_mean_daily


class AdaptiveTestCase(unittest.TestCase):
    """Test Adaptive functions."""

    def test_adaptive_comfort_ashrae55(self):
        """Test the adaptive_comfort_ashrae55 function"""
        # test typical condition
        comf_result = adaptive_comfort_ashrae55(22, 23, 27, 0.2)
        assert comf_result['to'] == 25
        assert comf_result['t_comf'] == pytest.approx(24.62, rel=1e-2)
        assert comf_result['ce'] == 0
        assert comf_result['deg_comf'] == pytest.approx(0.3799, rel=1e-2)
        assert comf_result['deg_comf'] == comf_result['to'] - comf_result['t_comf']

        # test a high air speed case
        comf_result = adaptive_comfort_ashrae55(16, 23, 27, 1.5)
        comf_result = adaptive_comfort_ashrae55(16, 23, 27, 1.0)
        comf_result = adaptive_comfort_ashrae55(16, 23, 27, 0.7)
        assert comf_result['to'] == 25
        assert comf_result['t_comf'] == pytest.approx(22.76, rel=1e-2)
        assert comf_result['ce'] == 1.2
        assert comf_result['deg_comf'] == pytest.approx(2.23999, rel=1e-2)
        assert comf_result['deg_comf'] == comf_result['to'] - comf_result['t_comf']

        # test a very cold outdoor case
        comf_result = adaptive_comfort_ashrae55(5, 21, 25, 0.1)
        assert comf_result['to'] == 23
        assert comf_result['t_comf'] == pytest.approx(20.900, rel=1e-2)
        assert comf_result['ce'] == 0
        assert comf_result['deg_comf'] == pytest.approx(2.0999, rel=1e-2)

        # testa a very hot outdoor case
        comf_result = adaptive_comfort_ashrae55(35, 26, 30, 0.1)
        assert comf_result['to'] == 28
        assert comf_result['t_comf'] == pytest.approx(28.185, rel=1e-2)
        assert comf_result['ce'] == 0
        assert comf_result['deg_comf'] == pytest.approx(-0.185, rel=1e-2)

        # test a fully conditioned case
        comf_result = adaptive_comfort_ashrae55(24, 22, 24, 0.1, 1)
        assert comf_result['to'] == 23
        assert comf_result['t_comf'] == pytest.approx(24.76, rel=1e-2)
        assert comf_result['ce'] == 0
        assert comf_result['deg_comf'] == pytest.approx(-1.76, rel=1e-2)

        # test a partially conditioned case
        comf_result = adaptive_comfort_ashrae55(24, 22, 24, 0.1, 0.5)
        assert comf_result['to'] == 23
        assert comf_result['t_comf'] == pytest.approx(25.0, rel=1e-2)
        assert comf_result['ce'] == 0
        assert comf_result['deg_comf'] == pytest.approx(-2.0, rel=1e-2)

    def test_adaptive_comfort_en15251(self):
        """Test the adaptive_comfort_en15251 function"""
        # test typical condition
        comf_result = adaptive_comfort_en15251(22, 23, 27, 0.15)
        assert comf_result['to'] == 25

        assert comf_result['t_comf'] == pytest.approx(26.06, rel=1e-2)
        assert comf_result['ce'] == 0
        assert comf_result['deg_comf'] == pytest.approx(-1.06, rel=1e-2)
        assert comf_result['deg_comf'] == comf_result['to'] - comf_result['t_comf']

        # test a high air speed case
        comf_result = adaptive_comfort_en15251(16, 23, 27, 1.5)
        comf_result = adaptive_comfort_en15251(16, 23, 27, 1.0)
        comf_result = adaptive_comfort_en15251(16, 23, 27, 0.7)
        assert comf_result['to'] == 25
        assert comf_result['t_comf'] == pytest.approx(24.08, rel=1e-2)
        assert comf_result['ce'] == pytest.approx(2.3466, rel=1e-2)
        assert comf_result['deg_comf'] == pytest.approx(0.9199, rel=1e-2)
        assert comf_result['deg_comf'] == comf_result['to'] - comf_result['t_comf']

        # test a very cold outdoor case
        comf_result = adaptive_comfort_en15251(5, 21, 25, 0.1)
        assert comf_result['to'] == 23
        assert comf_result['t_comf'] == pytest.approx(22.1, rel=1e-2)
        assert comf_result['ce'] == 0
        assert comf_result['deg_comf'] == pytest.approx(0.8999, rel=1e-2)

        # testa a very hot outdoor case
        comf_result = adaptive_comfort_en15251(35, 26, 30, 0.1)
        assert comf_result['to'] == 28
        assert comf_result['t_comf'] == pytest.approx(28.7, rel=1e-2)
        assert comf_result['ce'] == 0
        assert comf_result['deg_comf'] == pytest.approx(-0.7, rel=1e-2)

        # test a fully conditioned case
        comf_result = adaptive_comfort_en15251(24, 22, 24, 0.1, 1)
        assert comf_result['to'] == 23
        assert comf_result['t_comf'] == pytest.approx(24.76, rel=1e-2)
        assert comf_result['ce'] == 0
        assert comf_result['deg_comf'] == pytest.approx(-1.76, rel=1e-2)

        # test a partially conditioned case
        comf_result = adaptive_comfort_en15251(24, 22, 24, 0.1, 0.5)
        assert comf_result['to'] == 23
        assert comf_result['t_comf'] == pytest.approx(25.74, rel=1e-2)
        assert comf_result['ce'] == 0
        assert comf_result['deg_comf'] == pytest.approx(-2.74, rel=1e-2)

    def test_ashrae55_neutral_offset_from_ppd(self):
        """Test the ashrae55_neutral_offset_from_ppd function."""
        assert ashrae55_neutral_offset_from_ppd(90) == 2.5
        assert ashrae55_neutral_offset_from_ppd(80) == 3.5
        with pytest.raises(Exception):
            ashrae55_neutral_offset_from_ppd(110)
        with pytest.raises(Exception):
            ashrae55_neutral_offset_from_ppd(-10)

    def test_en15251_neutral_offset_from_comfort_class(self):
        """Test the ashrae55_neutral_offset_from_ppd function."""
        assert en15251_neutral_offset_from_comfort_class(1) == 2
        assert en15251_neutral_offset_from_comfort_class(2) == 3
        assert en15251_neutral_offset_from_comfort_class(3) == 4
        with pytest.raises(Exception):
            en15251_neutral_offset_from_comfort_class(0)
        with pytest.raises(Exception):
            en15251_neutral_offset_from_comfort_class(4)

    def test_weighted_running_mean_hourly(self):
        """Test the weighted_running_mean_hourly function."""
        # Test with typical values
        outdoor = list(range(24)) * 365
        prevailing = weighted_running_mean_hourly(outdoor)
        for temp in prevailing[:24]:
            assert temp == prevailing[0]
        assert prevailing[0] == pytest.approx(11.5, rel=1e-2)

        # test with a number of values not divisible by 24
        outdoor = list(range(25)) * 7
        prevailing = weighted_running_mean_hourly(outdoor)
        for temp in prevailing[:24]:
            assert temp == prevailing[0]
        assert prevailing[0] == pytest.approx(12.42215, rel=1e-2)

        # test that an exception is thrown when values are less than a week.
        outdoor = list(range(24)) * 5
        with pytest.raises(Exception):
            prevailing = weighted_running_mean_hourly(outdoor)

    def test_weighted_running_mean_daily(self):
        """Test the weighted_running_mean_daily function."""
        # Test with typical values
        outdoor = list(range(365))
        prevailing = weighted_running_mean_daily(outdoor)
        assert prevailing[0] == pytest.approx(362.1316, rel=1e-2)

        # test that an exception is thrown when values are less than a week.
        outdoor = list(range(5))
        with pytest.raises(Exception):
            prevailing = weighted_running_mean_daily(outdoor)

    def test_adaptive_parameter_init(self):
        """Test the initialization of the AdaptiveParameter object."""
        ashrae55_or_en15251 = False
        neutral_offset = 2
        avg_month_or_run = True
        discr_or_cont = True
        cold_prevail_temp_limit = 18
        conditioning = 0.5
        adaptive_par = AdaptiveParameter(ashrae55_or_en15251=ashrae55_or_en15251,
                                         neutral_offset=neutral_offset,
                                         avg_month_or_running_mean=avg_month_or_run,
                                         discrete_or_continuous_air_speed=discr_or_cont,
                                         cold_prevail_temp_limit=cold_prevail_temp_limit,
                                         conditioning=conditioning)
        assert adaptive_par.ashrae55_or_en15251 == ashrae55_or_en15251
        assert adaptive_par.neutral_offset == neutral_offset
        assert adaptive_par.avg_month_or_running_mean is avg_month_or_run
        assert adaptive_par.discrete_or_continuous_air_speed == discr_or_cont
        assert adaptive_par.cold_prevail_temp_limit == cold_prevail_temp_limit
        assert adaptive_par.conditioning == conditioning

    def test_adaptive_parameter_default_ahsrae55(self):
        """Test the default AdaptiveParameter properties."""
        adaptive_par = AdaptiveParameter()
        str(adaptive_par)  # test casting the parameters to a string
        assert adaptive_par.ashrae55_or_en15251 is True
        assert adaptive_par.neutral_offset == 2.5
        assert adaptive_par.avg_month_or_running_mean is True
        assert adaptive_par.discrete_or_continuous_air_speed is True
        assert adaptive_par.cold_prevail_temp_limit == 10
        assert adaptive_par.conditioning == 0
        assert adaptive_par.standard == 'ASHRAE-55'
        assert adaptive_par.prevailing_temperture_method == 'Averaged Monthly'
        assert adaptive_par.air_speed_method == 'Discrete'
        assert adaptive_par.minimum_operative == pytest.approx(18.4, rel=1e-2)

        adaptive_par.set_neutral_offset_from_ppd(80)
        assert adaptive_par.neutral_offset == 3.5

    def test_adaptive_parameter_default_en15251(self):
        """Test the default AdaptiveParameter properties."""
        adaptive_par = AdaptiveParameter(False)
        str(adaptive_par)  # test casting the parameters to a string
        assert adaptive_par.ashrae55_or_en15251 is False
        assert adaptive_par.neutral_offset == 3
        assert adaptive_par.avg_month_or_running_mean is False
        assert adaptive_par.discrete_or_continuous_air_speed is False
        assert adaptive_par.cold_prevail_temp_limit == 15
        assert adaptive_par.conditioning == 0
        assert adaptive_par.standard == 'EN-15251'
        assert adaptive_par.prevailing_temperture_method == 'Running Mean'
        assert adaptive_par.air_speed_method == 'Continuous'
        assert adaptive_par.minimum_operative == pytest.approx(20.75, rel=1e-2)

        adaptive_par.set_neutral_offset_from_comfort_class(1)
        assert adaptive_par.neutral_offset == 2

    def test_adaptive_parameter_incorrect(self):
        """Test incorrect AdaptiveParameter properties."""
        with pytest.raises(Exception):
            AdaptiveParameter(neutral_offset=-2)
        with pytest.raises(Exception):
            AdaptiveParameter(neutral_offset=12)
        with pytest.raises(Exception):
            AdaptiveParameter(cold_prevail_temp_limit=5)
        with pytest.raises(Exception):
            AdaptiveParameter(cold_prevail_temp_limit=30)
        with pytest.raises(Exception):
            AdaptiveParameter(conditioning=50)

    def test_comfort_check(self):
        """Test comfort check on AdaptiveParameter."""
        comf_result = adaptive_comfort_ashrae55(24, 26, 30, 0.2)
        adaptive_par = AdaptiveParameter()
        comf_test = adaptive_par.is_comfortable(comf_result)
        assert comf_test is False

        comf_result = adaptive_comfort_ashrae55(24, 26, 30, 3)
        adaptive_par = AdaptiveParameter()
        comf_test = adaptive_par.is_comfortable(comf_result)
        assert comf_test is True

    def test_thermal_condition_check(self):
        """Test the thermal condition check on PMVParameter."""
        comf_result = adaptive_comfort_ashrae55(24, 26, 30, 0.2)
        adaptive_par = AdaptiveParameter()
        condition_test = adaptive_par.thermal_condition(comf_result)
        assert condition_test == 1

        comf_result = adaptive_comfort_ashrae55(24, 26, 30, 3)
        adaptive_par = AdaptiveParameter()
        condition_test = adaptive_par.thermal_condition(comf_result)
        assert condition_test == 0


if __name__ == "__main__":
    unittest.main()
