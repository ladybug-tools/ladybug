# coding=utf-8
"""Utility functions for calculating Adaptive Thermal Comfort."""
from __future__ import division

import math
import sys
if (sys.version_info > (3, 0)):
    xrange = range


def adaptive_comfort_ashrae55(t_prevail, ta, tr, vel, conditioning=0):
    """Get adaptive comfort criteria according to ASHRAE-55.

    Note:
        [1] ASHRAE Standard 55 (2017). Thermal Environmental Conditions
        for Human Occupancy. Atlanta Georgoa: American Society of Heating,
        Refrigerating and Air Conditioning Engineers.

    Args:
        t_prevail: The prevailing outdoor temperature [C].  For the ASHRAE-55 adaptive
            comfort model, this is typically the average monthly outdoor temperature.
        ta: Air temperature [C]
        tr: Mean radiant temperature [C]
        vel: Relative air velocity [m/s]
        conditioning: A number between 0 and 1 that represents how "conditioned" vs.
            "free-running" the building is.
                0 = free-running (completely passive with no installed air conditioning)
                1 = conditioned (no operable windows and fully air conditioned)
            Note that this parameter is not an official part of the ASHRAE-55 standard.
            For more information on how adaptive comfort methods can be applied
            to conditioned buildings, see the neutral_temperature_conditioned function.

    Returns:
        result: A dictionary containing results with the following keys:
            to : Operative Temperature [C].
            t_comf : Adaptive comfort neutral temperature (desired by occupants) [C].
            ce : Cooling effect as a result of elevated air speed [C].
            deg_comf: The difference between the operative temperature (to)
                and the adaptive comfort neutral temperature (t_comf) [C].
                Negative values inidcate cool conditions and positive values
                indicate varm conditions.
    """
    to = (ta + tr) / 2  # operative temperature

    # fix upper and lower outdoor temperatures if outside the range of the model
    if t_prevail < 10.0:
        t_prevail = 10.0
    elif t_prevail > 33.5:
        t_prevail = 33.5

    # get the neutral temperature
    if conditioning == 0:
        t_comf = neutral_temperature_ashrae55(t_prevail)
    else:
        t_comf = neutral_temperature_conditioned(t_prevail, conditioning, 'ASHRAE-55')

    # get the cooling effect as a result of elevated air speed
    ce = cooling_effect_ashrae55(vel, to)

    result = {}
    result['to'] = to
    result['t_comf'] = t_comf
    result['ce'] = ce
    result['deg_comf'] = to - t_comf

    return result


def adaptive_comfort_en15251(t_prevail, ta, tr, vel, conditioning=0):
    """Get adaptive comfort criteria according to EN-15251.

    Note:
        [1] CEN (2007) Standard EN15251. Indoor Environmental Input Parameters for
        Design and Assessment of Energy Performance of Buildings: Addressing indoor
        air quality, thermal environmnet, lighting and acoustics, Brussels: Comite
        Europeen de Normalisation.

    Args:
        t_prevail: The prevailing outdoor temperature [C].  For the EN-15251 adaptive
            comfort model, this is typically the exponentially weighted running mean
            of the outdoor temperature over the past week.  Use the weighted_running_mean
            functions to compute this value.
        ta: Air temperature [C]
        tr: Mean radiant temperature [C]
        vel: Relative air velocity [m/s]
        conditioning: A number between 0 and 1 that represents how "conditioned" vs.
            "free-running" the building is.
                0 = free-running (completely passive with no running air conditioning)
                1 = conditioned (no operable windows and fully air conditioned)
            Note that this parameter is not an official part of the EN-15251 standard.
            For more information on how adaptive comfort methods can be applied
            to conditioned buildings, see the neutral_temperature_conditioned function.

    Returns:
        result: A dictionary containing results with the following keys:
            to : Operative Temperature [C].
            t_comf : Adaptive comfort neutral temperature (desired by occupants) [C].
            ce : Cooling effect as a result of elevated air speed [C].
            deg_comf: The difference between the operative temperature (to)
                and the adaptive comfort neutral temperature (t_comf) [C].
                Negative values inidcate cool conditions and positive values
                indicate varm conditions.
    """
    to = (ta + tr) / 2  # operative temperature

    # fix upper and lower outdoor temperatures if outside the range of the model
    if t_prevail < 10.0:
        t_prevail = 10.0
    elif t_prevail > 30:
        t_prevail = 30

    # get the neutral temperature
    if conditioning == 0:
        t_comf = neutral_temperature_en15251(t_prevail)
    else:
        t_comf = neutral_temperature_conditioned(t_prevail, conditioning, 'EN-15251')

    # get the cooling effect as a result of elevated air speed
    ce = cooling_effect_en15251(vel, to)

    result = {}
    result['to'] = to
    result['t_comf'] = t_comf
    result['ce'] = ce
    result['deg_comf'] = to - t_comf

    return result


