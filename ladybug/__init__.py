import sys

__version__ = '0.1.0'

# This is a variable to check if the library is a [+] library.
setattr(sys.modules[__name__], 'isplus', False)
