# coding=utf-8
"""Module for visualization of data collections in monthly intervals."""
from __future__ import division

from .datatype import UNITS, TYPESDICT
from .datatype.generic import GenericType
from .analysisperiod import AnalysisPeriod
from .datacollection import BaseCollection, HourlyDiscontinuousCollection, \
    DailyCollection, MonthlyCollection, MonthlyPerHourCollection
from .graphic import GraphicContainer

from ladybug_geometry.geometry2d.pointvector import Point2D, Vector2D
from ladybug_geometry.geometry2d.line import LineSegment2D
from ladybug_geometry.geometry2d.polygon import Polygon2D
from ladybug_geometry.geometry2d.polyline import Polyline2D
from ladybug_geometry.geometry2d.mesh import Mesh2D
from ladybug_geometry.geometry3d.pointvector import Point3D, Vector3D
from ladybug_geometry.geometry3d.plane import Plane


class MonthlyChart(object):
    """Object for visualization of data collections in monthly intervals.

    Args:
        data_collections: An array of data collections, which will be plotted
            on the monthly chart.
        legend_parameters: An optional LegendParameter object to change the display
            of the HourlyPlot (Default: None).
        base_point: An optional Point2D to be used as a starting point to generate
            the geometry of the plot (Default: (0, 0)).
        x_dim: An optional number to set the X dimension of each month of the
            chart. (Default: 10).
        y_dim: An optional number to set the Y dimension of the chart (Default: 40).
        stack: Boolean to note whether multiple connected data collections with
            the same cumulative data type should be stacked on top of each other.
            Otherwise, all bars for cumulative monthly/daily data will be placed
            next to each other and all meshes for cumulative hourly data will
            be overlapped on top of one another. Note that this input has no effect
            on data collections that do not have a cumulative data type or do
            not have a time aggregated data type that is cumulative. (Default: False).
        percentile: An optional number between 0 and 50 to be used for the percentile
            difference from the mean that hourly data meshes display at. For example,
            using 34 will generate hourly data meshes with a range of one standard
            deviation from the mean. Note that this input only has significance when
            the input data collections are hourly. (Default: 34)

    Properties:
        * data_collections
        * legend_parameters
        * base_point
        * x_dim
        * y_dim
        * stack
        * percentile
        * data_meshes
        * data_polylines
        * legend
        * chart_border
        * y_axis_lines
        * y_axis_label_points1
        * y_axis_label_points2
        * y_axis_labels1
        * y_axis_labels2
        * month_lines
        * month_label_points
        * month_labels
        * time_ticks
        * time_label_points
        * time_labels
        * y_axis_title_text1
        * y_axis_title_location1
        * y_axis_title_text2
        * y_axis_title_location2
        * title_text
        * lower_title_location
        * upper_title_location
        * time_interval
        * analysis_period
        * colors
        * data_types
    """
    __slots__ = ('_data_collections', '_base_point', '_x_dim', '_y_dim',
                 '_stack', '_percentile', '_time_interval', '_grouped_data',
                 '_units', '_data_types', '_color_map', '_minimums', '_maximums',
                 '_seg_count', '_container', '_analysis_period', '_months_int',
                 '_y_axis_points', '_month_points', '_month_label_points',
                 '_month_text', '_time_points')

    # editing HOUR_LABELS will change the labels produced for the entire chart
    HOUR_LABELS = (0, 6, 12, 18)

    def __init__(self, data_collections, legend_parameters=None, base_point=Point2D(),
                 x_dim=10, y_dim=40, stack=False, percentile=34):
        """Initialize monthly chart."""
        # check the input data collections
        if not isinstance(data_collections, list):
            try:
                data_collections = list(data_collections)
            except TypeError:
                raise TypeError('MonthlyChart data_collections must be an iterable. '
                                'Got {}.'.format(type(data_collections)))
        assert len(data_collections) >= 1, \
            'MonthlyChart must have at least one data collection.'
        for i, data in enumerate(data_collections):
            assert isinstance(data, BaseCollection), 'MonthlyChart data_collections' \
                ' must contain data collections. Got {}.'.format(type(data))
            if not data.validated_a_period:
                data = data.validate_analysis_period()
            data_collections[i] = data.to_immutable()
        self._time_interval = self._check_time_interval(data_collections)

        # check the input percentile and base point
        try:
            percentile = float(percentile)
        except (ValueError, TypeError):
            raise TypeError('Input percentile must be a number. Got {}: {}.'.format(
                type(percentile), percentile))
        assert 0 < percentile <= 50, 'Input percentile must be between 0 and 50. ' \
            'Got {}'.format(percentile)
        assert isinstance(base_point, Point2D), 'Expected Point2D for ' \
            'MonthlyChart base point. Got {}.'.format(type(base_point))

        # assign the inputs as properties of this data collection
        self._data_collections = data_collections
        self._base_point = base_point
        self._x_dim = self._check_dim(x_dim, 'x_dim')
        self._y_dim = self._check_dim(y_dim, 'y_dim')
        self._stack = bool(stack)
        self._percentile = percentile

        # set properties to None that will be computed later
        self._y_axis_points = None
        self._month_points = None
        self._month_label_points = None
        self._month_text = None
        self._time_points = None

        # group the input data by data type and figure out the max + min of the Y-axes
        self._grouped_data, self._data_types, self._units, self._color_map = \
            self._group_data_by_units()
        self._compute_maximums_minimums()
        self._seg_count = 11
        if legend_parameters is not None:
            legend_parameters = legend_parameters.duplicate()  # avoid editing original
            if legend_parameters.min is not None:
                self._minimums[0] = legend_parameters.min
                legend_parameters.min = None
            if legend_parameters.max is not None:
                self._maximums[0] = legend_parameters.max
                legend_parameters.max = None
            if not legend_parameters.is_segment_count_default:
                self._seg_count = legend_parameters.segment_count
                legend_parameters.segment_count = None

        # check the analysis periods of the data collections
        self._analysis_period = self._data_collections[0].header.analysis_period
        self._months_int = self._analysis_period.months_int
        # TODO: consider supporting different periods by analyzing their overlap
        apers = [data.header.analysis_period for data in self._data_collections[1:]]
        assert all([aper == self._analysis_period for aper in apers]), \
            'All MonthlyChart data collections must have the same analysis period.'

        # create the graphic container
        min_pt = Point3D(base_point.x, base_point.y)
        max_pt = Point3D(base_point.x + (x_dim * len(self._months_int)),
                         base_point.y + y_dim)
        mock_values = list(range(len(self._data_collections)))
        mock_descr = {}
        for i, data_c in enumerate(self._data_collections):
            data_t_str = data_c.header.metadata['type'] if 'type' in \
                data_c.header.metadata else str(data_c.header.data_type)
            mock_descr[i] = data_t_str
        mock_type = GenericType('Monthly Chart Data Streams', '', unit_descr=mock_descr)
        self._container = GraphicContainer(
            mock_values, min_pt, max_pt, legend_parameters, mock_type, '')

        # re-make the container if there is a second axis
        if len(self._data_types) > 1:  # there's a second axis; move max point
            offset = self.legend_parameters.text_height * \
                (len(self.y_axis_labels2[-1]) + 4)
            max_pt = Point3D(max_pt.x + offset, max_pt.y)
            self._container = GraphicContainer(
                mock_values, min_pt, max_pt, legend_parameters, mock_type, '')

    @property
    def data_collections(self):
        """Get the data collections assigned to this monthly chart."""
        return tuple(self._data_collections)

    @property
    def legend_parameters(self):
        """Get the legend parameters customizing this monthly chart."""
        return self._container.legend_parameters

    @property
    def base_point(self):
        """Get a Point2D for the base point of this monthly chart."""
        return self._base_point

    @property
    def x_dim(self):
        """Get a number for the X dimension of each month of the chart."""
        return self._x_dim

    @property
    def y_dim(self):
        """Get a number for the Y dimension of the chart."""
        return self._y_dim

    @property
    def stack(self):
        """Boolean for whether cumulative data should be stacked on top of each other."""
        return self._stack

    @property
    def percentile(self):
        """Get a number for the percentile difference from the mean for hourly data."""
        return self._percentile

    @property
    def data_meshes(self):
        """Get a list of colored Mesh2D for the data of this graphic.

        These meshes will resemble a bar chart in the case of monthly or daily data
        and will resemble a band between two ranges for hourly and sub-hourly data.
        """
        if self._time_interval == 'Monthly':
            return self._compute_monthly_bars()
        elif self._time_interval == 'Hourly':
            return self._compute_hourly_ranges()
        elif self._time_interval == 'Daily':
            return self._compute_daily_bars()

    @property
    def data_polylines(self):
        """Get a list of Polyline2D for the data of this graphic.

        These meshes will display the percentile borders of the data and the mean
        in the case of hourly data.  It will display a single line in the case of
        monthly-per-hour data.
        """
        if self._time_interval == 'Hourly':
            return self._compute_hourly_lines()
        elif self._time_interval == 'MonthlyPerHour':
            return self._compute_monthly_per_hour_lines()

    @property
    def legend(self):
        """The legend assigned to this graphic."""
        return self._container._legend

    @property
    def chart_border(self):
        """Get a Polyline2D for the border of the plot."""
        width = self._x_dim * len(self._months_int)
        height = self._y_dim
        pgon = Polygon2D.from_rectangle(self._base_point, Vector2D(0, 1), width, height)
        return Polyline2D.from_polygon(pgon)

    @property
    def y_axis_lines(self):
        """Get a list of LineSegment2D for the Y-axis values of the chart."""
        if not self._y_axis_points:
            self._compute_y_axis_points()
        vec = Vector2D(len(self._months_int) * self._x_dim)
        return [LineSegment2D(pt, vec) for pt in self._y_axis_points]

    @property
    def y_axis_label_points1(self):
        """Get a list of Point2Ds for the left-side labels of the Y-axis."""
        if not self._y_axis_points:
            self._compute_y_axis_points()
        txt_hght = self.legend_parameters.text_height
        return [Point2D(pt.x - txt_hght, pt.y) for pt in self._y_axis_points]

    @property
    def y_axis_label_points2(self):
        """Get a list of Point2Ds for the right-side labels of the Y-axis.

        This will be None if all of the input data collections are of the same
        data type.
        """
        if len(self._data_types) == 1:
            return None
        if not self._y_axis_points:
            self._compute_y_axis_points()
        txt_hght = self.legend_parameters.text_height
        x_dist = len(self._months_int) * self._x_dim + txt_hght
        return [Point2D(pt.x + x_dist, pt.y) for pt in self._y_axis_points]

    @property
    def y_axis_labels1(self):
        """Get a list of text strings for the left-side labels of the Y-axis."""
        return self._y_axis_label_text(0)

    @property
    def y_axis_labels2(self):
        """Get a list of text strings for the right-side labels of the Y-axis.

        This will be None if all of the input data collections are of the same
        data type.
        """
        if len(self._data_types) > 1:
            return self._y_axis_label_text(1)
        return None

    @property
    def month_lines(self):
        """Get a list of LineSegment2D for the month intervals of the chart."""
        if not self._month_points:
            self._compute_month_line_pts()
        vec = Vector2D(0, self._y_dim)
        return [LineSegment2D(pt, vec) for pt in self._month_points]

    @property
    def month_label_points(self):
        """Get a list of Point2Ds for the month text labels for the chart."""
        if not self._month_label_points:
            self._compute_month_line_pts()
        txt_hght = self.legend_parameters.text_height
        return [Point2D(pt.x, pt.y - txt_hght) for pt in self._month_label_points]

    @property
    def month_labels(self):
        """Get a list of text strings for the month labels for the chart."""
        if not self._month_text:
            self._compute_month_line_pts()
        return self._month_text

    @property
    def time_ticks(self):
        """Get a list of LineSegment2D for the time-of-day labels of the chart."""
        if not self._time_points:
            self._compute_time_pts()
        txt_hght = self.legend_parameters.text_height
        vec = Vector2D(0, -txt_hght / 2)
        return [LineSegment2D(pt, vec) for pt in self._time_points]

    @property
    def time_label_points(self):
        """Get a list of Point2Ds for the time-of-day text labels for the chart."""
        if not self._time_points:
            self._compute_time_pts()
        txt_hght = self.legend_parameters.text_height * 1.5
        return [Point2D(pt.x, pt.y - txt_hght) for pt in self._time_points]

    @property
    def time_labels(self):
        """Get a list of text strings for the time-of-day labels for the chart."""
        time_text = []
        for hr in self.HOUR_LABELS:
            hr_val = hr if hr <= 12 else hr - 12
            am_pm = 'PM' if 12 <= hr < 24 else 'AM'
            if hr_val == 0:
                hr_val = 12
            time_text.append('{} {}'.format(hr_val, am_pm))
        return time_text * len(self._months_int) + ['12 AM']

    @property
    def y_axis_title_text1(self):
        """Text string for the suggested title of the left-side Y-axis."""
        return '{} ({})'.format(self._data_types[0], self._units[0])

    @property
    def y_axis_title_location1(self):
        """A Plane for the location of left Y-axis title text."""
        pt = self._base_point
        txt_hght = self.legend_parameters.text_height
        txt_len = len(self.y_axis_labels1[-1])
        offset = txt_hght * (txt_len + 2)
        return Plane(Vector3D(0, 0, 1), Point3D(pt.x - offset, pt.y), Vector3D(0, 1))

    @property
    def y_axis_title_text2(self):
        """Text string for the suggested title of the right-side Y-axis.

        This will be None if all of the input data collections are of the same
        data type.
        """
        if len(self._data_types) > 1:
            return '{} ({})'.format(self._data_types[1], self._units[1])
        return None

    @property
    def y_axis_title_location2(self):
        """A Plane for the location of right Y-axis title text.

        This will be None if all of the input data collections are of the same
        data type.
        """
        if len(self._data_types) > 1:
            pt = self._base_point
            txt_hght = self.legend_parameters.text_height
            txt_len = len(self.y_axis_labels2[-1])
            offset = len(self._months_int) * self._x_dim + txt_hght * (txt_len + 2)
            return Plane(Vector3D(0, 0, 1), Point3D(pt.x + offset, pt.y), Vector3D(0, 1))
        return None

    @property
    def title_text(self):
        """Text string for the suggested title of the monthly chart."""
        excluded_keys = ('type', 'System', 'Zone', 'Surface')
        title_array = []
        for key, val in self._data_collections[0].header.metadata.items():
            if key not in excluded_keys:
                title_array.append('{}: {}'.format(key, val))
        return '\n'.join(title_array)

    @property
    def lower_title_location(self):
        """A Plane for the lower location of title text."""
        pln = self._container.lower_title_location
        txt_hght = self.legend_parameters.text_height
        return Plane(pln.n, Point3D(pln.o.x, pln.o.y - txt_hght * 2))

    @property
    def upper_title_location(self):
        """A Plane for the upper location of title text."""
        num_lines = self.title_text.count('\n') + 4
        pln = self._container.upper_title_location
        txt_hght = self.legend_parameters.text_height
        return Plane(pln.n, Point3D(pln.o.x, pln.o.y + txt_hght * num_lines))

    @property
    def time_interval(self):
        """Text for the time interval of the input data collections.

        This determines how the data displays on the chart.
        """
        return self._time_interval

    @property
    def analysis_period(self):
        """The AnalysisPeriod assigned to the hourly plot's data collection."""
        return self._analysis_period

    @property
    def colors(self):
        """An array of colors in the legend with one color per input data collection."""
        return self._container.value_colors

    @property
    def data_types(self):
        """A array of all the unique data types among the input collections."""
        return self._data_types

    def set_minimum_by_index(self, minimum_value, data_type_index=0):
        """Set the minimum value of the Y-axis given the index of a data_type.

        Args:
            minimum_value: The value to be set as the minimum of the Y-axis.
            data_type_index: An integer for the index of the data type to set
                the minimum_value for. This corresponds to one of the data types
                in the data_types property of this class. Using 0 indicates the
                left-side axis minimum and using 1 indicated the right-side
                axis minimum. (Default: 0).
        """
        try:
            self._minimums[data_type_index] = minimum_value
        except IndexError:
            pass  # does not refer to an index for the current data types

    def set_maximum_by_index(self, maximum_value, data_type_index=0):
        """Set the maximum value of the Y-axis given the index of a data_type.

        Args:
            maximum_value: The value to be set as the maximum of the Y-axis.
            data_type_index: An integer for the index of the data type to set
                the maximum_value for. This corresponds to one of the data types
                in the data_types property of this class. Using 0 indicates the
                left-side axis maximum and using 1 indicated the right-side
                axis maximum. (Default: 0).
        """
        try:
            self._maximums[data_type_index] = maximum_value
        except IndexError:
            pass  # does not refer to an index for the current data types

    def _compute_hourly_lines(self):
        """Compute a list of lines from this object's input data."""
        # get values used by all polylines
        lines = []
        step = self._grouped_data[0][0][0].header.analysis_period.timestep * 24
        x_dist = self._x_dim / step

        for j, (t, data_arr) in enumerate(zip(self._data_types, self._grouped_data)):
            d_range = self._maximums[j] - self._minimums[j]
            d_range = 1 if d_range == 0 else d_range  # catch case of all same values
            min_val = self._minimums[j]
            if self._stack:
                data_sign = self._compute_data_sign(data_arr)
                prev_y_low = self._hour_y_values_base(
                    data_arr[0][0], d_range, min_val, step)
                prev_y_up = self._hour_y_values_base(
                    data_arr[0][0], d_range, min_val, step)
                for i, (data, sign) in enumerate(zip(data_arr, data_sign)):
                    if sign in ('+/-', '-/+') and self._is_cumulative(t):
                        d_i = -1 if sign == '+/-' else 0
                        up_vals, low_vals = self._hour_y_values_stack_split(
                            data, d_range, min_val, step, prev_y_up, prev_y_low, d_i)
                        lines.extend(self._hour_polylines(low_vals, x_dist))
                        lines.extend(self._hour_polylines(up_vals, x_dist))
                        prev_y_up = up_vals
                        prev_y_low = low_vals
                    else:
                        prev_y = prev_y_up if sign == '+' else prev_y_low
                        low_vals = self._hour_y_values_stack(
                            data[0], d_range, min_val, step, prev_y)
                        up_vals = self._hour_y_values_stack(
                            data[-1], d_range, min_val, step, prev_y)
                        if self._is_cumulative(t):  # set start y so the next data stacks
                            if sign == '+':
                                prev_y_up = up_vals
                            else:
                                prev_y_low = low_vals
                        lines.extend(self._hour_polylines(low_vals, x_dist))
                        lines.extend(self._hour_polylines(up_vals, x_dist))
                        if len(data) == 3:  # get the middle value if it exists
                            mid_vals = self._hour_y_values(
                                data[1], d_range, min_val, step)
                            lines.extend(self._hour_polylines(mid_vals, x_dist))
            else:
                for data in data_arr:
                    low_vals = self._hour_y_values(data[0], d_range, min_val, step)
                    up_vals = self._hour_y_values(data[-1], d_range, min_val, step)
                    lines.extend(self._hour_polylines(low_vals, x_dist))
                    lines.extend(self._hour_polylines(up_vals, x_dist))
                    if len(data) == 3:  # get the middle value if it exists
                        mid_vals = self._hour_y_values(data[1], d_range, min_val, step)
                        lines.extend(self._hour_polylines(mid_vals, x_dist))
        return lines

    def _compute_monthly_per_hour_lines(self):
        """Compute a list of lines from this object's input data."""
        # get values used by all polylines
        lines = []
        step = self._grouped_data[0][0].header.analysis_period.timestep * 24
        x_dist = self._x_dim / step

        for j, (t, data_arr) in enumerate(zip(self._data_types, self._grouped_data)):
            d_range = self._maximums[j] - self._minimums[j]
            d_range = 1 if d_range == 0 else d_range  # catch case of all same values
            min_val = self._minimums[j]
            prev_y_low = self._hour_y_values_base(data_arr[0], d_range, min_val, step)
            prev_y_up = self._hour_y_values_base(data_arr[0], d_range, min_val, step)
            for i, data in enumerate(data_arr):
                if self._stack:
                    dat_total = sum(data.values)
                    prev_y = prev_y_up if dat_total > 0 else prev_y_low
                    vals = self._hour_y_values_stack(
                        data, d_range, min_val, step, prev_y)
                    if self._is_cumulative(t):  # set the start y so the next data stacks
                        if dat_total > 0:
                            prev_y_up = vals
                        else:
                            prev_y_low = vals
                else:
                    vals = self._hour_y_values(data, d_range, min_val, step)
                lines.extend(self._hour_polylines(vals, x_dist))
        return lines

    def _compute_monthly_bars(self):
        """Compute a list of bar colored meshes from this object's input data."""
        # get values used across all bars
        meshes = []
        colors = self.colors
        bar_count = 0
        bar_width = self._x_dim / (self._horizontal_bar_count() + 1)
        spacer_width = bar_width / 2

        # loop through each data set and build the bar meshes
        for j, (t, data_arr) in enumerate(zip(self._data_types, self._grouped_data)):
            d_range = self._maximums[j] - self._minimums[j]
            d_range = 1 if d_range == 0 else d_range  # catch case of all same values
            min_val = self._minimums[j]
            zero_val = self._y_dim * (min_val / d_range)
            base_y = self._base_point.y - zero_val if self._is_cumulative(t) \
                else self._base_point.y
            bar_y_low = [base_y] * len(data_arr[0])  # track the bar cumulative heights
            bar_y_up = [base_y] * len(data_arr[0])  # track the bar cumulative heights
            for i, data in enumerate(data_arr):
                verts = []
                faces = []
                vert_count = 0
                for m_i, val in enumerate(data):  # iterate through values
                    # compute critical dimensions of each bar
                    start_x = self._base_point.x + m_i * self._x_dim + \
                        spacer_width + bar_count * bar_width
                    if self._is_cumulative(t):
                        bar_hgt = (self._y_dim * ((val - min_val) / d_range)) + zero_val
                        if bar_hgt >= 0:
                            start_y = bar_y_up[m_i]
                            if self._stack:  # shift the baseline up for next bar
                                bar_y_up[m_i] += bar_hgt
                        else:
                            start_y = bar_y_low[m_i]
                            if self._stack:  # shift the baseline down for next bar
                                bar_y_low[m_i] += bar_hgt
                    else:  # always plot the value from the bottom
                        bar_hgt = self._y_dim * ((val - min_val) / d_range)
                        start_y = base_y
                    end_y = start_y + bar_hgt
                    # create the bar mesh face
                    verts.extend(self._bar_pts(start_x, start_y, bar_width, end_y))
                    faces.append(tuple(x + vert_count for x in (0, 1, 2, 3)))
                    vert_count += 4
                # create the final colored mesh
                mesh_col = [colors[self._color_map[j][i]]] * len(faces)
                meshes.append(Mesh2D(verts, faces, mesh_col))
                if not self._stack or not self._is_cumulative(t):  # shift bar in x dir
                    bar_count += 1
            if self._stack and self._is_cumulative(t):
                bar_count += 1
        return meshes

    def _compute_daily_bars(self):
        """Compute a list of bar colored meshes from this object's input data."""
        # get values used across all bars
        meshes = []
        colors = self.colors
        bar_count = 0
        n_big_bars = self._horizontal_bar_count()
        big_bar_width = self._x_dim / n_big_bars
        aper = self.analysis_period
        per_mon = aper.NUMOFDAYSEACHMONTH if not aper.is_leap_year \
            else aper.NUMOFDAYSEACHMONTHLEAP
        day_per_mon = [per_mon[i - 1] for i in self._months_int]

        # loop through each data set and build the bar meshes
        for j, (t, data_arr) in enumerate(zip(self._data_types, self._grouped_data)):
            d_range = self._maximums[j] - self._minimums[j]
            d_range = 1 if d_range == 0 else d_range  # catch case of all same values
            min_val = self._minimums[j]
            zero_val = self._y_dim * (min_val / d_range)
            base_y = self._base_point.y - zero_val if self._is_cumulative(t) \
                else self._base_point.y
            bar_y_low = [base_y] * len(data_arr[0])  # track the bar cumulative heights
            bar_y_up = [base_y] * len(data_arr[0])  # track the bar cumulative heights
            for i, data in enumerate(data_arr):
                verts = []
                faces = []
                vert_count = 0
                day_count = 0
                month_count = 0
                x_dist = 0
                bar_width = big_bar_width / day_per_mon[0]
                for m_i, val in enumerate(data):  # iterate through values
                    # compute critical dimensions of each bar
                    start_x = self._base_point.x + x_dist + \
                        month_count * self._x_dim + bar_count * big_bar_width
                    if self._is_cumulative(t):
                        bar_hgt = (self._y_dim * ((val - min_val) / d_range)) + zero_val
                        if bar_hgt >= 0:
                            start_y = bar_y_up[m_i]
                            if self._stack:  # shift the baseline up for next bar
                                bar_y_up[m_i] += bar_hgt
                        else:
                            start_y = bar_y_low[m_i]
                            if self._stack:  # shift the baseline down for next bar
                                bar_y_low[m_i] += bar_hgt
                    else:  # always plot the value from the bottom
                        bar_hgt = self._y_dim * ((val - min_val) / d_range)
                        start_y = base_y
                    end_y = start_y + bar_hgt
                    # create the bar mesh face
                    verts.extend(self._bar_pts(start_x, start_y, bar_width, end_y))
                    faces.append(tuple(x + vert_count for x in (0, 1, 2, 3)))
                    vert_count += 4
                    x_dist += bar_width
                    day_count += 1
                    if day_count == day_per_mon[month_count]:
                        day_count = 0
                        if month_count != len(day_per_mon) - 1:
                            month_count += 1
                            bar_width = big_bar_width / day_per_mon[month_count]
                            x_dist = 0
                # create the final colored mesh
                mesh_col = [colors[self._color_map[j][i]]] * len(faces)
                meshes.append(Mesh2D(verts, faces, mesh_col))
                if not self._stack or not self._is_cumulative(t):  # shift bar in x dir
                    bar_count += 1
            if self._stack and self._is_cumulative(t):
                bar_count += 1
        return meshes

    def _compute_hourly_ranges(self):
        """Compute a list of hour range colored meshes from this object's input data."""
        # get values used in all meshes
        meshes = []
        step = self._grouped_data[0][0][0].header.analysis_period.timestep * 24
        x_dist = self._x_dim / step
        colors = self.colors

        for j, (t, data_arr) in enumerate(zip(self._data_types, self._grouped_data)):
            d_range = self._maximums[j] - self._minimums[j]
            d_range = 1 if d_range == 0 else d_range  # catch case of all same values
            min_val = self._minimums[j]
            mesh_cols = [colors[self._color_map[j][i]] for i in range(len(data_arr))]
            if self._stack:
                data_sign = self._compute_data_sign(data_arr)
                prev_y_low = \
                    self._hour_y_values_base(data_arr[0][0], d_range, min_val, step)
                prev_y_up = \
                    self._hour_y_values_base(data_arr[0][0], d_range, min_val, step)
                for i, (data, sign) in enumerate(zip(data_arr, data_sign)):
                    if sign in ('+/-', '-/+') and self._is_cumulative(t):
                        d_i = -1 if sign == '+/-' else 0
                        up_vals, low_vals = self._hour_y_values_stack_split(
                            data, d_range, min_val, step, prev_y_up, prev_y_low, d_i)
                        verts1, faces1 = self._hour_mesh_components(
                            prev_y_up, up_vals, x_dist)
                        verts2, faces2 = self._hour_mesh_components(
                            prev_y_low, low_vals, x_dist)
                        prev_y_up = up_vals
                        prev_y_low = low_vals
                        verts = verts1 + verts2
                        st_i = len(verts1)
                        faces = faces1 + [tuple(v + st_i for v in f) for f in faces2]
                    else:
                        prev_y = prev_y_up if sign == '+' else prev_y_low
                        low_vals = self._hour_y_values_stack(
                            data[0], d_range, min_val, step, prev_y)
                        up_vals = self._hour_y_values_stack(
                            data[-1], d_range, min_val, step, prev_y)
                        if self._is_cumulative(t):  # set start y so the next data stacks
                            if sign == '+':
                                prev_y_up = up_vals
                            else:
                                prev_y_low = low_vals
                        verts, faces = self._hour_mesh_components(
                            low_vals, up_vals, x_dist)
                    # create the final colored mesh
                    mesh_col = [mesh_cols[i]] * len(faces)
                    meshes.append(Mesh2D(verts, faces, mesh_col))
            else:
                for i, data in enumerate(data_arr):
                    # get all of the upper and lower y-values of the data
                    low_vals = self._hour_y_values(data[0], d_range, min_val, step)
                    up_vals = self._hour_y_values(data[-1], d_range, min_val, step)
                    verts, faces = self._hour_mesh_components(low_vals, up_vals, x_dist)
                    # create the final colored mesh
                    mesh_col = [mesh_cols[i]] * len(faces)
                    meshes.append(Mesh2D(verts, faces, mesh_col))
        return meshes

    @staticmethod
    def _compute_data_sign(data_array):
        """Get the sign of data collections (+, -, +/-, -/+)."""
        data_sign = []
        for data in data_array:
            pos = all(v >= 0 for v in data[-1]._values)
            neutral = all(v == 0 for v in data[0]._values)
            if pos and neutral:
                data_sign.append('+')
            else:
                neg = all(v <= 0 for v in data[0]._values)
                if neg and not neutral:
                    data_sign.append('-')
                else:
                    neutral2 = all(v == 0 for v in data[-1]._values)
                    if neutral2:
                        data_sign.append('-/+')
                    else:
                        data_sign.append('+/-')
        return data_sign

    def _hour_mesh_components(self, low_vals, up_vals, x_hr_dist):
        """Get the vertices and faces of a mesh from upper/lower lists of values.

        Args:
            low_vals: A list of lists with each sublist having lower y values.
            up_vals: A list of lists with each sublist having upper y values.
            x_hr_dist: The x distance moved by each cell of the mesh.

        Returns:
            verts: A list of vertices for the mesh.
            faces: A list of faces for the mesh.
        """
        verts = []
        faces = []
        vert_count = 0
        for month in range(len(low_vals)):
            # create the two starting vertices for the month
            start_x = self._base_point.x + month * self._x_dim
            v1 = Point2D(start_x, low_vals[month][0])
            v2 = Point2D(start_x, up_vals[month][0])
            verts.extend((v1, v2))
            # loop through the hourly data and add vertices
            for hour in range(1, len(low_vals[0])):
                x_val = start_x + x_hr_dist * hour
                v3 = Point2D(x_val, low_vals[month][hour])
                v4 = Point2D(x_val, up_vals[month][hour])
                verts.extend((v3, v4))
                faces.append(tuple(x + vert_count for x in (0, 2, 3, 1)))
                vert_count += 2
            vert_count += 2
        return verts, faces

    def _hour_polylines(self, y_vals, x_hr_dist):
        """Get a polyline from a lists of Y-coordinate values.

        Args:
            y_vals: A list of lists with each sublist having y values.
            x_hr_dist: The x distance moved by each cell of the mesh.

        Returns:
            polylines: A list of Polyline2D.
        """
        plines = []
        for month in range(len(y_vals)):
            verts = []
            start_x = self._base_point.x + month * self._x_dim
            for hour in range(len(y_vals[0])):
                x_val = start_x + x_hr_dist * hour
                y_val = y_vals[month][hour]
                verts.append(Point2D(x_val, y_val))
            plines.append(Polyline2D(verts))
        return plines

    def _hour_y_values(self, data, d_range, minimum, step):
        """Get a list of y-coordinates from a monthly-per-hour data collection."""
        data_values = data.values
        y_values = []
        for i in range(0, len(data_values), step):
            month_val = []
            for val in data_values[i:i + step]:
                rel_y = ((val - minimum) / d_range)
                month_val.append(self._base_point.y + self._y_dim * rel_y)
            month_val.append(month_val[0])  # loop data in each month
            y_values.append(month_val)
        return y_values

    def _hour_y_values_stack(self, data, d_range, minimum, step, start_y):
        """Get a list of y-coordinates from a monthly-per-hour data collection."""
        data_values = data.values
        zero_val = self._y_dim * (minimum / d_range) if \
            self._is_cumulative(data.header.data_type) else 0
        y_values = []
        for count, i in enumerate(range(0, len(data_values), step)):
            month_val = []
            for j, val in enumerate(data_values[i:i + step]):
                rel_y = self._y_dim * ((val - minimum) / d_range)
                month_val.append(start_y[count][j] + rel_y + zero_val)
            month_val.append(month_val[0])  # loop start/end for each month
            y_values.append(month_val)
        return y_values

    def _hour_y_values_stack_split(
            self, data, d_range, minimum, step, st_y_up, st_y_low, d_index):
        """Get lists of y-coordinates from a monthly-per-hour data collection."""
        data_values = data[d_index].values
        zero_val = self._y_dim * (minimum / d_range)
        y_values_up, y_values_low = [], []
        for count, i in enumerate(range(0, len(data_values), step)):
            month_val_up, month_val_low = [], []
            for j, val in enumerate(data_values[i:i + step]):
                rel_y = self._y_dim * ((val - minimum) / d_range)
                if val >= 0:
                    month_val_up.append(st_y_up[count][j] + rel_y + zero_val)
                    month_val_low.append(st_y_low[count][j])
                else:
                    month_val_up.append(st_y_up[count][j])
                    month_val_low.append(st_y_low[count][j] + rel_y + zero_val)
            month_val_up.append(month_val_up[0])  # loop start/end for each month
            month_val_low.append(month_val_low[0])  # loop start/end for each month
            y_values_up.append(month_val_up)
            y_values_low.append(month_val_low)
        return y_values_up, y_values_low

    def _hour_y_values_base(self, data, d_range, minimum, step):
        """Get a list of base y-coordinates from a monthly-per-hour data collection."""
        y_values = []
        zero_val = self._y_dim * (-minimum / d_range) if \
            self._is_cumulative(data.header.data_type) else 0
        for i in range(0, len(data), step):
            y_values.append([self._base_point.y + zero_val] * (step + 1))
        return y_values

    def _horizontal_bar_count(self):
        """Get the number of bars in the horizontal direction."""
        if not self._stack:
            return len(self._data_collections)
        else:
            n_bars = 0
            for d_type, data_list in zip(self._data_types, self._grouped_data):
                if self._is_cumulative(d_type):
                    n_bars += 1
                else:
                    n_bars += len(data_list)
            return n_bars

    def _compute_y_axis_points(self):
        """Compute the points for the Y-axis lines and labels."""
        self._y_axis_points = []
        y_interval = self._y_dim / (self._seg_count - 1)
        base_y = self._base_point.y
        for i in range(self._seg_count):
            line_pt = Point2D(self._base_point.x, base_y + (i * y_interval))
            self._y_axis_points.append(line_pt)

    def _y_axis_label_text(self, index):
        """Get a list of Y-axis labels using the index of the data in _data_types."""
        format_str = '%.{}f'.format(self.legend_parameters.decimal_count)
        y_axis_text = []
        interval = (self._maximums[index] - self._minimums[index]) / \
            (self._seg_count - 1)
        base_val = self._minimums[index]
        for i in range(self._seg_count):
            val = base_val + (i * interval)
            y_axis_text.append(format_str % val)
        return y_axis_text

    def _compute_month_line_pts(self):
        """Compute the points for the month lines and labels."""
        self._month_text = [AnalysisPeriod.MONTHNAMES[mon] for mon in self._months_int]
        self._month_points = []
        for i in range(1, len(self._months_int)):
            pt = Point2D(self._base_point.x + (i * self._x_dim), self._base_point.y)
            self._month_points.append(pt)
        self._month_label_points = []
        start_x = self._base_point.x + (self._x_dim / 2)
        for i in range(len(self._months_int)):
            pt = Point2D(start_x + (i * self._x_dim), self._base_point.y)
            self._month_label_points.append(pt)

    def _compute_time_pts(self):
        """Compute the points for the time lines and labels."""
        self._time_points = []
        for i in range(len(self._months_int)):
            for t in self.HOUR_LABELS:
                x_val = self._base_point.x + (i * self._x_dim) + (t * self._x_dim / 24)
                pt = Point2D(x_val, self._base_point.y)
                self._time_points.append(pt)
        self._time_points.append(
            Point2D(self._base_point.x + (len(self._months_int) * self._x_dim),
                    self._base_point.y)
        )

    def _compute_maximums_minimums(self):
        """Set the maximum and minimum values of the chart using self._grouped_data."""
        self._minimums = []
        self._maximums = []
        for data_type, data_list in zip(self._data_types, self._grouped_data):
            # get the minimum values of all the data collections
            if self._time_interval == 'Hourly':
                min_vals = [data[0].min for data in data_list]
                max_vals = [data[-1].max for data in data_list]
            else:
                min_vals = [data.min for data in data_list]
                max_vals = [data.max for data in data_list]

            # determine the maximum and minium values depending on the stack input
            if not self._is_cumulative(data_type) or not self._stack:
                min_val = min(min_vals)
                max_val = max(max_vals)
            else:  # stacked data; sum up the values to get the total of the stack
                min_val = sum(min_vals)
                max_val = sum(max_vals)

            # plot everything from 0 if the data is cumulative
            if self._is_cumulative(data_type):
                if min_val > 0 and max_val > 0:
                    min_val = 0
                elif max_val < 0 and min_val < 0:
                    max_val = 0
                elif min_val < -1e-9 and max_val > 1e-9:
                    # probably an energy balance; center the chart on 0 by default
                    extreme = abs(min_val) if abs(min_val) > max_val else max_val
                    max_val = extreme
                    min_val = -extreme

            self._minimums.append(min_val)
            self._maximums.append(max_val)

    def _group_data_by_units(self):
        """Group an the data collections of this MonthlyChart by their units.

        This will also convert hourly data collections to lists of percentile
        collections if they are hourly.
        """
        # group the data collections by their units
        grouped_data = []
        units, other_types = [], []
        color_map = []
        for i, data in enumerate(self._data_collections):
            if data.header.unit in units:
                ind = units.index(data.header.unit)
                grouped_data[ind].append(data)
                color_map[ind].append(i)
            else:
                units.append(data.header.unit)
                other_types.append(data.header.data_type)
                grouped_data.append([data])
                color_map.append([i])

        # get the base type from the units
        data_types = []
        for i, unit in enumerate(units):
            for key in UNITS:
                if unit in UNITS[key]:
                    data_types.append(TYPESDICT[key]())
                    break
            else:
                data_types.append(other_types[i])

        # convert hourly data collections into monthly-per-hour collections
        if self._time_interval == 'Hourly':
            lower, upper = 50 - self._percentile, 50 + self._percentile
            new_data = [[] for data_list in grouped_data]
            for i, data_list in enumerate(grouped_data):
                cumul = self._is_cumulative(data_types[i])
                for data in data_list:
                    new_d = self._hourly_to_monthly_per_hour(data, lower, upper, cumul)
                    new_data[i].append(new_d)
            grouped_data = new_data
        return grouped_data, data_types, units, color_map

    def _is_cumulative(self, data_type):
        """Determine if a data type is cumulative and should be stack-able."""
        return data_type.cumulative or \
            (self._stack and data_type.time_aggregated_type is not None)

    @staticmethod
    def _bar_pts(start_x, base_y, bar_width, end_y):
        """Get a list of bar vertices from input bar properties."""
        # create each of the 4 vertices
        v1 = Point2D(start_x, base_y)
        v2 = Point2D(start_x + bar_width, base_y)
        v3 = Point2D(start_x + bar_width, end_y)
        v4 = Point2D(start_x, end_y)
        return (v1, v2, v3, v4)

    @staticmethod
    def _hourly_to_monthly_per_hour(hourly_collection, lower, upper, cumulative):
        """Convert hourly data into lists of 2-3 monthly-per-hour data.

        Args:
            hourly_collection: An hourly data collection to be analyzed.
            lower: The lower percentile for the first monthly-per-hour collection.
            upper: The upper percentile for the last monthly-per-hour collection.
            cumulative: Boolean to note if data is cumulative, in which case just
                a total collection and a zero collection will be output.
        """
        if not cumulative:
            low = hourly_collection.percentile_monthly_per_hour(lower)
            mid = hourly_collection.average_monthly_per_hour()
            up = hourly_collection.percentile_monthly_per_hour(upper)
            return [low, mid, up]
        else:
            total = hourly_collection.total_monthly_per_hour()
            zero = total.duplicate()
            zero.values = [0 for val in range(len(total))]
            if total.total > 0:
                return [zero, total]
            else:
                return [total, zero]

    @staticmethod
    def _check_dim(dim_value, dim_name):
        """Check a given value for a dimension input."""
        assert isinstance(dim_value, (float, int)), 'Expected number for ' \
            'MonthlyChart {}. Got {}.'.format(dim_name, type(dim_value))
        assert dim_value > 0, 'MonthlyChart {} must be greater than 0. ' \
            'Got {}.'.format(dim_name, dim_value)
        return dim_value

    @staticmethod
    def _check_time_interval(data_collections):
        """Check that input data collections all have the same time interval.

        For example: Hourly, Daily, Monthly, MonthlyPerHour.
        """
        # get the base class and the time interval from the first data collection
        base_collection = data_collections[0]
        if isinstance(base_collection, HourlyDiscontinuousCollection):
            base_class = HourlyDiscontinuousCollection
            time_interval = 'Hourly'
        elif isinstance(base_collection, DailyCollection):
            base_class = DailyCollection
            time_interval = 'Daily'
        elif isinstance(base_collection, MonthlyCollection):
            base_class = MonthlyCollection
            time_interval = 'Monthly'
        else:
            base_class = MonthlyPerHourCollection
            time_interval = 'MonthlyPerHour'

        # check that all of the data collections have the same time interval
        assert all(isinstance(data, base_class) for data in data_collections), \
            'MonthlyChart data collections must all be for the same time interval.\n' \
            'Either Hourly, Daily, Monthly, or MonthlyPerHour.'

        # check that all of the data collections are continuous
        assert all(data.is_continuous for data in data_collections), \
            'MonthlyChart data collections must all be continuous.'
        return time_interval

    def __repr__(self):
        """Monthly Chart representation."""
        return 'Monthly Chart:\n{} data collections'.format(len(self.data_collections))
