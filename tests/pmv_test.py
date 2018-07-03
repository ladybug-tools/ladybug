# coding utf-8

import unittest
from ladybug.comfort.comfortBase import ComfortModel
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
        myPmvComf = PMV.from_individual_values()

        assert myPmvComf.air_temperature == [20]
        assert myPmvComf.rad_temperature == [20]
        assert myPmvComf.wind_speed == [0]
        assert myPmvComf.rel_humidity == [50]
        assert myPmvComf.met_rate == [1.1]
        assert myPmvComf.clo_value == [0.85]
        assert myPmvComf.external_work == [0]
        assert myPmvComf.ppd_comfort_thresh == 10
        assert myPmvComf.humid_ratio_up == 0.03
        assert myPmvComf.humid_ratio_low == 0
        assert myPmvComf.still_air_threshold == 0.1
        assert myPmvComf.single_values == True

        pmv = myPmvComf.pmv
        # Assert similarity to 0.01 decimal based of http://comfort.cbe.berkeley.edu/
        assert round(pmv- (-0.85), 2) == 0

        ppd = myPmvComf.ppd
        # Assert similarity to 0.01 decimal based of http://comfort.cbe.berkeley.edu/
        # Remember that the values are in %
        assert round(ppd- 20) == 0

        # Check pmv, set and cooling effect are calculated properly
        # based of http://comfort.cbe.berkeley.edu/
        pmv = myPmvComf.pmv
        ppd = myPmvComf.ppd
        set = myPmvComf.set
        cooling_effect = myPmvComf.cooling_effect

        assert round(pmv- (-0.85), 2) == 0
        assert round(ppd- 20) == 0
        assert round(set- 22.2, 1) == 0
        assert round(cooling_effect - 0, 1) == 0

    def test_setters_single_values(self):
        """Test low level single value setting functions"""
        myPmvComf = PMV.from_individual_values()
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
        myPmvComf.air_temperature = air_temp
        myPmvComf.rad_temperature = rad_temp
        myPmvComf.wind_speed = wind_speed
        myPmvComf.rel_humidity = rel_humid
        myPmvComf.met_rate = met_rate
        myPmvComf.clo_value = clo
        myPmvComf.external_work = external_work
        myPmvComf.ppd_comfort_thresh = ppd_comfort_thresh
        myPmvComf.humid_ratio_up = humid_ratio_up
        myPmvComf.humid_ratio_low = humid_ratio_low
        myPmvComf.still_air_threshold = still_air_thresh

        # PmvComf model with values set up through classmethod
        PmvComf = PMV.from_individual_values(air_temperature=air_temp,
                                            rad_temperature=rad_temp,
                                            wind_speed=wind_speed,
                                            rel_humidity=rel_humid,
                                            met_rate=met_rate, clo_value=clo,
                                            external_work=external_work)

        assert myPmvComf.air_temperature == [air_temp]
        assert myPmvComf.rad_temperature == [rad_temp]
        assert myPmvComf.wind_speed == [wind_speed]
        assert myPmvComf.rel_humidity == [rel_humid]
        assert myPmvComf.met_rate == [met_rate]
        assert myPmvComf.clo_value == [clo]
        assert myPmvComf.external_work == [external_work]
        assert myPmvComf.ppd_comfort_thresh == ppd_comfort_thresh
        assert myPmvComf.humid_ratio_up == humid_ratio_up
        assert myPmvComf.humid_ratio_low == humid_ratio_low
        assert myPmvComf.still_air_threshold == still_air_thresh
        assert myPmvComf.single_values == True
        assert myPmvComf.is_data_aligned == False

        # myPmvComf & PmvComf should be different as thresholds not set
        assert myPmvComf.__dict__ != PmvComf.__dict__

        # Good to check general method to set comfort params
        PmvComf.set_comfort_par(ppd_comfort_thresh=ppd_comfort_thresh,
                                humid_ratio_up=humid_ratio_up,
                                humid_ratio_low=humid_ratio_low,
                                still_air_threshold=still_air_thresh)

        myPmvComf._check_and_align_lists()
        assert myPmvComf.__dict__ == PmvComf.__dict__

        # Check pmv, set and cooling effect are calculated properly
        pmv = myPmvComf.pmv
        ppd = myPmvComf.ppd
        set = myPmvComf.set
        cooling_effect = myPmvComf.cooling_effect

        assert round(pmv- (-1.74), 1) == 0
        assert round(ppd- 64, 1) < 5
        assert round(set- 18.7, 1) < 0.5
        assert round(cooling_effect -3.9, 1) == 0

    def test_setters_list_values(self):
        """Test low level list value setting functions"""
        myPmvComf = PMV()
        air_temp = [19, 19]
        rad_temp = [23, 23]
        wind_speed = [0.5, 0.5]
        rel_humid = [60, 60]
        met_rate = [1.5, 1.5]
        clo = [0.4, 0.4]
        external_work = [0, 0]

        # PmvComf model with values set up individually
        myPmvComf.air_temperature = air_temp
        myPmvComf.rad_temperature = rad_temp
        myPmvComf.wind_speed = wind_speed
        myPmvComf.rel_humidity = rel_humid
        myPmvComf.met_rate = met_rate
        myPmvComf.clo_value = clo
        myPmvComf.external_work = external_work

        # PmvComf model with value set up through class
        PmvComf = PMV(air_temperature=air_temp, rad_temperature=rad_temp,
                      wind_speed=wind_speed, rel_humidity=rel_humid, met_rate=met_rate,
                      clo_value=clo, external_work=external_work)

        assert myPmvComf.air_temperature == air_temp
        assert myPmvComf.rad_temperature == rad_temp
        assert myPmvComf.wind_speed == wind_speed
        assert myPmvComf.rel_humidity == rel_humid
        assert myPmvComf.met_rate == met_rate
        assert myPmvComf.clo_value == clo
        assert myPmvComf.external_work == external_work
        assert myPmvComf.single_values == False

        # Check that inputting values through __init__ or @setters results in same object
        assert myPmvComf.__dict__ == PmvComf.__dict__

        # Check pmv, set and cooling effect are calculated properly
        pmv = myPmvComf.pmv
        ppd = myPmvComf.ppd
        set = myPmvComf.set
        cooling_effect = myPmvComf.cooling_effect

        assert pmv[0] == pmv[1]
        assert ppd[0] == ppd[1]
        assert set[0] == set[1]
        assert cooling_effect[0] == cooling_effect[1]

        assert round(pmv[0]- (-1.74), 1) == 0
        assert round(ppd[0]- 64, 1) < 5
        assert round(set[0]- 18.7, 1) < 0.5
        assert round(cooling_effect[0] -3.9, 1) < 0.5 

    def test_from_single_values(self):
        """Test calculating PMV from a single set of values"""
        myPmvComf = PMV.from_individual_values(26, 26, 0.75, 80, 1.1, 0.5)
        pmv = myPmvComf.pmv
