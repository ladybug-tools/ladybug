import re
import datetime

class DateTimeLib:
    """Ladybug DateTime Libray
    This class includes useful data and methods for date and time
    """
    monthList = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    numOfDaysEachMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    numOfDaysUntilMonth = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]
    numOfHoursUntilMonth = [24 * numOfDay for numOfDay in numOfDaysUntilMonth]

    @classmethod
    def getHourOfYear(cls, month, day, hour):
        """Return hour of the year between 1 and 8760."""
        # make sure input values are correct
        cls.checkDateTime(month, day, hour)

        # fix the end day
        JD = cls.numOfDaysUntilMonth[month-1] + int(day)
        return (JD - 1) * 24 + hour

    # TODO: remove dependencies to datetime libray
    @staticmethod
    def checkDateTime(month, day, hour):
        """Checks if time combination is a valid time."""
        try:
            return datetime.datetime(2000, month, day, hour-1)
        except ValueError, e:
            raise e

    @classmethod
    def getMonthDayAndHour(cls, hourOfYear):
        """Return month, day and hour for an hour of the year"""
        if hourOfYear%8760==0: return 12, 31, 24

        # find month
        for monthCount in range(12):
            if hourOfYear <= cls.numOfHoursUntilMonth[monthCount + 1]:
                month = monthCount + 1
                break

        # find day and hour
        if hourOfYear%24 == 0:
            # last hour of the day
            day = int((hourOfYear - cls.numOfHoursUntilMonth[month - 1])/24)
            hour = 24
        else:
            day = int((hourOfYear - cls.numOfHoursUntilMonth[month - 1])/24) + 1
            hour = hourOfYear%24

        return month, day, hour

# TODO: add comparison methods (largerthan, smallerthan, ...)
# TODO: add monthly, daily average datetime values
class LBDateTime:
    def __init__(self, month = 1, day = 1, hour = 1):
        DateTimeLib.checkDateTime(month, day, hour)
        self.month = month
        self.day = day
        self.hour = hour
        self.HOY = DateTimeLib.getHourOfYear(self.month, self.day, self.hour)

    @classmethod
    def fromHOY(cls, HOY):
        month, day, hour = DateTimeLib.getMonthDayAndHour(HOY)
        return LBDateTime(month, day, hour)

    def __repr__(self):
        return "%d %s at %d"%( self.day, DateTimeLib.monthList[self.month-1], self.hour)

