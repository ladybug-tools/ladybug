# coding=utf-8
"""Ladybug data types."""
from __future__ import division

from os.path import dirname, basename, isfile, join
from os import listdir

# import all sub-modules from types
root_dir = join(dirname(__file__), 'types')
modules = listdir(root_dir)
modules = [join(root_dir, mod) for mod in modules]
importable = [basename(f)[:-3] for f in modules
              if isfile(f) and f.endswith('.py') and not f.endswith('__init__.py')]
for module in importable:
    statement = 'from .types.{} import *'.format(module)
    exec(statement)


def _all_subclasses(clss):
    return set(clss.__subclasses__()).union(
        [s for c in clss.__subclasses__() for s in _all_subclasses(c)])


class DataTypes(object):
    """Handles lookup of all data types by name and unit."""
    BASETYPES = {}
    TYPES = {}
    for clss in DataTypeBase.__subclasses__():
        if clss.units != [None]:
            BASETYPES[clss.__name__] = clss
            TYPES[clss.__name__] = clss
            all_subclss = _all_subclasses(clss)
            for subclss in all_subclss:
                TYPES[subclss.__name__] = subclss

    @classmethod
    def all_possible_units(cls):
        """Return a text string indicating all possible units."""
        unit_txt = []
        for base_d_type_name in cls.BASETYPES:
            base_d_type = cls.BASETYPES[base_d_type_name]
            unit_list = ', '.join(base_d_type.units)
            unit_txt.append('{}: {}'.format(base_d_type_name, unit_list))
        return '\n'.join(unit_txt)

    @classmethod
    def type_by_name(cls, type_name):
        """Return a class instance of a given data type using the name of the type.

        The type_name can be either the class name or the name property of the type.
        """
        assert isinstance(type_name, str), \
            'type_name must be a text string got {}'.format(type(type_name))
        data_types = cls.TYPES
        formatted_name = type_name.title().replace(' ', '')
        d_type = None

        if type_name in data_types:
            statement = 'd_type = {}()'.format(type_name)
            exec(statement, data_types)
            d_type = data_types['d_type']
            del data_types['d_type']
        elif formatted_name in data_types:
            statement = 'd_type = {}()'.format(formatted_name)
            exec(statement, data_types)
            d_type = data_types['d_type']
            del data_types['d_type']
        return d_type

    @classmethod
    def type_by_unit(cls, unit_name):
        """Return a class instance of a given data type using the name of the unit.

        Note this method can only return fundamental classes (those that inherit
        directly from DataTypeBase).
        """
        assert isinstance(unit_name, str), \
            'unit_name must be a text string got {}'.format(type(unit_name))
        d_type = None
        data_types = cls.BASETYPES
        for base_d_type_name in data_types:
            base_d_type = data_types[base_d_type_name]
            if hasattr(base_d_type, 'units') and unit_name in base_d_type.units:
                d_type = base_d_type_name
        if d_type is not None:
            statement = 'd_type = {}()'.format(d_type)
            exec(statement, cls.TYPES)
            d_type = cls.TYPES['d_type']
            del cls.TYPES['d_type']
        return d_type

    @classmethod
    def type_by_name_and_unit(cls, type_name, unit=None):
        """Return a class instance of a given data type using the tpye_name and unit.

        This method will always return a DataType object.  If an existing one cannot be
        found by name, it will be found by unit, and if neither methods find an
        existing DataType, a generic one will be returned.
        """
        d_type = cls.type_by_name(type_name)
        if d_type:
            d_type.is_unit_acceptable(unit, True)
            return d_type
        elif unit:
            d_type = cls.type_by_unit(unit)
            if d_type:
                d_type.name = type_name
                return d_type
            else:
                return GenericType(type_name, unit)
        else:
            return Unitless(type_name)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """DataTypes representation."""
        types = ('{}'.format(key) for key in self.TYPES)
        return '\n'.join(types)
