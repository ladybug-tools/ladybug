import datetime
import re

class AnalysisPeriod:
    """Define a Ladybug Analysis Period.

        Attributes:
            stMonth: An integer between 1-12 for starting month (default = 1)
            stDay: An integer between 1-31 for starting day (default = 1).
                    Note that some months are shorter than 31 days.
            stHour: An integer between 1-24 for starting hour (default = 1)
            endMonth: An integer between 1-12 for ending month (default = 12)
            endDay: An integer between 1-31 for ending day (default = 31)
                    Note that some months are shorter than 31 days.
            endHour: An integer between 1-24 for ending hour (default = 24)
            timestep: An integer between 1-60 for timestep (default = 1)
    """

    def __init__(self, stMonth = 1, stDay = 1, stHour = 1, endMonth = 12,
                endDay = 31, endHour = 24, timestep = 1):
        """Init an analysis period"""
        self.year = 2000 # Ladybug's Analysis period year is always set to 2000
        self.timestep = datetime.timedelta(hours = timestep)
        self.stTime = self.checkDateTime(stMonth, stDay, stHour-1)
        self.endTime = self.checkDateTime(endMonth, endDay, endHour-1)

        if stHour <= endHour:
            self.overnight = False # each segments of hours will be in a single day
        else:
            self.overnight = True

        # A reversed analysis period is went starting month is after ending month
        # (e.g DEC to JUN)
        if self.get_HOY(self.stTime)> self.get_HOY(self.endTime):
            self.reversed = True
        else:
            self.reversed = False

        self.timestamps = self.get_timestamps()

    def checkDateTime(self, month, day, hour):
        """Checks if time combination is a valid time."""
        try:
            return datetime.datetime(self.year, month, day, hour)
        except ValueError, e:
            raise e

    def get_HOY(self, time):
        """Return hour of the year between 1 and 8760."""
        # fix the end day
        numOfDays = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
        JD = numOfDays[time.month-1] + int(time.day)
        return (JD - 1) * 24 + time.hour

    def get_timestamps(self):
        """Return a list of timestamps in this analysis period."""
        timestamps = []
        curr = self.stTime
        while curr <= self.endTime:
            if self.isTimeIncluded(curr): timestamps.append(curr)
            curr += self.timestep
        return timestamps


    def isTimeIncluded(self, time):
        """Check if time is included in analysis period.

            Return True if time is inside this analysis period,
            otherwise return False

            Args:
                time: An input timedate

            Returns:

        """
        # time filtering in Ladybug and honeybee is slightly different since start hour and end hour will be
        # applied for every day. For instance 2/20 9am to 2/22 5pm means hour between 9-17 during 20, 21 and 22 of Feb
        # First check if the day is in range
        if not self.reversed and not self.stTime<= time <= self.endTime:
            return False
        if self.reversed and \
           not (self.stTime<= time <= datetime.datetime(self.year, 12, 31, 23) \
           or datetime.datetime(self.year, 1, 1, 1) <= time <= self.endTime):
               return False

        # Now check the hours to make sure it's between the range
        if not self.overnight and self.stTime.hour <= time.hour <= self.endTime.hour: return True
        if self.overnight and (self.stTime.hour <= time.hour <= 23 \
                                or 0<= time.hour <= self.endTime.hour): return True

        return False

    def get_startTimeAsTuple(self):
        """Return start month, day and hour as a tuple."""
        return (self.stTime.month, self.stTime.day, self.stTime.hour + 1)


    def get_endTimeAsTuple(self):
        """Return end month, day and hour of analysis period as a tuple."""
        return (self.endTime.month, self.endTime.day, self.endTime.hour + 1)

    def __repr__(self):
        return "%s/%s %s To %s/%s %s"%\
            (self.stTime.month, self.stTime.day, self.stTime.hour + 1, \
             self.endTime.month, self.endTime.day, self.endTime.hour + 1)


