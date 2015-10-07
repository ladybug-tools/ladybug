import os
import datetime
import re

class AnalysisPeriod:
    
    def __init__(self, stMonth = 1, stDay = 1, stHour = 1, endMonth = 12, endDay = 31, endHour = 24, timestep = 1):
        
        self.timestep = datetime.timedelta(hours = timestep)
        self.stTime = self.checkDateTime(stMonth, stDay, stHour-1)
        self.endTime = self.checkDateTime(endMonth, endDay, endHour-1)
        
        if stHour <= endHour: self.overnight = False # each segments of hours will be in a single day
        else: self.overnight = True
        
        self.timestamps = self.getTimestamps()
        
    def checkDateTime(self, month, day, hour):
        try:
            return datetime.datetime(2000, month, day, hour)
        except ValueError, e:
            raise e
    
    def getTimestamps(self):
        timestamps = []
        curr = self.stTime
        while curr <= self.endTime:
            if self.isTimeIncluded(curr): timestamps.append(curr)
            curr += self.timestep
        return timestamps
            
    
    def isTimeIncluded(self, time):
        # time filtering in Ladybug and honeybee is slightly different since start hour and end hour will be
        # applied for every day. For instance 2/20 9am to 2/22 5pm means hour between 9-17 during 20, 21 and 22 of Feb
        if not self.stTime<= time <= self.endTime: return False
        
        # check the hours to make sure it's between the range
        if not self.overnight and self.stTime.hour <= time.hour <= self.endTime.hour: return True
        if self.overnight and (self.stTime.hour <= time.hour <= 23 \
                                or 0<= time.hour <= self.endTime.hour): return True
        return False
    
    def getStartTimeAsTuple(self):
        return (self.stTime.month, self.stTime.day, self.stTime.hour + 1)
        
    
    def getEndTimeAsTuple(self):
        return (self.endTime.month, self.endTime.day, self.endTime.hour + 1)
    
    def __repr__(self):
        return "%s/%s %s To %s/%s %s"%\
            (self.stTime.month, self.stTime.day, self.stTime.hour + 1, \
             self.endTime.month, self.endTime.day, self.endTime.hour + 1)

