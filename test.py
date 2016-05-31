# use this file for your tests during the development.
# changes to this file will be ignored and won't be synced with github
# write your testunits under .\tests folder
# from ladybug import dt
# from datetime import timedelta as td
#
from ladybug.epw import EPW
from ladybug.datacollection import LBDataCollection
from ladybug.datatype import LBData, Radiation
from ladybug.dt import LBDateTime
from ladybug.header import Header
from ladybug.analysisperiod import AnalysisPeriod
from collections import namedtuple

from ladybug.location import Location
from ladybug.sunpath import LBSunpath

# test sunpath
# test defualt inputs
sunpath = LBSunpath()
sun = sunpath.calculateSun(month=12, day=21, hour=23)

print round(sun.sunVector.x, 2) == 0.23
print round(sun.sunVector.y, 2) == 0.40
print round(sun.sunVector.z, 2) == 0.89

# test sunpath from location
l = Location()
sunpath = LBSunpath.fromLocation(l)
sun = sunpath.calculateSun(month=12, day=21, hour=23)
print round(sun.sunVector.x, 2) == 0.23
print round(sun.sunVector.y, 2) == 0.40
print round(sun.sunVector.z, 2) == 0.89
