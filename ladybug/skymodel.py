# coding=utf-8
from __future__ import division
"""Functions for computing radiation for different idealized skies"""
import math


"""ORIGINAL AHSRAE CLEAR SKY SOLAR MODEL"""


def ashrae_clear_sky(altitudes, month, sky_clearness=1):
    """Calculate solar flux for an original ASHRAE Clear Sky

    Args:
        altitudes = A list of solar altitudes in degrees
        month: An integer (1-12) indicating the month the altitudes belong to
        sky_clearness: A factor that will be multiplied by the output of
            the model. This is to help account for locations where clear,
            dry skies predominate (e.g., at high elevations) or,
            conversely, where hazy and humid conditions are frequent. See
            Threlkeld and Jordan (1958) for recommended values. Typical
            values range from 0.95 to 1.05 and are usually never more
            than 1.2. Default is set to 1.0.

    Returns:
        dir_norm_rad: A list of direct normal radiation values for each
            of the connected altitudes in W/m2.
        dif_horiz_rad: A list of diffuse horizontall radiation values for each
            of the connected altitudes in W/m2.
    """
    # apparent solar irradiation at air mass m = 0
    MONTHLY_A = [1202, 1187, 1164, 1130, 1106, 1092, 1093, 1107, 1136,
                 1166, 1190, 1204]
    # atmospheric extinction coefficient
    MONTHLY_B = [0.141, 0.142, 0.149, 0.164, 0.177, 0.185, 0.186, 0.182,
                 0.165, 0.152, 0.144, 0.141]

    dir_norm_rad = []
    dif_horiz_rad = []
    for i, alt in enumerate(altitudes):
        if alt > 0:
            try:
                dir_norm = MONTHLY_A[month - 1] / (math.exp(
                    MONTHLY_B[month - 1] / (math.sin(math.radians(alt)))))
                diff_horiz = 0.17 * dir_norm * math.sin(math.radians(alt))
                dir_norm_rad.append(dir_norm * sky_clearness)
                dif_horiz_rad.append(diff_horiz * sky_clearness)
            except OverflowError:
                # very small altitude values
                dir_norm_rad.append(0)
                dif_horiz_rad.append(0)
        else:
            # night time
            dir_norm_rad.append(0)
            dif_horiz_rad.append(0)

    return dir_norm_rad, dif_horiz_rad


"""AHSRAE REVISED CLEAR SKY SOLAR MODEL (TAU MODEL)"""


def ashrae_revised_clear_sky(altitudes, tb, td):
    """Calculate solar flux for an ASHRAE Revised Clear Sky ("Tau Model")

    Args:
        altitudes = A list of solar altitudes in degrees.
        tb: A value indicating the beam optical depth of the sky.
        td: A value indicating the diffuse optical depth of the sky.

    Returns:
        dir_norm_rad: A list of direct normal radiation values for each
            of the connected altitudes in W/m2.
        dif_horiz_rad: A list of diffuse horizontall radiation values for each
            of the connected altitudes in W/m2.
    """
    dir_norm_rad = []
    dif_horiz_rad = []

    ab = 1.219 - (0.043 * tb) - (0.151 * td) - (0.204 * tb * td)
    ad = 0.202 + (0.852 * tb) - (0.007 * td) - (0.357 * tb * td)
    for alt in altitudes:
        # calculate hourly air mass between top of the atmosphere and earth
        if alt > 0:
            air_mass = get_relative_airmass(alt)
            dir_norm_rad.append(1415 * math.exp(-tb * math.pow(air_mass, ab)))
            dif_horiz_rad.append(1415 * math.exp(-td * math.pow(air_mass, ad)))
        else:
            dir_norm_rad.append(0)
            dif_horiz_rad.append(0)

    return dir_norm_rad, dif_horiz_rad


"""ZHANG-HUANG SOLAR MODEL"""


