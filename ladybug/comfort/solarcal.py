# coding=utf-8
"""Functions for adjusting MRT for radiative sky exchange (including shortwave solar).

The solarcal formulas of this module are taken from the following publications:

[1] Arens, E., T. Hoyt, X. Zhou, L. Huang, H. Zhang and S. Schiavon. 2015.
Modeling the comfort effects of short-wave solar radiation indoors.
Building and Environment, 88, 3-9. http://dx.doi.org/10.1016/j.buildenv.2014.09.004
https://escholarship.org/uc/item/89m1h2dg

[2] ASHRAE Standard 55 (2017). "Thermal Environmental Conditions for Human Occupancy".
"""
from __future__ import division

from ..skymodel import sky_temperature
from .__init__ import SOLARCALSPLINES

import math


def outdoor_sky_heat_exch(srfs_temp, horiz_ir, diff_horiz_solar, dir_normal_solar,
                          solar_altitude, solar_azimuth,
                          sky_view=1, fract_exposed=1, floor_reflectance=0.25,
                          posture='standing', body_azimuth=None,
                          body_absortivity=0.7, body_emissivity=0.95):
    """Perform a full outdoor sky radiant heat exchange.

    Args:
        srfs_temp: The temperature of surfaces around the person in degrees
            Celcius. This includes the ground and any other surfaces
            blocking the view to the sky. Typically, the dry bulb temperature
            is used when such surface temperatures are unknown.
        horiz_ir: The horizontal infrared radiation intensity from the sky in W/m2.
        diff_horiz_solar: Diffuse horizontal solar irradiance in W/m2.
        dir_normal_solar: Direct normal solar irradiance in W/m2.
        solar_altitude: The altitude of the sun in degrees [0-90].
        solar_azimuth: The azimuth of the sun in degrees [0-360].
        sky_view: A number between 0 and 1 representing the fraction of the
            sky vault in occupant’s view. Default is 1 for outdoors in an
            open field.
        fract_exposed: A number between 0 and 1 representing the fraction of
            the body exposed to direct sunlight. Note that this does not include the
            body’s self-shading; only the shading from surroundings.
            Default is 1 for a person standing in an open area.
        floor_reflectance: A number between 0 and 1 the represents the
            reflectance of the floor. Default is for 0.25 which is characteristic
            of outdoor grass or dry bare soil.
        posture: A text string indicating the posture of the body. Letters must
            be lowercase.  Choose from the following: "standing", "seated", "supine".
            Default is "standing".
        body_azimuth: A number between 0 and 360 representing the direction that
            the human is facing in degrees (0=North, 90=East, 180=South, 270=West).
            Default is None, which will assume that the person is always facing 135
            degrees from the sun, meaning that the person faces their side or
            back to the sun at all times in order to avoid glare.
        body_absortivity: A number between 0 and 1 representing the average
            shortwave absorptivity of the body (including clothing and skin color).
            Typical clothing values - white: 0.2, khaki: 0.57, black: 0.88
            Typical skin values - white: 0.57, brown: 0.65, black: 0.84
            Default is 0.7 for average (brown) skin and medium clothing.
        body_emissivity: A number between 0 and 1 representing the average
            longwave emissivity of the body.  Default is 0.95, which is almost
            always the case except in rare situations of wearing metalic clothing.

    Returns:
        heat_exch_result: A dictionary containing results with the following keys:
            s_erf : The shortwave effective radiant field (ERF) in W/m2.
            s_dmrt : The MRT delta as a result of shortwave irradinace in C.
            l_erf : The longwave effective radiant field (ERF) in W/m2.
            l_dmrt : The MRT delta as a result of longwave sky exchange in C.
            mrt: The final MRT expereinced as a result of sky heat excahnge in C.
    """
    # set defaults using the input parameters
    fract_efficiency = 0.696 if posture == 'seated' else 0.725
    if body_azimuth is not None:
        sharp = sharp_from_solar_and_body_azimuth(solar_azimuth, body_azimuth)
    else:
        sharp = 135

    # calculate the influence of shorwave irradiance
    if solar_altitude > 0:
        s_flux = body_solar_flux_from_parts(diff_horiz_solar, dir_normal_solar,
                                            solar_altitude, sharp, sky_view,
                                            fract_exposed, floor_reflectance, posture)
        short_erf = erf_from_body_solar_flux(s_flux, body_absortivity, body_emissivity)
        short_mrt_delta = mrt_delta_from_erf(short_erf, fract_efficiency)
    else:
        short_erf = 0
        short_mrt_delta = 0

    # calculate the influence of longwave heat exchange with the sky
    long_mrt_delta = longwave_mrt_delta_from_horiz_ir(horiz_ir, srfs_temp,
                                                      sky_view, body_emissivity)
    long_erf = erf_from_mrt_delta(long_mrt_delta, fract_efficiency)

    # calculate final MRT as a result of both longwave and shortwave heat exchange
    sky_adjusted_mrt = srfs_temp + short_mrt_delta + long_mrt_delta
    heat_exch_result = {
        's_erf': short_erf,
        's_dmrt': short_mrt_delta,
        'l_erf': long_erf,
        'l_dmrt': long_mrt_delta,
        'mrt': sky_adjusted_mrt
    }
    return heat_exch_result


