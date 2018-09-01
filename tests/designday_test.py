# coding=utf-8

import unittest
import os
from ladybug.designday import Ddy


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

    def test_standard_ddy_properties(self):
        """Test properties of a standard ddy."""
        relative_path = './tests/ddy/tokyo.ddy'

        ddy = Ddy.from_ddy_file(relative_path)

        # Test accuracy of import
        assert ddy.location.city == 'TOKYO HYAKURI_JPN Design_Conditions'
        assert ddy.location.latitude - 36.18 < 0.1
        assert ddy.location.longitude - 140.42 < 0.1
        assert ddy.location.time_zone == 9
        assert ddy.location.elevation == 35

        assert len(ddy.design_days) == 18
        for des_day in ddy.design_days:
            assert hasattr(des_day, 'isDesignDay')
        assert len(ddy.filter_by_keyword('.4%')) == 4
        assert len(ddy.filter_by_keyword('99.6%')) == 3

    def test_monthly_ddy_properties(self):
        """Test properties of a standard ddy."""
        relative_path = './tests/ddy/chicago_monthly.ddy'

        ddy = Ddy.from_ddy_file(relative_path)

        # Test accuracy of import
        assert ddy.location.city == 'Chicago Ohare Intl Ap'
        assert ddy.location.latitude - 41.96 < 0.1
        assert ddy.location.longitude - 87.92 < 0.1
        assert ddy.location.time_zone == -6
        assert ddy.location.elevation == 201

        assert len(ddy.design_days) == 12
        for des_day in ddy.design_days:
            assert hasattr(des_day, 'isDesignDay')


if __name__ == "__main__":
    unittest.main()
