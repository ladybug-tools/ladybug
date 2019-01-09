# coding=utf-8
"""Ladybug data types."""
from __future__ import division

from ._base import DataTypeBase

from os.path import dirname, basename, isfile, join
from os import listdir
from importlib import import_module


class DataTypeEnumeration(object):
    """Enumerates all data types, base types, and units."""
    _TYPES = {}
    _BASETYPES = {}
    _UNITS = {}
    _BASEUNITS = {}

    def __init__(self):
        self._import_modules()

        for clss in DataTypeBase.__subclasses__():
            if clss.__name__ != 'GenericType':
                self._TYPES[clss.__name__] = clss
                self._BASETYPES[clss.__name__] = clss
                self._UNITS[clss.__name__] = clss._units
                self._BASEUNITS[clss._units[0]] = clss.__name__
                for subclss in self._all_subclasses(clss):
                    self._TYPES[subclss.__name__] = subclss

    @property
    def types(self):
        """A text string indicating all cuurently supported types"""
        return '\n'.join(sorted(self._TYPES.keys()))

    @property
    def base_types(self):
        """A text string indicating all base types"""
        return '\n'.join(sorted(self._BASETYPES.keys()))

    @property
    def units(self):
        """A text string indicating all possible units"""
        unit_txt = []
        for base_d_type_name in self._BASETYPES:
            base_d_type = self._BASETYPES[base_d_type_name]
            unit_list = ', '.join(base_d_type._units)
            unit_txt.append('{}: {}'.format(base_d_type_name, unit_list))
        return '\n'.join(unit_txt)

    @property
    def base_units(self):
        """A text string indicating all base units for each base type."""
        unit_txt = []
        for base_unit in self._BASEUNITS:
            base_d_type_name = self._BASEUNITS[base_unit]
            unit_txt.append('{}: {}'.format(base_d_type_name, base_unit))
        return '\n'.join(unit_txt)

    def _import_modules(self):
        root_dir = dirname(__file__)
        modules = listdir(dirname(__file__))
        modules = [join(root_dir, mod) for mod in modules]
        importable = ['.{}'.format(basename(f)[:-3]) for f in modules
                      if isfile(f) and f.endswith('.py')
                      and not f.endswith('__init__.py')
                      and not f.endswith('_base.py')
                      and not f.endswith('_enumeration.py')]
        for mod in importable:
            import_module(mod, 'ladybug.datatype')

    def _all_subclasses(self, clss):
        return set(clss.__subclasses__()).union(
            [s for c in clss.__subclasses__() for s in self._all_subclasses(c)])