def indoor_sky_heat_exch(longwave_mrt, diff_horiz_solar, dir_normal_solar,
                         solar_altitude, solar_azimuth,
                         sky_view=1, fract_exposed=1, floor_reflectance=0.25,
                         posture='seated', body_azimuth=None,
                         body_absortivity=0.7, body_emissivity=0.95):
    """Perform a full indoor sky radiant heat exchange.

    Args:
        longwave_mrt: The longwave mean radiant temperature (MRT) expereinced
            as a result of indoor surface temperatures in C.
        diff_horiz_solar: Diffuse horizontal solar irradiance in W/m2.
        dir_normal_solar: Direct normal solar irradiance in W/m2.
        solar_altitude: The altitude of the sun in degrees [0-90].
        solar_azimuth: The azimuth of the sun in degrees [0-360].
        sky_view: A number between 0 and 1 representing the fraction of the
            sky vault in occupant’s view. Default is 1 for outdoors in an
            open field.
        fract_exposed: A number between 0 and 1 representing the fraction of
            the body exposed to direct sunlight. Note that this does not include the
            body’s self-shading; only the shading from surroundings.
            Default is 1 for a person standing in an open area.
        floor_reflectance: A number between 0 and 1 the represents the
            reflectance of the floor. Default is for 0.25 which is characteristic
            of outdoor grass or dry bare soil.
        posture: A text string indicating the posture of the body. Letters must
            be lowercase.  Choose from the following: "standing", "seated", "supine".
            Default is "standing".
        body_azimuth: A number between 0 and 360 representing the direction that
            the human is facing in degrees (0=North, 90=East, 180=South, 270=West).
            Default is None, which will assume that the person is always facing 135
            degrees from the sun, meaning that the person faces their side or
            back to the sun at all times in order to avoid glare.
        body_absortivity: A number between 0 and 1 representing the average
            shortwave absorptivity of the body (including clothing and skin color).
            Typical clothing values - white: 0.2, khaki: 0.57, black: 0.88
            Typical skin values - white: 0.57, brown: 0.65, black: 0.84
            Default is 0.7 for average (brown) skin and medium clothing.
        body_emissivity: A number between 0 and 1 representing the average
            longwave emissivity of the body.  Default is 0.95, which is almost
            always the case except in rare situations of wearing metalic clothing.

    Returns:
        heat_exch_result: A dictionary containing results with the following keys:
            erf : The shortwave effective radiant field (ERF) in W/m2.
            dmrt : The MRT delta as a result of shortwave irradinace in C.
            mrt: The final MRT expereinced as a result of sky heat excahnge in C.
    """
    # set defaults using the input parameters
    fract_efficiency = 0.696 if posture == 'seated' else 0.725
    if body_azimuth is not None:
        sharp = sharp_from_solar_and_body_azimuth(solar_azimuth, body_azimuth)
    else:
        sharp = 135

    # calculate the influence of shorwave irradiance
    if solar_altitude > 0:
        s_flux = body_solar_flux_from_parts(diff_horiz_solar, dir_normal_solar,
                                            solar_altitude, sharp, sky_view,
                                            fract_exposed, floor_reflectance, posture)
        short_erf = erf_from_body_solar_flux(s_flux, body_absortivity, body_emissivity)
        short_mrt_delta = mrt_delta_from_erf(short_erf, fract_efficiency)
    else:
        short_erf = 0
        short_mrt_delta = 0

    # calculate final MRT
    sky_adjusted_mrt = longwave_mrt + short_mrt_delta
    heat_exch_result = {
        'erf': short_erf,
        'dmrt': short_mrt_delta,
        'mrt': sky_adjusted_mrt
    }
    return heat_exch_result


