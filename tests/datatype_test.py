# coding=utf-8
from __future__ import division

from ladybug import datatype
from ladybug.datatype import base
from ladybug.datatype import angle, area, distance, energy, energyflux, \
    energyintensity, fraction, generic, illuminance, luminance, mass, massflowrate, \
    power, pressure, rvalue, speed, temperature, temperaturedelta, temperaturetime, \
    thermalcondition, time, specificenergy, uvalue, volume, volumeflowrate, \
    volumeflowrateintensity, voltage, current

import pytest
import math
PI = math.pi


def test_global_properties():
    """Test the global properties like TYPES, BASETYPES, and UNITS."""
    assert isinstance(datatype.TYPES, tuple)
    assert isinstance(datatype.BASETYPES, tuple)
    assert isinstance(datatype.UNITS, dict)
    assert isinstance(datatype.TYPESDICT, dict)


def test_from_dict():
    """Test the from dict method."""
    sample_dict = {'name': 'Temperature',
                   'data_type': 'Temperature',
                   'base_unit': 'C'}
    new_temp = base.DataTypeBase.from_dict(sample_dict)
    assert isinstance(new_temp, temperature.Temperature)


def test_to_from_dict():
    """Test the to/from dict methods."""
    my_temp = temperature.Temperature()
    temp_dict = my_temp.to_dict()
    new_temp = base.DataTypeBase.from_dict(temp_dict)
    new_temp = base.DataTypeBase.from_dict(temp_dict)
    assert new_temp.to_dict() == temp_dict


def test_dict_generic():
    """Test the from dict for a generic type."""
    unit_descr = {-1: 'High', 0: 'Medium', 1: 'High'}
    test_type = generic.GenericType('Test Type', 'widgets', unit_descr=unit_descr)
    sample_dict = test_type.to_dict()
    new_type = base.DataTypeBase.from_dict(sample_dict)
    assert isinstance(new_type, base.DataTypeBase)
    assert new_type.unit_descr == unit_descr


def test_generic_type():
    """Test the creation of generic types."""
    test_type = generic.GenericType('Test Type', 'widgets')
    assert isinstance(test_type, base.DataTypeBase)
    assert test_type.is_unit_acceptable('widgets')


def test_temperature():
    """Test Temperature type."""
    temp_type = temperature.Temperature()
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


def test_temperaturedelta():
    """Test TemperatureDelta type."""
    temp_type = temperaturedelta.TemperatureDelta()
    for unit in temp_type.units:
        assert temp_type.to_unit([1], unit, unit)[0] == pytest.approx(1, rel=1e-5)
        ip_vals, ip_u = temp_type.to_ip([1], unit)
        assert len(ip_vals) == 1
        si_vals, si_u = temp_type.to_si([1], unit)
        assert len(si_vals) == 1
        for other_unit in temp_type.units:
            assert len(temp_type.to_unit([1], other_unit, unit)) == 1
    assert temp_type.to_unit([1], 'dF', 'dC')[0] == pytest.approx(1.8, rel=1e-1)
    assert temp_type.to_unit([1], 'dK', 'dC')[0] == pytest.approx(1, rel=1e-1)
    assert temp_type.to_unit([1], 'dC', 'dF')[0] == pytest.approx(0.5555, rel=1e-1)
    assert temp_type.to_unit([1], 'dC', 'dK')[0] == pytest.approx(1, rel=1e-1)


def test_temperaturetime():
    """Test TemperatureTime type."""
    temp_type = temperaturetime.TemperatureTime()
    for unit in temp_type.units:
        assert temp_type.to_unit([1], unit, unit)[0] == pytest.approx(1, rel=1e-5)
        ip_vals, ip_u = temp_type.to_ip([1], unit)
        assert len(ip_vals) == 1
        si_vals, si_u = temp_type.to_si([1], unit)
        assert len(si_vals) == 1
        for other_unit in temp_type.units:
            assert len(temp_type.to_unit([1], other_unit, unit)) == 1
    assert temp_type.to_unit([1], 'degF-days', 'degC-days')[0] == pytest.approx(1.8, rel=1e-1)
    assert temp_type.to_unit([1], 'degC-hours', 'degC-days')[0] == pytest.approx(24, rel=1e-3)
    assert temp_type.to_unit([1], 'degF-hours', 'degC-days')[0] == pytest.approx(43.2, rel=1e-1)
    assert temp_type.to_unit([1], 'degC-days', 'degF-days')[0] == pytest.approx(0.5555, rel=1e-1)
    assert temp_type.to_unit([1], 'degC-days', 'degC-hours')[0] == pytest.approx(1 / 24, rel=1e-1)
    assert temp_type.to_unit([1], 'degC-days', 'degF-hours')[0] == pytest.approx(0.023148, rel=1e-1)