class EPW:
    
    def __init__(self, epwFileAddress):
        """
        Import epw data from a local epw file
        
        epwFileAddress: Local file address to an epw file
        
        """
        if epwFileAddress==None: return
        
        self.fileAddress = self.checkEpwFileAddress(epwFileAddress)
        
        self.location = Location()
        
        # data will be collected under 
        # 'timestamp': {'dbTemp': 25, 'RH': 80, ...},
        # 'timestamp': {'dbTemp': 26, 'RH': 75, ...},
        self.data = {}
        
        self.sortedTimestamps = [] # place holder for sorted time stamps
        
        self.importEpw() #import location and data
        
        self.keys = {
                    'modelYear' : {'fullname':'Year', 'unit':'Year'},
                    'dbTemp'    : {'fullname':'Dry Bulb Temperature', 'unit':'°C'}, 
                    'dewPoint'  : {'fullname':'Dew Point Temperature', 'unit':'°C'},
                    'RH'        : {'fullname':'Relative Humidity', 'unit':'%'}, 
                    'windSpeed' : {'fullname':'Wind Speed', 'unit':'m/s'}, 
                    'windDir'   : {'fullname':'Wind Direction', 'unit':'degrees'}, 
                    'dirRad'    : {'fullname':'Direct Normal Radiation', 'unit':'Wh/m2'}, 
                    'difRad'    : {'fullname':'Diffuse Horizontal Radiation', 'unit':'Wh/m2'}, 
                    'glbRad'    : {'fullname':'Global Horizontal Radiation', 'unit':'Wh/m2'}, 
                    'dirIll'    : {'fullname':'Direct Normal Illuminance', 'unit':'lux'}, 
                    'difIll'    : {'fullname':'Diffuse Horizontal Illuminance', 'unit':'lux'}, 
                    'glbIll'    : {'fullname':'Global Horizontal Illuminance', 'unit':'lux'}, 
                    'cloudCov'  : {'fullname':'Total Cloud Cover', 'unit':'tenth'}, 
                    'rainDepth' : {'fullname':'Liquid Precipitation Depth', 'unit':'mm'}, 
                    'barPress'  : {'fullname':'Barometric Pressure', 'unit':'Pa'}
                    }
        
    def checkEpwFileAddress(self, epwFileAddress):
        if not os.path.isfile(epwFileAddress):
            raise Exception(epwFileAddress + ' is not a valid address.')
        if not epwFileAddress.endswith('epw'):
            raise Exception(epwFileAddress + ' is not an .epw file.')
        return epwFileAddress
    
    def importEpw(self):
        
        with open(self.fileAddress, 'rb') as epwin:
            epwlines = epwin.readlines()
        
        # import location data
        # first line has location data - Here is an example
        # LOCATION,Denver Centennial  Golden   Nr,CO,USA,TMY3,724666,39.74,-105.18,-7.0,1829.0
        locationData = epwlines[0].strip().split(',')
        self.location.city = locationData[1]
        self.location.state = locationData[2]
        self.location.country = locationData[3]
        self.location.source = locationData[4]
        self.location.stationId = locationData[5]
        self.location.latitude = locationData[6]
        self.location.longitude = locationData[7]
        self.location.timeZone = locationData[8]
        self.location.elevation = locationData[9]
        
        # import hourly data
        for line in epwlines[8:]:
            data = line.strip().split(',')
            year, month, day, hour = map(int, data[:4])
            # in an epw file year can be different for each month
            # since I'm using this timestamp as the key and will be using it for sorting
            # I'm setting it up to 2000 - the real year will be collected under modelYear
            timestamp = datetime.datetime(2000, month, day, hour-1)
            self.data[timestamp] = {}
            self.data[timestamp]['modelYear'] = year
            try:
                self.data[timestamp]['dbTemp'] = float(data[6])
                self.data[timestamp]['dewPoint'] = float(data[7])
                self.data[timestamp]['RH'] = float(data[8])
                self.data[timestamp]['windSpeed'] = float(data[21]) 
                self.data[timestamp]['windDir'] = float(data[20])
                self.data[timestamp]['dirRad'] = float(data[14])
                self.data[timestamp]['difRad'] = float(data[15])
                self.data[timestamp]['glbRad'] = float(data[13])
                self.data[timestamp]['dirIll'] = float(data[17])
                self.data[timestamp]['difIll' ] = float(data[18])
                self.data[timestamp]['glbIll'] = float(data[16])
                self.data[timestamp]['cloudCov'] = int(data[22])
                self.data[timestamp]['rainDepth'] = float(data[33])
                self.data[timestamp]['barPress'] = float(data[9]) 
            except:
                raise Exception("Failed to import data for " + str(timestamp))
        
        self.sortedTimestamps = sorted(self.data.keys())
        
    def getDataByTime(self, month, day, hour, dataType = None):
        """
        Get weather data for a specific hour of the year for a specific data type (e.g. dbTemp, RH)
        If no type is provided all the available data will be returned
        """
        time = datetime.datetime(2000, month, day, hour-1)
        
        # if it's a valid key return data for the key
        # otherwise return all the data available for that time
        if dataType in self.keys.keys(): return self.data[time][dataType]
        return self.data[time]
    
    def getAnnualHourlyData(self, dataType, includeHeader = True):
        if dataType not in self.keys.keys():
            raise Exception(dataType + " is not a valid key" + \
                           "check self.keys for valid keys")
        header = []
        if includeHeader:
            header = LadybugHeader(self.location.city, dataType, \
                        self.keys[dataType]['unit'], "Hourly", analysisPeriod)
            
            header = header.toList()
            
        return header + [self.data[time][dataType] for time in self.sortedTimestamps]
    
    def getHourlyDataByAnalysisPeriod(self, dataType, analysisPeriod, includeHeader = True):
        if dataType not in self.keys.keys():
            raise Exception(dataType + " is not a valid key" + \
                           "check self.keys for valid keys")
        header = []
        if includeHeader:
            header = LadybugHeader(self.location.city, dataType, \
                        self.keys[dataType]['unit'], "Hourly", analysisPeriod)
            
            header = header.toList()
            
        return header + [self.data[time][dataType] for time in self.sortedTimestamps if analysisPeriod.isTimeIncluded(time)]
    
    def getHourlyDataByMonths(self, dataType = None, monthRange = range(1,13)):
        
        hourlyDataByMonth = {}
        for time in self.sortedTimestamps:
            
            if not time.month in monthRange: continue
            
            if not hourlyDataByMonth.has_key(time.month): hourlyDataByMonth[time.month] = [] #create an empty list for month
         
            if dataType in self.keys.keys():
                hourlyDataByMonth[time.month].append(self.data[time][dataType])
            else:
                hourlyDataByMonth[time.month].append(self.data[time])
             
        return hourlyDataByMonth

    def __repr__(self):
        return "EPW Data [%s]"%self.location.city