def shortwave_from_horiz_solar(longwave_mrt, diff_horiz_solar, dir_horiz_solar,
                               solar_altitude, solar_azimuth,
                               fract_exposed=1, floor_reflectance=0.25,
                               posture='standing', body_azimuth=None,
                               body_absortivity=0.7, body_emissivity=0.95):
    """Perform a shortwave radiant heat exchange using horizontal solar components.

    This is useful when building a map of MRT using the direct and diffuse
    results of a Radiance study instead of the solar components directly from
    an EPW or Wea file.  Note that all input radiation components should already
    account for the amount of sky seen and solar heat reflections off of surfaces.

    Args:
        longwave_mrt: The longwave mean radiant temperature (MRT) expereinced
            as a result of indoor surface temperatures in C.
        horiz_ir: The horizontal infrared radiation intensity from the sky in W/m2.
        diff_horiz_solar: Diffuse horizontal solar irradiance in W/m2.
        dir_horiz_solar: Direct horizontal solar irradiance in W/m2.
        solar_altitude: The altitude of the sun in degrees [0-90].
        solar_azimuth: The azimuth of the sun in degrees [0-360].
        sky_view: A number between 0 and 1 representing the fraction of the
            sky vault in occupant’s view. Default is 1 for outdoors in an
            open field.
        fract_exposed: A number between 0 and 1 representing the fraction of
            the body exposed to direct sunlight. Note that this does not include the
            body’s self-shading; only the shading from surroundings.
            Default is 1 for a person standing in an open area.
        floor_reflectance: A number between 0 and 1 the represents the
            reflectance of the floor. Default is for 0.25 which is characteristic
            of outdoor grass or dry bare soil.
        posture: A text string indicating the posture of the body. Letters must
            be lowercase.  Choose from the following: "standing", "seated", "supine".
            Default is "standing".
        body_azimuth: A number between 0 and 360 representing the direction that
            the human is facing in degrees (0=North, 90=East, 180=South, 270=West).
            Default is None, which will assume that the person is always facing 135
            degrees from the sun, meaning that the person faces their side or
            back to the sun at all times in order to avoid glare.
        body_absortivity: A number between 0 and 1 representing the average
            shortwave absorptivity of the body (including clothing and skin color).
            Typical clothing values - white: 0.2, khaki: 0.57, black: 0.88
            Typical skin values - white: 0.57, brown: 0.65, black: 0.84
            Default is 0.7 for average (brown) skin and medium clothing.
        body_emissivity: A number between 0 and 1 representing the average
            longwave emissivity of the body.  Default is 0.95, which is almost
            always the case except in rare situations of wearing metalic clothing.

    Returns:
        heat_exch_result: A dictionary containing results with the following keys:
            erf : The shortwave effective radiant field (ERF) in W/m2.
            dmrt : The MRT delta as a result of shortwave irradinace in C.
            mrt: The final MRT expereinced as a result of sky heat excahnge in C.
    """
    # set defaults using the input parameters
    fract_efficiency = 0.696 if posture == 'seated' else 0.725
    if body_azimuth is not None:
        sharp = sharp_from_solar_and_body_azimuth(solar_azimuth, body_azimuth)
    else:
        sharp = 135

    # calculate the influence of shorwave irradiance
    if solar_altitude > 0:
        s_flux = body_solar_flux_from_horiz_parts(diff_horiz_solar, dir_horiz_solar,
                                                  solar_altitude, sharp, fract_exposed,
                                                  floor_reflectance, posture)
        short_erf = erf_from_body_solar_flux(s_flux, body_absortivity, body_emissivity)
        short_mrt_delta = mrt_delta_from_erf(short_erf, fract_efficiency)
    else:
        short_erf = 0
        short_mrt_delta = 0

    # calculate final MRT as a result of both longwave and shortwave heat exchange
    sky_adjusted_mrt = longwave_mrt + short_mrt_delta
    heat_exch_result = {
        'erf': short_erf,
        'dmrt': short_mrt_delta,
        'mrt': sky_adjusted_mrt
    }
    return heat_exch_result


