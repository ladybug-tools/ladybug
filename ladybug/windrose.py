# coding=utf-8
from __future__ import division

from .datacollection import HourlyContinuousCollection, HourlyDiscontinuousCollection
from .graphic import GraphicContainer
from .legend import LegendParameters, Legend
from .compass import Compass

from ladybug_geometry.geometry2d.pointvector import Point2D, Vector2D
from ladybug_geometry.geometry2d.line import LineSegment2D
from ladybug_geometry.geometry2d.polygon import Polygon2D
from ladybug_geometry.geometry2d.mesh import Mesh2D
from ladybug_geometry.geometry3d.pointvector import Point3D

from math import pi, cos, sin, ceil
import functools

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



@functools.lru_cache(maxsize=128)
def memtest(ytick_num, real_freq_max, frequency_maximum,
            zeros_per_bin, show_zeros, show_stack, _ytick_zero_inc, cx, cy, bin_vectors,
            data, wind_radius):

    max_bar_radius = 1.0
    min_bar_radius = 0.0
    zero_mesh_array, zero_color_array = [], []

    # Calculate ytick nums for the wind mesh
    #ytick_num = self.legend_parameters.segment_count  # total
    #max_bar_num = self.real_freq_max + self.zeros_per_bin
    #ytick_num_mesh = max_bar_num / self.frequency_maximum * ytick_num  # wind mesh
    max_bar_num = real_freq_max + zeros_per_bin
    ytick_num_mesh = max_bar_num / frequency_maximum * ytick_num  # wind mesh

    if show_zeros:
        # Calculate radius of zero rose

        #min_bar_radius = self.zeros_per_bin / max_bar_num * max_bar_radius
        min_bar_radius = zeros_per_bin / max_bar_num * max_bar_radius

        # Update yticks
        #zero_ytick_num_mesh = self._ytick_zero_inc
        zero_ytick_num_mesh = _ytick_zero_inc
        ytick_num_mesh -= zero_ytick_num_mesh

        # Compute the array for calm rose
        # zero_data = [[0] for _ in self.data]
        # zero_mesh_array, zero_color_array = WindRose._compute_colored_mesh_array(
        #     zero_data, self.bin_vectors, zero_ytick_num_mesh, 0, min_bar_radius,
        #     show_stack=False)
        zero_data = [[0] for _ in data]
        zero_mesh_array, zero_color_array = WindRose._compute_colored_mesh_array(
            zero_data, bin_vectors, zero_ytick_num_mesh, 0, min_bar_radius,
            show_stack=False)


    # Calculate regular mesh
    # mesh_array, color_array = WindRose._compute_colored_mesh_array(
    #     self.data, self.bin_vectors, ytick_num_mesh, min_bar_radius, max_bar_radius,
    #     self.show_stack)
    mesh_array, color_array = WindRose._compute_colored_mesh_array(
        data, bin_vectors, ytick_num_mesh, min_bar_radius, max_bar_radius,
        show_stack)

    mesh_array += zero_mesh_array
    color_array += zero_color_array

    mesh = Mesh2D.from_face_vertices(mesh_array, purge=True)
    mesh.colors = color_array

    #return mesh.scale(self._wind_radius).move(self._center_point2d)
    return mesh.scale(wind_radius).move(Point2D(cx, cy))#self._center_point2d)

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
        * angles
        * legend
        * legend_parameters
        * base_point
        * colored_mesh
        * orientation_lines
        * frequency_lines
        * all_boundary_circles
        * inner_boundary_circle
        * frequency_spacing_distance
        * frequency_maximum
        * label_point_size_factor
        * label_tick_size_factor
        * orientation_labels
        """

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
        self._angles = linspace(0, 360, number_of_directions + 1)
        self._data, self._zero_count = \
            WindRose._compute_windrose_data(self.direction_values, self.analysis_values,
                                            number_of_directions, self.angles,
                                            (0, 360))

        # Editable public properties for visualization
        self._legend = None
        self._legend_parameters = None
        self._frequency_spacing_distance = None
        self._frequency_maximum = None
        self._label_point_size_factor = None
        self._label_tick_size_factor = None
        self._show_stack = None
        self._show_zeros = None
        self._base_point = None

        # Fixed properties for visualization that only need to be computed once
        self._bin_vectors = None
        self._zeros_per_bin = None
        self._orientation_labels = None
        self._real_freq_max = None

    @property
    def base_point(self):
        """An optional Point3D used as the bottom left corner of the windrose geometry.

        Default is Point3D(0, 0, 0)).
        """
        if self._base_point is None:
            self._base_point = Point3D()
        return self._base_point

    @base_point.setter
    def base_point(self, base_point):
        """Set the base point with a Point3D object."""
        assert isinstance(base_point, type(Point3D())), 'base_point must be a Point3D. ' \
            'Got {}.'.format(type(base_point))
        self._base_point = base_point

    @property
    def show_stack(self):
        """Property to control if windrose displays stacked histogram or not.

        Default is True.
        """
        if self._show_stack is None:
            self._show_stack = True
        return self._show_stack

    @show_stack.setter
    def show_stack(self, show_stack):
        """Set the show_stack boolean.

        Args:
            show_stack: Boolean.
        """
        self._show_stack = show_stack

    @property
    def show_zeros(self):
        """Property to control if windrose displays zero valuess or not.

        Default is True.
        """
        if self._show_zeros is None:
            self._show_zeros = True
        return self._show_zeros

    @show_zeros.setter
    def show_zeros(self, show_zeros):
        """Set the show_zeros boolean.

        Args:
            show_zeros: Boolean
        """
        self._show_zeros = show_zeros

    @property
    def frequency_spacing_distance(self):
        """Distance for frequency lines.

        Default is 0.1
        """
        if self._frequency_spacing_distance is None:
            self._frequency_spacing_distance = 0.1
        return self._frequency_spacing_distance

    @frequency_spacing_distance.setter
    def frequency_spacing_distance(self, frequency_spacing_distance):
        """Set the frequency spacing distance for the windrose plot.

        Args:
            frequency_spacing_distance: Float representing frequency gap distance.
        """
        self._frequency_spacing_distance = frequency_spacing_distance

    @property
    def frequency_maximum(self):
        """Maximum frequency to represent in the windrose plot.

        Default will be the maximum number of items in current windrose data.
        """
        if self._frequency_maximum is None:
            self._frequency_maximum = self.real_freq_max
        return self._frequency_maximum

    @frequency_maximum.setter
    def frequency_maximum(self, frequency_maximum):
        """Set the frequency maximum for the windrose plot.

        Args:
            frequency_maximum: Float representing frequency maximum.
        """
        self._frequency_maximum = frequency_maximum

    @property
    def label_point_size_factor(self):
        """Get the size of the points for labels in the windrose plot.

        Default is 0.8
        """
        if self._label_point_size_factor is None:
            self._label_point_size_factor = 0.8
        return self._label_point_size_factor

    @label_point_size_factor.setter
    def label_point_size_factor(self, label_point_size_factor):
        """Set the size of the points for labels in the windrose plot."""
        self._label_point_size_factor = label_point_size_factor

    @property
    def label_tick_size_factor(self):
        """Get the size of the ticks for labels in the windrose plot.

        Default is 0.3
        """
        if self._label_tick_size_factor is None:
            self._label_tick_size_factor = 0.3
        return self._label_tick_size_factor

    @label_tick_size_factor.setter
    def label_tick_size_factor(self, label_tick_size_factor):
        """Set the size of the ticks for labels in the windrose plot."""
        self._label_tick_size_factor = label_tick_size_factor

    @property
    def legend_parameters(self):
        """The LegendParameters object for this plot.

        Default is a legend parameter with minimum and maximum values of the
        windrose analysis values. If show_stack is False, then these min and max
        will be the average of the binned values per orientation.
        The default segment count is 10.
        """
        if self._legend_parameters is None:
            # if self.show_stack:
            #     min_analysis = self.analysis_data_collection.min
            #     max_analysis = self.analysis_data_collection.max
            # else:
            #     # If not stacked histogram, ensure legend parameter range is defined
            #     # by wind mean range per orientation.
            #     wind_means = [sum(bin)/float(len(bin)) for bin in self.data
            #                   if len(bin) > 0]
            #     min_analysis = min(wind_means)
            #     max_analysis = max(wind_means)
            # segment_count = 10
            # self._legend_parameters = LegendParameters(min=min_analysis,
            #                                            max=max_analysis,
            #                                            segment_count=segment_count)
            None
        return self._legend_parameters

    @legend_parameters.setter
    def legend_parameters(self, legend_parameters):
        """Set the legend parameters for the windrose plot.

        Args:
            legend_parameters: A LegendParameters object.
        """
        legtyp = type(LegendParameters(0, 1, 10))
        assert isinstance(legend_parameters, legtyp), 'legend_parameters must be' \
            ' a LegendParameters. Got {}.'.format(type(legend_parameters))
        self._legend_parameters = legend_parameters

    @property
    def legend(self):
        """The Legend object for this plot"""
        if self._legend is None:
            self._legend = self._container._legend
        return self._legend

    @legend.setter
    def legend(self, legend):
        """Set the Legend object"""
        assert isinstance(legend, type(Legend())), 'legend must be a Legend. ' \
            'Got {}.'.format(type(legend))
        self._legend = legend

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
    def angles(self):
        """List of orientation angles used to bin analysis values."""
        return self._angles

    @property
    def bin_vectors(self):
        """Vectors for orientation intervals."""
        if self._bin_vectors is None:
            self._bin_vectors = WindRose._bin_vectors_radial(self.angles)
        return self._bin_vectors

    @property
    def zeros_per_bin(self):
        """Number of analysis values that are equal to zero, per orientation bin."""
        if self._zeros_per_bin is None:
            self._zeros_per_bin = float(self._zero_count) / (len(self.angles) - 1)
        return self._zeros_per_bin

    @property
    def real_freq_max(self):
        """The maximum frequency of the windrose data."""
        if self._real_freq_max is None:
            self._real_freq_max = max([len(d) for d in self.data])
        return self._real_freq_max

    @property
    def container(self):
        """GraphicContainer for the windrose mesh."""
        # Create the graphic container from the inputs and associated legend properties
        max_pt = Point3D(self._center_point2d.x + self._radius,
                         self._center_point2d.y + self._radius, self.base_point.z)

        return GraphicContainer(self.analysis_values, self.base_point, max_pt,
                                self.legend_parameters, self.analysis_data_collection.header.data_type,
                                self.analysis_data_collection.header.unit)

    @property
    def colored_mesh(self):
        """Get a colored Mesh2D for this graphic.
        """
        ytick_num = self.legend_parameters.segment_count  # total

        data = tuple(tuple(d) for d in self.data)

        w = memtest(
            ytick_num, self.real_freq_max, self.frequency_maximum, self.zeros_per_bin, self.show_zeros,
            self.show_stack,
            self._ytick_zero_inc, self._center_point2d.x, self._center_point2d.y,
            tuple(self.bin_vectors), data,
            self._wind_radius
        )

        #print(memtest.cache_info())
        #print(dir(memoize_colored_mesh)[::-1])

        return w

    @property
    def all_boundary_circles(self):
        """Get a list of Arc2Ds for the boundary of the plot."""
        return self._compass.all_boundary_circles

    @property
    def inner_boundary_circle(self):
        """Get an Arc2D for the inner boundary of the plot."""
        return self._compass.inner_boundary_circle

    @property
    def orientation_lines(self):
        """Orientation lines for windrose as a LineSegment2D list."""
        lines = WindRose._xtick_radial_lines(self._bin_vectors)
        return [line.scale(self._radius).move(self._center_point2d) for line in lines]

    @property
    def orientation_labels(self):
        """List of labels corresponding to the orientation angles."""
        if self._orientation_labels is None:
            self._orientation_label = self.angles
        return self._orientation_labels

    @property
    def orientation_label_points(self):
        """Get a list of label points from a list of orientation angles between 0 and 360.
        """
        return self._compass.label_points_from_angles(
            self.angles, factor=self.label_point_size_factor)

    @property
    def orientation_label_ticks(self):
        """Get a list of Linesegment2Ds from a list of orientation angles between 0 and 360."""
        return self._compass.ticks_from_angles(self.angles,
                                               factor=self.label_tick_size_factor)

    @property
    def frequency_lines(self):
        """Frequency lines for windrose as Polygon2D lists."""
        freqs = WindRose._ytick_radial_lines(self._bin_vectors,
                                             self.legend_parameters.segment_count)
        return [freq.scale(self._radius).move(self._center_point2d) for freq in freqs]

    @property
    def _center_point2d(self):
        """Compute center of windrose plot as Point2D."""
        return Point2D(self.base_point.x + self._radius,
                       self.base_point.y + self._radius)

    @property
    def _radius(self):
        """Radius of the inner boundary of the windrose plot.

        This number will be a integer multiple of the legend parameter segement count.
        """
        ytick_num = self.legend_parameters.segment_count
        if self.show_zeros:
            ytick_num += self._ytick_zero_inc
        return self.frequency_spacing_distance * ytick_num

    @property
    def _wind_radius(self):
        """Radius of the windrose mesh."""
        if self.show_zeros:
            return (self.real_freq_max + self.zeros_per_bin) / \
                (self.frequency_maximum + self.zeros_per_bin) * self._radius
        else:
            return self.real_freq_max / self.frequency_maximum * self._radius

    @property
    def _ytick_zero_inc(self):
        """Returns how much yticks increasa with zeros"""
        return ceil(self.zeros_per_bin / (self.real_freq_max + self.zeros_per_bin) *
                    self.legend_parameters.segment_count)

    @property
    def _compass(self):
        """Compass object for the windrose plot."""
        ytick_num = self.legend_parameters.segment_count
        return Compass(self._radius, self._center_point2d, north_angle=0,
                       spacing_factor=1.0/ytick_num)

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
    def _compute_colored_mesh_array(regl_hist_data, bin_vecs, ytick_num, min_radius,
                                    max_radius, show_stack):
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

        # Compute histogram array
        regl_hist_array = WindRose._histogram_array_radial(
            bin_vecs, vec_cpt, regl_hist_data, (min_radius, max_radius), ytick_num,
            show_stack)

        # Flatten and add coordinates
        if not show_stack:
            regl_hist_array = ([v] for v in regl_hist_array)

        # Make mesh
        hist_coords = [intervals for bar in regl_hist_array for intervals in bar]
        mesh_array = [[Point2D.from_array(vec) for vec in vecs] for vecs in hist_coords]

        # Extract analysis values for colors
        color_array = WindRose._compute_hist_colors(regl_hist_data, regl_hist_array,
                                                    stack=show_stack)

        return mesh_array, color_array

    def set_visualization_properties(self, legend_parameters=None, base_point=None,
                                     frequency_spacing_distance=None,
                                     frequency_maximum=None,
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

        self.base_point = self.base_point if base_point is None else base_point
        self.show_stack = self.show_stack if show_stack is None else show_stack
        self.show_zeros = self.show_zeros if show_zeros is None else show_zeros
        self.frequency_spacing_distance = self.frequency_spacing_distance if \
            frequency_spacing_distance is None else frequency_spacing_distance
        self.frequency_maximum = self.frequency_maximum if frequency_maximum is None \
            else frequency_maximum
        self.label_point_size_factor = self.label_point_size_factor if \
            label_point_size_factor is None else label_point_size_factor
        self.label_tick_size_factor = self.label_tick_size_factor if \
            label_tick_size_factor is None else label_tick_size_factor
        self.legend_parameters = self.legend_parameters if legend_parameters is None \
            else legend_parameters

    def __repr__(self):
        """Wind rose Collection representation."""
        return 'Wind Rose:\n\n{}\n\n{}'.format(
            self.direction_data_collection.header,
            self.analysis_data_collection.header)