# coding=utf-8
"""A list of useful functions for psychrometrics"""

import math


def find_saturated_vapor_pressure_torr(temperature):
    """
    Calculates Saturated Vapor Pressure (Torr) at Temperature T (C)
    Used frequently throughtout the pmv comfort functions.
    """
    return math.exp(18.6686 - 4030.183 / (temperature + 235.0))


def find_saturated_vapor_pressure_high_accuracy(t_kelvin):
    """
    Calculates Saturated Vapor Pressure (Pa) at Temperature t_kelvin (K)
    to a high accuracy.  The function accounts for the different behaviour of above
    and below the freezing point of water.
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


def find_humid_ratio(air_temp, rel_humid, bar_press=101325):
    """
    Calculates Humidity Ratio (kg water/kg air), Partial Pressure (Pa), and
    saturation_pressure (Pa) at a given
    at Temperature air_temp (C), Relative Humidity rel_humid (%),
    and Barometric Pressure bar_press (Pa).
    """
    # Find saturation pressure
    t_kelvin = air_temp + 273
    saturation_pressure = find_saturated_vapor_pressure_high_accuracy(t_kelvin)
    # Calculate partial pressure
    decrh = rel_humid * 0.01
    partial_pressure = decrh * saturation_pressure
    # Calculate humidity ratio
    press_differ = bar_press - partial_pressure
    constant = partial_pressure * 0.621991
    humidity_ratio = constant / press_differ

    return humidity_ratio, partial_pressure, saturation_pressure


def find_enthalpy(air_temp, humid_ratio):
    """
    Calculates Enthalpy (kJ/kg) at Humidity Ratio humid_ratio (kg water/kg air)
    and at Temperature air_temp (C).
    """
    en_variable1 = 1.01 + (1.89 * humid_ratio)
    en_variable2 = en_variable1 * air_temp
    en_variable3 = 2500 * humid_ratio
    en_variable4 = en_variable2 + en_variable3
    if en_variable4 >= 0:
        enthalpy = en_variable4
    else:
        enthalpy = 0

    return enthalpy


def find_wet_bulb(db_temp, rh, psta=101325):
    """
    Calculates Wet Bulb Temperature (C) at Temperature db_temp (C),
    Relative Humidity rh (%), and Barometric Pressure psta (Pa).
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


def find_dew_point(db_temp, rh):
    """
    Calculates Dew Point Temperature (C) at Temperature db_temp (C) and
    Relative Humidity rh (%).
    """
    es = 6.112 * math.e**((17.67 * db_temp) / (db_temp + 243.5))
    e = (es * rh) / 100
    td = (243.5 * math.log(e / 6.112)) / (17.67 - math.log(e / 6.112))

    return td


def find_rel_humid_from_humid_ratio(abs_humid, air_temp, bar_press=101325):
    """
    Calculates Relative Humidity (%) at Humidity Ratio abs_humid (kg water/kg air),
    Temperature air_temp (C), and Barometric Pressure bar_press (Pa).
    """
    # Calculate the partial pressure of water in the atmostphere.
    pw = (abs_humid * 1000 * bar_press) / (621.9907 + (abs_humid * 1000))
    # Convert Temperature to Kelvin
    t_kelvin = air_temp + 273
    # Calculate saturation pressure.
    pws = find_saturated_vapor_pressure_high_accuracy(t_kelvin)
    # Calculate the relative humidity.
    rel_humid = (pw / pws) * 100

    return rel_humid


def find_rel_humid_from_dry_bulb_dew_pt(air_temp, dew_pt):
    """
    Calculates Relative Humidity (%).

    Relative humidity is calculated at Temperature air_temp (C), and Dew Point dew_pt
    (C).
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
    pws = find_saturated_vapor_pressure_high_accuracy(t_kelvin)
    # Calculate the relative humidity.
    rel_humid = (pw / pws) * 100

    return rel_humid


def find_air_temp_from_enthalpy(enthalpy, abs_humid):
    """
    Calculates Air Temperature (C).

    The calculation at Enthalpy enthalpy (kJ/kg) and Humidity Ratio abs_humid
    (kg water/kg air).
    """
    air_temp = (enthalpy - 2.5 * (abs_humid * 1000)) / \
        (1.01 + (0.00189 * abs_humid * 1000))

    return air_temp


def find_air_temp_from_wet_bulb(wet_bulb, rel_humid, avg_bar_press=101325):
    """
    Calculates Air Temperature (C) at Wet Bulb Temperature wet_bulb (C),
    Relative Humidity rel_humid (%) and Barometric Pressure avg_bar_press (Pa).
    """
    humidity_ratio, partial_pressure, saturation_pressure = find_humid_ratio(
        wet_bulb, rel_humid, avg_bar_press)
    abs_humid, partial_pressure, saturation_pressure = find_humid_ratio(
        wet_bulb, 100, avg_bar_press)
    air_temp = wet_bulb + (((abs_humid - humidity_ratio) * 2260000) / (1005))

    return air_temp, humidity_ratio
