import math
import core
import euclid

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

        self.__latitude = math.radians(float(latitude))
        self.__longitude = math.radians(float(longitude))
        self.northAngle = northAngle
        self.timeZone = timeZone
        self.daylightSavingPeriod = daylightSavingPeriod

    @classmethod
    def fromLocation(self, location, northAngle = 0, daylightSavingPeriod = None):
        return Sunpath(location.latitude, northAngle, location.longitude, \
            location.timeZone, daylightSavingPeriod)

    @property
    def latitude(self):
        """get latitude in degrees"""
        return math.degrees(self.__latitude)

    @latitude.setter
    def latitude(self, value):
        """set latitude value in degrees"""
        self.__latitude = math.radians(float(value))

    @property
    def longitude(self):
        """get latitude in degrees"""
        return math.degrees(self.__latitude)

    @longitude.setter
    def longitude(self, value):
        """set latitude value in degrees"""
        self.__longitude = math.radians(float(value))

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
        solDec, eqOfTime = self.__calculateSolarGeometry(datetime)

        month, day, hour = datetime.month, datetime.day, datetime.floatHour
        isDaylightSaving = self.isDaylightSavingHour(datetime.HOY)
        if isDaylightSaving: hour += 1

        #hours
        solTime = self.__calculateSolarTime(hour, eqOfTime, isSolarTime)

        #degrees
        hourAngle = (solTime*15 + 180) if (solTime*15 < 0) else (solTime*15 - 180)

        #RADIANS
        zenith = math.acos(math.sin(self.__latitude)*math.sin(solDec) \
            + math.cos(self.__latitude)*math.cos(solDec)*math.cos(math.radians(hourAngle)))

        altitude = (math.pi/2) - zenith

        if hourAngle == 0.0 or hourAngle == -180.0 or hourAngle == 180.0:
            if solDec < self.__latitude: azimuth = math.pi
            else: azimuth = 0.0
        else:
            azimuth = ((math.acos(((math.sin(self.__latitude)*math.cos(zenith)) \
                - math.sin(solDec))/(math.cos(self.__latitude)*math.sin(zenith))) + math.pi) % (2*math.pi)) \
                if (hourAngle > 0) else \
                    ((3*math.pi - math.acos(((math.sin(self.__latitude)*math.cos(zenith)) \
                    - math.sin(solDec))/(math.cos(self.__latitude)*math.sin(zenith)))) % (2*math.pi))

        # create the sun for this hour
        return Sun(datetime, altitude, azimuth, isSolarTime, isDaylightSaving, self.northAngle)

    def calculateSunriseSunset(self, month, day, depression = 0.833, isSolarTime = False):
        datetime = core.LBDateTime(month, day, hour = 12)
        return self.calculateSunriseSunsetFromDateTime(datetime, depression, isSolarTime)

    # TODO: implement solar time
    def calculateSunriseSunsetFromDateTime(self, datetime, depression = 0.833, isSolarTime = False):
        """Calculate sunrise, sunset and noon for a day of year"""

        solDec, eqOfTime = self.__calculateSolarGeometry(datetime)

        # calculate sunrise and sunset hour
        #if isSolarTime:
        #    noon = .5
        #else:
        noon = (720 - 4 * math.degrees(self.__longitude) - eqOfTime + self.timeZone * 60) / 1440

        sunRiseHourAngle = self.__calculateSunriseHourAngle(solDec, depression)
        sunrise  = noon - sunRiseHourAngle * 4 / 1440
        sunset   = noon + sunRiseHourAngle * 4 / 1440

        # convert demical hour to solar hour
        # noon    = self.__calculateSolarTime(24*noon, eqOfTime, isSolarTime)
        # sunrise = self.__calculateSolarTime(24*sunrise, eqOfTime, isSolarTime)
        # sunset  = self.__calculateSolarTime(24*sunset, eqOfTime, isSolarTime)

        return {
                "sunrise"   : core.LBDateTime(datetime.month, datetime.day, 24 * sunrise),
                "noon"      : core.LBDateTime(datetime.month, datetime.day, 24 * noon),
                "sunset"    : core.LBDateTime(datetime.month, datetime.day, 24 * sunset)}

    def __calculateSolarGeometry(self, datetime, year = 2015):

        """Calculate Solar geometry for an hour of the year

            Attributes:
                datetime: A Ladybug datetime

            Returns:
                Solar declination: Solar declination in radians
                eqOfTime: Equation of time as minutes
        """

        month, day, hour = datetime.month, datetime.day, datetime.floatHour

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

        return solDec, eqOfTime

    def __calculateSunriseHourAngle(self, solarDec, depression = 0.833):
        """Calculate hour angle for sunrise time in degrees"""
        hourAngleArg = math.cos(math.radians(90 + depression)) \
            /(math.cos(self.__latitude) * math.cos(solarDec)) \
            - math.tan(self.__latitude) * math.tan(solarDec)

        return math.degrees(math.acos(hourAngleArg))

    def __calculateSolarTime(self, hour, eqOfTime, isSolarTime):
        """Calculate Solar time for an hour"""
        if isSolarTime: return hour
        return ((hour*60 + eqOfTime + 4*math.degrees(self.__longitude) - 60*self.timeZone) % 1440)/60

