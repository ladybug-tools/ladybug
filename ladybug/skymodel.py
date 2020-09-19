# coding=utf-8
from __future__ import division
"""Functions for computing radiation for different idealized skies"""

from .psychrometrics import dew_point_from_db_rh

import math
try:  # python 2
    from itertools import izip as zip
except ImportError:  # python 3
    xrange = range


"""ORIGINAL AHSRAE CLEAR SKY SOLAR MODEL"""


def ashrae_clear_sky(altitudes, month, sky_clearness=1):
    """Calculate solar flux for an original ASHRAE Clear Sky.

    Note:
        [1] American Society of Heating Refrigerating and Air-Conditioning Engineers.
        2005. 2005 ASHRAE Handbook: Fundamentals. Atlanta, GA. Chapter 31.

    Args:
        altitudes: A list of solar altitudes in degrees
        month: An integer (1-12) indicating the month the altitudes belong to
        sky_clearness: A factor that will be multiplied by the output of
            the model. This is to help account for locations where clear,
            dry skies predominate (e.g., at high elevations) or,
            conversely, where hazy and humid conditions are frequent. See
            Threlkeld and Jordan (1958) for recommended values. Typical
            values range from 0.95 to 1.05 and are usually never more
            than 1.2. Default is set to 1.0.

    Returns:
        A tuple with two elements

        -   dir_norm_rad: A list of direct normal radiation values for each
            of the connected altitudes in W/m2.

        -   dif_horiz_rad: A list of diffuse horizontall radiation values for each
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


def ashrae_revised_clear_sky(altitudes, tb, td, use_2017_model=False):
    """Calculate solar flux for an ASHRAE Revised Clear Sky ("Tau Model").

    Note:
        [1] American Society of Heating, Refrigerating and Air-Conditioning Engineers.
        2009. 2009 Ashrae Handbook: Fundamentals. Atlanta, GA.

    Args:
        altitudes: A list of solar altitudes in degrees.
        tb: A value indicating the beam optical depth of the sky.
        td: A value indicating the diffuse optical depth of the sky.
        use_2017_model: Set to True to use coefficients associated with
            the new version of the Tau model released in the 2013 and 2017 HOF.
            Note that the correct use of the new version requires updated
            tb and td values. At present, all .stat files
            distributed by the US DoE are using the older (2009) values
            for tb and td and so this input defaults to False.

    Returns:
        A tuple with two elements

        -   dir_norm_rad: A list of direct normal radiation values for each
            of the connected altitudes in W/m2.

        -   dif_horiz_rad: A list of diffuse horizontall radiation values for each
            of the connected altitudes in W/m2.
    """
    dir_norm_rad = []
    dif_horiz_rad = []

    if use_2017_model:
        ab = 1.454 - (0.406 * tb) - (0.268 * td) - (0.021 * tb * td)
        ad = 0.507 + (0.205 * tb) - (0.080 * td) - (0.190 * tb * td)
    else:
        ab = 1.219 - (0.043 * tb) - (0.151 * td) - (0.204 * tb * td)
        ad = 0.202 + (0.852 * tb) - (0.007 * td) - (0.357 * tb * td)

    # compute hourly radiation
    for alt in altitudes:
        if alt > 0:
            # calculate hourly air mass between top of the atmosphere and earth
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

    Note:
        [1] Zhang, Q.Y. and Huang, Y.J. 2002. "Development of typical year weather files
        for Chinese locations", LBNL-51436, ASHRAE Transactions, Vol. 108, Part 2.

    Args:
        alt: A solar altitude in degrees.
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
        glob_ir -- A global horizontall radiation value in W/m2.
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
                            atm_pressure, use_disc=False):
    """Calculate direct and diffuse solar irradiance using the Zhang-Huang model.

    By default, this function uses the DIRINT method (aka. Perez split) to split global
    irradiance into direct and diffuse.  This is the same method used by EnergyPlus.

    Args:
        altitudes: A list of solar altitudes in degrees.
        doys: A list of days of the year that correspond to the altitudes.
        cloud_cover: A list of float values between 0 and 10 that represents cloud cover
            in tenths (0 = clear; 10 = completely overcast)
        relative_humidity: A list of float values between 0 and 100 that represents
            the relative humidity in percent.
        dry_bulb_present: A list of float values that represents the dry bulb
            temperature at the time of interest (in degrees C).
        dry_bulb_t3_hrs: A list of float values that represents the dry bulb
            temperature at three hours before the time of interest (in degrees C).
        wind_speed: A list of float values that represents the wind speed in m/s.
        atm_pressure: A list of float values that represent the
            atmospheric pressure in Pa.
        use_disc: Set to True to use the original DISC model as opposed to the
            newer and more accurate DIRINT model. Default: False.

    Returns:
        A tuple with two elements

        -   dir_norm_rad: A list of direct normal radiation values for each
            of the connected altitudes in W/m2.

        -   dif_horiz_rad: A list of diffuse horizontall radiation values for each
            of the connected altitudes in W/m2.
    """
    # Calculate global horizontal irradiance using the original zhang-huang model
    glob_ir = []
    for i in xrange(len(altitudes)):
        ghi = zhang_huang_solar(altitudes[i], cloud_cover[i], relative_humidity[i],
                                dry_bulb_present[i], dry_bulb_t3_hrs[i], wind_speed[i])
        glob_ir.append(ghi)

    if not use_disc:
        # Calculate dew point temperature to improve the splitting of direct + diffuse
        temp_dew = [dew_point_from_db_rh(dry_bulb_present[i], relative_humidity[i])
                    for i in xrange(len(glob_ir))]

        # Split global rad into direct + diffuse using dirint method (aka. Perez split)
        dir_norm_rad = dirint(glob_ir, altitudes, doys, atm_pressure,
                              use_delta_kt_prime=True, temp_dew=temp_dew)

        # Calculate diffuse horizontal from dni and ghi.
        dif_horiz_rad = [glob_ir[i] -
                         (dir_norm_rad[i] * math.sin(math.radians(altitudes[i])))
                         for i in xrange(len(glob_ir))]
    else:
        dir_norm_rad = []
        dif_horiz_rad = []
        for i in xrange(len(glob_ir)):
            dni, kt, am = disc(glob_ir[i], altitudes[i], doys[i], atm_pressure[i])
            dhi = glob_ir[i] - (dni * math.sin(math.radians(altitudes[i])))
            dir_norm_rad.append(dni)
            dif_horiz_rad.append(dhi)

    return dir_norm_rad, dif_horiz_rad


"""LUMINOUS EFFICACY OF THE SKY"""


def estimate_illuminance_from_irradiance(
        altitude, ghi, dni, dhi, dew_point, rel_airmass=None):
    """Estimate sky illuminance components from irradiance components.

    This function uses actual zenith rather than apparent zenith.

    Note:
        [1] Perez R. (1990). 'Modeling Daylight Availability and Irradiance
        Components from Direct and Global Irradiance'. Solar Energy.
        Vol. 44. No. 5, pp. 271-289. USA.

    Args:
        altitude: Solar altitude angle in degrees.
        ghi: Number for Global Horizontal Irradiance in W/m2.
        dni: Number for Direct Normal Irradiance in W/m2.
        dhi: Number for Diffuse Horizontal Irradiance in W/m2.
        dew_point: Surface dewpoint in degrees C.
        rel_airmass: A number between 1 and ~38 representing the ratio of air mass
            between the sun and the observer and the air mass that is directly above
            the observer. Default is None, which will simply use the input solar
            altitude and the get_relative_airmass function in this module with
            the kastenyoung1989 model to compute this value.

    Returns:
        A tuple with four elements

        -   gh_ill: Value for Global Horizontal Illuminance in lux.

        -   dn_ill: Value for Direct Normal Illuminance in lux.

        -   dh_ill: Value for Diffuse Horizontal Illuminance in lux.

        -   z_lum: Value for Zenith Luminance in lux.

    """
    if altitude <= 0:  # sun is below the horizon, return 0 for all results
        return 0, 0, 0, 0

    if rel_airmass is None:
        rel_airmass = get_relative_airmass(altitude)
    zenith = math.radians(90 - altitude)
    dhi = 0.1 if dhi == 0 else dhi
    kai = 1.041
    eps = ((dhi + dni) / dhi + kai * zenith ** 3) / (1 + kai * zenith ** 3)
    delta = dhi * rel_airmass / 1360
    w = math.exp(0.08 * dew_point - 0.075)

    # Perez Table 1: Discrete Sky Clearness Categories
    if eps >= 1 and eps < 1.065:
        e_category = 0
    elif eps >= 1.065 and eps < 1.23:
        e_category = 1
    elif eps >= 1.23 and eps < 1.5:
        e_category = 2
    elif eps >= 1.5 and eps < 1.95:
        e_category = 3
    elif eps >= 1.95 and eps < 2.8:
        e_category = 4
    elif eps >= 2.8 and eps < 4.5:
        e_category = 5
    elif eps >= 4.5 and eps < 6.2:
        e_category = 6
    elif eps >= 6.2:
        e_category = 7
    else:
        raise ValueError('Error in sky luminous efficacy calculation\n'
                         'eps: %f  altitude: %f' % (eps, altitude))

    # Perez Table 4: Luminous Efficacy
    glob_lum_eff_coeff = ((96.63, -0.47, 11.50, -9.16),
                          (107.54, 0.79, 1.79, -1.19),
                          (98.73, 0.70, 4.40, -6.95),
                          (92.72, 0.56, 8.36, -8.31),
                          (86.73, 0.98, 7.10, -10.94),
                          (88.34, 1.39, 6.06, -7.60),
                          (78.63, 1.47, 4.93, -11.37),
                          (99.65, 1.86, -4.46, -3.15))

    dir_lum_eff_coeff = ((57.20, -4.55, -2.98, 117.12),
                         (98.99, -3.46, -1.21, 12.38),
                         (109.83, -4.90, -1.71, -8.81),
                         (110.34, -5.84, -1.99, -4.56),
                         (106.36, -3.97, -1.75, -6.16),
                         (107.19, -1.25, -1.51, -26.73),
                         (105.75, 0.77, -1.26, -34.44),
                         (101.18, 1.58, -1.10, -8.29))

    diff_lum_eff_coeff = ((97.24, -0.46, 12.00, -8.91),
                          (107.22, 1.15, 0.59, -3.95),
                          (104.97, 2.96, -5.52, -8.77),
                          (102.39, 5.59, -13.95, -13.90),
                          (100.71, 5.94, -22.75, -23.74),
                          (106.42, 3.83, -36.15, -28.83),
                          (141.88, 1.90, -53.24, -14.03),
                          (152.23, 0.35, -45.27, -7.98))

    zen_lum_eff_coeff = ((40.86, 26.77, -29.59, -45.75),
                         (26.58, 14.73, 58.46, -21.25),
                         (19.34, 2.28, 100.00, 0.25),
                         (13.25, -1.39, 124.79, 15.66),
                         (14.47, -5.09, 160.09, 9.13),
                         (19.76, -3.88, 154.61, -19.21),
                         (28.39, -9.67, 151.58, -69.39),
                         (42.91, -19.62, 130.80, -164.08))

    # Eq 6
    a, b, c, d = glob_lum_eff_coeff[e_category]
    gh_ill = ghi * (a + b * w + c * math.cos(zenith) + d * math.log(delta))

    # Eq 8
    a, b, c, d = dir_lum_eff_coeff[e_category]
    dn_ill = max(0, dni * (a + b * w + c * math.exp(5.73 * zenith - 5) + d * delta))

    # Eq 7
    a, b, c, d = diff_lum_eff_coeff[e_category]
    dh_ill = dhi * (a + b * w + c * math.cos(zenith) + d * math.log(delta))

    # Eq 9
    a, b, c, d = zen_lum_eff_coeff[e_category]
    z_lum = dhi * (a + b * math.cos(zenith) + c * math.exp(-3 * zenith) + d * delta)

    return gh_ill, dn_ill, dh_ill, z_lum


"""HORIZONTAL INFRARED INTENSITY + SKY TEMPERATURE MODELS"""


def calc_horizontal_infrared(sky_cover, dry_bulb, dew_point):
    """Calculate horizontal infrared radiation intensity.

    See EnergyPlus Engineering Reference for more information:
    https://bigladdersoftware.com/epx/docs/8-9/engineering-reference/climate-calculations.html#sky-radiation-modeling

    Note:
        [1] Walton, G. N. 1983. Thermal Analysis Research Program Reference Manual.
        NBSSIR 83-2655. National Bureau of Standards, p. 21.

        [2] Clark, G. and C. Allen, “The Estimation of Atmospheric Radiation for
        Clear and Cloudy Skies,” Proceedings 2nd National Passive Solar Conference
        (AS/ISES), 1978, pp. 675-678.

    Args:
        sky_cover: A float value between 0 and 10 that represents the opaque
            sky cover in tenths (0 = clear; 10 = completely overcast)
        dry_bulb: A float value that represents the dry bulb temperature
            in degrees C.
        dew_point: A float value that represents the dew point temperature
            in degrees C.

    Returns:
        horiz_ir -- A horizontal infrared radiation intensity value in W/m2.
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


