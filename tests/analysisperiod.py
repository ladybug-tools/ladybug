import ladybug.core as core

ap = core.AnalysisPeriod.fromAnalysisPeriod("1/1 to 12/31 between 1 to 24 @1")
print ap.isAnnual
print ap.floatHOYs

time = core.LBDateTime.fromHOY(1.5)
print time.month, time.day, time.hour, time.minute
print time
print "HOY", time.HOY
print "MOY", time.MOY

t = core.LBDateTime.fromDateTimeString('1 JAN at 1:30')
print t
