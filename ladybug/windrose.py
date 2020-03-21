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


from math import pi, cos, sin, ceil


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
                interval1 = (k < bin_range[1] and k >= bin_arr[i])
                interval2 = (k < bin_arr[i + 1] and k >= bin_range[0])
                if interval1 or interval2:
                    hist[i].append(val)
                    break
            else:
                if k < bin_arr[i + 1]:
                    hist[i].append(val)
                    break

    return hist


class WindRose(object):
    """Module for visualization of wind data collection by orientation.
    # TODO: Add rest of args.
    Args:
        data_collection: A HourlyContinuousCollection or HourlyDiscontinuousCollection
            which will be used to generate the windrose.
        legend_parameters: An optional LegendParameter object to change the display
            of the windrose (Default: None).
        base_point: An optional Point3D to be used as a starting point to generate
            the geometry of the plot (Default: (0, 0, 0)).
        scale: The scale of the wind rose.
        number_of_directions: The number of orientations to divided the wind rose
            directions.

    Properties:
        * direction_data_collection
        * speed_data_collection
        * direction_values
        * speed_values
        * analysis_period
        * legend
        * legend_parameters
        * base_point
        * radius
        * colored_mesh
        * border
        * orientation_lines
        * frequency_lines

        # TODO: Add this
        # * orientation_label_points
        # * orientation_labels
        # * frequency_label_points
        # * frequency_labels
        """

    __slots__ = ('_direction_data_collection', '_speed_data_collection',
                 '_number_of_directions', '_legend_parameters', '_show_stack',
                 '_show_zeros', '_base_point', '_base_point', '_radius',
                 '_hist_bin_array', '_hist_bin_vectors', '_colored_mesh', '_border',
                 '_orientation_lines', '_frequency_lines', '_container')

    def __init__(self, direction_data_collection, speed_data_collection,
                 number_of_directions=8, legend_parameters=None, base_point=Point3D(),
                 radius=1, show_stack=True, show_zeros=True):

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

        if legend_parameters is None:
            # TODO: Modify this based on if show_stack = True
            legend_parameters = LegendParameters(min=speed_data_collection.min,
                                                 max=speed_data_collection.max,
                                                 segment_count=11)

        # Assign the inputs as properties of this data collection
        self._direction_data_collection = direction_data_collection.to_immutable()
        self._speed_data_collection = speed_data_collection.to_immutable()
        self._number_of_directions = number_of_directions
        self._legend_parameters = legend_parameters
        self._show_stack = show_stack
        self._show_zeros = show_zeros
        self._base_point = base_point
        self._radius = radius
        self._hist_bin_array = None
        self._hist_bin_vectors = None

        # set properties to None that will be computed later
        self._colored_mesh = None
        self._border = None
        self._orientation_lines = None
        self._frequency_lines = None
        # Create the graphic container from the inputs
        max_pt = Point3D(self._center_point2d.x + radius,
                         self._center_point2d.y + radius, self.base_point.z)
        self._container = GraphicContainer(
            speed_data_collection.values, base_point, max_pt, legend_parameters,
            speed_data_collection.header.data_type, speed_data_collection.header.unit)

    # TODO: Add max frequency parameter
    #     maximum_frequency: An optional number between 1 and 100 that represents the
    #         maximum percentage of hours that the outer-most ring of the wind rose
    #         represents.  By default, this value is set by the wind direction with the
    #         largest number of hours (the highest frequency) but you may want to change
    #         this if you have several wind roses that you want to compare to each other.
    #         For example, if you have wind roses for different months or seasons, which
    #         each have different maximum frequencies.

    @property
    def direction_data_collection(self):
        """The direction data collection assigned to this windrose plot."""
        return self._direction_data_collection

    @property
    def speed_data_collection(self):
        """The speed data collection assigned to this windrose plot."""
        return self._speed_data_collection

    @property
    def speed_values(self):
        """ The speed data values in this windrose plot."""
        return self._speed_data_collection.values

    @property
    def direction_values(self):
        """The direction data values in this windrose plot."""
        return self._direction_data_collection.values

    @property
    def analysis_period(self):
        """The AnalysisPeriod assigned to the hourly plot's data collection."""
        return self._speed_ata_collection.header.analysis_period

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
        return self._radius

    @property
    def colored_mesh(self):
        """Get a colored Mesh2D for this graphic."""
        if not self._colored_mesh:
            # Simplify args
            bin_values = self.direction_values
            sec_values = self.speed_values
            bin_intervals = self._number_of_directions
            bin_arr = self._bin_array
            bin_range = (0., 360.)
            ytick_num = self.legend_parameters.segment_count
            show_stack = self._show_stack

            # Compute the mesh
            if self._show_zeros:
                # TODO: Check radius length when show_stack = False and show_zero = True
                mesh, colors = WindRose._compute_colored_mesh_zero(
                    bin_values, sec_values, bin_intervals, bin_arr, bin_range, ytick_num,
                    show_stack)
            else:
                mesh, colors = WindRose._compute_colored_mesh_regl(
                    bin_values, sec_values, bin_intervals, bin_arr, bin_range, ytick_num,
                    show_stack)

            self._colored_mesh = mesh.scale(self.radius).move(self._center_point2d)
            self._colored_mesh.colors = colors

        return self._colored_mesh

    @property
    def legend(self):
        """The legend assigned to this graphic."""
        return self._container._legend

    @property
    def border(self):
        """Get a Arc2D for the border of the plot."""
        if self._border is None:
            self._border = Arc2D(self._center_point2d, self.radius, 0, 2 * pi)
        return self._border

    @property
    def _bin_array(self):
        if self._hist_bin_array is None:
            bin_intervals = self._number_of_directions
            bin_range = (0., 360.)
            self._hist_bin_array = _linspace(*bin_range, bin_intervals + 1)
        return self._hist_bin_array

    @property
    def _bin_vectors(self):
        if self._hist_bin_vectors is None:
            self._hist_bin_vectors = self._bin_vectors_radial(self._bin_array)
        return self._hist_bin_vectors

    @property
    def orientation_lines(self):
        """Orientation lines for windrose as LineSegment2D list."""
        if self._orientation_lines is None:
            lines = WindRose._xtick_radial_lines(self._bin_vectors)
            self._orientation_lines = [line.scale(self.radius).move(self._center_point2d)
                                       for line in lines]
        return self._orientation_lines

    @property
    def frequency_lines(self):
        """Frequency lines for windrose as Polygon2D lists."""
        if self._frequency_lines is None:
            ytick_num = self._container.legend_parameters.segment_count
            polys = WindRose._ytick_radial_lines(self._bin_vectors, ytick_num)
            self._frequency_lines = [poly.scale(self.radius).move(self._center_point2d)
                                     for poly in polys]
        return self._frequency_lines

    @property
    def _center_point2d(self):
        """Compute center of windrose plot as Point2D."""
        return Point2D(self.base_point.x + self.radius, self.base_point.y + self.radius)

    @staticmethod
    def _compute_bar_interval_vecs(base_vec_show_stack, vec1, vec2, curr_bar_radius,
                                   min_bar_radius, max_bar_radius, ytick_num,
                                   ytick_dist):
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
            bar_interval_vecs.append([*base_vec_show_stack,
                                     (vec1[0] * ytick_dist_inc,
                                      vec1[1] * ytick_dist_inc),
                                     (vec2[0] * ytick_dist_inc,
                                      vec2[1] * ytick_dist_inc)])

            base_vec_show_stack = reversed(bar_interval_vecs[-1][-2:])

        return bar_interval_vecs

    @staticmethod
    def _compute_hist_colors(hist_data, hist_coords, stack):

        if stack:
            colors = []
            for data, vecs in zip(hist_data, hist_coords):
                bar_data_num = len(vecs)
                bar_data_val = [x[1] for x in data]

                if bar_data_val:
                    crange = (min(bar_data_val), max(bar_data_val))
                    color_arr = _linspace(*crange, bar_data_num)
                    if not color_arr:
                        color_arr = [sum(bar_data_val) / len(bar_data_val)]
                    colors.extend(color_arr)
        else:
            colors = [sum((v[1] for v in hist))/len(hist)
                      if len(hist) > 0 else 0 for hist in hist_data]

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
    def _xtick_radial_lines(bin_vecs):
        """radial histogram.

        Args:
            # TODO

        Returns:
            # TODO
        """
        # Compute x-axis bin boundaries in polar coordinates
        vec_cpt = (0, 0)
        max_bar_radius = 1.0

        # Vector multiplication with max_bar_radius
        grid_xticks = (((vec_cpt,
                         (max_bar_radius * vec1[0], max_bar_radius * vec1[1])),
                        (vec_cpt,
                         (max_bar_radius * vec2[0], max_bar_radius * vec2[1])))
                       for (vec1, vec2) in bin_vecs)

        # Flattened list and return as LineSegment2D
        xtick_array = (xtick for xticks in grid_xticks for xtick in xticks)
        return [LineSegment2D.from_array(vecs) for vecs in xtick_array]

    @staticmethod
    def _ytick_radial_lines(bin_vecs, ytick_num):
        """radial histogram.

        Args:
            # TODO

        Returns:
            # TODO
        """
        max_bar_radius = 1.0

        # Compute y-axis in radial coordinates, vector multiplication with max_bar_radius
        bar_edge_loop = bin_vecs + [bin_vecs[0]]
        ytick_dist = max_bar_radius / ytick_num  # Length of 1 y-tick
        ytick_array = (((vec1[0] * i * ytick_dist, vec1[1] * i * ytick_dist)
                        for (vec1, _) in bar_edge_loop)
                       for i in range(1, ytick_num + 1))

        return [Polygon2D.from_array((v for v in vecs)) for vecs in ytick_array]

    @staticmethod
    def _histogram_array_radial(bin_vecs, vec_cpt, hist, radius_arr, ytick_num,
                                show_stack):
        """radial histogram.

        Args:
            # TODO

        Returns:
            # TODO
        """

        # Get histogram properties for plotting bars
        min_bar_radius, max_bar_radius = radius_arr
        delta_bar_radius = max_bar_radius - min_bar_radius
        max_bar_num = max([len(bar) for bar in hist])
        ytick_dist = delta_bar_radius / ytick_num  # Length of 1 y-tick

        # Plot histogram bar in radial coordinates
        hist_coords = []
        for i, curr_bar in enumerate(hist):
            # Compute the current bar radius
            # curr_bar_radius:delta_bar_radius = len(curr_bar):max_bar_num
            curr_bar_radius = len(curr_bar) / max_bar_num * delta_bar_radius

            (vec1, vec2) = bin_vecs[i]

            if show_stack:
                if min_bar_radius > 0.0:
                    base = reversed([(vec1[0] * min_bar_radius,
                                      vec1[1] * min_bar_radius),
                                     (vec2[0] * min_bar_radius,
                                      vec2[1] * min_bar_radius)])
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
    def _compute_colored_mesh_zero(bin_values, sec_values, bin_intervals, bin_arr,
                                   bin_range, ytick_num, show_stack):
        """Compute a colored mesh from this object's data collections.

        Args:
            # TODO

        Returns:
            # TODO
        """

        # Default rose is a unit circle centered at origin. We can scale and translate
        # the resulting mesh.
        vec_cpt = (0, 0)
        max_bar_radius = 1.0

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
        zero_hist_data = bin_histogram_data_circular(zero_bin_data, bin_arr, bin_range)

        # Regular hist data
        regl_hist_data = bin_histogram_data_circular(
            zip(_bin_values, _sec_values), bin_arr, bin_range, key=lambda v: v[0])

        # Calculate radius of zero rose
        max_bar_num = max([len(bar) for bar in regl_hist_data]) + zeros_per_bin
        zero_rose_radius = zeros_per_bin / max_bar_num * max_bar_radius

        # Compute the coordinates
        zero_hist_coords = WindRose._histogram_array_radial(
            bin_vecs, vec_cpt, zero_hist_data, (0.0, zero_rose_radius), ytick_num,
            show_stack=False)

        # Plot coordinates
        regl_hist_array = WindRose._histogram_array_radial(
            bin_vecs, vec_cpt, regl_hist_data, (zero_rose_radius, max_bar_radius),
            ytick_num, show_stack=show_stack)

        # Flatten and add coordinates
        zero_hist_coords = ([v] for v in zero_hist_coords)
        if not show_stack:
            regl_hist_array = ([v] for v in regl_hist_array)

        # Make mesh
        hist_coords = [intervals for bar in zero_hist_coords for intervals in bar] + \
            [intervals for bar in regl_hist_array for intervals in bar]
        mesh_array = [[Point2D.from_array(vec) for vec in vecs] for vecs in hist_coords]
        mesh = Mesh2D.from_face_vertices(mesh_array, purge=True)

        # Extract speed values for colors
        colors = [0 for i in range(len(zero_hist_data))]
        colors += WindRose._compute_hist_colors(regl_hist_data, regl_hist_array,
                                                stack=show_stack)

        return mesh, colors

    @staticmethod
    def _compute_colored_mesh_regl(bin_values, sec_values, bin_intervals, bin_arr,
                                   bin_range, ytick_num, show_stack):
        """Compute a colored mesh from this object's data collections.

        Args:
            # TODO

        Returns:
            # TODO
        """

        # Default rose is a unit circle centered at origin. We can scale and translate
        # the resulting mesh.
        vec_cpt = (0, 0)
        max_bar_radius = 1.0

        bin_vecs = WindRose._bin_vectors_radial(bin_arr)

        # Filter out zero values
        _bin_values = []
        _sec_values = []
        for d, v in zip(bin_values, sec_values):
            if v > 1.5:#1e-10:
                _bin_values.append(d)
                _sec_values.append(v)

        # Regular hist data
        regl_hist_data = bin_histogram_data_circular(
            zip(_bin_values, _sec_values), bin_arr, bin_range, key=lambda v: v[0])

        # Plot coordinates
        regl_hist_array = WindRose._histogram_array_radial(
            bin_vecs, vec_cpt, regl_hist_data, (0, max_bar_radius), ytick_num,
            show_stack)

        # Flatten and add coordinates
        if not show_stack:
            regl_hist_array = ([v] for v in regl_hist_array)

        # Make mesh
        hist_coords = [intervals for bar in regl_hist_array for intervals in bar]
        mesh_array = [[Point2D.from_array(vec) for vec in vecs] for vecs in hist_coords]
        mesh = Mesh2D.from_face_vertices(mesh_array, purge=True)

        # Extract speed values for colors
        colors = WindRose._compute_hist_colors(regl_hist_data, regl_hist_array,
                                               stack=show_stack)

        return mesh, colors

    def __repr__(self):
        """Wind rose Collection representation."""
        return 'Wind Rose:\n\n{}\n\n{}'.format(
            self.direction_data_collection.header,
            self.speed_data_collection.header)