def test_fraction():
    """Test Fraction type."""
    pct_type = fraction.Fraction()
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


def test_distance():
    """Test Distance type."""
    dist_type = distance.Distance()
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


def test_area():
    """Test Area type."""
    area_type = area.Area()
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


def test_volume():
    """Test Volume type."""
    vol_type = volume.Volume()
    for unit in vol_type.units:
        assert vol_type.to_unit([1], unit, unit)[0] == pytest.approx(1, rel=1e-5)
        ip_vals, ip_u = vol_type.to_ip([1], unit)
        assert len(ip_vals) == 1
        si_vals, si_u = vol_type.to_si([1], unit)
        assert len(si_vals) == 1
        for other_unit in vol_type.units:
            assert len(vol_type.to_unit([1], other_unit, unit)) == 1
    assert vol_type.to_unit([1], 'ft3', 'm3')[0] == pytest.approx(35.3147, rel=1e-2)
    assert vol_type.to_unit([1], 'mm3', 'm3')[0] == 1e+9
    assert vol_type.to_unit([1], 'in3', 'm3')[0] == pytest.approx(61023.7, rel=1e-1)
    assert vol_type.to_unit([1], 'km3', 'm3')[0] == 0.000000001
    assert vol_type.to_unit([1], 'mi3', 'm3')[0] == pytest.approx(1 / 4.168e+9, rel=1e-8)
    assert vol_type.to_unit([1], 'L', 'm3')[0] == 1000
    assert vol_type.to_unit([1], 'mL', 'm3')[0] == 1000000
    assert vol_type.to_unit([1], 'gal', 'm3')[0] == pytest.approx(264.172, rel=1e-1)
    assert vol_type.to_unit([1], 'fl oz', 'm3')[0] == pytest.approx(33814, rel=1e-1)
    assert vol_type.to_unit([1], 'm3', 'ft3')[0] == pytest.approx(1 / 35.3147, rel=1e-3)
    assert vol_type.to_unit([1], 'm3', 'mm3')[0] == 0.000000001
    assert vol_type.to_unit([1], 'm3', 'in3')[0] == pytest.approx(1 / 61023.7, rel=1e-5)
    assert vol_type.to_unit([1], 'm3', 'km3')[0] == 1e+9
    assert vol_type.to_unit([1], 'm3', 'mi3')[0] == pytest.approx(4.168e+9, rel=1e-1)
    assert vol_type.to_unit([1], 'm3', 'L')[0] == 0.001
    assert vol_type.to_unit([1], 'm3', 'mL')[0] == 0.000001
    assert vol_type.to_unit([1], 'm3', 'gal')[0] == pytest.approx(1 / 264.172, rel=1e-4)
    assert vol_type.to_unit([1], 'm3', 'fl oz')[0] == pytest.approx(1 / 33814, rel=1e-5)


def test_pressure():
    """Test Pressure type."""
    press_type = pressure.Pressure()
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


