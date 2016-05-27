# use this file for your tests during the development.
# changes to this file will be ignored and won't be synced with github
# write your testunits under .\tests folder
# from ladybug import dt
# from datetime import timedelta as td
#
from memory_profiler import profile
from ladybug.epw import EPW
import sys
import gc
from ladybug.datacollection import LBDataCollection
from ladybug.datatype import LBData
from ladybug.dt import LBDateTime
from ladybug.header import Header
from ladybug.analysisperiod import AnalysisPeriod
from collections import namedtuple

# @profile
def tetsPerformance():
    # epwFileAddress = r"C:\EnergyPlusV8-5-0\WeatherData\USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw"
    # epw = EPW(epwFileAddress)
    # epw.dryBulbTemperature
    # epw.relativeHumidity
    # epw.__dict__['__data'] = None
    # print sys.getrefcount(epw.dryBulbTemperature)
    ap = AnalysisPeriod(stHour=9, endHour=15, stMonth=7, endMonth=7, stDay=21, endDay=21, timestep=4)
    for a in ap.datetimes:
        print a

if __name__ == '__main__':
    tetsPerformance()
