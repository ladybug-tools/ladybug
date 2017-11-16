# coding=utf-8

import unittest
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
        pass

    def test_import_tokyo_epw(self):
        """Test import custom epw with wrong types."""
        pass

    def test_epw_location(self):
        """Test epw location."""
        pass


if __name__ == "__main__":
    unittest.main()