def calc_sky_temperature(horiz_ir, source_emissivity=1):
    """Calculate sky temperature in Celsius.

    See EnergyPlus Engineering Reference for more information:
    https://bigladdersoftware.com/epx/docs/8-9/engineering-reference/
    climate-calculations.html#energyplus-sky-temperature-calculation

    Args:
        horiz_ir: A float value that represents horizontal infrared radiation
            intensity in W/m2.
        source_emissivity: A float value between 0 and 1 indicating the emissivity
             of the heat source that is radiating to the sky. Default is 1 for
             most outdoor surfaces.

    Returns:
        sky_temp -- A sky temperature value in C.
    """
    sigma = 5.6697e-8  # stefan-boltzmann constant
    return ((horiz_ir / (source_emissivity * sigma)) ** 0.25) - 273.15


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


def dirint(ghi, altitudes, doys, pressures, use_delta_kt_prime=True,
           temp_dew=None, min_sin_altitude=0.065, min_altitude=3):
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
    The DIRINT model requires time series data.

    Note:
        [1] Perez, R., P. Ineichen, E. Maxwell, R. Seals and A. Zelenka,
        (1992). "Dynamic Global-to-Direct Irradiance Conversion Models".
        ASHRAE Transactions-Research Series, pp. 354-369

        [2] Maxwell, E. L., "A Quasi-Physical Model for Converting Hourly
        Global Horizontal to Direct Normal Insolation", Technical Report No.
        SERI/TR-215-3087, Golden, CO: Solar Energy Research Institute, 1987.

    Args:
        ghi: array-like
            Global horizontal irradiance in W/m^2.
        altitudes: array-like
            True (not refraction-corrected) solar altitude angles in decimal
            degrees.
        doys: array-like
            Integers representing the day of the year.
        pressures: array-like
            The site pressure in Pascal. Pressure may be measured or an
            average pressure may be calculated from site altitude.
        use_delta_kt_prime: bool, default True
            If True, indicates that the stability index delta_kt_prime is
            included in the model. The stability index adjusts the estimated
            DNI in response to dynamics in the time series of GHI. It is
            recommended that delta_kt_prime is not used if the time between
            GHI points is 1.5 hours or greater. If use_delta_kt_prime=True,
            input data must be Series.
        temp_dew: None or array-like, default None
            Surface dew point temperatures, in degrees C. Values of temp_dew
            must be numeric. If temp_dew is not provided, then dew point
            improvements are not applied.
        min_sin_altitude: numeric, default 0.065
            Minimum value of sin(altitude) to allow when calculating global
            clearness index `kt`. Equivalent to altitude = 3.727 degrees.
        min_altitude: numeric, default 87
            Minimum value of altitude to allow in DNI calculation. DNI will be
            set to 0 for times with altitude values smaller than `min_altitude`.

    Returns:
        dni -- array-like.
        The modeled direct normal irradiance in W/m^2 provided by the
        DIRINT model.
    """
    # calculate kt_prime values
    kt_primes = []
    disc_dni = []
    for i in xrange(len(ghi)):
        dni, kt, airmass = disc(ghi[i], altitudes[i], doys[i], pressure=pressures[i],
                                min_sin_altitude=min_sin_altitude,
                                min_altitude=min_altitude)
        kt_prime = clearness_index_zenith_independent(
            kt, airmass, max_clearness_index=1)
        kt_primes.append(kt_prime)
        disc_dni.append(dni)

    # calculate delta_kt_prime values
    if use_delta_kt_prime:
        delta_kt_prime = []
        for i in xrange(len(kt_primes)):
            try:
                kt_prime_1 = kt_primes[i + 1]
            except IndexError:
                # last hour
                kt_prime_1 = kt_primes[0]
            delta_kt_prime.append(0.5 * (abs(kt_primes[i] - kt_prime_1) +
                                         abs(kt_primes[i] - kt_primes[i - 1])))
    else:
        delta_kt_prime = [-1] * len(ghi)

    # calculate W values if dew point temperatures have been provided
    if temp_dew is not None:
        w = [math.exp(0.07 * td - 0.075) for td in temp_dew]
    else:
        w = [-1] * len(ghi)

    # bin the values into appropriate categories for lookup in the coefficient matrix.
    ktp_bin, alt_bin, w_bin, delta_ktp_bin = \
        _dirint_bins(kt_primes, altitudes, w, delta_kt_prime)

    # get the dirint coefficient by looking up values in the matrix
    coeffs = _get_dirint_coeffs()
    dirint_coeffs = [coeffs[ktp_bin[i]][alt_bin[i]][delta_ktp_bin[i]][w_bin[i]]
                     for i in xrange(len(ghi))]

    # Perez eqn 5
    dni = [disc_d * coef for disc_d, coef in zip(disc_dni, dirint_coeffs)]

    return dni


def _dirint_bins(ktp, alt, w, dktp):
    """
    Determine the bins for the DIRINT coefficients.

    Args:
        ktp : Altitude-independent clearness index
        alt : Solar altitude angle
        w : precipitable water estimated from surface dew-point temperature
        dktp : stability index

    Returns:
        tuple of ktp_bin, alt_bin, w_bin, dktp_bin
    """
    it = xrange(len(ktp))

    # Create kt_prime bins
    ktp_bin = [-1] * len(ktp)
    ktp_bin = [0 if ktp[i] >= 0 and ktp[i] < 0.24 else ktp_bin[i] for i in it]
    ktp_bin = [1 if ktp[i] >= 0.24 and ktp[i] < 0.4 else ktp_bin[i] for i in it]
    ktp_bin = [2 if ktp[i] >= 0.4 and ktp[i] < 0.56 else ktp_bin[i] for i in it]
    ktp_bin = [3 if ktp[i] >= 0.56 and ktp[i] < 0.7 else ktp_bin[i] for i in it]
    ktp_bin = [4 if ktp[i] >= 0.7 and ktp[i] < 0.8 else ktp_bin[i] for i in it]
    ktp_bin = [5 if ktp[i] >= 0.8 and ktp[i] <= 1 else ktp_bin[i] for i in it]

    # Create altitude angle bins
    alt_bin = [-1] * len(alt)
    alt_bin = [0 if alt[i] <= 90 and alt[i] > 65 else alt_bin[i] for i in it]
    alt_bin = [1 if alt[i] <= 65 and alt[i] > 50 else alt_bin[i] for i in it]
    alt_bin = [2 if alt[i] <= 50 and alt[i] > 35 else alt_bin[i] for i in it]
    alt_bin = [3 if alt[i] <= 35 and alt[i] > 20 else alt_bin[i] for i in it]
    alt_bin = [4 if alt[i] <= 20 and alt[i] > 10 else alt_bin[i] for i in it]
    alt_bin = [5 if alt[i] <= 10 else alt_bin[i] for i in it]

    # Create the bins for w based on dew point temperature
    w_bin = [-1] * len(w)
    w_bin = [0 if w[i] >= 0 and w[i] < 1 else w_bin[i] for i in it]
    w_bin = [1 if w[i] >= 1 and w[i] < 2 else w_bin[i] for i in it]
    w_bin = [2 if w[i] >= 2 and w[i] < 3 else w_bin[i] for i in it]
    w_bin = [3 if w[i] >= 3 else w_bin[i] for i in it]
    w_bin = [4 if w[i] == -1 else w_bin[i] for i in it]

    # Create delta_kt_prime binning.
    dktp_bin = [-1] * len(dktp)
    dktp_bin = [0 if dktp[i] >= 0 and dktp[i] < 0.015 else dktp_bin[i] for i in it]
    dktp_bin = [1 if dktp[i] >= 0.015 and dktp[i] < 0.035 else dktp_bin[i] for i in it]
    dktp_bin = [2 if dktp[i] >= 0.035 and dktp[i] < 0.07 else dktp_bin[i] for i in it]
    dktp_bin = [3 if dktp[i] >= 0.07 and dktp[i] < 0.15 else dktp_bin[i] for i in it]
    dktp_bin = [4 if dktp[i] >= 0.15 and dktp[i] < 0.3 else dktp_bin[i] for i in it]
    dktp_bin = [5 if dktp[i] >= 0.3 and dktp[i] <= 1 else dktp_bin[i] for i in it]
    dktp_bin = [6 if dktp[i] == -1 else dktp_bin[i] for i in it]

    return ktp_bin, alt_bin, w_bin, dktp_bin


def disc(ghi, altitude, doy, pressure=101325,
         min_sin_altitude=0.065, min_altitude=3, max_airmass=12):
    """
    Estimate Direct Normal Irradiance from Global Horizontal Irradiance
    using the DISC model.

    The DISC algorithm converts global horizontal irradiance to direct
    normal irradiance through empirical relationships between the global
    and direct clearness indices.

    This implementation limits the clearness index to 1 by default.

    The original report describing the DISC model [1] uses the
    relative air mass rather than the absolute (pressure-corrected)
    air mass. However, the NREL implementation of the DISC model [2]
    uses absolute air mass. PVLib Matlab also uses the absolute air mass.
    pvlib python defaults to absolute air mass, but the relative airmass
    can be used by supplying `pressure=None`.

    Note:
        [1] Maxwell, E. L., "A Quasi-Physical Model for Converting Hourly
        Global Horizontal to Direct Normal Insolation", Technical
        Report No. SERI/TR-215-3087, Golden, CO: Solar Energy Research
        Institute, 1987.

        [2] Maxwell, E. "DISC Model", Excel Worksheet.
        https://www.nrel.gov/grid/solar-resource/disc.html

    Args:
        ghi : numeric
            Global horizontal irradiance in W/m^2.
        altitude : numeric
            True (not refraction-corrected) solar altitude angles in decimal
            degrees.
        doy : An integer representing the day of the year.
        pressure : None or numeric, default 101325
            Site pressure in Pascal. If None, relative air mass is used
            instead of absolute (pressure-corrected) air mass.
        min_sin_altitude : numeric, default 0.065
            Minimum value of sin(altitude) to allow when calculating global
            clearness index `kt`. Equivalent to altitude = 3.727 degrees.
        min_altitude : numeric, default 87
            Minimum value of altitude to allow in DNI calculation. DNI will be
            set to 0 for times with altitude values smaller than `min_altitude`.
        max_airmass : numeric, default 12
            Maximum value of the air mass to allow in Kn calculation.
            Default value (12) comes from range over which Kn was fit
            to air mass in the original paper.

    Returns:
        A tuple with two elements

        -   dni: The modeled direct normal irradiance
            in W/m^2 provided by the
            Direct Insolation Simulation Code (DISC) model.

        -   kt: Ratio of global to extraterrestrial
            irradiance on a horizontal plane.

        -   am: Airmass
    """
    if altitude > min_altitude and ghi > 0:
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
        dni = max(dni, 0)

        return dni, kt, am
    else:
        return 0, 0, None


def _disc_kn(clearness_index, airmass, max_airmass=12):
    """
    Calculate Kn for `disc`

    Args:
        clearness_index : numeric
        airmass : numeric
        max_airmass : float
            airmass > max_airmass is set to max_airmass before being used
            in calculating Kn.

    Returns:
        A tuple with two elements

        -   Kn : numeric

        -   am : numeric
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
        a = 0.512 - 1.56 * kt + 2.286 * kt2 - 2.222 * kt3
        b = 0.37 + 0.962 * kt
        c = -0.28 + 0.932 * kt - 2.048 * kt2
    else:
        a = -5.743 + 21.77 * kt - 27.49 * kt2 + 11.56 * kt3
        b = 41.4 - 118.5 * kt + 66.05 * kt2 + 31.9 * kt3
        c = -47.01 + 184.2 * kt - 222.0 * kt2 + 73.81 * kt3

    delta_kn = a + b * math.exp(c * am)

    Knc = 0.866 - 0.122 * am + 0.0121 * am ** 2 - 0.000653 * am ** 3 + \
        1.4e-05 * am ** 4
    Kn = Knc - delta_kn
    return Kn, am


