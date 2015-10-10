import ladybug as lb

"""
Contains usage codes.It is NOT a unit test code.
"""
# _epwFile = r"C:\EnergyPlusV7-2-0\WeatherData\USA_CO_Golden-NREL.724666_TMY3.epw"
#
# analysisPeriod = lb.core.AnalysisPeriod(12, 30, 1, 2, 1, 24)
# epwfile = lb.epw.EPW(_epwFile)

# print epwfile.getHourlyDataByMonths("RH")[12]
# epwfile.getHourlyDataByAnalysisPeriod("RH", analysisPeriod, True)

# print epwfile.location
# header = lb.core.LadybugHeader(analysisPeriod= lb.core.AnalysisPeriod(stMonth=2, endMonth=10))
# print header.analysisPeriod

# lc = lb.core.Location(city= '', country='', latitude='',  longitude='', timeZone='', elevation='',  source='', stationId='')
# print lc.EPStyleLocationString
# print lc
dp = lb.core.DataTypes()
print dp.dataTypes