def zhang_huang_solar(alt, cloud_cover, relative_humidity,
                      dry_bulb_present, dry_bulb_t3_hrs, wind_speed,
                      irr_0=1355):
    """Calculate global horizontal solar irradiance using the Zhang-Huang model.

    Args:
        alt = A solar altitude in degrees.
        cloud_cover: A float value between 0 and 10 that represents the sky cloud cover
            in tenths (0 = clear; 10 = completely overcast)
        relative_humidity: A float value between 0 and 100 that represents
            the relative humidity in percent.
        dry_bulb_present: A float value that represents the dry bulb
            temperature at the time of interest (in degrees C).
        dry_bulb_t3_hrs: A float value that represents the dry bulb
            temperature at three hours before the time of interest (in degrees C).
        wind_speed: A float value that represents the wind speed in m/s.
        irr_0 = Optional extraterrestrial solar constant (W/m2).
            Default is to use the average value over the earth's orbit (1355).

    Returns:
        glob_ir: A global horizontall radiation value in W/m2.
    """
    # zhang-huang solar model regression constants
    C0, C1, C2, C3, C4, C5, D_COEFF, K_COEFF = 0.5598, 0.4982, \
        -0.6762, 0.02842, -0.00317, 0.014, -17.853, 0.843

    # start assuming night time
    glob_ir = 0

    if alt > 0:
        # get sin of the altitude
        sin_alt = math.sin(math.radians(alt))

        # shortened and converted versions of the input parameters
        cc, rh, n_temp, n3_temp, w_spd = cloud_cover / 10.0, \
            relative_humidity, dry_bulb_present, dry_bulb_t3_hrs, wind_speed

        # calculate zhang-huang global radiation
        glob_ir = ((irr_0 * sin_alt *
                    (C0 + (C1 * cc) + (C2 * cc**2) +
                     (C3 * (n_temp - n3_temp)) +
                     (C4 * rh) + (C5 * w_spd))) + D_COEFF) / K_COEFF
        if glob_ir < 0:
            glob_ir = 0

    return glob_ir


def zhang_huang_solar_split(altitudes, doys, cloud_cover, relative_humidity,
                            dry_bulb_present, dry_bulb_t3_hrs, wind_speed,
                            atmospheric_pressure):
    """Calculate direct and diffuse solar irradiance using the Zhang-Huang model.

    This function uses the dirint method (aka. Perez split) to split global horizontal
    irradiance into direct and diffuse.  This is the same method used by EnergyPlus.
    Args:
        altitudes = A list of solar altitudes in degrees.
        doys = A list of days of the year that correspond to the altitudes.
        cloud_cover: A list of float values between 0 and 10 that represents cloud cover
            in tenths (0 = clear; 10 = completely overcast)
        relative_humidity: A list of float values between 0 and 100 that represents
            the relative humidity in percent.
        dry_bulb_present: A list of float values that represents the dry bulb
            temperature at the time of interest (in degrees C).
        dry_bulb_t3_hrs: A list of float values that represents the dry bulb
            temperature at three hours before the time of interest (in degrees C).
        wind_speed: A list of float values that represents the wind speed in m/s.
        atmospheric_pressure: A list of float values that represent the
            atmospheric pressure in Pa.

    Returns:
        dir_norm_rad: A list of direct normal radiation values for each
            of the connected altitudes in W/m2.
        dif_horiz_rad: A list of diffuse horizontall radiation values for each
            of the connected altitudes in W/m2.
    """
    # Calculate global horizontal irradiance using the original zhang-huang model
    glob_ir = []
    for i in range(len(altitudes)):
        irr_0 = get_extra_radiation(doys[i])
        ghi = zhang_huang_solar(altitudes[i], cloud_cover[i], relative_humidity[i],
                                dry_bulb_present[i], dry_bulb_t3_hrs[i], wind_speed[i],
                                irr_0)
        glob_ir.append(ghi)

    # Split global radiation into direct + diffuse using dirint method (aka. Perez split)
    dir_norm_rad = []
    dif_horiz_rad = []
    for i in range(len(glob_ir)):
        dni, kt, am = disc(glob_ir[i], altitudes[i], doys[i], atmospheric_pressure[i])
        dhi = glob_ir[i] - (dni * math.sin(math.radians(altitudes[i])))
        dir_norm_rad.append(dni)
        dif_horiz_rad.append(dhi)

    return dir_norm_rad, dif_horiz_rad


