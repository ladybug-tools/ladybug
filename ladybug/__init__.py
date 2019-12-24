# These must be imported here in this order because of how they reference eachother.
import ladybug._datacollectionbase
import ladybug.datacollection
import ladybug.datacollectionimmutable

from ladybug.logutil import get_logger

import sys
import importlib
import pkgutil

# This is a variable to check if the library is a [+] library.
# TODO: Remove this line once the sunpath module no longer uses the isplus property
setattr(sys.modules[__name__], 'isplus', False)

# set up the logger
logger = get_logger(__name__)

#  find and import ladybug extensions
#  this is a critical step to add additional functionalities to ladybug core library.
extensions = {}
for finder, name, ispkg in pkgutil.iter_modules():
    if not name.startswith('ladybug_') or name.count('_') > 1:
        continue
    try:
        extensions[name] = importlib.import_module(name)
    except Exception:
        logger.exception('Failed to import {0}!'.format(name))
    else:
        logger.info('Successfully imported Ladybug plugin: {}'.format(name))
