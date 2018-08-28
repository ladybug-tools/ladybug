import math


def ashrae_revised_clear_sky(altitudes, tb, td):
    """Calculate solar flux for an ASHRAE Revised Clear Sky ("Tau Model")

    Args:
        altitudes = A list of solar altitudes in degrees
        tb: A value indicating the beam optical depth of the sky.
        td: A value indicating the diffuse optical depth of the sky.

    Returns:
        dir_norm_rad: A list of direct normal radiation values for each
            of the connected altitudes
        dif_horiz_rad: A list of diffuse horizontall radiation values for each
            of the connected altitudes
    """
    dir_norm_rad = []
    dif_horiz_rad = []

    ab = 1.219 - (0.043 * tb) - (0.151 * td) - (0.204 * tb * td)
    ad = 0.202 + (0.852 * tb) - (0.007 * td) - (0.357 * tb * td)
    for alt in altitudes:
        # calculate hourly air mass between top of the atmosphere and earth
        air_mass = 0
        if alt > 0:
            air_mass = 1 / (math.sin(math.radians(alt)) +
                            (0.50572 * math.pow((6.07995 + alt), -1.6364)))
            dir_norm_rad.append(1415 * math.exp(-tb * math.pow(air_mass, ab)))
            dif_horiz_rad.append(1415 * math.exp(-td * math.pow(air_mass, ad)))
        else:
            dir_norm_rad.append(0)
            dif_horiz_rad.append(0)

    return dir_norm_rad, dif_horiz_rad


# apparent solar irradiation at air mass m = 0
monthly_a = [1202, 1187, 1164, 1130, 1106, 1092, 1093, 1107, 1136,
             1166, 1190, 1204]
# atmospheric extinction coefficient
monthly_b = [0.141, 0.142, 0.149, 0.164, 0.177, 0.185, 0.186, 0.182,
             0.165, 0.152, 0.144, 0.141]


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
            of the connected altitudes
        dif_horiz_rad: A list of diffuse horizontall radiation values for each
            of the connected altitudes
    """
    dir_norm_rad = []
    dif_horiz_rad = []
    for i, alt in enumerate(altitudes):
        if alt > 0:
            try:
                dir_norm = monthly_a[month - 1] / (math.exp(
                    monthly_b[month - 1] / (math.sin(math.radians(alt)))))
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


def global_horizontal(altitudes, dir_norm_rad, dif_horiz_rad):
    """Calculate solar flux for an ASHRAE Revised Clear Sky ("Tau Model")

    Args:
        altitudes = A list of solar altitudes in degrees.
        dir_norm_rad: A list of direct normal radiation fluxes.
        dif_horiz_rad: A list of diffuse horizontal radiation fluxes.

    Returns:
        glob_horiz_rad: A list of global horizontall radiation values for each
            of the connected altitudes
    """
    return [dhr + dnr * math.sin(math.radians(alt)) for
            alt, dnr, dhr in zip(altitudes, dir_norm_rad, dif_horiz_rad)]