def mrt_delta_from_erf(erf, fract_efficiency=0.725, rad_trans_coeff=6.012):
    """Calculate the mean radiant temperature (MRT) delta as a result of an ERF.

    Args:
        erf: A number representing the effective radiant field (ERF) on the
            person in W/m2.
        fract_efficiency: A number representing the fraction of the body
            surface exposed to radiation from the environment. This is typically
            either 0.725 for a standing or supine person or 0.696 for a seated
            person. Default is 0.725 for a standing person.
        rad_trans_coeff: A number representing the radiant heat transfer coefficient
            in (W/m2-K).  Default is 6.012, which is almost always the case.
    """
    return erf / (fract_efficiency * rad_trans_coeff)


def erf_from_mrt_delta(mrt_delta, fract_efficiency=0.725, rad_trans_coeff=6.012):
    """Calculate the effective radiant field (ERF) from a MRT delta.

    Args:
        mrt_delta: A mean radiant temperature (MRT) delta in Kelvin or degrees Celcius.
        fract_efficiency: A number representing the fraction of the body
            surface exposed to radiation from the environment. This is typically
            either 0.725 for a standing or supine person or 0.696 for a seated
            person. Default is 0.725 for a standing person.
        rad_trans_coeff: A number representing the radiant heat transfer coefficient
            in (W/m2-K).  Default is 6.012, which is almost always the case.
    """
    return mrt_delta * fract_efficiency * rad_trans_coeff


def longwave_mrt_delta_from_horiz_ir(horiz_ir, srfs_temp, sky_view=1,
                                     body_emissivity=0.95):
    """Calculate the MRT delta as a result of longwave radiant exchange with the sky.

    Note that this value is typically negative since the earth (and humans)
    tend to radiate heat out to space in the longwave portion of the spectrum.

    Args:
        horiz_ir: A float value that represents the downwelling horizontal
            infrared radiation intensity in W/m2.
        srfs_temp: The temperature of surfaces around the person in degrees
            Celcius. This includes the ground and any other surfaces
            blocking the view to the sky. Typically, the dry bulb temperature
            is used when such surface temperatures are unknown.
        sky_view: A number between 0 and 1 representing the fraction of the
            sky vault in occupant’s view. Default is 1 for outdoors in an
            open field.
    """
    sky_temp = sky_temperature(horiz_ir, body_emissivity)
    return longwave_mrt_delta_from_sky_temp(sky_temp, srfs_temp, sky_view)


def longwave_mrt_delta_from_sky_temp(sky_temp, srfs_temp, sky_view=1):
    """Calculate the MRT delta as a result of longwave radiant exchange with the sky.

    Note that this value is typically negative since the earth (and humans)
    tend to radiate heat out to space in the longwave portion of the spectrum.

    Args:
        sky_temp: The sky temperature in degrees Celcius.
        srfs_temp: The temperature of surfaces around the person in degrees
            Celcius. This includes the ground and any other surfaces
            blocking the view to the sky. Typically, the dry bulb temperature
            is used when such surface temperatures are unknown.
        sky_view: A number between 0 and 1 representing the fraction of the
            sky vault in occupant’s view. Default is 1 for outdoors in an
            open field.
    """
    return 0.5 * sky_view * (sky_temp - srfs_temp)


