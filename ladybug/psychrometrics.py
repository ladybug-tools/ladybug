# coding=utf-8
"""Utility functions for converting between humidity metrics."""
from __future__ import division

import math


def saturated_vapor_pressure(t_kelvin):
    """Saturated vapor pressure (Pa) at a given dry bulb temperture (K).

    This function accounts for the different behaviour above vs. below
    the freezing point of water.

    Args:
        t_kelvin: Dry bulb temperature (K).

    Returns:
        Saturated vapor pressure (Pa).

    Note:
        [1] W. Wagner and A. Pru:" The IAPWS Formulation 1995 for the Thermodynamic
        Properties of Ordinary Water Substance for General and Scientific Use ",
        Journal of Physical and Chemical Reference Data,
        June 2002 ,Volume 31, Issue 2, pp. 387535

        [2] Vaisala. (2013) Humidity Conversion Formulas:
        Calculation Formulas for Humidity.
        www.vaisala.com/Vaisala%20Documents/Application%20notes/Humidity_Conversion_Formulas_B210973EN-F.pdf

        [3] ASHRAE Handbook - Fundamentals (2017) ch. 1 eqn. 5 and 6
    """

    if t_kelvin >= 273.15:
        # Calculate saturation vapor pressure above freezing
        sig = 1 - (t_kelvin / 647.096)
        sig_polynomial = (-7.85951783 * sig) + (1.84408259 * sig ** 1.5) + \
            (-11.7866487 * sig ** 3) + (22.6807411 * sig ** 3.5) + \
            (-15.9618719 * sig ** 4) + (1.80122502 * sig ** 7.5)
        crit_temp = 647.096 / t_kelvin
        exponent = crit_temp * sig_polynomial
        p_ws = math.exp(exponent) * 22064000
    else:
        # Calculate saturation vapor pressure below freezing
        theta = t_kelvin / 273.15
        exponent = -13.928169 * (1 - theta ** -1.5) + \
            34.707823 * (1 - theta ** -1.25)
        p_ws = math.exp(exponent) * 611.657
    return p_ws


def humid_ratio_from_db_rh(db_temp, rel_humid, b_press=101325):
    """Humidity ratio (kg water/kg air) from air temperature (C) and relative humidity (%).

    Args:
        db_temp: Dry bulb temperature (C).
        rel_humid: Relative humidity (%).
        b_press: Air pressure (Pa). Default is pressure at sea level (101325 Pa).

    Returns:
        Humidity ratio (kg water/kg air).

    Note:
        [1] Vaisala. (2013) Humidity Conversion Formulas:
        Calculation Formulas for Humidity.
        www.vaisala.com/Vaisala%20Documents/Application%20notes/Humidity_Conversion_Formulas_B210973EN-F.pdf
    """
    p_ws = saturated_vapor_pressure(db_temp + 273.15)  # saturation pressure
    p_w = p_ws * (rel_humid / 100)  # partial pressure
    return (p_w * 0.621991) / (b_press - p_w)  # humidity ratio


def enthalpy_from_db_hr(db_temp, humid_ratio, reference_temp=0):
    """Enthalpy (kJ/kg) at a given humidity ratio (water/air) and dry bulb temperature (C).

    Args:
        db_temp: Dry bulb temperature (C).
        rel_humid: Humidity ratio (kg water/kg air).
        reference_temp: Reference dry air temperature (C). Default is 0C,
            which is standard practice for SI enthalpy values. However, for
            IP enthalpy, this is typically at 0F (-17.78C). Alternatively, for
            aboslute thermodynamic enthalpy, one can input 0K (-273.15).

    Returns:
        Enthalpy (kJ/kg).

    Note:
        [1] Meyer et al., (2019). PsychroLib: a library of psychrometric
        functions to calculate thermodynamic properties of air. Journal of
        Open Source Software, 4(33), 1137, https://doi.org/10.21105/joss.01137
        https://github.com/psychrometrics/psychrolib/blob/master/src/python/psychrolib.py

        [2] ASHRAE Handbook - Fundamentals (2017) ch. 1 eqn 30
    """
    correct_temp = db_temp - reference_temp
    enthalpy = 1.006 * correct_temp + humid_ratio * (2501. + 1.86 * correct_temp)
    return enthalpy if enthalpy >= 0 else 0


