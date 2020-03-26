# coding=utf-8
from __future__ import division

from .datacollection import HourlyContinuousCollection, HourlyDiscontinuousCollection
from .graphic import GraphicContainer
from .legend import LegendParameters
from .compass import Compass

from ladybug_geometry.geometry2d.pointvector import Point2D, Vector2D
from ladybug_geometry.geometry2d.line import LineSegment2D
from ladybug_geometry.geometry2d.polygon import Polygon2D
from ladybug_geometry.geometry2d.mesh import Mesh2D
from ladybug_geometry.geometry3d.pointvector import Point3D

from math import pi, cos, sin, ceil


def linspace(start, stop, num):
    """Return evenly spaced numbers over calculated over the interval start, stop.

    Equivalent to numpy.linspace(0, 5, 6) -> array([0., 1., 2., 3., 4., 5.])

    Args:
        start: Start interval index as integer
        num: Number of divisions as integer

    Returns:
        A list of numbers.
    """
    try:
        delta = stop - start
        return [i * (delta / (num - 1)) + start for i in range(num)]
    except ZeroDivisionError:
        return [start]


def histogram(values, bins, hist_range=None, key=None):
    """Compute the frequency histogram from a list of values.

    The data is binned inclusive of the lower bound but exclusive of the upper bound for
    intervals. For example we will lose the last number in the following dataset because
    because of exclusive upper bound:

        histogram([0, 0, 0.9, 1, 1.5, 1.99, 2, 3], (0, 1, 2, 3))
        >>> [[0, 0, 0.9], [1, 1.5, 1.99], [2]]

    Args:
        values: Set of numerical data as a list.
        bins: A monotonically increasing array of uniform-width bin edges, excluding the
            rightmost edge.
        hist_range: Optional parameter to define the lower and upper range of the
            histogram as a tuple of numbers. If not provided the range is
            ``(min(values), max(values)+1)``.
        key: Optional function parameter to define key to bin values by. If not provided
            the histogram will be binned by value item.

    Returns:
        A list of lists representing the ordered values binned by frequency.
            histogram([0, 1, 1, 2, 3], [0, 2, 3]) -> [[0, 1, 1], [2]]
    """

    if hist_range is None:
        hist_range = (min(values), max(values)+1)

    if key is None:
        key = lambda v: v

    vals = sorted(values, key=key)

    bin_bound_num = len(bins)

    # Init histogram bins
    hist = [[] for i in range(bin_bound_num - 1)]
    bin_index = 0
    for val in vals:
        k = key(val)
        # Ignore values out of range
        if k < hist_range[0] or k >= hist_range[1]:
            continue

        # This loop will iterate through the bin upper bounds.
        # If the value is within the bounds, the lower bound
        # of the bin_index is updated, and the loop is broken
        for i in range(bin_index, bin_bound_num - 1):
            if k < bins[i + 1]:
                hist[i].append(val)
                bin_index = i
                break

    return hist


