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

    def test_epw_location(self):
        """Test epw location."""
        pass

    def test_to_and_from_json(self):
        """Test json serialization and deserialization methods"""
        path = './tests/epw/tokyo.epw'
        self.maxDiff = None
        epw = EPW(path)
        epw._import_data()
        json_epw = epw.to_json()
        new_data = []

        # shortening the json file to make it quicker to test
        for collection in json_epw['data']:
            new_collection = {
                'header': collection['header'],
                'data': collection['data'][0:30]
            }
            new_data.append(new_collection)

        json_epw['data'] = new_data

        epw_from_json = EPW.from_json(json_epw)
        cloned_epw = epw_from_json.to_json()
        # assert cmp(json_epw, cloned_epw) == 0
        self.assertDictEqual(json_epw, cloned_epw)


if __name__ == "__main__":
    unittest.main()