def get_extra_radiation(doy, solar_constant=1366.1):
    """
    Determine extraterrestrial radiation from day of year (using the spencer method).

    Note:
        [1] M. Reno, C. Hansen, and J. Stein, "Global Horizontal Irradiance
        Clear Sky Models: Implementation and Analysis", Sandia National
        Laboratories, SAND2012-2389, 2012.

        [2] <http://solardat.uoregon.edu/SolarRadiationBasics.html>, Eqs.
        SR1 and SR2

    Args:
        doy : array of integers representing the days of the year.
        solar_constant : float, default 1366.1
            The solar constant.

    Returns:
        dni_extra -- float, array, or Series.
        The extraterrestrial radiation present in watts per square meter
        on a surface which is normal to the sun. Pandas Timestamp and
        DatetimeIndex inputs will yield a Pandas TimeSeries. All other
        inputs will yield a float or an array of floats.
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

    Note:
        [1] Maxwell, E. L., "A Quasi-Physical Model for Converting Hourly
        Global Horizontal to Direct Normal Insolation", Technical
        Report No. SERI/TR-215-3087, Golden, CO: Solar Energy Research
        Institute, 1987.

    Args:
        ghi: numeric
            Global horizontal irradiance in W/m^2.
        altitude: numeric
            True (not refraction-corrected) solar altitude angle in decimal
            degrees.
        extra_radiation: numeric
            Irradiance incident at the top of the atmosphere
        min_sin_altitude: numeric, default 0.065
            Minimum value of sin(altitude) to allow when calculating global
            clearness index `kt`. Equivalent to altitude = 3.727 degrees.
        max_clearness_index: numeric, default 2.0
            Maximum value of the clearness index. The default, 2.0, allows
            for over-irradiance events typically seen in sub-hourly data.
            NREL's SRRL Fortran code used 0.82 for hourly data.

    Returns:
        kt -- numeric.
        Clearness index
    """
    sin_altitude = math.sin(math.radians(altitude))
    I0h = extra_radiation * max(sin_altitude, min_sin_altitude)
    kt = ghi / I0h
    kt = max(kt, 0)
    kt = min(kt, max_clearness_index)
    return kt