def histogram_circular(values, bins, hist_range=None, key=None):
    """Compute the frequency histogram from a list of circular values.

    Circular values refers to a set of values where there is no distinction between
    values at the lower or upper end of the range, for example angles in a circle, or
    time.

    Example:
        histogram_circular([358, 359, 0, 1, 2, 3], (358, 0, 3))
        >>> [[358, 359], [0, 1, 2]]

    The data is binned inclusive of the lower bound but exclusive of the upper bound for
    intervals. For example we will lose the last number in the following dataset because
    because of exclusive upper bound:

        histogram([0, 0, 0.9, 1, 1.5, 1.99, 2, 3], (0, 1, 2, 3))
        >>> [[0, 0, 0.9], [1, 1.5, 1.99], [2]]

    Args:
        values: Set of numerical data as a list.
        bins: An array of uniform-width bin edges, excluding the rightmost edge. These
            values do not have to be monotonically increasing.
        hist_range: Optional parameter to define the lower and upper range of the
            histogram as a tuple of numbers. If not provided the range is
            ``(a.min(), a.max()+1)``.
        key: Optional function parameter to define key to bin values by. If not provided
            the histogram will be binned by value item.

    Returns:
        A list of lists representing the ordered values binned by frequency.
            histogram([0, 1, 1, 2, 3], [0, 2, 3]) -> [[0, 1, 1], [2]]
    """

    if hist_range is None:
        hist_range = (min(values), max(values)+1)

    if key is None:
        key = lambda v: v

    vals = sorted(values, key=key)

    bin_bound_num = len(bins) - 1

    # Init histogram bins
    hist = [[] for i in range(bin_bound_num)]
    for val in vals:
        k = key(val)

        # Ignore values out of range
        if k < hist_range[0] or k >= hist_range[1]:
            continue

        # This loop will iterate through the bin upper bounds.
        # If the value is within the bounds, the loop is broken.
        # Since values at the end of the list can still be binned
        # into the earlier histogram bars for circular
        # data, we don't update the bin_index.
        for i in range(bin_bound_num):
            if bins[i] > bins[i + 1]:
                # If the interval starts data from the end of the list,
                # split the conditional checks into two to check two
                # intervals.
                interval1 = (k < hist_range[1] and k >= bins[i])
                interval2 = (k < bins[i + 1] and k >= hist_range[0])
                if interval1 or interval2:
                    hist[i].append(val)
                    break
            else:
                if k < bins[i + 1]:
                    hist[i].append(val)
                    break

    return hist


