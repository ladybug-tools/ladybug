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
        if self.getHOY(self.stTime)> self.getHOY(self.endTime):
            self.reversed = True
        else:
            self.reversed = False

        self.timestamps = self.getTimestamps()

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
                 self.analysisPeriod.getStartTimeAsTuple(),
                 self.analysisPeriod.getEndTimeAsTuple()
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

class DataPoint:
    """ A Ladybug data point which has a
         timestamp <datetime>
         value <flot> or <integer>
         dataType <string>
         unit  <string>
    """
    def __init__(self, value, dataType):
        self.value = value
        self.dataType = dataType
        self.unit = DataTypes(dataType).unit

    def __repr__(self):
        return self.value

class DataTypes:
    """Collection of Ladybug's data types"""
    def __init__(self):
        self.__dataTypes = {
            'modelYear' : {'fullName':'Year', 'unit':'Year'},
            'dbTemp'    : {'fullName':'Dry Bulb Temperature', 'unit':'C'},
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

    def unit(self, dataType):
        """Return unit for a dataType"""
        return self.__dataTypes[dataType]['unit']

    def fullName(self, dataType):
        """Return fullName for a dataType"""
        return self.__dataTypes[dataType]['fullName']

    @property
    def dataTypes(self):
        return self.__dataTypes.keys()

# ap = AnalysisPeriod(stMonth=1, stDay=1, stHour=1, endMonth=12, endDay=31, endHour=24, timestep=1)
# location = Location()
# header = LadybugHeader(city="", dataType="", unit="", timestep="Hourly", analysisPeriod=AnalysisPeriod())
