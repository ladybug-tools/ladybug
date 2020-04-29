# coding=utf-8
"""Module of Data Types (eg. Temperature, Area, etc.)

Possesses capabilities for unit conversions and range checks.
It also includes descriptions of the data types and the units.

Properties:
    TYPES: A tuple indicating all currently supported data types.

    BASETYPES: A tuple indicating all base types. Base types are the
    data types on which unit systems are defined.

    UNITS: A dictionary containing all currently supported units. The
    keys of this dictionary are the base type names (eg. 'Temperature').

    TYPESDICT: A dictionary containing pointers to the classes of each data type.
    The keys of this dictionary are the data type names.
"""

from .base import _DataTypeEnumeration

_data_types = _DataTypeEnumeration(import_modules=True)
TYPES = _data_types.types
BASETYPES = _data_types.base_types
UNITS = _data_types.units
TYPESDICT = _data_types.types_dict
