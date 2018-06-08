from .location import Location

import os


class STAT(object):
    """Import data from a local .stat file.

    args:
        file_path: Local file address to a .stat file.

    properties:
        location
        ashrae_climate_zone
        koppen_climate_zone
        monthly_tau_beam
        monthly_tau_diffuse
    """

    def __init__(self, file_path=None):
        """Initalize the class."""
        self.file_path = file_path
        self._is_data_loaded = False
        self._header = None  # epw header

    @property
    def file_path(self):
        """Get or set path to stat file."""
        return self._file_path

    @property
    def folder(self):
        """Get stat file folder."""
        return self._folder

    @property
    def file_name(self):
        """Get stat file name."""
        return self._file_name

    @file_path.setter
    def file_path(self, stat_file_path):
        self._file_path = os.path.normpath(stat_file_path)

        if not os.path.isfile(self._file_path):
            raise ValueError(
                'Cannot find an stat file at {}'.format(self._file_path))

        if not stat_file_path.lower().endswith('stat'):
            raise TypeError(stat_file_path + ' is not an .stat file.')

        self._folder, self._file_name = os.path.split(self.file_path)

    @property
    def is_data_loaded(self):
        """Return True if data is loaded."""
        return self._is_data_loaded

    # TODO: import heating + cooling design temperatures
    # TODO: import hot, cold and typical weeks
    def import_data(self):
        """Import data from a stat file.
        """
        with open(self.file_path, 'rb') as statwin:
            line = statwin.readline()
            self._header = [line] + [statwin.readline() for i in xrange(9)]

            # import location data
            # lines 3-9 alwyas have location data - Here is an example
            # Location -- New York J F Kennedy IntL Ar NY USA
            # {N 40 39'} {W  73 48'} {GMT -5.0 Hours}
            # Elevation --     5m above sea level
            # Standard Pressure at Elevation -- 101265Pa
            # Data Source -- TMY3
            #
            # WMO Station 744860
            loc_name = self._header[2].strip().replace('Location -- ', '')
            city = ' '.join(loc_name.split(' ')[:-1])
            country = loc_name.split(' ')[-1]
            source = self._header[6].strip().replace('Data Source -- ', '')
            station_id = self._header[8].strip().replace('WMO Station ', '')
            coor_str = self._header[3].strip().split('} {')
            lat_str = coor_str[0].replace('\xb0', '').replace('{', '') \
                .replace("'", '').split(' ')
            lon_str = coor_str[1].replace(
                '\xb0', '').replace("'", '').split(' ')
            while '' in lat_str:
                lat_str.remove('')
            while '' in lon_str:
                lon_str.remove('')
            latitude = float(lat_str[1]) + (float(lat_str[2])/60)
            if lat_str[0] == 'S':
                latitude = -latitude
            longitude = float(lon_str[-2]) + (float(lon_str[-1])/60)
            if lon_str[0] == 'W':
                longitude = -longitude
            time_zone = float(coor_str[2].replace('GMT ', '')
                              .replace(" Hours}", ''))
            elev_str = self._header[4].replace('Elevation --', '').strip() \
                .replace(' sea level', '').split(' ')
            elevation = int(elev_str[0].replace('m', ''))
            if elev_str[-1].strip().lower() == 'below':
                elevation = -elevation

            self._location = Location()
            self._location.city = city
            self._location.country = country
            self._location.source = source
            self._location.station_id = station_id
            self._location.latitude = latitude
            self._location.longitude = longitude
            self._location.time_zone = time_zone
            self._location.elevation = elevation

            # defaults in case the climate is unclassifiable
            self._ashrae_climate_zone = None
            self._koppen_climate_zone = None

            # move through the document and pull out the relevant data
            while line:
                if 'taub (beam)' in line:
                    taub_raw = line.replace('taub (beam)', '').strip() \
                        .split('\t')
                    self._monthly_tau_beam = [float(i) if 'N' not in i
                                              else None for i in taub_raw]
                elif 'taud (diffuse)' in line:
                    taud_raw = line.replace('taud (diffuse)', '').strip() \
                        .split('\t')
                    self._monthly_tau_diffuse = [float(i) if 'N' not in i
                                                 else None for i in taud_raw]
                elif 'Climate type' in line and 'ASHRAE' in line:
                    self._ashrae_climate_zone = line.split('"')[1]
                elif 'Climate type' in line:
                    self._koppen_climate_zone = line.split('"')[1]

                line = statwin.readline()

            self._is_data_loaded = True

    @property
    def header(self):
        """Return stat file header."""
        if not self.is_data_loaded:
            self.import_data()
        return self._header

    @property
    def location(self):
        """Return ladybug location object."""
        if not self.is_data_loaded:
            self.import_data()
        return self._location

    @property
    def ashrae_climate_zone(self):
        """Return a text string indicating the ASHRAE climate zone.

        ASHRAE climate zones are frequently used to make suggestions for
        heating and cooling systems and correspond to recommendations for
        insulation levels of a building.
        """
        if not self.is_data_loaded:
            self.import_data()
        return self._ashrae_climate_zone

    @property
    def koppen_climate_zone(self):
        """Return a text string indicating the Koppen climate zone.

        The Koppen climate classification is the most widely used climate
        classification system and combines average annual and monthly
        temperatures, precipitation, and the seasonality of precipitation.
        """
        if not self.is_data_loaded:
            self.import_data()
        return self._koppen_climate_zone

    @property
    def monthly_tau_beam(self):
        """Return a list of 12 float values for monthly beam optical depth.

        These values can be used to generate ASHRAE Revised Clear Skies, which
        are intended to determine peak solar load and sizing parmeters for
        HVAC systems.
        """
        if not self.is_data_loaded:
            self.import_data()
        return self._monthly_tau_beam

    @property
    def monthly_tau_diffuse(self):
        """Return a list of 12 float values for monthly diffuse optical depth.

        These values can be used to generate ASHRAE Revised Clear Skies, which
        are intended to determine peak solar load and sizing parmeters for
        HVAC systems.
        """
        if not self.is_data_loaded:
            self.import_data()
        return self._monthly_tau_diffuse

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """stat file representation."""
        return "STAT [%s]" % self.location.city
