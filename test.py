# use this file for your tests during the development.
# changes to this file will be ignored and won't be synced with github
# write your testunits under .\tests folder
# from ladybug import dt
# from datetime import timedelta as td
#
from ladybug.datatype import DryBulbTemperature, RelativeHumidity, Radiation, WindSpeed

print DryBulbTemperature.mute

t = DryBulbTemperature(20)
t.convertToIP()
print t

rh = RelativeHumidity(25)
print rh.unit

r = Radiation(9999, nickname='Extraterrestrial Horizontal Radiation')

w = WindSpeed(35)

print w.fullString()
