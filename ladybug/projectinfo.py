# coding=utf-8
"""Complete set of Project Information including location, orientation and weather."""
from __future__ import division
import os
import math
import re
from ladybug_geometry.geometry2d.pointvector import Vector2D

from .config import folders
from ladybug.futil import unzip_file, download_file
from .location import Location
from .epw import EPW
from .ddy import DDY
from .stat import STAT

try:
    INFPOS = math.inf
    INFNEG = -1 * math.inf
except AttributeError:
    # python 2
    INFPOS = float('inf')
    INFNEG = float('-inf')


class ProjectInfo(object):
    """Complete set of Project Information including location, orientation and weather.

    Args:
        north_angle: North angle in degrees. A number between -360 to 360 where
            positive values rotate the compass counterclockwise (towards the
            West) and negative values rotate the compass clockwise (towards
            the East). (Default: 0).
        weather_urls: A list of URLs to zip files that includes EPW, DDY and STAT files.
            Such URLs can be found on EPWmap. The first URL in this list is
            used as the primary default weather file.
        location: A Ladybug Location object for the exact latitude and longitude
            coordinates of the project. If unset and at least one URL has been
            specified from the weather_urls, the location will default to the
            information within the EPW file.
        ashrae_climate_zone: Text indicating the ASHRAE climate zone. This input can
            be a single integer (in which case it is interpreted as A) or it can
            include the A, B, or C qualifier (eg. 3C). If unset and at least
            one URL has been specified from the weather_urls, the ashrae_climate_zone
            will default to the information within the STAT file if it exists.
        building_type: A list of text for the building types contained within
            the project. The first building type is considered the primary type
            for the project. The following text values can be included.

            * NonResidential
            * Residential
            * MidriseApartment
            * HighriseApartment
            * LargeOffice
            * MediumOffice
            * SmallOffice
            * Retail
            * StripMall
            * PrimarySchool
            * SecondarySchool
            * SmallHotel
            * LargeHotel
            * Hospital
            * Outpatient
            * Warehouse
            * SuperMarket
            * FullServiceRestaurant
            * QuickServiceRestaurant
            * Laboratory
            * Courthouse
            * College

        vintage: A list of text for the building vintages contained within
            the project. The following text values can be included.

            * DOE_Ref_Pre_1980
            * DOE_Ref_1980_2004
            * ASHRAE_2004
            * ASHRAE_2007
            * ASHRAE_2010
            * ASHRAE_2013
            * ASHRAE_2016
            * ASHRAE_2019

    Properties:
        * north_angle
        * north_vector
        * weather_urls
        * location
        * default_epw_file
        * default_stat_file
        * default_ddy_file
        * default_design_days
        * ashrae_climate_zone
        * building_type
        * gbxml_building_type
        * vintage
    """
    __slots__ = ('_north_angle', '_weather_urls', '_location',
                 '_ashrae_climate_zone', '_building_type', '_vintage')
    CLIMATE_ZONES = (
        '0A', '1A', '2A', '3A', '4A', '5A', '6A',
        '0B', '1B', '2B', '3B', '4B', '5B', '6B',
        '3C', '4C', '5C', '7', '8'
    )
    BUILDING_TYPES = {
        'NonResidential': 'Unknown',
        'Residential': 'SingleFamily',
        'MidriseApartment': 'MultiFamily',
        'HighriseApartment': 'MultiFamily',
        'LargeOffice': 'Office',
        'MediumOffice': 'Office',
        'SmallOffice': 'Office',
        'Retail': 'Retail',
        'StripMall': 'Retail',
        'PrimarySchool': 'SchoolOrUniversity',
        'SecondarySchool': 'SchoolOrUniversity',
        'SmallHotel': 'Motel',
        'LargeHotel': 'Hotel',
        'Hospital': 'HospitalOrHealthcare',
        'Outpatient': 'HospitalOrHealthcare',
        'Warehouse': 'Warehouse',
        'SuperMarket': 'Retail',
        'FullServiceRestaurant': 'DiningFamily',
        'QuickServiceRestaurant': 'DiningCafeteriaFastFood',
        'Laboratory': 'Unknown',
        'Courthouse': 'Courthouse',
        'College': 'SchoolOrUniversity',
        'LargeDataCenterHighITE': 'DataCenter',
        'LargeDataCenterLowITE': 'DataCenter',
        'SmallDataCenterHighITE': 'DataCenter',
        'SmallDataCenterLowITE': 'DataCenter'
    }
    VINTAGES = ('DOE_Ref_Pre_1980', 'DOE_Ref_1980_2004', 'ASHRAE_2004', 'ASHRAE_2007',
                'ASHRAE_2010', 'ASHRAE_2013', 'ASHRAE_2016', 'ASHRAE_2019')

    def __init__(self, north_angle=0, weather_urls=None, location=None,
                 ashrae_climate_zone=None, building_type=None, vintage=None):
        """Initialize ProjectInfo."""
        self.north_angle = north_angle
        self.weather_urls = weather_urls
        self.location = location
        self.ashrae_climate_zone = ashrae_climate_zone
        self.building_type = building_type
        self.vintage = vintage

    @property
    def north_angle(self):
        """Get or set a number between -360 and 360 for the north direction in degrees.

        This is the counterclockwise difference between the North and the positive
        Y-axis. A value of 90 will rotate the compass West and -90 will rotate it East.
        """
        return self._north_angle

    @north_angle.setter
    def north_angle(self, value):
        self._north_angle = self._float_in_range(value, -360.0, 360.0, 'north angle')
        self._north_vector = Vector2D(0, 1).rotate(math.radians(self._north_angle))

    @property
    def north_vector(self):
        """Get or set a ladybug_geometry Vector2D for the north direction."""
        return self._north_vector

    @north_vector.setter
    def north_vector(self, value):
        assert isinstance(value, Vector2D), \
            'Expected Vector2D for north_vector. Got {}.'.format(type(value))
        self._north_vector = value
        self._north_angle = \
            math.degrees(self._north_vector.angle_clockwise(Vector2D(0, 1)))

    @property
    def weather_urls(self):
        """Get or set an array of Weather URLs for the weather files of the project."""
        return tuple(self._weather_urls)

    @weather_urls.setter
    def weather_urls(self, value):
        if value is not None:
            try:
                if not isinstance(value, list):
                    value = list(value)
            except TypeError:
                raise TypeError('Expected list or tuple for ProjectInfo '
                                'weather_urls. Got {}'.format(type(value)))
            for url in value:
                assert isinstance(url, str), 'Expected URL string for ' \
                    'ProjectInfo weather_urls. Got {}.'.format(type(url))
            self._weather_urls = value
        else:
            self._weather_urls = []

    @property
    def location(self):
        """Get or set a Location object for the location of the project.

        This property defaults to the location of the first weather file if not
        explicitly specified.
        """
        if self._location is None and self.default_epw_file is not None:
            epw_obj = EPW(self.default_epw_file)
            return epw_obj.location
        return self._location

    @location.setter
    def location(self, value):
        if value is not None:
            assert isinstance(value, Location), 'Expected Location ' \
                'for ProjectInfo location. Got {}.'.format(type(value))
        self._location = value

    @property
    def default_epw_file(self):
        """Get the default EPW file for the project if weather_urls are specified."""
        if len(self._weather_urls) != 0:
            epw, _, _ = self.download_weather(self._weather_urls[0])
            return epw

    @property
    def default_stat_file(self):
        """Get the default STAT file for the project if weather_urls are specified."""
        if len(self._weather_urls) != 0:
            _, stat, _ = self.download_weather(self._weather_urls[0])
            return stat

    @property
    def default_ddy_file(self):
        """Get the default DDY file for the project if weather_urls are specified."""
        if len(self._weather_urls) != 0:
            _, _, ddy = self.download_weather(self._weather_urls[0])
            return ddy

    @property
    def default_design_days(self):
        """Get the default design days for the project if weather_urls are specified."""
        if self.default_epw_file is not None:
            if self.default_ddy_file is not None:
                ddy_obj = DDY(self.default_ddy_file)
                des_days = []
                for dday in ddy_obj:
                    if '99.6%' in dday.name or '.4%' in dday.name:
                        des_days.append(dday)
                if len(des_days) != 0:
                    return des_days
            epw_obj = EPW(self.default_epw_file)
            return [
                epw_obj.approximate_design_day('WinterDesignDay'),
                epw_obj.approximate_design_day('SummerDesignDay')
            ]
        return []

    @property
    def ashrae_climate_zone(self):
        """Get or set text for the climate zone in which the project is located.

        This input can be a single integer (in which case it is interpreted as A)
        or it can include the A, B, or C qualifier (eg. 3C). This property defaults
        to the climate zone listed in the STAT or EPW weather file if not explicitly
        specified.
        """
        if self._ashrae_climate_zone is None and self.default_epw_file is not None:
            if self.default_stat_file is not None:
                stat_obj = STAT(self.default_stat_file)
                if stat_obj.ashrae_climate_zone is not None:
                    return stat_obj.ashrae_climate_zone
            epw_obj = EPW(self.default_epw_file)
            return epw_obj.ashrae_climate_zone
        return self._ashrae_climate_zone

    @ashrae_climate_zone.setter
    def ashrae_climate_zone(self, value):
        if value:
            value = self._valid_string(value, 'ashrae_climate_zone').upper()
            if len(value) == 1 and value not in ('7', '8'):
                value = '{}A'.format(value)
            if value not in self.CLIMATE_ZONES:
                raise ValueError(
                    'ASHRAE climate zone "{}" is not recognized.\nChoose from the '
                    'following:\n{}'.format(value, self.CLIMATE_ZONES))
        else:
            value = None
        self._ashrae_climate_zone = value

    @property
    def building_type(self):
        """Get or set a list of text for the uses of the building.

        Choose from the following.

        * NonResidential
        * Residential
        * MidriseApartment
        * HighriseApartment
        * LargeOffice
        * MediumOffice
        * SmallOffice
        * Retail
        * StripMall
        * PrimarySchool
        * SecondarySchool
        * SmallHotel
        * LargeHotel
        * Hospital
        * Outpatient
        * Warehouse
        * SuperMarket
        * FullServiceRestaurant
        * QuickServiceRestaurant
        * Laboratory
        * Courthouse
        * College
        """
        return self._building_type

    @building_type.setter
    def building_type(self, value):
        if value:
            try:
                if not isinstance(value, list):
                    value = list(value)
            except TypeError:
                raise TypeError('Expected list or tuple for ProjectInfo '
                                'building_type. Got {}'.format(type(value)))
            for i, bt in enumerate(value):
                clean_input = self._valid_string(bt, 'building_type').lower()
                for key in self.BUILDING_TYPES:
                    if key.lower() == clean_input:
                        value[i] = key
                        break
                else:
                    raise ValueError(
                        'Building type "{}" is not recognized.\nChoose from the '
                        'following:\n{}'.format(bt, list(self.BUILDING_TYPES.keys())))
            self._building_type = value
        else:
            self._building_type = []

    @property
    def gbxml_building_type(self):
        """Get text for the type of building as it might appear in gbXML."""
        if len(self._building_type == 1):
            return self.BUILDING_TYPES[self._building_type[0]]
        return 'Unknown'

    @property
    def vintage(self):
        """Get or set a list of text for the vintages that appear within the building.

        Choose from the following.

        * DOE_Ref_Pre_1980
        * DOE_Ref_1980_2004
        * ASHRAE_2004
        * ASHRAE_2007
        * ASHRAE_2010
        * ASHRAE_2013
        * ASHRAE_2016
        * ASHRAE_2019
        """
        return tuple(self._vintage)

    @vintage.setter
    def vintage(self, value):
        if value:
            try:
                if not isinstance(value, list):
                    value = list(value)
            except TypeError:
                raise TypeError('Expected list or tuple for ProjectInfo '
                                'building_type. Got {}'.format(type(value)))
            for i, vt in enumerate(value):
                clean_input = self._valid_string(vt, 'vintage').lower()
                for key in self.VINTAGES:
                    if key.lower() == clean_input:
                        value = key
                        break
                else:
                    raise ValueError(
                        'Vintage "{}" is not recognized.\nChoose from the '
                        'following:\n{}'.format(vt, self.VINTAGES))
            self._vintage = value
        else:
            self._vintage = []

    def assign_attributes_from_weather(self):
        """Hard-assign properties on this object from properties in the weather file."""
        if len(self._weather_urls) != 0:
            self._location = self.location
            self._ashrae_climate_zone = self.ashrae_climate_zone

    @classmethod
    def from_dict(cls, data):
        """Create a ProjectInfo object from a dictionary.

        Args:
            data: A ProjectInfo dictionary in following the format.

        .. code-block:: python

            {
            "type": "ProjectInfo",
            "north_angle": 15,  # project angle from true north
            "weather_urls": [],  # Array of URLs pointing to weather files
            "location": {},  # Ladybug Location object dictionary
            "ashrae_climate_zone": "5A",  # climate zone
            "building_type": ["LargeOffice"],  # array of uses within the building
            "vintage": ["ASHRAE_2004"],  # array of vintages in the building
            }
        """
        assert data['type'] == 'ProjectInfo', \
            'Expected ProjectInfo dictionary. Got {}.'.format(data['type'])
        north_angle = data['north_angle'] if 'north_angle' in data else 0
        urls = data['weather_urls'] if 'weather_urls' in data else None
        loc = Location.from_dict(data['location']) \
            if 'location' in data and data['location'] is not None else None
        cz = data['ashrae_climate_zone'] if 'ashrae_climate_zone' in data else None
        bt = data['building_type'] if 'building_type' in data else None
        vt = data['vintage'] if 'vintage' in data else None
        return cls(north_angle, urls, loc, cz, bt, vt)

    def to_dict(self):
        """ProjectInfo dictionary representation."""
        siz_par = {
            'type': 'ProjectInfo',
            'north_angle': self.north_angle
        }
        if len(self._weather_urls) != 0:
            siz_par['weather_urls'] = self._weather_urls
        if self._location is not None:
            siz_par['location'] = self._location.to_dict()
        if self._ashrae_climate_zone is not None:
            siz_par['ashrae_climate_zone'] = self._ashrae_climate_zone
        if len(self._building_type) != 0:
            siz_par['building_type'] = self._building_type
        if len(self._vintage) != 0:
            siz_par['vintage'] = self._vintage
        return siz_par

    @staticmethod
    def download_weather(weather_url, folder=None):
        """Download and extract EPW and other files from a weather URL.

        If the weather files are already found to exist on the machine, these
        will be returned instead of re-downloading them.

        Args:
            weather_url: Text representing the URL at which the climate data resides.
                To open the a map interface for all publicly available climate data,
                search the EPWmap application.
            folder: An optional path to a directory into which the weather file
                will be downloaded and unzipped. If None, the weather files will be
                downloaded to the ladybug default weather data folder and placed in
                a sub-folder with the name of the weather file location.

        Returns:
            A tuple with three elements.

            -   epw_file: The file path of the downloaded epw file.

            -   stat_file: The file path of the downloaded stat file or None if
                stat file is included.

            -   ddy_file: The file path of the downloaded ddy file or None if
                stat file is included.
        """
        # process the URL and check if it is outdated
        lone_epw = False
        weather_url = weather_url.strip()
        if weather_url.lower().endswith('.zip'):  # standard zip file format
            _folder_name = weather_url.split('/')[-1][:-4]
        elif weather_url.lower().endswith('.epw'):  # a lone epw file
            if os.path.isfile(weather_url):  # it is just a local EPW file
                return weather_url, None, None
            _folder_name = weather_url.split('/')[-1][:-4]
            lone_epw = True

        # establish the default file names
        folder = folders.default_epw_folder if folder is None else folder
        if not os.path.isdir(folder):
            os.makedirs(folder)
        epw = os.path.join(folder, _folder_name, _folder_name + '.epw')
        stat = os.path.join(folder, _folder_name, _folder_name + '.stat')
        ddy = os.path.join(folder, _folder_name, _folder_name + '.ddy')

        # download and unzip the files if they do not exist
        if not os.path.isfile(epw) or not os.path.isfile(stat) or not os.path.isfile(ddy):
            if lone_epw:
                download_file(weather_url, epw, True)
            else:
                zip_file_path = os.path.join(folder, _folder_name, _folder_name + '.zip')
                download_file(weather_url, zip_file_path, True)
                unzip_file(zip_file_path)

        # set output
        epw_file, stat_file, ddy_file = epw, None, None
        if not lone_epw:
            stat_file, ddy_file = stat, ddy
        return epw_file, stat_file, ddy_file

    @staticmethod
    def _valid_string(value, input_name=''):
        """Check that a string is valid for both Radiance and EnergyPlus.

        This is used for honeybee geometry object names.
        """
        try:
            value = str(value)
            illegal_match = re.search(r'[^.A-Za-z0-9_-]', value)
        except TypeError:
            raise TypeError('Input {} must be a text string. Got {}: {}.'.format(
                input_name, type(value), value))
        assert illegal_match is None, 'Illegal character "{}" found in {}'.format(
            illegal_match.group(0), input_name)
        return value

    @staticmethod
    def _float_in_range(value, mi=INFNEG, ma=INFPOS, input_name=''):
        """Check a float value to be between minimum and maximum."""
        number = ProjectInfo._number_check(value, input_name)
        assert mi <= number <= ma, 'Input number {} must be between {} and {}. ' \
            'Got {}'.format(input_name, mi, ma, value)
        return number

    @staticmethod
    def _number_check(value, input_name):
        """Check if value is a number."""
        try:
            number = float(value)
        except (ValueError, TypeError):
            raise TypeError('Input {} must be a number. Got {}: {}.'.format(
                input_name, type(value), value))
        return number

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __copy__(self):
        loc = self._location.duplicate() if self._location is not None else None
        return ProjectInfo(
            self._north_angle, self._weather_urls[:], loc,
            self._ashrae_climate_zone, self._building_type[:], self._vintage[:]
        )

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return tuple(self._weather_urls) + tuple(self._building_type), tuple(self._vintage) + \
            (self._north_angle, hash(self._location), self._ashrae_climate_zone)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, ProjectInfo) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __len__(self):
        return len(self._weather_urls)

    def __getitem__(self, key):
        return self._weather_urls[key]

    def __setitem__(self, key, value):
        assert isinstance(value, str), 'Expected URL string for ' \
            'ProjectInfo weather_urls. Got {}.'.format(type(value))
        self._weather_urls[key] = value

    def __iter__(self):
        return iter(self._weather_urls)

    def __contains__(self, item):
        return item in self._weather_urls

    def __repr__(self):
        return 'ProjectInfo: [{} weather files]'.format(len(self._weather_urls))