def test_energy():
    """Test Energy type."""
    energy_type = energy.Energy()
    for unit in energy_type.units:
        assert energy_type.to_unit([1], unit, unit)[0] == pytest.approx(1, rel=1e-5)
        ip_vals, ip_u = energy_type.to_ip([1], unit)
        assert len(ip_vals) == 1
        si_vals, si_u = energy_type.to_si([1], unit)
        assert len(si_vals) == 1
        for other_unit in energy_type.units:
            assert len(energy_type.to_unit([1], other_unit, unit)) == 1
    assert energy_type.to_unit([1], 'kBtu', 'kWh')[0] == pytest.approx(3.41214, rel=1e-2)
    assert energy_type.to_unit([1], 'Wh', 'kWh')[0] == 1000
    assert energy_type.to_unit([1], 'Btu', 'kWh')[0] == pytest.approx(3412.14, rel=1e-1)
    assert energy_type.to_unit([1], 'MMBtu', 'kWh')[0] == pytest.approx(0.00341214, rel=1e-5)
    assert energy_type.to_unit([1], 'J', 'kWh')[0] == 3600000
    assert energy_type.to_unit([1], 'kJ', 'kWh')[0] == 3600
    assert energy_type.to_unit([1], 'MJ', 'kWh')[0] == 3.6
    assert energy_type.to_unit([1], 'GJ', 'kWh')[0] == 0.0036
    assert energy_type.to_unit([1], 'therm', 'kWh')[0] == pytest.approx(0.0341214, rel=1e-5)
    assert energy_type.to_unit([1], 'cal', 'kWh')[0] == pytest.approx(860421, rel=1e-1)
    assert energy_type.to_unit([1], 'kcal', 'kWh')[0] == pytest.approx(860.421, rel=1e-2)
    assert energy_type.to_unit([1], 'kWh', 'kBtu')[0] == pytest.approx(1 / 3.41214, rel=1e-2)
    assert energy_type.to_unit([1], 'kWh', 'Wh')[0] == 0.001
    assert energy_type.to_unit([1], 'kWh', 'Btu')[0] == pytest.approx(1 / 3412.14, rel=1e-5)
    assert energy_type.to_unit([1], 'kWh', 'MMBtu')[0] == pytest.approx(1 / 0.00341214, rel=1e-1)
    assert energy_type.to_unit([1], 'kWh', 'J')[0] == 1 / 3600000
    assert energy_type.to_unit([1], 'kWh', 'kJ')[0] == 1 / 3600
    assert energy_type.to_unit([1], 'kWh', 'MJ')[0] == 1 / 3.6
    assert energy_type.to_unit([1], 'kWh', 'GJ')[0] == 1 / 0.0036
    assert energy_type.to_unit([1], 'kWh', 'therm')[0] == pytest.approx(1 / 0.0341214, rel=1e-1)
    assert energy_type.to_unit([1], 'kWh', 'cal')[0] == pytest.approx(1 / 860421, rel=1e-7)
    assert energy_type.to_unit([1], 'kWh', 'kcal')[0] == pytest.approx(1 / 860.421, rel=1e-4)


def test_energy_intensity():
    """Test Energy type."""
    energyi_type = energyintensity.EnergyIntensity()
    for unit in energyi_type.units:
        assert energyi_type.to_unit([1], unit, unit)[0] == pytest.approx(1, rel=1e-5)
        ip_vals, ip_u = energyi_type.to_ip([1], unit)
        assert len(ip_vals) == 1
        si_vals, si_u = energyi_type.to_si([1], unit)
        assert len(si_vals) == 1
        for other_unit in energyi_type.units:
            assert len(energyi_type.to_unit([1], other_unit, unit)) == 1
    assert energyi_type.to_unit([1], 'kBtu/ft2', 'kWh/m2')[0] == pytest.approx(0.316998, rel=1e-3)
    assert energyi_type.to_unit([1], 'Wh/m2', 'kWh/m2')[0] == 1000
    assert energyi_type.to_unit([1], 'Btu/ft2', 'kWh/m2')[0] == pytest.approx(316.998, rel=1e-1)
    assert energyi_type.to_unit([1], 'kWh/m2', 'kBtu/ft2')[0] == pytest.approx(1 / 0.316998, rel=1e-2)
    assert energyi_type.to_unit([1], 'kWh/m2', 'Wh/m2')[0] == 0.001
    assert energyi_type.to_unit([1], 'kWh/m2', 'Btu/ft2')[0] == pytest.approx(1 / 316.998, rel=1e-5)


