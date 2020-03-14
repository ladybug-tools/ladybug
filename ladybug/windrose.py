# coding=utf-8
from __future__ import division

from .analysisperiod import AnalysisPeriod
from .datacollection import HourlyContinuousCollection, HourlyDiscontinuousCollection
from .graphic import GraphicContainer
from .legend import LegendParameters

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


from math import pi, cos, sin, log, ceil


class WindRose(object):
    """Module for visualization of wind data collection by orientation.
    Args:
        data_collection: A HourlyContinuousCollection or HourlyDiscontinuousCollection
            which will be used to generate the hourly plot.
        legend_parameters: An optional LegendParameter object to change the display
            of the HourlyPlot (Default: None).
        base_point: An optional Point3D to be used as a starting point to generate
            the geometry of the plot (Default: (0, 0, 0)).
        scale: The scale of the wind rose.

    Properties:
        * data_collection
        * legend_parameters
        * base_point
        * radius_dim
        * colored_mesh
        * legend
        * orientation_lines
        * orientation_label_points
        * orientation_labels
        * frequency_lines
        * frequency_label_points
        * frequency_labels
        #* mean_velocity_lines
        #* mean_velocity_points
        #* mean_velocity_labels
        * title_text
        * analysis_period
        * frequency_values
        * frequency_value_colors
        #* mean_velocity_values
        #* mean_velocity_value_colors
        * wind_direction_values
    """

    # TODO: fix this once properties have stabilized
    # __slots__ = ('_data_collection', '_base_point', '_x_dim', '_y_dim', '_z_dim',
    #              '_num_y', '_num_x', '_container', '_colored_mesh2d', '_colored_mesh3d',
    #              '_hour_points', '_hour_text', '_month_points', '_month_label_points',
    #              '_month_text')

    def __init__(self, data_collection, legend_parameters=None, base_point=Point3D(),
                 scale=1):
        """Initialize wind rose plot."""

        # Check the input objects
        acceptable_colls = (HourlyContinuousCollection, HourlyDiscontinuousCollection)
        assert isinstance(data_collection, acceptable_colls), 'Wind rose' \
            'data_collection must be a HourlyContinuousCollection or ' \
            'HourlyDiscontinuousCollection. Got {}.'.format(type(data_collection))
        assert isinstance(base_point, Point3D), 'Expected Point3D for ' \
            'Wind rose base point. Got {}.'.format(type(base_point))

        # Ensure the analysis period of the data collection has been validated
        if not data_collection.validated_a_period:
            data_collection = data_collection.validate_analysis_period()

        # assign the inputs as properties of this data collection
        self._data_collection = data_collection.to_immutable()
        self._base_point = base_point
        self._scale = scale

        # set properties to None that will be computed later
        self._colored_mesh = None

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
            self._num_y = ((a_per.end_hour - a_per.st_hour) * a_per.timestep) + 1
        x_dist = x_dim * self._num_x
        y_dist = y_dim * self._num_y
        max_pt = Point3D(base_point.x + x_dist, base_point.y + y_dist, base_point.z)
        self._container = GraphicContainer(
            data_collection.values, base_point, max_pt, legend_parameters,
            data_collection.header.data_type, data_collection.header.unit)

    # maximum_frequency: An optional number between 1 and 100 that represents the
    #         maximum percentage of hours that the outer-most ring of the wind rose
    #         represents.  By default, this value is set by the wind direction with the
    #         largest number of hours (the highest frequency) but you may want to change
    #         this if you have several wind roses that you want to compare to each other.
    #         For example, if you have wind roses for different months or seasons, which
    #         each have different maximum frequencies.
    #     showFrequency_: Connect boolean and set it to True to display frequency of wind
    #         coming from each direction. By default, these values will be displayed in
    #         gray color.
    #     showAverageVelocity_: Connect boolean and set it to True to display average wind
    #         velocity in m/s for wind coming from each direction. If a conditional
    #         statement is connected to the conditionalStatement_ input, a beaufort number
    #         is plotted(in square brackets) along with the average velocities. This
    #         number indicates the effect caused by wind of average velocity coming from
    #         that partcular direction. By default, these values will be displayed in
    #         black color.
    #number_of_directions: The number of orientations to divided the wind rose
    #        directions.

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
    def scale(self):
        """A number for the scale of the wind rose plot."""
        return self._scale

    def colored_mesh(self):
        """Get a colored Mesh2D for this graphic."""
        if not self._colored_mesh2d:
            self._compute_colored_mesh2d()
        return self._colored_mesh2d

    @property
    def legend(self):
        """The legend assigned to this graphic."""
        return self._container._legend

    @property
    def chart_border(self):
        """Get a Polyline2D for the border of the plot."""
        base_pt = Point2D(self._base_point.x, self._base_point.y)
        width = self._container.max_point.x - self._container.min_point.x
        height = self._container.max_point.y - self._container.min_point.y
        pgon = Polygon2D.from_rectangle(base_pt, Vector2D(0, 1), width, height)
        return Polyline2D.from_polygon(pgon)

    @property
    def analysis_period(self):
        """The AnalysisPeriod assigned to the hourly plot's data collection."""
        return self._data_collection.header.analysis_period

    @property
    def values(self):
        """A list of values assigned to this hourly plot."""
        return self._data_collection.values

    @property
    def value_colors(self):
        """A list of colors assigned to the mesh faces of this hourly plot."""
        return self._container.value_colors

    @staticmethod
    def _bin_array(bin_num, bin_range):
        """Compute the bin intervals from number of bins.

        Args:
            bin_num: Number of bins
            bin_range: Tuple representing range of values

        Returns:
            A list of numbers defining bin intervals across bin range.
        """
        range_delta = bin_range[1] - bin_range[0]

        return [i * (range_delta / bin_num) + bin_range[0] for i in range(bin_num + 1)]

    @staticmethod
    def _bin_polar(bin_arr):
        """Compute the polar coordinates for the histogram bins of values.

        Args:
            # TODO

        Returns:
            # TODO
        """

        # Init polar matrix
        polar_mtx = [None] * (len(bin_arr) - 1)
        t = 180.0 / pi  # for degrees to radian conversion

        for i in range(len(bin_arr) - 1):

            # Get polar args for bin edges
            theta1, theta2 = bin_arr[i] + 90., bin_arr[i + 1] + 90.

            # Solve for unit x, y vectors
            polar_mtx[i] = (Vector2D(cos(theta1 / t), sin(theta1 / t)),
                            Vector2D(cos(theta2 / t), sin(theta2 / t)))

        return polar_mtx

    @staticmethod
    def histogram_bins(values, bin_arr, key=None):
        """Compute the histogram from this object's data collection.

        The data is binned inclusive of the lower bound but exclusive of the
        upper bound for intervals.

        Example of where we lose 3 because of exclusive upper bound:
        histogram([0, 0, 0.9, 1, 1.5, 1.99, 2, 3], (0, 1, 2, 3))
        >>> [[0, 0, 0.9], [1, 1.5, 1.99], [2]]

        Args:
            values: list of numerical data to bin.
            bin_arr: A list of bin bounds.
            is_gradient: Optional boolean parameter to pass to nest datas for histogram gradient

        Returns:
            A list of lists representing the ordered values binned by frequency.
                Example: histogram([0, 1, 1, 2, 3], [0, 2, 3]) -> [[0, 1, 1], [2]]
        """

        if key is None:
            key = lambda v: v

        vals = sorted(values, key=key)

        bin_bound_num = len(bin_arr)

        # Init histogram bins
        hist = [[] for i in range(bin_bound_num - 1)]
        bin_index = 0
        for val in vals:
            k = key(val)
            # Ignore values out of range
            if k < bin_arr[0] or k >= bin_arr[-1]:
                continue

            # This loop will iterate through the bin upper bounds.
            # If the value is within the bounds, the lower bound
            # of the bin_index is updated, and the loop is broken
            for i in range(bin_index, bin_bound_num - 1):
                if k < bin_arr[i + 1]:
                    hist[i].append(val)
                    bin_index = i
                    break

        return hist

    @staticmethod
    def histogram_polar_coords(bin_values, sec_values=None, bin_arr=None,  yticks=10):
        """Polar histogram.

        Args:
            # TODO

        Returns:
            # TODO
        """

        if bin_arr is None:
            bin_arr = (0, 45, 90, 135, 180, 225, 270, 315, 360)

        # Compute histogram data differently based on wheter we need nested data or not
        if sec_values is None:
            hist = WindRose.histogram_bins(bin_values, bin_arr)
        else:
            hist = WindRose.histogram_bins(zip(bin_values, sec_values), bin_arr,
                                           key=lambda v: v[0])

        # Compute polar edges
        polar_mtx = WindRose._bin_polar(bin_arr)

        # Get histogram properties for plotting
        num_vals = sum([len(bar) for bar in hist])
        vec_cpt = Vector2D(0, 0)
        max_radius = 1.0
        max_bar = max([len(bar) for bar in hist])
        y_dist = max_radius / (yticks-1)  # Length of 1 y-tick

        #from pprint import pprint as pp
        #pp(hist)
        #print(max_radius, y_dist)


        # Plot histogram bar in polar coordinates
        hist_coords = []
        bar_coords = []
        c = 0
        for (vec1, vec2), bar in zip(polar_mtx, hist):
            #if c == 0:
            #    print(bar)
            # Define the max edges of the wedge
            max_bar_num = len(bar)
            max_bar_radius = max_radius/max_bar * max_bar_num

            if sec_values is not None:
                #bar_coords = []
                base_coords = [vec_cpt]
                #y_intervals = WindRose._bin_array(yticks, (0, num_vals))
                bar_yticks = ceil(max_bar_radius / max_radius * yticks)

                for i in range(1, bar_yticks+1):
                    # Stack vectors for interval wedges
                    y_dist_inc = i * y_dist

                    if y_dist_inc > max_bar_radius:
                        y_dist_inc = ((i-1) * y_dist) + ((i * y_dist) % max_bar_radius)
                    bar_coords.append([*base_coords,
                                       vec1 * y_dist_inc,
                                       vec2 * y_dist_inc])
                    base_coords = bar_coords[-1][-2:][::-1]

                #hist_coords.append(bar_coords)

            else:
                hist_coords.append((vec_cpt,
                                    vec1 * max_bar_radius,
                                    vec2 * max_bar_radius))
            c += 1
        if sec_values is not None:
            hist_coords = bar_coords
        # Plot x-axis bin boundaries in polar coordinates
        grid_xticks = (([vec_cpt, max_radius * vec1], [vec_cpt, max_radius * vec2])
                       for (vec1, vec2), bar in zip(polar_mtx, hist))
        # Flatten list
        grid_xticks = (xtick for xticks in grid_xticks for xtick in xticks)

        # Plot y-axis in polar coordinates
        polar_mtx_loop = polar_mtx + [polar_mtx[0]]
        grid_yticks = ([vecs[0] * i * y_dist for vecs in polar_mtx_loop]
                       for i in range(1, yticks + 1))

        return hist_coords, grid_xticks, grid_yticks

    @staticmethod
    def plot_histogram(bars, grid_xticks, grid_yticks, base_point=None, scale=None):
        """Plot histogram.

        Args:
            # TODO

        Returns:
            # TODO
        """
        # TODO: Add/sclae vectors here
        # Plot histogram bar in polar coordinates
        hist = [Polygon2D.from_array([v.to_array() for v in vecs]) for vecs in bars]

        # Plot x-axis bin boundaries in polar coordinates w/ stacked list comprehensions
        grid_xticks = [LineSegment2D.from_array((v.to_array() for v in vecs))
                       for vecs in grid_xticks]

        # Plot y-axis in polar coordinates
        # TODO: Is there a way to generalize Polyine2d for rect and polar hist?
        grid_yticks = [Polyline2D.from_array((v.to_array() for v in vecs))
                       for vecs in grid_yticks]

        return hist, grid_xticks, grid_yticks


    @staticmethod
    def _compute_colored_mesh():
        """Compute a colored mesh from this object's data collection."""

        # # generate the base mesh as a stanadard grid
        # self._colored_mesh2d = Mesh2D.from_grid(
        #     self.base_point, self._num_x, self._num_y, self.x_dim, self.y_dim)

        # # reomve any faces in the base mesh that do not represent the data
        # if not isinstance(self.data_collection, HourlyContinuousCollection):
        #     # get a pattern of booleans for whether mesh faces should be included
        #     data_coll_moys = [dt.moy for dt in self.data_collection.datetimes]
        #     data_coll_moys.append(527100)  # extra value for the end of the list
        #     found_i = 0
        #     mesh_pattern = []
        #     for moy in self.analysis_period.moys:
        #         if moy == data_coll_moys[found_i]:
        #             mesh_pattern.append(True)
        #             found_i += 1
        #         else:
        #             mesh_pattern.append(False)
        #     self._colored_mesh2d = self._colored_mesh2d.remove_faces_only(mesh_pattern)

        # # assign the colors to the mesh
        # self._colored_mesh2d.colors = self.value_colors



    @staticmethod
    def _check_dim(dim_value, dim_name):
        """Check a given value for a dimension input."""
        assert isinstance(dim_value, (float, int)), 'Expected number for ' \
            'HourlyPlot {}. Got {}.'.format(dim_name, type(dim_value))
        assert dim_value > 0, 'HourlyPlot {} must be greater than 0. ' \
            'Got {}.'.format(dim_name, dim_value)
        return dim_value

    def __repr__(self):
        """Wind rose Collection representation."""
        return 'Wind Rose:\n{}'.format(self.data_collection.header)