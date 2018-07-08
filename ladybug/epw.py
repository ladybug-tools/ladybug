# coding=utf-8
from .location import Location
from .analysisperiod import AnalysisPeriod
from .datatype import DataPoint  # Temperature, RelativeHumidity, Radiation, Illuminance
from .header import Header
from .datacollection import DataCollection
from .dt import DateTime

import os
import copy
import sys
if (sys.version_info > (3, 0)):
    # https://docs.python.org/3/tutorial/inputoutput.html#reading-and-writing-files
    # python 3
    readmode = 'r'
    writemode = 'w'
    xrange = range
else:
    readmode = 'rb'
    writemode = 'wb'


class EPW(object):
    """Import epw data from a local epw file.

    args:
        file_path: Local file address to an epw file.

    properties:
        years
        dry_bulb_temperature
        dew_point_temperature
        relative_humidity
        atmospheric_station_pressure
        extraterrestrial_horizontal_radiation
        extraterrestrial_direct_normal_radiation
        horizontal_infrared_radiation_intensity
        global_horizontal_radiation
        direct_normal_radiation
        diffuse_horizontal_radiation
        global_horizontal_illuminance
        direct_normal_illuminance
        diffuse_horizontal_illuminance
        zenith_luminance
        wind_direction
        wind_speed
        total_sky_cover
        opaque_sky_cover
        visibility
        ceiling_height
        present_weather_observation
        present_weather_codes
        precipitable_water
        aerosol_optical_depth
        snow_depth
        days_since_last_snowfall
        albedo
        liquid_precipitation_depth
        liquid_precipitation_quantity
        sky_temperature
    """

    def __init__(self, file_path=None):
        """Init class."""
        self.file_path = file_path
        self._is_data_loaded = False
        self._is_location_loaded = False
        self._data = []  # place holder for data as ladybug data collection
        self._header = None  # epw header
        self._num_of_fields = 35  # it is 35 for TMY3 files

    @property
    def file_path(self):
        """Get path to epw file."""
        return self._file_path

    @property
    def folder(self):
        """Get epw file folder."""
        return self._folder

    @property
    def file_name(self):
        """Get epw file name."""
        return self._file_name

    @file_path.setter
    def file_path(self, epw_file_path):
        """Get path to epw file."""
        self._file_path = os.path.normpath(epw_file_path)

        if not os.path.isfile(self._file_path):
            raise ValueError(
                'Cannot find an epw file at {}'.format(self._file_path))

        if not epw_file_path.lower().endswith('epw'):
            raise TypeError(epw_file_path + ' is not an .epw file.')

        self._folder, self._file_name = os.path.split(self.file_path)

    @property
    def is_data_loaded(self):
        """Return True if weather data is loaded."""
        return self._is_data_loaded

    @property
    def is_location_loaded(self):
        """Return True if location data is loaded."""
        return self._is_location_loaded

    @property
    def header(self):
        """Return epw file header."""
        if not self.is_location_loaded:
            self._import_data(import_location_only=True)
        return self._header

    @property
    def location(self):
        """Return location data."""
        if not self.is_location_loaded:
            self._import_data(import_location_only=True)
        return self._location

    # TODO: import EPW header. Currently I just ignore header data
    def _import_data(self, import_location_only=False):
        """Import data from an epw file.

        Hourly data will be saved in self.data and location data
        will be saved in self.location
        """
        with open(self.file_path, readmode) as epwin:
            line = epwin.readline()

            # import location data
            # first line has location data - Here is an example
            # LOCATION,Denver Centennial  Golden   Nr,CO,USA,TMY3,724666,39.74,
            # -105.18,-7.0,1829.0
            if not self._is_location_loaded:
                location_data = line.strip().split(',')
                self._location = Location()
                self._location.city = location_data[1].replace('\\', ' ') \
                    .replace('/', ' ')
                self._location.country = location_data[3]
                self._location.source = location_data[4]
                self._location.station_id = location_data[5]
                self._location.latitude = location_data[6]
                self._location.longitude = location_data[7]
                self._location.time_zone = location_data[8]
                self._location.elevation = location_data[9]

                self._is_location_loaded = True

            # TODO: add parsing for header
            self._header = [line] + [epwin.readline() for i in xrange(7)]

            if import_location_only:
                return

            # read first line of data to overwrite the number of fields
            line = epwin.readline()
            self._num_of_fields = min(len(line.strip().split(',')), 35)

            # create an annual analysis period
            analysis_period = AnalysisPeriod()

            # create an empty collection for each field in epw file
            for field_number in range(self._num_of_fields):
                # create header
                field = EPWFields.field_by_number(field_number)
                # the header of data collection
                header = Header(location=self.location, analysis_period=analysis_period,
                                data_type=field.name, unit=field.unit,
                                middle_hour=field.middle_hour)

                # create an empty data list with the header
                self._data.append(DataCollection(header=header))

            # collect hourly data
            while line:
                data = line.strip().split(',')
                year, month, day, hour = map(int, data[:4])

                # in an epw file year can be different for each month
                # since I'm using this timestamp as the key and will be using it for
                # sorting. I'm setting it up to 2015 - the real year will be collected
                # under modelYear
                timestamp = DateTime(month, day, hour - 1)

                for field_number in xrange(self._num_of_fields):
                    value_type = EPWFields.field_by_number(field_number).value_type
                    try:
                        value = value_type(data[field_number])
                    except ValueError as e:
                        # failed to convert the value for the specific TypeError
                        if value_type != int:
                            raise ValueError(e)
                        value = int(round(float(data[field_number])))

                    self._data[field_number].append(DataPoint(value, timestamp))

                line = epwin.readline()

            # move last item to start position for fields on the hour
            for field_number in xrange(self._num_of_fields):
                middle_hour = EPWFields.field_by_number(field_number).middle_hour
                if middle_hour is False:
                    # shift datetimes for an hour
                    for data in self._data[field_number]:
                        try:
                            data.datetime = data.datetime.add_hour(1)
                        except ValueError:
                            # this is the last hour
                            data.datetime = DateTime(1, 1, 0)

                    # now move the last hour to first
                    last_hour = self._data[field_number].pop()
                    self._data[field_number].insert(0, last_hour)

            self._is_data_loaded = True

    def _get_data_by_field(self, field_number):
        """Return a data field by field number.

        This is a useful method to get the values for fields that Ladybug
        currently doesn't import by default. You can find list of fields by typing
        EPWFields.fields

        Args:
            field_number: a value between 0 to 34 for different available epw fields.

        Returns:
            An annual Ladybug list
        """
        if not self.is_data_loaded:
            self._import_data()

        # check input data
        if not 0 <= field_number < self._num_of_fields:
            raise ValueError("Field number should be between 0-%d" % self._num_of_fields)

        return self._data[field_number]

    # TODO: Add utility library to check file path, filename, etc
    def save(self, folder=None, file_name=None):
        """Save epw object as an epw file."""
        # check file_path
        if not folder:
            folder = self.folder

        if not file_name:
            file_name = os.path.splitext(self.file_name)[0] + '_modified.epw'

        full_path = os.path.join(folder, file_name)

        # load data if it's  not loaded
        if not self.is_data_loaded:
            self._import_data()

        # write the file
        with open(full_path, writemode) as modEpwFile:
            modEpwFile.writelines(self._header)
            lines = []
            try:
                # move first item to end position for fields on the hour
                for field in range(0, self._num_of_fields):
                    middle_hour = EPWFields.field_by_number(field).middle_hour
                    if middle_hour is False:
                        first_hour = self._data[field].pop(0)
                        self._data[field].append(first_hour)

                for hour in xrange(0, 8760):
                    line = []
                    for field in range(0, self._num_of_fields):
                        line.append(str(self._data[field].values[hour].value))
                    lines.append(",".join(line) + "\n")
            except IndexError:
                # cleaning up
                modEpwFile.close()
                length_error_msg = 'Data length is not 8760 hours and cannot be ' + \
                    'saved as an EPW file.'
                raise ValueError(length_error_msg)
            else:
                modEpwFile.writelines(lines)
            finally:
                del(lines)
                # move last item to start position for fields on the hour
                for field in range(0, self._num_of_fields):
                    middle_hour = EPWFields.field_by_number(field).middle_hour
                    if middle_hour is False:
                        last_hour = self._data[field].pop()
                        self._data[field].insert(0, last_hour)

        return full_path

    def import_data_by_field(self, field_number):
        """Return annual values for any field_number in epw file.

        This is a useful method to get the values for fields that Ladybug currently
        doesn't import by default. You can find list of fields by typing
        EPWFields.fields

        Args:
            field_number: a value between 0 to 34 for different available epw fields.
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
        return self._get_data_by_field(field_number)

    @property
    def years(self):
        """Return years as a Ladybug Data List."""
        return self._get_data_by_field(0)

    @property
    def dry_bulb_temperature(self):
        """Return annual Dry Bulb Temperature as a Ladybug Data List.

        This is the dry bulb temperature in C at the time indicated. Note that
        this is a full numeric field (i.e. 23.6) and not an integer representation
        with tenths. Valid values range from -70C to 70 C. Missing value for this
        field is 99.9

        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs
            /pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self._get_data_by_field(6)

    @property
    def dew_point_temperature(self):
        u"""Return annual Dew Point Temperature as a Ladybug Data List.

        This is the dew point temperature in C at the time indicated. Note that this is
        a full numeric field (i.e. 23.6) and not an integer representation with tenths.
        Valid values range from -70 C to 70 C. Missing value for this field is 99.9
        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs
            /pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self._get_data_by_field(7)

    @property
    def relative_humidity(self):
        u"""Return annual Relative Humidity as a Ladybug Data List.

        This is the Relative Humidity in percent at the time indicated. Valid values
        range from 0% to 110%. Missing value for this field is 999.
        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs
            /pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self._get_data_by_field(8)

    @property
    def atmospheric_station_pressure(self):
        """Return annual Atmospheric Station Pressure as a Ladybug Data List.

        This is the station pressure in Pa at the time indicated. Valid values range
        from 31,000 to 120,000. (These values were chosen from the standard barometric
        pressure for all elevations of the World). Missing value for this field is 999999
        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs
            /pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self._get_data_by_field(9)

    @property
    def extraterrestrial_horizontal_radiation(self):
        """Return annual Extraterrestrial Horizontal Radiation as a Ladybug Data List.

        This is the Extraterrestrial Horizontal Radiation in Wh/m2. It is not currently
        used in EnergyPlus calculations. It should have a minimum value of 0; missing
        value for this field is 9999.
        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs
            /pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self._get_data_by_field(10)

    @property
    def extraterrestrial_direct_normal_radiation(self):
        """Return annual Extraterrestrial Direct Normal Radiation as a Ladybug Data List.

        This is the Extraterrestrial Direct Normal Radiation in Wh/m2. (Amount of solar
        radiation in Wh/m2 received on a surface normal to the rays of the sun at the top
        of the atmosphere during the number of minutes preceding the time indicated).
        It is not currently used in EnergyPlus calculations. It should have a minimum
        value of 0; missing value for this field is 9999.
        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs
            /pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self._get_data_by_field(11)

    @property
    def horizontal_infrared_radiation_intensity(self):
        """Return annual Horizontal Infrared Radiation Intensity as a Ladybug Data List.

        This is the Horizontal Infrared Radiation Intensity in Wh/m2. If it is missing,
        it is calculated from the Opaque Sky Cover field as shown in the following
        explanation. It should have a minimum value of 0; missing value for this field
        is 9999.
        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs
            /pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self._get_data_by_field(12)

    @property
    def global_horizontal_radiation(self):
        """Return annual Global Horizontal Radiation as a Ladybug Data List.

        This is the Global Horizontal Radiation in Wh/m2. (Total amount of direct and
        diffuse solar radiation in Wh/m2 received on a horizontal surface during the
        number of minutes preceding the time indicated.) It is not currently used in
        EnergyPlus calculations. It should have a minimum value of 0; missing value
        for this field is 9999.
        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs
            /pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self._get_data_by_field(13)

    @property
    def direct_normal_radiation(self):
        """Return annual Direct Normal Radiation as a Ladybug Data List.

        This is the Direct Normal Radiation in Wh/m2. (Amount of solar radiation in
        Wh/m2 received directly from the solar disk on a surface perpendicular to the
        sun's rays, during the number of minutes preceding the time indicated.) If the
        field is missing ( >= 9999) or invalid ( < 0), it is set to 0. Counts of such
        missing values are totaled and presented at the end of the runperiod.
        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs
            /pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self._get_data_by_field(14)

    @property
    def diffuse_horizontal_radiation(self):
        """Return annual Diffuse Horizontal Radiation as a Ladybug Data List.

        This is the Diffuse Horizontal Radiation in Wh/m2. (Amount of solar radiation in
        Wh/m2 received from the sky (excluding the solar disk) on a horizontal surface
        during the number of minutes preceding the time indicated.) If the field is
        missing ( >= 9999) or invalid ( < 0), it is set to 0. Counts of such missing
        values are totaled and presented at the end of the runperiod
        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs
        /pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self._get_data_by_field(15)

    @property
    def global_horizontal_illuminance(self):
        """Return annual Global Horizontal Illuminance as a Ladybug Data List.

        This is the Global Horizontal Illuminance in lux. (Average total amount of
        direct and diffuse illuminance in hundreds of lux received on a horizontal
        surface during the number of minutes preceding the time indicated.) It is not
        currently used in EnergyPlus calculations. It should have a minimum value of 0;
        missing value for this field is 999999 and will be considered missing if greater
        than or equal to 999900.
        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs
            /pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self._get_data_by_field(16)

    @property
    def direct_normal_illuminance(self):
        """Return annual Direct Normal Illuminance as a Ladybug Data List.

        This is the Direct Normal Illuminance in lux. (Average amount of illuminance in
        hundreds of lux received directly from the solar disk on a surface perpendicular
        to the sun's rays, during the number of minutes preceding the time indicated.)
        It is not currently used in EnergyPlus calculations. It should have a minimum
        value of 0; missing value for this field is 999999 and will be considered missing
        if greater than or equal to 999900.

        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs
            /pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self._get_data_by_field(17)

    @property
    def diffuse_horizontal_illuminance(self):
        """Return annual Diffuse Horizontal Illuminance as a Ladybug Data List.

        This is the Diffuse Horizontal Illuminance in lux. (Average amount of illuminance
        in hundreds of lux received from the sky (excluding the solar disk) on a
        horizontal surface during the number of minutes preceding the time indicated.)
        It is not currently used in EnergyPlus calculations. It should have a minimum
        value of 0; missing value for this field is 999999 and will be considered missing
        if greater than or equal to 999900.

        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs
            /pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self._get_data_by_field(18)

    @property
    def zenith_luminance(self):
        """Return annual Zenith Luminance as a Ladybug Data List.

        This is the Zenith Illuminance in Cd/m2. (Average amount of luminance at
        the sky's zenith in tens of Cd/m2 during the number of minutes preceding
        the time indicated.) It is not currently used in EnergyPlus calculations.
        It should have a minimum value of 0; missing value for this field is 9999.

        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs
            /pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self._get_data_by_field(19)

    @property
    def wind_direction(self):
        """Return annual Wind Direction as a Ladybug Data List.

        This is the Wind Direction in degrees where the convention is that North=0.0,
        East=90.0, South=180.0, West=270.0. (Wind direction in degrees at the time
        indicated. If calm, direction equals zero.) Values can range from 0 to 360.
        Missing value is 999.

        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs
            /pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self._get_data_by_field(20)

    @property
    def wind_speed(self):
        """Return annual Wind Speed as a Ladybug Data List.

        This is the wind speed in m/sec. (Wind speed at time indicated.) Values can
        range from 0 to 40. Missing value is 999.

        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs
            /pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self._get_data_by_field(21)

    @property
    def total_sky_cover(self):
        """Return annual Total Sky Cover as a Ladybug Data List.

        This is the value for total sky cover (tenths of coverage). (i.e. 1 is 1/10
        covered. 10 is total coverage). (Amount of sky dome in tenths covered by clouds
        or obscuring phenomena at the hour indicated at the time indicated.) Minimum
        value is 0; maximum value is 10; missing value is 99.

        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs
            /pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self._get_data_by_field(22)

    @property
    def opaque_sky_cover(self):
        """Return annual Opaque Sky Cover as a Ladybug Data List.

        This is the value for opaque sky cover (tenths of coverage). (i.e. 1 is 1/10
        covered. 10 is total coverage). (Amount of sky dome in tenths covered by
        clouds or obscuring phenomena that prevent observing the sky or higher cloud
        layers at the time indicated.) This is not used unless the field for Horizontal
        Infrared Radiation Intensity is missing and then it is used to calculate
        Horizontal Infrared Radiation Intensity. Minimum value is 0; maximum value is
        10; missing value is 99.

        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs
            /pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self._get_data_by_field(23)

    @property
    def visibility(self):
        """Return annual Visibility as a Ladybug Data List.

        This is the value for visibility in km. (Horizontal visibility at the time
        indicated.) It is not currently used in EnergyPlus calculations. Missing
        value is 9999.

        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs
            /pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self._get_data_by_field(24)

    @property
    def ceiling_height(self):
        """Return annual Ceiling Height as a Ladybug Data List.

        This is the value for ceiling height in m. (77777 is unlimited ceiling height.
        88888 is cirroform ceiling.) It is not currently used in EnergyPlus calculations.
        Missing value is 99999

        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs
            /pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self._get_data_by_field(25)

    @property
    def present_weather_observation(self):
        """Return annual Present Weather Observation as a Ladybug Data List.

        If the value of the field is 0, then the observed weather codes are taken from
        the following field. If the value of the field is 9, then "missing" weather is
        assumed. Since the primary use of these fields (Present Weather Observation and
        Present Weather Codes) is for rain/wet surfaces, a missing observation field or
        a missing weather code implies no rain.

        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs
            /pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self._get_data_by_field(26)

    @property
    def present_weather_codes(self):
        """Return annual Present Weather Codes as a Ladybug Data List.

        The present weather codes field is assumed to follow the TMY2 conventions for
        this field. Note that though this field may be represented as numeric (e.g. in
        the CSV format), it is really a text field of 9 single digits. This convention
        along with values for each "column" (left to right) is presented in Table 16.
        Note that some formats (e.g. TMY) does not follow this convention - as much as
        possible, the present weather codes are converted to this convention during
        WeatherConverter processing. Also note that the most important fields are those
        representing liquid precipitation - where the surfaces of the building would be
        wet. EnergyPlus uses "Snow Depth" to determine if snow is on the ground.

        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs
            /pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self._get_data_by_field(27)

    @property
    def precipitable_water(self):
        """Return annual Precipitable Water as a Ladybug Data List.

        This is the value for Precipitable Water in mm. (This is not rain - rain is
        inferred from the PresWeathObs field but a better result is from the Liquid
        Precipitation Depth field). It is not currently used in EnergyPlus calculations
        (primarily due to the unreliability of the reporting of this value). Missing
        value is 999.

        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs
            /pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self._get_data_by_field(28)

    @property
    def aerosol_optical_depth(self):
        """Return annual Aerosol Optical Depth as a Ladybug Data List.

        This is the value for Aerosol Optical Depth in thousandths. It is not currently
        used in EnergyPlus calculations. Missing value is .999.

        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs
            /pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self._get_data_by_field(29)

    @property
    def snow_depth(self):
        """Return annual Snow Depth as a Ladybug Data List.

        This is the value for Snow Depth in cm. This field is used to tell when snow
        is on the ground and, thus, the ground reflectance may change. Missing value
        is 999.

        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs
            /pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self._get_data_by_field(30)

    @property
    def days_since_last_snowfall(self):
        """Return annual Days Since Last Snow Fall as a Ladybug Data List.

        This is the value for Days Since Last Snowfall. It is not currently used in
        EnergyPlus calculations. Missing value is 99.

        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs
            /pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self._get_data_by_field(31)

    @property
    def albedo(self):
        """Return annual Albedo values as a Ladybug Data List.

        The ratio (unitless) of reflected solar irradiance to global horizontal
        irradiance. It is not currently used in EnergyPlus.

        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs
            /pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self._get_data_by_field(32)

    @property
    def liquid_precipitation_depth(self):
        """Return annual liquid precipitation depth as a Ladybug Data List.

        The amount of liquid precipitation (mm) observed at the indicated time for the
        period indicated in the liquid precipitation quantity field. If this value is
        not missing, then it is used and overrides the "precipitation" flag as rainfall.
        Conversely, if the precipitation flag shows rain and this field is missing or
        zero, it is set to 1.5 (mm).

        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs
            /pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self._get_data_by_field(33)

    @property
    def liquid_precipitation_quantity(self):
        """Return annual Liquid Precipitation Quantity as a Ladybug Data List.

        The period of accumulation (hr) for the liquid precipitation depth field.
        It is not currently used in EnergyPlus.

        Read more at: https://energyplus.net/sites/all/modules/custom/nrel_custom/
            pdfs/pdfs_v8.4.0/AuxiliaryPrograms.pdf (Chapter 2.9.1)
        """
        return self._get_data_by_field(34)

    @property
    def sky_temperature(self):
        """Return annual Sky Temperature as a Ladybug Data List.

        This value in degrees Celcius is derived from the Horizontal Infrared
        Radiation Intensity in Wh/m2. It represents the long wave radiant
        temperature of the sky
        Read more at: https://bigladdersoftware.com/epx/docs/8-9/engineering-reference
            /climate-calculations.html#energyplus-sky-temperature-calculation
        """
        # create sky temperature data collection from horizontal infrared
        horiz_ir = self._get_data_by_field(12)
        sky_temp_header = copy.copy(horiz_ir.header)
        sky_temp_header.data_type = 'Sky Temperature'
        sky_temp_header.unit = 'C'

        # calculate sy temperature for each hour
        sky_temp_data = []
        for hor_ir in horiz_ir.values:
            dat = hor_ir.datetime
            temp = ((float(hor_ir) / (5.6697 * (10**(-8))))**(0.25)) - 273.15
            sky_temp_data.append(DataPoint(temp, dat))
        sky_temp = DataCollection(sky_temp_data, sky_temp_header)
        return sky_temp

    def _get_wea_header(self):
        return "place %s\n" % self.location.city + \
            "latitude %.2f\n" % self.location.latitude + \
            "longitude %.2f\n" % -self.location.longitude + \
            "time_zone %d\n" % (-self.location.time_zone * 15) + \
            "site_elevation %.1f\n" % self.location.elevation + \
            "weather_data_file_unit 1\n"

    def to_wea(self, file_path=None, hoys=None):
        """Write an wea file from the epw file.

        WEA carries radiation values from epw. Gendaymtx uses these values to
        generate the sky. For an annual analysis it is identical to using epw2wea.

        args:
            file_path: Full file path for output file.
            hoys: List of hours of the year. Default is 0-8759.
        """
        hoys = hoys or xrange(8760)
        if not file_path:
            file_path = self.file_path[:-4] + '.wea'

        if not file_path.lower().endswith('.wea'):
            file_path += '.wea'

        with open(file_path, "wb") as weaFile:
            # write header
            weaFile.write(self._get_wea_header())
            # write values
            for hoy in hoys:
                dir_rad = self.direct_normal_radiation[hoy]
                dif_rad = self.diffuse_horizontal_radiation[hoy]
                line = "%d %d %.3f %d %d\n" \
                    % (dir_rad.datetime.month,
                       dir_rad.datetime.day,
                       dir_rad.datetime.hour + 0.5,
                       dir_rad, dif_rad)

                weaFile.write(line)

        return file_path

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """epw file representation."""
        return "EPW file Data for [%s]" % self.location.city


class EPWFields(object):
    """EPW weather file fields.

    Read more at:
    https://energyplus.net/sites/all/modules/custom/nrel_custom/pdfs/
        pdfs_v8.4.0/AuxiliaryPrograms.pdf
    (Chapter 2.9.1)
    """

    FIELDS = {
        0: {'name': 'Year',
            'type': int,
            'middle_hour': False
            },

        1: {'name': 'Month',
            'type': int,
            'middle_hour': False
            },

        2: {'name': 'Day',
            'type': int,
            'middle_hour': False
            },

        3: {'name': 'Hour',
            'type': int,
            'middle_hour': False
            },

        4: {'name': 'Minute',
            'type': int,
            'middle_hour': False
            },

        5: {'name': 'Uncertainty Flags',
            'type': str,
            'middle_hour': False
            },

        6: {'name': 'Dry Bulb Temperature',
            'type': float,
            'unit': 'C',
            'min': -70,
            'max': 70,
            'missing': 99.9,
            'middle_hour': False
            },

        7: {'name': 'Dew Point Temperature',
            'type': float,
            'unit': 'C',
            'min': -70,
            'max': 70,
            'missing': 99.9,
            'middle_hour': False
            },

        8: {'name': 'Relative Humidity',
            'type': int,
            'unit': '%',
            'missing': 999,
            'min': 0,
            'max': 110,
            'middle_hour': False
            },

        9: {'name': 'Atmospheric Station Pressure',
            'type': int,
            'unit': 'Pa',
            'missing': 999999,
            'min': 31000,
            'max': 120000,
            'middle_hour': False
            },

        10: {'name': 'Extraterrestrial Horizontal Radiation',
             'type': int,
             'unit': 'Wh/m2',
             'missing': 9999,
             'min': 0,
             'middle_hour': True
             },

        11: {'name': 'Extraterrestrial Direct Normal Radiation',
             'type': int,
             'unit': 'Wh/m2',
             'missing': 9999,
             'min': 0,
             'middle_hour': True
             },

        12: {'name': 'Horizontal Infrared Radiation Intensity',
             'type': int,
             'unit': 'Wh/m2',
             'missing': 9999,
             'min': 0,
             'middle_hour': False
             },

        13: {'name': 'Global Horizontal Radiation',
             'type': int,
             'unit': 'Wh/m2',
             'missing': 9999,
             'min': 0,
             'middle_hour': True
             },

        14: {'name': 'Direct Normal Radiation',
             'type': int,
             'unit': 'Wh/m2',
             'missing': 9999,
             'min': 0,
             'middle_hour': True
             },

        15: {'name': 'Diffuse Horizontal Radiation',
             'type': int,
             'unit': 'Wh/m2',
             'missing': 9999,
             'min': 0,
             'middle_hour': True
             },

        16: {'name': 'Global Horizontal Illuminance',
             'type': int,
             'unit': 'lux',
             'missing': 999999,  # note will be missing if >= 999900
             'min': 0,
             'middle_hour': True
             },

        17: {'name': 'Direct Normal Illuminance',
             'type': int,
             'unit': 'lux',
             'missing': 999999,  # note will be missing if >= 999900
             'min': 0,
             'middle_hour': True
             },

        18: {'name': 'Diffuse Horizontal Illuminance',
             'type': int,
             'unit': 'lux',
             'missing': 999999,  # note will be missing if >= 999900
             'min': 0,
             'middle_hour': True
             },

        19: {'name': 'Zenith Luminance',
             'type': int,
             'unit': 'Cd/m2',
             'missing': 9999,  # note will be missing if >= 9999
             'min': 0,
             'middle_hour': True
             },

        20: {'name': 'Wind Direction',
             'type': int,
             'unit': 'degrees',
             'missing': 999,
             'min': 0,
             'max': 360,
             'middle_hour': False
             },

        21: {'name': 'Wind Speed',
             'type': float,
             'unit': 'm/s',
             'missing': 999,
             'min': 0,
             'max': 40,
             'middle_hour': False
             },

        22: {'name': 'Total Sky Cover',  # (used if Horizontal IR Intensity missing)
             'type': int,
             'missing': 99,
             'min': 0,
             'max': 10,
             'middle_hour': False
             },

        23: {'name': 'Opaque Sky Cover',  # (used if Horizontal IR Intensity missing)
             'type': int,
             'missing': 99,
             'middle_hour': False
             },

        24: {'name': 'Visibility',
             'type': float,
             'unit': 'km',
             'missing': 9999,
             'middle_hour': False
             },

        25: {'name': 'Ceiling Height',
             'type': int,
             'unit': 'm',
             'missing': 99999,
             'middle_hour': False
             },

        26: {'name': 'Present Weather Observation',
             'type': int,
             'middle_hour': False
             },

        27: {'name': 'Present Weather Codes',
             'type': int,
             'middle_hour': False
             },

        28: {'name': 'Precipitable Water',
             'type': int,
             'unit': 'mm',
             'missing': 999,
             'middle_hour': False
             },

        29: {'name': 'Aerosol Optical Depth',
             'type': float,
             'unit': 'thousandths',
             'missing': 999,
             'middle_hour': False
             },

        30: {'name': 'Snow Depth',
             'type': int,
             'unit': 'cm',
             'missing': 999,
             'middle_hour': False
             },

        31: {'name': 'Days Since Last Snowfall',
             'type': int,
             'missing': 99,
             'middle_hour': False
             },

        32: {'name': 'Albedo',
             'type': float,
             'missing': 999,
             'middle_hour': False
             },

        33: {'name': 'Liquid Precipitation Depth',
             'type': float,
             'unit': 'mm',
             'missing': 999,
             'middle_hour': False
             },

        34: {'name': 'Liquid Precipitation Quantity',
             'type': float,
             'unit': 'hr',
             'missing': 99,
             'middle_hour': False
             }
    }

    @classmethod
    def field_by_number(cls, field_number):
        """Return an EPWField based on field number.

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
        return EPWField(cls.FIELDS[field_number])

    def __repr__(self):
        """EPW fields representation."""
        fields = (
            '{}: {}'.format(key, value['name'])
            for key, value in self.FIELDS.items()
        )

        return '\n'.join(fields)


class EPWField(object):
    """An EPW field.

    Attributes:
        name: Name of the field.
        type: field value type (e.g. int, float, str)
        unit: Field unit.
    """

    def __init__(self, field_dict):
        self.name = field_dict['name']
        self.value_type = field_dict['type']
        self.middle_hour = field_dict['middle_hour']
        if 'unit' in field_dict:
            self.unit = field_dict['unit']
        else:
            self.unit = None