def test_power():
    """Test Power type."""
    power_type = power.Power()
    for unit in power_type.units:
        assert power_type.to_unit([1], unit, unit)[0] == pytest.approx(1, rel=1e-5)
        ip_vals, ip_u = power_type.to_ip([1], unit)
        assert len(ip_vals) == 1
        si_vals, si_u = power_type.to_si([1], unit)
        assert len(si_vals) == 1
        for other_unit in power_type.units:
            assert len(power_type.to_unit([1], other_unit, unit)) == 1
    assert power_type.to_unit([1], 'Btu/h', 'W')[0] == pytest.approx(3.41214, rel=1e-3)
    assert power_type.to_unit([1], 'kW', 'W')[0] == 0.001
    assert power_type.to_unit([1], 'kBtu/h', 'W')[0] == pytest.approx(0.00341214, rel=1e-5)
    assert power_type.to_unit([1], 'TR', 'W')[0] == pytest.approx(1 / 3516.85, rel=1e-5)
    assert power_type.to_unit([1], 'hp', 'W')[0] == pytest.approx(1 / 745.7, rel=1e-5)
    assert power_type.to_unit([1], 'W', 'Btu/h')[0] == pytest.approx(1 / 3.41214, rel=1e-2)
    assert power_type.to_unit([1], 'W', 'kW')[0] == 1000
    assert power_type.to_unit([1], 'W', 'kBtu/h')[0] == pytest.approx(1 / 0.00341214, rel=1e-1)
    assert power_type.to_unit([1], 'W', 'TR')[0] == pytest.approx(3516.85, rel=1e-1)
    assert power_type.to_unit([1], 'W', 'hp')[0] == pytest.approx(745.7, rel=1e-1)


def test_energy_flux():
    """Test EnergyFlux type."""
    energyf_type = energyflux.EnergyFlux()
    for unit in energyf_type.units:
        assert energyf_type.to_unit([1], unit, unit)[0] == pytest.approx(1, rel=1e-5)
        ip_vals, ip_u = energyf_type.to_ip([1], unit)
        assert len(ip_vals) == 1
        si_vals, si_u = energyf_type.to_si([1], unit)
        assert len(si_vals) == 1
        for other_unit in energyf_type.units:
            assert len(energyf_type.to_unit([1], other_unit, unit)) == 1
    assert energyf_type.to_unit([1], 'Btu/h-ft2', 'W/m2')[0] == pytest.approx(1 / 3.15459075, rel=1e-2)
    assert energyf_type.to_unit([1], 'kW/m2', 'W/m2')[0] == 0.001
    assert energyf_type.to_unit([1], 'kBtu/h-ft2', 'W/m2')[0] == pytest.approx(1 / 3154.59075, rel=1e-5)
    assert energyf_type.to_unit([1], 'W/ft2', 'W/m2')[0] == pytest.approx(1 / 10.7639, rel=1e-4)
    assert energyf_type.to_unit([1], 'met', 'W/m2')[0] == pytest.approx(1 / 58.2, rel=1e-4)
    assert energyf_type.to_unit([1], 'W/m2', 'Btu/h-ft2')[0] == pytest.approx(3.15459075, rel=1e-2)
    assert energyf_type.to_unit([1], 'W/m2', 'kW/m2')[0] == 1000
    assert energyf_type.to_unit([1], 'W/m2', 'kBtu/h-ft2')[0] == pytest.approx(3154.59075, rel=1e-1)
    assert energyf_type.to_unit([1], 'W/m2', 'W/ft2')[0] == pytest.approx(10.7639, rel=1e-1)
    assert energyf_type.to_unit([1], 'W/m2', 'met')[0] == pytest.approx(58.2, rel=1e-1)


def test_voltage():
    """Test Voltage type."""
    voltage_type = voltage.Voltage()
    for unit in voltage_type.units:
        assert voltage_type.to_unit([1], unit, unit)[0] == pytest.approx(1, rel=1e-5)
        ip_vals, ip_u = voltage_type.to_ip([1], unit)
        assert len(ip_vals) == 1
        si_vals, si_u = voltage_type.to_si([1], unit)
        assert len(si_vals) == 1
        for other_unit in voltage_type.units:
            assert len(voltage_type.to_unit([1], other_unit, unit)) == 1
    assert voltage_type.to_unit([1], 'kV', 'V')[0] == 0.001
    assert voltage_type.to_unit([1], 'V', 'kV')[0] == 1000


