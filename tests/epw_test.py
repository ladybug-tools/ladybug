# coding=utf-8

import unittest
import os
import pytest
from collections import OrderedDict

from ladybug.epw import EPW
from ladybug.datacollection import HourlyContinuousCollection, MonthlyCollection
from ladybug.designday import DesignDay
from ladybug.analysisperiod import AnalysisPeriod


class EPWTestCase(unittest.TestCase):
    """Test for (ladybug/epw.py)"""

    # preparing to test.
    def setUp(self):
        """set up."""
        pass

    def tearDown(self):
        """Nothing to tear down as nothing gets written to file."""
        pass

    def test_import_epw(self):
        """Test import standard epw."""
        relative_path = './tests/epw/chicago.epw'
        abs_path = os.path.abspath(relative_path)
        epw_rel = EPW(relative_path)
        epw = EPW(abs_path)

        assert epw_rel.file_path == os.path.normpath(relative_path)
        assert epw_rel.location.city == 'Chicago Ohare Intl Ap'
        assert epw.file_path == abs_path
        assert epw.location.city == 'Chicago Ohare Intl Ap'
        # Check that calling location getter only retrieves location
        assert epw.is_data_loaded is False
        dbt = epw.dry_bulb_temperature
        skyt = epw.sky_temperature  # test sky temperature calculation
        assert epw.is_data_loaded is True
        assert len(dbt) == 8760
        assert len(skyt) == 8760

    def test_import_tokyo_epw(self):
        """Test import custom epw with wrong types."""
        path = './tests/epw/tokyo.epw'
        epw = EPW(path)
        assert epw.is_header_loaded is False
        assert epw.location.city == 'Tokyo'
        assert epw.is_header_loaded is True
        assert epw.is_data_loaded is False
        dbt = epw.dry_bulb_temperature
        assert epw.is_data_loaded is True
        assert len(dbt) == 8760

    def test_invalid_epw(self):
        """Test the import of incorrect epw files."""
        path = './tests/epw/non-exitent.epw'
        with pytest.raises(Exception):
            epw = EPW(path)
            epw.location

    def test_non_epw(self):
        """Test the import of incorrect epw files."""
        path = './tests/stat/chicago.stat'
        with pytest.raises(Exception):
            epw = EPW(path)
            epw.location

    def test_import_design_conditions(self):
        """Test the functions that import design conditions."""
        relative_path = './tests/epw/chicago.epw'
        epw = EPW(relative_path)
        assert isinstance(epw.heating_design_condition_dictionary, OrderedDict)
        assert len(epw.heating_design_condition_dictionary.keys()) == 15
        assert isinstance(epw.cooling_design_condition_dictionary, OrderedDict)
        assert len(epw.cooling_design_condition_dictionary.keys()) == 32
        assert isinstance(epw.extreme_design_condition_dictionary, OrderedDict)
        assert len(epw.extreme_design_condition_dictionary.keys()) == 16

    def test_import_design_days(self):
        """Test the functions that import design days."""
        relative_path = './tests/epw/chicago.epw'
        epw = EPW(relative_path)
        assert isinstance(epw.annual_heating_design_day_996, DesignDay)
        assert epw.annual_heating_design_day_996.dry_bulb_condition.dry_bulb_max == -20.0
        assert isinstance(epw.annual_heating_design_day_990, DesignDay)
        assert epw.annual_heating_design_day_990.dry_bulb_condition.dry_bulb_max == -16.6
        assert isinstance(epw.annual_cooling_design_day_004, DesignDay)
        assert epw.annual_cooling_design_day_004.dry_bulb_condition.dry_bulb_max == 33.3
        assert isinstance(epw.annual_cooling_design_day_010, DesignDay)
        assert epw.annual_cooling_design_day_010.dry_bulb_condition.dry_bulb_max == 31.6

    def test_import_extreme_weeks(self):
        """Test the functions that import the extreme weeks."""
        relative_path = './tests/epw/chicago.epw'
        epw = EPW(relative_path)
        ext_cold = list(epw.extreme_cold_weeks.values())[0]
        ext_hot = list(epw.extreme_hot_weeks.values())[0]
        assert isinstance(ext_cold, AnalysisPeriod)
        assert len(ext_cold.doys_int) == 7
        assert (ext_cold.st_month, ext_cold.st_day, ext_cold.end_month,
                ext_cold.end_day) == (1, 27, 2, 2)
        assert isinstance(ext_hot, AnalysisPeriod)
        assert len(ext_hot.doys_int) == 7
        assert (ext_hot.st_month, ext_hot.st_day, ext_hot.end_month,
                ext_hot.end_day) == (7, 13, 7, 19)

    def test_import_typical_weeks(self):
        """Test the functions that import the typical weeks."""
        relative_path = './tests/epw/chicago.epw'
        epw = EPW(relative_path)
        typ_weeks = list(epw.typical_weeks.values())
        assert len(typ_weeks) == 4
        for week in typ_weeks:
            assert isinstance(week, AnalysisPeriod)
            assert len(week.doys_int) == 7

    def test_import_ground_temperatures(self):
        """Test the functions that import ground temprature."""
        relative_path = './tests/epw/chicago.epw'
        epw = EPW(relative_path)
        assert len(epw.monthly_ground_temperature.keys()) == 3
        assert tuple(epw.monthly_ground_temperature.keys()) == (0.5, 2.0, 4.0)
        assert isinstance(epw.monthly_ground_temperature[0.5], MonthlyCollection)
        assert epw.monthly_ground_temperature[0.5].values == \
            (-1.89, -3.06, -0.99, 2.23, 10.68, 17.2,
             21.6, 22.94, 20.66, 15.6, 8.83, 2.56)
        assert epw.monthly_ground_temperature[2].values == \
            (2.39, 0.31, 0.74, 2.45, 8.1, 13.21,
             17.3, 19.5, 19.03, 16.16, 11.5, 6.56)
        assert epw.monthly_ground_temperature[4].values == \
            (5.93, 3.8, 3.34, 3.98, 7.18, 10.62,
             13.78, 15.98, 16.49, 15.25, 12.51, 9.17)

    def test_epw_header(self):
        """Check that the process of parsing the EPW header hasn't mutated it."""
        relative_path = './tests/epw/chicago.epw'
        epw = EPW(relative_path)
        for char1, char2 in zip(''.join(epw.header), ''.join(epw._header)):
            assert char1 == char2

    def test_save_epw(self):
        """Test save epw_rel."""
        path = './tests/epw/tokyo.epw'
        epw = EPW(path)

        modified_path = './tests/epw/tokyo_modified.epw'
        epw.save(modified_path)
        assert os.path.isfile(modified_path)
        assert os.stat(modified_path).st_size > 1
        os.remove(modified_path)

    def test_save_wea(self):
        """Test save wea_rel."""
        path = './tests/epw/chicago.epw'
        epw = EPW(path)

        wea_path = './tests/wea/chicago_epw.wea'

        epw.to_wea(wea_path)
        assert os.path.isfile(wea_path)
        assert os.stat(wea_path).st_size > 1

        # check the order of the data in the file
        with open(wea_path) as wea_f:
            line = wea_f.readlines()
            assert float(line[6].split(' ')[-2]) == epw.direct_normal_radiation[0]
            assert float(line[6].split(' ')[-1]) == epw.diffuse_horizontal_radiation[0]
            assert float(line[17].split(' ')[-2]) == epw.direct_normal_radiation[11]
            assert float(line[17].split(' ')[-1]) == epw.diffuse_horizontal_radiation[11]

        os.remove(wea_path)


if __name__ == "__main__":
    unittest.main()