def erf_from_body_solar_flux(solar_flux, body_absortivity=0.7, body_emissivity=0.95):
    """Calculate effective radiant field (ERF) from incident solar flux on body in W/m2.

    Args:
        solar_flux: A number for the average solar flux over the human body in W/m2.
        body_absortivity: A number between 0 and 1 representing the average
            shortwave absorptivity of the body (including clothing and skin color).
            Typical clothing values - white: 0.2, khaki: 0.57, black: 0.88
            Typical skin values - white: 0.57, brown: 0.65, black: 0.84
            Default is 0.7 for average (brown) skin and medium clothing.
        body_emissivity: A number between 0 and 1 representing the average
            longwave emissivity of the body.  Default is 0.95, which is almost
            always the case except in rare situations of wearing metalic clothing.
    """
    return solar_flux * (body_absortivity / body_emissivity)


def body_solar_flux_from_parts(diff_horiz_solar, dir_normal_solar, altitude,
                               sharp=135, sky_view=1, fract_exposed=1,
                               floor_reflectance=0.25, posture='standing'):
    """Estimate the total solar flux on human geometry from solar components.

    Args:
        diff_horiz_solar: Diffuse horizontal solar irradiance in W/m2.
        dir_normal_solar: Direct normal solar irradiance in W/m2.
        solar_altitude: The altitude of the sun in degrees [0-90].
        sharp: A number between 0 and 180 representing the solar horizontal
            angle relative to front of person (SHARP). 0 signifies sun that is
            shining directly into the person's face and 180 signifies sun that
            is shining at the person's back. Default is 135, asuming that a person
            typically faces their side or back to the sun to avoid glare.
        sky_view: A number between 0 and 1 representing the fraction of the
            sky vault in occupant’s view. Default is 1 for outdoors in an
            open field.
        fract_exposed: A number between 0 and 1 representing the fraction of
            the body exposed to direct sunlight. Note that this does not include the
            body’s self-shading; only the shading from surroundings.
            Default is 1 for a person standing in an open area.
        floor_reflectance: A number between 0 and 1 the represents the
            reflectance of the floor. Default is for 0.25 which is characteristic
            of outdoor grass or dry bare soil.
        posture: A text string indicating the posture of the body. Letters must
            be lowercase.  Choose from the following: "standing", "seated", "supine".
            Default is "standing".
    """
    fract_eff = 0.696 if posture == 'seated' else 0.725
    glob_horiz = diff_horiz_solar + (dir_normal_solar * math.sin(math.radians(altitude)))

    dir_solar = body_dir_from_dir_normal(dir_normal_solar, altitude, sharp,
                                         posture, fract_exposed)
    diff_solar = body_diff_from_diff_horiz(diff_horiz_solar, sky_view, fract_eff)
    ref_solar = body_ref_from_glob_horiz(glob_horiz, floor_reflectance,
                                         sky_view, fract_eff)
    return dir_solar + diff_solar + ref_solar


def body_solar_flux_from_horiz_parts(diff_horiz_solar, dir_horiz_solar, altitude,
                                     sharp=135, fract_exposed=1,
                                     floor_reflectance=0.25, posture='standing'):
    """Estimate total solar flux on human geometry from horizontal solar components.

    This method is useful for cases when one wants to take the hourly results
    of a spatial radiation study with Radiance and use them to build a map
    of ERF or MRT delta on a person.

    Args:
        diff_horiz_solar: Diffuse horizontal solar irradiance in W/m2.
        dir_horiz_solar: Direct horizontal solar irradiance in W/m2.
        solar_altitude: The altitude of the sun in degrees [0-90].
        sharp: A number between 0 and 180 representing the solar horizontal
            angle relative to front of person (SHARP). 0 signifies sun that is
            shining directly into the person's face and 180 signifies sun that
            is shining at the person's back. Default is 135, asuming that a person
            typically faces their side or back to the sun to avoid glare.
        fract_exposed: A number between 0 and 1 representing the fraction of
            the body exposed to direct sunlight. Note that this does not include the
            body’s self-shading; only the shading from surroundings.
            Default is 1 for a person standing in an open area.
        floor_reflectance: A number between 0 and 1 the represents the
            reflectance of the floor. Default is for 0.25 which is characteristic
            of outdoor grass or dry bare soil.
        posture: A text string indicating the posture of the body. Letters must
            be lowercase.  Choose from the following: "standing", "seated", "supine".
            Default is "standing".
    """
    fract_eff = 0.696 if posture == 'seated' else 0.725
    glob_horiz = diff_horiz_solar + dir_horiz_solar

    dir_solar = body_dir_from_dir_horiz(dir_horiz_solar, altitude, sharp,
                                        posture, fract_exposed)
    diff_solar = body_diff_from_diff_horiz(diff_horiz_solar, 1, fract_eff)
    ref_solar = body_ref_from_glob_horiz(glob_horiz, floor_reflectance, 1, fract_eff)
    return dir_solar + diff_solar + ref_solar