def test_current():
    """Test Current type."""
    current_type = current.Current()
    for unit in current_type.units:
        assert current_type.to_unit([1], unit, unit)[0] == pytest.approx(1, rel=1e-5)
        ip_vals, ip_u = current_type.to_ip([1], unit)
        assert len(ip_vals) == 1
        si_vals, si_u = current_type.to_si([1], unit)
        assert len(si_vals) == 1
        for other_unit in current_type.units:
            assert len(current_type.to_unit([1], other_unit, unit)) == 1
    assert current_type.to_unit([1], 'A', 'mA')[0] == 0.001
    assert current_type.to_unit([1], 'mA', 'A')[0] == 1000


def test_illuminance():
    """Test Illuminance type."""
    ill_type = illuminance.Illuminance()
    for unit in ill_type.units:
        assert ill_type.to_unit([1], unit, unit)[0] == pytest.approx(1, rel=1e-5)
        ip_vals, ip_u = ill_type.to_ip([1], unit)
        assert len(ip_vals) == 1
        si_vals, si_u = ill_type.to_si([1], unit)
        assert len(si_vals) == 1
        for other_unit in ill_type.units:
            assert len(ill_type.to_unit([1], other_unit, unit)) == 1
    assert ill_type.to_unit([1], 'fc', 'lux')[0] == pytest.approx(1 / 10.7639, rel=1e-3)
    assert ill_type.to_unit([1], 'lux', 'fc')[0] == pytest.approx(10.7639, rel=1e-1)


def test_luminance():
    """Test Luminance type."""
    lum_type = luminance.Luminance()
    for unit in lum_type.units:
        assert lum_type.to_unit([1], unit, unit)[0] == pytest.approx(1, rel=1e-5)
        ip_vals, ip_u = lum_type.to_ip([1], unit)
        assert len(ip_vals) == 1
        si_vals, si_u = lum_type.to_si([1], unit)
        assert len(si_vals) == 1
        for other_unit in lum_type.units:
            assert len(lum_type.to_unit([1], other_unit, unit)) == 1
    assert lum_type.to_unit([1], 'cd/ft2', 'cd/m2')[0] == pytest.approx(1 / 10.7639, rel=1e-3)
    assert lum_type.to_unit([1], 'cd/m2', 'cd/ft2')[0] == pytest.approx(10.7639, rel=1e-1)


def test_angle():
    """Test Angle type."""
    ang_type = angle.Angle()
    for unit in ang_type.units:
        assert ang_type.to_unit([1], unit, unit)[0] == pytest.approx(1, rel=1e-5)
        ip_vals, ip_u = ang_type.to_ip([1], unit)
        assert len(ip_vals) == 1
        si_vals, si_u = ang_type.to_si([1], unit)
        assert len(si_vals) == 1
        for other_unit in ang_type.units:
            assert len(ang_type.to_unit([1], other_unit, unit)) == 1
    assert ang_type.to_unit([1], 'radians', 'degrees')[0] == pytest.approx(PI / 180, rel=1e-3)
    assert ang_type.to_unit([1], 'degrees', 'radians')[0] == pytest.approx((1 / PI) * 180, rel=1e-1)


def test_mass():
    """Test Mass type."""
    mass_type = mass.Mass()
    for unit in mass_type.units:
        assert mass_type.to_unit([1], unit, unit)[0] == pytest.approx(1, rel=1e-5)
        ip_vals, ip_u = mass_type.to_ip([1], unit)
        assert len(ip_vals) == 1
        si_vals, si_u = mass_type.to_si([1], unit)
        assert len(si_vals) == 1
        for other_unit in mass_type.units:
            assert len(mass_type.to_unit([1], other_unit, unit)) == 1
    assert mass_type.to_unit([1], 'lb', 'kg')[0] == pytest.approx(2.20462, rel=1e-3)
    assert mass_type.to_unit([1], 'g', 'kg')[0] == 1000
    assert mass_type.to_unit([1], 'tonne', 'kg')[0] == 0.001
    assert mass_type.to_unit([1], 'ton', 'kg')[0] == pytest.approx(1 / 907.185, rel=1e-5)
    assert mass_type.to_unit([1], 'oz', 'kg')[0] == pytest.approx(35.274, rel=1e-1)
    assert mass_type.to_unit([1], 'kg', 'lb')[0] == pytest.approx(1 / 2.20462, rel=1e-3)
    assert mass_type.to_unit([1], 'kg', 'g')[0] == 0.001
    assert mass_type.to_unit([1], 'kg', 'tonne')[0] == 1000
    assert mass_type.to_unit([1], 'kg', 'ton')[0] == pytest.approx(907.185, rel=1e-1)
    assert mass_type.to_unit([1], 'kg', 'oz')[0] == pytest.approx(1 / 35.274, rel=1e-3)