"""HORIZONTAL INFRARED INTENSITY + SKY TEMPERATURE MODELS"""


def horizontal_infrared(sky_cover, dry_bulb, dew_point):
    """Calculate horizontal infrared radiation intensity.

    See EnergyPlus Enrineering Reference for more information:
    https://bigladdersoftware.com/epx/docs/8-9/engineering-reference/climate-calculations.html#sky-radiation-modeling
    Args:
        sky_cover: A float value between 0 and 10 that represents the opaque
            sky cover in tenths (0 = clear; 10 = completely overcast)
        dry_bulb: A float value that represents the dry bulb temperature
            in degrees C.
        dew_point: A float value that represents the dew point temperature
            in degrees C.

    Returns:
        horiz_ir: A horizontal infrared radiation intensity value in W/m2.
    """
    # stefan-boltzmann constant
    SIGMA = 5.6697e-8

    # convert to kelvin
    db_k = dry_bulb + 273.15
    dp_k = dew_point + 273.15

    # calculate sky emissivity and horizontal ir
    sky_emiss = (0.787 + (0.764 * math.log(dp_k / 273.15))) * \
        (1 + (0.022 * sky_cover) - (0.0035 * (sky_cover ** 2)) +
         (0.00028 * (sky_cover ** 3)))
    horiz_ir = sky_emiss * SIGMA * (db_k ** 4)
    return horiz_ir


def sky_temperature(horiz_ir, dry_bulb):
    """Calculate sky temperature in Celcius.

    See EnergyPlus Enrineering Reference for more information:
    https://bigladdersoftware.com/epx/docs/8-9/engineering-reference/climate-calculations.html#energyplus-sky-temperature-calculation
    Args:
        horiz_ir: A float value that represents horizontal infrared radiation
            intensity in W/m2.
        dry_bulb: A float value that represents the dry bulb temperature
            in degrees C.

    Returns:
        sky_temp: A sky temperature value in C.
    """
    # stefan-boltzmann constant
    SIGMA = 5.6697e-8

    # convert to kelvin
    db_k = dry_bulb + 273.15

    # calculate sky temperature
    sky_temp = ((horiz_ir / SIGMA) ** 0.25) - db_k
    return sky_temp


"""DIRECT AND DIFFUSE SPLITTING FROM GLOBAL HORIZONTAL"""
"""The following code is a modified version of the PVLib python library.

PVLib
Copyright (c) 2013-2018, Sandia National Laboratories and pvlib python Development Team
All rights reserved.

Developed at Sandia National Laboratories, PVLib implements
many of the models and methods developed at the Lab.
More information can be found on the pvlib-python github:
https://github.com/pvlib/pvlib-python
"""


