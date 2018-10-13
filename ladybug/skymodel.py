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
            air_mass = 1 / (math.sin(math.radians(alt)) +
                            (0.50572 * math.pow((6.07995 + alt), -1.6364)))
            dir_norm_rad.append(1415 * math.exp(-tb * math.pow(air_mass, ab)))
            dif_horiz_rad.append(1415 * math.exp(-td * math.pow(air_mass, ad)))
        else:
            dir_norm_rad.append(0)
            dif_horiz_rad.append(0)

    return dir_norm_rad, dif_horiz_rad


"""ZHANG-HUANG SOLAR MODEL"""
# TODO: Split golbal into direct and diffuse using Perez method.


def zhang_huang_solar_model(alt, cloud_cover, relative_humidity,
                            dry_bulb_present, dry_bulb_t3_hrs, wind_speed):
    """Calculate solar flux using the Zhang-Huang model.

    Args:
        alt = A solar altitudes in degrees.
        cloud_cover: A float value between 0 and 10 that represents the sky cloud cover
            in tenths (0 = clear; 10 = completely overcast)
        relative_humidity: A float value between 0 and 100 that represents
            the relative humidity in percent.
        dry_bulb_present: A float value that represents the dry bulb
            temperature at the time of interest (in degrees C).
        dry_bulb_t3_hrs: A float value that represents the dry bulb
            temperature at three hours before the time of interest (in degrees C).
        wind_speed: A float value that represents the wind speed in m/s.

    Returns:
        dir_ir: A direct normal radiation value in W/m2.
        diff_ir: A diffuse horizontall radiation value in W/m2.
    """
    # extraterrestrial solar constant (W/m2)
    IRR0 = 1355
    # zhang-huang solar model regression constants
    C0, C1, C2, C3, C4, C5, D_COEFF, K_COEFF = 0.5598, 0.4982, \
        -0.6762, 0.02842, -0.00317, 0.014, -17.853, 0.843

    # start assuming night time
    glob_ir = 0
    dir_ir = 0
    diff_ir = 0

    if alt > 0:
        # get sin of the altitude
        sin_alt = math.sin(math.radians(alt))

        # shortened and converted versions of the input parameters
        cc, rh, n_temp, n3_temp, w_spd = cloud_cover / 10.0, \
            relative_humidity, dry_bulb_present, dry_bulb_t3_hrs, wind_speed

        # calculate zhang-huang global radiation
        glob_ir = ((IRR0 * sin_alt *
                    (C0 + (C1 * cc) + (C2 * cc**2) +
                     (C3 * (n_temp - n3_temp)) +
                     (C4 * rh) + (C5 * w_spd))) + D_COEFF) / K_COEFF
        if glob_ir < 0:
            glob_ir = 0
        else:
            # calculate direct and diffuse solar
            k_t = glob_ir / (IRR0 * sin_alt)
            k_tc = 0.4268 + (0.1934 * sin_alt)
            if k_t >= k_tc:
                k_ds = k_t - ((1.107 + (0.03569 * sin_alt) +
                               (1.681 * sin_alt**2)) * (1 - k_t)**2)
            else:
                k_ds = (3.996 - (3.862 * sin_alt) +
                        (1.540 * sin_alt**2)) * k_t**3
            diff_ir = (IRR0 * sin_alt * (k_t - k_ds)) / (1 - k_ds)
            dir_horiz_ir = (IRR0 * sin_alt * k_ds * (1 - k_t)) / (1 - k_ds)
            dir_ir = dir_horiz_ir / math.sin(math.radians(alt))

    return dir_ir, diff_ir


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
