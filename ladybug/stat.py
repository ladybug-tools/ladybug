from .location import Location

import os
import re
import codecs
import platform


class Stat(object):
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
        try:
            iron_python = True if platform.python_implementation() == 'IronPython' \
                else False
        except ValueError as e:
            # older versions of IronPython fail to parse version correctly
            # failed to parse IronPython sys.version: '2.7.5 (IronPython 2.7.5 (2.7.5.0)
            # on .NET 4.0.30319.42000 (64-bit))'
            if 'IronPython' in str(e):
                iron_python = True

        if iron_python:
            statwin = codecs.open(self.file_path, 'r')
        else:
            statwin = codecs.open(self.file_path, 'r', encoding='utf-8', errors='ignore')
        try:
            line = statwin.readline()
            # import header with location
            self._header = [line] + [statwin.readline() for i in range(9)]
        except Exception as e:
            import traceback
            raise Exception('{}\n{}'.format(e, traceback.format_exc()))
        else:
            # import location data
            loc_name = self._header[2].strip().replace('Location -- ', '')
            if ' - ' in loc_name:
                city = ' '.join(loc_name.split(' - ')[:-1])
            else:
                # for US stat files it is full name separated by spaces
                # Chicago Ohare Intl Ap IL USA
                city = ' '.join(loc_name.split()[:-2])

            country = loc_name.split(' ')[-1]

            source = self._header[6].strip().replace('Data Source -- ', '')
            station_id = self._header[8].strip().replace('WMO Station ', '')
            if iron_python:
                # IronPython
                coord_pattern = re.compile(r"{([NSEW])(\s*\d*)deg(\s*\d*)'}")
                matches = coord_pattern.findall(self._header[3].replace('\xb0', 'deg'))
            else:
                # CPython
                coord_pattern = re.compile(r"{([NSEW])(\s*\d*) (\s*\d*)'}")
                matches = coord_pattern.findall(self._header[3])
            lat_sign = -1 if matches[0][0] == 'S' else 1
            latitude = lat_sign * (float(matches[0][1]) + (float(matches[0][2]) / 60))
            lon_sign = -1 if matches[1][0] == 'W' else 1
            longitude = lon_sign * (float(matches[1][1]) + (float(matches[1][2]) / 60))
            tz_pattern = re.compile(r"{GMT\s*(\S*)\s*Hours}")
            time_zone = float(tz_pattern.findall(self._header[3])[0])
            elev_pattern = re.compile(r"Elevation\s*[-]*\s*(\d*)m\s*(\S*)")
            elev_matches = elev_pattern.findall(self._header[4])
            elev_sign = -1 if elev_matches[0][-1].lower() == 'below' else 1
            elevation = elev_sign * float(elev_matches[0][0])

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

            # move through the document and pull out the climate zone and tau values
            for line in statwin:
                if 'taub (beam)' in line:
                    taub_raw = line.replace('taub (beam)', '').strip().split('\t')
                    self._monthly_tau_beam = [float(i) if 'N' not in i
                                              else None for i in taub_raw]
                elif 'taud (diffuse)' in line:
                    taud_raw = line.replace('taud (diffuse)', '').strip().split('\t')
                    self._monthly_tau_diffuse = [float(i) if 'N' not in i
                                                 else None for i in taud_raw]
                elif 'Climate type' in line and 'ASHRAE' in line:
                    self._ashrae_climate_zone = line.split('"')[1]
                elif 'Climate type' in line:
                    self._koppen_climate_zone = line.split('"')[1]
        finally:
            statwin.close()
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
