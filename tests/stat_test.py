# coding=utf-8

import unittest
import os
from ladybug.stat import Stat


class StatTestCase(unittest.TestCase):
    """Test for (ladybug/stat.py)"""

    # preparing to test.
    def setUp(self):
        """set up."""
        pass

    def tearDown(self):
        """Nothing to tear down as nothing gets written to file."""
        pass

    def test_import_stat(self):
        """Test import standard stat."""
        relative_path = './tests/stat/tokyo.stat'
        abs_path = os.path.abspath(relative_path)

        stat_rel = Stat(relative_path)
        stat = Stat(abs_path)

        # Test imports don't break
        assert stat.file_path == abs_path
        assert stat_rel.file_path == os.path.normpath(relative_path)
        assert stat.is_data_loaded is False
        assert stat.header == stat_rel.header
        assert stat.is_data_loaded is True

        # Test accuracy of import
        assert stat.location.city == 'TOKYO HYAKURI'
        assert stat.location.country == 'JPN'
        assert stat.location.source == 'IWEC Data'
        assert stat.location.station_id == '477150'
        assert stat.location.latitude - 36.18 < 0.1
        assert stat.location.longitude - 140.42 < 0.1
        assert stat.location.time_zone == 9
        assert stat.location.elevation == 35

        assert stat.monthly_tau_beam == \
            [0.341, 0.392, 0.48, 0.601, 0.654, 0.632, 0.553, 0.546, 0.473, 0.423, 0.388,
             0.338]
        assert stat.monthly_tau_diffuse == \
            [2.214, 1.999, 1.765, 1.546, 1.501, 1.591, 1.811, 1.827, 2.024, 2.083, 2.105,
             2.267]
        assert stat.ashrae_climate_zone == '4A'
        assert stat.koppen_climate_zone == 'Cfa'


if __name__ == "__main__":
    unittest.main()