def body_diff_from_diff_horiz(diff_horiz_solar, sky_view=1, fract_efficiency=0.725):
    """Estimate the diffuse solar flux on human geometry from diffuse horizontal solar.

    Args:
        diff_horiz_solar: Diffuse horizontal solar irradiance in W/m2.
        sky_view: A number between 0 and 1 representing the fraction of the
            sky vault in occupant’s view. Default is 1 for outdoors in an
            open field.
        fract_efficiency: A number representing the fraction of the body
            surface exposed to radiation from the environment. This is typically
            either 0.725 for a standing or supine person or 0.696 for a seated
            person. Default is 0.725 for a standing person.
    """
    return 0.5 * sky_view * fract_efficiency * diff_horiz_solar


def body_ref_from_glob_horiz(glob_horiz_solar, floor_reflectance=0.25,
                             sky_view=1, fract_efficiency=0.725):
    """Estimate floor-reflected solar flux on human geometry from global horizontal solar.

    Args:
        glob_horiz_solar: Global horizontal solar irradiance in W/m2.
        floor_reflectance: A number between 0 and 1 the represents the
            reflectance of the floor. Default is for 0.25 which is characteristic
            of outdoor grass or dry bare soil.
        sky_view: A number between 0 and 1 representing the fraction of the
            sky vault in occupant’s view. Default is 1 for outdoors in an
            open field.
        fract_efficiency: A number representing the fraction of the body
            surface exposed to radiation from the environment. This is typically
            either 0.725 for a standing or supine person or 0.696 for a seated
            person. Default is 0.725 for a standing person.
    """
    return 0.5 * sky_view * fract_efficiency * glob_horiz_solar * floor_reflectance


def body_dir_from_dir_horiz(dir_horiz_solar, altitude, sharp=135,
                            posture='standing', fract_exposed=1):
    """Estimate the direct solar flux on human geometry from direct horizontal solar.

    Args:
        dir_horiz_solar: Direct horizontal solar irradiance in W/m2.
        altitude: A number between 0 and 90 representing the altitude of the
            sun in degrees.
        sharp: A number between 0 and 180 representing the solar horizontal
            angle relative to front of person (SHARP). 0 signifies sun that is
            shining directly into the person's face and 180 signifies sun that
            is shining at the person's back. Default is 135, asuming that a person
            typically faces their side or back to the sun to avoid glare.
        posture: A text string indicating the posture of the body. Letters must
            be lowercase.  Choose from the following: "standing", "seated", "supine".
            Default is "standing".
        fract_exposed: A number between 0 and 1 representing the fraction of
            the body exposed to direct sunlight. Note that this does not include
            the body’s self-shading; only the shading from surroundings.
            Default is 1 for a person in an open area.
    """
    try:
        proj_fac = get_projection_factor(altitude, sharp, posture)
    except KeyError:
        proj_fac = get_projection_factor_simple(altitude, sharp, posture)
    dir_normal_solar = dir_horiz_solar / math.sin(math.radians(altitude))
    return proj_fac * fract_exposed * dir_normal_solar


