import os
import ladybug as lb
import ladybug.core as core

"""
Contains usage codes.It is NOT a unit test code.
"""
_epwFile = r"C:\EnergyPlusV7-2-0\WeatherData\USA_CO_Golden-NREL.724666_TMY3.epw"

# analysisPeriod = lb.core.AnalysisPeriod(12, 30, 1, 2, 1, 24)
# print analysisPeriod.get_timestamps()

epwfile = lb.epw.EPW(_epwFile)

#f = lb.epw.EPWDataTypes.fields()
f = lb.epw.EPWDataTypes.get_fieldByNumber(6)
#print f.name, f.units

print epwfile.dryBulbTemperature.toList
# print lb.epw.EPW.get_dataByField(_epwFile, 29)


# print epwfile.get_hourlyDataByAnalysisPeriod("RH", analysisPeriod, True)

# lb.windRose.getWindRoseData(epwFile)
#windrose = lbg.calculateWindrose(windRoseData)

# Return data separated in months
# print epwfile.get_hourlyDataByMonths("RH")


#print epwfile.location
#print epwfile.location.city
#print epwfile.location.source

#header = lb.core.Header(analysisPeriod= lb.core.AnalysisPeriod(stMonth=2, endMonth=10))
#print header.analysisPeriod

# lc = lb.core.Location(city= '', country='', latitude='',  longitude='', timeZone='', elevation='',  source='', stationId='')
# print lc.EPStyleLocationString
# print lc

# dt = lb.core.DataTypes.get_dataTypes()
# print lb.core.DataTypes.unit("dbTemp")

# value = lb.core.Temperature(0, isEpwData=True, standard=lb.core.SI)
# value.convertToIP()
# print value, value.standard, value.unit
#
# print lb.core.Temperature.get_valueInSI(-40)
# print lb.core.Temperature.get_valueInIP(-40)
#print 100 * 5/9 -32
# print value.convertToIP()