def neutral_temperature_ashrae55(t_prevail):
    """Get the neutral temperature (desired by occupants) according to ASHRAE-55.

    Note:
        [1] de Dear, R.J. and Brager, G.S. (2002) Thermal comfort in naturally
        ventilated buildings: Revisions to ASHRAE Standard 55.
        Energy and Buildings 34(6), 549-61.

        [2] de Dear, R.J. (1998) A global database of thermal comfort experiments.
        ASHRAE Technical data bulletin 14(1), 15-26.

    Args:
        t_prevail: The prevailing outdoor temperature [C].  For the ASHRAE-55 adaptive
            comfort model, this is typically the average monthly outdoor temperature.

    Return:
        The desired neutral temperature for the input previaling outdoor temperature.
    """
    return 0.31 * t_prevail + 17.8


def neutral_temperature_en15251(t_prevail):
    """Get the neutral temperature (desired by occupants) according to EN-15251.

    Note:
        [1] CIBSE (2006) Environmental Criteria for Design, Chapter 1: Environmental
        Design: CIBSE Guide A. London: Chartered Institution of Building
        Services Engineers.

        [2] Nicol, F. and McCartney, K. (2001) Final Report (Public) Smart Controls
        and Thermal Comfort (SCATs). Report to the European Comission of the Smart
        Controls and Thermal Comfort project. Oxford: Oxford Brokes University.

    Args:
        t_prevail: The prevailing outdoor temperature [C].  For the EN-15251 adaptive
            comfort model, this is typically the exponentially weighted running mean
            of the outdoor temperature over the past week.  Use the weighted_running_mean
            functions to compute this value.

    Return:
        The desired neutral temperature for the input previaling outdoor temperature.
    """
    return 0.33 * t_prevail + 18.8


def neutral_temperature_conditioned(t_prevail, conditioning, model='EN-15251'):
    """Get the neutral temperature for a conditioned or partly conditioned building.

    Note that the use of adative comfort methods in conditioned buildings is not an
    official part of any standard. Both the American ASHRAE-55 standard and the
    European EN-15251 standard state that the adaptive model should only be used
    when the following criteria are met:
        (a) There is no mechanical cooling or heating system in operation
            (in the case of ASHRAE-55, no mechanical cooling system is installed
            and no heating system is in operation)
        (b) Metabolic rates of occupants range from 1.0 to 1.3 met
        (c) Occupants are allowed to freely adapt their clothing insulation
            (in the case of ASHRAE-55, occupants must specifically be allowed
            to adapt clothing within a range at least as wide as 0.5 - 1.0 clo)

    However, the SCATs project[1], from which EN-15251 is derived, involved the survey
    of conditioned buildings and a neutral temperature function was obtained for
    heated and cooled modes of operation.  While the coefficient of determination (aka.
    R squared) of this function was not as strong as that for free-running buildings,
    it appears to be stronger than PMV calculated from the observed conditions in the
    SCATs data set[2].  Accordingly, it has been published in CIBSE guide[3] and has
    been included here along with methods to calculate netural temperature functions
    in between free-running and heated/cooled conditions.

    Note:
        [1] Nicol, F. and McCartney, K. (2001) Final Report (Public) Smart Controls
        and Thermal Comfort (SCATs). Report to the European Comission of the Smart
        Controls and Thermal Comfort project. Oxford: Oxford Brokes University.

        [2] Humphreys, M., Nicol, F. and Roaf, S. (2016) Adaptive Thermal Comfort:
        Foundations and Analysis. Routledge. Chapter 14: PMV and the results of
        field studies.

        [3] CIBSE (2006) Environmental Criteria for Design, Chapter 1: Environmental
        Design: CIBSE Guide A. London: Chartered Institution of Building
        Services Engineers.

    Args:
        t_prevail: The prevailing outdoor temperature [C].
        conditioning: A number between 0 and 1 that represents how "conditioned" vs.
            "free-running" the building is.
                0 = free-running (completely passive with no air conditioning)
                1 = conditioned (no operable windows and fully air conditioned)
        model: The comfort standard, which will be used to represent the "free-running"
            function.  Chose from: 'EN-15251', 'ASHRAE-55'.

    Return:
        The desired neutral temperature for the input previaling outdoor temperature.

    """
    if conditioning == 1:
        t_comf = 0.09 * t_prevail + 22.6
    elif model == 'ASHRAE-55':
        inv_conditioning = 1 - conditioning
        t_comf = ((0.09 * conditioning) + (0.31 * inv_conditioning)) * t_prevail + \
            ((22.6 * conditioning) + (17.8 * inv_conditioning))
    elif model == 'EN-15251':
        inv_conditioning = 1 - conditioning
        t_comf = ((0.09 * conditioning) + (0.33 * inv_conditioning)) * t_prevail + \
            ((22.6 * conditioning) + (18.8 * inv_conditioning))
    else:
        raise ValueError('Adpative comfort model type {} not recongized. '
                         'Choose: EN-15251 or ASHRAE-55'.format(model))
    return t_comf


