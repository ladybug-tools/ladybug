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
        self.epwHeader = None

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
        if not self.__isLocationLoaded:
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

        # TODO: create an object from the header and analyze data
        # get epw header
        self.epwHeader = epwlines[:9]

        # import hourly data
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

    def __get_dataByField(self, fieldNumber):
        """Return a data field by field number
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

        if not self.isDataLoaded: self.importData()
        return self.__data[fieldNumber]

    def save(self, filePath):
        """Save epw object as an epw file"""
        # check filePath

        # collect data

        # add header and data together

        # write them to a file
        raise NotImplementedError

    @classmethod
    def import_dataByField(cls, fieldNumber):
        """Return annual values for any fieldNumber in epw file.

        This is a useful method to get the values for fields that Ladybug currently
        doesn't import by default. You can find list of fields by typing EPWDataTypes.fields

        Args:
            fieldNumber: a value between 1 to 31 for different available epw fields.
                1 Year
                2 Month
                3 Day
                4 Hour
                5 Minute
                6 Dry Bulb Temperature
                7 Dew Point Temperature
                8 Relative Humidity
                9 Atmospheric Station Pressure
                10 Extraterrestrial Horizontal Radiation
                11 Extraterrestrial Direct Normal Radiation
                12 Horizontal Infrared Radiation Intensity
                13 Global Horizontal Radiation
                14 Direct Normal Radiation
                15 Diffuse Horizontal Radiation
                16 Global Horizontal Illuminance
                17 Direct Normal Illuminance
                18 Diffuse Horizontal Illuminance
                19 Zenith Luminance
                20 Wind Direction
                21 Wind Speed
                22 Total Sky Cover
                23 Opaque Sky Cover
                24 Visibility
                25 Ceiling Height
                26 Present Weather Observation
                27 Present Weather Codes
                28 Precipitable Water
                29 Aerosol Optical Depth
                30 Snow Depth
                31 Days Since Last Snowfall
        Returns:
            An annual Ladybug list
        """
        return cls.__get_dataByField(fieldNumber)

    @property
    def years(self):
        """Return years as a Ladybug Data List"""
        return self.__get_dataByField(1)

    @property
    def dryBulbTemperature(self):
        """Return annual Dry Bulb Temperature as a Ladybug Data List"""
        return self.__get_dataByField(6)

    @property
    def dewPointTemperature(self):
        """Return annual Dew Point Temperature as a Ladybug Data List"""
        return self.__get_dataByField(7)

    @property
    def relativeHumidity(self):
        """Return annual Relative Humidity as a Ladybug Data List"""
        return self.__get_dataByField(8)

    @property
    def atmosphericStationPressure(self):
        """Return annual Atmospheric Station Pressure as a Ladybug Data List"""
        return self.__get_dataByField(9)

    @property
    def extraterrestrialHorizontalRadiation(self):
        """Return annual Extraterrestrial Horizontal Radiation as a Ladybug Data List"""
        return self.__get_dataByField(6)

    @property
    def extraterrestrialDirectNormalRadiation(self):
        """Return annual Extraterrestrial Direct Normal Radiation as a Ladybug Data List"""
        return self.__get_dataByField(6)

    @property
    def horizontalInfraredRadiationIntensity(self):
        """Return annual Horizontal Infrared Radiation Intensity as a Ladybug Data List"""
        return self.__get_dataByField(6)

    @property
    def globalHorizontalRadiation(self):
        """Return annual Global Horizontal Radiation as a Ladybug Data List"""
        return self.__get_dataByField(13)

    @property
    def directNormalRadiation(self):
        """Return annual Direct Normal Radiation as a Ladybug Data List"""
        return self.__get_dataByField(14)

    @property
    def diffuseHorizontalRadiation(self):
        """Return annual Diffuse Horizontal Radiation as a Ladybug Data List"""
        return self.__get_dataByField(15)

    @property
    def globalHorizontalIlluminance(self):
        """Return annual Global Horizontal Illuminance as a Ladybug Data List"""
        return self.__get_dataByField(16)

    @property
    def directNormalIlluminance(self):
        """Return annual Direct Normal Illuminance as a Ladybug Data List"""
        return self.__get_dataByField(17)

    @property
    def diffuseHorizontalIlluminance(self):
        """Return annual Diffuse Horizontal Illuminance as a Ladybug Data List"""
        return self.__get_dataByField(18)

    @property
    def zenithLuminance(self):
        """Return annual Zenith Luminance as a Ladybug Data List"""
        return self.__get_dataByField(19)

    @property
    def windDirection(self):
        """Return annual Wind Direction as a Ladybug Data List"""
        return self.__get_dataByField(20)

    @property
    def windSpeed(self):
        """Return annual Wind Speed as a Ladybug Data List"""
        return self.__get_dataByField(21)

    @property
    def totalSkyCover(self):
        """Return annual Total Sky Cover as a Ladybug Data List"""
        return self.__get_dataByField(22)

    @property
    def opaqueSkyCover(self):
        """Return annual Opaque Sky Cover as a Ladybug Data List"""
        return self.__get_dataByField(23)

    @property
    def visibility(self):
        """Return annual Visibility as a Ladybug Data List"""
        return self.__get_dataByField(24)

    @property
    def ceilingHeight(self):
        """Return annual Ceiling Height as a Ladybug Data List"""
        return self.__get_dataByField(25)

    @property
    def presentWeatherObservation(self):
        """Return annual Present Weather Observation as a Ladybug Data List"""
        return self.__get_dataByField(26)

    @property
    def presentWeatherCodes(self):
        """Return annual Present Weather Codes as a Ladybug Data List"""
        return self.__get_dataByField(27)

    @property
    def precipitableWater(self):
        """Return annual Precipitable Water as a Ladybug Data List"""
        return self.__get_dataByField(28)

    @property
    def aerosolOpticalDepth(self):
        """Return annual Aerosol Optical Depth as a Ladybug Data List"""
        return self.__get_dataByField(29)

    @property
    def snowDepth(self):
        """Return annual Snow Depth as a Ladybug Data List"""
        return self.__get_dataByField(30)

    @property
    def daysSinceLastSnowfall(self):
        """Return annual Days Since Last Snow Fall as a Ladybug Data List"""
        return self.__get_dataByField(31)

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
    def fieldNumbers(cls):
        for key, value in cls.__fields.items():
            print key, value['name']

    @classmethod
    def fields(cls):
        """Return fields as a dictionary
            If you are looking for field numbers try fieldNumbers method instead
        """
        return cls.__fields

    @classmethod
    def get_fieldByNumber(cls, fieldNumber):
        """Return an EPWField based on field number
            1 Year
            2 Month
            3 Day
            4 Hour
            5 Minute
            6 Dry Bulb Temperature
            7 Dew Point Temperature
            8 Relative Humidity
            9 Atmospheric Station Pressure
            10 Extraterrestrial Horizontal Radiation
            11 Extraterrestrial Direct Normal Radiation
            12 Horizontal Infrared Radiation Intensity
            13 Global Horizontal Radiation
            14 Direct Normal Radiation
            15 Diffuse Horizontal Radiation
            16 Global Horizontal Illuminance
            17 Direct Normal Illuminance
            18 Diffuse Horizontal Illuminance
            19 Zenith Luminance
            20 Wind Direction
            21 Wind Speed
            22 Total Sky Cover
            23 Opaque Sky Cover
            24 Visibility
            25 Ceiling Height
            26 Present Weather Observation
            27 Present Weather Codes
            28 Precipitable Water
            29 Aerosol Optical Depth
            30 Snow Depth
            31 Days Since Last Snowfall
        """
        return cls.EPWField(cls.__fields[fieldNumber])