class Header:
    """Standard Ladybug header for lists.

        The header carries data for city,
        data type, unit, and analysis period

        Attributes:
            city: A string for the city name
            dataType: A valid Ladybug data type. Try DataType.dataTypes to see list of data types
            unit: dataType unit. If empty string it will be set based on dataType
            timestep: Data timestep "Hourly", "Daily", "Monthly", "Annual", "N/A"
            analysisPeriod: A Ladybug analysis period. (defualt: 1 Jan 1 to 31 Dec 24)
    """

    def __init__(self, city = "", dataType = "", unit = "", frequency = "Hourly", analysisPeriod = None):
        """Initiate Ladybug header for lists."""
        self.header = 'location|dataType|units|frequency|startsAt|endsAt'
        self.city = city
        self.dataType = dataType
        self.unit = unit
        self.frequency = frequency
        self.analysisPeriod = AnalysisPeriod() if not analysisPeriod else analysisPeriod

    @property
    def toList(self):
        """Return Ladybug header as a list"""
        return [
                 self.header,
                 self.city,
                 self.dataType,
                 self.unit,
                 self.frequency,
                 self.analysisPeriod.get_startTimeAsTuple(),
                 self.analysisPeriod.get_endTimeAsTuple()
               ]

    def __repr__(self):
        return "%s for %s during %s"%(self.dataType, self.city, self.analysisPeriod)

class Location:

    def __init__(self, city = '', country = '', latitude = '', \
                longitude = '', timeZone = '', elevation ='', \
                source = '', stationId = ''):

        self.city = str(city)
        self.country = str(country)
        self.latitude = str(latitude)
        self.longitude = str(longitude)
        self.timeZone = str(timeZone)
        self.elevation = str(elevation)
        self.source = str(source)
        self.stationId = str(stationId)

    def createFromEPString(self, EPString):
        """Create a Ladybug location from an EnergyPlus location string
            Parameters:
                EPString: Standard EP location string

            Usage:
                l = Location() #initiate location
                l.createFromEPString(EPString)
                print "LAT:%s, LON:%s"%(l.latitude, l.longitude)
        """

        try:
            self.city, self.latitude, \
            self.longitude, self.timeZone, \
            self.elevation = re.findall(r'\r*\n*([a-zA-Z0-9.:_ ]*)[,|;]', \
                                    EPString, re.DOTALL)[1:]
        except Exception, e:
            raise Exception ("Failed to import EP string!")

    @property
    def EPStyleLocationString(self):
        """Return EnergyPlus's location string"""
        return "Site:Location,\n" + \
            self.city + ',\n' + \
            self.latitude +',      !Latitude\n' + \
            self.longitude +',     !Longitude\n' + \
            self.timeZone +',     !Time Zone\n' + \
            self.elevation + ';       !Elevation'

    def __repr__(self):
        return "%s"%(self.EPStyleLocationString)

class Dataset:
    """A standard Ladybug Dataset
        Storage of key: values for Ladybug data where:
         key is alway a datetime
         It will be normally used with Ladybug header
    """
    def __init__(self, data, header):
        self.data = data
        self.header = header


    def filterByTime(self):
        pass

    def filterByConditionalStatement(self):
        pass

    def filterByPattern(self):
        pass

    @property
    def averageMonthly(self):
        return

    @property
    def averageWeekly(self):
        return

    @property
    def averageForAnHourEveryMonth(self):
        return

