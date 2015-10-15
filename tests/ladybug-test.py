import os
import ladybug as lb
import datetime

"""
Contains usage codes.It is NOT a unit test code.
"""
# _epwFile = r"C:\EnergyPlusV7-2-0\WeatherData\USA_CO_Golden-NREL.724666_TMY3.epw"
#
# print lb.epw.EPW.get_dataByField(_epwFile, 29)
#analysisPeriod = lb.core.AnalysisPeriod(12, 30, 1, 2, 1, 24)
# epwfile = lb.epw.EPW(_epwFile)

# print epwfile.get_hourlyDataByMonths("RH")[12]

#print epwfile.getHourlyDataByAnalysisPeriod("RH", analysisPeriod, True)

# print epwfile.location
# header = lb.core.LadybugHeader(analysisPeriod= lb.core.AnalysisPeriod(stMonth=2, endMonth=10))
# print header.analysisPeriod

# lc = lb.core.Location(city= '', country='', latitude='',  longitude='', timeZone='', elevation='',  source='', stationId='')
# print lc.EPStyleLocationString
# print lc

# dt = lb.core.DataTypes.get_dataTypes()
# print lb.core.DataTypes.unit("db")

value = lb.core.Temperature(0, isEpwData=True, standard=lb.core.SI)
value.convertToIP()
print value, value.standard, value.unit
#
# print lb.core.Temperature.get_valueInSI(-40)
# print lb.core.Temperature.get_valueInIP(-40)
#print 100 * 5/9 -32
# print value.convertToIP()
#
# #.IsInRange(100)
# # print value.unit