def body_dir_from_dir_normal(dir_normal_solar, altitude, sharp=135,
                             posture='standing', fract_exposed=1):
    """Estimate the direct solar flux on human geometry from direct horizontal solar.

    Args:
        dir_normal_solar: Direct normal solar irradiance in W/m2.
        altitude: A number between 0 and 90 representing the altitude of the
            sun in degrees.
        sharp: A number between 0 and 180 representing the solar horizontal
            angle relative to front of person (SHARP). 0 signifies sun that is
            shining directly into the person's face and 180 signifies sun that
            is shining at the person's back. Default is 135, asuming that a person
            typically faces their side or back to the sun to avoid glare.
        posture: A text string indicating the posture of the body. Letters must
            be lowercase.  Choose from the following: "standing", "seated", "supine".
            Default is "standing".
        fract_exposed: A number between 0 and 1 representing the fraction of
            the body exposed to direct sunlight. Note that this does not include
            the body’s self-shading; only the shading from surroundings.
            Default is 1 for a person in an open area.
    """
    try:
        proj_fac = get_projection_factor(altitude, sharp, posture)
    except KeyError:
        proj_fac = get_projection_factor_simple(altitude, sharp, posture)
    return proj_fac * fract_exposed * dir_normal_solar


def sharp_from_solar_and_body_azimuth(solar_azimuth, body_azimuth=0):
    """Calculate solar horizontal angle relative to front of person (SHARP).

    Args:
        solar_azimuth: A number between 0 and 360 representing the solar azimuth
            in degrees (0=North, 90=East, 180=South, 270=West).
        body_azimuth: A number between 0 and 360 representing the direction that
            the human is facing in degrees (0=North, 90=East, 180=South, 270=West).
    """
    angle_diff = abs(solar_azimuth - body_azimuth)
    if angle_diff <= 180:
        return angle_diff
    else:
        return angle_diff - 180


def get_projection_factor(altitude, sharp=135, posture='standing'):
    """Get the fraction of body surface area exposed to direct sun from solar position.

    This is effectively Ap / Ad in the original Solarcal equations.

    Args:
        altitude: A number between 0 and 90 representing the altitude of the
            sun in degrees.
        sharp: A number between 0 and 180 representing the solar horizontal
            angle relative to front of person (SHARP). 0 signifies sun that is
            shining directly into the person's face and 180 signifies sun that
            is shining at the person's back. Default is 135, asuming that a person
            typically faces their side or back to the sun to avoid glare.
        posture: A text string indicating the posture of the body. Letters must
            be lowercase.  Choose from the following: "standing", "seated", "supine".
            Default is "standing".
    """
    if posture == 'supine':
        altitude, sharp = transpose_altitude_azimuth(altitude, sharp)
        altitude = 1 if altitude == 0 else altitude
        posture = 'standing'
    return SOLARCALSPLINES[posture][int(sharp)][math.ceil(altitude) - 1]