def cooling_effect_ashrae55(vel, to):
    """Get ASHRAE-55 cooling effect as a result of elevated air speed.

    Args:
        vel: Relative air velocity [m/s]
        to : Operative Temperature [C]

    Returns:
        ce : Cooling effect as a result of elevated air speed [C]
    """
    ce = 0
    if vel >= 0.6 and to >= 25:
        if vel < 0.9:
            ce = 1.2
        elif vel < 1.2:
            ce = 1.8
        elif vel >= 1.2:
            ce = 2.2
    return ce


def cooling_effect_en15251(vel, to):
    """Get EN-15251 cooling effect as a result of elevated air speed.

    Args:
        vel: Relative air velocity [m/s]
        to : Operative Temperature [C]

    Returns:
        ce : Cooling effect as a result of elevated air speed [C]
    """
    ce = 0
    if vel >= 0.2 and to >= 25:
        ce = 1.7856 * math.log(vel) + 2.9835
    return ce


def ashrae55_neutral_offset_from_ppd(ppd=90):
    """Get acceptable offset from neutral temperature given the ASHRAE-55 PPD limit.

    Args:
        ppd: The acceptable limit of Percentage of People Dissatisfied (PPD).
            Usually, this is 90% but it can be 80% in some cases.

    Returns:
        offset : Acceptable temperature offset from neutral temperature [C]
    """
    assert 0 <= ppd <= 100, 'ppd must be between 0 and 100. Got {}'.format(ppd)
    return -0.1 * ppd + 11.5


def en15251_neutral_offset_from_comfort_class(comf_class):
    """Get acceptable offset from neutral temperature given the EN-15251 comfort class.

    Args:
        comf_class: An integer representing the EN-15251 comfort class.
            Choose from: 1, 2, 3 (the higher the class, the greater the offset)

    Returns:
        offset : Acceptable temperature offset from neutral temperature [C]
    """
    if comf_class == 1:
        offset = 2
    elif comf_class == 2:
        offset = 3
    elif comf_class == 3:
        offset = 4
    else:
        raise ValueError('Comfort class {} is not an acceptable value. '
                         'Choose from: 1, 2, 3'.format(comf_class))
    return offset