class LadybugHeader:
    
    def __init__(self, city = "", dataType = "", unit = "", timestep = "Hourly", analysisPeriod = AnalysisPeriod()):
        """Standard Ladybug header for lists
           The header carries data for city,
           data type, unit, and analysis period
           
           Parameters:
               dataType: EPW file data type (e.g. dbTemp, RH)
               analysisPeriod: A valid Ladybug analysis period. If None analysis
                    period will be annual.
        """
        
        self.header = 'location|dataType|units|frequency|startsAt|endsAt'
        self.city = city
        self.dataType = dataType
        self.unit = unit
        self.timestep = timestep
        self.analysisPeriod = analysisPeriod
        
    def toList(self):
        """returns a list of data as Ladybug header.
        """
        return [
                 self.header,
                 self.city,
                 self.dataType,
                 self.unit,
                 self.timestep,
                 self.analysisPeriod.getStartTimeAsTuple(),
                 self.analysisPeriod.getEndTimeAsTuple()
               ]
        
    def __repr__(self):
        return "%s for %s during %s"%(self.dataType, self.city, self.analysisPeriod)


class Location:
    
    def __init__(self, city = '', country = '', latitude = '', \
                longitude = '', timeZone = '', elevation ='', \
                source = '', stationId = ''):
        
        self.city = str(city)
        self.country = str(country)
        self.latitude = str(latitude)
        self.longitude = str(longitude)
        self.timeZone = str(timeZone)
        self.elevation = str(elevation)
        self.source = str(source)
        self.stationId = str(stationId)
    
    def getEPStyleLocation(self):
        """returns EnergyPlus's location string"""
        return "Site:Location,\n" + \
            self.city + ',\n' + \
            self.latitude +',      !Latitude\n' + \
            self.longitude +',     !Longitude\n' + \
            self.timeZone +',     !Time Zone\n' + \
            self.elevation + ';       !Elevation'
    
    def createFromEPString(self, EPString):
        try:
            self.city, self.latitude, \
            self.longitude, self.timeZone, \
            self.elevation = re.findall(r'\r*\n*([a-zA-Z0-9.:_ ]*)[,|;]', \
                                    EPString, re.DOTALL)[1:]
        except Exception, e:
            raise Exception ("Failed to import EP string!")
            
    def __repr__(self):
        return "%s"%(self.getEPStyleLocation())
        

# Tes cases # will be removed before the release
"""
analysisPeriod = AnalysisPeriod()
epwfile = EPW(_epwFile)
#print epwfile.getHourlyDataByMonth("RH")[12]
b = epwfile.getHourlyDataByAnalysisPeriod("RH", analysisPeriod, True)
#print epwfile.getAnnualHourlyData("RH")

l = Location()
l.createFromEPString(x)
c = l
"""
