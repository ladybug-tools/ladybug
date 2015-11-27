import os
import ladybug as lb
import ladybug.core as core

"""
Contains usage codes.It is NOT a unit test code.
"""
_epwFile = r"C:\EnergyPlusV7-2-0\WeatherData\USA_CO_Golden-NREL.724666_TMY3.epw"


statement = 'x>25 and x==0'

## create an analysis period
analysisPeriod = lb.core.AnalysisPeriod(12, 30, 1, 2, 1, 24)
## check length of analysis period
print "Total number of hours in %s is %d"%(analysisPeriod, analysisPeriod.totalNumOfHours)
# print analysisPeriod.isAnnual

## get values based on field number
f = lb.epw.EPWDataTypes.get_fieldByNumber(8)
print f.name, f.units

# create and epw object
epwfile = lb.epw.EPW(_epwFile)

d = epwfile.import_dataByField(8)
filteredData = d.filterByAnalysisPeriod(analysisPeriod)

fDataByStatement = d.filterByConditionalStatement('x>90')
print "Number of hours with Humidity more than 90 is %d "%len(fDataByStatement.timeStamps)

# get annual dry bulb temperature
DBT = epwfile.dryBulbTemperature

## get header, values or both
# print DBT.header
# print DBT.values
# print DBT.valuesWithHeader

## filter data by analysis period
# DBT.filterByAnalysisPeriod(analysisPeriod)

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
# epwfile.save()

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
