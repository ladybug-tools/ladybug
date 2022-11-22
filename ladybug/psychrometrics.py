# coding=utf-8
"""Utility functions for converting between humidity metrics."""
from __future__ import division

import math


def saturated_vapor_pressure(t_kelvin):
    """Saturated vapor pressure (Pa) at a given dry bulb temperature (K).

    This function accounts for the different behavior above vs. below
    the freezing point of water.

    Args:
        t_kelvin: Dry bulb temperature (K).

    Returns:
        Saturated vapor pressure (Pa).

    Note:
        [1] ASHRAE Handbook - Fundamentals (2017) ch. 1 eqn. 5 and 6

        [2] Meyer et al., (2019). PsychroLib: a library of psychrometric
        functions to calculate thermodynamic properties of air. Journal of
        Open Source Software, 4(33), 1137, https://doi.org/10.21105/joss.01137
        https://github.com/psychrometrics/psychrolib/blob/master/src/python/psychrolib.py
    """
    if (t_kelvin <= 273.15):  # saturation vapor pressure below freezing
        ln_p_ws = -5.6745359E+03 / t_kelvin + 6.3925247 - 9.677843E-03 * t_kelvin + \
            6.2215701E-07 * t_kelvin**2 + 2.0747825E-09 * math.pow(t_kelvin, 3) - \
            9.484024E-13 * math.pow(t_kelvin, 4) + 4.1635019 * math.log(t_kelvin)
    else:  # saturation vapor pressure above freezing
        ln_p_ws = -5.8002206E+03 / t_kelvin + 1.3914993 - 4.8640239E-02 * t_kelvin + \
            4.1764768E-05 * t_kelvin**2 - 1.4452093E-08 * math.pow(t_kelvin, 3) + \
            6.5459673 * math.log(t_kelvin)
    return math.exp(ln_p_ws)


def humid_ratio_from_db_rh(db_temp, rel_humid, b_press=101325):
    """Humidity ratio (kg water/kg air) from air temperature (C) and relative humidity (%).

    Args:
        db_temp: Dry bulb temperature (C).
        rel_humid: Relative humidity (%).
        b_press: Air pressure (Pa). Default is pressure at sea level (101325 Pa).

    Returns:
        Humidity ratio (kg water/kg air).

    Note:
        [1] ASHRAE Handbook - Fundamentals (2017) ch. 1 eqn 20

        [2] Meyer et al., (2019). PsychroLib: a library of psychrometric
        functions to calculate thermodynamic properties of air. Journal of
        Open Source Software, 4(33), 1137, https://doi.org/10.21105/joss.01137
        https://github.com/psychrometrics/psychrolib/blob/master/src/python/psychrolib.py
    """
    p_ws = saturated_vapor_pressure(db_temp + 273.15)  # saturation pressure
    p_w = p_ws * (rel_humid / 100)  # partial pressure
    return (p_w * 0.621945) / (b_press - p_w)  # humidity ratio


def enthalpy_from_db_hr(db_temp, humid_ratio, reference_temp=0):
    """Enthalpy (kJ/kg) at a given humidity ratio (water/air) and dry bulb temperature (C).

    Args:
        db_temp: Dry bulb temperature (C).
        humid_ratio: Humidity ratio (kg water/kg air).
        reference_temp: Reference dry air temperature (C). Default is 0C,
            which is standard practice for SI enthalpy values. However, for
            IP enthalpy, this is typically at 0F (-17.78C). Alternatively, for
            absolute thermodynamic enthalpy, one can input 0K (-273.15).

    Returns:
        Enthalpy (kJ/kg).

    Note:
        [1] ASHRAE Handbook - Fundamentals (2017) ch. 1 eqn 30

        [2] Meyer et al., (2019). PsychroLib: a library of psychrometric
        functions to calculate thermodynamic properties of air. Journal of
        Open Source Software, 4(33), 1137, https://doi.org/10.21105/joss.01137
        https://github.com/psychrometrics/psychrolib/blob/master/src/python/psychrolib.py
    """
    correct_temp = db_temp - reference_temp
    enthalpy = 1.006 * correct_temp + humid_ratio * (2501. + 1.86 * correct_temp)
    return enthalpy if enthalpy >= 0 else 0