class AnalysisPeriod:
    """Ladybug Analysis Period.

        A continuous analysis period between two days of the year between certain hours

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
    #TODO: handle timestep between 1-60
    def __init__(self, stMonth = 1, stDay = 1, stHour = 1, endMonth = 12,
                endDay = 31, endHour = 24):
        """Init an analysis period"""

        self.stTime = LBDateTime(int(stMonth), int(stDay), int(stHour))
        self.endTime = LBDateTime(int(endMonth), int(endDay), int(endHour))
        self.timestep = 1

        if self.stTime.hour <= self.endTime.hour:
            self.overnight = False # each segments of hours will be in a single day
        else:
            self.overnight = True

        # A reversed analysis period defines a period that starting month is after ending month
        # (e.g DEC to JUN)
        if self.stTime.HOY > self.endTime.HOY:
            self.reversed = True
        else:
            self.reversed = False

    @classmethod
    def fromAnalysisPeriod(cls, analysisPeriod):
        """Create and Analysis Period from an analysis period

            This method is useful to be called from inside Grasshopper or Dynamo
        """
        if not analysisPeriod:
            print "Analysis period is set to annual"
            return AnalysisPeriod()
        elif isinstance(analysisPeriod, AnalysisPeriod):
            return analysisPeriod
        elif isinstance(analysisPeriod, str):
            return cls.__fromAnalysisPeriodString(analysisPeriod)

    @classmethod
    def __fromAnalysisPeriodString(cls, analysisPeriodString):

        # %s/%s to %s/%s between %s to %s
        ap = analysisPeriodString.lower() \
                        .replace(' to ', ' ') \
                        .replace('/', ' ') \
                        .replace(' between ', ' ')

        try:
            stMonth, stDay, \
            endMonth, endDay, \
            stHour, endHour =  ap.split(' ')
            return AnalysisPeriod(stMonth, stDay, stHour, endMonth, endDay, endHour)
        except:
            raise ValueError(analysisPeriodString + " is not a valid analysis period!")

    def get_timestamps(self):
        """Return a list of Ladybug DateTime in this analysis period."""
        timestamps = []
        curr = self.stTime.HOY
        if not self.reversed:
            while curr <= self.endTime.HOY:
                time = LBDateTime.fromHOY(curr)
                if self.isTimeIncluded(time):
                    timestamps.append(time)
                curr += self.timestep
        else:
            while (1 <= curr <= self.endTime.HOY or self.stTime.HOY <= curr <= 8760):
                time = LBDateTime.fromHOY(curr)
                if self.isTimeIncluded(time):
                    timestamps.append(time)

                if curr == 8759:
                    curr = 8760
                else:
                    curr = (curr + self.timestep)%8760

        return timestamps

    def isTimeIncluded(self, time):
        """Check if time is included in analysis period.

            Return True if time is inside this analysis period,
            otherwise return False

            Args:
                time: A LBDateTime to be tested

            Returns:

        """
        # time filtering in Ladybug and honeybee is slightly different since start hour and end hour will be
        # applied for every day. For instance 2/20 9am to 2/22 5pm means hour between 9-17 during 20, 21 and 22 of Feb

        # First check if the day is in range
        if not self.reversed and not self.stTime.HOY<= time.HOY <= self.endTime.HOY:
            return False
        if self.reversed and \
           not (self.stTime.HOY<= time.HOY <= 8760 or 1 <= time.HOY <= self.endTime.HOY):
               return False

        # The day is in range. Now check the hours to make sure it's between the range
        hour = time.hour

        if not self.overnight \
            and self.stTime.hour <= hour <= self.endTime.hour: return True

        if self.overnight and (self.stTime.hour <= hour <= 24 \
                                or 1 <= hour <= self.endTime.hour): return True

        return False

    def __repr__(self):
        return "%s/%s to %s/%s between %s to %s"%\
            (self.stTime.month, self.stTime.day, \
             self.endTime.month, self.endTime.day, \
             self.stTime.hour, self.endTime.hour)

class LBHeader:
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

    def __init__(self, city = 'unknown', dataType = 'unknown', unit = 'unknown', frequency = 'unknown', analysisPeriod = None):
        """Initiate Ladybug header for lists."""
        self.city = city
        self.dataType = dataType
        self.unit = unit
        self.frequency = frequency
        self.analysisPeriod = 'unknown' if not analysisPeriod \
                else AnalysisPeriod.fromAnalysisPeriod(analysisPeriod)

    @property
    def __key(self):
        return 'location|dataType|units|frequency|dataPeriod'

    @property
    def toList(self):
        """Return Ladybug header as a list"""
        return [
                 self.__key,
                 self.city,
                 self.dataType,
                 self.unit,
                 self.frequency,
                 self.analysisPeriod
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

class LBData:
    """Ladybug data point"""

    # TODO: Change value to be an object from it's data type
    #       Check datatype.py for available datatypes

    def __init__(self, value, dateTime):
        self.datetime = dateTime
        self.value = value

    @classmethod
    def fromLBData(cls, data):
        if isinstance(data, LBData):
            return data
        else:
            raise ValueError

    def __repr__(self):
        return str(self.value)

class DataList:
    """Ladybug data list

        A list of ladybug data with a LBHeader
    """
    def __init__(self, data = None, header = None):

        self.__data = self.checkInputData(data)
        self.__header = LBHeader() if not header else header

    def checkInputData(self, data):
        """Check input data"""
        if not data: return []
        return [LBData.fromLBData(d) for d in data]

    def append(self, data):
        """Append LBData to current list"""
        self.extend([data])

    def extend(self, dataList):
        """Extend a list of LBData to the end of current list"""
        self.__data.extend(self.checkInputData(dataList))

    def updateValuesForAnAnalysisPeriod(self, values, AnalysisPeriod):
        raise NotImplemented

    def updateHourlyValues(self, values, hoursOfYear):
        raise NotImplemented

    def updateHourlyValue(self, value, hourOfYear):
        raise NotImplemented

    def filterByAnalysisPeriod(self):
        pass

    def filterByConditionalStatement(self):
        pass

    def filterByPattern(self):
        raise NotImplemented

    @property
    def averageMonthly(self):
        raise NotImplemented

    @property
    def averageWeekly(self):
        raise NotImplemented

    @property
    def averageForAnHourEveryMonth(self):
        raise NotImplemented

    @property
    def toList(self):
        return self.__header.toList + self.__data
