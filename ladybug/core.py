import re
import copy

class DateTimeLib:
    """Ladybug DateTime Libray
    This class includes useful data and methods for date and time
    """
    monthList = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    numOfDaysEachMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    numOfDaysUntilMonth = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]
    numOfHoursUntilMonth = [24 * numOfDay for numOfDay in numOfDaysUntilMonth]

    @classmethod
    def checkDateTime(cls, month, day, hour, minute = None):
        """Checks if time combination is a valid time."""
        # check month
        if not 1 <= month <= 12:
            raise ValueError("month should be between 1-12")

        if day < 1 or day > cls.numOfDaysEachMonth[month-1]:
            raise ValueError("Number of days for %s should be \
                    between 1-%d"%(cls.monthList[month-1], cls.numOfDaysEachMonth[month-1]))

        if not 0 <= hour <= 24:
            raise ValueError("hour should be between 0.0-24.0")

        if not minute or minute == 0:
            if hour == 0 and day == 1 and month == 1:
                # last hour of the year
                month = 12
                day = 31
                hour = 24

            elif hour == 0 and day == 1:
                # The last hour of the last day of the month before
                month -= 1
                day = cls.numOfDaysEachMonth[month-1]
                hour = 24

            elif hour==0:
                # the last hour of the day before
                hour = 24
                day -= 1

        hour, minute = cls.__getHourAndMinute(hour, minute)

        return month, day, hour, minute

    @classmethod
    def getHourOfYear(cls, month, day, hour, minute = None):
        """Return hour of the year between 1 and 8760."""
        # make sure input values are correct
        month, day, hour, minute = cls.checkDateTime(month, day, hour, minute)

        # fix the end day
        JD = cls.numOfDaysUntilMonth[month-1] + int(day)
        return (JD - 1) * 24 + hour

    @classmethod
    def getDayOfYear(cls, month, day):
        """Retuen day of the year between 1 and 365"""
        # make sure input values are correct
        month, day, hour, minute = cls.checkDateTime(month, day, hour = 1)

        # fix the end day
        return cls.numOfDaysUntilMonth[month-1] + int(day)

    @classmethod
    def getMonthDayHourAndMinute(cls, hourOfYear):
        """Return month, day and hour for an hour of the year"""
        if hourOfYear == 8760: return 12, 31, 24, 0

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
            minute = 0
        else:
            day = int((hourOfYear - cls.numOfHoursUntilMonth[month - 1])/24) + 1
            hour = int(hourOfYear%24)
            minute = cls.__getHourAndMinute(hourOfYear)[1]

        return month, day, hour, minute

    @staticmethod
    def __getHourAndMinute(hour, minute = None):

        """Calculate and return hour and minute

            This method is mainly usefule for calculating minutes from float hours
            if minute is missing. otherwise it will only check the inputs append
            returns the checked values

            Args:
                hour: A float value between 0.0-24.0
                minutes: An integer between 0-59. Default in None

            Returns:
                hour: An interger between 0-24
                minute: An integer between 0-59
        """
        if not minute:
            minute = (hour - int(hour)) * 60

        # cast values to integer
        hour = int(hour + int(minute/60))
        minute = minute%60

        return hour, minute

# TODO: add comparison methods (largerthan, smallerthan, ...)
class LBDateTime:
    """Ladybug Date time"""
    def __init__(self, month = 1, day = 1, hour = 1, minute = None):
        self.month, self.day, self.hour, \
            self.minute = DateTimeLib.checkDateTime(month, day, hour, minute)

        self.floatHour = self.hour + self.minute/60.0
        self.DOY = DateTimeLib.getDayOfYear(self.month, self.day)
        self.HOY = DateTimeLib.getHourOfYear(self.month, self.day, self.hour, self.minute)
        self.MOY = self.HOY * 60  + self.minute # minute of the year
        self.floatHOY = self.HOY + self.minute/60.0

    @classmethod
    def fromHOY(cls, HOY):
        """Create Ladybug Datetime from an hour of the year

            Args:
                HOY: A float value between 0.0 to 8760.0
        """
        month, day, hour, minute = DateTimeLib.getMonthDayHourAndMinute(HOY)
        return cls(month, day, hour, minute)

    @classmethod
    def fromMOY(cls, MOY):
        """create Ladybug DateTime from Minute of the year"""
        HOY = MOY/60.0
        return cls.fromHOY(HOY)

    @classmethod
    def fromDateTimeString(cls, datetimeString):
        day, month, hour, minute = datetimeString \
                .replace(" at ", " ") \
                .replace(":", " ") \
                .split(" ")

        month = DateTimeLib.monthList.index(month.upper()) + 1

        return cls(month, int(day), int(hour), int(minute))

    @property
    def humanReadableHour(self):
        """Return hours and minutes in a human readable way"""
        minute = str(self.minute)
        if len(minute) == 1: minute = "0" + minute
        return "%d:%s"%(self.hour, minute)

    def __repr__(self):
        return "%d %s at %s"%( self.day, DateTimeLib.monthList[self.month-1], self.humanReadableHour)


