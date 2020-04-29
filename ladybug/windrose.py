# coding=utf-8
from __future__ import division

from .datacollection import HourlyContinuousCollection, HourlyDiscontinuousCollection
from .graphic import GraphicContainer
from .legend import LegendParameters
from .compass import Compass

from ladybug_geometry.geometry2d.pointvector import Point2D
from ladybug_geometry.geometry2d.line import LineSegment2D
from ladybug_geometry.geometry2d.polygon import Polygon2D
from ladybug_geometry.geometry2d.mesh import Mesh2D
from ladybug_geometry.geometry3d.pointvector import Point3D

import math

# Simplify method names
linspace = HourlyContinuousCollection.linspace
histogram = HourlyContinuousCollection.histogram
histogram_circular = HourlyContinuousCollection.histogram_circular


class WindRose(object):
    """Module for calculation and visualization of wind data collection by orientation.

    Args:

        direction_data_collection: A HourlyContinuousCollection or
            HourlyDiscontinuousCollection of wind directions which will be used to
            generate the "bin" intervals for the windrose.
        analysis_data_collection: A HourlyContinuousCollection or
            HourlyDiscontinuousCollection of wind values, corresponding to the wind
            directions, which is "binned" by the calculated direction intervals.
        number_of_directions: The number of orientations to divided the wind rose
            directions.

    Properties:
        * direction_data_collection
        * analysis_data_collection
        * direction_values
        * analysis_values
        * analysis_period
        * histogram_data
        * zero_count
        * angles
        * legend
        * legend_parameters
        * base_point
        * radius
        * wind_radius
        * colored_mesh
        * orientation_lines
        * frequency_lines
        * frequency_spacing_distance
        * frequency_maximum
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
        assert direction_data_collection.is_collection_aligned(
            analysis_data_collection), 'Windrose direction_data_collection must be' \
            'aligned with analysis_data_collection. The provided values are not aligned.'

        # Ensure the analysis period of the data collection has been validated
        if not direction_data_collection.validated_a_period:
            direction_data_collection = \
                direction_data_collection.validate_analysis_period()
        if not analysis_data_collection.validated_a_period:
            analysis_data_collection = \
                analysis_data_collection.validate_analysis_period()

        # Assign the inputs as read-only properties of this data collection
        self._direction_data_collection = direction_data_collection.to_immutable()
        self._analysis_data_collection = analysis_data_collection.to_immutable()
        self._number_of_directions = int(number_of_directions)

        # Compute the windrose data and associated read-only properties
        self._angles = WindRose._compute_angles(number_of_directions)
        self._histogram_data, self._zero_count = \
            self._compute_windrose_data(self.direction_values, self.analysis_values,
                                        number_of_directions, self.angles, (0, 360))

        # Editable public properties for visualization
        self._legend_parameters = None
        self._frequency_spacing_distance = None
        self._frequency_maximum = None
        self._show_stack = True
        self._show_zeros = True
        self._base_point = Point2D()
        self._compass = None

        # Fixed properties that only need to be computed once
        self._bin_vectors = None
        self._zeros_per_bin = None
        self._real_freq_max = None
        self._prevailing_direction = None
        self._container = None

    @property
    def base_point(self):
        """Get or set a Point2D used as the center point of the windrose geometry.

        (Default: Point3D(0, 0, 0)).
        """
        return self._base_point

    @base_point.setter
    def base_point(self, base_point):
        assert isinstance(base_point, type(Point2D())), 'base_point must be a Point2D. '\
            'Got {}.'.format(type(base_point))
        self._base_point = base_point

    @property
    def show_stack(self):
        """Get or set property to control if windrose displays stacked histogram or not.

        (Default: True).
        """
        return self._show_stack

    @show_stack.setter
    def show_stack(self, show_stack):
        self._show_stack = bool(show_stack)

    @property
    def show_zeros(self):
        """Get or set property to control if windrose displays zero values or not.

        (Default: True).
        """
        return self._show_zeros

    @show_zeros.setter
    def show_zeros(self, show_zeros):
        self._show_zeros = bool(show_zeros)

    @property
    def frequency_spacing_distance(self):
        """Get or set distance for frequency lines.

        (Default: autocalculated from legend_parameters to generate radius of 1.0)
        """
        if self._frequency_spacing_distance is None:
            self._frequency_spacing_distance = 1./self.legend_parameters.segment_count
        return self._frequency_spacing_distance

    @frequency_spacing_distance.setter
    def frequency_spacing_distance(self, frequency_spacing_distance):
        f = frequency_spacing_distance
        assert f > 0.0 and isinstance(f, (float, int)), 'frequency_spacing_distance' \
            'should be a number greater then 0. Got {}.'.format(f)
        self._compass = None
        self._container = None
        self._frequency_spacing_distance = frequency_spacing_distance

    @property
    def frequency_maximum(self):
        """Get or set maximum frequency to represent in the windrose plot.

        (Default: maximum number of items in current windrose data).
        """
        if self._frequency_maximum is None:
            self._frequency_maximum = self.real_freq_max
        return self._frequency_maximum

    @frequency_maximum.setter
    def frequency_maximum(self, frequency_maximum):
        self._compass = None
        self._container = None
        self._frequency_maximum = frequency_maximum

    @property
    def legend_parameters(self):
        """Get or set the LegendParameters object for this plot.

        Default segment count is 10.
        """
        if self._legend_parameters is None:
            self._legend_parameters = LegendParameters(segment_count=10)
        return self._legend_parameters

    @legend_parameters.setter
    def legend_parameters(self, legend_parameters):
        assert isinstance(legend_parameters, LegendParameters), 'legend_parameters' \
            ' must be a LegendParameters. Got {}.'.format(type(legend_parameters))

        # This will mutate the legend_parameters in the windrose Legend object.
        self._compass = None
        self._container = None
        self._legend_parameters = legend_parameters

    @property
    def legend(self):
        """Get the Legend object for this plot"""
        return self.container.legend

    @property
    def direction_data_collection(self):
        """Get the direction data collection assigned to this windrose plot."""
        return self._direction_data_collection

    @property
    def analysis_data_collection(self):
        """Get the analysis data collection assigned to this windrose plot."""
        return self._analysis_data_collection

    @property
    def analysis_values(self):
        """Get the hourly wind analysis values to bin by direction (i.e wind speed)."""
        return self._analysis_data_collection.values

    @property
    def direction_values(self):
        """Get the direction data values in this windrose plot."""
        return self._direction_data_collection.values

    @property
    def histogram_data(self):
        """Get a histogram of wind analysis values binned by the wind directions."""
        return self._histogram_data

    @property
    def prevailing_direction(self):
        """Get the predominant direction of the wind values.

        In case of ties, this property will return the first direction value in the
        ordered direction values.
        """
        if self._prevailing_direction is None:
            dirvals = sorted(self.direction_values)
            self._prevailing_direction = dirvals[dirvals.index(max(dirvals))]
        return self._prevailing_direction

    @property
    def zero_count(self):
        """Get the number of wind analysis values equal to zero."""
        return self._zero_count

    @property
    def analysis_period(self):
        """Get the AnalysisPeriod assigned to the hourly plot's data collection."""
        return self._analysis_data_collection.header.analysis_period

    @property
    def angles(self):
        """Get a list of orientation angles used to bin analysis values."""
        return self._angles

    @property
    def bin_vectors(self):
        """Get vectors for orientation intervals."""
        if self._bin_vectors is None:
            self._bin_vectors = WindRose._bin_vectors_radial(self.angles)
        return self._bin_vectors

    @property
    def zeros_per_bin(self):
        """Get the number of analysis values that are equal to zero, per orientation bin."""
        if self._zeros_per_bin is None:
            self._zeros_per_bin = float(self._zero_count) / (len(self.angles) - 1)
        return self._zeros_per_bin

    @property
    def real_freq_max(self):
        """The maximum frequency of the windrose data."""
        if self._real_freq_max is None:
            self._real_freq_max = max([len(d) for d in self.histogram_data])
        return self._real_freq_max

    @property
    def container(self):
        """GraphicContainer for the windrose mesh.

        Since the setable properties of basepoint, frequency_spacing_distance, and
        legend_parameters all influence the initiation of this object, this property
        is to None if any of those properties are edited by the user.
        """
        if self._container is None:
            if self.show_stack:
                stacked_values = WindRose._histogram_data_stacked(
                    self.histogram_data, self.legend_parameters.segment_count)
                values = [val for vals in stacked_values for val in vals]
            else:
                values = [sum(d) / len(d) for d in self.histogram_data if len(d) > 0]

            # Create the graphic container from the inputs and associated legend
            # properties
            max_pt = Point3D(self.base_point.x + self.radius,
                             self.base_point.y + self.radius, 0)
            base_point3d = Point3D(self.base_point.x, self.base_point.y, 0)

            self._container = GraphicContainer(
                values, base_point3d, max_pt, self.legend_parameters,
                self.analysis_data_collection.header.data_type,
                self.analysis_data_collection.header.unit)
        return self._container

    @property
    def colored_mesh(self):
        """Get a colored Mesh2D for this graphic.
        """
        max_bar_radius = 1.0
        min_bar_radius = 0.0
        zero_mesh_array, zero_color_array = [], []

        # Calculate ytick nums for the wind mesh
        ytick_num = self.legend.legend_parameters.segment_count  # total
        max_bar_num = self.real_freq_max
        ytick_num_mesh = ytick_num  # default

        if self.show_zeros:
            # Calculate radius of zero rose

            max_bar_num += self.zeros_per_bin
            min_bar_radius = self.zeros_per_bin / max_bar_num * max_bar_radius
            ytick_num_mesh = max_bar_num / self.frequency_maximum * ytick_num

            # Update yticks
            zero_ytick_num_mesh = self._ytick_zero_inc()
            ytick_num_mesh -= zero_ytick_num_mesh

            # Compute the array for calm rose
            zero_data = [[0] for _ in self.histogram_data]
            zero_data_stacked = [[0] for _ in self.histogram_data]
            zero_mesh_array, zero_color_array = WindRose._compute_colored_mesh_array(
                zero_data, zero_data_stacked, self.bin_vectors, zero_ytick_num_mesh,
                0, min_bar_radius, show_stack=False)

        # Calculate regular mesh
        if self.show_stack:
            histogram_data_stacked = WindRose._histogram_data_stacked(
                self.histogram_data, ytick_num)
        else:
            histogram_data_stacked = [[sum(h) / len(h)]  if len(h) > 0 else [0]
                                      for h in self.histogram_data]
        mesh_array, color_array = WindRose._compute_colored_mesh_array(
            self.histogram_data, histogram_data_stacked, self.bin_vectors,
            ytick_num_mesh, min_bar_radius, max_bar_radius, self.show_stack)

        mesh_array += zero_mesh_array
        color_array += zero_color_array

        mesh = Mesh2D.from_face_vertices(mesh_array, purge=True)
        mesh.colors = color_array

        return mesh.scale(self.wind_radius).move(self.base_point)

    @property
    def orientation_lines(self):
        """Orientation lines for windrose as a LineSegment2D list."""
        lines = WindRose._xtick_radial_lines(self._bin_vectors)
        return [line.scale(self.radius).move(self.base_point) for line in lines]

    @property
    def frequency_lines(self):
        """Get the frequency lines for windrose as Polygon2D lists."""
        freqs = WindRose._ytick_radial_lines(self._bin_vectors,
                                             self.legend_parameters.segment_count)
        return [freq.scale(self.radius).move(self.base_point) for freq in freqs]

    @property
    def radius(self):
        """Get the radius of the inner boundary of the windrose plot.

        This number will be a integer multiple of the legend parameter segment count.
        """
        ytick_num = self.legend_parameters.segment_count
        if self.show_zeros:
            ytick_num += self._ytick_zero_inc()
        return self.frequency_spacing_distance * ytick_num

    @property
    def wind_radius(self):
        """Get the radius of the windrose mesh."""
        if self.show_zeros:
            return (self.real_freq_max + self.zeros_per_bin) / \
                (self.frequency_maximum + self.zeros_per_bin) * self.radius
        else:
            return self.real_freq_max / self.frequency_maximum * self.radius

    @property
    def compass(self):
        """Get the compass object for the windrose plot.

        Since the setable properties of basepoint, frequency_spacing_distance, and
        legend_parameters all influence the initiation of this object, this property
        is to None if any of those properties are edited by the user.
        """
        if self._compass is None:
            ytick_num = self.legend_parameters.segment_count
            return Compass(self.radius, self.base_point, north_angle=0,
                           spacing_factor=1.0/ytick_num)
        return self._compass

    @staticmethod
    def _compute_bar_stack_vecs(base_vec_show_stack, vec1, vec2, curr_bar_radius,
                                min_bar_radius, ytick_curr_num, ytick_dist):
        """Compute the bar geometry arrays for stacked histogram bars.

        Args:
            base_vec_show_stack: list of points for bottem edge of the histogram bar.
            vec1: first bin edge as a vector array.
            vec2: second bin edge as a vector array
            curr_bar_radius: length of the histogram bar.
            min_bar_radius: length from the center of the windrose to the start of the
                histogram bar.
            ytick_curr_num: Number of intervals in the current stacked histogram bar.
            ytick_dist: Length of stack interval.
        Returns:
            List of vector arrays representing a stacked histogram bar.
        """
        bar_interval_vecs = []

        for i in range(1, ytick_curr_num + 1):
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
    def _compute_angles(num_of_dir):
        """Compute angles"""

        bin_arr = linspace(0, 360, num_of_dir + 1)

        # Subtract half of segment to capture circular data.
        phi = 360. / (len(bin_arr) - 1) / 2.
        return [b - phi if (b - phi) >= 0.0 else b - phi + 360.
                for b in bin_arr]

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
        t = 180.0 / math.pi  # for degrees to radian conversion

        # Correction to ensure center of wedge is at the top
        bin_arr = [b - 90. for b in bin_arr]

        # Plot the vectors
        for i in range(len(bin_arr) - 1):
            # Correct range
            theta1 = bin_arr[i]
            theta2 = bin_arr[i + 1]

            # Solve for unit x, y vectors
            # Flip y-component to ensure clockwise rotation of each wedge
            vecs.append(((math.cos(theta1 / t), -math.sin(theta1 / t)),
                         (math.cos(theta2 / t), -math.sin(theta2 / t))))
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
    def _histogram_array_radial(bin_vecs, vec_cpt, hist, hist_stacked, radius_arr,
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
        ytick_num = max([len(h) for h in hist_stacked])
        ytick_dist = delta_bar_radius / ytick_num  # Length of 1 y-tick

        # Plot histogram bar in radial coordinates
        hist_coords = []
        for i, (curr_bar, curr_stacks) in enumerate(zip(hist, hist_stacked)):
            # Compute the current bar radius
            curr_bar_radius = len(curr_bar) / max_bar_num * delta_bar_radius
            (vec2, vec1) = bin_vecs[i]  # flip vecs to be ccw

            # Compute array for bottom of the bar
            if min_bar_radius > 0.0:
                base = [(vec2[0] * min_bar_radius, vec2[1] * min_bar_radius),
                        (vec1[0] * min_bar_radius, vec1[1] * min_bar_radius)]
            else:
                base = [vec_cpt]

            if show_stack:
                bar_vecs = WindRose._compute_bar_stack_vecs(
                    base, vec1, vec2, curr_bar_radius, min_bar_radius,
                    len(curr_stacks), ytick_dist)
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

        # Filter out the direction values and make immutable
        data = tuple(tuple(val[1] for val in bin) for bin in data)

        return data, zero_count

    @staticmethod
    def _histogram_data_stacked_count(histogram_data, ytick_num, max_bar_num=None):
        """Compute number of intervals in each bin interval based on frequency subdivision.

        Args:
            histogram_data: Histogram of values as list of binned values.
            ytick_num: Number of maximum frequencies to subdivide bins into.
            max_bar_num: Optional parameter for maximum count of histogram data
                (can be different from max frequency of histogram_data) as number.

        Returns:
            A list of frequency intervals, per histogram bin.
        """
        stacked_nums = []

        if max_bar_num is None:
            max_bar_num = max([len(bin) for bin in histogram_data])

        for bar_data_val in histogram_data:
            # Get number of intervals
            curr_bar_ratio = float(len(bar_data_val)) / max_bar_num
            bar_data_num = math.ceil(curr_bar_ratio * ytick_num)
            stacked_nums.append(bar_data_num)

        return stacked_nums

    @staticmethod
    def _histogram_data_stacked(histogram_data, ytick_num):
        """Get a histogram of stacked wind analysis values binned by wind directions.

        Each histogram bin in this data structure is "stacked" meaning the range of the
        analysis values per bin are averaged to provide a list of average values per
        frequency.

        Args:
            histogram_data: Histogram of the analysis values binned by direction values,
                as list of analysis arrays.
            ytick_num: Maximum number of frequency divisions in the histogram.

        Returns:
            A list of analysis values per bin averaged by frequency count of each bin.
        """
        _histogram_data_stacked = []

        # Get number of intervals per histogram bar
        histogram_data_nums = WindRose._histogram_data_stacked_count(histogram_data,
                                                                     ytick_num)
        for bar_data_vals, bar_data_num in zip(histogram_data, histogram_data_nums):
            if len(bar_data_vals) > 0:
                interval_arr = linspace(min(bar_data_vals), max(bar_data_vals),
                                        int(bar_data_num + 1))

                # Compute midpoint between values
                mean_vals_per_bar = []
                for i in range(len(interval_arr) - 1):
                    midpt = (interval_arr[i] + interval_arr[i+1]) / 2.0
                    mean_vals_per_bar.append(midpt)
            else:
                mean_vals_per_bar = []

            _histogram_data_stacked.append(mean_vals_per_bar)

        return _histogram_data_stacked

    @staticmethod
    def _compute_colored_mesh_array(hist_data, hist_data_stacked, bin_vecs, ytick_num,
                                    min_radius, max_radius, show_stack):
        """Compute a colored mesh from this object's histogram.

        Args:
            hist_data: Histogram of analysis values greater then zero.
            hist_data_stacked: Histogram of analysis values averaged by number of
                stacks.
            bin_vecs: Array of histogram bin edge vectors.
            ytick_num: Number of Y-axis intervals.
            min_radius: Minimum radius for windrose mesh.
            max_radius: Maximum radius for windrose mesh.
            show_stack: Boolean indicating if stacked histogram.
        Returns:
            A colored Mesh2D.
        """

        # Default rose is a unit circle centered at origin. We can scale and translate
        # the resulting mesh.
        vec_cpt = (0, 0)

        # Compute histogram array
        hist_array = WindRose._histogram_array_radial(
            bin_vecs, vec_cpt, hist_data, hist_data_stacked, (min_radius, max_radius),
            show_stack)

        # Flatten and add coordinates
        if not show_stack:
            hist_array = ([v] for v in hist_array)

        # Make mesh
        hist_coords = [interval for bar in hist_array for interval in bar]
        mesh_array = [[Point2D.from_array(vec) for vec in vecs] for vecs in hist_coords]

        # Extract analysis values for color
        color_array = [interval for bar in hist_data_stacked for interval in bar]

        return mesh_array, color_array

    def set_visualization_properties(self, legend_parameters=None, base_point=None,
                                     frequency_spacing_distance=None,
                                     frequency_maximum=None, show_stack=None,
                                     show_zeros=None):
        """Sets visualization properties for this object.

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
        self.legend_parameters = self.legend_parameters if legend_parameters is None \
            else legend_parameters

    def _ytick_zero_inc(self):
        """Get the additional number of yticks required when we display zero values."""
        return math.ceil(self.zeros_per_bin / (self.real_freq_max + self.zeros_per_bin) *
                         self.legend_parameters.segment_count)

    def __repr__(self):
        """Wind rose Collection representation."""
        return 'Wind Rose:\n\n{}\n\n{}'.format(
            self.direction_data_collection.header,
            self.analysis_data_collection.header)