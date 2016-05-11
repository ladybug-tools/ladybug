# use this file for your tests during the development.
# changes to this file will be ignored and won't be synced with github
# write your testunits under .\tests folder

import time
from ladybug.epw import EPW

st = time.time()
print "loading the weather file..."
epwData = EPW(epwFileAddress=r"c:\EnergyPlusV8-3-0\WeatherData\USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw")
epwData.location
epwData.dryBulbTemperature.values(header=True)
epwData.dewPointTemperature.values(header=True)
epwData.relativeHumidity.values(header=True)
epwData.windDirection.values(header=True)
epwData.windSpeed.values(header=True)
epwData.directNormalRadiation.values(header=True)
epwData.diffuseHorizontalRadiation.values(header=True)
epwData.globalHorizontalRadiation.values(header=True)
epwData.directNormalIlluminance.values(header=True)
epwData.diffuseHorizontalIlluminance.values(header=True)
epwData.globalHorizontalIlluminance.values(header=True)
epwData.totalSkyCover.values(header=True)
epwData.liquidPrecipitationDepth.values(header=True)
epwData.atmosphericStationPressure.values(header=True)
epwData.years.values(header=True)
print time.time() - st