def test_speed():
    """Test Speed type."""
    speed_type = speed.Speed()
    for unit in speed_type.units:
        assert speed_type.to_unit([1], unit, unit)[0] == pytest.approx(1, rel=1e-5)
        ip_vals, ip_u = speed_type.to_ip([1], unit)
        assert len(ip_vals) == 1
        si_vals, si_u = speed_type.to_si([1], unit)
        assert len(si_vals) == 1
        for other_unit in speed_type.units:
            assert len(speed_type.to_unit([1], other_unit, unit)) == 1
    assert speed_type.to_unit([1], 'mph', 'm/s')[0] == pytest.approx(2.23694, rel=1e-3)
    assert speed_type.to_unit([1], 'km/h', 'm/s')[0] == 3.6
    assert speed_type.to_unit([1], 'knot', 'm/s')[0] == pytest.approx(1.94384, rel=1e-3)
    assert speed_type.to_unit([1], 'ft/s', 'm/s')[0] == pytest.approx(3.28084, rel=1e-3)
    assert speed_type.to_unit([1], 'm/s', 'mph')[0] == pytest.approx(1 / 2.23694, rel=1e-3)
    assert speed_type.to_unit([1], 'm/s', 'km/h')[0] == 1 / 3.6
    assert speed_type.to_unit([1], 'm/s', 'knot')[0] == pytest.approx(1 / 1.94384, rel=1e-3)
    assert speed_type.to_unit([1], 'm/s', 'ft/s')[0] == pytest.approx(1 / 3.28084, rel=1e-3)


def test_volume_flow_rate():
    """Test VolumeFlowRate type."""
    vfr_type = volumeflowrate.VolumeFlowRate()
    for unit in vfr_type.units:
        assert vfr_type.to_unit([1], unit, unit)[0] == pytest.approx(1, rel=1e-5)
        ip_vals, ip_u = vfr_type.to_ip([1], unit)
        assert len(ip_vals) == 1
        si_vals, si_u = vfr_type.to_si([1], unit)
        assert len(si_vals) == 1
        for other_unit in vfr_type.units:
            assert len(vfr_type.to_unit([1], other_unit, unit)) == 1
    assert vfr_type.to_unit([1], 'ft3/s', 'm3/s')[0] == pytest.approx(35.3147, rel=1e-3)
    assert vfr_type.to_unit([1], 'L/s', 'm3/s')[0] == 1000
    assert vfr_type.to_unit([1], 'cfm', 'm3/s')[0] == pytest.approx(2118.88, rel=1e-1)
    assert vfr_type.to_unit([1], 'gpm', 'm3/s')[0] == pytest.approx(15850.3231, rel=1e-3)
    assert vfr_type.to_unit([1], 'mL/s', 'm3/s')[0] == 1000000
    assert vfr_type.to_unit([1], 'fl oz/s', 'm3/s')[0] == pytest.approx(33814, rel=1e-3)
    assert vfr_type.to_unit([1], 'm3/s', 'ft3/s')[0] == pytest.approx(1 / 35.3147, rel=1e-4)
    assert vfr_type.to_unit([1], 'm3/s', 'L/s')[0] == 0.001
    assert vfr_type.to_unit([1], 'm3/s', 'cfm')[0] == pytest.approx(1 / 2118.88, rel=1e-7)
    assert vfr_type.to_unit([1], 'm3/s', 'gpm')[0] == pytest.approx(1 / 15850.3231, rel=1e-8)
    assert vfr_type.to_unit([1], 'm3/s', 'mL/s')[0] == 0.000001
    assert vfr_type.to_unit([1], 'm3/s', 'fl oz/s')[0] == pytest.approx(1 / 33814, rel=1e-7)


