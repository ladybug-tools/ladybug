# use this file for your tests during the development.
# changes to this file will be ignored and won't be synced with github
# write your testunits under .\tests folder
# from ladybug import dt
# from datetime import timedelta as td
#

from ladybug.location import Location
from ladybug.sunpath import Sunpath

loc = Location('Jessheim', latitude=60.155, longitude=11.9, timezone=1, elevation=200)

sp = Sunpath.fromLocation(loc)
