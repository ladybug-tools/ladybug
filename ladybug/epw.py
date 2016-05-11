import os
import core

class EPW:
    def __init__(self, epwFileAddress=None):
        """
        Import epw data from a local epw file.

        epwFileAddress: Local file address to an epw file

        """
        if not epwFileAddress:
            return
        self.fileAddress = self.checkEpwFileAddress(epwFileAddress)
        self.filePath, self.fileName = os.path.split(self.fileAddress)
        self.__isDataLoaded = False
        self.__isLocationLoaded = False
        self.__data = dict()
        self.epwHeader = None
        self.numOfFields = 35  # it is 35 for TMY3 files

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
        if not self.isLocationLoaded:
            self.importData(True)
        return self.stationLocation

    # TODO: import EPW header. Currently I just ignore header data
    def importData(self, onlyImportLocation=False):
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
            self.stationLocation.latitude = float(locationData[6])
            self.stationLocation.longitude = float(locationData[7])
            self.stationLocation.timeZone = float(locationData[8])
            self.stationLocation.elevation = float(locationData[9])

            self.__isLocationLoaded = True

        if onlyImportLocation:
            return

        # TODO: create an object from the header and analyze data
        # get epw header
        self.epwHeader = epwlines[:8]

        self.numOfFields = len(epwlines[8].strip().split(','))
        # import hourly data
        analysisPeriod = core.AnalysisPeriod()
        for fieldNumber in range(0, self.numOfFields):
            # create header
            field = EPWDataTypes.get_fieldByNumber(fieldNumber)
            header = core.LBHeader(city=self.stationLocation.city,
                                   frequency='Hourly',
                                   analysisPeriod=analysisPeriod,
                                   dataType=field.name, unit=field.units)

            # create an empty data list with the header
            self.__data[fieldNumber] = core.DataList(header =header)

        for line in epwlines[8:]:
            data = line.strip().split(',')

            year, month, day, hour = map(int, data[:4])
            # in an epw file year can be different for each month
            # since I'm using this timestamp as the key and will be using it for sorting
            # I'm setting it up to 2000 - the real year will be collected under modelYear
            timestamp = core.LBDateTime(month, day, hour)

            for fieldNumber in range(0, self.numOfFields):
                valueType = EPWDataTypes.get_fieldByNumber(fieldNumber).valueType
                value = map(valueType, [data[fieldNumber]])[0]
                self.__data[fieldNumber].append(core.LBData(value, timestamp))

        del(epwlines)
        self.__isDataLoaded = True

    def __get_dataByField(self, fieldNumber):
        """Return a data field by field number.

        This is a useful method to get the values for fields that Ladybug currently
        doesn't import by default. You can find list of fields by typing EPWDataTypes.fields

        Args:
            fieldNumber: a value between 0 to 34 for different available epw fields.

        Returns:
            An annual Ladybug list
        """
        if not self.isDataLoaded:
            self.importData()

        # check input data
        if not 0 <= fieldNumber < self.numOfFields:
            raise ValueError("Field number should be between 0-%d" % self.numOfFields)

        return self.__data[fieldNumber]

    # TODO: Add utility library to check file path, filename, etc
    def save(self, filePath=None, fileName=None):
        """Save epw object as an epw file."""
        # check filePath
        if not filePath:
            filePath = self.filePath

        if not fileName:
            fileName = ".".join((self.fileName).split(".")[:-1]) + "_modified.epw"

        fullPath = os.path.join(filePath, fileName)

        # load data if it's  not loaded
        if not self.isDataLoaded:
            self.importData()

        # write the file
        with open(fullPath, 'wb') as modEpwFile:
            modEpwFile.writelines(self.epwHeader)
            lines = []
            try:
                for hour in xrange(0, 8760):
                    line = []
                    for field in range(0, self.numOfFields):
                        line.append(str(self.__data[field].values[hour].value))
                    lines.append(",".join(line) + "\n")
            except IndexError:
                # cleaning up
                modEpwFile.close()
                lengthErrorMsg = "Data length is not 8760 hours! Data can't be saved to epw file. " + \
                    "Did you filtered the data by AnalysisPeriod or by ConditionalStatment?"
                raise ValueError(lengthErrorMsg)
            else:
                modEpwFile.writelines(lines)
            finally:
                del(lines)

        print "New epw file is written to [%s]" % fullPath

    def import_dataByField(self, fieldNumber):
        """Return annual values for any fieldNumber in epw file.

        This is a useful method to get the values for fields that Ladybug currently
        doesn't import by default. You can find list of fields by typing EPWDataTypes.fields

        Args:
            fieldNumber: a value between 0 to 34 for different available epw fields.
            0 Year
            1 Month
            2 Day
            3 Hour
            4 Minute
            -
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
            32 Albedo
            33 Liquid Precipitation Depth
            34 Liquid Precipitation Quantity
        Returns:
            An annual Ladybug list
        """
        return self.__get_dataByField(fieldNumber)

    @property
    def years(self):
        """Return years as a Ladybug Data List."""
        return self.__get_dataByField(0)

    @property
    def dryBulbTemperature(self):
        """Return annual Dry Bulb Temperature as a Ladybug Data List.

        This is the dry bulb temperature in C at the time indicated. Note that
        this is a full numeric field (i.e. 23.6) and not an integer representation
        with tenths. Valid values range from -70C to 70 C. Missing value for this
        field is 99.9

        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs
            /pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self.__get_dataByField(6)

    @property
    def dewPointTemperature(self):
        """Return annual Dew Point Temperature as a Ladybug Data List.

        This is the dew point temperature in C at the time indicated. Note that this is a full numeric field (i.e. 23.6) and not an integer representation with tenths. Valid values range from -70 C to 70 C. Missing value for this field is 99.9
        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self.__get_dataByField(7)

    @property
    def relativeHumidity(self):
        """Return annual Relative Humidity as a Ladybug Data List.

        This is the Relative Humidity in percent at the time indicated. Valid values range from 0% to 110%. Missing value for this field is 999.
        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self.__get_dataByField(8)

    @property
    def atmosphericStationPressure(self):
        """Return annual Atmospheric Station Pressure as a Ladybug Data List.

        This is the station pressure in Pa at the time indicated. Valid values range from 31,000 to 120,000. (These values were chosen from the standard barometric pressure for all elevations of the World). Missing value for this field is 999999.
        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self.__get_dataByField(9)

    @property
    def extraterrestrialHorizontalRadiation(self):
        """Return annual Extraterrestrial Horizontal Radiation as a Ladybug Data List.

        This is the Extraterrestrial Horizontal Radiation in Wh/m2. It is not currently used in EnergyPlus calculations. It should have a minimum value of 0; missing value for this field is 9999
        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self.__get_dataByField(10)

    @property
    def extraterrestrialDirectNormalRadiation(self):
        """Return annual Extraterrestrial Direct Normal Radiation as a Ladybug Data List.

        This is the Extraterrestrial Direct Normal Radiation in Wh/m2. (Amount of solar radiation in Wh/m2 received on a surface normal to the rays of the sun at the top of the atmosphere during the number of minutes preceding the time indicated). It is not currently used in EnergyPlus calculations. It should have a minimum value of 0; missing value for this field is 9999.
        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self.__get_dataByField(11)

    @property
    def horizontalInfraredRadiationIntensity(self):
        """Return annual Horizontal Infrared Radiation Intensity as a Ladybug Data List.

        This is the Horizontal Infrared Radiation Intensity in Wh/m2. If it is missing, it is calculated from the Opaque Sky Cover field as shown in the following explanation. It should have a minimum value of 0; missing value for this field is 9999.
        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self.__get_dataByField(12)

    @property
    def globalHorizontalRadiation(self):
        """Return annual Global Horizontal Radiation as a Ladybug Data List.

        This is the Global Horizontal Radiation in Wh/m2. (Total amount of direct and diffuse solar radiation in Wh/m2 received on a horizontal surface during the number of minutes preceding the time indicated.) It is not currently used in EnergyPlus calculations. It should have a minimum value of 0; missing value for this field is 9999.
        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self.__get_dataByField(13)

    @property
    def directNormalRadiation(self):
        """Return annual Direct Normal Radiation as a Ladybug Data List.

        This is the Direct Normal Radiation in Wh/m2. (Amount of solar radiation in Wh/m2 received directly from the solar disk on a surface perpendicular to the sun's rays, during the number of minutes preceding the time indicated.) If the field is missing ( >= 9999) or invalid ( < 0), it is set to 0. Counts of such missing values are totaled and presented at the end of the runperiod.
        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self.__get_dataByField(14)

    @property
    def diffuseHorizontalRadiation(self):
        """Return annual Diffuse Horizontal Radiation as a Ladybug Data List.

        This is the Diffuse Horizontal Radiation in Wh/m2. (Amount of solar radiation in Wh/m2 received from the sky (excluding the solar disk) on a horizontal surface during the number of minutes preceding the time indicated.) If the field is missing ( >= 9999) or invalid ( < 0), it is set to 0. Counts of such missing values are totaled and presented at the end of the runperiod
        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self.__get_dataByField(15)

    @property
    def globalHorizontalIlluminance(self):
        """Return annual Global Horizontal Illuminance as a Ladybug Data List

            This is the Global Horizontal Illuminance in lux. (Average total amount of direct and diffuse illuminance in hundreds of lux received on a horizontal surface during the number of minutes preceding the time indicated.) It is not currently used in EnergyPlus calculations. It should have a minimum value of 0; missing value for this field is 999999 and will be considered missing if greater than or equal to 999900.
            Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self.__get_dataByField(16)

    @property
    def directNormalIlluminance(self):
        """Return annual Direct Normal Illuminance as a Ladybug Data List

            This is the Direct Normal Illuminance in lux. (Average amount of illuminance in hundreds of lux received directly from the solar disk on a surface perpendicular to the sun's rays, during the number of minutes preceding the time indicated.) It is not currently used in EnergyPlus calculations. It should have a minimum value of 0; missing value for this field is 999999 and will be considered missing if greater than or equal to 999900.
            Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self.__get_dataByField(17)

    @property
    def diffuseHorizontalIlluminance(self):
        """Return annual Diffuse Horizontal Illuminance as a Ladybug Data List

            This is the Diffuse Horizontal Illuminance in lux. (Average amount of illuminance in hundreds of lux received from the sky (excluding the solar disk) on a horizontal surface during the number of minutes preceding the time indicated.) It is not currently used in EnergyPlus calculations. It should have a minimum value of 0; missing value for this field is 999999 and will be considered missing if greater than or equal to 999900.
            Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self.__get_dataByField(18)

    @property
    def zenithLuminance(self):
        """Return annual Zenith Luminance as a Ladybug Data List

            This is the Zenith Illuminance in Cd/m2. (Average amount of luminance at the sky's zenith in tens of Cd/m2 during the number of minutes preceding the time indicated.) It is not currently used in EnergyPlus calculations. It should have a minimum value of 0; missing value for this field is 9999.
            Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self.__get_dataByField(19)

    @property
    def windDirection(self):
        """Return annual Wind Direction as a Ladybug Data List

            This is the Wind Direction in degrees where the convention is that North=0.0, East=90.0, South=180.0, West=270.0. (Wind direction in degrees at the time indicated. If calm, direction equals zero.) Values can range from 0 to 360. Missing value is 999.
            Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self.__get_dataByField(20)

    @property
    def windSpeed(self):
        """Return annual Wind Speed as a Ladybug Data List

            This is the wind speed in m/sec. (Wind speed at time indicated.) Values can range from 0 to 40. Missing value is 999.
            Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self.__get_dataByField(21)

    @property
    def totalSkyCover(self):
        """Return annual Total Sky Cover as a Ladybug Data List

            This is the value for total sky cover (tenths of coverage). (i.e. 1 is 1/10 covered. 10 is total coverage). (Amount of sky dome in tenths covered by clouds or obscuring phenomena at the hour indicated at the time indicated.) Minimum value is 0; maximum value is 10; missing value is 99.
            Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self.__get_dataByField(22)

    @property
    def opaqueSkyCover(self):
        """Return annual Opaque Sky Cover as a Ladybug Data List

            This is the value for opaque sky cover (tenths of coverage). (i.e. 1 is 1/10 covered. 10 is total coverage). (Amount of sky dome in tenths covered by clouds or obscuring phenomena that prevent observing the sky or higher cloud layers at the time indicated.) This is not used unless the field for Horizontal Infrared Radiation Intensity is missing and then it is used to calculate Horizontal Infrared Radiation Intensity. Minimum value is 0; maximum value is 10; missing value is 99.
            Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self.__get_dataByField(23)

    @property
    def visibility(self):
        """Return annual Visibility as a Ladybug Data List

            This is the value for visibility in km. (Horizontal visibility at the time indicated.) It is not currently used in EnergyPlus calculations. Missing value is 9999.
            Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self.__get_dataByField(24)

    @property
    def ceilingHeight(self):
        """Return annual Ceiling Height as a Ladybug Data List

            This is the value for ceiling height in m. (77777 is unlimited ceiling height. 88888 is cirroform ceiling.) It is not currently used in EnergyPlus calculations. Missing value is 99999
            Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self.__get_dataByField(25)

    @property
    def presentWeatherObservation(self):
        """Return annual Present Weather Observation as a Ladybug Data List

            If the value of the field is 0, then the observed weather codes are taken from the following field. If the value of the field is 9, then "missing" weather is assumed. Since the primary use of these fields (Present Weather Observation and Present Weather Codes) is for rain/wet surfaces, a missing observation field or a missing weather code implies no rain.
            Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self.__get_dataByField(26)

    @property
    def presentWeatherCodes(self):
        """Return annual Present Weather Codes as a Ladybug Data List

            The present weather codes field is assumed to follow the TMY2 conventions for this field. Note that though this field may be represented as numeric (e.g. in the CSV format), it is really a text field of 9 single digits. This convention along with values for each "column" (left to right) is presented in Table 16. Note that some formats (e.g. TMY) does not follow this convention - as much as possible, the present weather codes are converted to this convention during WeatherConverter processing. Also note that the most important fields are those representing liquid precipitation - where the surfaces of the building would be wet. EnergyPlus uses "Snow Depth" to determine if snow is on the ground.
            Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self.__get_dataByField(27)

    @property
    def precipitableWater(self):
        """Return annual Precipitable Water as a Ladybug Data List

            This is the value for Precipitable Water in mm. (This is not rain - rain is inferred from the PresWeathObs field but a better result is from the Liquid Precipitation Depth field)). It is not currently used in EnergyPlus calculations (primarily due to the unreliability of the reporting of this value). Missing value is 999.
            Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self.__get_dataByField(28)

    @property
    def aerosolOpticalDepth(self):
        """Return annual Aerosol Optical Depth as a Ladybug Data List

            This is the value for Aerosol Optical Depth in thousandths. It is not currently used in EnergyPlus calculations. Missing value is .999.
            Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self.__get_dataByField(29)

    @property
    def snowDepth(self):
        """Return annual Snow Depth as a Ladybug Data List

            This is the value for Snow Depth in cm. This field is used to tell when snow is on the ground and, thus, the ground reflectance may change. Missing value is 999.
            Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self.__get_dataByField(30)

    @property
    def daysSinceLastSnowfall(self):
        """Return annual Days Since Last Snow Fall as a Ladybug Data List

            This is the value for Days Since Last Snowfall. It is not currently used in EnergyPlus calculations. Missing value is 99.
            Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self.__get_dataByField(31)

    @property
    def albedo(self):
        """Return annual Albedo values as a Ladybug Data List

            The ratio (unitless) of reflected solar irradiance to global horizontal irradiance. It is not currently used in EnergyPlus
            Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self.__get_dataByField(32)

    @property
    def liquidPrecipitationDepth(self):
        """Return annual liquid precipitation depth as a Ladybug Data List

            The amount of liquid precipitation (mm) observed at the indicated time for the period indicated in the liquid precipitation quantity field. If this value is not missing, then it is used and overrides the "precipitation" flag as rainfall. Conversely, if the precipitation flag shows rain and this field is missing or zero, it is set to 1.5 (mm).
            Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self.__get_dataByField(33)

    @property
    def liquidPrecipitationQuantity(self):
        """Return annual Liquid Precipitation Quantity as a Ladybug Data List.

        The period of accumulation (hr) for the liquid precipitation depth field.
        It is not currently used in EnergyPlus.
        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/
            pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self.__get_dataByField(34)

    def __getWEAHeader(self):
        return "place %s\n" % self.location.city + \
            "latitude %.2f\n" % self.location.latitude + \
            "longitude %.2f\n" % -self.location.longitude + \
            "time_zone %d\n" % (-self.location.timeZone * 15) + \
            "site_elevation %.1f\n" % self.location.elevation + \
            "weather_data_file_units 1\n"

    def epw2wea(self, filePath=None):
        """Write wea file from epw file.

        WEA carries radiation values from epw ans is what gendaymtx uses to
        generate the sky. I wrote my own implementation to avoid shipping
        epw2wea.exe file. Now epw2wea is part of the Radiance distribution
        """
        if not filePath:
            filePath = self.fileAddress[:-3] + "wea"

        with open(filePath, "wb") as weaFile:
            # write header
            weaFile.write(self.__getWEAHeader())
            # write values
            for dirRad, difRad in zip(self.directNormalRadiation,
                                      self.diffuseHorizontalRadiation):
                line = "%d %d %.3f %d %d\n" \
                    % (dirRad.datetime.month,
                       dirRad.datetime.day,
                       dirRad.datetime.hour - 0.5,
                       dirRad, difRad)

                weaFile.write(line)

        return filePath

    def __repr__(self):
        """epw file representation."""
        return "EPW file Data for [%s]" % self.location.city


class EPWDataTypes:
    """EPW weather file fields.

    Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
    """
    __fields = {
        0 : { 'name'  : 'Year',
                'type' : int
            },

        1 : { 'name'  : 'Month',
                'type' : int
            },

        2 : { 'name'  : 'Day',
                'type' : int
            },

        3 : { 'name'  : 'Hour',
                'type' : int
            },

        4 : { 'name'  : 'Minute',
                'type' : int
            },

        5 : { 'name'  : 'Uncertainty Flags',
                'type' : str
            },

        6 : { 'name'  : 'Dry Bulb Temperature',
                'type' : float,
                'units' : 'C',
                'min'   : -70,
                'max'   : 70,
                'missing' : 99.9
            },

        7 : { 'name' : 'Dew Point Temperature',
                'type' : float,
                'units' : 'C',
                'min' : -70,
                'max' : 70,
                'missing' : 99.9
            },

        8 : { 'name' : 'Relative Humidity',
                'type' : int,
                'missing' : 999,
                'min' : 0,
                'max' : 110
            },

        9 : { 'name' : 'Atmospheric Station Pressure',
                'type' : int,
                'units' : 'Pa',
                'missing' : 999999,
                'min' : 31000,
                'max' : 120000
            },

        10 : { 'name' : 'Extraterrestrial Horizontal Radiation',
                'type' : int,
                'units' : 'Wh/m2',
                'missing' :  9999,
                'min' : 0
            },

        11 : { 'name' : 'Extraterrestrial Direct Normal Radiation',
                'type' : int,
                'units' :  'Wh/m2',
                'missing' : 9999,
                'min' : 0
            },

        12 : { 'name' : 'Horizontal Infrared Radiation Intensity',
                'type' : int,
                'units' : 'Wh/m2',
                'missing' : 9999,
                'min' : 0
            },

        13 : { 'name' : 'Global Horizontal Radiation',
                'type' : int,
                'units' : 'Wh/m2',
                'missing' : 9999,
                'min' : 0
            },

        14 : { 'name' : 'Direct Normal Radiation',
                'type' : int,
                'units' : 'Wh/m2',
                'missing' : 9999,
                'min' : 0
            },

        15 : { 'name' : 'Diffuse Horizontal Radiation',
                'type' : int,
                'units' : 'Wh/m2',
                'missing' : 9999,
                'min' : 0
            },

        16 : { 'name' : 'Global Horizontal Illuminance',
                'type' : int,
                'units' : 'lux',
                'missing' : 999999, # note will be missing if >= 999900
                'min' : 0
            },

        17 : { 'name' : 'Direct Normal Illuminance',
                'type' : int,
                'units' : 'lux',
                'missing' : 999999, # note will be missing if >= 999900
                'min' : 0
            },

        18 : { 'name' : 'Diffuse Horizontal Illuminance',
                'type' : int,
                'units' : 'lux',
                'missing' : 999999, # note will be missing if >= 999900
                'min' : 0
            },

        19 : { 'name' : 'Zenith Luminance',
                'type' : int,
                'units' : 'Cd/m2',
                'missing' : 9999, # note will be missing if >= 9999
                'min' : 0
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
                'type' : int,
                'missing' : 99,
                'min' : 0,
                'max' : 10
            },

        23 : { 'name' : 'Opaque Sky Cover', #(used if Horizontal IR Intensity missing)
                'type' : int,
                'missing' : 99
            },

        24 : { 'name' : 'Visibility',
                'type' : float,
                'units' : 'km',
                'missing' : 9999
            },

        25 : { 'name' : 'Ceiling Height',
                'type' : int,
                'units' : 'm',
                'missing' : 99999
            },

        26 : { 'name' : 'Present Weather Observation',
                'type' : int
            },

        27 : { 'name' : 'Present Weather Codes',
                'type' : int
            },

        28 : { 'name' : 'Precipitable Water',
                'type' : int,
                'units' : 'mm',
                'missing' : 999
            },

        29 : { 'name' : 'Aerosol Optical Depth',
                'type' : float,
                'units' : 'thousandths',
                'missing' : 999
            },

        30 : { 'name' : 'Snow Depth',
                'type' : int,
                'units' : 'cm',
                'missing' : 999
            },

        31 : { 'name' :  'Days Since Last Snowfall',
                'type' : int,
                'missing' : 99
            },

        32 : { 'name' :  'Albedo',
                'type' : float,
                'missing': 999
            },

        33 : { 'name' :  'Liquid Precipitation Depth',
                'type' : float,
                'units': 'mm',
                'missing': 999
            },

        34 : { 'name' :  'Liquid Precipitation Quantity',
                'type' : float,
                'units': 'hr',
                'missing': 99
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
            0 Year
            1 Month
            2 Day
            3 Hour
            4 Minute
            -
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
            32 Albedo
            33 Liquid Precipitation Depth
            34 Liquid Precipitation Quantity
        """
        return cls.EPWField(cls.__fields[fieldNumber])