class DataTypes:
    """Collection of Ladybug's data types

        Ladybug types are mainly based on available data in epw file.
        There are also native Ladybug types which doesn't exist in epw file
        such as cumulative radiation, sunlight hours, etc.

    """

    # TODO: Use field numbers to match  the names. the rest should come from type
    __dataTypesData = {
        'modelYear' : {'fullName':'Year', 'unit':'Year'},
        'dbTemp'    : {'fullName':'Dry Bulb Temperature', 'type': 'Temperature'},
        'dewPoint'  : {'fullName':'Dew Point Temperature', 'unit':'C'},
        'RH'        : {'fullName':'Relative Humidity', 'unit':'%'},
        'windSpeed' : {'fullName':'Wind Speed', 'unit':'m/s'},
        'windDir'   : {'fullName':'Wind Direction', 'unit':'degrees'},
        'dirRad'    : {'fullName':'Direct Normal Radiation', 'unit':'Wh/m2'},
        'difRad'    : {'fullName':'Diffuse Horizontal Radiation', 'unit':'Wh/m2'},
        'glbRad'    : {'fullName':'Global Horizontal Radiation', 'unit':'Wh/m2'},
        'dirIll'    : {'fullName':'Direct Normal Illuminance', 'unit':'lux'},
        'difIll'    : {'fullName':'Diffuse Horizontal Illuminance', 'unit':'lux'},
        'glbIll'    : {'fullName':'Global Horizontal Illuminance', 'unit':'lux'},
        'cloudCov'  : {'fullName':'Total Cloud Cover', 'unit':'tenth'},
        'rainDepth' : {'fullName':'Liquid Precipitation Depth', 'unit':'mm'},
        'barPress'  : {'fullName':'Barometric Pressure', 'unit':'Pa'}
        }

    __dataTypes = __dataTypesData.keys()

    # error message to be raised on type error
    __typeErrorMsg = "%s is not a valid Ladybug data Type!\nValid data types are: %s"

    @classmethod
    def unit(cls, dataType):
        """Return unit for a dataType"""
        if dataType not in cls.__dataTypes:
            raise ValueError(cls.__typeErrorMsg%(dataType, cls.__dataTypes))
        return cls.__dataTypesData[dataType]['unit']

    @classmethod
    def fullName(cls, dataType):
        """Return fullName for a dataType"""
        if dataType not in cls.__dataTypes:
            raise ValueError(cls.__typeErrorMsg%(dataType, cls.__dataTypes))
        return cls.__dataTypesData[dataType]['fullName']

    @classmethod
    def get_dataTypes(cls):
        return cls.__dataTypes

    def __repr__():
        return "Ladybug Data Types"

class DataPoint(object):
    """ A Ladybug data point

        Attributes:
            value :<flot>, <integer>, <string> based on type
            isEpwData: A boolean that indicates if the data is from an epw
                file. Valid range for epw file can be differnt. For example
                Temperature range in an ewp file is -70 C - 70 C (Default: False)
            standard: class of SI or IP. (Default is SI)
    """

    def __init__(self, value, isEpwData = False, standard = None):
        if not standard: standard = SI
        self.value = value
        self.standard = standard
        self.isEpwData = isEpwData

        self.__typeErrorMsg = "%s is not a valid input type. " + \
            "Input should be from %s"
        self.__valueErrorMsg = "%s is not a valid input type. " + \
            "Input should be between %s and %s"
        self.__standardErrorMsg = "%s is not a valid standard type. " + \
            "Valid standards are SI and IP"

        #check validity of input
        self.isValid(raiseException = True)

    def isValid(self, raiseException = False):
        """Check validity of input"""
        if not(self.standard is IP or self.standard is SI):
            raise Exception(self.__standardErrorMsg%self.standard)

        if self.valueType:
            try:
                self.value = map(self.valueType, [self.value])[0]
            except:
                if raiseException:
                    raise TypeError(self.__typeErrorMsg%(self.value, self.valueType))
                return False #not a valid standard

        #check if the valus is in range
        if self.valueType is str: return True # if not a number return True

        isValid = self.__isInRange
        if not isValid and raiseException:
            raise ValueError(self.__valueErrorMsg%(self.value, self.minimum, self.maximum))
        else:
            return isValid

    @property
    def __isInRange(self):
        """Retuen True is value is in range"""
        return self.minimum <= self.value <= self.maximum

    def get_valueBasedOnCurrentStandard(self, value, valueStandard):
        """Return the value based on the current standard IP/SI

            This method makes it possible to set minimum and maximum values
            with a single number in SI or IP
        """
        if valueStandard is self.standard:
            return value # the standard is the same so return the same value
        elif self.standard is SI:
            #The value is in IP and should be converted to SI
            return self.get_valueInSI(value)
        elif self.standard is IP:
            #The value is in SI and should be converted to IP
            return self.get_valueInIP(value)

    def convertToIP(self):
        """Change to IP system

            Warning: convertToIP only and only changes this value to IP
        """
        if self.standard is IP: return True
        # If it's in SI change system and value
        self.standard = IP
        self.value = self.get_valueBasedOnCurrentStandard(self.value, SI)
        return True

    def convertToSI(self):
        """Change to SI system

            Warning: convertToSI only and only changes this value to SI
        """
        if self.standard is SI: return True
        # If it's in IP change system and value
        self.standard = SI
        self.value = self.get_valueBasedOnCurrentStandard(self.value, IP)
        return True

    def unit(self):
        raise NotImplementedError

    def valueType(self):
        raise NotImplementedError

    def minimum(self):
        raise NotImplementedError

    def maximum(self):
        raise NotImplementedError

    def __repr__(self):
        return str(self.value)

