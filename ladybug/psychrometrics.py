# coding=utf-8
"""A list of useful functions for psychrometrics"""

import math


def saturated_vapor_pressure_torr(temperature):
    """Saturated Vapor Pressure (Torr) at temperature (C)

    Used frequently throughtout the pmv comfort functions.
    """
    return math.exp(18.6686 - 4030.183 / (temperature + 235.0))


def saturated_vapor_pressure_high_accuracy(t_kelvin):
    """Saturated Vapor Pressure (Pa) at t_kelvin (K) to a high accuracy.

    This function accounts for the different behaviour above vs. below
    the freezing point of water.
    """

    if t_kelvin >= 273:
        # Calculate saturation vapor pressure above freezing
        sigma = 1 - (t_kelvin / 647.096)
        express_result = (sigma * (-7.85951783)) + ((sigma**1.5) * 1.84408259) + \
            ((sigma**3) * (-11.7866487)) + \
            ((sigma**3.5) * 22.6807411) + ((sigma**4) *
                                           (-15.9618719)) + ((sigma**7.5) * 1.80122502)
        crit_temp = 647.096 / t_kelvin
        exponent = crit_temp * express_result
        power = math.exp(exponent)
        saturation_pressure = power * 22064000
    else:
        # Calculate saturation vapor pressure below freezing
        theta = t_kelvin / 273.16
        exponent2 = ((1 - (theta**(-1.5))) * (-13.928169)) + \
            ((1 - (theta**(-1.25))) * 34.707823)
        power = math.exp(exponent2)
        saturation_pressure = power * 611.657

    return saturation_pressure


def humid_ratio_from_db_rh(air_temp, rel_humid, psta=101325):
    """humidity_ratio (kg water/kg air), partial_pressure (Pa), and saturation_pressure
    (Pa) at a given air_temp (C), rel_humid (%) and Pressure psta (Pa).
    """
    # Find saturation pressure
    t_kelvin = air_temp + 273
    saturation_pressure = saturated_vapor_pressure_high_accuracy(t_kelvin)
    # Calculate partial pressure
    decrh = rel_humid * 0.01
    partial_pressure = decrh * saturation_pressure
    # Calculate humidity ratio
    press_differ = psta - partial_pressure
    constant = partial_pressure * 0.621991
    humidity_ratio = constant / press_differ

    return humidity_ratio, partial_pressure, saturation_pressure


def enthalpy_from_db_hr(air_temp, humid_ratio):
    """Enthalpy (kJ/kg) at humid_ratio (kg water/kg air) and at air_temp (C).
    """
    enthalpy = ((1.01 + (1.89 * humid_ratio)) * air_temp) + (2500 * humid_ratio)
    if enthalpy >= 0:
        return enthalpy
    else:
        return 0


def wet_bulb_from_db_rh(db_temp, rh, psta=101325):
    """Wet Bulb Temperature (C) at db_temp (C),
    Relative Humidity rh (%), and Pressure psta (Pa).
    """
    es = 6.112 * math.e**((17.67 * db_temp) / (db_temp + 243.5))
    e = (es * rh) / 100
    tw = 0
    increse = 10
    previoussign = 1
    ed = 1

    while math.fabs(tw) > 0.005:
        ewg = 6.112 * math.e**((17.67 * tw) / (tw + 243.5))
        eg = ewg - (psta / 100) * (db_temp - tw) * 0.00066 * (1 + (0.00155 * tw))
        ed = e - eg
        if ed == 0:
            break
        else:
            if ed < 0:
                cursign = -1
                if cursign != previoussign:
                    previoussign = cursign
                    increse = increse / 10
                else:
                    increse = increse
            else:
                cursign = 1
                if cursign != previoussign:
                    previoussign = cursign
                    increse = increse / 10
                else:
                    increse = increse
        tw = tw + increse * previoussign

    return tw


def dew_point_from_db_rh(db_temp, rh):
    """
    Calculates Dew Point Temperature (C) at Temperature db_temp (C) and
    Relative Humidity rh (%).
    """
    es = 6.112 * math.e**((17.67 * db_temp) / (db_temp + 243.5))
    e = (es * rh) / 100
    td = (243.5 * math.log(e / 6.112)) / (17.67 - math.log(e / 6.112))

    return td


def rel_humid_from_hr_db(humid_ratio, air_temp, psta=101325):
    """Relative Humidity (%) at humid_ratio (kg water/kg air), air_temp (C),
    and Pressure psta (Pa).
    """
    # Calculate the partial pressure of water in the atmostphere.
    pw = (humid_ratio * 1000 * psta) / (621.9907 + (humid_ratio * 1000))
    # Convert Temperature to Kelvin
    t_kelvin = air_temp + 273
    # Calculate saturation pressure.
    pws = saturated_vapor_pressure_high_accuracy(t_kelvin)
    # Calculate the relative humidity.
    rel_humid = (pw / pws) * 100

    return rel_humid


def rel_humid_from_db_dpt(air_temp, dew_pt):
    """Relative Humidity (%) at air_temp (C), and dew_pt (C).
    """
    # Calculate the partial pressure of water in the atmosphere.
    a = 6.11657
    m = 7.591386
    tn = 240.7263
    td = dew_pt + 273
    pw = ((math.pow(10, (m / ((tn / td) + 1)))) * a) / 100
    # Convert Temperature to Kelvin
    t_kelvin = air_temp + 273
    # Calculate saturation pressure.
    pws = saturated_vapor_pressure_high_accuracy(t_kelvin)
    # Calculate the relative humidity.
    rel_humid = (pw / pws) * 100

    return rel_humid


def air_temp_from_enth_hr(enthalpy, humid_ratio):
    """Air Temperature (C) at Enthalpy enthalpy (kJ/kg) and humid_ratio (kg water/kg air).
    """
    air_temp = (enthalpy - 2.5 * (humid_ratio * 1000)) / \
        (1.01 + (0.00189 * humid_ratio * 1000))

    return air_temp


def air_temp_from_wb_rh(wet_bulb, rel_humid, avg_psta=101325):
    """Air Temperature (C) at wet_bulb (C), rel_humid (%) and Pressure avg_psta (Pa).
    """
    humidity_ratio, partial_pressure, saturation_pressure = humid_ratio_from_db_rh(
        wet_bulb, rel_humid, avg_psta)
    humid_ratio, partial_pressure, saturation_pressure = humid_ratio_from_db_rh(
        wet_bulb, 100, avg_psta)
    air_temp = wet_bulb + (((humid_ratio - humidity_ratio) * 2260000) / (1005))

    return air_temp, humidity_ratio
