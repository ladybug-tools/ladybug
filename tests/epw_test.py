# coding=utf-8

import unittest
import os
from ladybug.epw import EPW


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
        assert epw.is_data_loaded is True
        assert len(dbt) == 8760

    def test_import_tokyo_epw(self):
        """Test import custom epw with wrong types."""
        path = './tests/epw/tokyo.epw'

        epw = EPW(path)
        assert epw.is_location_loaded is False
        assert epw.location.city == 'Tokyo'
        assert epw.is_location_loaded is True
        assert epw.is_data_loaded is False
        dbt = epw.dry_bulb_temperature
        assert epw.is_data_loaded is True
        assert len(dbt) == 8760

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
            lines = wea_f.readlines()
            assert float(lines[6].split(' ')[-2]) == \
                epw.direct_normal_radiation[0].value
            assert float(lines[6].split(' ')[-1]) == \
                epw.diffuse_horizontal_radiation[0].value
            assert float(lines[17].split(' ')[-2]) == \
                epw.direct_normal_radiation[11].value
            assert float(lines[17].split(' ')[-1]) == \
                epw.diffuse_horizontal_radiation[11].value

        os.remove(wea_path)


if __name__ == "__main__":
    unittest.main()