def wet_bulb_from_db_rh(db_temp, rh, b_press=101325):
    """Wet bulb temperature (C) from air temperature (C) and relative humidity (%).

    Args:
        db_temp: Dry bulb temperature (C).
        rel_humid: Relative humidity (%).
        b_press: Air pressure (Pa). Default is pressure at sea level (101325 Pa).

    Returns:
        Wet bulb temperature (C).

    Note:
        [1] J. Sullivan and L. D. Sanders. "Method for obtaining wet-bulb temperatures by
        modifying the psychrometric formula." Center for Experiment Design and Data
        Analysis. NOAA - National Oceanic and Atmospheric Administration.
        https://www.weather.gov/epz/wxcalc_rh
    """
    es = 6.112 * math.e**((17.67 * db_temp) / (db_temp + 243.5))
    e = (es * rh) / 100
    t_w = 0
    increse = 10.0
    previoussign = 1
    e_d = 1
    while math.fabs(e_d) > 0.005:
        e_wg = 6.112 * (math.e**((17.67 * t_w) / (t_w + 243.5)))
        eg = e_wg - (b_press/100) * (db_temp - t_w) * 0.00066 * (1 + (0.00155 * t_w))
        e_d = e - eg
        if e_d == 0:
            break
        else:
            if e_d < 0:
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
        t_w = t_w + increse * previoussign
    return t_w


def dew_point_from_db_rh(db_temp, rh):
    """Dew point temperature (C) from air temperature (C) and relative humidity (%).

    Note that the formula here is fast but is only accurate up to 90C. For accurate
    values at extreme temperatures, the dew_point_from_db_rh_high_accuracy
    function should be used.

    Args:
        db_temp: Dry bulb temperature (C).
        rel_humid: Relative humidity (%).

    Returns:
        Dew point temperature (C).

    Note:
        [1] J. Sullivan and L. D. Sanders. "Method for obtaining wet-bulb temperatures by
        modifying the psychrometric formula." Center for Experiment Design and Data
        Analysis. NOAA - National Oceanic and Atmospheric Administration.
        https://www.weather.gov/epz/wxcalc_rh
    """
    es = 6.112 * math.e**((17.67 * db_temp) / (db_temp + 243.5))
    e = (es * rh) / 100
    try:
        return (243.5 * math.log(e / 6.112)) / (17.67 - math.log(e / 6.112))
    except ValueError:  # relative humidity of 0, return absolute zero
        return -273.15


def rel_humid_from_db_hr(db_temp, humid_ratio, b_press=101325):
    """Relative Humidity (%) from humidity ratio (water/air) and air temperature (C).

    Args:
        db_temp: Dry bulb temperature (C).
        humid_ratio: Humidity ratio (kg water/kg air).
        b_press: Air pressure (Pa). Default is pressure at sea level (101325 Pa).

    Returns:
        Relative humidity (%).
    """
    pw = (humid_ratio * 1000 * b_press) / (621.9907 + (humid_ratio * 1000))
    pws = saturated_vapor_pressure(db_temp + 273.15)
    return (pw / pws) * 100


def rel_humid_from_db_enth(db_temp, enthalpy, b_press=101325, reference_temp=0):
    """Relative Humidity (%) from air temperature (C) and enthalpy (kJ/kg).

    Args:
        db_temp: Dry bulb temperature (C).
        enthalpy: Enthalpy (kJ/kg).
        b_press: Air pressure (Pa). Default is pressure at sea level (101325 Pa).
        reference_temp: Reference dry air temperature (C). Default is 0C,
            which is standard practice for SI enthalpy values. However, for
            IP enthalpy, this is typically at 0F (-17.78C). Alternatively, for
            aboslute thermodynamic enthalpy, one can input 0K (-273.15).

    Returns:
        Relative humidity (%).
    """
    correct_temp = db_temp - reference_temp
    hr = (enthalpy - (1.006 * correct_temp)) / ((1.86 * correct_temp) + 2501)
    return rel_humid_from_db_hr(db_temp, hr, b_press)


