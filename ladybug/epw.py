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
        return self.get_dataByField(6)


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

        analysisPeriod = core.AnalysisPeriod()
        fieldNumbers = [1] + range(6, 32) # 1 is year that data is collected
        for fieldNumber in fieldNumbers:
            # create header
            field = EPWDataTypes.get_fieldByNumber(fieldNumber)
            header = core.LBHeader(city = self.stationLocation.city, frequency ='Hourly', \
                    analysisPeriod = analysisPeriod, \
                    dataType = field.name, unit =field.units)

            # create an empty data list with the header
            self.__data[fieldNumber] = core.DataList(header =header)

        for line in epwlines[8:]:
            data = line.strip().split(',')
            year, month, day, hour = map(int, data[:4])
            # in an epw file year can be different for each month
            # since I'm using this timestamp as the key and will be using it for sorting
            # I'm setting it up to 2000 - the real year will be collected under modelYear
            timestamp = core.LBDateTime(month, day, hour)

            for fieldNumber in fieldNumbers:
                valueType = EPWDataTypes.get_fieldByNumber(fieldNumber).valueType
                value = map(valueType, [data[fieldNumber]])[0]
                self.__data[fieldNumber].append(core.LBData(value, timestamp))

        self.__isDataLoaded = True

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

    def get_dataByField(self, fieldNumber):
        if not self.isDataLoaded: self.importData()
        return self.__data[fieldNumber]

    @classmethod
    def import_dataByField(cls, fieldNumber):
        """Return annual values for any fieldNumber in epw file.

        This is a useful method to get the values for fields that Ladybug currently
        doesn't import by default. You can find list of fields by typing EPWDataTypes.fields

        Args:
            fieldNumber: a value between 1 to 31 for different available epw fields.

        Returns:
            An annual Ladybug list
        """
        # check input data
        if not 1 <= fieldNumber <= 31:
            raise ValueError("Field number should be between 1-31")

        return cls.get_dataByField(fieldNumber)

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
        1 : { 'name'  : 'Year',
                'type' : int
            },

        2 : { 'name'  : 'Month',
                'type' : int
            },

        3 : { 'name'  : 'Day',
                'type' : int
            },

        4 : { 'name'  : 'Hour',
                'type' : int
            },

        5 : { 'name'  : 'Minute',
                'type' : int
            },

        6 : { 'name'  : 'Dry Bulb Temperature',
                'type' : float,
                'units' : 'C',
                'min'   : -70,
                'max'   : 70
            },

        7 : { 'name' : 'Dew Point Temperature',
                'type' : float,
                'units' : 'C',
                'min' : -70,
                'max' : 70
            },

        8 : { 'name' : 'Relative Humidity',
                'type' : float,
                'missing' : 999,
                'min' : 0,
                'max' : 110
            },

        9 : { 'name' : 'Atmospheric Station Pressure',
                'type' : float,
                'units' : 'Pa',
                'missing' : 999999,
                'min' : 31000,
                'max' : 120000
            },

        10 : { 'name' : 'Extraterrestrial Horizontal Radiation',
                'type' : float,
                'units' : 'Wh/m2',
                'missing' :  9999
            },

        11 : { 'name' : 'Extraterrestrial Direct Normal Radiation',
                'type' : float,
                'units' :  'Wh/m2',
                'missing' : 9999
            },

        12 : { 'name' : 'Horizontal Infrared Radiation Intensity',
                'type' : float,
                'units' : 'Wh/m2',
                'missing' : 9999
            },

        13 : { 'name' : 'Global Horizontal Radiation',
                'type' : float,
                'units' : 'Wh/m2',
                'missing' : 9999
            },

        14 : { 'name' : 'Direct Normal Radiation',
                'type' : float,
                'units' : 'Wh/m2',
                'missing' : 9999,
                'min' : 0
            },

        15 : { 'name' : 'Diffuse Horizontal Radiation',
                'type' : float,
                'units' : 'Wh/m2',
                'missing' : 9999,
                'min' : 0
            },

        16 : { 'name' : 'Global Horizontal Illuminance',
                'type' : float,
                'units' : 'lux',
                'missing' : 999999
                # note will be missing if >= 999900
            },

        17 : { 'name' : 'Direct Normal Illuminance',
                'type' : float,
                'units' : 'lux',
                'missing' : 999999,
                # note will be missing if >= 999900
            },

        18 : { 'name' : 'Diffuse Horizontal Illuminance',
                'type' : float,
                'units' : 'lux',
                'missing' : 999999
                # note will be missing if >= 999900
            },

        19 : { 'name' : 'Zenith Luminance',
                'type' : float,
                'units' : 'Cd/m2',
                'missing' : 9999,
                # note will be missing if >= 9999
            },

        20 : { 'name' : 'Wind Direction',
                'type' : int,
                'units' : 'degrees',
                'missing' : 999,
                'min' : 0,
                'max' : 360
            },

        21 : { 'name' : 'Wind Speed',
                'type' : float,
                'units' : 'm/s',
                'missing' : 999,
                'min' : 0,
                'max' : 40
            },

        22 : { 'name' : 'Total Sky Cover', # (used if Horizontal IR Intensity missing)
                'type' : float,
                'missing' : 99
            },

        23 : { 'name' : 'Opaque Sky Cover', #(used if Horizontal IR Intensity missing)
                'type' : float,
                'missing' : 99
            },

        24 : { 'name' : 'Visibility',
                'type' : float,
                'units' : 'km',
                'missing' : 9999
            },

        25 : { 'name' : 'Ceiling Height',
                'type' : float,
                'units' : 'm',
                'missing' : 99999
            },

        26 : { 'name' : 'Present Weather Observation',
                'type' : str
            },

        27 : { 'name' : 'Present Weather Codes',
                'type' : str
            },

        28 : { 'name' : 'Precipitable Water',
                'type' : float,
                'units' : 'mm',
                'missing' : 999
            },

        29 : { 'name' : 'Aerosol Optical Depth',
                'type' : float,
                'units' : 'thousandths',
                'missing' : 999
            },

        30 : { 'name' : 'Snow Depth',
                'type' : float,
                'units' : 'cm',
                'missing' : 999
            },

        31 : { 'name' :  'Days Since Last Snowfall',
                'type' : int,
                'missing' : 99
            }
        }

    class EPWField:
        def __init__(self, dataDict):
            self.name = dataDict['name']
            self.valueType = dataDict['type']
            if 'units' in dataDict:
                self.units = dataDict['units']
            else:
                self.units = 'N/A'

    @classmethod
    def fields(cls):
        return cls.__fields

    @classmethod
    def get_fieldByNumber(cls, fieldNumber):
        """Return detailed field information based on field number"""
        return cls.EPWField(cls.fields()[fieldNumber])