def clearness_index_zenith_independent(clearness_index, airmass,
                                       max_clearness_index=2.0):
    """
    Calculate the zenith angle independent clearness index.

    Note:
        [1] Perez, R., P. Ineichen, E. Maxwell, R. Seals and A. Zelenka,
        (1992). "Dynamic Global-to-Direct Irradiance Conversion Models".
        ASHRAE Transactions-Research Series, pp. 354-369

    Args:
        clearness_index: numeric.
            Ratio of global to extraterrestrial irradiance on a horizontal
            plane
        airmass: numeric
            Airmass
        max_clearness_index: numeric, default 2.0
            Maximum value of the clearness index. The default, 2.0, allows
            for over-irradiance events typically seen in sub-hourly data.
            NREL's SRRL Fortran code used 0.82 for hourly data.

    Returns:
        kt_prime -- numeric.
        Zenith independent clearness index
    """
    if airmass is not None:
        # Perez eqn 1
        kt_prime = clearness_index / (
            1.031 * math.exp(-1.4 / (0.9 + 9.4 / airmass)) + 0.1)
        kt_prime = max(kt_prime, 0)
        kt_prime = min(kt_prime, max_clearness_index)
        return kt_prime
    else:
        return 0


def get_absolute_airmass(airmass_relative, pressure=101325.):
    """
    Determine absolute (pressure corrected) airmass from relative
    airmass and atmospheric pressure.

    Gives the airmass for locations not at sea-level (i.e. not at
    standard pressure). The input argument airmass_relative is the relative
    air mass. The input argument pressure is the pressure (in Pascals)
    at the location of interest and must be greater than 0. The
    calculation for absolute air mass is
    `absolute airmass = (relative airmass)*pressure/101325`

    Note:
        [1] C. Gueymard, "Critical analysis and performance assessment of
        clear sky solar irradiance models using theoretical and measured
        data," Solar Energy, vol. 51, pp. 121-138, 1993.

    Args:
        airmass_relative: numeric.
            The air mass at sea-level.
        pressure: numeric, default 101325
            The site pressure in Pascal.

    Returns:
        airmass_absolute -- numeric.
        Absolute (pressure corrected) air mass
    """
    if airmass_relative is not None:
        return airmass_relative * pressure / 101325.
    else:
        return None