def rel_humid_from_db_dpt(db_temp, dew_pt):
    """Relative humidity (%) from dry bulb temperature (C), and dew point temperature (C).

    Args:
        db_temp: Dry bulb temperature (C).
        dew_pt: Dew point temperature (C).

    Returns:
        Relative humidity (%).
    """
    pws_ta = saturated_vapor_pressure(db_temp + 273.15)
    pws_td = saturated_vapor_pressure(dew_pt + 273.15)
    return 100 * (pws_td / pws_ta)


def rel_humid_from_db_wb(db_temp, wet_bulb, b_press=101325):
    """Relative humidity (%) from dry bulb temperature (C), and wet bulb temperature (C).

    Args:
        db_temp: Dry bulb temperature (C).
        wet_bulb: Wet bulb temperature (C).
        b_press: Air pressure (Pa). Default is pressure at sea level (101325 Pa).

    Returns:
        Relative humidity (%).
    """
    # Calculate saturation pressures
    p_ws = saturated_vapor_pressure(db_temp + 273.15)
    p_ws_wb = saturated_vapor_pressure(wet_bulb + 273.15)
    # calculate partial vapor pressure
    p_w = p_ws_wb - (b_press * 0.000662 * (db_temp - wet_bulb))
    return (p_w / p_ws) * 100


def dew_point_from_db_hr(db_temp, humid_ratio, b_press=101325):
    """Dew Point Temperature (C) from air temperature (C) and humidity ratio (water/air).

    Args:
        db_temp: Dry bulb temperature (C).
        humid_ratio: Humidity ratio (kg water/kg air).
        b_press: Air pressure (Pa). Default is pressure at sea level (101325 Pa).

    Returns:
        Dew point temperature (C).
    """
    rh = rel_humid_from_db_hr(db_temp, humid_ratio, b_press)
    return dew_point_from_db_rh(db_temp, rh)


def dew_point_from_db_enth(db_temp, enthlpy, b_press=101325, reference_temp=0):
    """Dew point temperature (C) from air temperature (C) and enthalpy (kJ/kg).

    Args:
        db_temp: Dry bulb temperature (C).
        enthalpy: Enthalpy (kJ/kg).
        b_press: Air pressure (Pa). Default is pressure at sea level (101325 Pa).
        reference_temp: Reference dry air temperature (C). Default is 0C,
            which is standard practice for SI enthalpy values. However, for
            IP enthalpy, this is typically at 0F (-17.78C). Alternatively, for
            aboslute thermodynamic enthalpy, one can input 0K (-273.15).

    Returns:
        Dew point temperature (C).
    """
    rh = rel_humid_from_db_enth(db_temp, enthlpy, b_press, reference_temp)
    return dew_point_from_db_rh(db_temp, rh)


def dew_point_from_db_wb(db_temp, wet_bulb, b_press=101325):
    """Dew point temperature (C) from dry bulb (C) and wet bulb temperature (C).

    Args:
        db_temp: Dry bulb temperature (C).
        wet_bulb: Wet bulb temperature (C).
        b_press: Air pressure (Pa). Default is pressure at sea level (101325 Pa).

    Returns:
        Dew point temperature (C).
    """
    rh = rel_humid_from_db_wb(db_temp, wet_bulb, b_press)
    return dew_point_from_db_rh(db_temp, rh)


def db_temp_from_enth_hr(enthalpy, humid_ratio, reference_temp=0):
    """Dry bulb temperature (C) from enthalpy (kJ/kg) and humidity ratio (water/air).

    Args:
        enthalpy: Enthalpy (kJ/kg).
        humid_ratio: Humidity ratio (kg water/kg air).
        reference_temp: Reference dry air temperature (C). Default is 0C,
            which is standard practice for SI enthalpy values. However, for
            IP enthalpy, this is typically at 0F (-17.78C). Alternatively, for
            aboslute thermodynamic enthalpy, one can input 0K (-273.15).

    Returns:
        Dry bulb temperature (C).
    """
    db_temp = (enthalpy - 2.5 * (humid_ratio * 1000)) / \
        (1.01 + (0.00189 * humid_ratio * 1000))
    return db_temp + reference_temp


