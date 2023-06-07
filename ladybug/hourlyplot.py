# coding=utf-8
"""Module for visualization of hourly data collections."""
from __future__ import division

from .analysisperiod import AnalysisPeriod
from .datacollection import HourlyContinuousCollection, HourlyDiscontinuousCollection
from .graphic import GraphicContainer

from ladybug_geometry.geometry2d.pointvector import Point2D, Vector2D
from ladybug_geometry.geometry2d.line import LineSegment2D
from ladybug_geometry.geometry2d.polygon import Polygon2D
from ladybug_geometry.geometry2d.polyline import Polyline2D
from ladybug_geometry.geometry2d.mesh import Mesh2D
from ladybug_geometry.geometry3d.pointvector import Point3D, Vector3D
from ladybug_geometry.geometry3d.line import LineSegment3D
from ladybug_geometry.geometry3d.plane import Plane
from ladybug_geometry.geometry3d.polyline import Polyline3D
from ladybug_geometry.geometry3d.mesh import Mesh3D


class HourlyPlot(object):
    """Object for visualization of hourly data collections.

    Args:
        data_collection: A HourlyContinuousCollection or HourlyDiscontinuousCollection
            which will be used to generate the hourly plot.
        legend_parameters: An optional LegendParameter object to change the display
            of the HourlyPlot (Default: None).
        base_point: An optional Point3D to be used as a starting point to generate
            the geometry of the plot (Default: (0, 0, 0)).
        x_dim: An optional number to set the X dimension of the mesh cells (Default: 1).
        y_dim: An optional number to set the Y dimension of the mesh cells (Default: 4).
        z_dim: An optional number to set the Z dimension of the entire chart. This
            will be used to make the colored_mesh3d of the chart vary in the Z
            dimension according to the data. The value input here should usually be
            several times larger than the x_dim or y_dim in order to be noticeable
            (e.g. 100). If 0, the colored_mesh3d will simply be flat. (Default: 0).
        reverse_y: Boolean to note whether the Y-axis of the chart is reversed
            such that time flows from the top of the chart to the bottom instead of
            the bottom to the top. (Default: False).

    Properties:
        * data_collection
        * legend_parameters
        * base_point
        * x_dim
        * y_dim
        * z_dim
        * reverse_y
        * colored_mesh2d
        * colored_mesh3d
        * legend
        * chart_border2d
        * chart_border3d
        * hour_lines2d
        * hour_lines3d
        * hour_label_points2d
        * hour_label_points3d
        * hour_labels
        * month_lines2d
        * month_lines3d
        * month_label_points2d
        * month_label_points3d
        * month_labels
        * title_text
        * lower_title_location
        * upper_title_location
        * analysis_period
        * values
        * colors
    """
    __slots__ = (
        '_data_collection', '_base_point', '_x_dim', '_y_dim', '_z_dim',
        '_num_y', '_num_x', '_container', '_hour_points', '_hour_text', '_hour_text_24',
        '_month_points', '_month_label_points', '_month_text', '_reverse_y')

    # editing HOUR_LABELS will change the labels produced for the entire chart
    HOUR_LABELS = (0, 6, 12, 18, 24)

    def __init__(self, data_collection, legend_parameters=None, base_point=Point3D(),
                 x_dim=1, y_dim=4, z_dim=0, reverse_y=False):
        """Initialize hourly plot."""
        # check the input objects
        acceptable_colls = (HourlyContinuousCollection, HourlyDiscontinuousCollection)
        assert isinstance(data_collection, acceptable_colls), 'HourlyPlot ' \
            'data_collection must be a HourlyContinuousCollection or ' \
            'HourlyDiscontinuousCollection. Got {}.'.format(type(data_collection))
        assert isinstance(base_point, Point3D), 'Expected Point3D for ' \
            'HourlyPlot base point. Got {}.'.format(type(base_point))

        # ensure the analysis period of the data collection has been validated
        if not data_collection.validated_a_period:
            data_collection = data_collection.validate_analysis_period()

        # assign the inputs as properties of this data collection
        self._data_collection = data_collection.to_immutable()
        self._base_point = base_point
        self._x_dim = self._check_dim(x_dim, 'x_dim')
        self._y_dim = self._check_dim(y_dim, 'y_dim')
        self._z_dim = 0
        if z_dim != 0:
            self._z_dim = self._check_dim(z_dim, 'z_dim')
        self._reverse_y = bool(reverse_y)

        # set properties to None that will be computed later
        self._hour_points = None
        self._hour_text = None
        self._month_points = None
        self._month_label_points = None
        self._month_text = None

        # create the graphic container from the inputs
        a_per = self.analysis_period
        if not a_per.is_reversed:
            self._num_x = a_per.end_time.doy - a_per.st_time.doy + 1
        else:
            num_doys = 365 if not a_per.is_leap_year else 366
            self._num_x = num_doys - a_per.st_time.doy + a_per.end_time.doy + 1
        if a_per.end_hour == 23:  # the last datetime is not included
            self._num_y = ((a_per.end_hour - a_per.st_hour + 1) * a_per.timestep)
        else:  # the last datetime is included
            if a_per.st_hour <= a_per.end_hour:
                self._num_y = ((a_per.end_hour - a_per.st_hour) * a_per.timestep) + 1
            else:
                self._num_y = 24 * a_per.timestep
        x_dist = x_dim * self._num_x
        y_dist = y_dim * self._num_y
        max_pt = Point3D(base_point.x + x_dist, base_point.y + y_dist, base_point.z)
        self._container = GraphicContainer(
            data_collection.values, base_point, max_pt, legend_parameters,
            data_collection.header.data_type, data_collection.header.unit)

    @classmethod
    def from_z_dim_per_unit(cls, data_collection, legend_parameters=None,
                            base_point=Point3D(), x_dim=1, y_dim=4, z_dim_per_unit=0):
        """Create HourlyPlot with an option to set the Z dimension on a per-unit basis.

        This is useful in cases of wanting to compare the Z dimensions of two plots
        to each other.

        Args:
            data_collection: A Hourly Collection, which will be used to generate
                the hourly plot.
            legend_parameters: An optional LegendParameter object to change the display
                of the HourlyPlot (Default: None).
            base_point: An optional Point3D to be used as a starting point to generate
                the geometry of the plot (Default: (0, 0, 0)).
            x_dim: Optional number to set the X dimension of the mesh cells (Default: 1).
            y_dim: Optional number to set the Y dimension of the mesh cells (Default: 4).
            z_dim: Optional number to set the Z dimension per unit of value in the input
                data_collection. If 0, the colored_mesh3d will be flat. (Default: 0).
        """
        z_dim = (data_collection.max - data_collection.min) * z_dim_per_unit
        return cls(data_collection, legend_parameters, base_point, x_dim, y_dim, z_dim)

    @property
    def data_collection(self):
        """The data collection assigned to this hourly plot."""
        return self._data_collection

    @property
    def legend_parameters(self):
        """The legend parameters customizing this hourly plot."""
        return self._container.legend_parameters

    @property
    def base_point(self):
        """Point3D for the base point of this hourly plot."""
        return self._base_point

    @property
    def x_dim(self):
        """A number for the X dimension of each cell of the hourly plot."""
        return self._x_dim

    @property
    def y_dim(self):
        """A number for the Y dimension of each cell of the hourly plot."""
        return self._y_dim

    @property
    def z_dim(self):
        """A number for the Z dimension of the entire hourly plot."""
        return self._z_dim

    @property
    def reverse_y(self):
        """Boolean to note whether the Y-axis of the chart is reversed.

        If True, time over the day flows from the top of the chart to the bottom
        instead of the bottom to the top.
        """
        return self._reverse_y

    @property
    def colored_mesh2d(self):
        """Get a colored Mesh2D for this graphic."""
        return self._compute_colored_mesh2d()

    @property
    def colored_mesh3d(self):
        """Get a colored Mesh3D for this graphic.

        Note that this will be the same as the colored_mesh2d if the z_dim
        value is 0.
        """
        return self._compute_colored_mesh3d()

    @property
    def legend(self):
        """The legend assigned to this graphic."""
        return self._container._legend

    @property
    def chart_border2d(self):
        """Get a Polyline2D for the border of the plot."""
        base_pt = Point2D(self._base_point.x, self._base_point.y)
        width = self._container.max_point.x - self._container.min_point.x
        height = self._container.max_point.y - self._container.min_point.y
        pgon = Polygon2D.from_rectangle(base_pt, Vector2D(0, 1), width, height)
        return Polyline2D.from_polygon(pgon)

    @property
    def chart_border3d(self):
        """Get a Polyline3D for the border of the plot."""
        plane = Plane(o=Point3D(0, 0, self._base_point.z))
        return Polyline3D.from_polyline2d(self.chart_border2d, plane)

    @property
    def hour_lines2d(self):
        """Get a list of LineSegment2D for the 6-hour intervals of the chart."""
        if not self._hour_points:
            self._compute_static_hour_line_pts()
        vec = Vector2D(self._num_x * self._x_dim)
        return [LineSegment2D(pt, vec) for pt in self._hour_points]

    @property
    def hour_lines3d(self):
        """Get a list of LineSegment3D for the 6-hour intervals of the chart."""
        if not self._hour_points:
            self._compute_static_hour_line_pts()
        vec = Vector3D(self._num_x * self._x_dim)
        return [LineSegment3D(Point3D(pt.x, pt.y, self._base_point.z), vec)
                for pt in self._hour_points]

    @property
    def hour_label_points2d(self):
        """Get a list of Point2Ds for the 6-hour text labels for the chart."""
        if not self._hour_points:
            self._compute_static_hour_line_pts()
        txt_hght = self.legend_parameters.text_height
        return [Point2D(pt.x - txt_hght * 2, pt.y) for pt in self._hour_points]

    @property
    def hour_label_points3d(self):
        """Get a list of Point3Ds for the 6-hour text labels for the chart."""
        if not self._hour_points:
            self._compute_static_hour_line_pts()
        txt_hght = self.legend_parameters.text_height
        return [Point3D(pt.x - txt_hght * 2, pt.y, self._base_point.z)
                for pt in self._hour_points]

    @property
    def hour_labels(self):
        """Get a list of text strings for the hour labels for the chart.

        These will be in 12-hour clock format.
        """
        if not self._hour_text:
            self._compute_static_hour_line_pts()
        return self._hour_text

    @property
    def hour_labels_24(self):
        """Get a list of text strings for the hour labels for the chart.

        These will be in 24-hour clock format.
        """
        if not self._hour_text_24:
            self._compute_static_hour_line_pts()
        return self._hour_text_24

    @property
    def month_lines2d(self):
        """Get a list of LineSegment2D for the month intervals of the chart."""
        if not self._month_points:
            self._compute_month_line_pts()
        vec = Vector2D(0, self._num_y * self._y_dim)
        return [LineSegment2D(pt, vec) for pt in self._month_points]

    @property
    def month_lines3d(self):
        """Get a list of LineSegment3D for the month intervals of the chart."""
        if not self._month_points:
            self._compute_month_line_pts()
        vec = Vector3D(0, self._num_y * self._y_dim, 0)
        return [LineSegment3D(Point3D(pt.x, pt.y, self._base_point.z), vec)
                for pt in self._month_points]

    @property
    def month_label_points2d(self):
        """Get a list of Point2Ds for the month text labels for the chart."""
        if not self._month_label_points:
            self._compute_month_line_pts()
        txt_hght = self.legend_parameters.text_height
        return [Point2D(pt.x, pt.y - txt_hght) for pt in self._month_label_points]

    @property
    def month_label_points3d(self):
        """Get a list of Point3Ds for the month text labels for the chart."""
        if not self._month_label_points:
            self._compute_month_line_pts()
        txt_hght = self.legend_parameters.text_height
        return [Point3D(pt.x, pt.y - txt_hght, self._base_point.z)
                for pt in self._month_label_points]

    @property
    def month_labels(self):
        """Get a list of text strings for the month labels for the chart."""
        if not self._month_text:
            self._compute_month_line_pts()
        return self._month_text

    @property
    def title_text(self):
        """Text string for the title of the hourly plot."""
        title_array = ['{} ({})'.format(self._data_collection.header.data_type,
                                        self._data_collection.header.unit)]
        title_array.append(str(self._data_collection.header.analysis_period))
        for key, val in self._data_collection.header.metadata.items():
            title_array.append('{}: {}'.format(key, val))
        return '\n'.join(title_array)

    @property
    def lower_title_location(self):
        """A Plane for the lower location of title text."""
        pln = self._container.lower_title_location
        txt_hght = self.legend_parameters.text_height
        return Plane(pln.n, Point3D(pln.o.x, pln.o.y - txt_hght * 2, pln.o.z))

    @property
    def upper_title_location(self):
        """A Plane for the upper location of title text."""
        num_lines = self.title_text.count('\n') + 4
        pln = self._container.upper_title_location
        txt_hght = self.legend_parameters.text_height
        return Plane(pln.n, Point3D(pln.o.x, pln.o.y + txt_hght * num_lines, pln.o.z))

    @property
    def analysis_period(self):
        """The AnalysisPeriod assigned to the hourly plot's data collection."""
        return self._data_collection.header.analysis_period

    @property
    def values(self):
        """A list of values assigned to this hourly plot.

        These will align correctly with the mesh faces, even when reverse_y is True.
        """
        if self._reverse_y:  # reverse each day of values before returning it
            rev_values = []
            dts = self._data_collection.datetimes
            day_values = []
            current_day = dts[0].day
            for dat_t, col in zip(dts, self._data_collection.values):
                if dat_t.day == current_day:
                    day_values.append(col)
                else:
                    day_values.reverse()
                    rev_values.extend(day_values)
                    current_day = dat_t.day
                    day_values = [col]
            day_values.reverse()
            rev_values.extend(day_values)
            return rev_values
        return self._data_collection.values

    @property
    def colors(self):
        """A list of colors assigned to the mesh faces of this hourly plot.

        These will align correctly with the mesh faces, even when reverse_y is True.
        """
        if self._reverse_y:  # reverse each day of colors before returning it
            rev_colors = []
            dts = self._data_collection.datetimes
            day_colors = []
            current_day = dts[0].day
            for dat_t, col in zip(dts, self._container.value_colors):
                if dat_t.day == current_day:
                    day_colors.append(col)
                else:
                    day_colors.reverse()
                    rev_colors.extend(day_colors)
                    current_day = dat_t.day
                    day_colors = [col]
            day_colors.reverse()
            rev_colors.extend(day_colors)
            return rev_colors
        return self._container.value_colors

    def custom_hour_lines2d(self, hour_labels):
        """Get a list of LineSegment2D for a list of numbers representing hour labels.

        Args:
            hour_labels: An array of numbers from 0 to 24 representing the hours
                to display. (eg. [0, 3, 6, 9, 12, 15, 18, 21, 24])
        """
        _hour_points, _hour_text, _hour_24 = self._compute_hour_line_pts(hour_labels)
        vec = Vector2D(self._num_x * self._x_dim)
        return [LineSegment2D(pt, vec) for pt in _hour_points]

    def custom_hour_lines3d(self, hour_labels):
        """Get a list of LineSegment3D for the 6-hour intervals of the chart.

        Args:
            hour_labels: An array of numbers from 0 to 24 representing the hours
                to display. (eg. [0, 3, 6, 9, 12, 15, 18, 21, 24])
        """
        _hour_points, _hour_text, _hour_24 = self._compute_hour_line_pts(hour_labels)
        vec = Vector3D(self._num_x * self._x_dim)
        return [LineSegment3D(Point3D(pt.x, pt.y, self._base_point.z), vec)
                for pt in _hour_points]

    def custom_hour_label_points2d(self, hour_labels):
        """Get a list of Point2Ds for the 6-hour text labels for the chart.

        Args:
            hour_labels: An array of numbers from 0 to 24 representing the hours
                to display. (eg. [0, 3, 6, 9, 12, 15, 18, 21, 24])
        """
        _hour_points, _hour_text, _hour_24 = self._compute_hour_line_pts(hour_labels)
        txt_hght = self.legend_parameters.text_height
        return [Point2D(pt.x - txt_hght * 2, pt.y) for pt in _hour_points]

    def custom_hour_label_points3d(self, hour_labels):
        """Get a list of Point3Ds for the 6-hour text labels for the chart.

        Args:
            hour_labels: An array of numbers from 0 to 24 representing the hours
                to display. (eg. [0, 3, 6, 9, 12, 15, 18, 21, 24])
        """
        _hour_points, _hour_text, _hour_24 = self._compute_hour_line_pts(hour_labels)
        txt_hght = self.legend_parameters.text_height
        return [Point3D(pt.x - txt_hght * 2, pt.y, self._base_point.z)
                for pt in _hour_points]

    def custom_hour_labels(self, hour_labels, clock_24=False):
        """Get a list of text strings for the 6-hour labels for the chart.

        Args:
            hour_labels: An array of numbers from 0 to 24 representing the hours
                to display. (eg. [0, 3, 6, 9, 12, 15, 18, 21, 24])
            clock_24: Boolean for whether a 24-hour clock should be used instead
                of the 12-hour clock.
        """
        _hour_points, _hour_text, _hour_24 = self._compute_hour_line_pts(hour_labels)
        return _hour_24 if clock_24 else _hour_text

    def _compute_colored_mesh2d(self):
        """Compute a colored mesh from this object's data collection."""
        # generate the base mesh as a standard grid
        _colored_mesh2d = Mesh2D.from_grid(
            self.base_point, self._num_x, self._num_y, self.x_dim, self.y_dim)

        # remove any faces in the base mesh that do not represent the data
        if not isinstance(self.data_collection, HourlyContinuousCollection):
            # get a pattern of booleans for whether mesh faces should be included
            data_coll_moys = [dt.moy for dt in self.data_collection.datetimes]
            data_coll_moys.append(527100)  # extra value for the end of the list
            found_i = 0
            mesh_pattern = []
            s_aper = self.analysis_period
            m_aper = s_aper if s_aper.st_hour <= s_aper.end_hour else \
                AnalysisPeriod(s_aper.st_month, s_aper.st_day, 0, s_aper.end_month,
                               s_aper.end_day, 23, s_aper.timestep, s_aper.is_leap_year)
            for moy in m_aper.moys:
                if moy == data_coll_moys[found_i]:
                    mesh_pattern.append(True)
                    found_i += 1
                else:
                    mesh_pattern.append(False)
            if self._reverse_y:
                hr_diff = abs(m_aper.end_hour - m_aper.st_hour)
                t_step = m_aper.timestep
                t_diff = t_step * hr_diff + 1 if t_step == 1 or hr_diff != 23 else \
                    t_step * (hr_diff + 1)
                mesh_pat_rev = []
                for i in range(0, len(mesh_pattern), t_diff):
                    mesh_pat_rev.extend(reversed(mesh_pattern[i:i + t_diff]))
                mesh_pattern = mesh_pat_rev
            _colored_mesh2d = _colored_mesh2d.remove_faces_only(mesh_pattern)

        # assign the colors to the mesh
        _colored_mesh2d.colors = self.colors
        return _colored_mesh2d

    def _compute_colored_mesh3d(self):
        """Compute a colored mesh from this object's data collection."""
        _colored_mesh3d = Mesh3D.from_mesh2d(
            self.colored_mesh2d, Plane(o=Point3D(0, 0, self._container.min_point.z)))
        if self.z_dim != 0:
            _colored_mesh3d = _colored_mesh3d.height_field_mesh(
                self.data_collection.values, (0, self.z_dim))
        return _colored_mesh3d

    def _compute_static_hour_line_pts(self):
        """Compute the points for the hour lines and labels."""
        self._hour_points, self._hour_text, self._hour_text_24 = \
            self._compute_hour_line_pts(self.HOUR_LABELS)

    def _compute_hour_line_pts(self, hour_labels):
        """Compute the points for the hour lines and labels."""
        s_aper = self.analysis_period
        m_aper = s_aper if s_aper.st_hour <= s_aper.end_hour else \
            AnalysisPeriod(s_aper.st_month, s_aper.st_day, 0, s_aper.end_month,
                           s_aper.end_day, 23, s_aper.timestep, s_aper.is_leap_year)
        st_hr = m_aper.st_hour
        end_hr = m_aper.end_hour + 1
        t_step = m_aper.timestep
        _hour_points = []
        _hour_text, _hour_text_24 = [], []
        last_hr = 0
        for hr in hour_labels:
            if st_hr <= hr <= end_hr:
                y_dist = (hr - st_hr) * self.y_dim * t_step
                pt_y = self.base_point.y + y_dist if not self._reverse_y else \
                    self._container.max_point.y - y_dist
                pt = Point2D(self._container.min_point.x, pt_y)
                _hour_points.append(pt)
                _hour_text_24.append('{}:00'.format(hr))
                hr_val = hr if hr <= 12 else hr - 12
                am_pm = 'PM' if 12 <= hr < 24 else 'AM'
                if hr_val == 0:
                    hr_val = 12
                _hour_text.append('{} {}'.format(hr_val, am_pm))
                last_hr = hr
        if self.analysis_period.timestep > 1 and last_hr == end_hr:
            _hour_points.pop(-1)
            _hour_text.pop(-1)
        return _hour_points, _hour_text, _hour_text_24

    def _compute_month_line_pts(self):
        """Compute the points for the month lines and labels."""
        # extract several reused properties from the analysis period
        st_mon = self.analysis_period.st_month
        end_mon = self.analysis_period.end_month
        st_day = self.analysis_period.st_day
        end_day = self.analysis_period.end_day
        dpm = AnalysisPeriod.NUMOFDAYSEACHMONTHLEAP \
            if self.analysis_period.is_leap_year \
            else AnalysisPeriod.NUMOFDAYSEACHMONTH

        # create a list of days in each of the months and collect month text
        self._month_text = [AnalysisPeriod.MONTHNAMES[st_mon]]
        days_list = []
        if st_mon == end_mon:
            days_list = [dpm[st_mon - 1] + 1 - st_day + (end_day - dpm[st_mon - 1])]
        else:
            days_list.append(dpm[st_mon - 1] + 1 - st_day)
        month_count = len(self.analysis_period.months_int) - 2
        for count, month in enumerate(self.analysis_period.months_int[1:]):
            self._month_text.append(AnalysisPeriod.MONTHNAMES[month])
            if count == month_count:
                days_list.append(end_day)
            else:
                days_list.append(dpm[month - 1])

        # create the points for each of the month labels
        b_pt = self._base_point
        self._month_label_points = \
            [Point2D(b_pt.x + (days_list[0] / 2) * self.x_dim, b_pt.y)]
        for mon_days in days_list[1:]:
            prev_pt = self._month_label_points[-1]
            new_pt = Point2D(prev_pt.x + mon_days * self.x_dim, prev_pt.y)
            self._month_label_points.append(new_pt)

        # create the points for each of the month lines
        self._month_points = []
        if len(days_list) > 1:
            prev_x = b_pt.x + days_list[0] * self.x_dim
            for mon_days in days_list[1:]:
                self._month_points.append(Point2D(prev_x, b_pt.y))
                prev_x += mon_days * self.x_dim

    @staticmethod
    def _check_dim(dim_value, dim_name):
        """Check a given value for a dimension input."""
        assert isinstance(dim_value, (float, int)), 'Expected number for ' \
            'HourlyPlot {}. Got {}.'.format(dim_name, type(dim_value))
        assert dim_value > 0, 'HourlyPlot {} must be greater than 0. ' \
            'Got {}.'.format(dim_name, dim_value)
        return dim_value

    def __repr__(self):
        """Hourly Plot representation."""
        return 'Hourly Plot:\n{}'.format(self.data_collection.header)