class GenericData(DataPoint):
    """Generic Data Point

        Attributes:
            value :<flot>, <integer>, <string> based on type
            isEpwData: A boolean that indicates if the data is from an epw
                file. Valid range for epw file can be differnt. For example
                Temperature range in an ewp file is -70 C - 70 C (Default: False)
            standard: SI or IP. (Default is SI)
            def __init__(self, value, isEpwData = False, standard= None):
                DataPoint.__init__(self, value, isEpwData, standard)
                #check validity of input
                self.isValid(valueType = self.valueType, raiseException = True)
    """
    def __init__(self, value, isEpwData = False, standard= None):
        DataPoint.__init__(self, value, isEpwData, standard)

    @property
    def unit(self):
        return ""

    @property
    def valueType(self):
        return str

    @property
    def minimum(self):
        """Return minimum valid value"""
        return float("-inf")

    @property
    def maximum(self):
        return float("inf")

    @staticmethod
    def get_valueInIP(value):
        """return the value in IP assuming input value is in SI"""
        return value

    @staticmethod
    def get_valueInSI(value):
        """return the value in SI assuming input value is in IP"""
        return value

class Temperature(DataPoint):
    """Base type for temperature"""

    def __init__(self, value, isEpwData = False, standard= None):
        DataPoint.__init__(self, value, isEpwData, standard)

    @property
    def unit(self):
        if self.standard is SI: return "C"
        elif self.standard is IP: return "F"

    @property
    def valueType(self):
        return float

    @property
    def minimum(self):
        """Return minimum valid value"""
        if self.isEpwData:
            return self.get_valueBasedOnCurrentStandard(-70, SI)
        else:
            return float("-inf")

    @property
    def maximum(self):
        """Return maximum valid value"""
        if self.isEpwData:
            return self.get_valueBasedOnCurrentStandard(70, SI)
        else:
            return float("inf")

    @staticmethod
    def get_valueInIP(value):
        """return the value in F assuming input value is in C"""
        return value * 9 / 5 + 32

    @staticmethod
    def get_valueInSI(value):
        """return the value in C assuming input value is in F"""
        return (value - 32) * 5 / 9

class RelativeHumidity(DataPoint):
    """Base type for Relative Humidity"""

    def __init__(self, value, isEpwData = False, standard= None):
        DataPoint.__init__(self, value, isEpwData, standard)

    @property
    def unit(self):
        return "%"

    @property
    def valueType(self):
        return float

    @property
    def minimum(self):
        """Return minimum valid value"""
        return 0

    @property
    def maximum(self):
        """Return maximum valid value"""
        return 100

    @staticmethod
    def get_valueInIP(value):
        """return the value in IP assuming input value is in SI"""
        return value

    @staticmethod
    def get_valueInSI(value):
        """return the value in SI assuming input value is in IP"""
        return value

class SI(object):
    def __repr__():
        return "SI"

class IP(object):
    def __repr__():
        return "IP"
