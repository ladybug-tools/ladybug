# coding=utf-8

import unittest
import pytest
from ladybug.dt import DateTime
from ladybug.datatype import DataTypeBase, DryBulbTemperature


class DataTypeBaseTestCase(unittest.TestCase):
    """Test for (ladybug/datatype.py)"""

    # preparing to test.
    def setUp(self):
        """set up."""

    def tearDown(self):
        """Nothing to tear down as nothing gets written to file."""
        pass

    def test__init__nothing(self):
        """Fails to init without a value"""
        with pytest.raises(Exception):
            DataTypeBase()

    def test__init__wrong_data(self):
        """Can init with wrong values"""
        value = 3
        dt = DateTime()
        standard = 'International System of Units'
        nickname = 'myFavouriteUnit'
        with pytest.raises(Exception):
            DataTypeBase(value, datetime=dt, standard=standard, nickname=nickname)

    def test__init__success(self):
        """Can init with just value or with extra data"""
        value = 3
        dt = DateTime()
        standard = 'SI'
        nickname = 'myFavouriteUnit'

        dtb = DataTypeBase(value, datetime=dt, standard=standard, nickname=nickname)

        assert dtb.value == value
        assert dtb.datetime == dt
        assert dtb.standard == standard
        assert dtb.nickname == nickname

        dtb = DataTypeBase(value)
        assert dtb.value == value

    def test_json_methods(self):
        """Test the JSON serialization functions"""
        value = 3
        dt = DateTime()
        standard = 'SI'
        nickname = 'myFavouriteUnit'

        dtb = DataTypeBase(value, datetime=dt, standard=standard, nickname=nickname)
        dtb_from_json = DataTypeBase.from_json(dtb.to_json())

        assert dtb_from_json.value == value
        assert dtb_from_json.datetime == dt
        assert dtb_from_json.standard == standard
        assert dtb_from_json.nickname == nickname


class DataPointTestCase(unittest.TestCase):
    """Test for (ladybug/datatype.py)"""

    # preparing to test.
    def setUp(self):
        """set up."""

    def tearDown(self):
        """Nothing to tear down as nothing gets written to file."""
        pass


class DryBulbTemperatureTestCase(unittest.TestCase):
    """Test for DrybulbTemperature class of ladybug/datatype.py)"""

    def setup(self):
        """set up."""

    def test_init(self):
        t = 20
        temp = DryBulbTemperature(t)
        json_data = {
            'value': t,
            'datetime': {},
            'standard': 'SI',
            'nickname': None,
            'type': 'DryBulbTemperature'
        }

        assert temp.to_json() == json_data
        assert temp.to_ip == t * 9 / 5 + 32


if __name__ == "__main__":
    unittest.main()