def test_volume_flow_rate_intensity():
    """Test VolumeFlowRateIntensity type."""
    vfr_type = volumeflowrateintensity.VolumeFlowRateIntensity()
    for unit in vfr_type.units:
        assert vfr_type.to_unit([1], unit, unit)[0] == pytest.approx(1, rel=1e-5)
        ip_vals, ip_u = vfr_type.to_ip([1], unit)
        assert len(ip_vals) == 1
        si_vals, si_u = vfr_type.to_si([1], unit)
        assert len(si_vals) == 1
        for other_unit in vfr_type.units:
            assert len(vfr_type.to_unit([1], other_unit, unit)) == 1
    assert vfr_type.to_unit([1], 'ft3/s-ft2', 'm3/s-m2')[0] == pytest.approx(3.28084, rel=1e-3)
    assert vfr_type.to_unit([1], 'L/s-m2', 'm3/s-m2')[0] == 1000
    assert vfr_type.to_unit([1], 'cfm/ft2', 'm3/s-m2')[0] == pytest.approx(196.85, rel=1e-1)
    assert vfr_type.to_unit([1], 'L/h-m2', 'm3/s-m2')[0] == 3600000
    assert vfr_type.to_unit([1], 'gph/ft2', 'm3/s-m2')[0] == pytest.approx(88352.5923, rel=1e-1)


def test_mass_flow_rate():
    """Test MassFlowRate type."""
    mfr_type = massflowrate.MassFlowRate()
    for unit in mfr_type.units:
        assert mfr_type.to_unit([1], unit, unit)[0] == pytest.approx(1, rel=1e-5)
        ip_vals, ip_u = mfr_type.to_ip([1], unit)
        assert len(ip_vals) == 1
        si_vals, si_u = mfr_type.to_si([1], unit)
        assert len(si_vals) == 1
        for other_unit in mfr_type.units:
            assert len(mfr_type.to_unit([1], other_unit, unit)) == 1
    assert mfr_type.to_unit([1], 'lb/s', 'kg/s')[0] == pytest.approx(2.2046, rel=1e-2)
    assert mfr_type.to_unit([1], 'g/s', 'kg/s')[0] == 1000
    assert mfr_type.to_unit([1], 'oz/s', 'kg/s')[0] == pytest.approx(35.274, rel=1e-2)
    assert mfr_type.to_unit([1], 'kg/s', 'lb/s')[0] == pytest.approx(1 / 2.2046, rel=1e-4)
    assert mfr_type.to_unit([1], 'kg/s', 'g/s')[0] == 0.001
    assert mfr_type.to_unit([1], 'kg/s', 'oz/s')[0] == pytest.approx(1 / 35.274, rel=1e-5)


def test_u_value():
    """Test UValue type."""
    uval_type = uvalue.UValue()
    for unit in uval_type.units:
        assert uval_type.to_unit([1], unit, unit)[0] == pytest.approx(1, rel=1e-5)
        ip_vals, ip_u = uval_type.to_ip([1], unit)
        assert len(ip_vals) == 1
        si_vals, si_u = uval_type.to_si([1], unit)
        assert len(si_vals) == 1
        for other_unit in uval_type.units:
            assert len(uval_type.to_unit([1], other_unit, unit)) == 1
    assert uval_type.to_unit([1], 'Btu/h-ft2-F', 'W/m2-K')[0] == pytest.approx(1 / 5.678263337, rel=1e-5)
    assert uval_type.to_unit([1], 'W/m2-K', 'Btu/h-ft2-F')[0] == pytest.approx(5.678263337, rel=1e-4)


def test_r_value():
    """Test RValue type."""
    rval_type = rvalue.RValue()
    for unit in rval_type.units:
        assert rval_type.to_unit([1], unit, unit)[0] == pytest.approx(1, rel=1e-5)
        ip_vals, ip_u = rval_type.to_ip([1], unit)
        assert len(ip_vals) == 1
        si_vals, si_u = rval_type.to_si([1], unit)
        assert len(si_vals) == 1
        for other_unit in rval_type.units:
            assert len(rval_type.to_unit([1], other_unit, unit)) == 1
    assert rval_type.to_unit([1], 'h-ft2-F/Btu', 'm2-K/W')[0] == pytest.approx(5.678263337, rel=1e-4)
    assert rval_type.to_unit([1], 'clo', 'm2-K/W')[0] == pytest.approx(1 / 0.155, rel=1e-2)
    assert rval_type.to_unit([1], 'm2-K/W', 'h-ft2-F/Btu')[0] == pytest.approx(1 / 5.678263337, rel=1e-5)
    assert rval_type.to_unit([1], 'm2-K/W', 'clo')[0] == pytest.approx(0.155, rel=1e-3)