def weighted_running_mean_hourly(outdoor_temperatures, alpha=0.8):
    """Get weighted running mean temperatures given hourly outdoor temperatures.

    Note:
        [1] Nicol, F. and McCartney, K. (2001) Final Report (Public) Smart Controls
        and Thermal Comfort (SCATs). Report to the European Comission of the Smart
        Controls and Thermal Comfort project. Oxford: Oxford Brokes University.

    Args:
        outdoor_temperatures: A list of hourly outdoor temperatures in Celcius for which
            running mean values will be computed.  The list should contain at least
            168 values (1 week of data) in order to be meaningful.  Lists shorter
            than 24 are not acceptable.
        alpha: A constant between 0 and 1 that governs how quickly the running mean
            responds to the outdoor temperature. Default is 0.8, which was found to
            be most suitable by Nicol and McCartney[1].

    Returns:
        prevailing_temp: A list of prevailing outdoor temperatures with a length that
            matches the input outdoor_temperatures.
    """
    # ensure that there are at least a day's worth of values
    assert len(outdoor_temperatures) >= 168, 'outdoor_temperatures must be for '\
        'at least a week (168 values). Got {} values.'.format(len(outdoor_temperatures))

    # compute the initial prevailing outdoor temperature by looking over the past week
    divisor = 1 + alpha + alpha ** 2 + alpha ** 3 + alpha ** 4 + alpha ** 5
    dividend = (sum(outdoor_temperatures[-24:]) / 24) + \
        (alpha * (sum(outdoor_temperatures[-48:-24]) / 24)) + \
        (alpha ** 2 * (sum(outdoor_temperatures[-72:-48]) / 24)) + \
        (alpha ** 3 * (sum(outdoor_temperatures[-96:-72]) / 24)) + \
        (alpha ** 4 * (sum(outdoor_temperatures[-120:-96]) / 24)) + \
        (alpha ** 5 * (sum(outdoor_temperatures[-144:-120]) / 24))
    starting_temp = dividend / divisor
    daily_run_means = [starting_temp]
    daily_means = [sum(outdoor_temperatures[:24]) / 24]
    prevailing_temp = [starting_temp] * 24

    # run through each day of data and compute the running mean using the previous day's
    start_hour = 24
    for i in xrange(int(math.floor(len(outdoor_temperatures) / 24) - 1)):
        daily_mean = sum(outdoor_temperatures[start_hour: start_hour + 24]) / 24
        daily_run_mean = ((1 - alpha) * daily_means[-1]) + alpha * daily_run_means[-1]
        daily_run_means.append(daily_run_mean)
        daily_means.append(daily_mean)
        prevailing_temp.extend([daily_run_mean] * 24)
        start_hour += 24

    # if there are extra hours, compute the new running mean of the last day.
    if len(prevailing_temp) != len(outdoor_temperatures):
        daily_run_mean = ((1 - alpha) * daily_means[-1]) + alpha * daily_run_means[-1]
        num_extra = len(outdoor_temperatures) - len(prevailing_temp)
        prevailing_temp.extend([daily_run_mean] * num_extra)

    return prevailing_temp


def weighted_running_mean_daily(outdoor_temperatures, alpha=0.8):
    """Get weighted running mean temperatures given average daily outdoor temperatures.

    Note:
        [1] Nicol, F. and McCartney, K. (2001) Final Report (Public) Smart Controls
        and Thermal Comfort (SCATs). Report to the European Comission of the Smart
        Controls and Thermal Comfort project. Oxford: Oxford Brokes University.

    Args:
        outdoor_temperatures: A list of daily outdoor temperatures in Celcius for which
            running mean values will be computed.  The list should contain at least
            7 values in order to be meaningful.  Lists shorter than 1 are not acceptable.
        alpha: A constant between 0 and 1 that governs how quickly the running mean
            responds to the outdoor temperature. Default is 0.8, which was found to
            be most suitable by Nicol and McCartney[1].

    Returns:
        daily_run_means: A list of prevailing outdoor temperatures with a length that
            matches the input outdoor_temperatures.
    """
    # ensure that there are at least one value
    assert len(outdoor_temperatures) >= 7, 'outdoor_temperatures must have '\
        'at least 7 values to be meaningful.'

    # compute the initial prevailing outdoor temperature by looking over the past week
    divisor = 1 + alpha + alpha ** 2 + alpha ** 3 + alpha ** 4 + alpha ** 5
    dividend = outdoor_temperatures[-1] + alpha * outdoor_temperatures[-2] + \
        alpha ** 2 * outdoor_temperatures[-3] + alpha ** 3 * outdoor_temperatures[-4] + \
        alpha ** 4 * outdoor_temperatures[-5] + alpha ** 5 * outdoor_temperatures[-6]
    starting_temp = dividend / divisor
    daily_run_means = [starting_temp]
    daily_means = [outdoor_temperatures[0]]

    # run through each day of data and compute the running mean using the previous day's
    for i in xrange(len(outdoor_temperatures) - 1):
        daily_run_mean = ((1 - alpha) * daily_means[-1]) + alpha * daily_run_means[-1]
        daily_run_means.append(daily_run_mean)
        daily_means.append(outdoor_temperatures[i])

    return daily_run_means