def get_relative_airmass(altitude, model='kastenyoung1989'):
    """
    Gives the relative (not pressure-corrected) airmass.

    Gives the airmass at sea-level when given a sun altitude angle (in
    degrees). The `model` variable allows selection of different
    airmass models (described below). If `model` is not included or is
    not valid, the default model is 'kastenyoung1989'.

    Note:
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

    Args:
        altitude: numeric
            Altitude angle of the sun in degrees. Note that some models use
            the apparent (refraction corrected) altitude angle, and some
            models use the true (not refraction-corrected) altitude angle. See
            model descriptions to determine which type of altitude angle is
            required. Apparent altitude angles must be calculated at sea level.
        model: string, default 'kastenyoung1989'

                Available models include the following:

                *   'simple' - secant(apparent altitude angle) -
                    Note that this gives -inf at altitude=0
                *   'kasten1966' - See reference [1] -
                    requires apparent sun altitude
                *   'youngirvine1967' - See reference [2] -
                    requires true sun altitude
                *   'kastenyoung1989' - See reference [3] -
                    requires apparent sun altitude
                *   'gueymard1993' - See reference [4] -
                    requires apparent sun altitude
                *   'young1994' - See reference [5] -
                    requires true sun altitude
                *   'pickering2002' - See reference [6] -
                    requires apparent sun altitude

    Returns:
        airmass_relative -- Relative airmass at sea level. Will return None for any
        altitude angle smaller than 0 degrees.
    """
    if altitude < 0:
        return None
    else:
        alt_rad = math.radians(altitude)
        model = model.lower()

        if 'kastenyoung1989' == model:
            am = (1.0 / (math.sin(alt_rad) +
                  0.50572 * (((6.07995 + altitude) ** - 1.6364))))
        elif 'kasten1966' == model:
            am = 1.0 / (math.sin(alt_rad) + 0.15 * ((3.885 + altitude) ** - 1.253))
        elif 'simple' == model:
            am = 1.0 / math.sin(altitude)
        elif 'pickering2002' == model:
            am = (1.0 / (math.sin(math.radians(altitude +
                  244.0 / (165 + 47.0 * altitude ** 1.1)))))
        elif 'youngirvine1967' == model:
            sec_zen = 1.0 / math.sin(alt_rad)
            am = sec_zen * (1 - 0.0012 * (sec_zen * sec_zen - 1))
        elif 'young1994' == model:
            am = ((1.002432 * ((math.sin(alt_rad)) ** 2) +
                  0.148386 * (math.sin(alt_rad)) + 0.0096467) /
                  (math.sin(alt_rad) ** 3 +
                  0.149864 * (math.sin(alt_rad) ** 2) +
                  0.0102963 * (math.sin(alt_rad)) + 0.000303978))
        elif 'gueymard1993' == model:
            am = (1.0 / (math.sin(alt_rad) +
                  0.00176759 * (90 - altitude) * (
                      (94.37515 - (90 - altitude)) ** - 1.21563)))
        else:
            raise ValueError('%s is not a valid model for relativeairmass', model)
    return am


