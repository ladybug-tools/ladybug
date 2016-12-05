"""A list of useful functions for psychrometrics"""

import math


def findSaturatedVaporPressureTorr(T):
    """
    Calculates Saturated Vapor Pressure (Torr) at Temperature T (C)
    Used frequently throughtout the pmv comfort functions.
    """
    return math.exp(18.6686 - 4030.183 / (T + 235.0))


def findSaturatedVaporPressureHighAccuracy(tKelvin):
    """
    Calculates Saturated Vapor Pressure (Pa) at Temperature tKelvin (K)
    to a high accuracy.  The function accounts for the different behaviour of above
    and below the freezing point of water.
    """

    if tKelvin >= 273:
        # Calculate saturation vapor pressure above freezing
        sigma = 1 - (tKelvin / 647.096)
        expressResult = (sigma * (-7.85951783)) + ((sigma**1.5) * 1.84408259) + ((sigma**3) * (-11.7866487)) + ((sigma**3.5) * 22.6807411) + ((sigma**4) * (-15.9618719)) + ((sigma**7.5) * 1.80122502)
        critTemp = 647.096 / tKelvin
        exponent = critTemp * expressResult
        power = math.exp(exponent)
        saturationPressure = power * 22064000
    else:
        # Calculate saturation vapor pressure below freezing
        theta = tKelvin / 273.16
        exponent2 = ((1 - (theta**(-1.5))) * (-13.928169)) + ((1 - (theta**(-1.25))) * 34.707823)
        power = math.exp(exponent2)
        saturationPressure = power * 611.657

    return saturationPressure


def findHumidRatio(airTemp, relHumid, barPress=101325):
    """
    Calculates Humidity Ratio (kg water/kg air), Partial Pressure (Pa), and
    saturationPressure (Pa) at a given
    at Temperature airTemp (C), Relative Humidity relHumid (%),
    and Barometric Pressure barPress (Pa).
    """
    # Find saturation pressure
    tKelvin = airTemp + 273
    saturationPressure = findSaturatedVaporPressureHighAccuracy(tKelvin)
    # Calculate partial pressure
    decRH = relHumid * 0.01
    partialPressure = decRH * saturationPressure
    # Calculate humidity ratio
    pressDiffer = barPress - partialPressure
    constant = partialPressure * 0.621991
    humidityRatio = constant / pressDiffer

    return humidityRatio, partialPressure, saturationPressure


def findEnthalpy(airTemp, humidRatio):
    """
    Calculates Enthalpy (kJ/kg) at Humidity Ratio humidRatio (kg water/kg air)
    and at Temperature airTemp (C).
    """
    enVariable1 = 1.01 + (1.89 * humidRatio)
    enVariable2 = enVariable1 * airTemp
    enVariable3 = 2500 * humidRatio
    enVariable4 = enVariable2 + enVariable3
    if enVariable4 >= 0: enthalpy = enVariable4
    else: enthalpy = 0

    return enthalpy


def findWetBulb(dbTemp, RH, Psta=101325):
    """
    Calculates Wet Bulb Temperature (C) at Temperature dbTemp (C),
    Relative Humidity RH (%), and Barometric Pressure Psta (Pa).
    """
    es = 6.112 * math.e**((17.67 * dbTemp) / (dbTemp + 243.5))
    e = (es * RH) / 100
    Tw = 0
    increse = 10
    previoussign = 1
    Ed = 1

    while math.fabs(Ed) > 0.005:
        Ewg = 6.112 * math.e**((17.67 * Tw) / (Tw + 243.5))
        eg = Ewg - (Psta / 100) * (dbTemp - Tw) * 0.00066 * (1 + (0.00155 * Tw))
        Ed = e - eg
        if Ed == 0:
            break
        else:
            if Ed < 0:
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
        Tw = Tw + increse * previoussign

    return Tw


def findDewPoint(dbTemp, RH):
    """
    Calculates Dew Point Temperature (C) at Temperature dbTemp (C) and
    Relative Humidity RH (%).
    """
    es = 6.112 * math.e**((17.67 * dbTemp) / (dbTemp + 243.5))
    e = (es * RH) / 100
    Td = (243.5 * math.log(e / 6.112)) / (17.67 - math.log(e / 6.112))

    return Td


def findRelHumidFromHumidRatio(absHumid, airTemp, barPress=101325):
    """
    Calculates Relative Humidity (%) at Humidity Ratio absHumid (kg water/kg air),
    Temperature airTemp (C), and Barometric Pressure barPress (Pa).
    """
    # Calculate the partial pressure of water in the atmostphere.
    Pw = (absHumid * 1000 * barPress) / (621.9907 + (absHumid * 1000))
    # Convert Temperature to Kelvin
    tKelvin = airTemp + 273
    # Calculate saturation pressure.
    Pws = findSaturatedVaporPressureHighAccuracy(tKelvin)
    # Calculate the relative humidity.
    relHumid = (Pw / Pws) * 100

    return relHumid


def findRelHumidFromDryBulbDewPt(airTemp, dewPt):
    """
    Calculates Relative Humidity (%) at Temperature airTemp (C), and Dew Point dewPt (C).
    """
    # Calculate the partial pressure of water in the atmosphere.
    A = 6.11657
    m = 7.591386
    Tn = 240.7263
    Td = dewPt + 273
    Pw = ((math.pow(10, (m / ((Tn / Td) + 1)))) * A) / 100
    # Convert Temperature to Kelvin
    tKelvin = airTemp + 273
    # Calculate saturation pressure.
    Pws = findSaturatedVaporPressureHighAccuracy(tKelvin)
    # Calculate the relative humidity.
    relHumid = (Pw / Pws) * 100

    return relHumid


def findAirTempFromEnthalpy(enthalpy, absHumid):
    """
    Calculates Air Temperature (C) at Enthalpy enthalpy (kJ/kg) and Humidity Ratio absHumid (kg water/kg air).
    """
    airTemp = (enthalpy - 2.5 * (absHumid * 1000)) / (1.01 + (0.00189 * absHumid * 1000))

    return airTemp


def findAirTempFromWetBulb(wetBulb, relHumid, avgBarPress=101325):
    """
    Calculates Air Temperature (C) at Wet Bulb Temperature wetBulb (C), Relative Humidity relHumid (%)
    and Barometric Pressure avgBarPress (Pa).
    """
    humidityRatio, partialPressure, saturationPressure = findHumidRatio(wetBulb, relHumid, avgBarPress)
    absHumid, partialPressure, saturationPressure = findHumidRatio(wetBulb, 100, avgBarPress)
    airTemp = wetBulb + (((absHumid - humidityRatio) * 2260000) / (1005))

    return airTemp, humidityRatio