def dirint(ghi, solar_zenith, times, pressure=101325., use_delta_kt_prime=True,
           temp_dew=None, min_cos_zenith=0.065, max_zenith=87):
    """
    Determine DNI from GHI using the DIRINT modification of the DISC
    model.

    Implements the modified DISC model known as "DIRINT" introduced in
    [1]. DIRINT predicts direct normal irradiance (DNI) from measured
    global horizontal irradiance (GHI). DIRINT improves upon the DISC
    model by using time-series GHI data and dew point temperature
    information. The effectiveness of the DIRINT model improves with
    each piece of information provided.

    The pvlib implementation limits the clearness index to 1.

    Parameters
    ----------
    ghi : array-like
        Global horizontal irradiance in W/m^2.

    solar_zenith : array-like
        True (not refraction-corrected) solar_zenith angles in decimal
        degrees.

    times : DatetimeIndex

    pressure : float or array-like, default 101325.0
        The site pressure in Pascal. Pressure may be measured or an
        average pressure may be calculated from site altitude.

    use_delta_kt_prime : bool, default True
        If True, indicates that the stability index delta_kt_prime is
        included in the model. The stability index adjusts the estimated
        DNI in response to dynamics in the time series of GHI. It is
        recommended that delta_kt_prime is not used if the time between
        GHI points is 1.5 hours or greater. If use_delta_kt_prime=True,
        input data must be Series.

    temp_dew : None, float, or array-like, default None
        Surface dew point temperatures, in degrees C. Values of temp_dew
        may be numeric or NaN. Any single time period point with a
        temp_dew=NaN does not have dew point improvements applied. If
        temp_dew is not provided, then dew point improvements are not
        applied.

    min_cos_zenith : numeric, default 0.065
        Minimum value of cos(zenith) to allow when calculating global
        clearness index `kt`. Equivalent to zenith = 86.273 degrees.

    max_zenith : numeric, default 87
        Maximum value of zenith to allow in DNI calculation. DNI will be
        set to 0 for times with zenith values greater than `max_zenith`.

    Returns
    -------
    dni : array-like
        The modeled direct normal irradiance in W/m^2 provided by the
        DIRINT model.

    Notes
    -----
    DIRINT model requires time series data (ie. one of the inputs must
    be a vector of length > 2).

    References
    ----------
    [1] Perez, R., P. Ineichen, E. Maxwell, R. Seals and A. Zelenka,
    (1992). "Dynamic Global-to-Direct Irradiance Conversion Models".
    ASHRAE Transactions-Research Series, pp. 354-369

    [2] Maxwell, E. L., "A Quasi-Physical Model for Converting Hourly
    Global Horizontal to Direct Normal Insolation", Technical Report No.
    SERI/TR-215-3087, Golden, CO: Solar Energy Research Institute, 1987.
    """

    disc_out = disc(ghi, solar_zenith, times, pressure=pressure,
                    min_cos_zenith=min_cos_zenith, max_zenith=max_zenith)
    airmass = disc_out['airmass']
    kt = disc_out['kt']

    kt_prime = clearness_index_zenith_independent(
        kt, airmass, max_clearness_index=1)
    delta_kt_prime = _delta_kt_prime_dirint(kt_prime, use_delta_kt_prime,
                                            times)
    w = _temp_dew_dirint(temp_dew, times)

    dirint_coeffs = _dirint_coeffs(times, kt_prime, solar_zenith, w,
                                   delta_kt_prime)

    # Perez eqn 5
    dni = disc_out['dni'] * dirint_coeffs

    return dni