def _get_dirint_coeffs():
    """
    Here be a large multi-dimensional matrix of dirint coefficients.

    Returns:
        Array with shape ``(6, 6, 7, 5)``.
        Ordering is ``[kt_prime_bin, zenith_bin, delta_kt_prime_bin, w_bin]``
    """
    coeffs = [[0 for i in xrange(6)] for j in xrange(6)]

    coeffs[0][0] = [
        [0.385230, 0.385230, 0.385230, 0.462880, 0.317440],
        [0.338390, 0.338390, 0.221270, 0.316730, 0.503650],
        [0.235680, 0.235680, 0.241280, 0.157830, 0.269440],
        [0.830130, 0.830130, 0.171970, 0.841070, 0.457370],
        [0.548010, 0.548010, 0.478000, 0.966880, 1.036370],
        [0.548010, 0.548010, 1.000000, 3.012370, 1.976540],
        [0.582690, 0.582690, 0.229720, 0.892710, 0.569950]]

    coeffs[0][1] = [
        [0.131280, 0.131280, 0.385460, 0.511070, 0.127940],
        [0.223710, 0.223710, 0.193560, 0.304560, 0.193940],
        [0.229970, 0.229970, 0.275020, 0.312730, 0.244610],
        [0.090100, 0.184580, 0.260500, 0.687480, 0.579440],
        [0.131530, 0.131530, 0.370190, 1.380350, 1.052270],
        [1.116250, 1.116250, 0.928030, 3.525490, 2.316920],
        [0.090100, 0.237000, 0.300040, 0.812470, 0.664970]]

    coeffs[0][2] = [
        [0.587510, 0.130000, 0.400000, 0.537210, 0.832490],
        [0.306210, 0.129830, 0.204460, 0.500000, 0.681640],
        [0.224020, 0.260620, 0.334080, 0.501040, 0.350470],
        [0.421540, 0.753970, 0.750660, 3.706840, 0.983790],
        [0.706680, 0.373530, 1.245670, 0.864860, 1.992630],
        [4.864400, 0.117390, 0.265180, 0.359180, 3.310820],
        [0.392080, 0.493290, 0.651560, 1.932780, 0.898730]]

    coeffs[0][3] = [
        [0.126970, 0.126970, 0.126970, 0.126970, 0.126970],
        [0.810820, 0.810820, 0.810820, 0.810820, 0.810820],
        [3.241680, 2.500000, 2.291440, 2.291440, 2.291440],
        [4.000000, 3.000000, 2.000000, 0.975430, 1.965570],
        [12.494170, 12.494170, 8.000000, 5.083520, 8.792390],
        [21.744240, 21.744240, 21.744240, 21.744240, 21.744240],
        [3.241680, 12.494170, 1.620760, 1.375250, 2.331620]]

    coeffs[0][4] = [
        [0.126970, 0.126970, 0.126970, 0.126970, 0.126970],
        [0.810820, 0.810820, 0.810820, 0.810820, 0.810820],
        [3.241680, 2.500000, 2.291440, 2.291440, 2.291440],
        [4.000000, 3.000000, 2.000000, 0.975430, 1.965570],
        [12.494170, 12.494170, 8.000000, 5.083520, 8.792390],
        [21.744240, 21.744240, 21.744240, 21.744240, 21.744240],
        [3.241680, 12.494170, 1.620760, 1.375250, 2.331620]]

    coeffs[0][5] = [
        [0.126970, 0.126970, 0.126970, 0.126970, 0.126970],
        [0.810820, 0.810820, 0.810820, 0.810820, 0.810820],
        [3.241680, 2.500000, 2.291440, 2.291440, 2.291440],
        [4.000000, 3.000000, 2.000000, 0.975430, 1.965570],
        [12.494170, 12.494170, 8.000000, 5.083520, 8.792390],
        [21.744240, 21.744240, 21.744240, 21.744240, 21.744240],
        [3.241680, 12.494170, 1.620760, 1.375250, 2.331620]]

    coeffs[1][0] = [
        [0.337440, 0.337440, 0.969110, 1.097190, 1.116080],
        [0.337440, 0.337440, 0.969110, 1.116030, 0.623900],
        [0.337440, 0.337440, 1.530590, 1.024420, 0.908480],
        [0.584040, 0.584040, 0.847250, 0.914940, 1.289300],
        [0.337440, 0.337440, 0.310240, 1.435020, 1.852830],
        [0.337440, 0.337440, 1.015010, 1.097190, 2.117230],
        [0.337440, 0.337440, 0.969110, 1.145730, 1.476400]]

    coeffs[1][1] = [
        [0.300000, 0.300000, 0.700000, 1.100000, 0.796940],
        [0.219870, 0.219870, 0.526530, 0.809610, 0.649300],
        [0.386650, 0.386650, 0.119320, 0.576120, 0.685460],
        [0.746730, 0.399830, 0.470970, 0.986530, 0.785370],
        [0.575420, 0.936700, 1.649200, 1.495840, 1.335590],
        [1.319670, 4.002570, 1.276390, 2.644550, 2.518670],
        [0.665190, 0.678910, 1.012360, 1.199940, 0.986580]]

    coeffs[1][2] = [
        [0.378870, 0.974060, 0.500000, 0.491880, 0.665290],
        [0.105210, 0.263470, 0.407040, 0.553460, 0.582590],
        [0.312900, 0.345240, 1.144180, 0.854790, 0.612280],
        [0.119070, 0.365120, 0.560520, 0.793720, 0.802600],
        [0.781610, 0.837390, 1.270420, 1.537980, 1.292950],
        [1.152290, 1.152290, 1.492080, 1.245370, 2.177100],
        [0.424660, 0.529550, 0.966910, 1.033460, 0.958730]]

    coeffs[1][3] = [
        [0.310590, 0.714410, 0.252450, 0.500000, 0.607600],
        [0.975190, 0.363420, 0.500000, 0.400000, 0.502800],
        [0.175580, 0.196250, 0.476360, 1.072470, 0.490510],
        [0.719280, 0.698620, 0.657770, 1.190840, 0.681110],
        [0.426240, 1.464840, 0.678550, 1.157730, 0.978430],
        [2.501120, 1.789130, 1.387090, 2.394180, 2.394180],
        [0.491640, 0.677610, 0.685610, 1.082400, 0.735410]]

    coeffs[1][4] = [
        [0.597000, 0.500000, 0.300000, 0.310050, 0.413510],
        [0.314790, 0.336310, 0.400000, 0.400000, 0.442460],
        [0.166510, 0.460440, 0.552570, 1.000000, 0.461610],
        [0.401020, 0.559110, 0.403630, 1.016710, 0.671490],
        [0.400360, 0.750830, 0.842640, 1.802600, 1.023830],
        [3.315300, 1.510380, 2.443650, 1.638820, 2.133990],
        [0.530790, 0.745850, 0.693050, 1.458040, 0.804500]]

    coeffs[1][5] = [
        [0.597000, 0.500000, 0.300000, 0.310050, 0.800920],
        [0.314790, 0.336310, 0.400000, 0.400000, 0.237040],
        [0.166510, 0.460440, 0.552570, 1.000000, 0.581990],
        [0.401020, 0.559110, 0.403630, 1.016710, 0.898570],
        [0.400360, 0.750830, 0.842640, 1.802600, 3.400390],
        [3.315300, 1.510380, 2.443650, 1.638820, 2.508780],
        [0.204340, 1.157740, 2.003080, 2.622080, 1.409380]]

    coeffs[2][0] = [
        [1.242210, 1.242210, 1.242210, 1.242210, 1.242210],
        [0.056980, 0.056980, 0.656990, 0.656990, 0.925160],
        [0.089090, 0.089090, 1.040430, 1.232480, 1.205300],
        [1.053850, 1.053850, 1.399690, 1.084640, 1.233340],
        [1.151540, 1.151540, 1.118290, 1.531640, 1.411840],
        [1.494980, 1.494980, 1.700000, 1.800810, 1.671600],
        [1.018450, 1.018450, 1.153600, 1.321890, 1.294670]]

    coeffs[2][1] = [
        [0.700000, 0.700000, 1.023460, 0.700000, 0.945830],
        [0.886300, 0.886300, 1.333620, 0.800000, 1.066620],
        [0.902180, 0.902180, 0.954330, 1.126690, 1.097310],
        [1.095300, 1.075060, 1.176490, 1.139470, 1.096110],
        [1.201660, 1.201660, 1.438200, 1.256280, 1.198060],
        [1.525850, 1.525850, 1.869160, 1.985410, 1.911590],
        [1.288220, 1.082810, 1.286370, 1.166170, 1.119330]]

    coeffs[2][2] = [
        [0.600000, 1.029910, 0.859890, 0.550000, 0.813600],
        [0.604450, 1.029910, 0.859890, 0.656700, 0.928840],
        [0.455850, 0.750580, 0.804930, 0.823000, 0.911000],
        [0.526580, 0.932310, 0.908620, 0.983520, 0.988090],
        [1.036110, 1.100690, 0.848380, 1.035270, 1.042380],
        [1.048440, 1.652720, 0.900000, 2.350410, 1.082950],
        [0.817410, 0.976160, 0.861300, 0.974780, 1.004580]]

    coeffs[2][3] = [
        [0.782110, 0.564280, 0.600000, 0.600000, 0.665740],
        [0.894480, 0.680730, 0.541990, 0.800000, 0.669140],
        [0.487460, 0.818950, 0.841830, 0.872540, 0.709040],
        [0.709310, 0.872780, 0.908480, 0.953290, 0.844350],
        [0.863920, 0.947770, 0.876220, 1.078750, 0.936910],
        [1.280350, 0.866720, 0.769790, 1.078750, 0.975130],
        [0.725420, 0.869970, 0.868810, 0.951190, 0.829220]]

    coeffs[2][4] = [
        [0.791750, 0.654040, 0.483170, 0.409000, 0.597180],
        [0.566140, 0.948990, 0.971820, 0.653570, 0.718550],
        [0.648710, 0.637730, 0.870510, 0.860600, 0.694300],
        [0.637630, 0.767610, 0.925670, 0.990310, 0.847670],
        [0.736380, 0.946060, 1.117590, 1.029340, 0.947020],
        [1.180970, 0.850000, 1.050000, 0.950000, 0.888580],
        [0.700560, 0.801440, 0.961970, 0.906140, 0.823880]]

    coeffs[2][5] = [
        [0.500000, 0.500000, 0.586770, 0.470550, 0.629790],
        [0.500000, 0.500000, 1.056220, 1.260140, 0.658140],
        [0.500000, 0.500000, 0.631830, 0.842620, 0.582780],
        [0.554710, 0.734730, 0.985820, 0.915640, 0.898260],
        [0.712510, 1.205990, 0.909510, 1.078260, 0.885610],
        [1.899260, 1.559710, 1.000000, 1.150000, 1.120390],
        [0.653880, 0.793120, 0.903320, 0.944070, 0.796130]]

    coeffs[3][0] = [
        [1.000000, 1.000000, 1.050000, 1.170380, 1.178090],
        [0.960580, 0.960580, 1.059530, 1.179030, 1.131690],
        [0.871470, 0.871470, 0.995860, 1.141910, 1.114600],
        [1.201590, 1.201590, 0.993610, 1.109380, 1.126320],
        [1.065010, 1.065010, 0.828660, 0.939970, 1.017930],
        [1.065010, 1.065010, 0.623690, 1.119620, 1.132260],
        [1.071570, 1.071570, 0.958070, 1.114130, 1.127110]]

    coeffs[3][1] = [
        [0.950000, 0.973390, 0.852520, 1.092200, 1.096590],
        [0.804120, 0.913870, 0.980990, 1.094580, 1.042420],
        [0.737540, 0.935970, 0.999940, 1.056490, 1.050060],
        [1.032980, 1.034540, 0.968460, 1.032080, 1.015780],
        [0.900000, 0.977210, 0.945960, 1.008840, 0.969960],
        [0.600000, 0.750000, 0.750000, 0.844710, 0.899100],
        [0.926800, 0.965030, 0.968520, 1.044910, 1.032310]]

    coeffs[3][2] = [
        [0.850000, 1.029710, 0.961100, 1.055670, 1.009700],
        [0.818530, 0.960010, 0.996450, 1.081970, 1.036470],
        [0.765380, 0.953500, 0.948260, 1.052110, 1.000140],
        [0.775610, 0.909610, 0.927800, 0.987800, 0.952100],
        [1.000990, 0.881880, 0.875950, 0.949100, 0.893690],
        [0.902370, 0.875960, 0.807990, 0.942410, 0.917920],
        [0.856580, 0.928270, 0.946820, 1.032260, 0.972990]]

    coeffs[3][3] = [
        [0.750000, 0.857930, 0.983800, 1.056540, 0.980240],
        [0.750000, 0.987010, 1.013730, 1.133780, 1.038250],
        [0.800000, 0.947380, 1.012380, 1.091270, 0.999840],
        [0.800000, 0.914550, 0.908570, 0.999190, 0.915230],
        [0.778540, 0.800590, 0.799070, 0.902180, 0.851560],
        [0.680190, 0.317410, 0.507680, 0.388910, 0.646710],
        [0.794920, 0.912780, 0.960830, 1.057110, 0.947950]]

    coeffs[3][4] = [
        [0.750000, 0.833890, 0.867530, 1.059890, 0.932840],
        [0.979700, 0.971470, 0.995510, 1.068490, 1.030150],
        [0.858850, 0.987920, 1.043220, 1.108700, 1.044900],
        [0.802400, 0.955110, 0.911660, 1.045070, 0.944470],
        [0.884890, 0.766210, 0.885390, 0.859070, 0.818190],
        [0.615680, 0.700000, 0.850000, 0.624620, 0.669300],
        [0.835570, 0.946150, 0.977090, 1.049350, 0.979970]]

    coeffs[3][5] = [
        [0.689220, 0.809600, 0.900000, 0.789500, 0.853990],
        [0.854660, 0.852840, 0.938200, 0.923110, 0.955010],
        [0.938600, 0.932980, 1.010390, 1.043950, 1.041640],
        [0.843620, 0.981300, 0.951590, 0.946100, 0.966330],
        [0.694740, 0.814690, 0.572650, 0.400000, 0.726830],
        [0.211370, 0.671780, 0.416340, 0.297290, 0.498050],
        [0.843540, 0.882330, 0.911760, 0.898420, 0.960210]]

    coeffs[4][0] = [
        [1.054880, 1.075210, 1.068460, 1.153370, 1.069220],
        [1.000000, 1.062220, 1.013470, 1.088170, 1.046200],
        [0.885090, 0.993530, 0.942590, 1.054990, 1.012740],
        [0.920000, 0.950000, 0.978720, 1.020280, 0.984440],
        [0.850000, 0.908500, 0.839940, 0.985570, 0.962180],
        [0.800000, 0.800000, 0.810080, 0.950000, 0.961550],
        [1.038590, 1.063200, 1.034440, 1.112780, 1.037800]]

    coeffs[4][1] = [
        [1.017610, 1.028360, 1.058960, 1.133180, 1.045620],
        [0.920000, 0.998970, 1.033590, 1.089030, 1.022060],
        [0.912370, 0.949930, 0.979770, 1.020420, 0.981770],
        [0.847160, 0.935300, 0.930540, 0.955050, 0.946560],
        [0.880260, 0.867110, 0.874130, 0.972650, 0.883420],
        [0.627150, 0.627150, 0.700000, 0.774070, 0.845130],
        [0.973700, 1.006240, 1.026190, 1.071960, 1.017240]]

    coeffs[4][2] = [
        [1.028710, 1.017570, 1.025900, 1.081790, 1.024240],
        [0.924980, 0.985500, 1.014100, 1.092210, 0.999610],
        [0.828570, 0.934920, 0.994950, 1.024590, 0.949710],
        [0.900810, 0.901330, 0.928830, 0.979570, 0.913100],
        [0.761030, 0.845150, 0.805360, 0.936790, 0.853460],
        [0.626400, 0.546750, 0.730500, 0.850000, 0.689050],
        [0.957630, 0.985480, 0.991790, 1.050220, 0.987900]]

    coeffs[4][3] = [
        [0.992730, 0.993880, 1.017150, 1.059120, 1.017450],
        [0.975610, 0.987160, 1.026820, 1.075440, 1.007250],
        [0.871090, 0.933190, 0.974690, 0.979840, 0.952730],
        [0.828750, 0.868090, 0.834920, 0.905510, 0.871530],
        [0.781540, 0.782470, 0.767910, 0.764140, 0.795890],
        [0.743460, 0.693390, 0.514870, 0.630150, 0.715660],
        [0.934760, 0.957870, 0.959640, 0.972510, 0.981640]]

    coeffs[4][4] = [
        [0.965840, 0.941240, 0.987100, 1.022540, 1.011160],
        [0.988630, 0.994770, 0.976590, 0.950000, 1.034840],
        [0.958200, 1.018080, 0.974480, 0.920000, 0.989870],
        [0.811720, 0.869090, 0.812020, 0.850000, 0.821050],
        [0.682030, 0.679480, 0.632450, 0.746580, 0.738550],
        [0.668290, 0.445860, 0.500000, 0.678920, 0.696510],
        [0.926940, 0.953350, 0.959050, 0.876210, 0.991490]]

    coeffs[4][5] = [
        [0.948940, 0.997760, 0.850000, 0.826520, 0.998470],
        [1.017860, 0.970000, 0.850000, 0.700000, 0.988560],
        [1.000000, 0.950000, 0.850000, 0.606240, 0.947260],
        [1.000000, 0.746140, 0.751740, 0.598390, 0.725230],
        [0.922210, 0.500000, 0.376800, 0.517110, 0.548630],
        [0.500000, 0.450000, 0.429970, 0.404490, 0.539940],
        [0.960430, 0.881630, 0.775640, 0.596350, 0.937680]]

    coeffs[5][0] = [
        [1.030000, 1.040000, 1.000000, 1.000000, 1.049510],
        [1.050000, 0.990000, 0.990000, 0.950000, 0.996530],
        [1.050000, 0.990000, 0.990000, 0.820000, 0.971940],
        [1.050000, 0.790000, 0.880000, 0.820000, 0.951840],
        [1.000000, 0.530000, 0.440000, 0.710000, 0.928730],
        [0.540000, 0.470000, 0.500000, 0.550000, 0.773950],
        [1.038270, 0.920180, 0.910930, 0.821140, 1.034560]]

    coeffs[5][1] = [
        [1.041020, 0.997520, 0.961600, 1.000000, 1.035780],
        [0.948030, 0.980000, 0.900000, 0.950360, 0.977460],
        [0.950000, 0.977250, 0.869270, 0.800000, 0.951680],
        [0.951870, 0.850000, 0.748770, 0.700000, 0.883850],
        [0.900000, 0.823190, 0.727450, 0.600000, 0.839870],
        [0.850000, 0.805020, 0.692310, 0.500000, 0.788410],
        [1.010090, 0.895270, 0.773030, 0.816280, 1.011680]]

    coeffs[5][2] = [
        [1.022450, 1.004600, 0.983650, 1.000000, 1.032940],
        [0.943960, 0.999240, 0.983920, 0.905990, 0.978150],
        [0.936240, 0.946480, 0.850000, 0.850000, 0.930320],
        [0.816420, 0.885000, 0.644950, 0.817650, 0.865310],
        [0.742960, 0.765690, 0.561520, 0.700000, 0.827140],
        [0.643870, 0.596710, 0.474460, 0.600000, 0.651200],
        [0.971740, 0.940560, 0.714880, 0.864380, 1.001650]]

    coeffs[5][3] = [
        [0.995260, 0.977010, 1.000000, 1.000000, 1.035250],
        [0.939810, 0.975250, 0.939980, 0.950000, 0.982550],
        [0.876870, 0.879440, 0.850000, 0.900000, 0.917810],
        [0.873480, 0.873450, 0.751470, 0.850000, 0.863040],
        [0.761470, 0.702360, 0.638770, 0.750000, 0.783120],
        [0.734080, 0.650000, 0.600000, 0.650000, 0.715660],
        [0.942160, 0.919100, 0.770340, 0.731170, 0.995180]]

    coeffs[5][4] = [
        [0.952560, 0.916780, 0.920000, 0.900000, 1.005880],
        [0.928620, 0.994420, 0.900000, 0.900000, 0.983720],
        [0.913070, 0.850000, 0.850000, 0.800000, 0.924280],
        [0.868090, 0.807170, 0.823550, 0.600000, 0.844520],
        [0.769570, 0.719870, 0.650000, 0.550000, 0.733500],
        [0.580250, 0.650000, 0.600000, 0.500000, 0.628850],
        [0.904770, 0.852650, 0.708370, 0.493730, 0.949030]]

    coeffs[5][5] = [
        [0.911970, 0.800000, 0.800000, 0.800000, 0.956320],
        [0.912620, 0.682610, 0.750000, 0.700000, 0.950110],
        [0.653450, 0.659330, 0.700000, 0.600000, 0.856110],
        [0.648440, 0.600000, 0.641120, 0.500000, 0.695780],
        [0.570000, 0.550000, 0.598800, 0.400000, 0.560150],
        [0.475230, 0.500000, 0.518640, 0.339970, 0.520230],
        [0.743440, 0.592190, 0.603060, 0.316930, 0.794390]]

    return coeffs
