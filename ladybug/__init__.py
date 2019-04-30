# These must be imported here in this order because of how they reference eachother.
import ladybug._datacollectionbase
import ladybug.datacollection
import ladybug.datacollectionimmutable

import sys
import importlib
import pkgutil

# This is a variable to check if the library is a [+] library.
setattr(sys.modules[__name__], 'isplus', False)

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

