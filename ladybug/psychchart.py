# coding=utf-8
"""Object for calculating PMV comfort from DataCollections."""
from __future__ import division

from ladybug_geometry.geometry2d.pointvector import Point2D, Vector2D
from ladybug_geometry.geometry2d.line import LineSegment2D
from ladybug_geometry.geometry2d.polyline import Polyline2D
from ladybug_geometry.geometry2d.mesh import Mesh2D
from ladybug_geometry.geometry3d.pointvector import Point3D

from .epw import EPW
from .datacollection import DailyCollection, HourlyContinuousCollection, \
    HourlyDiscontinuousCollection
from .psychrometrics import humid_ratio_from_db_rh, db_temp_from_enth_hr, \
    db_temp_from_rh_hr, db_temp_and_hr_from_wb_rh
from .legend import LegendParameters
from .graphic import GraphicContainer

from .datatype.time import Time
from .datatype.temperature import Temperature
from .datatype.fraction import Fraction
from .datatype.specificenergy import Enthalpy


class PsychrometricChart(object):
    """Class for constructing psychrometric charts and plotting data on them.

    Args:
        temperature: Hourly, daily, or sub-hourly data collection of temperature
            values in Celsius or a single temperature value to be used for the
            whole analysis.
        relative_humidity: Hourly, daily, or sub-hourly data collection of relative
            humidity values in % or a single relative humidity value to be used
            for the whole analysis.
        average_pressure: Number for the average air pressure across the data
            plotted on the chart (Pa). (Default: 101325 Pa; pressure at sea level).
        legend_parameters: An optional LegendParameter object to change the display
            of the PsychrometricChart. (Default: None).
        base_point: A Point2D to be used as a starting point to generate the geometry
            of the plot. (Default: (0, 0)).
        x_dim: A number to set the X dimension of each degree of temperature on the
            chart. (Default: 1).
        y_dim: A number to set the Y dimension of a unity humidity ratio on the chart.
            Note that most maximum humidity ratios are around 0.03. (Default: 1500).
        min_temperature: An integer for the minimum temperature on the chart in
            degrees. This should be celsius if use_ip is False and fahrenheit if
            use_ip is True. (Default: -20; suitable for celsius).
        max_temperature: An integer for the maximum temperature on the chart in
            degrees. This should be celsius if use_ip is False and fahrenheit if
            use_ip is True. (Default: 50; suitable for celsius).
        max_humidity_ratio: A value for the maximum humidity ratio in kg water / kg
            air. (Default: 0.03).
        use_ip: Boolean to note whether temperature values should be plotted in
            Fahrenheit instead of Celsius. (Default: False).

    Properties:
        * temperature
        * relative_humidity
        * average_pressure
        * legend_parameters
        * base_point
        * x_dim
        * y_dim
        * min_temperature
        * max_temperature
        * max_humidity_ratio
        * use_ip
        * saturation_line
        * chart_border
        * temperature_labels
        * temperature_label_points
        * temperature_lines
        * rh_labels
        * rh_label_points
        * rh_lines
        * hr_labels
        * hr_label_points
        * hr_lines
        * enthalpy_labels
        * enthalpy_label_points
        * enthalpy_lines
        * wb_labels
        * wb_label_points
        * wb_lines
        * title_text
        * title_location
        * x_axis_text
        * x_axis_location
        * y_axis_text
        * y_axis_location
        * data_points
        * time_matrix
        * hour_values
        * colored_mesh
        * legend
        * container
    """
    ACCEPTABLE_COLLECTIONS = (DailyCollection, HourlyContinuousCollection,
                              HourlyDiscontinuousCollection)
    TEMP_TYPE = Temperature()
    ENTH_TYPE = Enthalpy()

    def __init__(self, temperature, relative_humidity, average_pressure=101325,
                 legend_parameters=None, base_point=Point2D(), x_dim=1, y_dim=1500,
                 min_temperature=-20, max_temperature=50, max_humidity_ratio=0.03,
                 use_ip=False):
        """Initialize Psychrometric Chart."""
        # check and assign the temperature and humidity
        self._use_ip = bool(use_ip)
        self._calc_length = 1
        self._time_multiplier = 1
        self._temperature = temperature
        self._relative_humidity = relative_humidity
        self._t_values = self._t_values_c = self._check_input(
            temperature, Temperature, 'C', 'temperature')
        self._rh_values = self._check_input(
            relative_humidity, Fraction, '%', 'relative_humidity')
        if len(self._t_values) == 1:
            self._t_values = self._t_values_c = self._t_values * self._calc_length
        if self._use_ip:  # convert everything to Fahrenheit
            self._t_values = self.TEMP_TYPE.to_unit(self._t_values, 'F', 'C')
        assert len(self._t_values) == len(self._rh_values), \
            'Number of temperature and humidity values must match.'

        # assign the inputs as properties of the chart
        self._average_pressure = self._check_number(average_pressure, 'average_pressure')
        assert isinstance(base_point, Point2D), 'Expected Point2D for ' \
            'PsychrometricChart base point. Got {}.'.format(type(base_point))
        self._base_point = base_point
        self._x_dim = self._check_number(x_dim, 'x_dim')
        self._y_dim = self._check_number(y_dim, 'y_dim')
        assert max_temperature - min_temperature >= 10, 'Psychrometric chart ' \
            'max_temperature and min_temperature difference must be at least 10.'
        self._max_temperature = int(max_temperature)
        self._min_temperature = int(min_temperature)
        self._max_humidity_ratio = float(max_humidity_ratio)
        assert self._max_humidity_ratio >= 0.005, 'Psychrometric chart ' \
            'max_humidity_ratio must be at least 0.005.'

        # create the graphic container
        if self._use_ip:  # categorize based on every 1.66 fahrenheit
            self._t_category = []
            current_t, max_t = self._min_temperature, self._max_temperature + 1.75
            while current_t < max_t:
                current_t += (5 / 3)
                self._t_category.append(current_t)
        else:  # categorize based on every degree celsius
            self._t_category = list(range(self._min_temperature + 1,
                                          self._max_temperature + 1))
        self._rh_category = list(range(5, 105, 5))
        self._time_matrix, self._hour_values, self._remove_pattern = \
            self._compute_hour_values()
        assert len(self._hour_values) > 0, \
            'No data was found to lie on the psychrometric chart.'
        max_x = base_point.x + (self._max_temperature - self._min_temperature + 5) \
            * self._x_dim
        max_pt = Point3D(max_x, self.hr_y_value(self.max_humidity_ratio), 0)
        min_pt = Point3D(base_point.x, base_point.y, 0)
        self._container = GraphicContainer(
            self._hour_values, min_pt, max_pt, legend_parameters, Time(), 'hr')
        self._process_legend_default(self._container.legend_parameters)

        # create global attributes used by several of the geometry properties
        self._temp_range = list(range(self._min_temperature, self._max_temperature, 5)) \
            + [self._max_temperature]
        self._x_range = [self.t_x_value(t) for t in self._temp_range]
        if use_ip:  # ensure that _temp_range is always in celsius
            self._temp_range = self.TEMP_TYPE.to_unit(self._temp_range, 'C', 'F')
        rh_range = range(10, 110, 10)
        self._rh_lines = tuple(self.relative_humidity_polyline(rh) for rh in rh_range)
        self._saturation_line = self.relative_humidity_polyline(100, 2)
        max_hr_thnd = int(self._max_humidity_ratio * 1000)
        base_hr_range = list(range(5, max_hr_thnd, 5)) + [max_hr_thnd]
        max_db_hr = 1000 * humid_ratio_from_db_rh(
            self._temp_range[-1], 100, self._average_pressure)
        base_hr_range = [val for val in base_hr_range if val <= max_db_hr]
        self._hr_range = tuple(round(val / 1000, 3) for val in base_hr_range)
        self._y_range = [self._y_dim * hr + self._base_point.y for hr in self._hr_range]

        # set null values for properties that are optional
        self._chart_border = None
        self._enth_range = None
        self._enth_lines = None
        self._wb_range = None
        self._wb_lines = None
        self._data_points = None
        self._colored_mesh = None

        # check to be sure we don't have conditions above the boiling point
        assert self._temp_range[-1] < 100, \
            'Temperatures above the boiling point of water are not plot-able.'

    @classmethod
    def from_epw(cls, epw_file, legend_parameters=None, base_point=Point2D(),
                 x_dim=1, y_dim=1500, min_temperature=-20, max_temperature=50,
                 max_humidity_ratio=0.03, use_ip=False):
        """Create a psychrometric chart object using the data in an epw file.

        Args:
            epw_file: Full path to epw weather file.
            legend_parameters: An optional LegendParameter object to change the display
                of the PsychrometricChart. (Default: None).
            base_point: A Point2D to be used as a starting point to generate the geometry
                of the plot. (Default: (0, 0)).
            x_dim: A number to set the X dimension of each degree of temperature on the
                chart. (Default: 1).
            y_dim: A number to set the Y dimension of unity humidity ratio on the chart.
                Note that most maximum humidity ratios are around 0.03. (Default: 1500).
            min_temperature: An integer for the minimum temperature on the chart in
                degrees. This should be celsius if use_ip is False and fahrenheit if
                use_ip is True. (Default: -20; suitable for celsius).
            max_temperature: An integer for the maximum temperature on the chart in
                degrees. This should be celsius if use_ip is False and fahrenheit if
                use_ip is True. (Default: 50; suitable for celsius).
            max_humidity_ratio: A value for the maximum humidity ratio in kg water / kg
                air. (Default: 0.03).
            use_ip: Boolean to note whether temperature values should be plotted in
                Fahrenheit instead of Celsius. (Default: False).
        """
        epw = EPW(epw_file)
        pressure = epw.atmospheric_station_pressure.average
        return cls(
            epw.dry_bulb_temperature, epw.relative_humidity, pressure, legend_parameters,
            base_point, x_dim, y_dim, min_temperature, max_temperature,
            max_humidity_ratio, use_ip)

    @classmethod
    def from_dict(cls, data):
        """ Create PsychrometricChart from a dictionary

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            'type': 'PsychrometricChart',
            'temperature': {},  # data collection or value for temperature [C]
            'relative_humidity': {},  # data collection or value for humidity [%]
            'average_pressure': 101325,  # average atmospheric pressure [Pa]
            'legend_parameters': {},  # legend parameters dictionary
            'base_point': {},  # Point2D dictionary
            'x_dim': 1.0,  # value for X dimension per degree
            'y_dim': 1500.0,  # value for Y dimension for unity humidity ratio
            'min_temperature': -20.0,  # value for minimum temperature
            'max_temperature': 50.0,  # value for maximum temperature
            'max_humidity_ratio': 0.03,  # value for maximum humidity ratio
            'use_ip': False,  # boolean for whether to use IP values
            }
        """
        # process the optional inputs
        p = data['average_pressure'] if 'average_pressure' in data else 101325
        lp = LegendParameters.from_dict(data['legend_parameters']) \
            if 'legend_parameters' in data else None
        bpt = Point2D.from_dict(data['base_point']) if 'base_point' in data \
            else Point2D()
        xd = data['x_dim'] if 'x_dim' in data else 1
        yd = data['y_dim'] if 'y_dim' in data else 1500
        tmin = data['min_temperature'] if 'min_temperature' in data else -20
        tmax = data['max_temperature'] if 'max_temperature' in data else 50
        hrmax = data['max_humidity_ratio'] if 'max_humidity_ratio' in data else 0.03
        ip = data['use_ip'] if 'use_ip' in data else False

        # process the data collections
        class_mapper = {
            'DailyCollection': DailyCollection,
            'HourlyContinuousCollection': HourlyContinuousCollection,
            'HourlyDiscontinuousCollection': HourlyDiscontinuousCollection}
        t_data, rh_data = data['temperature'], data['relative_humidity']
        temp = class_mapper[t_data['type']].from_dict(t_data) \
            if isinstance(t_data, dict) else t_data
        rh = class_mapper[rh_data['type']].from_dict(rh_data) \
            if isinstance(rh_data, dict) else rh_data
        return cls(temp, rh, p, lp, bpt, xd, yd, tmin, tmax, hrmax, ip)

    @property
    def temperature(self):
        """The temperature assigned to this psychrometric chart [C]."""
        return self._temperature

    @property
    def relative_humidity(self):
        """The relative humidity assigned to this psychrometric chart."""
        return self._relative_humidity

    @property
    def average_pressure(self):
        """the average air pressure across the data plotted on the chart (Pa)."""
        return self._average_pressure

    @property
    def legend_parameters(self):
        """The legend parameters customizing this psychrometric chart."""
        return self._container.legend_parameters

    @property
    def base_point(self):
        """Point3D for the base point of this psychrometric chart."""
        return self._base_point

    @property
    def x_dim(self):
        """The X dimension of each degree of temperature on the chart."""
        return self._x_dim

    @property
    def y_dim(self):
        """The Y dimension of a unity humidity ratio on the chart."""
        return self._y_dim

    @property
    def min_temperature(self):
        """An integer for the minimum temperature on the chart.

        Will be in celsius if use_ip is False and fahrenheit if use_ip is True.
        """
        return self._min_temperature

    @property
    def max_temperature(self):
        """An integer for the maximum temperature on the chart.

        Will be in celsius if use_ip is False and fahrenheit if use_ip is True.
        """
        return self._max_temperature

    @property
    def max_humidity_ratio(self):
        """A value for the maximum humidity ratio in kg water / kg air."""
        return self._max_humidity_ratio

    @property
    def use_ip(self):
        """Boolean for whether temperature should be in Fahrenheit or Celsius."""
        return self._use_ip

    @property
    def saturation_line(self):
        """Get a Polyline2D for the saturation line of the chart."""
        return self._saturation_line

    @property
    def chart_border(self):
        """Get a Polyline2D for the border of the chart (excluding saturation line)."""
        if self._chart_border is None:
            self._chart_border = self._compute_border()
        return self._chart_border

    @property
    def temperature_labels(self):
        """Get a tuple of text for the temperature labels on the chart."""
        if self.use_ip:
            temp_range = tuple(range(self._min_temperature, self._max_temperature, 5)) \
                + (self._max_temperature,)
            return tuple(str(val) for val in temp_range)
        return tuple(str(val) for val in self._temp_range)

    @property
    def temperature_label_points(self):
        """Get a tuple of Point2Ds for the temperature labels on the chart."""
        y_val = self._base_point.y - self.legend_parameters.text_height * 0.5
        return tuple(Point2D(x_val, y_val) for x_val in self._x_range)

    @property
    def temperature_lines(self):
        """Get a tuple of LineSegment2Ds for the temperature labels on the chart."""
        # get the Y-values for the top of the temperature lines
        hr_vals = (humid_ratio_from_db_rh(t, 100, self.average_pressure)
                   for t in self._temp_range)
        top_y = []
        for hr in hr_vals:
            y_val = self.hr_y_value(hr) if hr < self._max_humidity_ratio \
                else self.hr_y_value(self._max_humidity_ratio)
            top_y.append(y_val)

        t_lines = []  # create the array of line segments
        for x_val, y_val in zip(self._x_range, top_y):
            l_seg = LineSegment2D.from_end_points(
                Point2D(x_val, self._base_point.y), Point2D(x_val, y_val))
            t_lines.append(l_seg)
        return t_lines

    @property
    def rh_labels(self):
        """Get a tuple of text for the relative humidity labels on the chart."""
        return tuple('{}%'.format(val) for val in range(10, 110, 10))

    @property
    def rh_label_points(self):
        """Get a tuple of Point2Ds for the relative humidity labels on the chart."""
        last_sgs = (LineSegment2D.from_end_points(p[-2], p[-1]) for p in self._rh_lines)
        last_dirs = (seg.v.reverse().normalize() * (self._x_dim * 2) for seg in last_sgs)
        move_vec = (Vector2D(vec.x - (self._x_dim * 0.4), vec.y) for vec in last_dirs)
        return tuple(pl[-1].move(vec) for pl, vec in zip(self._rh_lines, move_vec))

    @property
    def rh_lines(self):
        """Get a tuple of Polyline2Ds for the relative humidity labels on the chart."""
        return self._rh_lines

    @property
    def hr_labels(self):
        """Get a tuple of text for the humidity ratio labels on the chart."""
        return tuple(str(val) for val in self._hr_range)

    @property
    def hr_label_points(self):
        """Get a tuple of Point2Ds for the humidity ratio labels on the chart."""
        x_val = self._x_range[-1] + self.legend_parameters.text_height * 0.5
        return tuple(Point2D(x_val, y_val) for y_val in self._y_range)

    @property
    def hr_lines(self):
        """Get a tuple of LineSegment2Ds for the humidity ratio labels on the chart."""
        hr_lines, xmax = [], self._x_range[-1]
        for hr, y in zip(self._hr_range, self._y_range):
            tmin = db_temp_from_rh_hr(100, hr, self.average_pressure)
            tmin = self.TEMP_TYPE.to_unit([tmin], 'F', 'C')[0] if self.use_ip else tmin
            xmin = self.t_x_value(tmin)
            xmin = xmin if xmin > self.base_point.x else self.base_point.x
            l_seg = LineSegment2D.from_end_points(Point2D(xmax, y), Point2D(xmin, y))
            hr_lines.append(l_seg)
        return hr_lines

    @property
    def enthalpy_labels(self):
        """Get a tuple of text for the enthalpy labels on the chart."""
        if self._enth_range is None:
            self._compute_enthalpy_range()
        return tuple('{} kJ/kg'.format(val) for val in self._enth_range) if not \
            self.use_ip else tuple('{} Btu/lb'.format(val) for val in self._enth_range)

    @property
    def enthalpy_label_points(self):
        """Get a tuple of Point2Ds for the humidity ratio labels on the chart."""
        if self._enth_lines is None:
            self._compute_enthalpy_range()
        return self._labels_points_from_lines(self._enth_lines)

    @property
    def enthalpy_lines(self):
        """Get a tuple of LineSegment2Ds for the humidity ratio labels on the chart."""
        if self._enth_lines is None:
            self._compute_enthalpy_range()
        return self._enth_lines

    @property
    def wb_labels(self):
        """Get a tuple of text for the wet bulb labels on the chart."""
        if self._wb_range is None:
            self._compute_wb_range()
        return tuple('{} C'.format(val) for val in self._wb_range) if not \
            self.use_ip else tuple('{} F'.format(val) for val in self._wb_range)

    @property
    def wb_label_points(self):
        """Get a tuple of Point2Ds for the wet bulb labels on the chart."""
        if self._wb_lines is None:
            self._compute_wb_range()
        return self._labels_points_from_lines(self._wb_lines)

    @property
    def wb_lines(self):
        """Get a tuple of LineSegment2Ds for the wet bulb temp labels on the chart."""
        if self._wb_lines is None:
            self._compute_wb_range()
        return self._wb_lines

    @property
    def title_text(self):
        """Get text for the title of the chart."""
        title_items = ['Time [hr]']
        extra_data = []
        if isinstance(self.temperature, self.ACCEPTABLE_COLLECTIONS):
            extra_data = self.temperature.header.metadata.items()
        elif isinstance(self.relative_humidity, self.ACCEPTABLE_COLLECTIONS):
            extra_data = self.relative_humidity.header.metadata.items()
        return '\n'.join(title_items + ['{}: {}'.format(k, v) for k, v in extra_data])

    @property
    def title_location(self):
        """Get a Point2D for the title of the chart."""
        origin = self.container.upper_title_location.o
        return Point2D(origin.x, origin.y)

    @property
    def x_axis_text(self):
        """Get text for the X-axis label of the chart."""
        unit = 'C' if not self.use_ip else 'F'
        if isinstance(self.temperature, self.ACCEPTABLE_COLLECTIONS):
            if 'type' in self.temperature.header.metadata:
                return '{} [{}]'.format(self.temperature.header.metadata['type'], unit)
            else:
                return '{} [{}]'.format(self.temperature.header.data_type, unit)
        return 'Temperature [{}]'.format(unit)

    @property
    def x_axis_location(self):
        """Get a Point2D for the X-axis label of the chart."""
        y_val = self._base_point.y - self.legend_parameters.text_height * 2.5
        return Point2D(self.base_point.x, y_val)

    @property
    def y_axis_text(self):
        """Get text for the Y-axis label of the chart."""
        unit = 'kg' if not self.use_ip else 'lb'
        return 'Humidity Ratio\n[{0} water / {0} air]'.format(unit)

    @property
    def y_axis_location(self):
        """Get a Point2D for the Y-axis label of the chart."""
        x_val = self._container.max_point.x + self.legend_parameters.text_height * 1.5
        return Point2D(x_val, self._container.max_point.y)

    @property
    def data_points(self):
        """Get a tuple of Point2Ds for each of the temperature and humidity values."""
        if self._data_points is None:
            p = self._average_pressure
            self._data_points = tuple(
                Point2D(
                    self.t_x_value(t), self.hr_y_value(humid_ratio_from_db_rh(c, r, p)))
                for t, c, r in zip(self._t_values, self._t_values_c, self._rh_values))
        return self._data_points

    @property
    def time_matrix(self):
        """Get a tuple of of tuples where each sub-tuple is a row of the mesh.

        Each value in the resulting matrix corresponds to the number of temperature/
        humidity points in a given cell of the mesh.
        """
        return tuple(tuple(row) for row in self._time_matrix)

    @property
    def hour_values(self):
        """Get a tuple for the number of hours associated with each colored_mesh face."""
        return self._hour_values

    @property
    def colored_mesh(self):
        """Get a colored mesh for the number of hours for each part of the chart."""
        if self._colored_mesh is None:
            self._colored_mesh = self._generate_mesh()
        return self._colored_mesh

    @property
    def legend(self):
        """The legend assigned to this graphic."""
        return self._container._legend

    @property
    def container(self):
        """Get the GraphicContainer for the colored mesh."""
        return self._container

    def plot_point(self, temperature, relative_humidity):
        """Get a Point2D for a given temperature and relative humidity on the chart.

        Args:
            temperature: A temperature value, which should be in Celsius if use_ip
                is False and Fahrenheit is use_ip is True.
            relative_humidity: A relative humidity value in % (from 0 to 100).
        """
        tc = temperature if not self.use_ip else \
            self.TEMP_TYPE.to_unit([temperature], 'C', 'F')[0]
        hr = humid_ratio_from_db_rh(tc, relative_humidity, self.average_pressure)
        return Point2D(self.t_x_value(temperature), self.hr_y_value(hr))

    def data_mesh(self, data_collection, legend_parameters=None):
        """Get a colored mesh for a data_collection aligned with the chart's data.

        Args:
            data_collection: A data collection that is aligned with the temperature
                and humidity values of the chart.
            legend_parameters: Optional legend parameters to customize the legend
                and look of the resulting mesh.

        Returns:
            A tuple with two values.

            -   mesh: A colored Mesh2D similar to the chart's colored_mesh property
                but where each face is colored with the average value of the input
                data_collection.

            -   container: A GraphicContainer object for the mesh, which possesses
                a legend that corresponds to the mesh.
        """
        # check to be sure the data collection aligns
        data_vals = data_collection.values
        assert len(data_vals) == self._calc_length, 'Number of data collection values ' \
            'must match those of the psychometric chart temperature and humidity.'

        # create a matrix with a tally of the hours for all the data
        base_mtx = [[[] for val in self._t_category] for rh in self._rh_category]
        for t, rh, val in zip(self._t_values, self._rh_values, data_vals):
            if t < self._min_temperature or t > self._max_temperature:
                continue  # temperature value does not currently fit on the chart
            for y, rh_cat in enumerate(self._rh_category):
                if rh < rh_cat:
                    break
            for x, t_cat in enumerate(self._t_category):
                if t < t_cat:
                    break
            base_mtx[y][x].append(val)

        # compute average values
        avg_values = [sum(val_list) / len(val_list) for rh_l in base_mtx
                      for val_list in rh_l if len(val_list) != 0]

        # create the colored mesh and graphic container
        base_contain = self.container
        container = GraphicContainer(
            avg_values, base_contain.min_point, base_contain.max_point,
            legend_parameters, data_collection.header.data_type,
            data_collection.header.unit)
        self._process_legend_default(container.legend_parameters)
        mesh = self.colored_mesh.duplicate()  # start with hour mesh as a base
        mesh.colors = container.value_colors
        return mesh, container

    def relative_humidity_polyline(self, rh, subdivisions=1):
        """Get a Polyline2D for a given relative humidity value.

        Args:
            rh: A number between 0 and 100 for the relative humidity line to draw.
            subdivisions: Integer for the number of subdivisions for every 5
                degrees. (Default: 1).
        """
        # get the HR values and temperatures
        prs = self.average_pressure
        if subdivisions == 1:
            hr_vals = [humid_ratio_from_db_rh(t, rh, prs) for t in self._temp_range]
            x_vals = self._x_range
        else:  # build up custom temperatures and HRs
            hr_vals = [humid_ratio_from_db_rh(self._temp_range[0], rh, prs)]
            x_vals = [self._x_range[0]]
            t_diff = (self._temp_range[1] - self._temp_range[0]) / subdivisions
            x_diff = (self._x_range[1] - self._x_range[0]) / subdivisions
            for i in range(len(self._temp_range) - 1):
                st_t, st_x = self._temp_range[i], self._x_range[i]
                for j in range(subdivisions):
                    t = st_t + (j + 1) * t_diff
                    hr_vals.append(humid_ratio_from_db_rh(t, rh, prs))
                    x_vals.append(st_x + (j + 1) * x_diff)

        # loop through the values and create the points
        pts = []
        for i, (x, hr) in enumerate(zip(x_vals, hr_vals)):
            if hr < self._max_humidity_ratio:
                pts.append(Point2D(x, self.hr_y_value(hr)))
            else:  # we're at the top of the chart; cut it off
                if abs(self._max_humidity_ratio - hr_vals[i - 1]) < 0.001:
                    del pts[-1]  # avoid the case of a bad interpolation
                last_db = db_temp_from_rh_hr(
                    rh, self._max_humidity_ratio, self.average_pressure)
                last_db = self.TEMP_TYPE.to_unit([last_db], 'F', 'C')[0] \
                    if self.use_ip else last_db
                x_val = self.t_x_value(last_db)
                pts.append(Point2D(x_val, self.hr_y_value(self._max_humidity_ratio)))
                break
        return Polyline2D(pts, interpolated=True)

    def hr_y_value(self, humidity_ratio):
        """Get the Y-coordinate associated with a certain HR on the chart.

        Args:
            humidity_ratio: A humidity ratio value in kg water / kg air.
        """
        return self.base_point.y + humidity_ratio * self._y_dim

    def t_x_value(self, temperature):
        """Get the X-coordinate associated with a certain temperature on the chart.

        Args:
            temperature: A temperature value, which should be in Celsius if use_ip
                is False and Fahrenheit is use_ip is True.
        """
        return self._base_point.x + self._x_dim * (temperature - self._min_temperature)

    def to_dict(self):
        """Get psychrometric chart as a dictionary."""
        temp = self.temperature
        temp = temp.to_dict() if isinstance(temp, self.ACCEPTABLE_COLLECTIONS) else temp
        rh = self.relative_humidity
        rh = rh.to_dict() if isinstance(rh, self.ACCEPTABLE_COLLECTIONS) else rh
        return {
            'temperature': temp,
            'relative_humidity': rh,
            'average_pressure': self.average_pressure,
            'legend_parameters': self.legend_parameters.to_dict(),
            'base_point': self.base_point.to_dict(),
            'x_dim': self.x_dim,
            'y_dim': self.y_dim,
            'min_temperature': self.min_temperature,
            'max_temperature': self.max_temperature,
            'max_humidity_ratio': self.max_humidity_ratio,
            'use_ip': self.use_ip,
            'type': 'PsychrometricChart'
        }

    def _compute_hour_values(self):
        """Compute the matrix of binned time values based on the chart inputs.

        Returns:
            A tuple with three values.

            -   base_mtx: A full matrix with counts of values for each degree
                temperature and 5% RH of the chart.

            -   mesh_values: A list of numbers for the values of the mesh.

            -   remove_pattern: A list of booleans for which faces of the full mesh
                should be removed.
        """
        # create a matrix with a tally of the hours for all the data
        base_mtx = [[0 for val in self._t_category] for rh in self._rh_category]
        for t, rh in zip(self._t_values, self._rh_values):
            if t < self._min_temperature or t > self._max_temperature:
                continue  # temperature value does not currently fit on the chart
            for y, rh_cat in enumerate(self._rh_category):
                if rh < rh_cat:
                    break
            for x, t_cat in enumerate(self._t_category):
                if t < t_cat:
                    break
            base_mtx[y][x] += 1

        # flatten the matrix and create a pattern to remove faces
        flat_values = [tc * self._time_multiplier for rh_l in base_mtx for tc in rh_l]
        remove_pattern = [val != 0 for val in flat_values]
        mesh_values = tuple(val for val in flat_values if val != 0)
        return base_mtx, mesh_values, remove_pattern

    def _generate_mesh(self):
        """Get the colored mesh from this object's hour values."""
        # global properties used in the generation of the mesh
        prs = self.average_pressure
        t_per_row = [self._min_temperature] + self._t_category
        x_per_row = [self.t_x_value(t) for t in t_per_row]
        temp_in_c = self.TEMP_TYPE.to_unit(t_per_row, 'C', 'F') \
            if self.use_ip else t_per_row

        # loop through RH rows and create mesh vertices and faces
        vertices = [Point2D(x, self._base_point.y) for x in x_per_row]
        faces, vert_count, row_len = [], 0, len(t_per_row)
        for rh in self._rh_category:
            vert_count += row_len
            y1 = self.hr_y_value(humid_ratio_from_db_rh(temp_in_c[0], rh, prs))
            vertices.append(Point2D(x_per_row[0], y1))
            for i, t in enumerate(temp_in_c[1:]):
                y = self.hr_y_value(humid_ratio_from_db_rh(t, rh, prs))
                vertices.append(Point2D(x_per_row[i + 1], y))
                v1 = vert_count - row_len + i
                v2 = v1 + 1
                v3 = vert_count + i + 1
                v4 = v3 - 1
                faces.append((v1, v2, v3, v4))

        # create the Mesh2D, remove unused faces, and assign the colors
        mesh = Mesh2D(vertices, faces)
        mesh = mesh.remove_faces_only(self._remove_pattern)
        mesh.colors = self._container.value_colors
        return mesh

    def _compute_border(self):
        """Compute a Polyline2D for the outer border of the chart."""
        # get properties used to establish the border of the chart
        prs, bpt, hmax = self.average_pressure, self.base_point, self.max_humidity_ratio
        max_hr = humid_ratio_from_db_rh(self._temp_range[-1], 100, prs)
        y_left = self.hr_y_value(humid_ratio_from_db_rh(self._temp_range[0], 100, prs))
        y_right = self.hr_y_value(hmax) if max_hr > hmax else self.hr_y_value(max_hr)
        x_max = bpt.x + (self.max_temperature - self.min_temperature) * self._x_dim

        # get the points and build the polyline
        pt1, pt2, pt3, pt4 = \
            Point2D(bpt.x, y_left), bpt, Point2D(x_max, bpt.y), Point2D(x_max, y_right)
        if max_hr > hmax:
            return Polyline2D((pt1, pt2, pt3, pt4, self._saturation_line[-1]))
        return Polyline2D((pt1, pt2, pt3, pt4))

    def _compute_enthalpy_range(self):
        """Compute the values for enthalpy range and lines."""
        # constants used throughout the calculation
        low_y = self.base_point.y + 1e-6
        up_y = self.hr_y_value(self._max_humidity_ratio)
        border, sat_line = self.chart_border, self._saturation_line
        all_enthalpies, ref_temp = tuple(range(0, 160, 10)), 0
        enth_lbl = all_enthalpies
        if self.use_ip:
            enth_lbl = tuple(range(0, 65, 5))
            all_enthalpies = self.ENTH_TYPE.to_unit(enth_lbl, 'kJ/kg', 'Btu/lb')
            ref_temp = self.TEMP_TYPE.to_unit([0], 'C', 'F')[0]

        # loop through the enthalpies and compute the lines of constant enthalpy
        enth_range, enth_lines = [], []
        for i, enthalpy in enumerate(all_enthalpies):
            st_db = db_temp_from_enth_hr(enthalpy, 0.0, ref_temp)
            end_db = db_temp_from_enth_hr(enthalpy, 0.03, ref_temp)
            if self.use_ip:
                st_db, end_db = self.TEMP_TYPE.to_unit((st_db, end_db), 'F', 'C')
            enth_line = LineSegment2D.from_end_points(
                Point2D(self.t_x_value(st_db), low_y),
                Point2D(self.t_x_value(end_db), up_y))
            border_ints = border.intersect_line_ray(enth_line)
            if len(border_ints) == 2:
                enth_range.append(enth_lbl[i])
                seg = LineSegment2D.from_end_points(border_ints[0], border_ints[1])
                enth_lines.append(seg)
            else:
                sat_ints = sat_line.intersect_line_ray(enth_line)
                if len(sat_ints) != 0:
                    enth_range.append(enth_lbl[i])
                    if len(border_ints) == 1:
                        seg = LineSegment2D.from_end_points(border_ints[0], sat_ints[0])
                    else:
                        seg = LineSegment2D.from_end_points(enth_line.p, sat_ints[0])
                    enth_lines.append(seg)

        # set the properties on this class
        self._enth_range = enth_range
        self._enth_lines = enth_lines

    def _compute_wb_range(self):
        """Compute the values for wet bulb range and lines."""
        # constants used throughout the calculation
        low_y, border = self.base_point.y - 1e-6, self.chart_border
        all_wbs = wb_c = tuple(range(self._min_temperature, self._max_temperature, 5))
        if self.use_ip:
            wb_c = self.TEMP_TYPE.to_unit(wb_c, 'C', 'F')

        # loop through the wet bulb and compute the lines of constant wet bulb
        wb_range, wb_lines = [], []
        for i, wb in enumerate(wb_c):
            st_db = db_temp_and_hr_from_wb_rh(wb, 0, self._average_pressure)[0]
            end_db, end_hr = db_temp_and_hr_from_wb_rh(wb, 100, self._average_pressure)
            if self.use_ip:
                st_db, end_db = self.TEMP_TYPE.to_unit((st_db, end_db), 'F', 'C')
            enth_line = LineSegment2D.from_end_points(
                Point2D(self.t_x_value(st_db), low_y),
                Point2D(self.t_x_value(end_db), self.hr_y_value(end_hr)))
            border_ints = border.intersect_line_ray(enth_line)
            if len(border_ints) == 2:
                wb_range.append(all_wbs[i])
                seg = LineSegment2D.from_end_points(border_ints[0], border_ints[1])
                wb_lines.append(seg)
            elif len(border_ints) == 1:
                wb_range.append(all_wbs[i])
                seg = LineSegment2D.from_end_points(border_ints[0], enth_line.p2)
                wb_lines.append(seg)

        # set the properties on this class
        self._wb_range = wb_range
        self._wb_lines = wb_lines

    def _labels_points_from_lines(self, label_lines):
        """Extract label points from lines."""
        move_vec = []
        base_pts = []
        for seg in label_lines:
            if seg.v.y < 0:
                move_vec.append(seg.v.reverse().normalize() * self._x_dim * 1.5)
                base_pts.append(seg.p1)
            else:
                move_vec.append(seg.v.normalize() * self._x_dim * 1.5)
                base_pts.append(seg.p2)
        return tuple(pt.move(vec) for pt, vec in zip(base_pts, move_vec))

    def _process_legend_default(self, l_par):
        """Override the dimensions of the legend to ensure it fits the chart."""
        min_pt, max_pt = self.container.min_point, self.container.max_point
        if l_par.vertical and l_par.is_segment_height_default:
            l_par.properties_3d.segment_height = (max_pt.y - min_pt.y) / 20
            l_par.properties_3d._is_segment_height_default = True
        elif l_par.vertical and l_par.is_segment_height_default:
            l_par.properties_3d.segment_width = (max_pt.x - min_pt.x) / 20
            l_par.properties_3d._is_segment_width_default = True

    def _check_input(self, data_coll, dat_type, unit, name):
        """Check an input that can be either a number or a Data Collection."""
        if isinstance(data_coll, self.ACCEPTABLE_COLLECTIONS):
            self._check_datacoll(data_coll, dat_type, unit, name)
            return data_coll.values
        else:
            try:  # assume that it's a single number
                value = float(data_coll)
                return [value] * self._calc_length
            except (ValueError, TypeError):
                raise TypeError('{} must be either a number or a hourly/daily data '
                                'collection. Got {}'.format(name, type(data_coll)))

    def _check_datacoll(self, data_coll, dat_type, unit, name):
        """Check the data type and units of a Data Collection."""
        assert isinstance(data_coll.header.data_type, dat_type) and \
            data_coll.header.unit == unit, '{} must be {} in {}. ' \
            'Got {} in {}'.format(name, dat_type().name, unit,
                                  data_coll.header.data_type.name,
                                  data_coll.header.unit)
        if isinstance(data_coll, DailyCollection):
            self._time_multiplier = 24
        else:  # it's an hourly or sub-hourly collection
            self._time_multiplier = 1 / data_coll.header.analysis_period.timestep
        self._calc_length = len(data_coll)

    @staticmethod
    def _check_number(value, value_name):
        """Check a given value for a dimension input."""
        try:
            value = float(value)
        except (ValueError, TypeError):
            raise TypeError('Expected number for Psychrometric Chart {}. '
                            'Got {}.'.format(value_name, type(value)))
        assert value > 0, 'Psychrometric Chart {} must be greater than 0. ' \
            'Got {}.'.format(value_name, value)
        return value

    def __len__(self):
        """Return length of values on the object."""
        return len(self._t_values)

    def __getitem__(self, key):
        """Return a tuple of temperature and humidity."""
        return self._t_values[key], self._rh_values[key]

    def __iter__(self):
        """Iterate through the values."""
        return zip(self._t_values, self._rh_values)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """Psychrometric Chart representation."""
        return 'Psychrometric Chart: {} values'.format(len(self._t_values))
