# use this file for your tests during the development.
# changes to this file will be ignored and won't be synced with github
# write your testunits under .\tests folder

from ladybug.comfort.pmv import PMV

airTemp = [10, 12, 15, 18, 19]
relHumid = [75, 70, 60, 50, 75]
myPmvComf = PMV(airTemp, [], [], relHumid)

print myPmvComf.pmv