def disc(ghi, altitude, doy, pressure=101325,
         min_sin_altitude=0.065, min_altitude=3, max_airmass=12):
    """
    Estimate Direct Normal Irradiance from Global Horizontal Irradiance
    using the DISC model.

    The DISC algorithm converts global horizontal irradiance to direct
    normal irradiance through empirical relationships between the global
    and direct clearness indices.

    This implementation limits the clearness index to 1 by default.

    The original report describing the DISC model [1]_ uses the
    relative airmass rather than the absolute (pressure-corrected)
    airmass. However, the NREL implementation of the DISC model [2]_
    uses absolute airmass. PVLib Matlab also uses the absolute airmass.
    pvlib python defaults to absolute airmass, but the relative airmass
    can be used by supplying `pressure=None`.

    Parameters
    ----------
    ghi : numeric
        Global horizontal irradiance in W/m^2.

    altitude : numeric
        True (not refraction-corrected) solar altitude angles in decimal
        degrees.

    doy : array of integers representing the days of the year.

    pressure : None or numeric, default 101325
        Site pressure in Pascal. If None, relative airmass is used
        instead of absolute (pressure-corrected) airmass.

    min_sin_altitude : numeric, default 0.065
        Minimum value of sin(altitude) to allow when calculating global
        clearness index `kt`. Equivalent to altitude = 3.727 degrees.

    min_altitude : numeric, default 87
        Minimum value of altitude to allow in DNI calculation. DNI will be
        set to 0 for times with altitude values smaller than `min_altitude`.

    max_airmass : numeric, default 12
        Maximum value of the airmass to allow in Kn calculation.
        Default value (12) comes from range over which Kn was fit
        to airmass in the original paper.

    Returns
    -------
    dni: The modeled direct normal irradiance
        in W/m^2 provided by the
        Direct Insolation Simulation Code (DISC) model.
    kt: Ratio of global to extraterrestrial
        irradiance on a horizontal plane.
    am: Airmass

    References
    ----------
    .. [1] Maxwell, E. L., "A Quasi-Physical Model for Converting Hourly
       Global Horizontal to Direct Normal Insolation", Technical
       Report No. SERI/TR-215-3087, Golden, CO: Solar Energy Research
       Institute, 1987.

    .. [2] Maxwell, E. "DISC Model", Excel Worksheet.
       https://www.nrel.gov/grid/solar-resource/disc.html
    """
    if altitude > min_altitude:
        # this is the I0 calculation from the reference
        # SSC uses solar constant = 1367.0 (checked 2018 08 15)
        I0 = get_extra_radiation(doy, 1370.)

        kt = clearness_index(ghi, altitude, I0, min_sin_altitude=min_sin_altitude,
                             max_clearness_index=1)

        am = get_relative_airmass(altitude, model='kasten1966')
        if pressure is not None:
            am = get_absolute_airmass(am, pressure)

        Kn, am = _disc_kn(kt, am, max_airmass=max_airmass)
        dni = Kn * I0

        return dni, kt, am
    else:
        return 0, 0, None


def _disc_kn(clearness_index, airmass, max_airmass=12):
    """
    Calculate Kn for `disc`

    Parameters
    ----------
    clearness_index : numeric
    airmass : numeric
    max_airmass : float
        airmass > max_airmass is set to max_airmass before being used
        in calculating Kn.

    Returns
    -------
    Kn : numeric
    am : numeric
        airmass used in the calculation of Kn. am <= max_airmass.
    """
    # short names for equations
    kt = clearness_index
    am = airmass

    am = min(am, max_airmass)  # GH 450

    # powers of kt will be used repeatedly, so compute only once
    kt2 = kt * kt  # about the same as kt ** 2
    kt3 = kt2 * kt  # 5-10x faster than kt ** 3

    if kt <= 0.6:
        a = 0.512 - 1.56*kt + 2.286*kt2 - 2.222*kt3
        b = 0.37 + 0.962*kt
        c = -0.28 + 0.932*kt - 2.048*kt2
    else:
        a = -5.743 + 21.77*kt - 27.49*kt2 + 11.56*kt3
        b = 41.4 - 118.5*kt + 66.05*kt2 + 31.9*kt3
        c = -47.01 + 184.2*kt - 222.0*kt2 + 73.81*kt3

    delta_kn = a + b * math.exp(c*am)

    Knc = 0.866 - 0.122*am + 0.0121*am**2 - 0.000653*am**3 + 1.4e-05*am**4
    Kn = Knc - delta_kn
    return Kn, am


