# use this file for your tests during the development.
# changes to this file will be ignored and won't be synced with github
# write your testunits under .\tests folder
# from ladybug import dt
# from datetime import timedelta as td
#
from ladybug.datacollection import LBDataCollection

l = LBDataCollection.fromList(range(10))
l2 = l.duplicate()

#
# l.append(15)
# print l
