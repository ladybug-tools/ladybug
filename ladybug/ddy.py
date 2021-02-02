# coding=utf-8
from __future__ import division

from .location import Location
from .designday import DesignDay
from .futil import write_to_file

import os
import re
import platform
import codecs


class DDY(object):
    """A DDY object containing all of the data of a .ddy file.

    Args:
        location: A Ladybug location object
        design_days: A list of the design days in the ddy file.

    Properties:
        * file_path
        * location
        * design_days
    """
    __slots__ = ('_location', '_design_days', '_file_path')

    def __init__(self, location, design_days):
        assert isinstance(location, Location), 'Expected' \
            ' Location type. Got {}'.format(type(location))

        self._location = location
        self.design_days = design_days
        self._file_path = None

    @classmethod
    def from_dict(cls, data):
        """Create a DDY from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "type": "DDY",
            "location": {},  # ladybug Location schema
            "design_days": []  # list of ladybug DesignDay schemas
            }
        """
        required_keys = ('location', 'design_days')
        for key in required_keys:
            assert key in data, 'Required key "{}" is missing!'.format(key)

        return cls(Location.from_dict(data['location']),
                   [DesignDay.from_dict(des_day) for des_day in data['design_days']])

    @classmethod
    def from_ddy_file(cls, file_path):
        """Initialize from a ddy file object from an existing ddy file.

        Args:
            file_path: A string representing a complete path to the .ddy file.
        """
        # check that the file is there
        if not os.path.isfile(file_path):
            raise ValueError(
                'Cannot find a .ddy file at {}'.format(file_path))
        if not file_path.lower().endswith('.ddy'):
            raise ValueError(
                'DDY file does not have a .ddy extension.')

        # check the python version and open the file
        if platform.python_implementation() == 'IronPython':
            ddywin = codecs.open(file_path, 'r')
        else:
            ddywin = codecs.open(file_path, 'r', encoding='utf-8', errors='ignore')

        # extract all location and design day definitions from the file
        loc_p = re.compile(r"(Site:Location,(.|\n)*?((;\s*!)|(;\s*\n)|(;\n)))")
        dday_p = re.compile(r"(SizingPeriod:DesignDay,(.|\n)*?((;\s*!)|(;\s*\n)|(;\n)))")
        try:
            ddytxt = ddywin.read()
            loc_matches = loc_p.findall(ddytxt)
            dday_matches = dday_p.findall(ddytxt)
        except Exception as e:  # the file likely doesn't exist
            import traceback
            raise Exception('{}\n{}'.format(e, traceback.format_exc()))
        else:
            # check to be sure a location and a design day was found
            assert len(loc_matches) > 0, 'No location objects found in .ddy file.'
            assert len(dday_matches) > 0, 'No design day objects found in .ddy file.'

            # build design day and location objects
            location = Location.from_idf(loc_matches[0][0])
            ddays = [DesignDay.from_idf(match[0], location) for match in dday_matches]
        finally:
            ddywin.close()

        cls_ = cls(location, ddays)
        cls_._file_path = os.path.normpath(file_path)
        return cls_

    @classmethod
    def from_design_day(cls, design_day):
        """Initialize from a ddy file object from a ladybug design day object.

        Args:
            design_day: A Ladybug DesignDay object.
        """
        return cls(design_day.location, [design_day])

    def filter_by_keyword(self, keyword):
        """Return a list of ddys that have a certain keyword in their name.

        This is useful for selecting out design days from a ddy file that are
        for a specific type of condition (for example, .4% cooling design days)
        """
        filtered_days = []
        for des_day in self._design_days:
            if keyword in des_day.name:
                filtered_days.append(des_day)
        return filtered_days

    @property
    def file_path(self):
        """Get the original .ddy file path.

        Will be None if the DDY did not originate from a file.
        """
        return self._file_path

    @property
    def location(self):
        """Get or set the location."""
        return self._location

    @location.setter
    def location(self, data):
        assert isinstance(data, Location), 'Expected' \
            ' Ladybug Location. Got {}'.format(type(data))
        self._location = data
        for dd in self._design_days:
            if dd.location != self._location:
                dd.location = self._location
                print('Updating location of {} to {}.'.format(dd, self._location))

    @property
    def design_days(self):
        """Get or set the design_days."""
        return tuple(self._design_days)

    @design_days.setter
    def design_days(self, data):
        try:
            if not isinstance(data, list):
                data = list(data)
        except TypeError:
            raise TypeError('Expected list or tuple for DDY design_days. '
                            'Got {}'.format(type(data)))
        for item in data:
            assert isinstance(item, DesignDay), 'Expected' \
                ' DesignDay type. Got {}'.format(type(item))
        self._design_days = data
        for dd in self._design_days:
            if dd.location != self._location:
                dd.location = self._location
                print('Updating location of {} to {}.'.format(dd, self._location))

    def to_dict(self):
        """Convert the Design Day to a dictionary."""
        return {
            'type': 'DDY',
            'location': self.location.to_dict(),
            'design_days': [des_d.to_dict() for des_d in self.design_days]
        }

    def to_file_string(self):
        """Get a text string for the entirety of the DDY file contents."""
        data = self.location.to_idf() + '\n\n'
        for d_day in self.design_days:
            data = data + d_day.to_idf() + '\n\n'
        return data

    def write(self, file_path):
        """Write DDY object as a .ddy file and return the file path.

        Args:
            file_path: Text for the full path to where the .ddy file will be written.
        """
        if not file_path.lower().endswith('.ddy'):
            file_path += '.ddy'
        file_data = self.to_file_string()
        write_to_file(file_path, file_data, True)
        return file_data

    def save(self, file_path):
        """Write DDY object as a file.

        Args:
            file_path: Text for the full path to where the file will be written.
        """
        file_data = self.to_file_string()
        write_to_file(file_path, file_data, True)

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __copy__(self):
        new_ddy = DDY(self._location, [dday.duplicate() for dday in self._design_days])
        new_ddy._file_path = self._file_path
        return new_ddy

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (hash(self._location),) + tuple(hash(dday) for dday in self._design_days)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, DDY) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __len__(self):
        return len(self._design_days)

    def __getitem__(self, key):
        return self._design_days[key]

    def __setitem__(self, key, value):
        assert isinstance(value, DesignDay), 'Expected' \
            ' DesignDay type. Got {}'.format(type(value))
        self._design_days[key] = value

    def __iter__(self):
        return iter(self._design_days)

    def __contains__(self, item):
        return item in self._design_days

    def __repr__(self):
        """DDY object representation."""
        return "DDY File - {} [# days: {}]".format(
            self.location.city, str(len(self._design_days)))