def get_extra_radiation(doy, solar_constant=1366.1):
    """
    Determine extraterrestrial radiation from day of year (using the spencer method).

    Parameters
    ----------
    doy : array of integers representing the days of the year.

    solar_constant : float, default 1366.1
        The solar constant.

    Returns
    -------
    dni_extra : float, array, or Series
        The extraterrestrial radiation present in watts per square meter
        on a surface which is normal to the sun. Pandas Timestamp and
        DatetimeIndex inputs will yield a Pandas TimeSeries. All other
        inputs will yield a float or an array of floats.

    References
    ----------
    [1] M. Reno, C. Hansen, and J. Stein, "Global Horizontal Irradiance
    Clear Sky Models: Implementation and Analysis", Sandia National
    Laboratories, SAND2012-2389, 2012.

    [2] <http://solardat.uoregon.edu/SolarRadiationBasics.html>, Eqs.
    SR1 and SR2
    """
    # Calculates the day angle for the Earth's orbit around the Sun.
    B = (2. * math.pi / 365.) * (doy - 1)
    # Calculate R over R squared from the angle
    RoverR0sqrd = (1.00011 + 0.034221 * math.cos(B) + 0.00128 * math.sin(B) +
                   0.000719 * math.cos(2 * B) + 7.7e-05 * math.sin(2 * B))

    Ea = solar_constant * RoverR0sqrd

    return Ea


def clearness_index(ghi, altitude, extra_radiation, min_sin_altitude=0.065,
                    max_clearness_index=2.0):
    """
    Calculate the clearness index.

    The clearness index is the ratio of global to extraterrestrial
    irradiance on a horizontal plane.

    Parameters
    ----------
    ghi : numeric
        Global horizontal irradiance in W/m^2.

    altitude : numeric
        True (not refraction-corrected) solar altitude angle in decimal
        degrees.

    extra_radiation : numeric
        Irradiance incident at the top of the atmosphere

    min_sin_altitude : numeric, default 0.065
        Minimum value of sin(altitude) to allow when calculating global
        clearness index `kt`. Equivalent to altitude = 3.727 degrees.

    max_clearness_index : numeric, default 2.0
        Maximum value of the clearness index. The default, 2.0, allows
        for over-irradiance events typically seen in sub-hourly data.
        NREL's SRRL Fortran code used 0.82 for hourly data.

    Returns
    -------
    kt : numeric
        Clearness index

    References
    ----------
    .. [1] Maxwell, E. L., "A Quasi-Physical Model for Converting Hourly
           Global Horizontal to Direct Normal Insolation", Technical
           Report No. SERI/TR-215-3087, Golden, CO: Solar Energy Research
           Institute, 1987.
    """
    sin_altitude = math.sin(math.radians(altitude))
    I0h = extra_radiation * max(sin_altitude, min_sin_altitude)
    kt = ghi / I0h
    kt = max(kt, 0)
    kt = min(kt, max_clearness_index)
    return kt


def get_absolute_airmass(airmass_relative, pressure=101325.):
    '''
    Determine absolute (pressure corrected) airmass from relative
    airmass and pressure
    Gives the airmass for locations not at sea-level (i.e. not at
    standard pressure). The input argument "AMrelative" is the relative
    airmass. The input argument "pressure" is the pressure (in Pascals)
    at the location of interest and must be greater than 0. The
    calculation for absolute airmass is
    .. math::
        absolute airmass = (relative airmass)*pressure/101325
    Parameters
    ----------
    airmass_relative : numeric
        The airmass at sea-level.
    pressure : numeric, default 101325
        The site pressure in Pascal.
    Returns
    -------
    airmass_absolute : numeric
        Absolute (pressure corrected) airmass
    References
    ----------
    [1] C. Gueymard, "Critical analysis and performance assessment of
    clear sky solar irradiance models using theoretical and measured
    data," Solar Energy, vol. 51, pp. 121-138, 1993.
    '''
    if airmass_relative is not None:
        return airmass_relative * pressure / 101325.
    else:
        return None


