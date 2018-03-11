"""This is not a unit test for the windrose"""

import os
from ladybug.windroseplus import *
from ladybug.windrose import WindRose
from ladybug.epw import EPW

os.chdir("G:\Dropbox\Github\ladybug-1")
# os.chdir("D:\Dropbox\Github\ladybug-1")
# os.chdir("/Users/cdev/Dropbox/Github/ladybug-1")

epw_filePath = "./tests/epw/chicago.epw"
weatherData = EPW(epw_filePath)
dryBulbTemp = weatherData.dry_bulb_temperature
humidity = weatherData.relative_humidity
wind = WindRose(epw_filePath,
                HOYs=range(1, 500),
                annualHourlyData=[dryBulbTemp],
                windCondition=None,
                dataCondition=["x<3"])
print makeRanges(16)
