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
    epwFileAddress = r"C:\EnergyPlusV8-5-0\WeatherData\USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw"
    epw = EPW(epwFileAddress)
    print repr(epw.location)
    # temp = epw.dryBulbTemperature
    # epw.relativeHumidity
    # epw.__dict__['__data'] = None
    # print sys.getrefcount(epw.dryBulbTemperature)
    # del(epw)
    # gc.collect()
    # data = (LBData(i, LBDateTime.fromHOY(i)) for i in xrange(8759))
    # c = LBDataCollection(data)
    # a = c.filterByPattern((True, False))
    # for d in data:
    #     pass
    # b = list(range(8760))

if __name__ == '__main__':
    tetsPerformance()