def get_relative_airmass(altitude, model='kastenyoung1989'):
    '''
    Gives the relative (not pressure-corrected) airmass.
    Gives the airmass at sea-level when given a sun altitude angle (in
    degrees). The ``model`` variable allows selection of different
    airmass models (described below). If ``model`` is not included or is
    not valid, the default model is 'kastenyoung1989'.
    Parameters
    ----------
    altitude : numeric
        Altitude angle of the sun in degrees. Note that some models use
        the apparent (refraction corrected) altitude angle, and some
        models use the true (not refraction-corrected) altitude angle. See
        model descriptions to determine which type of altitude angle is
        required. Apparent altitude angles must be calculated at sea level.
    model : string, default 'kastenyoung1989'
        Available models include the following:
        * 'simple' - secant(apparent altitude angle) -
          Note that this gives -inf at altitude=0
        * 'kasten1966' - See reference [1] -
          requires apparent sun altitude
        * 'youngirvine1967' - See reference [2] -
          requires true sun altitude
        * 'kastenyoung1989' - See reference [3] -
          requires apparent sun altitude
        * 'gueymard1993' - See reference [4] -
          requires apparent sun altitude
        * 'young1994' - See reference [5] -
          requries true sun altitude
        * 'pickering2002' - See reference [6] -
          requires apparent sun altitude
    Returns
    -------
    airmass_relative : numeric
        Relative airmass at sea level. Will return None for any
        altitude angle smaller than 0 degrees.
    References
    ----------
    [1] Fritz Kasten. "A New Table and Approximation Formula for the
    Relative Optical Air Mass". Technical Report 136, Hanover, N.H.:
    U.S. Army Material Command, CRREL.
    [2] A. T. Young and W. M. Irvine, "Multicolor Photoelectric
    Photometry of the Brighter Planets," The Astronomical Journal, vol.
    72, pp. 945-950, 1967.
    [3] Fritz Kasten and Andrew Young. "Revised optical air mass tables
    and approximation formula". Applied Optics 28:4735-4738
    [4] C. Gueymard, "Critical analysis and performance assessment of
    clear sky solar irradiance models using theoretical and measured
    data," Solar Energy, vol. 51, pp. 121-138, 1993.
    [5] A. T. Young, "AIR-MASS AND REFRACTION," Applied Optics, vol. 33,
    pp. 1108-1110, Feb 1994.
    [6] Keith A. Pickering. "The Ancient Star Catalog". DIO 12:1, 20,
    [7] Matthew J. Reno, Clifford W. Hansen and Joshua S. Stein, "Global
    Horizontal Irradiance Clear Sky Models: Implementation and Analysis"
    Sandia Report, (2012).
    '''
    if altitude < 0:
        return None
    else:
        alt_rad = math.radians(altitude)
        model = model.lower()

        if 'kastenyoung1989' == model:
            am = (1.0 / (math.sin(alt_rad) +
                  0.50572*(((6.07995 + altitude) ** - 1.6364))))
        elif 'kasten1966' == model:
            am = 1.0 / (math.sin(alt_rad) + 0.15*((3.885 + altitude) ** - 1.253))
        elif 'simple' == model:
            am = 1.0 / math.sin(altitude)
        elif 'pickering2002' == model:
            am = (1.0 / (math.sin(math.radians(altitude +
                  244.0 / (165 + 47.0 * altitude ** 1.1)))))
        elif 'youngirvine1967' == model:
            sec_zen = 1.0 / math.sin(alt_rad)
            am = sec_zen * (1 - 0.0012 * (sec_zen * sec_zen - 1))
        elif 'young1994' == model:
            am = ((1.002432*((math.sin(alt_rad)) ** 2) +
                  0.148386*(math.sin(alt_rad)) + 0.0096467) /
                  (math.sin(alt_rad) ** 3 +
                  0.149864*(math.sin(alt_rad) ** 2) +
                  0.0102963*(math.sin(alt_rad)) + 0.000303978))
        elif 'gueymard1993' == model:
            am = (1.0 / (math.sin(alt_rad) +
                  0.00176759*(90 - altitude)*(
                      (94.37515 - (90 - altitude)) ** - 1.21563)))
        else:
            raise ValueError('%s is not a valid model for relativeairmass', model)
    return am