def get_projection_factor_simple(altitude, sharp=135, posture='standing'):
    """Get the fraction of body surface area exposed to direct sun using a simpler method.

    This is effectively Ap / Ad in the original Solarcal equations.

    This is a more portable version of the get_projection_area() function
    since it does not rely on the large matrix of projection factors
    stored externally in csv files. However, it is less precise since it
    effectively interpolates over the missing parts of the matrix. So this is
    only recommended for cases where such csv files are missing.

    Args:
        altitude: A number between 0 and 90 representing the altitude of the
            sun in degrees.
        sharp: A number between 0 and 180 representing the solar horizontal
            angle relative to front of person (SHARP). Default is 135, asuming
            a person typically faces their side or back to the sun to avoid glare.
        posture: A text string indicating the posture of the body. Letters must
            be lowercase.  Choose from the following: "standing", "seated", "supine".
            Default is "standing".
    """
    if posture == 'supine':
        altitude, sharp = transpose_altitude_azimuth(altitude, sharp)
        posture = 'standing'

    if posture == 'standing':
        ap_table = ((0.254, 0.254, 0.228, 0.187, 0.149, 0.104, 0.059),
                    (0.248, 0.248, 0.225, 0.183, 0.145, 0.102, 0.059),
                    (0.239, 0.239, 0.218, 0.177, 0.138, 0.096, 0.059),
                    (0.225, 0.225, 0.199, 0.165, 0.127, 0.09, 0.059),
                    (0.205, 0.205, 0.182, 0.151, 0.116, 0.083, 0.059),
                    (0.183, 0.183, 0.165, 0.136, 0.109, 0.078, 0.059),
                    (0.167, 0.167, 0.155, 0.131, 0.107, 0.078, 0.059),
                    (0.175, 0.175, 0.161, 0.131, 0.111, 0.081, 0.059),
                    (0.199, 0.199, 0.178, 0.147, 0.12, 0.084, 0.059),
                    (0.22, 0.22, 0.196, 0.16, 0.126, 0.088, 0.059),
                    (0.238, 0.238, 0.21, 0.17, 0.133, 0.091, 0.059),
                    (0.249, 0.249, 0.22, 0.177, 0.138, 0.093, 0.059),
                    (0.252, 0.252, 0.223, 0.178, 0.138, 0.093, 0.059))
    elif posture == 'seated':
        ap_table = ((0.202, 0.226, 0.212, 0.211, 0.182, 0.156, 0.123),
                    (0.203, 0.228, 0.205, 0.2, 0.187, 0.158, 0.123),
                    (0.2, 0.231, 0.207, 0.202, 0.184, 0.155, 0.123),
                    (0.191, 0.227, 0.205, 0.201, 0.175, 0.149, 0.123),
                    (0.177, 0.214, 0.195, 0.192, 0.168, 0.141, 0.123),
                    (0.16, 0.196, 0.182, 0.181, 0.162, 0.134, 0.123),
                    (0.15, 0.181, 0.173, 0.17, 0.153, 0.129, 0.123),
                    (0.163, 0.18, 0.164, 0.158, 0.145, 0.125, 0.123),
                    (0.182, 0.181, 0.156, 0.145, 0.136, 0.122, 0.123),
                    (0.195, 0.181, 0.146, 0.134, 0.128, 0.118, 0.123),
                    (0.207, 0.178, 0.135, 0.121, 0.117, 0.117, 0.123),
                    (0.213, 0.174, 0.125, 0.109, 0.109, 0.116, 0.123),
                    (0.209, 0.167, 0.117, 0.106, 0.106, 0.114, 0.123))
    else:
        raise TypeError('Posture type {} is not recognized.'.format(posture))

    def _find_span(arr, x):
        # For orderd array arr, find the left index of the closest interval x falls in.
        for i in range(len(arr) - 1):
            if x <= arr[i+1] and x >= arr[i]:
                return i
        return -1

    alt_range = (0, 15, 30, 45, 60, 75, 90)
    az_range = (0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 180)
    alt_i = _find_span(alt_range, altitude)
    az_i = _find_span(az_range, sharp)

    ap11 = ap_table[az_i][alt_i]
    ap12 = ap_table[az_i][alt_i + 1]
    ap21 = ap_table[az_i + 1][alt_i]
    ap22 = ap_table[az_i + 1][alt_i + 1]

    az1 = az_range[az_i]
    az2 = az_range[az_i+1]
    alt1 = alt_range[alt_i]
    alt2 = alt_range[alt_i+1]

    # bilinear interpolation
    ap = ap11 * (az2 - sharp) * (alt2 - altitude)
    ap += ap21 * (sharp - az1) * (alt2 - altitude)
    ap += ap12 * (az2 - sharp) * (altitude - alt1)
    ap += ap22 * (sharp - az1) * (altitude - alt1)
    ap /= (az2 - az1) * (alt2 - alt1)

    return ap


def transpose_altitude_azimuth(altitude, azimuth):
    """Transpose altitude and azimuth.

    This is necessary for getting correct projection factors for a supine posture
    from the standing posture matrix.
    """
    alt_temp = altitude
    altitude = abs(90 - azimuth)
    azimuth = alt_temp
    return altitude, azimuth
