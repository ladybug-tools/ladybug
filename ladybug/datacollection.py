"""Ladybug data collection."""
from .header import Header
from .datatype import DataPoint

from collections import OrderedDict
from itertools import izip


class DataCollection(object):
    """A list of data with a header."""

    __slots__ = ('_header', '_values')

    def __init__(self, data=None, header=None):
        """Init class."""
        self.header = header
        self._values = []

        if not data:
            data = ()
        elif not hasattr(data, '__iter__'):
            data = (data,)
        for d in data:
            assert self._checkData(d), \
                'Expected DataPoint got {}'.format(type(d))
            self._values.append(d)

    @classmethod
    def fromList(cls, lst, location=None, dataType=None, unit=None,
                 analysisPeriod=None):
        """Create a data collection from a list.

        lst items can be DataPoint or other values.

        Args:
            lst: A list of data.
            location: location data as a ladybug Location or location string
                (Default: unknown).
            dataType: Type of data (e.g. Temperature) (Default: unknown).
            unit: dataType unit (Default: unknown).
            analysisPeriod: A Ladybug analysis period (Defualt: None)
        """
        header = Header(location, dataType, unit, analysisPeriod)
        if analysisPeriod:
            return cls.fromDataAndDatetimes(lst, analysisPeriod.datetimes, header)
        else:
            data = (DataPoint.fromData(d) for d in lst)
            return cls(data, header)

    @classmethod
    def fromDataAndDatetimes(cls, data, datetimes, header=None):
        """Create a list from data and dateteimes."""
        _d = (DataPoint(v, d) for v, d in izip(data, datetimes))
        return cls(_d, header)

    @classmethod
    def fromDataAndAnalysisPeriod(cls, data, analysisPeriod, header=None):
        """Create a list from data and analysis period."""
        return cls.fromDataAndDatetimes(data, analysisPeriod.datetimes, header)

    @property
    def header(self):
        """Get or set header."""
        return self._header

    @header.setter
    def header(self, h):
        self._header = None if not h else Header.fromHeader(h)

    def append(self, d):
        """Append a single item to the list."""
        assert self._checkData(d), \
            'Expected DataPoint got {}'.format(type(d))
        self._values.append(d)

    def extend(self, newData):
        """Extend a number of items to the end of items."""
        for d in newData:
            assert self._checkData(d), \
                'Expected DataPoint got {}'.format(type(d))
        self._values.extend(newData)

    @property
    def datetimes(self):
        """Return datetimes for this collection as a tuple."""
        return tuple(value.datetime for value in self)

    @property
    def values(self):
        """Return the list of values.

        Args:
            header: A boolean that indicates if values should include the header

        Return:
            A list of values
        """
        return self._values

    def _checkData(self, d):
        return True if hasattr(d, 'isDataPoint') else False

    def duplicate(self):
        """Duplicate current data list."""
        return self.__class__(self.values, self.header)

    @staticmethod
    def average(data):
        """Return average value for a list of values."""
        values = (value.value for value in data)
        return sum(values) / len(data)

    @staticmethod
    def groupDataByMonth(data, monthRange=xrange(1, 13)):
        """Return a dictionary of values where values are grouped for each month.

        Key values are between 1-12

        Args:
            data: A list of DataPoint to be processed
            monthRange: A list of numbers for months. Default is 1-12
        """
        hourlyDataByMonth = OrderedDict()
        for m in monthRange:
            hourlyDataByMonth[m] = []

        for d in data:
            try:
                hourlyDataByMonth[d.datetime.month].append(d)
            except KeyError:
                # month is not there
                pass

        return hourlyDataByMonth

    def groupByMonth(self, monthRange=xrange(1, 13)):
        """
        Return a dictionary of values where values are grouped for each month.

        Key values are between 1-12

        Args:
           monthRange: A list of numbers for months. Default is 1-12

        Usage:

           epwfile = EPW("epw file address")
           monthlyValues = epwfile.dryBulbTemperature.groupByMonth()
           print monthlyValues[2] # returns values for the month of March
        """
        return self.groupDataByMonth(self.values, monthRange)

    @staticmethod
    def groupDataByDay(data, dayRange=xrange(1, 366)):
        """
        Return a dictionary of values where values are grouped by each day of year.

        Key values are between 1-365

        Args:
            data: A list of DataPoint to be processed
            dayRange: A list of numbers for days. Default is 1-365
        """
        hourlyDataByDay = OrderedDict()
        for d in dayRange:
            hourlyDataByDay[d] = []

        for d in data:
            try:
                hourlyDataByDay[d.datetime.doy].append(d)
            except KeyError:
                # day is not there
                pass

        return hourlyDataByDay

    def groupByDay(self, dayRange=xrange(1, 366)):
        """
        Return a dictionary of values where values are grouped by each day of year.

        Key values are between 1-365

        Args:
            dayRange: A list of numbers for days. Default is 1-365
            userDataList: An optional data list of DataPoint to be processed

        Usage:

            epwfile = EPW("epw file address")
            dailyValues = epwfile.dryBulbTemperature.groupByDay(range(1, 30))
            print dailyValues[2] # returns values for the second day of year
        """
        return self.groupDataByDay(self.values, dayRange)

    @staticmethod
    def groupDataByHour(data, hourRange=xrange(0, 24)):
        """Return a dictionary of values where values are grouped by each hour of day.

        Key values are between 0-23

        Args:
            data: A list of DataPoint to be processed
            hourRange: A list of numbers for hours. Default is 1-24
        """
        hourlyDataByHour = OrderedDict()
        for h in hourRange:
            hourlyDataByHour[h] = []

        for d in data:
            try:
                hourlyDataByHour[d.datetime.hour].append(d)
            except KeyError:
                # day is not there
                pass

        return hourlyDataByHour

    def groupByHour(self, hourRange=xrange(0, 24)):
        """Return a dictionary of values where values are grouped by each hour of day.

        Key values are between 0-23

        Args:
            hourRange: A list of numbers for hours. Default is 1-24
            userDataList: An optional data list of DataPoint to be processed

        Usage:

            epwfile = EPW("epw file address")
            monthlyValues = epwfile.dryBulbTemperature.groupByMonth([1])
            groupedHourlyData = epwfile.dryBulbTemperature.groupDataDataByHour(
                monthlyValues[1])
            for hour, data in groupedHourlyData.items():
                print("average temperature values for hour {} during JAN is {} {}"
                      .format(hour, core.DataList.average(data), DBT.header.unit))
        """
        return self.groupDataByHour(self.values, hourRange)

    def updateDataForHoursOfYear(self, values, hoursOfYear):
        """Update values new set of values for a list of hours of the year.

        Length of values should be equal to number of hours in hours of year

        Args:
            values: A list of values to be replaced in the file
            hoursOfYear: A list of hoy between 1 and 8760
        """
        # check length of data vs length of analysis hoursOfYear
        if len(values) != len(hoursOfYear):
            raise ValueError("Length of values %d is not equal to " +
                             "number of hours in analysis period %d" %
                             (len(values), len(hoursOfYear)))

        # update values
        updatedCount = 0
        for data in self.values:
            try:
                data.value = values[hoursOfYear.index(data.datetime.hoy)]
                updatedCount += 1
            except IndexError:
                pass

        print "Data %s updated for %d hour%s." % \
            ('are' if len(values) > 1 else 'is',
             updatedCount,
             's' if len(values) > 1 else '')

        # return self for chaining methods
        return self

    def updateDataForAnHour(self, value, hourOfYear):
        """
        Replace current value in data list with a new value for a specific hoy.

        Args:
            value: A single value
            hoursOfYear: The hour of the year
        """
        return self.updateDataForHoursOfYear([value], [hourOfYear])

    def updateDataForAnalysisPeriod(self, values, analysisPeriod):
        """Update values with new set of values for an analysis period.

        Length of values should be equal to number of hours in analysis period.

        Args:
            values: A list of values to be replaced in the file
            analysisPeriod: An analysis period for input the input values.
                Default is set to the whole year.
        """
        return self.updateDataForHoursOfYear(values, analysisPeriod.hoys)

    def interpolateData(self, timestep):
        """Interpolate data for a finer timestep.

        Args:
            timestep: Target timestep as an integer. Target timestep must be
                divisable by current timestep.
        """
        assert timestep % self.header.analysisPeriod.timestep == 0, \
            'Target timestep({}) must be divisable by current timestep({})' \
            .format(timestep, self.header.analysisPeriod.timestep)

        _minutesStep = int(60 / int(timestep / self.header.analysisPeriod.timestep))
        _dataLength = len(self.values)
        # generate new data
        _data = tuple(
            self[d].__class__(_v, self[d].datetime.addminutes(step * _minutesStep))
            for d in xrange(_dataLength)
            for _v, step in zip(self.xxrange(self[d],
                                             self[(d + 1) % _dataLength],
                                             timestep),
                                xrange(timestep))
        )
        # generate data for last hour
        return _data

    @staticmethod
    def xxrange(start, end, stepCount):
        """Generate n values between start and end."""
        _step = (end - start) / float(stepCount)
        return (start + (i * _step) for i in xrange(int(stepCount)))

    def filterByAnalysisPeriod(self, analysisPeriod=None):
        """
        Filter a list based on an analysis period.

        Args:
           analysis period: A Ladybug analysis period

        Return:
            A new DataList with filtered data

        Usage:

           # start of Feb to end of Mar
           analysisPeriod = AnalysisPeriod(2,1,1,3,31,24)
           epw = EPW("c:/ladybug/weatherdata.epw")
           DBT = epw.dryBulbTemperature
           filteredDBT = DBT.filterByAnalysisPeriod(analysisPeriod)
        """
        if analysisPeriod.timestep != 1:
            # interpolate data for smaller timestep
            _intData = self.interpolateData(timestep=analysisPeriod.timestep)
            # create a new header
            _hea = self.header.duplicate()
            _hea.analysisPeriod = analysisPeriod
            _data = self.__class__(_intData, _hea)
        else:
            _data = self

        if not analysisPeriod or analysisPeriod.isAnnual:
            return _data.duplicate()

        # create a new filteredData
        _filteredData = _data.filterByHOYs(analysisPeriod.hoys)
        if self.header:
            _filteredData.header.analysisPeriod = analysisPeriod

        return _filteredData

    def filterByMOYs(self, MOYs):
        """Filter the list based on a list of minutes of the year.

        Args:
           MOYs: A List of minutes of the year [0..8759 * 60]

        Return:
            A new DataList with filtered data

        Usage:

           MOYs = range(0, 48 * 60)  # The first two days of the year
           epw = EPW("c:/ladybug/weatherdata.epw")
           DBT = epw.dryBulbTemperature
           filteredDBT = DBT.filterByMOYs(MOYs)
        """
        # There is no guarantee that data is continuous so I iterate through the
        # each data point one by one
        _filteredData = [d for d in self.values if d.datetime.moy in MOYs]

        # create a new filteredData
        if self.header:
            _filteredHeader = self.header.duplicate()
            _filteredHeader.analysisPeriod = None
            return self.__class__(_filteredData, _filteredHeader)
        else:
            return self.__class__(_filteredData)

    def filterByHOYs(self, hoys):
        """Filter the list based on an analysis period.

        Args:
           hoys: A List of hours of the year 0..8759

        Return:
            A new DataList with filtered data

        Usage:

           hoys = range(1,48)  # The first two days of the year
           epw = EPW("c:/ladybug/weatherdata.epw")
           DBT = epw.dryBulbTemperature
           filteredDBT = DBT.filterByHOYs(hoys)
        """
        _moys = tuple(int(hour * 60) for hour in hoys)

        return self.filterByMOYs(_moys)

    def filterByConditionalStatement(self, statement):
        """Filter the list based on an analysis period.

        Args:
           statement: A conditional statement as a string (e.g. x>25 and x%5==0).
            The variable should always be named as x

        Return:
            A new DataList with filtered data

        Usage:

           epw = EPW("c:/ladybug/weatherdata.epw")
           DBT = epw.dryBulbTemperature
           # filter data for when dry bulb temperature is more then 25
           filteredDBT = DBT.filterByConditionalStatement('x > 25')
           # get the list of time stamps that meet the conditional statement
           print filteredDBT.timeStamps
        """
        def checkInputStatement(statement):
            stStatement = statement.lower() \
                .replace("and", "").replace("or", "") \
                .replace("not", "").replace("in", "").replace("is", "")

            parsedSt = [s for s in stStatement if s.isalpha()]
            if list(set(parsedSt)) != ['x']:
                statementErrorMsg = 'Invalid input statement. ' + \
                    'Statement should be a valid Python statement' + \
                    ' and the variable should be named as x'
                raise ValueError(statementErrorMsg)

        checkInputStatement(statement)

        statement = statement.replace('x', 'd.value')
        _filteredData = [d for d in self.values if eval(statement)]

        # create a new filteredData
        if self.header:
            _filteredHeader = self.header.duplicate()
            _filteredHeader.analysisPeriod = None
            return self(_filteredData, _filteredHeader)
        else:
            return self(_filteredData)

    def filterByPattern(self, pattern):
        """Filter the list based on a list of Boolean.

        Length of Boolean should be equal to length of values in DataList

        Args:
            pattern: A list of True, False values

        Return:
            A new DataList with filtered data
        """
        try:
            _len = len(pattern)
        except TypeError:
            raise ValueError("pattern should be a list of values.")

        _filteredData = [d for count, d in enumerate(self.values)
                         if pattern[count % _len]]

        # create a new filteredData
        if self.header:
            _filteredHeader = self.header.duplicate()
            _filteredHeader.analysisPeriod = None
            return self.__class__(_filteredData, _filteredHeader)
        else:
            return self.__class__(_filteredData)

    @staticmethod
    def averageDataMonthly(self, data):
        """Return a dictionary of values for average values for available months."""
        # group data for each month
        monthlyValues = self.groupDataByMonth(data)

        averageValues = OrderedDict()

        # average values for each month
        for month, values in monthlyValues.iteritems():
            averageValues[month] = self.average(values)

        return averageValues

    def averageMonthly(self):
        """Return a dictionary of values for average values for available months."""
        return self.averageDataMonthly(self.values)

    @staticmethod
    def averageDataMonthlyForEachHour(self, data):
        """Calculate average value for each hour during each month.

        This method returns a dictionary with nested dictionaries for each hour
        """
        # get monthy values
        monthlyHourlyValues = self.groupDataByMonth(data)

        # group data for each hour in each month and collect them in a dictionary
        averagedMonthlyValuesPerHour = OrderedDict()
        for month, monthlyValues in monthlyHourlyValues.iteritems():
            if month not in averagedMonthlyValuesPerHour:
                averagedMonthlyValuesPerHour[month] = OrderedDict()

            # group data for each hour
            groupedHourlyData = self.groupDataByHour(monthlyValues)
            for hour, data in groupedHourlyData.items():
                averagedMonthlyValuesPerHour[month][hour] = self.average(data)

        return averagedMonthlyValuesPerHour

    def averageMonthlyForEachHour(self):
        """Calculate average value for each hour during each month.

        This method returns a dictionary with nested dictionaries for each hour
        """
        return self.averageDataMonthlyForEachHour(self.values)

    def __len__(self):
        return len(self._values)

    def __getitem__(self, key):
        return self._values[key]

    def __setitem__(self, key, value):
        self._values[key] = value

    def __delitem__(self, key):
        del self._values[key]

    def __iter__(self):
        return iter(self._values)

    def __reversed__(self):
        return reversed(self._values)

    def __contains__(self, item):
        return item in self._values

    def ToString(self):
        """Overwrite .NET ToString method."""
        return self.__repr__()

    def __repr__(self):
        """Data collection representation."""
        if self.header and self.header.dataType:
            return "{}: #{}".format(self.header.dataType, len(self._values))
        else:
            return "DataCollection: #{}".format(len(self._values))
