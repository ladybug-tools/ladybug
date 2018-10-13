# coding=utf-8
"""Functions for converting between various humidity metrics"""
import math


def saturated_vapor_pressure_torr(db_temp):
    """Saturated Vapor Pressure (Torr) at temperature (C)

    Used frequently throughtout the pmv comfort functions.
    """
    return math.exp(18.6686 - 4030.183 / (db_temp + 235.0))


def saturated_vapor_pressure(t_kelvin):
    """Saturated Vapor Pressure (Pa) at t_kelvin (K).

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
        p_ws = power * 22064000
    else:
        # Calculate saturation vapor pressure below freezing
        theta = t_kelvin / 273.16
        exponent2 = ((1 - (theta**(-1.5))) * (-13.928169)) + \
            ((1 - (theta**(-1.25))) * 34.707823)
        power = math.exp(exponent2)
        p_ws = power * 611.657
    return p_ws


def humid_ratio_from_db_rh(db_temp, rel_humid, b_press=101325):
    """Humidity Ratio (kg water/kg air) at a db_temp (C),
    rel_humid (%) and Pressure b_press (Pa).
    """
    # Find saturation pressure
    p_ws = saturated_vapor_pressure(db_temp + 273)
    # Calculate partial pressure
    decrh = rel_humid * 0.01
    p_w = decrh * p_ws
    # Calculate humidity ratio
    press_differ = b_press - p_w
    constant = p_w * 0.621991
    humidity_ratio = constant / press_differ
    return humidity_ratio


def enthalpy_from_db_hr(db_temp, humid_ratio):
    """Enthalpy (kJ/kg) at humid_ratio (kg water/kg air) and at db_temp (C).
    """
    enthalpy = ((1.01 + (1.89 * humid_ratio)) * db_temp) + (2500 * humid_ratio)
    return enthalpy if enthalpy >= 0 else 0


def wet_bulb_from_db_rh(db_temp, rh, b_press=101325):
    """Wet Bulb Temperature (C) at db_temp (C),
    Relative Humidity rh (%), and Pressure b_press (Pa).
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
                    increse = increse/10
                else:
                    increse = increse
        t_w = t_w + increse * previoussign
    return t_w


def dew_point_from_db_rh(db_temp, rh):
    """Dew Point Temperature (C) at Dry Bulb Temperature db_temp (C) and
    Relative Humidity rh (%).
    """
    es = 6.112 * math.e**((17.67 * db_temp) / (db_temp + 243.5))
    e = (es * rh) / 100
    td = (243.5 * math.log(e / 6.112)) / (17.67 - math.log(e / 6.112))
    return td


def rel_humid_from_db_hr(db_temp, humid_ratio, b_press=101325):
    """Relative Humidity (%) at humid_ratio (kg water/kg air), db_temp (C),
    and Pressure b_press (Pa).
    """
    pw = (humid_ratio * 1000 * b_press) / (621.9907 + (humid_ratio * 1000))
    pws = saturated_vapor_pressure(db_temp + 273)
    rel_humid = (pw / pws) * 100
    return rel_humid


def rel_humid_from_db_enth(db_temp, enthalpy, b_press=101325):
    """Relative Humidity (%) at db_temp (C), enthalpy (kJ/kg)
    and Pressure b_press (Pa).
    """
    assert enthalpy >= 0, 'enthalpy must be' \
        'greater than 0. Got {}'.format(str(enthalpy))
    hr = (enthalpy - (1.006 * db_temp)) / ((1.84 * db_temp) + 2501)
    rel_humid = rel_humid_from_db_hr(db_temp, hr, b_press)
    return rel_humid


def rel_humid_from_db_dpt(db_temp, dew_pt):
    """Relative Humidity (%) at db_temp (C), and dew_pt (C).
    """
    pws_ta = saturated_vapor_pressure(db_temp + 273)
    pws_td = saturated_vapor_pressure(dew_pt + 273)
    rh = 100 * (pws_td / pws_ta)
    return rh


def rel_humid_from_db_wb(db_temp, wet_bulb, b_press=101325):
    """Relative Humidity (%) at db_temp(C), wet_bulb (C), and Pressure b_press (Pa).
    """
    # Calculate saturation pressure.
    p_ws = saturated_vapor_pressure(db_temp + 273)
    p_ws_wb = saturated_vapor_pressure(wet_bulb + 273)
    # calculate partial vapor pressure
    p_w = p_ws_wb - (b_press * 0.000662 * (db_temp - wet_bulb))
    # Calculate the relative humidity.
    rel_humid = (p_w / p_ws) * 100
    return rel_humid


def dew_point_from_db_hr(db_temp, hr, b_press=101325):
    """Dew Point Temperature (C) at Temperature db_temp (C),
    Humidity Ratio hr (kg water/kg air) and Pressure b_press (Pa).
    """
    rh = rel_humid_from_db_hr(db_temp, hr, b_press)
    td = dew_point_from_db_rh(db_temp, rh)
    return td


def dew_point_from_db_enth(db_temp, enthlpy, b_press=101325):
    """Dew Point Temperature (C) at Temperature db_temp (C), enthalpy (kJ/kg)
    and Pressure b_press (Pa).
    """
    rh = rel_humid_from_db_enth(db_temp, enthlpy, b_press)
    td = dew_point_from_db_rh(db_temp, rh)
    return td


def dew_point_from_db_wb(db_temp, wet_bulb, b_press=101325):
    """Dew Point Temperature (C) at Temperature db_temp (C), wet_bulb (C)
    and Pressure b_press (Pa).
    """
    rh = rel_humid_from_db_wb(db_temp, wet_bulb, b_press)
    td = dew_point_from_db_rh(db_temp, rh)
    return td


def db_temp_from_enth_hr(enthalpy, humid_ratio):
    """Dry Bulb Temperature (C) at Enthalpy enthalpy (kJ/kg) and
    humid_ratio (kg water/kg air).
    """
    db_temp = (enthalpy - 2.5 * (humid_ratio * 1000)) / \
        (1.01 + (0.00189 * humid_ratio * 1000))
    return db_temp


def db_temp_from_wb_rh(wet_bulb, rel_humid, b_press=101325):
    """Dry Bulb Temperature (C) and humidity_ratio at at wet_bulb (C),
    rel_humid (%) and Pressure b_press (Pa).

    Formula is only valid for rel_humid == 0 or rel_humid == 100.
    """
    assert rel_humid == 0 or rel_humid == 100, 'formula is only valid for' \
        ' rel_humid == 0 or rel_humid == 100'
    humidity_ratio = humid_ratio_from_db_rh(wet_bulb, rel_humid, b_press)
    hr_saturation = humid_ratio_from_db_rh(wet_bulb, 100, b_press)
    db_temp = wet_bulb + (((hr_saturation - humidity_ratio) * 2260000) / (1005))
    return db_temp, humidity_ratio