# TODO: Add NA analysis period
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
            timestep: An integer number from 1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60
    """

    __validTimesteps = {1 : 60, 2 : 30, 3 : 20, 4 : 15, 5 : 12, \
        6 : 10, 10 : 6, 12 : 5, 15 : 4, 20 : 3, 30 : 2, 60 : 1}

    #TODO: handle timestep between 1-60
    def __init__(self, stMonth = 1, stDay = 1, stHour = 1, endMonth = 12,
                endDay = 31, endHour = 24, timestep = 1):

        """Init an analysis period"""

        # calculate start time and end time
        self.stTime = LBDateTime(int(stMonth), int(stDay), float(stHour))
        self.endTime = LBDateTime(int(endMonth), int(endDay), float(endHour))

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

        # check time step
        if timestep not in self.__validTimesteps:
            raise ValueError("Invalid timestep. Valid values are %s"%str(self.__validTimesteps))

        # calculate time stamp
        self.timestep = timestep
        self.minuteIntervals = self.__validTimesteps[timestep]

        # calculate timestamps and hoursOfYear
        self.__timestampsData = {} # A dictionary for timedates. Key values will be minute of year
        self.__calculateTimestamps()

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

        # %s/%s to %s/%s between %s to %s @%s
        ap = analysisPeriodString.lower() \
                        .replace(' ', '') \
                        .replace('to', ' ') \
                        .replace('/', ' ') \
                        .replace('between', ' ') \
                        .replace('@', ' ')
        try:
            stMonth, stDay, \
            endMonth, endDay, \
            stHour, endHour, timestep =  ap.split(' ')
            return cls(stMonth, stDay, stHour, endMonth, endDay, endHour, int(timestep))
        except:
           raise ValueError(analysisPeriodString + " is not a valid analysis period!")

    def __calculateTimestamps(self):
        """Return a list of Ladybug DateTime in this analysis period."""

        # calculate based on minutes
        curr = self.stTime.MOY - 60 + self.minuteIntervals

        if not self.reversed:
            while curr <= self.endTime.MOY:
                time = LBDateTime.fromMOY(curr)
                if not self.isTimeIncluded(time):
                    self.__timestampsData[time.MOY] = time
                curr += self.minuteIntervals
        else:
            while (0 <= curr <= self.endTime.MOY or self.stTime.MOY <= curr < 8760 * 60):
                time = LBDateTime.fromMOY(curr)
                if not self.isTimeIncluded(time):
                    self.__timestampsData[time.MOY] = time

                curr = (curr + self.minuteIntervals)%(8760 * 60)

    @property
    def dates(self):
        """A sorted list of dates in this analysis period"""
        # sort dictionary based on key values (minute of the year)
        sortedTimestamps = sorted(self.__timestampsData.items(), key= lambda x: x[0])
        return [timestamp[1] for timestamp in sortedTimestamps]

    @property
    def  HOYs(self):
        """A sorted list of hours of year in this analysis period"""
        return [timestamp.HOY for timestamp in self.dates]

    @property
    def  floatHOYs(self):
        """A sorted list of hours of year as float values in this analysis period"""
        return [timestamp.floatHOY for timestamp in self.dates]

    @property
    def totalNumOfHours(self):
        """Total number of hours during this analysis period"""
        return len(self.__timestampsData)/self.timestep

    @property
    def isAnnual(self):
        """Check if an analysis period is annual"""
        return True if self.totalNumOfHours == 8760 else False

    def isTimeIncluded(self, time):
        """Check if time is included in analysis period.

            Return True if time is inside this analysis period,
            otherwise return False

            Args:
                time: A LBDateTime to be tested

            Returns:
                A boolean. True if time is included in analysis period
        """
        # time filtering in Ladybug and honeybee is slightly different since start hour and end hour will be
        # applied for every day. For instance 2/20 9am to 2/22 5pm means hour between 9-17 during 20, 21 and 22 of Feb
        return time.MOY in self.__timestampsData

    def __repr__(self):
        return "%s/%s to %s/%s between %s to %s @%d"%\
            (self.stTime.month, self.stTime.day, \
             self.endTime.month, self.endTime.day, \
             self.stTime.hour, self.endTime.hour, \
             self.timestep)

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

    def duplicate(self):
        return copy.deepcopy(self)

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

# TODO: write classes for latitude, longitude, etc
class Location:

    def __init__(self, city = '', country = '', latitude = '0.00', \
                longitude = '0.00', timeZone = '0.00', elevation ='0.00', \
                source = '', stationId = ''):

        self.city = str(city)
        self.country = str(country)
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.timeZone = float(timeZone)
        self.elevation = float(elevation)
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
            self.elevation = re.findall(r'\r*\n*([a-zA-Z0-9.:_-]*)[,|;]', \
                                    EPString, re.DOTALL)[1:]

            self.latitude = float(self.latitude)
            self.longitude = float(self.longitude)
            self.timeZone = float(self.timeZone)
            self.elevation = float(self.elevation)
        except Exception, e:
            raise Exception ("Failed to import EP string! %s"%str(e))

    def duplicate(self):
        return copy.deepcopy(self)

    @property
    def EPStyleLocationString(self):
        """Return EnergyPlus's location string"""
        return "Site:Location,\n" + \
            self.city + ',\n' + \
            str(self.latitude) +',      !Latitude\n' + \
            str(self.longitude) +',     !Longitude\n' + \
            str(self.timeZone) +',     !Time Zone\n' + \
            str(self.elevation) + ';       !Elevation'

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

    def updateValue(self, newValue):
        self.value = newValue

    def __repr__(self):
        return str(self.value)

