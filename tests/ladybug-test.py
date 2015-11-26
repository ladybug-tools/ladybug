import os
import ladybug as lb
import ladybug.core as core

"""
Contains usage codes.It is NOT a unit test code.
"""
_epwFile = r"C:\EnergyPlusV7-2-0\WeatherData\USA_CO_Golden-NREL.724666_TMY3.epw"

## create an analysis period
analysisPeriod = lb.core.AnalysisPeriod(12, 30, 1, 2, 1, 24)
# print len(analysisPeriod.get_timestamps())
print analysisPeriod.totalNumOfHours

epwfile = lb.epw.EPW(_epwFile)

# lb.epw.EPWDataTypes.fieldNumbers()

#f = lb.epw.EPWDataTypes.get_fieldByNumber(6)
#print f.name, f.units

DBT = epwfile.dryBulbTemperature
# RH_values = epwfile.relativeHumidity.values
#print DBT.header
# print DBT

#DBT.filterByAnalysisPeriod(analysisPeriod)

#montlyData = DBT.separateDataByMonth()
#dailyData = DBT.separateDataByDay(range(1, 30))

# for value in dailyData[2]: print value.datetime

# print DBT.averageMonthly()
# print DBT.averageMonthlyForEachHour()

# monthlyValues = DBT.separateDataByMonth([1])
# separatedHourlyData = DBT.separateDataByHour(userDataList = monthlyValues[1])
# for hour, data in separatedHourlyData.items():
#    print "average temperature values for hour " + str(hour) + " during JAN is " + str(core.DataList.average(data)) + " " + DBT.header.unit


## modify data in an epw weather file
newValues = analysisPeriod.totalNumOfHours * [0]
DBT.updateDataForAnAnalysisPeriod(newValues, analysisPeriod)
DBT.updateDataForAnHour(20, 34)

## save the epw file as a new epw file

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
