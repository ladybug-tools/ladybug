# use this file for your tests during the development.
# changes to this file will be ignored and won't be synced with github
# write your testunits under .\tests folder
# from ladybug import dt
# from datetime import timedelta as td
#
from ladybug.location import Location

l = Location()

print l
lo = repr(l)

l2 = Location.fromString("Tehran")

print repr(l2)
