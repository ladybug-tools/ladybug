# coding=utf-8

import unittest
import os
from ladybug.location import Location
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.designday import \
    Ddy, \
    DesignDay


class DdyTestCase(unittest.TestCase):
    """Test for (ladybug/designday.py)"""

    # preparing to test.
    def setUp(self):
        """set up."""
        pass

    def tearDown(self):
        """Nothing to tear down as nothing gets written to file."""
        pass

    def test_import_ddy(self):
        """Test import standard ddy."""
        relative_path = './tests/ddy/chicago.ddy'
        abs_path = os.path.abspath(relative_path)

        ddy_rel = Ddy.from_ddy_file(relative_path)
        ddy = Ddy.from_ddy_file(abs_path)

        # Test imports don't break
        assert ddy.file_path == abs_path
        assert ddy_rel.file_path == os.path.normpath(relative_path)
        assert ddy.file_name == 'chicago.ddy'

    def test_ddy_from_design_day(self):
        """Test ddy from design day method."""
        relative_path = './tests/ddy/chicago_monthly.ddy'
        ddy = Ddy.from_ddy_file(relative_path)
        new_ddy = Ddy.from_design_day(ddy.design_days[0])
        assert ddy.location == new_ddy.location
        assert ddy.design_days[0] == new_ddy.design_days[0]

    def test_standard_ddy_properties(self):
        """Test properties of a standard ddy."""
        relative_path = './tests/ddy/tokyo.ddy'

        ddy = Ddy.from_ddy_file(relative_path)

        # Test accuracy of import
        assert ddy.location.city == 'TOKYO HYAKURI_JPN Design_Conditions'
        assert -0.1 < ddy.location.latitude - 36.18 < 0.1
        assert -0.1 < ddy.location.longitude - 140.42 < 0.1
        assert ddy.location.time_zone == 9
        assert ddy.location.elevation == 35

        assert len(ddy.design_days) == 18
        for des_day in ddy.design_days:
            assert hasattr(des_day, 'isDesignDay')
        assert len(ddy.filter_by_keyword('.4%')) == 4
        assert len(ddy.filter_by_keyword('99.6%')) == 3

    def test_monthly_ddy_properties(self):
        """Test properties of a monthly ddy."""
        relative_path = './tests/ddy/chicago_monthly.ddy'
        ddy = Ddy.from_ddy_file(relative_path)

        # Test accuracy of import
        assert ddy.location.city == 'Chicago Ohare Intl Ap'
        assert -0.1 < ddy.location.latitude - 41.96 < 0.1
        assert -0.1 < ddy.location.longitude + 87.92 < 0.1
        assert ddy.location.time_zone == -6
        assert ddy.location.elevation == 201

        assert len(ddy.design_days) == 12
        for des_day in ddy.design_days:
            assert hasattr(des_day, 'isDesignDay')
            assert des_day.day_type == 'SummerDesignDay'

    def test_design_day_from_properties(self):
        """Test hourly data properties of a standard ddy."""
        location = Location('Test City', 'USA', 34.20, -118.35, -8, 226)
        a_period = AnalysisPeriod(12, 21, 0, 12, 21, 23)
        des_day = DesignDay.from_design_day_properties('Test Day', 'WinterDesignDay',
                                                       location, a_period, 3.9, 0,
                                                       'Wetbulb', 3.9, 98639, 0.8, 330,
                                                       'ASHRAEClearSky', [0])
        assert des_day.location == location
        new_period = des_day.analysis_period
        assert new_period.st_month == a_period.st_month
        assert new_period.st_day == a_period.st_day
        assert new_period.st_hour == a_period.st_hour
        assert new_period.end_month == a_period.end_month
        assert new_period.end_day == a_period.end_day
        assert new_period.end_hour == a_period.end_hour

    def test_design_day_hourly_data_properties(self):
        """Test hourly data properties of a standard ddy."""
        location = Location('Test City', 'USA', 34.20, -118.35, -8, 226)
        a_period = AnalysisPeriod(8, 21, 0, 8, 21, 23)
        des_day = DesignDay.from_design_day_properties('Test Day', 'SummerDesignDay',
                                                       location, a_period, 36.8, 13.2,
                                                       'Wetbulb', 20.5, 98639, 3.9, 170,
                                                       'ASHRAETau', [0.436, 2.106])
        # dry bulb values
        db_data_collect = des_day.hourly_dry_bulb_data.values
        assert -0.1 < db_data_collect[5] - 23.6 < 0.1
        assert -0.1 < db_data_collect[14] - 36.8 < 0.1

        # dew point values
        dpt_data_collect = des_day.hourly_dew_point_data.values
        assert -0.1 < dpt_data_collect[0] - 11.296 < 0.1
        assert -0.1 < dpt_data_collect[-1] - 11.296 < 0.1

        # relative humidity values
        rh_data_collect = des_day.hourly_relative_humidity_data.values
        assert -0.1 < rh_data_collect[5] - 45.896 < 0.1
        assert -0.1 < rh_data_collect[14] - 21.508 < 0.1

        # barometric pressure values
        bp_data_collect = des_day.hourly_barometric_pressure_data.values
        assert -1 < bp_data_collect[0] - 98639 < 1
        assert -1 < bp_data_collect[-1] - 98639 < 1

        # wind speed values
        ws_data_collect = des_day.hourly_wind_speed_data.values
        assert -0.1 < ws_data_collect[0] - 3.9 < 0.1
        assert -0.1 < ws_data_collect[-1] - 3.9 < 0.1

        # wind direction values
        wd_data_collect = des_day.hourly_wind_direction_data.values
        assert -0.1 < wd_data_collect[0] - 170 < 0.1
        assert -0.1 < wd_data_collect[-1] - 170 < 0.1

        # radiation values
        direct_normal_rad, diffuse_horizontal_rad, global_horizontal_rad = \
            des_day.hourly_solar_radiation_data
        assert direct_normal_rad.values[0] == 0
        assert -0.1 < direct_normal_rad.values[11] - 891.46 < 0.1
        assert diffuse_horizontal_rad.values[0] == 0
        assert -0.1 < diffuse_horizontal_rad.values[11] - 165.32 < 0.1
        assert global_horizontal_rad.values[0] == 0
        assert -0.1 < global_horizontal_rad.values[11] - 985.05 < 0.1


if __name__ == "__main__":
    unittest.main()
