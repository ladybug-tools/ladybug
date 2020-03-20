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
from ladybug_geometry.geometry2d.arc import Arc2D
from ladybug_geometry.geometry3d.pointvector import Point3D, Vector3D
from ladybug_geometry.geometry3d.line import LineSegment3D
from ladybug_geometry.geometry3d.plane import Plane
from ladybug_geometry.geometry3d.polyline import Polyline3D
from ladybug_geometry.geometry3d.mesh import Mesh3D


from math import pi, cos, sin, atan2, log, ceil


class WindRose(object):
    """Module for visualization of wind data collection by orientation.
    Args:
        data_collection: A HourlyContinuousCollection or HourlyDiscontinuousCollection
            which will be used to generate the windrose.
        legend_parameters: An optional LegendParameter object to change the display
            of the windrose (Default: None).
        base_point: An optional Point3D to be used as a starting point to generate
            the geometry of the plot (Default: (0, 0, 0)).
        scale: The scale of the wind rose.

    Properties:
        * direction_data_collection
        * speed_data_collection
        * legend
        * legend_parameters
        * base_point
        * radius
        * colored_mesh
        * chart_border
        * orientation_lines
        * frequency_lines
        * title_text
        * analysis_period
        * values
        * colors

        # TODO: Add this
        # * orientation_label_points
        # * orientation_labels
        # * frequency_label_points
        # * frequency_labels
        """

    # TODO: Uncomment this.
    # __slots__ = ('_direction_data_collection', '_speed_data_collection', '_center_point',
    #              '_base_point', '_stack', '_radius', '_colored_mesh', '_container',
    #              '_legend_parameters', '_chart_border')

    def __init__(self, direction_data_collection, speed_data_collection,
                 legend_parameters=None, stack=True, base_point=Point3D(), radius=1):

        """Initialize windrose plot."""
        # Check the input objects
        acceptable_colls = (HourlyContinuousCollection, HourlyDiscontinuousCollection)
        assert isinstance(direction_data_collection, acceptable_colls), 'Windrose ' \
            'direction_data_collection must be a HourlyContinuousCollection or ' \
            'HourlyDiscontinuousCollection. Got {}.'.format(
                type(direction_data_collection))
        assert isinstance(speed_data_collection, acceptable_colls), 'Windrose ' \
            'speed_data_collection must be a HourlyContinuousCollection or ' \
            'HourlyDiscontinuousCollection. Got {}.'.format(
                type(speed_data_collection))
        assert isinstance(base_point, Point3D), 'Expected Point3D for ' \
            'Wind rose base point. Got {}.'.format(type(base_point))

        # Ensure the analysis period of the data collection has been validated
        if not direction_data_collection.validated_a_period:
            direction_data_collection = \
                direction_data_collection.validate_analysis_period()
        if not direction_data_collection.validated_a_period:
            speed_data_collection = \
                speed_data_collection.validate_analysis_period()

        # Assign the inputs as properties of this data collection
        self._direction_data_collection = direction_data_collection.to_immutable()
        self._speed_data_collection = speed_data_collection.to_immutable()
        self._legend_parameters = legend_parameters
        self._stack = stack
        self._base_point = base_point
        self._center_point = base_point - Point3D(-radius, -radius)
        self._radius = radius

        # set properties to None that will be computed later
        self._colored_mesh = None
        self._chart_border = None
        # Create the graphic container from the inputs
        max_pt = self._center_point + Point3D(radius, radius)
        self._container = GraphicContainer(
            speed_data_collection.values, base_point, max_pt, legend_parameters,
            speed_data_collection.header.data_type, speed_data_collection.header.unit)

    # TODO: Add these properties?
    #     maximum_frequency: An optional number between 1 and 100 that represents the
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
    #      number_of_directions: The number of orientations to divided the wind rose
    #        directions.

    @property
    def direction_data_collection(self):
        """The direction data collection assigned to this windrose plot."""
        return self._direction_data_collection

    @property
    def speed_data_collection(self):
        """The speed data collection assigned to this windrose plot."""
        return self._speed_data_collection

    @property
    def legend_parameters(self):
        """The legend parameters customizing this windrose plot."""
        return self._container.legend_parameters

    @property
    def base_point(self):
        """Point3D for the base point of this windrose plot."""
        return self._base_point

    @property
    def radius(self):
        """A number for the radius of the windrose plot."""
        return self._scale

    @property
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
        """Get a Arc2D for the border of the plot."""
        boundary = Arc2D(self._center_point, self.radius * 1.05, 0, 2 * pi)
        return boundary

    @property
    def analysis_period(self):
        """The AnalysisPeriod assigned to the hourly plot's data collection."""
        return self._data_collection.header.analysis_period

    @property
    def values(self):
        """A list of values assigned to this plot."""
        return self._speed_data_collection.values

    @property
    def colors(self):
        """A list of colors assigned to the mesh faces of this windrose plot."""
        return self._container.value_colors

    @staticmethod
    def _linspace(start, stop, num):
        """Return evenly spaced numbers over a specified interval.

        Returns num evenly spaced samples, calculated over the interval [start, stop].
        Equivalent to numpy.linspace(0, 5, 6) -> array([0., 1., 2., 3., 4., 5.])

        Args:
            bin_num: Number of bins
            bin_range: Tuple representing range of values

        Returns:
            A list of numbers defining bin intervals across bin range.
        """
        try:
            delta = stop - start
            return [i * (delta / (num - 1)) + start for i in range(num)]
        except ZeroDivisionError:
            return [start]

    @staticmethod
    def bin_histogram_data(values, bin_arr, bin_range, key=None):
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
            if k < bin_range[0] or k >= bin_range[1]:
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
    def bin_histogram_data_circular(values, bin_arr, bin_range, key=None):
        """Bin data into a histogram for cyclical data.

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

        bin_bound_num = len(bin_arr) - 1

        # Init histogram bins
        hist = [[] for i in range(bin_bound_num)]
        for val in vals:
            k = key(val)

            # Ignore values out of range
            if k < bin_range[0] or k >= bin_range[1]:
                continue

            # This loop will iterate through the bin upper bounds.
            # If the value is within the bounds, the loop is broken.
            # Since values at the end of the list can still be binned
            # into the earlier histogram bars since we have circular
            # data we don't update the bin_index.
            for i in range(bin_bound_num):
                if bin_arr[i] > bin_arr[i + 1]:
                    # If the interval starts data from the end of the list,
                    # split the conditional checks into two to check two
                    # intervals.
                    if (k < bin_range[1] and k >= bin_arr[i]) or \
                       (k < bin_arr[i + 1] and k >= bin_range[0]):
                        hist[i].append(val)
                        break
                else:
                    if k < bin_arr[i + 1]:
                        hist[i].append(val)
                        break

        return hist

    @staticmethod
    def _compute_bar_interval_vecs(base_vec_stack, vec1, vec2, curr_bar_radius,
                                   min_bar_radius, max_bar_radius, ytick_num, ytick_dist):
        """Compute the vectors for intervals of the histogram bars.

        Args:
            # TODO

        Returns:
            # TODO
        """
        bar_interval_vecs = []

        bar_radius = max_bar_radius - min_bar_radius
        # Identify maximum yticks
        max_yticks = ceil(curr_bar_radius / bar_radius * ytick_num)

        for i in range(1, max_yticks + 1):

            # Stack vectors for interval wedges
            ytick_dist_inc = i * ytick_dist
            if ytick_dist_inc > curr_bar_radius:
                ytick_dist_inc = ((i - 1) * ytick_dist) + \
                    (ytick_dist_inc % curr_bar_radius)

            ytick_dist_inc += min_bar_radius

            # Vector multiplication with y_dist_inc and add to bar_coords
            bar_interval_vecs.append([*base_vec_stack,
                                     (vec1[0] * ytick_dist_inc,
                                      vec1[1] * ytick_dist_inc),
                                     (vec2[0] * ytick_dist_inc,
                                      vec2[1] * ytick_dist_inc)])

            base_vec_stack = bar_interval_vecs[-1][-2:][::-1]

        return bar_interval_vecs

    @staticmethod
    def _compute_bar_stack_colors(hist_data, hist_coords):

        colors = []
        for data, vecs in zip(hist_data, hist_coords):
            bar_data_num = len(vecs)
            bar_data_val = [x[1] for x in data]

            if bar_data_val:
                crange = (min(bar_data_val), max(bar_data_val))
                color_arr = WindRose._linspace(*crange, bar_data_num)
                if not color_arr:
                    color_arr = [sum(bar_data_val) / len(bar_data_val)]
                colors.extend(color_arr)
        return colors

    @staticmethod
    def _bin_vectors_radial(bin_arr):
        """Compute the radial coordinates for the histogram bins of values.

        This component will re-orient angles so that 0 degrees starts at the top,
        and increases in a clockwise direction.

        Args:
            # TODO

        Returns:
            # TODO
        """
        vecs = []
        t = 180.0 / pi  # for degrees to radian conversion

        # Midpoint correction to ensure center of wedge is at the top
        phi = 360. / (len(bin_arr) - 1) / 2.
        bin_arr = [t - phi if (t - phi) >= 0.0 else t - phi + 360.
                   for t in bin_arr]

        # Plot the vectors
        for i in range(len(bin_arr) - 1):
            # Correct range
            theta1 = bin_arr[i] - 90.
            theta2 = bin_arr[i + 1] - 90.

            # Solve for unit x, y vectors
            # Flip y-component to ensure clockwise orietnation
            vecs.append(((cos(theta1 / t), -sin(theta1 / t)),
                        (cos(theta2 / t), -sin(theta2 / t))))
        return vecs

    @staticmethod
    def _xtick_grid_radial(bin_vecs, max_bar_radius, vec_cpt):
        """radial histogram.

        Args:
            # TODO

        Returns:
            # TODO
        """
        # Compute x-axis bin boundaries in polar coordinates
        # Vector multiplication with max_bar_radius
        grid_xticks = (((vec_cpt,
                         (max_bar_radius * vec1[0], max_bar_radius * vec1[1])),
                        (vec_cpt,
                         (max_bar_radius * vec2[0], max_bar_radius * vec2[1])))
                       for (vec1, vec2) in bin_vecs)

        # Return flattened list
        return (xtick for xticks in grid_xticks for xtick in xticks)

    @staticmethod
    def _ytick_grid_radial(bin_vecs, max_bar_radius, ytick_num):
        """radial histogram.

        Args:
            # TODO

        Returns:
            # TODO
        """
        # Compute y-axis in radial coordinates, vector multiplication with max_bar_radius
        bar_edge_loop = bin_vecs + [bin_vecs[0]]
        ytick_dist = max_bar_radius / ytick_num  # Length of 1 y-tick
        grid_yticks = (((vec1[0] * i * ytick_dist, vec1[1] * i * ytick_dist)
                        for (vec1, _) in bar_edge_loop)
                       for i in range(1, ytick_num + 1))

        return grid_yticks

    @staticmethod
    def _histogram_coords_radial(bin_vecs, vec_cpt, hist, radius_arr, ytick_num, stack):
        """radial histogram.

        Args:
            # TODO

        Returns:
            # TODO
        """

        # Get histogram properties for plotting bars
        min_bar_radius, max_bar_radius = radius_arr
        bar_radius = max_bar_radius - min_bar_radius
        max_bar_num = max([len(bar) for bar in hist])
        ytick_dist = bar_radius / ytick_num  # Length of 1 y-tick

        # Plot histogram bar in radial coordinates
        hist_coords = []
        for i, curr_bar in enumerate(hist):
            # Compute the current bar radius
            curr_bar_radius = bar_radius / max_bar_num * len(curr_bar)

            (vec1, vec2) = bin_vecs[i]

            if stack:
                if min_bar_radius > 0.0:
                    base = [(vec1[0] * min_bar_radius, vec1[1] * min_bar_radius),
                            (vec2[0] * min_bar_radius, vec2[1] * min_bar_radius)][::-1]
                else:
                    base = [vec_cpt]
                bar_vecs = WindRose._compute_bar_interval_vecs(
                    base, vec1, vec2, curr_bar_radius, min_bar_radius, max_bar_radius,
                    ytick_num, ytick_dist)
                hist_coords.append(bar_vecs)
            else:
                bar_vecs = (vec_cpt,
                            (vec1[0] * curr_bar_radius,
                             vec1[1] * curr_bar_radius),
                            (vec2[0] * curr_bar_radius,
                             vec2[1] * curr_bar_radius))
                hist_coords.append(bar_vecs)

        return hist_coords

    @staticmethod
    def plot_histogram(bars, grid_xticks, grid_yticks, base_point=None, scale=None):
        """Plot histogram.

        Args:
            # TODO

        Returns:
            # TODO
        """
        # Plot histogram bar in radial coordinates
        bars = ((Point2D.from_array(vec) for vec in vecs) for vecs in bars)
        hist = Mesh2D.from_face_vertices(bars, purge=True)

        # Plot x-axis bin boundaries in radial coordinates w/ stacked list comprehensions
        grid_xticks = [LineSegment2D.from_array((v for v in vecs))
                       for vecs in grid_xticks]

        # Plot y-axis in radial coordinates
        grid_yticks = [Polyline2D.from_array((v for v in vecs))
                       for vecs in grid_yticks]

        return hist, grid_xticks, grid_yticks

    @staticmethod
    def windrose(bin_values, sec_values, bin_intervals, bin_range, bar_intervals=None,
                 stack=True, ytick_num=10, xticks=None):

        vec_cpt = (0, 0)
        max_bar_radius = 1.0
        bin_arr = WindRose._linspace(*bin_range, bin_intervals + 1)
        bin_vecs = WindRose._bin_vectors_radial(bin_arr)

        # Filter out zero values
        _bin_values = []
        _sec_values = []
        for d, v in zip(bin_values, sec_values):
            if v > 1.5:#1e-10:
                _bin_values.append(d)
                _sec_values.append(v)

        # Calculate zero rose properties
        zeros_per_bin = (len(sec_values) - len(_sec_values)) / bin_intervals
        zero_bin_data = [i * 360. / bin_intervals for i in range(bin_intervals)]

        # Zero hist data
        zero_hist_data = WindRose.bin_histogram_data_circular(zero_bin_data, bin_arr,
                                                              bin_range)

        # Regular hist data
        regl_hist_data = WindRose.bin_histogram_data_circular(zip(_bin_values,
                                                                  _sec_values),
                                                              bin_arr, bin_range,
                                                              key=lambda v: v[0])

        # Calculate radius of zero rose
        max_bar_num = max([len(bar) for bar in regl_hist_data]) + zeros_per_bin
        zero_rose_radius = zeros_per_bin / max_bar_num * max_bar_radius

        # Compute the coordinates
        zero_hist_coords = WindRose._histogram_coords_radial(bin_vecs, vec_cpt,
                                                             zero_hist_data,
                                                             (0.0, zero_rose_radius),
                                                             ytick_num, stack=False)

        # Plot coordinates
        regl_hist_coords = WindRose._histogram_coords_radial(bin_vecs, vec_cpt,
                                                             regl_hist_data,
                                                             (zero_rose_radius,
                                                              max_bar_radius),
                                                             ytick_num, stack=stack)

        # Plot grid
        xgrid_coords = WindRose._xtick_grid_radial(bin_vecs, max_bar_radius, vec_cpt)
        ygrid_coords = WindRose._ytick_grid_radial(bin_vecs, max_bar_radius, ytick_num)

        # Flatten and add coordinates
        zero_hist_coords = ([v] for v in zero_hist_coords)
        hist_coords = [intervals for bar in zero_hist_coords for intervals in bar] + \
            [intervals for bar in regl_hist_coords for intervals in bar]

        # Plot
        plotted = WindRose.plot_histogram(hist_coords, grid_xticks=xgrid_coords,
                                          grid_yticks=ygrid_coords, base_point=None, scale=None)

        # Get colors
        colors = [0 for i in range(len(zero_hist_data))]
        colors += WindRose._compute_bar_stack_colors(regl_hist_data, regl_hist_coords)

        return plotted, colors

    @staticmethod
    def _compute_colored_mesh():
        """Compute a colored mesh from this object's data collections."""
        #     self._colored_mesh2d = self._colored_mesh2d.remove_faces_only(mesh_pattern)

        # # assign the colors to the mesh
        # self._colored_mesh2d.colors = self.value_colors

    def __repr__(self):
        """Wind rose Collection representation."""
        return 'Wind Rose:\n\n{}\n\n{}'.format(
            self.direction_data_collection.header,
            self.speed_data_collection.header)