def test_thermal_condition():
    """Test ThermalCondition type."""
    tc_type = thermalcondition.ThermalCondition()
    for unit in tc_type.units:
        assert tc_type.to_unit([1], unit, unit)[0] == pytest.approx(1, rel=1e-5)
        ip_vals, ip_u = tc_type.to_ip([1], unit)
        assert len(ip_vals) == 1
        si_vals, si_u = tc_type.to_si([1], unit)
        assert len(si_vals) == 1
        for other_unit in tc_type.units:
            assert len(tc_type.to_unit([1], other_unit, unit)) == 1
    assert tc_type.to_unit([1], 'PMV', 'condition')[0] == 1
    assert tc_type.to_unit([1], 'condition', 'PMV')[0] == 1


def test_time():
    """Test Time type."""
    time_type = time.Time()
    for unit in time_type.units:
        assert time_type.to_unit([1], unit, unit)[0] == pytest.approx(1, rel=1e-5)
        ip_vals, ip_u = time_type.to_ip([1], unit)
        assert len(ip_vals) == 1
        si_vals, si_u = time_type.to_si([1], unit)
        assert len(si_vals) == 1
        for other_unit in time_type.units:
            assert len(time_type.to_unit([1], other_unit, unit)) == 1
    assert time_type.to_unit([1], 'min', 'hr')[0] == 60
    assert time_type.to_unit([1], 'sec', 'hr')[0] == 3600
    assert time_type.to_unit([1], 'day', 'hr')[0] == 1 / 24.
    assert time_type.to_unit([60], 'hr', 'min')[0] == 1.
    assert time_type.to_unit([3600], 'hr', 'sec')[0] == 1.
    assert time_type.to_unit([1], 'hr', 'day')[0] == 24.


def test_specific_energy():
    """Test ThermalCondition type."""
    tc_type = specificenergy.SpecificEnergy()
    for unit in tc_type.units:
        assert tc_type.to_unit([1], unit, unit)[0] == pytest.approx(1, rel=1e-5)
        ip_vals, ip_u = tc_type.to_ip([1], unit)
        assert len(ip_vals) == 1
        si_vals, si_u = tc_type.to_si([1], unit)
        assert len(si_vals) == 1
        for other_unit in tc_type.units:
            assert len(tc_type.to_unit([1], other_unit, unit)) == 1
    assert tc_type.to_unit([1], 'kBtu/lb', 'kWh/kg')[0] == pytest.approx(1.54772, rel=1e-4)
    assert tc_type.to_unit([1], 'Btu/lb', 'kWh/kg')[0] == pytest.approx(1547.72, rel=1e-2)
    assert tc_type.to_unit([1], 'Wh/kg', 'kWh/kg')[0] == pytest.approx(1000, rel=1e-1)
    assert tc_type.to_unit([1], 'J/kg', 'kWh/kg')[0] == pytest.approx(3600000, rel=1e-1)
    assert tc_type.to_unit([1], 'kJ/kg', 'kWh/kg')[0] == pytest.approx(3600, rel=1e-1)
    assert tc_type.to_unit([1], 'kWh/kg', 'kBtu/lb')[0] == pytest.approx(0.646111699, rel=1e-5)
    assert tc_type.to_unit([1], 'kWh/kg', 'Btu/lb')[0] == pytest.approx(0.00064611169979, rel=1e-7)
    assert tc_type.to_unit([1], 'kWh/kg', 'Wh/kg')[0] == pytest.approx(0.001, rel=1e-3)
    assert tc_type.to_unit([1], 'kWh/kg', 'J/kg')[0] == pytest.approx(2.7777777777777776e-07, rel=1e-9)
    assert tc_type.to_unit([1], 'kWh/kg', 'kJ/kg')[0] == pytest.approx(0.0002777777777777778, rel=1e-7)