class DataList:
    """Ladybug data list

        A list of ladybug data with a LBHeader
    """
    def __init__(self, data = None, header = None):
        self.__data = self.checkInputData(data)
        self.header = LBHeader() if not header else header

    @property
    def values(self):
        """Return the list of values"""
        return self.__data

    @property
    def timeStamps(self):
        "Return time stamps for current data"
        return [value.datetime for value in self.__data]

    @property
    def valuesWithHeader(self):
        """Return the list of values with ladybug header"""
        return self.header.toList + self.__data

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

    def duplicate(self):
        """Duplicate current data list"""
        return copy.deepcopy(self)

    @staticmethod
    def average(data):
        values = [value.value for value in data]
        return sum(values)/len(data)

    def separateDataByMonth(self, monthRange = range(1,13), userDataList = None):
        """Return a dictionary of values where values are separated for each month

            key values are between 1-12

           Parameters:
               monthRange: A list of numbers for months. Default is 1-12
               userDataList: An optional data list of LBData to be processed

           Usage:
               epwfile = EPW("epw file address")
               monthlyValues = epwfile.dryBulbTemperature.separateValuesByMonth()
               print monthlyValues[2] # returns values for the month of March
        """
        hourlyDataByMonth = {}
        if userDataList:
            data = [LBData.fromLBData(d) for d in userDataList]
        else:
            data = self.__data

        for d in data:
            if not d.datetime.month in monthRange: continue

            if not hourlyDataByMonth.has_key(d.datetime.month): hourlyDataByMonth[d.datetime.month] = [] #create an empty list for month

            hourlyDataByMonth[d.datetime.month].append(d)

        print "Found data for months " + str(hourlyDataByMonth.keys())
        return hourlyDataByMonth

    def separateDataByDay(self, dayRange = range(1, 366), userDataList = None):
        """Return a dictionary of values where values are separated by each day of year

            key values are between 1-365

           Parameters:
               dayRange: A list of numbers for days. Default is 1-365
               userDataList: An optional data list of LBData to be processed
           Usage:
               epwfile = EPW("epw file address")
               dailyValues = epwfile.dryBulbTemperature.separateDataByDay(range(1, 30))
               print dailyValues[2] # returns values for the second day of year
        """
        hourlyDataByDay = {}

        if userDataList:
            data = [LBData.fromLBData(d) for d in userDataList]
        else:
            data = self.__data

        for d in data:
            DOY = DateTimeLib.getDayOfYear(d.datetime.month, d.datetime.day)

            if not DOY in dayRange: continue

            if not hourlyDataByDay.has_key(DOY): hourlyDataByDay[DOY] = [] #create an empty list for month

            hourlyDataByDay[DOY].append(d)

        print "Found data for " + str(len(hourlyDataByDay.keys())) + " days."
        return hourlyDataByDay

    def separateDataByHour(self, hourRange = range(1, 25), userDataList = None):
        """Return a dictionary of values where values are separated by each hour of day

            key values are between 1-24

           Parameters:
               hourRange: A list of numbers for hours. Default is 1-24
               userDataList: An optional data list of LBData to be processed

           Usage:
               epwfile = EPW("epw file address")
               monthlyValues = epwfile.dryBulbTemperature.separateDataByMonth([1])
               separatedHourlyData = epwfile.dryBulbTemperature.separateDataByHour(userDataList = monthlyValues[2])
               for hour, data in separatedHourlyData.items():
                   print "average temperature values for hour " + str(hour) + " during JAN is " + str(core.DataList.average(data)) + " " + DBT.header.unit
        """
        hourlyDataByHour = {}

        if userDataList:
            data = [LBData.fromLBData(d) for d in userDataList]
        else:
            data = self.__data

        for d in data:

            if not d.datetime.hour in hourRange: continue

            if not hourlyDataByHour.has_key(d.datetime.hour): hourlyDataByHour[d.datetime.hour] = [] #create an empty list for month

            hourlyDataByHour[d.datetime.hour].append(d)

        print "Found data for hours " + str(hourlyDataByHour.keys())
        return hourlyDataByHour

    # TODO: Add validity check for input values
    def updateDataForAnAnalysisPeriod(self, values, analysisPeriod = None):
        """Replace current values in data list with new set of values
            for a specific analysis period.

            Length of values should be equal to number of hours in analysis period

            Parameters:
                values: A list of values to be replaced in the file
                analysisPeriod: An analysis period for input the input values.
                    Default is set to the whole year.
        """
        if not analysisPeriod:
            analysisPeriod = AnalysisPeriod()

        # check length of data vs length of analysis period
        if len(values) != analysisPeriod.totalNumOfHours:
            raise ValueError("Length of values %d is not equal to " + \
                "number of hours in analysis period %d"%(len(values), \
                                                        analysisPeriod.totalNumOfHours))
        # get all time stamps
        timeStamps = analysisPeriod.dates

        # map timeStamps and values
        newValues = {}
        for count, value in enumerate(values):
            HOY = timeStamps[count].HOY
            newValues[HOY] = value

        # update values
        updatedCount = 0
        for counter, data in enumerate(self.__data):
            try:
                value = newValues[data.datetime.HOY]
                data.updateValue(value)
                updatedCount+=1
            except KeyError:
                pass

        # return self for chaining methods
        print "%s data are updated for %d hours."%(self.header.dataType, updatedCount)
        # return self for chaining methods
        return self

    def updateDataForHoursOfYear(self, values, hoursOfYear):
        """Replace current values in data list with new set of values
            for a list of hours of year

            Length of values should be equal to number of hours in hours of year

            Parameters:
                values: A list of values to be replaced in the file
                hoursOfYear: A list of HOY between 1 and 8760
        """
        # check length of data vs length of analysis period
        if len(values) != len(hoursOfYear):
            raise ValueError("Length of values %d is not equal to " + \
                "number of hours in analysis period %d"%(len(values), \
                                                        len(hoursOfYear)))

        # map hours and values
        newValues = {}
        for count, value in enumerate(values):
            HOY = hoursOfYear[count]
            newValues[HOY] = value

        # update values
        updatedCount = 0
        for counter, data in enumerate(self.__data):
            try:
                value = newValues[data.datetime.HOY]
                data.updateValue(value)
                updatedCount+=1
            except KeyError:
                pass

        print "%s data %s updated for %d hour%s."%(self.header.dataType, \
                'are' if len(values)>1 else 'is', updatedCount,\
                's' if len(values)>1 else '')

        # return self for chaining methods
        return self

    def updateDataForAnHour(self, value, hourOfYear):
        """Replace current value in data list with a new value
            for a specific hour of the year

            Parameters:
                value: A single value
                hoursOfYear: The hour of the year
        """
        return self.updateDataForHoursOfYear([value], [hourOfYear])

    def filterByAnalysisPeriod(self, analysisPeriod):

        """Filter the list based on an analysis period
            Parameters:
               analysis period: A Ladybug analysis period

            Return:
                A new DataList with filtered data

            Usage:
               analysisPeriod = AnalysisPeriod(2,1,1,3,31,24) #start of Feb to end of Mar
               epw = EPW("c:\ladybug\weatherdata.epw")
               DBT = epw.dryBulbTemperature
               filteredDBT = DBT.filterByAnalysisPeriod(analysisPeriod)
        """
        if not analysisPeriod or analysisPeriod.isAnnual:
            print "You need a valid analysis period to filter data."
            return self

        # There is no guarantee that data is continuous so I iterate through the
        # each data point one by one
        filteredData = [ d for d in self.__data if analysisPeriod.isTimeIncluded(d.datetime)]

        # create a new filteredData
        filteredHeader = self.header.duplicate()
        filteredHeader.analysisPeriod = analysisPeriod
        filteredDataList = DataList(filteredData, filteredHeader)

        return filteredDataList

    def filterByConditionalStatement(self, statement):
        """Filter the list based on an analysis period
            Parameters:
               statement: A conditional statement as a string (e.g. x>25 and x%5==0).
                The variable should always be named as x

            Return:
                A new DataList with filtered data

            Usage:
               epw = EPW("c:\ladybug\weatherdata.epw")
               DBT = epw.dryBulbTemperature
               # filter data for when dry bulb temperature is more then 25
               filteredDBT = DBT.filterByConditionalStatement('x > 25')
               # get the list of time stamps that meet the conditional statement
               print filteredDBT.timeStamps
        """

        def checkInputStatement(statement):
            stStatement = statement.lower().replace("and", "").replace("or", "")\
                    .replace("not", "").replace("in", "").replace("is", "")

            l = [s for s in stStatement if s.isalpha()]
            if list(set(l)) != ['x']:
                statementErrorMsg = 'Invalid input statement. Statement should be a valid Python statement' + \
                    ' and the variable should be named as x'
                raise ValueError(statementErrorMsg)

        checkInputStatement(statement)

        statement = statement.replace('x', 'd.value')
        filteredData = [d for d in self.__data if eval(statement)]

        # create a new filteredData
        filteredHeader = self.header.duplicate()
        filteredHeader.analysisPeriod = 'N/A'
        filteredDataList = DataList(filteredData, filteredHeader)

        return filteredDataList

    def filterByPattern(self, patternList):
        """Filter the list based on a list of Boolean

            Length of Boolean should be equal to length of values in DataList

            Parameters:
                patternList: A list of True, False values

            Return:
                A new DataList with filtered data
        """
        # check length of data vs length of analysis period
        if len(self.values) != len(patternList):
            print len(self.values), len(patternList)
            errMsg = "Length of values %d is not equal to number of patterns %d" \
                    %(len(self.values), len(patternList))
            raise ValueError(errMsg)

        filteredData = [d for count, d in enumerate(self.__data) if patternList[count]]

        # create a new filteredData
        filteredHeader = self.header.duplicate()
        filteredHeader.analysisPeriod = 'N/A'
        filteredDataList = DataList(filteredData, filteredHeader)

        return filteredDataList

    def averageMonthly(self, userDataList = None):
        """Return a dictionary of values for average values for available months"""

        # separate data for each month
        monthlyValues = self.separateDataByMonth(userDataList= userDataList)

        averageValues = dict()

        # average values for each month
        for month, values in monthlyValues.items():
            averageValues[month] = self.average(values)

        return averageValues

    def averageMonthlyForEachHour(self, userDataList = None):
        """Calculate average value for each hour during each month

            This method returns a dictionary with nested dictionaries for each hour
        """
        # get monthy values
        monthlyHourlyValues = self.separateDataByMonth(userDataList= userDataList)

        # separate data for each hour in each month and collect them in a dictionary
        averagedMonthlyValuesPerHour = {}
        for month, monthlyValues in monthlyHourlyValues.items():
            if month not in averagedMonthlyValuesPerHour: averagedMonthlyValuesPerHour[month] = {}

            # separate data for each hour
            separatedHourlyData = self.separateDataByHour(userDataList = monthlyValues)
            for hour, data in separatedHourlyData.items():
                averagedMonthlyValuesPerHour[month][hour] = self.average(data)

        return averagedMonthlyValuesPerHour
