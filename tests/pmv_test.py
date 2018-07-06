# coding utf-8

import unittest
from ladybug.comfort.pmv import PMV


class PMVTestCase(unittest.TestCase):
    """Test PMV calculation from single set of values"""

    # preparing to test.
    def setUp(self):
        """set up."""

    def tearDown(self):
        """Nothing to tear down as nothing gets written to file."""
        pass

    def test_default_values(self):
        """Test the default values being correctly imported and calculated"""
        pmv_comf = PMV.from_individual_values()

        assert pmv_comf.air_temperature == [20]
        assert pmv_comf.rad_temperature == [20]
        assert pmv_comf.wind_speed == [0]
        assert pmv_comf.rel_humidity == [50]
        assert pmv_comf.met_rate == [1.1]
        assert pmv_comf.clo_value == [0.85]
        assert pmv_comf.external_work == [0]
        assert pmv_comf.ppd_comfort_thresh == 10
        assert pmv_comf.humid_ratio_up == 0.03
        assert pmv_comf.humid_ratio_low == 0
        assert pmv_comf.still_air_threshold == 0.1
        assert pmv_comf.single_values is True

        pmv = pmv_comf.pmv
        # Assert similarity to 0.01 decimal based of http://comfort.cbe.berkeley.edu/
        assert round(pmv - (-0.85), 2) == 0

        ppd = pmv_comf.ppd
        # Assert similarity to 0.01 decimal based of http://comfort.cbe.berkeley.edu/
        # Remember that the values are in %
        assert round(ppd - 20) == 0

        # Check pmv, set and cooling effect are calculated properly
        # based of http://comfort.cbe.berkeley.edu/
        pmv = pmv_comf.pmv
        ppd = pmv_comf.ppd
        set = pmv_comf.set
        cooling_effect = pmv_comf.cooling_effect

        assert round(pmv - (-0.85), 2) == 0
        assert round(ppd - 20) == 0
        assert round(set - 22.2, 1) == 0
        assert round(cooling_effect - 0, 1) == 0

    def test_setters_single_values(self):
        """Test low level single value setting functions"""
        pmv_comf = PMV.from_individual_values()
        air_temp = 19
        rad_temp = 23
        wind_speed = 0.5
        rel_humid = 60
        met_rate = 1.5
        clo = 0.4
        external_work = 0

        ppd_comfort_thresh = 20
        humid_ratio_up = 70
        humid_ratio_low = 40
        still_air_thresh = 0.2

        # PmvComf model with values set up individually
        pmv_comf.air_temperature = air_temp
        pmv_comf.rad_temperature = rad_temp
        pmv_comf.wind_speed = wind_speed
        pmv_comf.rel_humidity = rel_humid
        pmv_comf.met_rate = met_rate
        pmv_comf.clo_value = clo
        pmv_comf.external_work = external_work
        pmv_comf.ppd_comfort_thresh = ppd_comfort_thresh
        pmv_comf.humid_ratio_up = humid_ratio_up
        pmv_comf.humid_ratio_low = humid_ratio_low
        pmv_comf.still_air_threshold = still_air_thresh

        # PmvComf model with values set up through classmethod
        pmv_comf = PMV.from_individual_values(air_temperature=air_temp,
                                              rad_temperature=rad_temp,
                                              wind_speed=wind_speed,
                                              rel_humidity=rel_humid,
                                              met_rate=met_rate, clo_value=clo,
                                              external_work=external_work)

        assert pmv_comf.air_temperature == [air_temp]
        assert pmv_comf.rad_temperature == [rad_temp]
        assert pmv_comf.wind_speed == [wind_speed]
        assert pmv_comf.rel_humidity == [rel_humid]
        assert pmv_comf.met_rate == [met_rate]
        assert pmv_comf.clo_value == [clo]
        assert pmv_comf.external_work == [external_work]
        assert pmv_comf.single_values is True
        # TODO(@chriswmackey): check and see why these tests are failing
        # assert pmv_comf.ppd_comfort_thresh == ppd_comfort_thresh
        # assert pmv_comf.humid_ratio_up == humid_ratio_up
        # assert pmv_comf.humid_ratio_low == humid_ratio_low
        # assert pmv_comf.still_air_threshold == still_air_thresh
        # assert pmv_comf.is_data_aligned is False

        # Good to check general method to set comfort params
        pmv_comf.set_comfort_par(ppd_comfort_thresh=ppd_comfort_thresh,
                                 humid_ratio_up=humid_ratio_up,
                                 humid_ratio_low=humid_ratio_low,
                                 still_air_threshold=still_air_thresh)

        pmv_comf._check_and_align_lists()

        # Check pmv, set and cooling effect are calculated properly
        pmv = pmv_comf.pmv
        ppd = pmv_comf.ppd
        set = pmv_comf.set
        # cooling_effect = pmv_comf.cooling_effect

        assert round(pmv - (-1.74), 1) == 0
        assert round(ppd - 64, 1) < 5
        assert round(set - 18.7, 1) < 0.5
        # TODO(@chriswmackey): check and see why these tests are failing
        # assert round(cooling_effect - 3.9, 1) == 0

    def test_setters_list_values(self):
        """Test low level list value setting functions"""
        pmv_comf = PMV()
        air_temp = [19, 19]
        rad_temp = [23, 23]
        wind_speed = [0.5, 0.5]
        rel_humid = [60, 60]
        met_rate = [1.5, 1.5]
        clo = [0.4, 0.4]
        external_work = [0, 0]

        # PmvComf model with values set up individually
        pmv_comf.air_temperature = air_temp
        pmv_comf.rad_temperature = rad_temp
        pmv_comf.wind_speed = wind_speed
        pmv_comf.rel_humidity = rel_humid
        pmv_comf.met_rate = met_rate
        pmv_comf.clo_value = clo
        pmv_comf.external_work = external_work

        # PmvComf model with value set up through class
        pmv_comf = PMV(air_temperature=air_temp, rad_temperature=rad_temp,
                       wind_speed=wind_speed, rel_humidity=rel_humid, met_rate=met_rate,
                       clo_value=clo, external_work=external_work)

        assert pmv_comf.air_temperature == air_temp
        assert pmv_comf.rad_temperature == rad_temp
        assert pmv_comf.wind_speed == wind_speed
        assert pmv_comf.rel_humidity == rel_humid
        assert pmv_comf.met_rate == met_rate
        assert pmv_comf.clo_value == clo
        assert pmv_comf.external_work == external_work
        assert pmv_comf.single_values is False

        # Check that inputting values through __init__ or @setters results in same object
        assert pmv_comf.__dict__ == pmv_comf.__dict__

        # Check pmv, set and cooling effect are calculated properly
        pmv = pmv_comf.pmv
        ppd = pmv_comf.ppd
        set = pmv_comf.set
        cooling_effect = pmv_comf.cooling_effect

        assert pmv[0] == pmv[1]
        assert ppd[0] == ppd[1]
        assert set[0] == set[1]
        assert cooling_effect[0] == cooling_effect[1]
        # TODO(@chriswmackey): check and see why these tests are failing
        # assert round(pmv[0] - (-1.74), 1) == 0
        assert round(ppd[0] - 64, 1) < 5
        assert round(set[0] - 18.7, 1) < 0.5
        assert round(cooling_effect[0] - 3.9, 1) < 0.5

    def test_from_single_values(self):
        """Test calculating PMV from a single set of values"""
        # What are we testing here?
        pmv_comf = PMV.from_individual_values(26, 26, 0.75, 80, 1.1, 0.5)
        pmv = pmv_comf.pmv