def dew_point_from_db_rh(db_temp, rel_humid):
    """Dew point temperature (C) from air temperature (C) and relative humidity (%).

    The dew point temperature is solved by inverting the equation giving water vapor
    pressure at saturation from temperature, which is relatively slow but ensures
    high accuracy down to 0.1 C at a wide range of dry bulb temperatures.
    The Newton-Raphson (NR) method is used on the logarithm of water vapour
    pressure as a function of temperature, which is a very smooth function
    Convergence is usually achieved in 3 to 5 iterations.

    Args:
        db_temp: Dry bulb temperature (C).
        rel_humid: Relative humidity (%).

    Returns:
        Dew point temperature (C).

    Note:
        [1] ASHRAE Handbook - Fundamentals (2017) ch. 1 eqn. 5 and 6

        [2] Meyer et al., (2019). PsychroLib: a library of psychrometric
        functions to calculate thermodynamic properties of air. Journal of
        Open Source Software, 4(33), 1137, https://doi.org/10.21105/joss.01137
        https://github.com/psychrometrics/psychrolib/blob/master/src/python/psychrolib.py
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
        td = td_iter - (ln_vp_iter - ln_vp) / d_ln_vp  # New estimate

        if ((math.fabs(td - td_iter) <= 0.1)):  # 0.1 is degree C tolerance
            break  # solution has been found
        if (index > 100):  # 100 is the max iterations (usually only 3-5 are needed)
            break  # max number of iterations has been exceeded
        index = index + 1

    return min(td, db_temp)


def wet_bulb_from_db_rh(db_temp, rel_humid, b_press=101325):
    """Wet bulb temperature (C) from air temperature (C) and relative humidity (%).

    Args:
        db_temp: Dry bulb temperature (C).
        rel_humid: Relative humidity (%).
        b_press: Air pressure (Pa). Default is pressure at sea level (101325 Pa).

    Returns:
        Wet bulb temperature (C).

    Note:
        [1] ASHRAE Handbook - Fundamentals (2017) ch. 1 eqn 33 and 35

        [2] Meyer et al., (2019). PsychroLib: a library of psychrometric
        functions to calculate thermodynamic properties of air. Journal of
        Open Source Software, 4(33), 1137, https://doi.org/10.21105/joss.01137
        https://github.com/psychrometrics/psychrolib/blob/master/src/python/psychrolib.py
    """
    humid_ratio = humid_ratio_from_db_rh(db_temp, rel_humid, b_press)
    # Initial guesses
    wb_temp_sup = db_temp
    wb_temp_inf = dew_point_from_db_rh(db_temp, rel_humid)
    wb_temp = (wb_temp_inf + wb_temp_sup) / 2

    index = 1
    while ((wb_temp_sup - wb_temp_inf) > 0.1):  # 0.1 is degree C tolerance
        # Compute humidity ratio at temperature Tstar
        w_star = humid_ratio_from_db_wb(db_temp, wb_temp, b_press)
        # Get new bounds
        if w_star > humid_ratio:
            wb_temp_sup = wb_temp
        else:
            wb_temp_inf = wb_temp
        # New guess of wet bulb temperature
        wb_temp = (wb_temp_sup + wb_temp_inf) / 2
        if index >= 100:
            break  # 100 is the max iterations (usually only 3-5 are needed)
        index = index + 1
    return wb_temp


def wet_bulb_from_db_hr(db_temp, humid_ratio, b_press=101325):
    """Wet bulb temperature (C) from air temperature (C) and humidity ratio.

    Args:
        db_temp: Dry bulb temperature (C).
        humid_ratio: Humidity ratio (kg water/kg air).
        b_press: Air pressure (Pa). Default is pressure at sea level (101325 Pa).

    Returns:
        Wet bulb temperature (C).
    """
    rh = rel_humid_from_db_hr(db_temp, humid_ratio, b_press)
    return wet_bulb_from_db_rh(db_temp, rh, b_press)


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
            absolute thermodynamic enthalpy, one can input 0K (-273.15).

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


def dew_point_from_db_enth(db_temp, enthalpy, b_press=101325, reference_temp=0):
    """Dew point temperature (C) from air temperature (C) and enthalpy (kJ/kg).

    Args:
        db_temp: Dry bulb temperature (C).
        enthalpy: Enthalpy (kJ/kg).
        b_press: Air pressure (Pa). Default is pressure at sea level (101325 Pa).
        reference_temp: Reference dry air temperature (C). Default is 0C,
            which is standard practice for SI enthalpy values. However, for
            IP enthalpy, this is typically at 0F (-17.78C). Alternatively, for
            absolute thermodynamic enthalpy, one can input 0K (-273.15).

    Returns:
        Dew point temperature (C).
    """
    rh = rel_humid_from_db_enth(db_temp, enthalpy, b_press, reference_temp)
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


def humid_ratio_from_db_wb(db_temp, wb_temp, b_press=101325):
    """Humidity ratio from air temperature (C) and wet bulb temperature (C).

    Args:
        db_temp: Dry bulb temperature (C).
        wb_temp: Wet bulb temperature (C).
        b_press: Air pressure (Pa). Default is pressure at sea level (101325 Pa).

    Returns:
        Humidity ratio (kg water / kg air).

    Note:
        [1] ASHRAE Handbook - Fundamentals (2017) ch. 1 eqn 36, solved for W
    """
    p_ws = saturated_vapor_pressure(wb_temp + 273.15)
    p_ws_star = 0.621945 * p_ws / (b_press - p_ws)
    if wb_temp >= 0:
        humid_ratio = \
            ((2501. - 2.326 * wb_temp) * p_ws_star - 1.006 * (db_temp - wb_temp)) \
            / (2501. + 1.86 * db_temp - 4.186 * wb_temp)
    else:
        humid_ratio = \
            ((2830. - 0.24 * wb_temp) * p_ws_star - 1.006 * (db_temp - wb_temp)) \
            / (2830. + 1.86 * db_temp - 2.1 * wb_temp)
    return humid_ratio


def db_temp_from_enth_hr(enthalpy, humid_ratio, reference_temp=0):
    """Dry bulb temperature (C) from enthalpy (kJ/kg) and humidity ratio (water/air).

    Args:
        enthalpy: Enthalpy (kJ/kg).
        humid_ratio: Humidity ratio (kg water/kg air).
        reference_temp: Reference dry air temperature (C). Default is 0C,
            which is standard practice for SI enthalpy values. However, for
            IP enthalpy, this is typically at 0F (-17.78C). Alternatively, for
            absolute thermodynamic enthalpy, one can input 0K (-273.15).

    Returns:
        Dry bulb temperature (C).

    Note:
        [1] ASHRAE Handbook - Fundamentals (2017) ch. 1 eqn 30
    """
    db_temp = (enthalpy - 2501. * humid_ratio) / (1.006 + 1.86 * humid_ratio)
    return db_temp + reference_temp


def db_temp_from_rh_hr(rel_humid, humid_ratio, b_press=101325):
    """Dry bulb temperature (C) from relative humidity (%) and humidity ratio (water/air).

    Args:
        rel_humid: Relative humidity (%).
        humid_ratio: Humidity ratio (kg water/kg air).
        b_press: Air pressure (Pa). Default is pressure at sea level (101325 Pa).

    Returns:
        Dry bulb temperature (C).

    Note:
        [1] Antoine equation - Antoine, C. (1888), Vapor Pressure: a new relationship
        between pressure and temperature, 107: 681–684, 778–780, 836–837.
        https://en.wikipedia.org/wiki/Antoine_equation
    """
    p_w = (b_press * humid_ratio) / (0.621945 + humid_ratio)  # partial pressure
    p_ws = p_w / (rel_humid / 100)  # saturation pressure
    return (1730.63 / (8.07131 - math.log10(p_ws / 133.322))) - 233.426


def db_temp_and_hr_from_wb_rh(wb_temp, rel_humid, b_press=101325):
    """Dry bulb temperature (C) from wet bulb temperature (C) and relative humidity (%).

    Args:
        wb_temp: Wet bulb temperature (C).
        rel_humid: Relative humidity (%).
        b_press: Air pressure (Pa). Default is pressure at sea level (101325 Pa).

    Returns:
        A tuple with two values.

        -   Dry bulb temperature (C).

        -   Humidity ratio (kg water/kg air).

    Note:
        [1] ASHRAE Handbook - Fundamentals (2017)
    """
    hr = humid_ratio_from_db_rh(wb_temp, rel_humid, b_press)
    hr_sat = humid_ratio_from_db_rh(wb_temp, 100, b_press)
    db_temp = (((hr_sat - hr) * 2260000) / 1005) + wb_temp
    return db_temp, hr


def dew_point_from_db_rh_fast(db_temp, rel_humid):
    """Dew point temperature (C) from air temperature (C) and relative humidity (%).

    Note that the formula here is fast but is only accurate up to 90C. For accurate
    values at extreme temperatures, the dew_point_from_db_rh
    function should be used.

    Args:
        db_temp: Dry bulb temperature (C).
        rel_humid: Relative humidity (%).

    Returns:
        Dew point temperature (C).

    Note:
        [1] J. Sullivan and L. D. Sanders. "Method for obtaining wet-bulb temperatures
        by modifying the psychrometric formula." Center for Experiment Design and Data
        Analysis. NOAA - National Oceanic and Atmospheric Administration.
        https://www.weather.gov/epz/wxcalc_rh
    """
    es = 6.112 * math.e**((17.67 * db_temp) / (db_temp + 243.5))
    e = (es * rel_humid) / 100
    try:
        return (243.5 * math.log(e / 6.112)) / (17.67 - math.log(e / 6.112))
    except ValueError:  # relative humidity of 0, return absolute zero
        return -273.15


def wet_bulb_from_db_rh_fast(db_temp, rel_humid, b_press=101325):
    """Wet bulb temperature (C) from air temperature (C) and relative humidity (%).

    Note that the formula here is fast but is only accurate around temperatures
    of 20C and lower. For accurate values at extreme temperatures, the
    wet_bulb_from_db_rh function should be used.

    Args:
        db_temp: Dry bulb temperature (C).
        rel_humid: Relative humidity (%).
        b_press: Air pressure (Pa). Default is pressure at sea level (101325 Pa).

    Returns:
        Wet bulb temperature (C).

    Note:
        [1] J. Sullivan and L. D. Sanders. "Method for obtaining wet-bulb temperatures
        by modifying the psychrometric formula." Center for Experiment Design and Data
        Analysis. NOAA - National Oceanic and Atmospheric Administration.
        https://www.weather.gov/epz/wxcalc_rh
    """
    es = 6.112 * math.e**((17.67 * db_temp) / (db_temp + 243.5))
    e = (es * rel_humid) / 100
    t_w = 0
    increase = 10.0
    previoussign = 1
    e_d = 1
    while math.fabs(e_d) > 0.005:
        e_wg = 6.112 * (math.e**((17.67 * t_w) / (t_w + 243.5)))
        eg = e_wg - (b_press / 100) * (db_temp - t_w) * 0.00066 * (1 + (0.00155 * t_w))
        e_d = e - eg
        if e_d == 0:
            break
        else:
            if e_d < 0:
                cursign = -1
                if cursign != previoussign:
                    previoussign = cursign
                    increase = increase / 10
                else:
                    increase = increase
            else:
                cursign = 1
                if cursign != previoussign:
                    previoussign = cursign
                    increase = increase / 10
                else:
                    increase = increase
        t_w = t_w + increase * previoussign
    return t_w


def _d_ln_p_ws(db_temp):
    """Helper function for the derivative of the log of saturation vapor pressure.

    Args:
        db_temp : Dry bulb temperature (C).

    Returns:
        Derivative of natural log of vapor pressure of saturated air in Pa.
    """
    T = db_temp + 273.15  # temperature in kelvin
    if db_temp <= 0.:
        d_ln_p_ws = 5.6745359E+03 / math.pow(T, 2) - 9.677843E-03 + 2 * \
            6.2215701E-07 * T + 3 * 2.0747825E-09 * math.pow(T, 2) - 4 * \
            9.484024E-13 * math.pow(T, 3) + 4.1635019 / T
    else:
        d_ln_p_ws = 5.8002206E+03 / math.pow(T, 2) - 4.8640239E-02 + 2 * \
            4.1764768E-05 * T - 3 * 1.4452093E-08 * math.pow(T, 2) + \
            6.5459673 / T
    return d_ln_p_ws
