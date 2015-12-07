import math
import ladybug.core as core

class Sunpath:
    """
    Calculates sun path

    Attributes:
        latitude: The latitude of the location. Values must be between -90 and 90. Default is set to the equator.
        northAngle: Angle to north (0-360). 90 is west and 270 is east (Default: 0)
        longitude: The longitude of the location (Default: 0)
        timeZone: A number representing the time zone of the location you are constructing. This can improve the accuracy of the resulting sun plot.  The time zone should follow the epw convention and should be between -12 and +12, where 0 is at Greenwich, UK, positive values are to the East of Greenwich and negative values are to the West.
        daylightSavingPeriod: An analysis period for daylight saving. (Default = None)

    Usage:
        import ladybug.sunpath as sunpath
        # initiate sunpath
        sp = sunpath.Sunpath(50)
        sun = sp.calculateSun(1, 1, 12) # calculate sun data for Jan 1 at noon
        print sun.azimuth, sun.altitude
    """

    def __init__(self, latitude = 0, northAngle = 0, longitude = 0, timeZone = 0,
                daylightSavingPeriod = None):

        self.latitude = math.radians(float(latitude))
        self.longitude = math.radians(float(longitude))
        self.northAngle = northAngle
        self.timeZone = timeZone
        self.daylightSavingPeriod = daylightSavingPeriod

    @classmethod
    def fromLocation(self, location, northAngle = 0, daylightSavingPeriod = None):
        return Sunpath(location.latitude, northAngle, location.longitude, \
            location.timeZone, daylightSavingPeriod)

    def isDaylightSavingHour(self, datetime):
        if not self.daylightSavingPeriod: return False
        return self.daylightSavingPeriod.isTimeIncluded(datetime.HOY)


    def calculateSun(self, month, day, hour, isSolarTime = False):
        """Get Sun data for an hour of the year

            Args:
                month: An integer between 1-12
                day: An integer between 1-31
                hour: A positive number <= 24
                isSolarTime: A boolean to indicate if the input hour is solar time. (Default: False)

            Returns:
                A sun object for this particular time
        """
        datetime = core.LBDateTime(month, day, hour)
        return self.calculateSunFromDataTime(datetime, isSolarTime)

    def calculateSunFromHOY(self, HOY, isSolarTime = False):
        """Get Sun data for an hour of the year

            Args:
                datetime: Ladybug datetime
                isSolarTime: A boolean to indicate if the input hour is solar time. (Default: False)

            Returns:
                A sun object for this particular time
        """
        datetime = core.LBDateTime.fromHOY(HOY)
        return self.calculateSunFromDataTime(datetime, isSolarTime)

    def calculateSunFromDataTime(self, datetime, isSolarTime = False):
        """Get Sun data for an hour of the year
            This code is originally written by Trygve Wastvedt (Trygve.Wastvedt@gmail.com)
            based on (NOAA) and modified by Chris Mackey and Mostapha Roudsari

            Args:
                datetime: Ladybug datetime
                isSolarTime: A boolean to indicate if the input hour is solar time. (Default: False)

            Returns:
                A sun object for this particular time
        """
        year = 2015
        month, day, hour = datetime.month, datetime.day, datetime.hour

        isDaylightSaving = self.isDaylightSavingHour(datetime.HOY)
        if isDaylightSaving: hour += 1

        a = 1 if (month < 3) else 0
        y = year + 4800 - a
        m = month + 12*a - 3

        julianDay = day + math.floor((153*m + 2)/5) + 59

        julianDay += (hour - self.timeZone)/24.0  + 365*y + math.floor(y/4) \
            - math.floor(y/100) + math.floor(y/400) - 32045.5 - 59

        julianCentury = (julianDay - 2451545) / 36525

        #degrees
        geomMeanLongSun = (280.46646 + julianCentury * (36000.76983 + julianCentury*0.0003032)) % 360

        #degrees
        geomMeanAnomSun = 357.52911 + julianCentury*(35999.05029 - 0.0001537*julianCentury)
        eccentOrbit = 0.016708634 - julianCentury*(0.000042037 + 0.0000001267*julianCentury)
        sunEqOfCtr = math.sin(math.radians(geomMeanAnomSun))*(1.914602 - julianCentury*(0.004817+0.000014*julianCentury)) + \
            math.sin(math.radians(2*geomMeanAnomSun))*(0.019993-0.000101*julianCentury) + \
            math.sin(math.radians(3*geomMeanAnomSun))*0.000289

        #degrees
        sunTrueLong = geomMeanLongSun + sunEqOfCtr
        #AUs
        sunTrueAnom = geomMeanAnomSun + sunEqOfCtr
        #AUs
        sunRadVector = (1.000001018*(1 - eccentOrbit**2))/ \
            (1 + eccentOrbit*math.cos(math.radians(sunTrueLong)))
        #degrees
        sunAppLong = sunTrueLong - 0.00569 - 0.00478*math.sin(math.radians(125.04-1934.136*julianCentury))

        #degrees
        meanObliqEcliptic = 23 + (26 + ((21.448 - julianCentury*(46.815 + \
            julianCentury*(0.00059 - julianCentury*0.001813))))/60)/60
        #degrees
        obliqueCorr = meanObliqEcliptic + 0.00256*math.cos(math.radians(125.04 - 1934.136*julianCentury))
        #degrees
        sunRightAscen = math.degrees(math.atan2(math.cos(math.radians(obliqueCorr))* \
            math.sin(math.radians(sunAppLong)), math.cos(math.radians(sunAppLong))))

        #RADIANS
        solDec = math.asin(math.sin(math.radians(obliqueCorr))*math.sin(math.radians(sunAppLong)))

        varY = math.tan(math.radians(obliqueCorr/2))*math.tan(math.radians(obliqueCorr/2))
        #minutes
        eqOfTime = 4*math.degrees(varY*math.sin(2*math.radians(geomMeanLongSun)) \
            - 2*eccentOrbit*math.sin(math.radians(geomMeanAnomSun)) \
            + 4*eccentOrbit*varY*math.sin(math.radians(geomMeanAnomSun))*math.cos(2*math.radians(geomMeanLongSun)) \
            - 0.5*(varY**2)*math.sin(4*math.radians(geomMeanLongSun)) \
            - 1.25*(eccentOrbit**2)*math.sin(2*math.radians(geomMeanAnomSun)))
        #hours
        if isSolarTime == False:
            solTime = ((hour*60 + eqOfTime + 4*math.degrees(self.longitude) - 60*self.timeZone) % 1440)/60
        else:
            solTime = hour

        #degrees
        hourAngle = (solTime*15 + 180) if (solTime*15 < 0) else (solTime*15 - 180)

        #RADIANS
        zenith = math.acos(math.sin(self.latitude)*math.sin(solDec) \
            + math.cos(self.latitude)*math.cos(solDec)*math.cos(math.radians(hourAngle)))

        altitude = (math.pi/2) - zenith

        if hourAngle == 0.0 or hourAngle == -180.0 or hourAngle == 180.0:
            if solDec < self.latitude: azimuth = math.pi
            else: azimuth = 0.0
        else:
            azimuth = ((math.acos(((math.sin(self.latitude)*math.cos(zenith)) \
                - math.sin(solDec))/(math.cos(self.latitude)*math.sin(zenith))) + math.pi) % (2*math.pi)) \
                if (hourAngle > 0) else \
                    ((3*math.pi - math.acos(((math.sin(self.latitude)*math.cos(zenith)) \
                    - math.sin(solDec))/(math.cos(self.latitude)*math.sin(zenith)))) % (2*math.pi))

        # create the sun for this hour
        return Sun(datetime, altitude, azimuth, isSolarTime, isDaylightSaving)


class Sun:
    def __init__(self, datetime, altitude, azimuth, isSolarTime, isDaylightSaving):
        self.datetime = datetime
        self.altitude = altitude
        self.azimuth = azimuth
        self.isSolarTime = isSolarTime
        self.isDaylightSaving = isDaylightSaving
