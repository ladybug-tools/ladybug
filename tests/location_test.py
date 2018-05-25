# coding=utf-8

import unittest
from ladybug.location import Location


class LocationTestCase(unittest.TestCase):
    """Test for (ladybug/location.py)"""

    # preparing to test.
    def setUp(self):
        """set up."""
        pass

    def tearDown(self):
        """Nothing to tear down as nothing gets written to file."""
        pass

    def test_default_values(self):
        """Test if the command correctly creates a location."""
        loc = Location()
        self.assertEqual(loc.latitude, 0)

    def test_from_string(self):
        pass

    def test_set_values(self):
        pass


if __name__ == "__main__":
    unittest.main()
