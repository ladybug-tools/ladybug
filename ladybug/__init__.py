from ._datacollectionbase import _DataCollectionEnumeration

import sys
import importlib
import pkgutil

__version__ = '0.1.0'

#  find and import ladybug plugins
#  this is a critical step to add additional functionalities to ladybug core library.
lb_plugins = {
    name: importlib.import_module(name)
    for finder, name, ispkg
    in pkgutil.iter_modules()
    if name.startswith('ladybug_')
}

for key in lb_plugins:
    print('Successfully imported Ladybug plugin: {}'.format(key))

# This is a variable to check if the library is a [+] library.
setattr(sys.modules[__name__], 'isplus', False)

# This ensurse that the conversion between mutable and immutable collections can happen.
_data_collections = _DataCollectionEnumeration(import_modules=True)
MUTABLECOLLECTIONS = _data_collections.mutable_collections
IMMUTABLECOLLECTIONS = _data_collections.immutable_collections
