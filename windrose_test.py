import os
from ladybug.windrose import WindRose
from ladybug.epw import EPW

# os.chdir("G:\Dropbox\Github\ladybug-1")
os.chdir("D:\Dropbox\Github\ladybug-1")
# os.chdir("/Users/cdev/Dropbox/Github/ladybug-1")

epw_filePath = "./tests/epw/chicago.epw"
weatherData = EPW(epw_filePath)
dryBulbTemp = weatherData.dry_bulb_temperature
wind = WindRose(epw_filePath,
                range(1, 500),
                annualHourlyData=None,
                windCondition=None,
                dataCondition="x>20")
print wind.parse_wind_data()