class WindRose(object):
    """Module for calculation and visualization of wind data collection by orientation.

    Args:

        direction_data_collection: A HourlyContinuousCollection or
            HourlyDiscontinuousCollection of wind directions which will be used to
            generate the windrose.
        direction_data_collection: A HourlyContinuousCollection or
            HourlyDiscontinuousCollection of wind speeds which will be used to
            generate the windrose.
        number_of_directions: The number of orientations to divided the wind rose
            directions.

    Properties:
        * direction_data_collection
        * analysis_data_collection
        * direction_values
        * analysis_values
        * analysis_period
        * data
        * zero_count
        * bin_angles
        * legend
        * legend_parameters
        * base_point
        * radius
        * colored_mesh
        * orientation_lines
        * frequency_lines
        * all_boundary_circles
        * inner_boundary_circle
        * frequency_spacing_distance
        * frequency_maximum
        * label_point_size_factor
        * label_tick_size_factor
        """

    _VIZ_ASSERTION_ERROR = 'Windrose visualization properties have not been set. ' \
        'Use the "set_visualization_properties" method to set them before ' \
        'calling this property.'

    __slots__ = ('_direction_data_collection', '_analysis_data_collection',
                 '_number_of_directions', '_bin_angles', '_data',
                 '_zero_count', 'legend', 'legend_parameters', '_radius',
                 'frequency_spacing_distance', 'label_point_size_factor',
                 'label_tick_size_factor', 'show_stack', 'show_zeros', '_viz_set',
                 '_base_point', '_colored_mesh', '_bin_vectors',
                 '_all_boundary_circles', '_inner_boundary_circle',
                 '_orientation_lines', '_frequency_lines', '_compass', '_container',
                 'frequency_maximum', '_wind_radius')

    def __init__(self, direction_data_collection, analysis_data_collection,
                 number_of_directions=8):

        """Initialize windrose plot."""
        # Check the input objects
        acceptable_colls = (HourlyContinuousCollection, HourlyDiscontinuousCollection)
        assert isinstance(direction_data_collection, acceptable_colls), 'Windrose ' \
            'direction_data_collection must be a HourlyContinuousCollection or ' \
            'HourlyDiscontinuousCollection. Got {}.'.format(
                type(direction_data_collection))
        assert isinstance(analysis_data_collection, acceptable_colls), 'Windrose ' \
            'analysis_data_collection must be a HourlyContinuousCollection or ' \
            'HourlyDiscontinuousCollection. Got {}.'.format(
                type(analysis_data_collection))

        # Ensure the analysis period of the data collection has been validated
        if not direction_data_collection.validated_a_period:
            direction_data_collection = \
                direction_data_collection.validate_analysis_period()
        if not direction_data_collection.validated_a_period:
            analysis_data_collection = \
                analysis_data_collection.validate_analysis_period()

        # Assign the inputs as read-only properties of this data collection
        self._direction_data_collection = direction_data_collection.to_immutable()
        self._analysis_data_collection = analysis_data_collection.to_immutable()
        self._number_of_directions = number_of_directions

        # Compute the windrose data and associated read-only properties
        self._bin_angles = linspace(0, 360, number_of_directions + 1)
        self._data, self._zero_count = \
            WindRose._compute_windrose_data(self.direction_values, self.analysis_values,
                                            number_of_directions, self.bin_angles,
                                            (0, 360))

        # Editable properties computed for visualization
        self.legend = None
        self.legend_parameters = None
        self.frequency_spacing_distance = None
        self.frequency_maximum = None
        self.label_point_size_factor = None
        self.label_tick_size_factor = None
        self.show_stack = None
        self.show_zeros = None

        # Read only properties computed for visualization
        self._viz_set = False
        self._base_point = None
        self._radius = None
        self._colored_mesh = None
        self._all_boundary_circles = None
        self._inner_boundary_circle = None
        self._orientation_lines = None
        self._frequency_lines = None
        self._compass = None
        self._container = None
        self._bin_vectors = WindRose._bin_vectors_radial(self.bin_angles)

    @property
    def direction_data_collection(self):
        """The direction data collection assigned to this windrose plot."""
        return self._direction_data_collection

    @property
    def analysis_data_collection(self):
        """The analysis data collection assigned to this windrose plot."""
        return self._analysis_data_collection

    @property
    def analysis_values(self):
        """ The hourly wind analysis values to bin by direction (i.e wind speed)."""
        return self._analysis_data_collection.values

    @property
    def direction_values(self):
        """The direction data values in this windrose plot."""
        return self._direction_data_collection.values

    @property
    def data(self):
        """A histogram of wind analysis values binned by the wind directions."""
        return self._data

    @property
    def zero_count(self):
        """Number of wind analysis values equal to zero."""
        return self._zero_count

    @property
    def analysis_period(self):
        """The AnalysisPeriod assigned to the hourly plot's data collection."""
        return self._analysis_data_collection.header.analysis_period

    @property
    def bin_angles(self):
        """List of orientation angles used to bin analysis values."""
        return self._bin_angles

    @property
    def base_point(self):
        """An optional Point3D used as the bottom left corner of the windrose geometry.

        Default is (0, 0, 0))."""
        return self._base_point

    @base_point.setter
    def base_point(self, base_point):
        """Set the base point with a Point3D object."""
        assert isinstance(base_point, type(Point3D())), 'base_point must be a Point3D. ' \
            'Got {}.'.format(type(base_point))
        self._base_point = base_point

    @property
    def _center_point2d(self):
        """Compute center of windrose plot as Point2D."""
        return Point2D(self.base_point.x + self._radius, self.base_point.y + self._radius)

    @property
    def colored_mesh(self):
        """Get a colored Mesh2D for this graphic.
        """
        assert self._viz_set, self._VIZ_ASSERTION_ERROR
        if self._colored_mesh is None:
            ytick_num = self.legend_parameters.segment_count
            if self.show_zeros:
                mesh = WindRose._compute_colored_mesh_zero(
                    self.data, self.zero_count, self._bin_vectors, ytick_num,
                    self.show_stack)
            else:
                mesh = WindRose._compute_colored_mesh_regl(
                    self.data, self._bin_vectors, ytick_num, self.show_stack)

            self._colored_mesh = mesh.scale(self._wind_radius).move(self._center_point2d)
        return self._colored_mesh

    @colored_mesh.setter
    def colored_mesh(self, colored_mesh):
        """Set the colored_mesh for this graphic"""
        self._colored_mesh = colored_mesh

    @property
    def all_boundary_circles(self):
        """Get a list of Arc2Ds for the boundary of the plot."""
        assert self._viz_set, self._VIZ_ASSERTION_ERROR
        if self._all_boundary_circles is None:
            self._all_boundary_circles = self._compass.all_boundary_circles
        return self._all_boundary_circles

    @property
    def inner_boundary_circle(self):
        """Get an Arc2D for the inner boundary of the plot."""
        assert self._viz_set, self._VIZ_ASSERTION_ERROR
        if self._inner_boundary_circle is None:
            self._inner_boundary_circle = self._compass.inner_boundary_circle
        return self._border

    @property
    def orientation_lines(self):
        """Orientation lines for windrose as a LineSegment2D list."""
        assert self._viz_set, self._VIZ_ASSERTION_ERROR
        if self._orientation_lines is None:
            lines = WindRose._xtick_radial_lines(self._bin_vectors)
            self._orientation_lines = [line.scale(self._radius).move(self._center_point2d)
                                       for line in lines]
        return self._orientation_lines

    @property
    def orientation_labels(self):
        """List of labels corresponding to the orientation angles."""
        assert self._viz_set, self._VIZ_ASSERTION_ERROR
        if self._orientation_labels is None:
            self._orientation_label = self.bin_angles
        return self._orietnation_labels

    @property
    def orientation_label_points(self):
        """Get a list of label points from a list of orientation angles between 0 and 360.
        """
        assert self._viz_set, self._VIZ_ASSERTION_ERROR
        return self._compass.label_points_from_angles(
            self.bin_angles, factor=self.label_point_size_factor)

    @property
    def orientation_label_ticks(self):
        """Get a list of Linesegment2Ds from a list of orientation angles between 0 and 360."""
        assert self._viz_set, self._VIZ_ASSERTION_ERROR
        return self._compass.ticks_from_angles(self.bin_angles,
                                               factor=self.label_tick_size_factor)

    @property
    def frequency_lines(self):
        """Frequency lines for windrose as Polygon2D lists."""
        assert self._viz_set, self._VIZ_ASSERTION_ERROR
        if self._frequency_lines is None:
            freqs = WindRose._ytick_radial_lines(self._bin_vectors,
                                                 self.legend_parameters.segment_count)
            self._frequency_lines = [freq.scale(self._radius).move(self._center_point2d)
                                     for freq in freqs]
        return self._frequency_lines

    @staticmethod
    def _compute_bar_stack_vecs(base_vec_show_stack, vec1, vec2, curr_bar_radius,
                                min_bar_radius, max_bar_radius, ytick_num,
                                ytick_dist):
        """Compute the bar geometry arrays for stacked histogram bars.

        Args:
            base_vec_show_stack: list of points for bottem edge of the histogram bar.
            vec1: first bin edge as a vector array.
            vec2: second bin edge as a vector array
            curr_bar_radius: length of the histogram bar.
            min_bar_radius: lenght from the center of the windrose to the start of the
                histogram bar.
            max_bar_radius: radius of the windrose.
            ytick_num: Number of intervals in the current stacked histogram bar.
            ytick_dist: Length of stack interval.
        Returns:
            List of vector arrays representing a stacked histogram bar.
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
            bar_interval_vecs.append(base_vec_show_stack +
                                     [(vec1[0] * ytick_dist_inc,
                                       vec1[1] * ytick_dist_inc),
                                      (vec2[0] * ytick_dist_inc,
                                       vec2[1] * ytick_dist_inc)])
            base_vec_show_stack = list(reversed(bar_interval_vecs[-1][-2:]))

        return bar_interval_vecs

    @staticmethod
    def _compute_hist_colors(hist_data, hist_coords, stack):
        """
        Compute the colors for the mesh corresponding to mesh faces.

        Args:
            hist_data: Histogram of values as list.
            hist_coords: Geometry of histogram as list of vector arrays.
            stack: Boolean indicating if stacked histogram.

        Returns:
            List of histogram values to translate into colors.
        """

        if stack:
            colors = []
            for data, vecs in zip(hist_data, hist_coords):
                bar_data_num = len(vecs)
                bar_data_val = data

                if bar_data_val:
                    color_arr = linspace(min(bar_data_val), max(bar_data_val),
                                         bar_data_num)
                    if not color_arr:
                        color_arr = [sum(bar_data_val) / len(bar_data_val)]
                    colors.extend(color_arr)
        else:
            colors = [sum(hist)/len(hist)
                      if len(hist) > 0 else 0 for hist in hist_data]

        return colors

    @staticmethod
    def _bin_vectors_radial(bin_arr):
        """Compute the radial coordinates for the histogram bins of values.

        This component will re-orient angles so that 0 degrees starts at the top,
        and increases in a clockwise direction.

        Args:
            bin_arr: List of angles for histogram bar edges in degrees.

        Returns:
            List of vector arrays representing radial histogram.
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
        """X-axis lines for radial histogram as List of lineSegment2Ds.

        Args:
            bin_vecs: Array of histogram bin edge vectors.

        Returns:
            List of LineSegment2Ds.
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
        """Y-axis lines for radial histogram as List of lineSegment2Ds.

        Args:
            bin_vecs: Array of histogram bin edge vectors.
            ytick_num: Number of Y-axis intervals.
        Returns:
            List of LineSegment2Ds.
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
        """Coordinates for a radial histogram as a vector array.

        Args:
            bin_vecs: Array of histogram bin edge vectors.
            vec_cpt: Centerpoint of histogram as tuple.
            hist: Histogram data as a list of lists.
            radius_arr: Minimum and maximum distance for bar radius.
            ytick_num: Number of Y-axis intervals.
            show_stack: Boolean indicating if stacked histogram.
        Returns:
            List of histogram bars as array of vector coordinates.
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

            # Compute array for bottom of the bar
            if min_bar_radius > 0.0:
                base = [(vec2[0] * min_bar_radius, vec2[1] * min_bar_radius),
                        (vec1[0] * min_bar_radius, vec1[1] * min_bar_radius)]
            else:
                base = [vec_cpt]

            if show_stack:
                bar_vecs = WindRose._compute_bar_stack_vecs(
                    base, vec1, vec2, curr_bar_radius, min_bar_radius, max_bar_radius,
                    ytick_num, ytick_dist)
                hist_coords.append(bar_vecs)
            else:
                bar_vecs = base + [(vec1[0] * (curr_bar_radius + min_bar_radius),
                                    vec1[1] * (curr_bar_radius + min_bar_radius)),
                                   (vec2[0] * (curr_bar_radius + min_bar_radius),
                                    vec2[1] * (curr_bar_radius + min_bar_radius))]
                hist_coords.append(bar_vecs)

        return hist_coords

    @staticmethod
    def _compute_windrose_data(direction_values, analysis_values, bin_intervals,
                               bin_array, bin_range):
        """
        Computes the histogram for the windrose.

        Args:
            direction_values: Hourly direction values to bin analysis data by.
            analysis_values: Hourly analysis values.
            bin_intervals: Number of bins for the histogram.
            bin_array: Bin edges as list of direction values.
            bin_range: Maximum and minimum range for histogram.

        Returns:
            The histogram, a proxy histogram to represent zero values, and the
                number of zeros in the analysis values, as a tuple.
        """
        # Filter out zero values
        _direction_values = []
        _analysis_values = []
        for d, v in zip(direction_values, analysis_values):
            if v > 1e-10:
                _direction_values.append(d)
                _analysis_values.append(v)

        # Calculate zero rose properties
        zero_count = (len(analysis_values) - len(_analysis_values))

        # Regular hist data
        data = histogram_circular(
            zip(_direction_values, _analysis_values), bin_array, bin_range,
            key=lambda v: v[0])

        # Filter out the direction values
        data = [[val[1] for val in bin] for bin in data]

        return data, zero_count

    @staticmethod
    def _compute_colored_mesh_zero(regl_hist_data, zero_count, bin_vecs, ytick_num,
                                   show_stack):
        """Compute a colored mesh from this object's histogram data.

        Args:
            regl_hist_data: Histogram of analysis values greater then zero as a list of
                lists.
            zero_count: The number of zero analysis values.
            bin_vecs: Array of histogram bin edge vectors.
            ytick_num: Number of Y-axis intervals.
            show_stack: Boolean indicating if stacked histogram.
        Returns:
            A colored Mesh2D.
        """

        # Default rose is a unit circle centered at origin. We can scale and translate
        # the resulting mesh.
        vec_cpt = (0, 0)
        max_bar_radius = 1.0
        zeros_per_bin = float(zero_count) / len(regl_hist_data)

        # Calculate radius of zero rose
        max_bar_num = max([len(bar) for bar in regl_hist_data]) + zeros_per_bin
        zero_rose_radius = zeros_per_bin / max_bar_num * max_bar_radius

        # Compute the array for calm rose
        zero_hist_data = [[0] for _ in regl_hist_data]
        zero_hist_coords = WindRose._histogram_array_radial(
            bin_vecs, vec_cpt, zero_hist_data, (0.0, zero_rose_radius), ytick_num,
            show_stack=False)

        # Compute the array for the regular rose
        regl_hist_array = WindRose._histogram_array_radial(
            bin_vecs, vec_cpt, regl_hist_data, (zero_rose_radius, max_bar_radius),
            ytick_num, show_stack=show_stack)

        # Flatten and add coordinates
        zero_hist_coords = ([v] for v in zero_hist_coords)
        if not show_stack:
            regl_hist_array = ([v] for v in regl_hist_array)

        # Make mesh
        hist_coords = [intervals for bar in zero_hist_coords for intervals in bar]
        hist_coords += [intervals for bar in regl_hist_array for intervals in bar]

        # Make the mesh
        mesh_array = [[Point2D.from_array(vec) for vec in vecs] for vecs in hist_coords]
        mesh = Mesh2D.from_face_vertices(mesh_array, purge=True)

        # Extract analysis values for colors
        colors = [0 for i in range(len(zero_hist_data))]
        colors += WindRose._compute_hist_colors(regl_hist_data, regl_hist_array,
                                                stack=show_stack)

        # Assign colors
        mesh.colors = colors

        return mesh

    @staticmethod
    def _compute_colored_mesh_regl(regl_hist_data, bin_vecs, ytick_num,
                                   show_stack):
        """Compute a colored mesh from this object's historam.

        Args:
            regl_hist_data: Histogram of analysis values greater then zero as a list of
                lists.
            bin_vecs: Array of histogram bin edge vectors.
            ytick_num: Number of Y-axis intervals.
            show_stack: Boolean indicating if stacked histogram.
        Returns:
            A colored Mesh2D.
        """

        # Default rose is a unit circle centered at origin. We can scale and translate
        # the resulting mesh.
        vec_cpt = (0, 0)
        max_bar_radius = 1.0

        # Compute histogram array
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

        # Extract analysis values for colors
        mesh.colors = WindRose._compute_hist_colors(regl_hist_data, regl_hist_array,
                                                    stack=show_stack)

        return mesh

    def set_visualization_properties(self, legend_parameters=None, base_point=None,
                                     frequency_spacing_distance=None, frequency_maximum=None,
                                     label_point_size_factor=None,
                                     label_tick_size_factor=None, show_stack=None,
                                     show_zeros=None):
        """Sets visualzation properties for this object.

        This method will override visualization properties that have already been set,
        if the argument is passed. If the properties are not already set, and no argument
        is passed, default values will be used.

        Args:
            legend_parameters: A LegendParameters object.
            base_point: A Point3D representing the bottom-left corner of the
                visualization.
            frequency_spacing_distance: Spacing distance for frequency grid as float
                between 0 and 1.
            frequency_maximum: Maximum frequency of analysis values.
            label_point_size_factor: Size factor for orientation label points as float
                between 0 and 1.
            label_tick_size_factor: Size factor for orientation label ticks as float
                between 0 and 1.
            show_stack: Boolean indicating if the analysis values will be stacked.
            show_zeros: Boolean indicating if the zero values will be represented in the
                plot.
        """
        real_freq_max = max([len(d) for d in self.data])
        scale_freq_max = True

        if base_point is None:
            base_point = Point3D() if self.base_point is None else self.base_point
        self.base_point = base_point

        if show_stack is None:
            show_stack = True if self.show_stack is None else self.show_stack
        self.show_stack = show_stack

        if show_zeros is None:
            show_zeros = True if self.show_zeros is None else self.show_zeros
        self.show_zeros = show_zeros

        if frequency_spacing_distance is None:
            frequency_spacing_distance = 0.1 \
                if self.frequency_spacing_distance is None \
                else self.frequency_spacing_distance
        self.frequency_spacing_distance = frequency_spacing_distance

        if (frequency_maximum is not None) or (self.frequency_maximum is not None):
            scale_freq_max = False
        if frequency_maximum is None:
            frequency_maximum = real_freq_max \
                if self.frequency_maximum is None else self.frequency_maximum
        self.frequency_maximum = frequency_maximum

        if label_point_size_factor is None:
            label_point_size_factor = 0.8 \
                if self.label_point_size_factor is None else self.label_point_size_factor
        self.label_point_size_factor = label_point_size_factor

        if label_tick_size_factor is None:
            label_tick_size_factor = 0.3 \
                if self.label_tick_size_factor is None else self.label_tick_size_factor
        self.label_tick_size_factor = label_tick_size_factor

        if legend_parameters is None:
            if self.legend_parameters is None:
                if show_stack:
                    min_analysis = self.analysis_data_collection.min
                    max_analysis = self.analysis_data_collection.max
                else:
                    # If not stacked histogram, ensure legend parameter range is defined
                    # by wind mean range per orientation.
                    wind_means = [sum(bin)/float(len(bin)) for bin in self.data
                                  if len(bin) > 0]
                    min_analysis = min(wind_means)
                    max_analysis = max(wind_means)
                segment_count = 10
                legend_parameters = LegendParameters(min=min_analysis, max=max_analysis,
                                                     segment_count=segment_count)
        self.legend_parameters = legend_parameters

        # Update viz paramters if showing calm rose
        if self.show_zeros:
            zeros_per_bin = float(self._zero_count) / (len(self.bin_angles) - 1)
            real_freq_max += zeros_per_bin

            if scale_freq_max:
                self.frequency_maximum += zeros_per_bin
                self.legend_parameters.segment_count += \
                    ceil(zeros_per_bin / self.frequency_maximum)

        # Calculate radius from frequencing spacing
        ytick_num = self.legend_parameters.segment_count
        self._radius = self.frequency_spacing_distance * ytick_num
        self._wind_radius = (real_freq_max / self.frequency_maximum) * self._radius

        # Create compass object
        self._compass = Compass(self._radius, self._center_point2d, north_angle=0,
                                spacing_factor=1.0/ytick_num)

        # Create the graphic container from the inputs and associated legend properties
        max_pt = Point3D(self._center_point2d.x + self._radius,
                         self._center_point2d.y + self._radius, self.base_point.z)

        self._container = GraphicContainer(
            self.analysis_values, self.base_point, max_pt,
            self.legend_parameters, self.analysis_data_collection.header.data_type,
            self.analysis_data_collection.header.unit)
        self.legend = self._container._legend

        self._viz_set = True

    def __repr__(self):
        """Wind rose Collection representation."""
        return 'Wind Rose:\n\n{}\n\n{}'.format(
            self.direction_data_collection.header,
            self.analysis_data_collection.header)