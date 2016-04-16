# use this file for your tests during the development.
# changes to this file will be ignored and won't be synced with github
# write your testunits under .\tests folder

from ladybug.comfort.pmv import PMV

airTemp = [20, 21, 22, 23, 24]
relHumid = [75, 70, 60, 50, 75]
myPmvComf = PMV(airTemp, [], [], relHumid)
print myPmvComf.pmv

myPmvComf = PMV.fromIndividualValues(26, 26, 0.5, 80, 1.1, 0.5)
print myPmvComf.pmv

epwFileAddress = "C:\ladybug\New_York_J_F_Kennedy_IntL_Ar_NY_USA\New_York_J_F_Kennedy_IntL_Ar_NY_USA.epw"
myPmvComf = PMV.fromEPWFile(epwFileAddress)
print myPmvComf.pmv
