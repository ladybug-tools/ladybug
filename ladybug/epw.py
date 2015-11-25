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
        self.__isDataLoaded = False
        self.__isLocationLoaded = False
        self.__data = dict()

    @property
    def isDataLoaded(self):
        return self.__isDataLoaded

    @property
    def isLocationLoaded(self):
        return self.__isLocationLoaded

    @staticmethod
    def checkEpwFileAddress(epwFileAddress):
        """ Checks the path and checks the type for an epw file"""
        if not os.path.isfile(epwFileAddress):
            raise Exception(epwFileAddress + ' is not a valid address.')
        if not epwFileAddress.lower().endswith('epw'):
            raise Exception(epwFileAddress + ' is not an .epw file.')
        return epwFileAddress

    @property
    def location(self):
        if not self.isLocationLoaded: self.importData(True)
        return self.stationLocation

    @property
    def dryBulbTemperature(self):
        """Return annaual Dry Bulb Temperature as a Ladybug Data List"""
        if not self.isDataLoaded: self.importData()
        return self.get_dataByField[6]


    #TODO: import EPW header. Currently I just ignore header data
    def importData(self, onlyImportLocation = False):
        """
        imports data from an epw file.
        Hourly data will be saved in self.data and location data
        will be saved in self.location
        """

        with open(self.fileAddress, 'rb') as epwin:
            epwlines = epwin.readlines()

        # import location data
        # first line has location data - Here is an example
        # LOCATION,Denver Centennial  Golden   Nr,CO,USA,TMY3,724666,39.74,-105.18,-7.0,1829.0
        locationData = epwlines[0].strip().split(',')
        self.stationLocation = core.Location()
        self.stationLocation.city = locationData[1]
        self.stationLocation.state = locationData[2]
        self.stationLocation.country = locationData[3]
        self.stationLocation.source = locationData[4]
        self.stationLocation.stationId = locationData[5]
        self.stationLocation.latitude = locationData[6]
        self.stationLocation.longitude = locationData[7]
        self.stationLocation.timeZone = locationData[8]
        self.stationLocation.elevation = locationData[9]

        self.__isLocationLoaded = True

        if onlyImportLocation: return

        # import hourly data
        # TODO: create empty Ladybug data list for all the fields
        # TODO: clean and modify methods - some of the methods will be moved to DataList

        # create generic header

        for line in epwlines[8:]:
            data = line.strip().split(',')
            year, month, day, hour = map(int, data[:4])
            # in an epw file year can be different for each month
            # since I'm using this timestamp as the key and will be using it for sorting
            # I'm setting it up to 2000 - the real year will be collected under modelYear
            timestamp = core.LBDateTime(month, day, hour)
            self.data[timestamp]['modelYear'] = year
            try:
                self.__data[6] = core.DataList()
                self.__data[6] = core.LBData(float(data[6]), timestamp)
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

        self.__isDataLoaded = True

        self.sortedTimestamps = sorted(self.data.keys())

    # TODO: This should move under Ladybug data list
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
            header = core.Header(self.stationLocation.city, dataType, \
                        self.keys[dataType]['unit'], "Hourly", analysisPeriod)

            header = header.toList

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
            header = core.Header(self.stationLocation.city, dataType, \
                        self.keys[dataType]['unit'], "Hourly", analysisPeriod)

            header = header.toList

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

        return hourlyData

    @classmethod
    def get_fieldInfo(cls,fieldNumber):
        """Return full name and base type for field number"""
        # TODO copy data from DataPoints to this file
        # TODO finish base class types for Radiation, etc
        raise NotImplementedError

    def __repr__(self):
        return "EPW Data [%s]"%self.stationLocation.city

class EPWDataTypes:
    """EPW weather file fields"""

    __fields = {
        1 : { 'name'  : 'Year'
            },

        2 : { 'name'  : 'Month'
            },

        3 : { 'name'  : 'Day'
            },

        4 : { 'name'  : 'Hour'
            },

        5 : { 'name'  : 'Minute'
            },

        6 : { 'name'  : 'Dry Bulb Temperature',
                'units' : 'C',
                'min'   : -70,
                'max'   : 70
            },

        7 : { 'name' : 'Dew Point Temperature',
                'units' : 'C',
                'min' : -70,
                'max' : 70
            },

        8 : { 'name' : 'Relative Humidity',
                'missing' : 999,
                'min' : 0,
                'max' : 110
            },

        9 : { 'name' : 'Atmospheric Station Pressure',
                'units' : 'Pa',
                'missing' : 999999,
                'min' : 31000,
                'max' : 120000
            },

        10 : { 'name' : 'Extraterrestrial Horizontal Radiation',
             'units' : 'Wh/m2',
             'missing' :  9999
            },

        11 : { 'name' : 'Extraterrestrial Direct Normal Radiation',
             'units' :  'Wh/m2',
             'missing' : 9999
            },

        12 : { 'name' : 'Horizontal Infrared Radiation Intensity',
             'units' : 'Wh/m2',
             'missing' : 9999
            },

        13 : { 'name' : 'Global Horizontal Radiation',
             'units' : 'Wh/m2',
             'missing' : 9999
            },

        14 : { 'name' : 'Direct Normal Radiation',
             'units' : 'Wh/m2',
             'missing' : 9999,
             'min' : 0
            },

        15 : { 'name' : 'Diffuse Horizontal Radiation',
             'units' : 'Wh/m2',
             'missing' : 9999,
             'min' : 0
            },

        16 : { 'name' : 'Global Horizontal Illuminance',
             'units' : 'lux',
             'missing' : 999999
             # note will be missing if >= 999900
            },

        17 : { 'name' : 'Direct Normal Illuminance',
             'units' : 'lux',
             'missing' : 999999,
             # note will be missing if >= 999900
            },

        18 : { 'name' : 'Diffuse Horizontal Illuminance',
             'units' : 'lux',
             'missing' : 999999
             # note will be missing if >= 999900
            },

        19 : { 'name' : 'Zenith Luminance',
             'units' : 'Cd/m2',
             'missing' : 9999,
             # note will be missing if >= 9999
            },

        20 : { 'name' : 'Wind Direction',
             'units' : 'degrees',
             'missing' : 999,
             'min' : 0,
             'max' : 360
            },

        21 : { 'name' : 'Wind Speed',
             'units' : 'm/s',
             'missing' : 999,
             'min' : 0,
             'max' : 40
            },

        22 : { 'name' : 'Total Sky Cover', # (used if Horizontal IR Intensity missing)
             'missing' : 99
            },

        23 : { 'name' : 'Opaque Sky Cover', #(used if Horizontal IR Intensity missing)
             'missing' : 99
            },

        24 : { 'name' : 'Visibility',
             'units' : 'km',
             'missing' : 9999
            },

        25 : { 'name' : 'Ceiling Height',
             'units' : 'm',
             'missing' : 99999
            },

        26 : { 'name' : 'Present Weather Observation'
            },

        27 : { 'name' : 'Present Weather Codes'
            },

        28 : { 'name' : 'Precipitable Water',
             'units' : 'mm',
             'missing' : 999
            },

        29 : { 'name' : 'Aerosol Optical Depth',
             'units' : 'thousandths',
             'missing' : 999
            },

        30 : { 'name' : 'Snow Depth',
             'units' : 'cm',
             'missing' : 999
            },

        31 : { 'name' :  'Days Since Last Snowfall',
             'missing' : 99
            }
        }

    @classmethod
    def get_fieldByNumber(cls, fieldNumber):
        """Return detailed field information based on field number"""
        pass