def db_temp_from_wb_rh(wet_bulb, rel_humid, b_press=101325):
    """Dry bulb temperature (C) from wet bulb temperature (C) and relative humidity (%).

    Formula is only valid for rel_humid == 0 or rel_humid == 100.

    Args:
        wet_bulb: Wet bulb temperature (C).
        rel_humid: Relative humidity (%).
        b_press: Air pressure (Pa). Default is pressure at sea level (101325 Pa).

    Returns:
        db_temp: Dry bulb temperature (C).
        humidity_ratio: Humidity ratio (kg water/kg air).
    """
    assert rel_humid == 0 or rel_humid == 100, 'formula is only valid for' \
        ' rel_humid == 0 or rel_humid == 100'
    humidity_ratio = humid_ratio_from_db_rh(wet_bulb, rel_humid, b_press)
    hr_saturation = humid_ratio_from_db_rh(wet_bulb, 100, b_press)
    db_temp = wet_bulb + (((hr_saturation - humidity_ratio) * 2260000) / (1005))
    return db_temp, humidity_ratio


def dew_point_from_db_rh_high_accuracy(db_temp, rel_humid):
    """Dew point temperature (C) from air temperature (C) and relative humidity (%).

    The dew point temperature is solved by inverting the equation giving water vapor
    pressure at saturation from temperature, which is slow but ensures accuracy
    at dry bulb temperatures above 90 C.
    The Newton-Raphson (NR) method is used on the logarithm of water vapour
    pressure as a function of temperature, which is a very smooth function
    Convergence is usually achieved in 3 to 5 iterations.

    Args:
        db_temp: Dry bulb temperature (C).
        rel_humid: Relative humidity (%).

    Returns:
        Dew point temperature (C).

    Note:
        [1] Meyer et al., (2019). PsychroLib: a library of psychrometric
        functions to calculate thermodynamic properties of air. Journal of
        Open Source Software, 4(33), 1137, https://doi.org/10.21105/joss.01137
        https://github.com/psychrometrics/psychrolib/blob/master/src/python/psychrolib.py

        [2] ASHRAE Handbook - Fundamentals (2017) ch. 1 eqn. 5 and 6
    """
    p_ws = saturated_vapor_pressure(db_temp + 273.15)  # saturation pressure
    p_w = p_ws * (rel_humid / 100)  # partial pressure

    # We use NR to approximate the solution.
    td = db_temp  # First guess for dew point temperature (solved for iteratively)
    try:
        ln_vp = math.log(p_w)  # partial pressure of water vapor in moist air
    except ValueError:  # relative humidity of 0, return absolute zero
        return -273.15

    index = 1
    while True:
        td_iter = td   # td used in NR calculation
        ln_vp_iter = math.log(saturated_vapor_pressure(td_iter + 273.15))
        d_ln_vp = _d_ln_p_ws(td_iter)  # Derivative of function, calculated analytically

        # New estimate, bounded by the search domain defined by the max validity
        td = td_iter - (ln_vp_iter - ln_vp) / d_ln_vp
        td = max(td, -100)
        td = min(td, 200)

        if ((math.fabs(td - td_iter) <= 0.1)):  # 0.1 is degree C tolerance
            break  # solution has been found
        if (index > 100):  # 100 is the max iterations (usually ony 3-5 are needed)
            break  # max number of iterations has been exceeded
        index = index + 1

    return min(td, db_temp)


def _d_ln_p_ws(db_temp):
    """Helper function returning the derivative of the natural log of the
    saturation vapor pressure as a function of dry-bulb temperature.

    Args:
        db_temp : Dry bulb temperature (C).
    Returns:
        Derivative of natural log of vapor pressure of saturated air in Pa.

    Note:
        [1] ASHRAE Handbook - Fundamentals (2017) ch. 1  eqn 5 & 6
    """
    T = db_temp + 273.15  # temperature in kelvin
    if db_temp <= 0.:
        d_ln_p_ws = 5.6745359E+03 / math.pow(T, 2) - 9.677843E-03 + 2 * 6.2215701E-07 * T \
            + 3 * 2.0747825E-09 * math.pow(T, 2) - 4 * 9.484024E-13 * math.pow(T, 3) \
            + 4.1635019 / T
    else:
        d_ln_p_ws = 5.8002206E+03 / math.pow(T, 2) - 4.8640239E-02 + 2 * 4.1764768E-05 * T \
              - 3 * 1.4452093E-08 * math.pow(T, 2) + 6.5459673 / T
    return d_ln_p_ws
