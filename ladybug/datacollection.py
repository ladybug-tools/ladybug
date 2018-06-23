"""Ladybug data collection."""
from .header import Header
from .datatype import DataPoint

from collections import OrderedDict
from itertools import izip


class DataCollection(object):
    """A list of data with a header."""

    __slots__ = ('_header', '_data')

    def __init__(self, data=None, header=None):
        """Init class."""
        self.header = header

        if not data:
            data = []
        elif not hasattr(data, '__iter__'):
            data = [data]

        for d in data:
            assert hasattr(d, 'isDataPoint'), \
                'Expected DataPoint got {}'.format(type(d))

        self._data = list(data)

    @classmethod
    def from_json(cls, data):
        """Create a data collection from a dictionary.

        Args:
            {
                "data": [], //An array of Ladybug data points,
                "header": {} // A Ladybug header
            }
        """
        if 'data' not in data:
            input_data = []
        else:
            input_data = [DataPoint.from_json(d) for d in data['data']]

        if 'header' not in data:
            data['header'] = {}

        return cls(input_data, Header.from_json(data['header']))

    @classmethod
    def from_list(cls, lst, location=None, data_type=None, unit=None,
                  analysis_period=None):
        """Create a data collection from a list.

        lst items can be DataPoint or other values.

        Args:
            lst: A list of data.
            location: location data as a ladybug Location or location string
                (Default: unknown).
            data_type: Type of data (e.g. Temperature) (Default: unknown).
            unit: data_type unit (Default: unknown).
            analysis_period: A Ladybug analysis period (Defualt: None)
        """
        header = Header(location, data_type, unit, analysis_period)
        if analysis_period:
            return cls.from_data_and_datetimes(lst, analysis_period.datetimes, header)
        else:
            data = (DataPoint.from_data(d) for d in lst)
            return cls(data, header)

    @classmethod
    def from_data_and_datetimes(cls, data, datetimes, header=None):
        """Create a list from data and dateteimes."""
        _d = (DataPoint(v, d) for v, d in izip(data, datetimes))
        return cls(_d, header)

    @classmethod
    def from_data_and_analysis_period(cls, data, analysis_period, header=None):
        """Create a list from data and analysis period."""
        return cls.from_data_and_datetimes(data, analysis_period.datetimes, header)

    @property
    def header(self):
        """Get or set header."""
        return self._header

    @header.setter
    def header(self, h):
        self._header = None if not h else Header.from_header(h)

    def append(self, d):
        """Append a single item to the list."""
        assert hasattr(d, 'isDataPoint'), \
            'Expected DataPoint got {}'.format(type(d))
        self._data.append(d)

    def extend(self, new_data):
        """Extend a number of items to the end of items."""
        for d in new_data:
            assert hasattr(d, 'isDataPoint'), \
                'Expected DataPoint got {}'.format(type(d))
        self._data.extend(new_data)

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
        return self._data

    def duplicate(self):
        """Duplicate current data list."""
        return DataCollection(self.values, self.header)

    @staticmethod
    def average(data):
        """Return average value for a list of ladybug data."""
        values = (value.value for value in data)
        return sum(values) / len(data)

    @staticmethod
    def group_data_by_month(data, month_range=xrange(1, 13)):
        """Return a dictionary of values where values are grouped for each month.

        Key values are between 1-12

        Args:
            data: A list of DataPoint to be processed
            month_range: A list of numbers for months. Default is 1-12
        """
        hourly_data_by_month = OrderedDict()
        for m in month_range:
            hourly_data_by_month[m] = []

        for d in data:
            try:
                hourly_data_by_month[d.datetime.month].append(d)
            except KeyError:
                # month is not there
                pass

        return hourly_data_by_month

    def group_by_month(self, month_range=xrange(1, 13)):
        """
        Return a dictionary of values where values are grouped for each month.

        Key values are between 1-12

        Args:
           month_range: A list of numbers for months. Default is 1-12

        Usage:

           epwfile = EPW("epw file address")
           monthly_values = epwfile.dry_bulb_temperature.group_by_month()
           print(monthly_values[2]) # returns values for the month of March
        """
        return self.group_data_by_month(self.values, month_range)

    @staticmethod
    def group_data_by_day(data, day_range=xrange(1, 366)):
        """
        Return a dictionary of values where values are grouped by each day of year.

        Key values are between 1-365

        Args:
            data: A list of DataPoint to be processed
            day_range: A list of numbers for days. Default is 1-365
        """
        hourly_data_by_day = OrderedDict()
        for d in day_range:
            hourly_data_by_day[d] = []

        for d in data:
            try:
                hourly_data_by_day[d.datetime.doy].append(d)
            except KeyError:
                # day is not there
                pass

        return hourly_data_by_day

    def group_by_day(self, day_range=xrange(1, 366)):
        """
        Return a dictionary of values where values are grouped by each day of year.

        Key values are between 1-365

        Args:
            day_range: A list of numbers for days. Default is 1-365
            user_dataList: An optional data list of DataPoint to be processed

        Usage:

            epwfile = EPW("epw file address")
            daily_values = epwfile.dry_bulb_temperature.group_by_day(range(1, 30))
            print(daily_values[2]) # returns values for the second day of year
        """
        return self.group_data_by_day(self.values, day_range)

    @staticmethod
    def group_data_by_hour(data, hour_range=xrange(0, 24)):
        """Return a dictionary of values where values are grouped by each hour of day.

        Key values are between 0-23

        Args:
            data: A list of DataPoint to be processed
            hour_range: A list of numbers for hours. Default is 1-24
        """
        hourly_data_by_hour = OrderedDict()
        for h in hour_range:
            hourly_data_by_hour[h] = []

        for d in data:
            try:
                hourly_data_by_hour[d.datetime.hour].append(d)
            except KeyError:
                # day is not there
                pass

        return hourly_data_by_hour

    def group_by_hour(self, hour_range=xrange(0, 24)):
        """Return a dictionary of values where values are grouped by each hour of day.

        Key values are between 0-23

        Args:
            hour_range: A list of numbers for hours. Default is 1-24
            user_dataList: An optional data list of DataPoint to be processed

        Usage:

            epwfile = EPW("epw file address")
            monthly_values = epwfile.dry_bulb_temperature.group_by_month([1])
            grouped_hourly_data = epwfile.dry_bulb_temperature.group_data_dataBy_hour(
                monthly_values[1])
            for hour, data in grouped_hourly_data.items():
                print("average temperature values for hour {} during JAN is {} {}"
                      .format(hour, core._dataList.average(data), DBT.header.unit))
        """
        return self.group_data_by_hour(self.values, hour_range)

    def update_data_for_hours_of_year(self, values, hours_of_year):
        """Update values new set of values for a list of hours of the year.

        Length of values should be equal to number of hours in hours of year.

        Args:
            values: A list of values to be replaced in the file
            hours_of_year: A list of hoy between 1 and 8760
        """
        # check length of data vs length of analysis hours_of_year
        if len(values) != len(hours_of_year):
            raise ValueError("Length of values %d is not equal to " +
                             "number of hours in analysis period %d" %
                             (len(values), len(hours_of_year)))

        # update values
        updated_count = 0
        for data in self.values:
            try:
                # find matching index for input data
                index = hours_of_year.index(data.datetime.hoy)
            except ValueError:
                continue
            else:
                # update the value
                data.value = values[index]
                updated_count += 1

        print("%s updated for %d hour%s." %
              ('Values are' if len(values) > 1 else 'Value is',
               updated_count,
               's' if len(values) > 1 else ''))

        # return self for chaining methods
        return self

    def update_data_for_an_hour(self, value, hour_of_year):
        """
        Replace current value in data list with a new value for a specific hoy.

        Args:
            value: A single value
            hours_of_year: The hour of the year
        """
        return self.update_data_for_hours_of_year((value,), (hour_of_year,))

    def update_data_for_analysis_period(self, values, analysis_period):
        """Update values with new set of values for an analysis period.

        Length of values should be equal to number of hours in analysis period.

        Args:
            values: A list of values to be replaced in the file
            analysis_period: An analysis period for input the input values.
                Default is set to the whole year.
        """
        return self.update_data_for_hours_of_year(values, analysis_period.hoys)

    def interpolate_data(self, timestep):
        """Interpolate data for a finer timestep.

        Args:
            timestep: Target timestep as an integer. Target timestep must be
                divisable by current timestep.
        """
        assert timestep % self.header.analysis_period.timestep == 0, \
            'Target timestep({}) must be divisable by current timestep({})' \
            .format(timestep, self.header.analysis_period.timestep)

        _minutesStep = int(60 / int(timestep / self.header.analysis_period.timestep))
        _dataLength = len(self.values)
        # generate new data
        _data = tuple(
            self[d].__class__(_v, self[d].datetime.add_minute(step * _minutesStep))
            for d in xrange(_dataLength)
            for _v, step in zip(self.xxrange(self[d],
                                             self[(d + 1) % _dataLength],
                                             timestep),
                                xrange(timestep))
        )
        # generate data for last hour
        return _data

    @staticmethod
    def xxrange(start, end, step_count):
        """Generate n values between start and end."""
        _step = (end - start) / float(step_count)
        return (start + (i * _step) for i in xrange(int(step_count)))

    def filter_by_analysis_period(self, analysis_period=None):
        """
        Filter a list based on an analysis period.

        Args:
           analysis period: A Ladybug analysis period

        Return:
            A new _dataList with filtered data

        Usage:

           # start of Feb to end of Mar
           analysis_period = Analysis_period(2,1,1,3,31,24)
           epw = EPW("c:/ladybug/weatherdata.epw")
           DBT = epw.dry_bulb_temperature
           filteredDBT = DBT.filter_by_analysis_period(analysis_period)
        """
        if analysis_period.timestep != 1:
            # interpolate data for smaller timestep
            _int_data = self.interpolate_data(timestep=analysis_period.timestep)
            # create a new header
            _hea = self.header.duplicate()
            _hea.analysis_period = analysis_period
            _data = DataCollection(_int_data, _hea)
        else:
            _data = self

        if not analysis_period or analysis_period.is_annual:
            return _data.duplicate()

        # create a new filtered_data
        _filtered_data = _data.filter_by_hoys(analysis_period.hoys)
        if self.header:
            _filtered_data.header.analysis_period = analysis_period

        return _filtered_data

    def filter_by_moys(self, moys):
        """Filter the list based on a list of minutes of the year.

        Args:
           moys: A List of minutes of the year [0..8759 * 60]

        Return:
            A new _dataList with filtered data

        Usage:

           moys = range(0, 48 * 60)  # The first two days of the year
           epw = EPW("c:/ladybug/weatherdata.epw")
           DBT = epw.dry_bulb_temperature
           filteredDBT = DBT.filter_by_moys(moys)
        """
        # There is no guarantee that data is continuous so I iterate through the
        # each data point one by one
        _filtered_data = [d for d in self.values if d.datetime.moy in moys]

        # create a new filtered_data
        if self.header:
            _filteredHeader = self.header.duplicate()
            _filteredHeader.analysis_period = None
            return DataCollection(_filtered_data, _filteredHeader)
        else:
            return DataCollection(_filtered_data)

    def filter_by_hoys(self, hoys):
        """Filter the list based on an analysis period.

        Args:
           hoys: A List of hours of the year 0..8759

        Return:
            A new _dataList with filtered data

        Usage:

           hoys = range(1,48)  # The first two days of the year
           epw = EPW("c:/ladybug/weatherdata.epw")
           DBT = epw.dry_bulb_temperature
           filteredDBT = DBT.filter_by_hoys(hoys)
        """
        _moys = tuple(int(hour * 60) for hour in hoys)
        return self.filter_by_moys(_moys)

    def filter_by_conditional_statement(self, statement):
        """Filter the list based on a conditional statement.

        Args:
           statement: A conditional statement as a string (e.g. x>25 and x%5==0).
            The variable should always be named as x

        Return:
            A new _dataList with filtered data

        Usage:

           epw = EPW("c:/ladybug/weatherdata.epw")
           DBT = epw.dry_bulb_temperature
           # filter data for when dry bulb temperature is more then 25
           filtered_DBT = DBT.filter_by_conditional_statement('x > 25')
           # get the list of time stamps that meet the conditional statement
           print(filtered_DBT.time_stamps)
        """
        def check_input_statement(statement):
            st_statement = statement.lower() \
                .replace("and", "").replace("or", "") \
                .replace("not", "").replace("in", "").replace("is", "")

            parsed_st = [s for s in st_statement if s.isalpha()]
            if list(set(parsed_st)) != ['x']:
                statement_error_msg = 'Invalid input statement. ' + \
                    'Statement should be a valid Python statement' + \
                    ' and the variable should be named as x'
                raise ValueError(statement_error_msg)

        check_input_statement(statement)

        statement = statement.replace('x', 'd.value')
        _filtered_data = [d for d in self.values if eval(statement)]

        # create a new filtered_data
        if self.header:
            _filteredHeader = self.header.duplicate()
            _filteredHeader.analysis_period = None
            return DataCollection(_filtered_data, _filteredHeader)
        else:
            return DataCollection(_filtered_data)

    def filter_by_pattern(self, pattern):
        """Filter the list based on a list of Boolean.

        Length of Boolean should be equal to length of values in _dataList

        Args:
            pattern: A list of True, False values

        Return:
            A new _dataList with filtered data
        """
        try:
            _len = len(pattern)
        except TypeError:
            raise ValueError("pattern should be a list of values.")

        _filtered_data = [d for count, d in enumerate(self.values)
                          if pattern[count % _len]]

        # create a new filtered_data
        if self.header:
            _filteredHeader = self.header.duplicate()
            _filteredHeader.analysis_period = None
            return DataCollection(_filtered_data, _filteredHeader)
        else:
            return DataCollection(_filtered_data)

    def average_data_monthly(self, data):
        """Return a dictionary of values for average values for available months."""
        # group data for each month
        monthly_values = self.group_data_by_month(data)

        average_values = OrderedDict()

        # average values for each month
        for month, values in monthly_values.iteritems():
            average_values[month] = self.average(values)

        return average_values

    def average_monthly(self):
        """Return a dictionary of values for average values for available months."""
        return self.average_data_monthly(self.values)

    def average_data_monthly_for_each_hour(self, data):
        """Calculate average value for each hour during each month.

        This method returns a dictionary with nested dictionaries for each hour
        """
        # get monthy values
        monthly_hourly_values = self.group_data_by_month(data)

        # group data for each hour in each month and collect them in a dictionary
        averaged_monthly_values_per_hour = OrderedDict()
        for month, monthly_values in monthly_hourly_values.iteritems():
            if month not in averaged_monthly_values_per_hour:
                averaged_monthly_values_per_hour[month] = OrderedDict()

            # group data for each hour
            grouped_hourly_data = self.group_data_by_hour(monthly_values)
            for hour, data in grouped_hourly_data.items():
                averaged_monthly_values_per_hour[month][hour] = self.average(data)

        return averaged_monthly_values_per_hour

    def average_monthly_for_each_hour(self):
        """Calculate average value for each hour during each month.

        This method returns a dictionary with nested dictionaries for each hour
        """
        return self.average_data_monthly_for_each_hour(self.values)

    def __len__(self):
        return len(self._data)

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        raise TypeError('Use update_data_for_an_hour to set the values.')

    def __delitem__(self, key):
        del self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __reversed__(self):
        return reversed(self._data)

    def __contains__(self, item):
        return item in self._data

    def to_json(self):
        """Convert data collection to a dictionary."""
        return {
            'data': [d.to_json() for d in self._data],
            'header': self.header.to_json()
        }

    def ToString(self):
        """Overwrite .NET ToString method."""
        return self.__repr__()

    def __repr__(self):
        """_data collection representation."""
        if self.header and self.header.data_type:
            return "{}: #{}".format(self.header.data_type, len(self._data))
        else:
            return "DataCollection: #{}".format(len(self._data))
