# coding=utf-8
"""Functions for computing climate classifications/zones from weather data."""
from __future__ import division

from .datacollection import HourlyContinuousCollection


def ashrae_climate_zone(dry_bulb_temperature, annual_precipitation=None):
    """Estimate the ASHRAE climate zone from a single year of dry bulb temperature.

    Note:
        [1] American Society of Heating Refrigerating and Air-Conditioning Engineers.
        2010. ASHRAE 90.1-2010, Table B-4 International Climate Zone Definitions.

    Args:
        dry_bulb_temperature: A HourlyContinuousCollection of air temperature data,
            typically coming from an EPW.
        annual_precipitation: A number for the total annual liquid precipitation
            depth in millimeters. This is used to determine whether the resulting
            climate has the "dry" classification. If None, the climate will always
            be assumed to be humid (type "A"), which tends to be more common than
            the dry classification (type "B").

    Returns:
        Text for the ASHRAE climate zone classification (eg. "4A").
    """
    # check the input dry_bulb_temperature
    dbt = dry_bulb_temperature
    assert isinstance(dbt, HourlyContinuousCollection), \
        'Expected HourlyContinuousCollection for ashrae_climate_zone ' \
        'dry_bulb_temperature. Got {}.'.format(type(dbt))
    aper = dbt.header.analysis_period
    assert aper.is_annual, 'ashrae_climate_zone dry_bulb_temperature must be annual.'
    assert aper.timestep == 1, \
        'ashrae_climate_zone dry_bulb_temperature must have a timestep of 1.'
    if dbt.header.unit != 'C':
        dbt = dbt.to_unit('C')
    
    # compute the number of heating and cooling degree days
    cooling_deg_days, heating_deg_days = 0, 0
    for t in dbt.values:
        cdd = (t - 10) / 24 if t > 10 else 0
        cooling_deg_days += cdd
        hdd = (18 - t) / 24 if t < 18 else 0
        heating_deg_days += hdd

    # get the climate zone number from analysis of the degree days
    potential_c, no_letter = False, False
    if cooling_deg_days > 5000:
        cz_number = '1'
    elif cooling_deg_days > 3500:
        cz_number = '2'
    elif cooling_deg_days > 2500:
        cz_number = '3'
    elif cooling_deg_days <= 2500 and heating_deg_days <= 2000:
        cz_number, potential_c = '3', True
    elif cooling_deg_days <= 2500 and heating_deg_days <= 3000:
        cz_number = '4'
    elif heating_deg_days <= 3000:
        cz_number, potential_c = '4', True
    elif heating_deg_days <= 4000:
        cz_number, potential_c = '5', True
    elif heating_deg_days <= 5000:
        cz_number = '6'
    elif heating_deg_days <= 7000:
        cz_number, no_letter = '7', True
    else:
        cz_number, no_letter = '8', True

    # determine the letter of the climate zone and return the result
    if no_letter:
        return cz_number
    if potential_c:
        month_temps = dry_bulb_temperature.average_monthly()
        if -3 < month_temps.min < 18 and month_temps.max < 22:
            if len([mon for mon in month_temps if mon > 10]) >= 4:
                return '{}C'.format(cz_number)
    if annual_precipitation is not None:
        precipitation_limit = 20 * (dry_bulb_temperature.average + 7)
        if annual_precipitation < precipitation_limit:
            return '{}B'.format(cz_number)
    return '{}A'.format(cz_number)