class Sun:
    """Create a sun

    Attributes:
        datetime: A Ladybug datetime that represents the datetime for this sunVector
        altitude: Solar Altitude in radians
        azimuth: Solar Azimuth in radians
        isSolarTime: A Boolean that indicates if datetime represents the solar time
        isDaylightSaving: A Boolean that indicates if datetime is calculated for Daylight saving period
        northAngle: North angle of the sunpath in Degrees. This will be only used to calculate the solar vector.

    """
    def __init__(self, datetime, altitude, azimuth, isSolarTime, isDaylightSaving, northAngle):
        self.__datetime = datetime
        self.__altitude = altitude
        self.__azimuth = azimuth
        self.__isSolarTime = isSolarTime
        self.__isDaylightSaving = isDaylightSaving
        self.__northAngle = northAngle # useful to calculate sun vector - sun angle is in degrees
        self.__hourlyData = [] # Place holder for hourly data I'm not sure how it will work yet

    @property
    def datetime(self):
        """Return datetime"""
        return self.__datetime

    @property
    def HOY(self):
        """Return Hour of the year"""
        return self.__datetime.floatHOY

    @property
    def altitude(self):
        """Return solar altitude in degrees"""
        return math.degrees(self.__altitude)

    @property
    def azimuth(self):
        """Return solar azimuth in degrees"""
        return math.degrees(self.__azimuth)

    @property
    def isSolarTime(self):
        """Return a Boolean that indicates is datetime is solar time"""
        return self.__isSolarTime

    @property
    def isDaylightSaving(self):
        """Return a Boolean that indicates is datetime is solar time"""
        return self.__isDaylightSaving

    @property
    def hourlyData(self):
        return self.__hourlyData

    def appendHourlyData(self, data):
        """Append Ladybug hourly data to this sun"""
        assert data.datetime.HOY == self.HOY
        self.__hourlyData.append(data)
        return True

    @property
    def isDuringDay(self):
        # sun vector is flipped to look to the center
        return self.sunVector.z <= 0

    @property
    def sunVector(self):
        """Return sun vector for this sun
            Sun vector will face
        """
        zAxis = euclid.Vector3(0., 0., -1.)
        xAxis = euclid.Vector3(1., 0., 0.)
        northVector = euclid.Vector3(0., 1., 0.)
        # .rotate_around(zAxis, math.radians(self.__northAngle))

        # rotate north vector based on azimuth, altitude, and north
        sunvector = northVector \
            .rotate_around(xAxis, self.__altitude) \
            .rotate_around(zAxis, self.__azimuth) \
            .rotate_around(zAxis, math.radians(-self.__northAngle))

        sunvector.normalize().flip()

        return sunvector
