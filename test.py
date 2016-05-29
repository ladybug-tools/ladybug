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

from datetime import timedelta

# # AnalysisPeriod
# ap = AnalysisPeriod()
# dates = ap.datetimes
# print len(dates) == 8760
# hoys = ap.HOYs
# print len(hoys) == 8760
#
# app = AnalysisPeriod.fromAnalysisPeriod(ap)
# print str(app) == "1/1 to 12/31 between 0 to 23 @1"
#
# anp = AnalysisPeriod.fromAnalysisPeriod(str(app))
# print anp
#
# ap = AnalysisPeriod(endMonth=2, endDay=31)
# print ap.endTime.day == 28 and ap.endTime.month == 2

# ap = AnalysisPeriod(stHour=8, endHour=15, endMonth=2, timestep=4)
# print ap.datetimes[1].hour == 8
# print ap.datetimes[1].minute == 15
#
# print ap.datetimes[-1].hour == 15
# print ap.datetimes[-1].minute == 45

# # epw
epwData = EPW("C:\EnergyPlusV8-3-0\WeatherData\USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw")

# analysisPeriod = AnalysisPeriod.fromAnalysisPeriod(None)
#
# # print epwData.location
# data = epwData.dryBulbTemperature.filterByAnalysisPeriod(analysisPeriod).values()
# print len(data) == 8760
#
# LBDateTime.fromMOY(1395)
ap = AnalysisPeriod(stMonth=1, stDay=1, stHour=0, \
                     endMonth=1, endDay=31, endHour=23, timestep=4)
dewTemp = epwData.dewPointTemperature.filterByAnalysisPeriod(ap)

for d in dewTemp[:8]:
    print d

# ap = AnalysisPeriod(stMonth=1, stDay=1, stHour=0, \
#                      endMonth=1, endDay=31, endHour=23, timestep=3)
#
# dewTemp.filterByAnalysisPeriod(ap).values(header=True)

# print len(dewTemp) == 31 * 24 + 1
#
# print dewTemp[-1].datetime
#
# for m in range(60, 65):
#     print LBDateTime(1, 1, 0).addminutes(m)
