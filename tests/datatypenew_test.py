# coding=utf-8
from __future__ import division

import unittest
import pytest
from ladybug.datatypenew import DataTypes
from ladybug.datatypenew import DataTypeBase

class DataTypesTestCase(unittest.TestCase):
    """Test for (ladybug/datatype.py)"""

    # preparing to test.
    def setUp(self):
        """set up."""

    def tearDown(self):
        """Nothing to tear down as nothing gets written to file."""
        pass

    def test_all_possible_units(self):
        """Check to be sure that we can get all currently supported units."""
        all_types = DataTypes.all_possible_units()
        assert len(all_types.split('\n')) == len(DataTypes().BASETYPES)

    def test_type_by_name(self):
        """Check the type_by_name methods."""
        all_types = DataTypes().TYPES
        for typ in all_types.keys():
            assert hasattr(DataTypes.type_by_name(typ), 'isDataType')

    def test_type_by_unit(self):
        """Check the type_by_unit method."""
        all_types = DataTypes().BASETYPES
        for typ in range(len(all_types)):
            typ_units = all_types[typ].units
            for u in typ_units:
                assert hasattr(DataTypes.type_by_unit(u), 'isDataType')

    def test_type_by_name_and_unit(self):
        """Check the type_by_unit method."""
        all_types = DataTypes().BASETYPES
        for typ in range(len(all_types)):
            typ_name = all_types[typ].name
            typ_units = all_types[typ].units
            for u in typ_units:
                assert hasattr(DataTypes.type_by_name_and_unit(
                    typ_name, u), 'isDataType')

    def test_unitless_type(self):
        """Test the creation of generic types."""
        test_type = DataTypes.type_by_name_and_unit('Test Type', None)
        assert hasattr(test_type, 'isDataType')

    def test_generic_type(self):
        """Test the creation of generic types."""
        test_type = DataTypes.type_by_name_and_unit('Test Type', 'widgets')
        assert hasattr(test_type, 'isDataType')
        assert test_type.is_unit_acceptable('widgets')

    def test_json_methods(self):
        """Test to_json and from_json methods."""
        test_type = DataTypes.type_by_name_and_unit('Test Type', 'widgets')
        test_json = test_type.to_json()
        assert test_json == DataTypeBase.from_json(test_json).to_json()

        temp_type = DataTypes.type_by_name('Temperature')
        temp_json = temp_type.to_json()
        assert temp_json == DataTypeBase.from_json(temp_json).to_json()

    def test_temperature(self):
        """Test Temperature type."""
        temp_type = DataTypes.type_by_name('Temperature')
        for unit in temp_type.units:
            assert temp_type.to_unit([1], unit, unit)[0] == pytest.approx(1, rel=1e-5)
            ip_vals, ip_u = temp_type.to_ip([1], unit)
            assert len(ip_vals) == 1
            si_vals, si_u = temp_type.to_si([1], unit)
            assert len(si_vals) == 1
            for other_unit in temp_type.units:
                assert len(temp_type.to_unit([1], other_unit, unit)) == 1
        assert temp_type.to_unit([1], 'F', 'C')[0] == pytest.approx(33.8, rel=1e-1)
        assert temp_type.to_unit([1], 'K', 'C')[0] == pytest.approx(274.15, rel=1e-1)
        assert temp_type.to_unit([1], 'C', 'F')[0] == pytest.approx(-17.2222, rel=1e-1)
        assert temp_type.to_unit([1], 'C', 'K')[0] == pytest.approx(-272.15, rel=1e-1)

    def test_percentage(self):
        """Test Percentage type."""
        pct_type = DataTypes.type_by_name('Percentage')
        for unit in pct_type.units:
            assert pct_type.to_unit([1], unit, unit)[0] == pytest.approx(1, rel=1e-5)
            ip_vals, ip_u = pct_type.to_ip([1], unit)
            assert len(ip_vals) == 1
            si_vals, si_u = pct_type.to_si([1], unit)
            assert len(si_vals) == 1
            for other_unit in pct_type.units:
                assert len(pct_type.to_unit([1], other_unit, unit)) == 1
        assert pct_type.to_unit([1], 'fraction', '%')[0] == 0.01
        assert pct_type.to_unit([1], 'tenths', '%')[0] == 0.1
        assert pct_type.to_unit([1], 'thousandths', '%')[0] == 10
        assert pct_type.to_unit([1], '%', 'fraction')[0] == 100
        assert pct_type.to_unit([1], '%', 'tenths')[0] == 10
        assert pct_type.to_unit([1], '%', 'thousandths')[0] == 0.1

    def test_distance(self):
        """Test Distance type."""
        dist_type = DataTypes.type_by_name('Distance')
        for unit in dist_type.units:
            assert dist_type.to_unit([1], unit, unit)[0] == pytest.approx(1, rel=1e-5)
            ip_vals, ip_u = dist_type.to_ip([1], unit)
            assert len(ip_vals) == 1
            si_vals, si_u = dist_type.to_si([1], unit)
            assert len(si_vals) == 1
            for other_unit in dist_type.units:
                assert len(dist_type.to_unit([1], other_unit, unit)) == 1
        assert dist_type.to_unit([1], 'ft', 'm')[0] == pytest.approx(3.28084, rel=1e-2)
        assert dist_type.to_unit([1], 'mm', 'm')[0] == 1000
        assert dist_type.to_unit([1], 'in', 'm')[0] == pytest.approx(39.3701, rel=1e-1)
        assert dist_type.to_unit([1], 'km', 'm')[0] == 0.001
        assert dist_type.to_unit([1], 'mi', 'm')[0] == pytest.approx(1 / 1609.344, rel=1e-1)
        assert dist_type.to_unit([1], 'cm', 'm')[0] == 100
        assert dist_type.to_unit([1], 'm', 'ft')[0] == pytest.approx(1 / 3.28084, rel=1e-2)
        assert dist_type.to_unit([1], 'm', 'mm')[0] == 0.001
        assert dist_type.to_unit([1], 'm', 'in')[0] == pytest.approx(1 / 39.3701, rel=1e-1)
        assert dist_type.to_unit([1], 'm', 'km')[0] == 1000
        assert dist_type.to_unit([1], 'm', 'mi')[0] == pytest.approx(1609.344, rel=1e-1)
        assert dist_type.to_unit([1], 'm', 'cm')[0] == 0.01

    def test_area(self):
        """Test Area type."""
        area_type = DataTypes.type_by_name('Area')
        for unit in area_type.units:
            assert area_type.to_unit([1], unit, unit)[0] == pytest.approx(1, rel=1e-5)
            ip_vals, ip_u = area_type.to_ip([1], unit)
            assert len(ip_vals) == 1
            si_vals, si_u = area_type.to_si([1], unit)
            assert len(si_vals) == 1
            for other_unit in area_type.units:
                assert len(area_type.to_unit([1], other_unit, unit)) == 1
        assert area_type.to_unit([1], 'ft2', 'm2')[0] == pytest.approx(10.7639, rel=1e-2)
        assert area_type.to_unit([1], 'mm2', 'm2')[0] == 1000000
        assert area_type.to_unit([1], 'in2', 'm2')[0] == pytest.approx(1550, rel=1e-1)
        assert area_type.to_unit([1], 'km2', 'm2')[0] == 0.000001
        assert area_type.to_unit([1], 'mi2', 'm2')[0] == pytest.approx(1 / 2590000, rel=1e-8)
        assert area_type.to_unit([1], 'cm2', 'm2')[0] == 10000
        assert area_type.to_unit([1], 'ha', 'm2')[0] == 0.0001
        assert area_type.to_unit([1], 'acre', 'm2')[0] == pytest.approx(1 / 4046.86, rel=1e-8)
        assert area_type.to_unit([1], 'm2', 'ft2')[0] == pytest.approx(1 / 10.7639, rel=1e-3)
        assert area_type.to_unit([1], 'm2', 'mm2')[0] == 0.000001
        assert area_type.to_unit([1], 'm2', 'in2')[0] == pytest.approx(1 / 1550, rel=1e-4)
        assert area_type.to_unit([1], 'm2', 'km2')[0] == 1000000
        assert area_type.to_unit([1], 'm2', 'mi2')[0] == pytest.approx(2590000, rel=1e-1)
        assert area_type.to_unit([1], 'm2', 'cm2')[0] == 0.0001
        assert area_type.to_unit([1], 'm2', 'ha')[0] == 10000
        assert area_type.to_unit([1], 'm2', 'acre')[0] == pytest.approx(4046.86, rel=1e-1)

    def test_pressure(self):
        """Test Pressure type."""
        press_type = DataTypes.type_by_name('Pressure')
        for unit in press_type.units:
            assert press_type.to_unit([1], unit, unit)[0] == pytest.approx(1, rel=1e-5)
            ip_vals, ip_u = press_type.to_ip([1], unit)
            assert len(ip_vals) == 1
            si_vals, si_u = press_type.to_si([1], unit)
            assert len(si_vals) == 1
            for other_unit in press_type.units:
                assert len(press_type.to_unit([1], other_unit, unit)) == 1
        assert press_type.to_unit([1], 'inHg', 'Pa')[0] == pytest.approx(0.0002953, rel=1e-5)
        assert press_type.to_unit([1], 'atm', 'Pa')[0] == pytest.approx(1 / 101325, rel=1e-7)
        assert press_type.to_unit([1], 'bar', 'Pa')[0] == 0.00001
        assert press_type.to_unit([1], 'Torr', 'Pa')[0] == pytest.approx(0.00750062, rel=1e-5)
        assert press_type.to_unit([1], 'psi', 'Pa')[0] == pytest.approx(0.000145038, rel=1e-5)
        assert press_type.to_unit([1], 'inH2O', 'Pa')[0] == pytest.approx(0.00401865, rel=1e-5)
        assert press_type.to_unit([1], 'Pa', 'inHg')[0] == pytest.approx(1 / 0.0002953, rel=1e-1)
        assert press_type.to_unit([1], 'Pa', 'atm')[0] == pytest.approx(101325, rel=1e-1)
        assert press_type.to_unit([1], 'Pa', 'bar')[0] == 100000
        assert press_type.to_unit([1], 'Pa', 'Torr')[0] == pytest.approx(1 / 0.00750062, rel=1e-1)
        assert press_type.to_unit([1], 'Pa', 'psi')[0] == pytest.approx(1 / 0.000145038, rel=1e-1)
        assert press_type.to_unit([1], 'Pa', 'inH2O')[0] == pytest.approx(1 / 0.00401865, rel=1e-1)


if __name__ == "__main__":
    unittest.main()
