import os
import datetime
import core

class EPW:
    def __init__(self, epwFileAddress = None):
        """
        Import epw data from a local epw file

        epwFileAddress: Local file address to an epw file

        """
        if not epwFileAddress: return

        self.fileAddress = self.checkEpwFileAddress(epwFileAddress)

        self.location = core.Location()

        # data will be collected under
        # 'timestamp': {'dbTemp': 25, 'RH': 80, ...},
        # 'timestamp': {'dbTemp': 26, 'RH': 75, ...},
        self.data = dict()

        self.year = 2000
        self.sortedTimestamps = [] # place holder for sorted time stamps

        self.importEpw() #import location and data

    @staticmethod
    def checkEpwFileAddress(epwFileAddress):
        """ Checks the path and checks the type for an epw file"""
        if not os.path.isfile(epwFileAddress):
            raise Exception(epwFileAddress + ' is not a valid address.')
        if not epwFileAddress.endswith('epw'):
            raise Exception(epwFileAddress + ' is not an .epw file.')
        return epwFileAddress

    def importEpw(self):
        """
        imports data from am epw file.
        Hourly data will be saved in self.data and location data
        will be saved in self.location
        """

        with open(self.fileAddress, 'rb') as epwin:
            epwlines = epwin.readlines()

        # import location data
        # first line has location data - Here is an example
        # LOCATION,Denver Centennial  Golden   Nr,CO,USA,TMY3,724666,39.74,-105.18,-7.0,1829.0
        locationData = epwlines[0].strip().split(',')
        self.location.city = locationData[1]
        self.location.state = locationData[2]
        self.location.country = locationData[3]
        self.location.source = locationData[4]
        self.location.stationId = locationData[5]
        self.location.latitude = locationData[6]
        self.location.longitude = locationData[7]
        self.location.timeZone = locationData[8]
        self.location.elevation = locationData[9]

        # import hourly data
        for line in epwlines[8:]:
            data = line.strip().split(',')
            year, month, day, hour = map(int, data[:4])
            # in an epw file year can be different for each month
            # since I'm using this timestamp as the key and will be using it for sorting
            # I'm setting it up to 2000 - the real year will be collected under modelYear
            timestamp = datetime.datetime(self.year, month, day, hour-1)
            self.data[timestamp] = dict()
            self.data[timestamp]['modelYear'] = year
            try:
                self.data[timestamp]['dbTemp'] = float(data[6])
                self.data[timestamp]['dewPoint'] = float(data[7])
                self.data[timestamp]['RH'] = float(data[8])
                self.data[timestamp]['windSpeed'] = float(data[21])
                self.data[timestamp]['windDir'] = float(data[20])
                self.data[timestamp]['dirRad'] = float(data[14])
                self.data[timestamp]['difRad'] = float(data[15])
                self.data[timestamp]['glbRad'] = float(data[13])
                self.data[timestamp]['dirIll'] = float(data[17])
                self.data[timestamp]['difIll' ] = float(data[18])
                self.data[timestamp]['glbIll'] = float(data[16])
                self.data[timestamp]['cloudCov'] = int(data[22])
                self.data[timestamp]['rainDepth'] = float(data[33])
                self.data[timestamp]['barPress'] = float(data[9])
            except:
                raise Exception("Failed to import data for " + str(timestamp))

        self.sortedTimestamps = sorted(self.data.keys())

    def get_dataByTime(self, month, day, hour, dataType = None):
        """
        Get weather data for a specific hour of the year for a specific data type (e.g. dbTemp, RH)
        If no type is provided all the available data will be returned
        """
        time = datetime.datetime(self.year, month, day, hour-1)

        # if it's a valid key return data for the key
        # otherwise return all the data available for that time
        if dataType in self.keys.keys(): return self.data[time][dataType]
        return self.data[time]

    def get_annualHourlyData(self, dataType, includeHeader = True):
        """Returns a list of values for annual hourly data for a specific data type

           Parameters:
               data Type: Any of the available dataTypes in self.keys
               includeHeader: Set to True to have Ladybug Header added at the start of list

           Usage:
               epw = EPW("epw file address"")
               epw.get_annualHourlyData("RH", True)
        """

        if dataType not in self.keys.keys():
            raise Exception(dataType + " is not a valid key" + \
                           "check self.keys for valid keys")
        header = []
        if includeHeader:
            header = LadybugHeader(self.location.city, dataType, \
                        self.keys[dataType]['unit'], "Hourly", analysisPeriod)

            header = header.toList()

        return header + [self.data[time][dataType] for time in self.sortedTimestamps]

    def get_hourlyDataByAnalysisPeriod(self, dataType, analysisPeriod, includeHeader = True):

        """Returns a list of values for the analysis period for a specific data type

           Parameters:
               data Type: Any of the available dataTypes in self.keys
               analysis period: A Ladybug analysis period
               includeHeader: Set to True to have Ladybug Header added at the start of list

           Usage:
               analysisPeriod = AnalysisPeriod(2,1,1,3,31,24) #start of Feb to end of Mar
               epw = EPW("epw file address")
               epw.get_annualHourlyData("dbTemp", analysisPeriod, True)

        """

        if dataType not in self.keys.keys():
            raise Exception(dataType + " is not a valid key" + \
                           "check self.keys for valid keys")
        header = []
        if includeHeader:
            header = LadybugHeader(self.location.city, dataType, \
                        self.keys[dataType]['unit'], "Hourly", analysisPeriod)

            header = header.toList()

        # Find the index for start to end of analysis period
        stInd = self.sortedTimestamps.index(analysisPeriod.stTime)
        endInd = self.sortedTimestamps.index(analysisPeriod.endTime)

        if analysisPeriod.reversed:
            timestamprange = self.sortedTimestamps[stInd:] + self.sortedTimestamps[:endInd + 1]
        else:
            timestamprange = self.sortedTimestamps[stInd:endInd + 1]

        return header + [self.data[time][dataType] for time in timestamprange if analysisPeriod.isTimeIncluded(time)]

    def get_hourlyDataByMonths(self, dataType = None, monthRange = range(1,13)):
        """Returns dictionary of values for a specific data type separated in months

           Parameters:
               dataType:
               monthRange: A list of numbers for months. Default is all the 12 months

           Usage:
               epwfile = EPW("epw file address")
               epwfile.get_hourlyDataByMonth("RH") # return values for relative humidity for 12 months
               epwfile.get_hourlyDataByMonth("dbTemp", [1,6,10]) # return values for dry bulb for Jan, Jun and Oct

        """
        hourlyDataByMonth = {}
        for time in self.sortedTimestamps:

            if not time.month in monthRange: continue

            if not hourlyDataByMonth.has_key(time.month): hourlyDataByMonth[time.month] = [] #create an empty list for month

            if dataType in self.keys.keys():
                hourlyDataByMonth[time.month].append(self.data[time][dataType])
            else:
                hourlyDataByMonth[time.month].append(self.data[time])

        return hourlyDataByMonth

    @classmethod
    def get_dataByField(cls, epwFileAddress, fieldNumber):
        """Return annual values for any fieldNumber in epw file.

        This is a useful method to get the values for fields that Ladybug currently
        doesn't import by default. For full list of field numbers check EnergyPlus Auxilary Programs

        Args:
            epwFile: Filepath to local epw file
            fieldNumber: a value between 1 to 31 for different available epw fields.

        Returns:
            A list of 8760 values as string

        TODO: Return should be changed to Ladybug list object
        """

        # check input data
        cls.checkEpwFileAddress(epwFileAddress)
        if not 0 < fieldNumber < 32:
            raise ValueError("Field number should be between 1-31")

        hourlyData = range(8760)
        with open(epwFileAddress, 'rb') as epwin:
            epwlines = epwin.readlines()

        for HOY, line in enumerate(epwlines[8:]):
            hourlyData[HOY] = line.strip().split(',')[fieldNumber]

        return data

    @classmethod
    def get_fieldInfo(cls,fieldNumber):
        """Return full name and base type for field number"""
        # TODO copy data from DataPoints to this file
        # TODO finish base class types for Radiation, etc
        raise NotImplementedError

    def __repr__(self):
        return "EPW Data [%s]"%self.location.city
