# coding=utf-8
from __future__ import division

import math

from .color import ColorRange
from .datacollection import HourlyContinuousCollection, HourlyDiscontinuousCollection
from .datatype.speed import Speed
from .graphic import GraphicContainer
from .legend import LegendParameters, LegendParametersCategorized
from .compass import Compass

from ladybug_geometry.geometry2d.pointvector import Point2D
from ladybug_geometry.geometry2d.line import LineSegment2D
from ladybug_geometry.geometry2d.polygon import Polygon2D
from ladybug_geometry.geometry2d.mesh import Mesh2D

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
        number_of_directions: A number greater then zero that determines the number
            of directions to "bin" the wind data by. The number of directions must
            be greater then three to plot the wind rose (Default: 8).

    Properties:
        * direction_data_collection
        * analysis_data_collection
        * direction_values
        * analysis_values
        * analysis_period
        * north
        * histogram_data
        * angles
        * legend
        * legend_parameters
        * base_point
        * compass
        * container
        * prevailing_direction
        * mesh_radius
        * compass_radius
        * colored_mesh
        * color_range
        * orientation_lines
        * frequency_lines
        * windrose_lines
        * frequency_spacing_distance
        * frequency_intervals_compass
        * frequency_intervals_mesh
        * frequency_maximum
        * frequency_hours
    """

    DEFAULT_FREQUENCY_SPACING = 10.0
    DEFAULT_FREQUENCY_HOURS = 200.0
    DEFAULT_BASE_POINT = Point2D()
    DEFAULT_NORTH = 0.0

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
        assert number_of_directions > 0, 'The number of directions must be ' \
            'greater then one to bin the data, (and greater then three for ' \
            'plotting the wind rose). Currently the number_of_directions parameter is: '\
            '{}'.format(number_of_directions)

        # Ensure the analysis period of the data collection has been validated
        if not direction_data_collection.validated_a_period:
            direction_data_collection = \
                direction_data_collection.validate_analysis_period()
        if not analysis_data_collection.validated_a_period:
            analysis_data_collection = \
                analysis_data_collection.validate_analysis_period()

        # Assign the inputs as read-only properties of this data collection
        # get rid of duplicate 0 and 360 values
        direction_data_collection.values = \
            [d % 360.0 for d in direction_data_collection.values]
        self._direction_data_collection = direction_data_collection.to_immutable()
        self._analysis_data_collection = analysis_data_collection.to_immutable()
        self._number_of_directions = int(number_of_directions)

        # Compute the windrose data and associated read-only properties
        self._angles = WindRose._compute_angles(number_of_directions)
        self._is_speed_data_type = isinstance(
            self._analysis_data_collection.header.data_type, Speed)
        self._histogram_data, self._zero_count = \
            self._compute_windrose_data(self.direction_values, self.analysis_values,
                                        self.angles, (0, 360), self._is_speed_data_type)

        # Editable public properties for visualization
        self._legend_parameters = None
        self._frequency_spacing_distance = self.DEFAULT_FREQUENCY_SPACING
        self._frequency_hours = None
        self._frequency_intervals_compass = None
        self._show_freq = True
        self._show_zeros = False
        self._base_point = None
        self._compass = None
        self._north = self.DEFAULT_NORTH
        self._poly_array = None
        self._color_array = None

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
        if self._base_point is None:
            self._base_point = self.DEFAULT_BASE_POINT.duplicate()
        return self._base_point

    @base_point.setter
    def base_point(self, base_point):
        assert isinstance(base_point, type(Point2D())), 'base_point must be a Point2D. '\
            'Got {}.'.format(type(base_point))
        self._compass = None
        self._container = None
        self._base_point = base_point

    @property
    def show_freq(self):
        """Get or set property to control displays of frequency of values per direction.

        (Default: True).
        """
        return self._show_freq

    @show_freq.setter
    def show_freq(self, show_freq):
        self._compass = None
        self._container = None
        self._show_freq = bool(show_freq)

    @property
    def show_zeros(self):
        """Get or set property to control if windrose displays zero values or not.

        (Default: True).
        """
        return self._show_zeros

    @show_zeros.setter
    def show_zeros(self, show_zeros):
        _zero_error = (not self._is_speed_data_type and not show_zeros)
        assert self._is_speed_data_type or _zero_error, 'The calmrose can ' \
            'only be shown if the analysis data type is Speed, for all other data ' \
            'types the zero values will be treated the same as the other numeric ' \
            'values.'
        self._compass = None
        self._container = None
        self._show_zeros = bool(show_zeros)

    @property
    def frequency_spacing_distance(self):
        """Get or set distance for frequency lines (Default: 10 model units).

        To maintain fixed radius, this can be set to: 1.0 / self._legend_segment_count
        """
        return self._frequency_spacing_distance

    @frequency_spacing_distance.setter
    def frequency_spacing_distance(self, val):
        assert val > 0.0 and isinstance(val, (float, int)), \
            'frequency_spacing_distance should be a number greater then 0. ' \
            'Got {}.'.format(val)
        self._compass = None
        self._container = None
        self._frequency_spacing_distance = val

    @property
    def frequency_spacing_hypot_distance(self):
        """Length of radius of windrose assuming perpendicular frequency spacing.

        The limit of the frequency_spacing_hypot_distance as number of directions
        approaches infinity equals the frequency_spacing_distance (as is the case
        with a circle).
        """
        _theta = 360.0 / self._number_of_directions
        theta = _theta / 2.0 / 180.0 * math.pi
        return self.frequency_spacing_distance / math.cos(theta)

    @property
    def frequency_maximum(self):
        """Get maximum frequency to represent in the windrose plot.

        Default: number of items in largest windrose histogram bin.
        """
        return self.frequency_intervals_compass * self.frequency_hours

    @property
    def frequency_hours(self):
        """Get or set number of hours to bin analysis values, per direction."""
        if self._frequency_hours is None:
            self._frequency_hours = self.DEFAULT_FREQUENCY_HOURS
        return self._frequency_hours

    @frequency_hours.setter
    def frequency_hours(self, frequency_hours):
        assert frequency_hours > 0, 'frequency_hours must be a number greater then 0. ' \
            'Got: {}'.format(frequency_hours)
        self._frequency_hours = int(frequency_hours)

    @property
    def frequency_intervals_compass(self):
        """Get or set the number of intervals in the windrose compass."""
        if self._frequency_intervals_compass is None:
            self._frequency_intervals_compass = self.frequency_intervals_mesh
        return self._frequency_intervals_compass

    @frequency_intervals_compass.setter
    def frequency_intervals_compass(self, frequency_intervals_compass):
        assert frequency_intervals_compass >= 1, 'The frequency_intervals_compass ' \
            'must be greater then 0. Got: {}'.format(frequency_intervals_compass)
        self._compass = None
        self._container = None
        self._frequency_intervals_compass = int(frequency_intervals_compass)

    @property
    def frequency_intervals_mesh(self):
        """Get the number of intervals in the windrose mesh."""
        return int(math.ceil(self.real_freq_max / self.frequency_hours))

    @property
    def legend_parameters(self):
        """Get or set the LegendParameters object for this plot.

        Default segment count is 10.
        """
        return self.container.legend_parameters

    @legend_parameters.setter
    def legend_parameters(self, legend_parameters):
        if legend_parameters is not None:
            assert isinstance(legend_parameters, LegendParameters), 'legend_parameters' \
                ' must be a LegendParameters. Got {}.'.format(type(legend_parameters))
        self._compass = None
        self._container = None
        self._legend_parameters = legend_parameters

    @property
    def north(self):
        """Get or set north orientation for windrose by degrees.

        This must be a number between -360 and 360. 0 is North, 90 is West and 270
        is East. The rotation is applied counterclockwise.
        """
        return self._north

    @north.setter
    def north(self, north):
        assert isinstance(north, (float, int)), 'north must be a number representing ' \
            'degrees. Got {}.'.format(north)

        self._compass = None
        self._container = None
        self._north = float(north) % 360.0

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
        """Get a histogram of wind analysis values binned by wind direction.

        This histogram will not contain any zero values, so the total amount of hours
        may not add up to hours in the year. The histogram values per bin will be
        reduced to equal the frequency_maximum property which may occur if the
        frequency_intervals_compass property results in maximum hours less then the
        actual binned data.
        """

        if self._frequency_intervals_compass is not None:
            _real_freq_max = max([len(d) for d in self._histogram_data])
            _freq_int_mesh = int(math.ceil(_real_freq_max / self.frequency_hours))
            if self.frequency_intervals_compass < _freq_int_mesh:
                new_histogram_data = []
                for hbin in self._histogram_data:
                    new_histogram_data.append(hbin[:self.frequency_maximum])
                return tuple(new_histogram_data)

        return self._histogram_data

    @property
    def prevailing_direction(self):
        """Get a tuple of the predominant directions of the wind values.
        """
        if self._prevailing_direction is None:
            dirv_num = self._number_of_directions
            freqs = [len(b) for b in self._histogram_data]
            dirvs = [i / dirv_num * 360.0 for i in range(dirv_num)]

            # To ensure ties are captured, iterate through check all values.
            max_freq = 0
            max_dirv = []
            for freq, dirv in zip(freqs, dirvs):
                if max_freq < freq:
                    max_freq = freq
                    max_dirv = [dirv]
                elif max_freq == freq:
                    max_dirv.append(dirv)

            self._prevailing_direction = tuple(max_dirv)

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
        """Get the number of analysis values equal to zero, per orientation bin."""
        if self._zeros_per_bin is None:
            self._zeros_per_bin = float(self.zero_count) / (len(self.angles) - 1)
        return self._zeros_per_bin

    @property
    def real_freq_max(self):
        """Get the maximum hours of wind in the largest histogram bin."""
        return max([len(d) for d in self.histogram_data])

    @property
    def compass(self):
        """Get the compass object for the windrose plot.

        Since the setable properties of basepoint, frequency_spacing_distance, and
        legend_parameters all influence the initiation of this object, this property
        is to None if any of those properties are edited by the user.
        """
        if self._compass is None:
            return Compass(self.compass_radius, self.base_point, north_angle=self.north)
        return self._compass

    @property
    def container(self):
        """Get the GraphicContainer for the windrose mesh.

        Since the setable properties of basepoint, frequency_spacing_distance, and
        legend_parameters all influence the initiation of this object, this property
        is to None if any of those properties are edited by the user.
        """
        if self._container is None:
            # Get analysis values
            if self.show_freq:
                values = [b for a in self.histogram_data for b in a]
            else:
                values = [sum(h) / float(len(h)) for h in self.histogram_data]

            if self.show_zeros:
                values += [0 for i in range(self.zero_count)]

            # Create the graphic container
            z = 0
            self._container = GraphicContainer(
                values, self.compass.min_point3d(z), self.compass.max_point3d(z),
                legend_parameters=self._legend_parameters,
                data_type=self.analysis_data_collection.header.data_type,
                unit=self.analysis_data_collection.header.unit)
        return self._container

    @property
    def colored_mesh(self):
        """Get the colored Mesh2D for this graphic.

        Returns:
            A Mesh2D of the wind rose plot.
        """
        assert self._number_of_directions > 2, 'The number of directions must be ' \
            'greater then three to plot the wind rose. Currently the ' \
            'number_of_directions parameter is: {}'.format(self._number_of_directions)
        assert not all(len(h) == 0 for h in self.histogram_data), \
            'No data is available to plot on the wind rose. Mesh cannot be drawn.'

        # Reset computed graphics to account for changes to cached viz properties
        self._compass = None
        self._container = None

        zero_poly_array, zero_color_array = [], []
        max_bar_radius = self.mesh_radius
        min_bar_radius = self._zero_mesh_radius

        if self.show_zeros and self.zero_count > 0:
            # Compute the array for calm rose
            zero_data = [[0] for _ in self.histogram_data]
            zero_data_stacked = [[[0]] for _ in self.histogram_data]
            zero_poly_array, zero_color_array = self._compute_colored_mesh_array(
                zero_data, zero_data_stacked, self.bin_vectors, 0, min_bar_radius,
                show_freq=False)

        # Calculate stacked_data
        flat_data = [b for a in self.histogram_data for b in a]
        max_data = self._legend_parameters.max if self._legend_parameters is not None \
            and self._legend_parameters.max is not None else max(flat_data)
        if self.show_zeros:
            min_data = min(self.analysis_values)
        else:
            min_data = self._legend_parameters.min if self._legend_parameters is not \
                None and self._legend_parameters.min is not None else min(flat_data)
        bin_count = self.legend_parameters.segment_count
        data_range = (min_data, max_data)
        histogram_data_stacked, bin_range = self._histogram_data_nested(
            self.histogram_data, data_range, bin_count)

        # Compute colors
        if not self.show_freq:
            for i in range(self._number_of_directions):
                stack = histogram_data_stacked[i]
                vals = [b for a in stack for b in a]
                if len(vals) > 0:
                    mean_val = sum(vals) / float(len(vals))
                    histogram_data_stacked[i] = [[mean_val for b in a] for a in stack]
        poly_array, color_array = self._compute_colored_mesh_array(
            self.histogram_data, histogram_data_stacked, self.bin_vectors,
            min_bar_radius, max_bar_radius, self.show_freq)
        poly_array += zero_poly_array
        color_array += zero_color_array

        # Store colors and polygons before processing
        self._poly_array = poly_array
        self._color_array = color_array  # for testing

        # Assign colors
        _color_range = self.color_range
        _color_range = [_color_range.color(val) for val in color_array]
        mesh = Mesh2D.from_face_vertices(poly_array, purge=True)
        mesh.colors = tuple(_color_range)

        # Scale up unit circle to windrose radius (and other transforms)
        return self._transform(mesh)

    @property
    def color_range(self):
        """Get the color range associated with this legend."""
        _l_par = self.legend_parameters

        if isinstance(_l_par, LegendParametersCategorized):
            return ColorRange(_l_par.colors, _l_par.domain, _l_par.continuous_colors)
        else:
            values = self.container.values
            min_val = _l_par.min if _l_par.min is not None else min(values)
            max_val = _l_par.max if _l_par.max is not None else max(values)
            return ColorRange(_l_par.colors, (min_val, max_val))

    @property
    def orientation_lines(self):
        """Get the orientation lines for windrose as a LineSegment2D list."""

        # Reset computed graphics to account for changes to cached viz properties
        self._compass = None
        self._container = None

        # Compute x-axis bin boundaries in polar coordinates
        vec_cpt = (0, 0)
        max_bar_radius = self.compass_radius

        # Vector multiplication with max_bar_radius
        segs = []
        for (vec1, vec2) in self.bin_vectors:
            _seg1 = vec_cpt, (max_bar_radius * vec1[0], max_bar_radius * vec1[1])
            _seg2 = vec_cpt, (max_bar_radius * vec2[0], max_bar_radius * vec2[1])
            segs.extend((LineSegment2D.from_array(_seg1),
                         LineSegment2D.from_array(_seg2)))

        return [self._transform(seg) for seg in segs]

    @property
    def frequency_lines(self):
        """Get the frequency lines for windrose as Polygon2D lists."""

        # Reset computed graphics to account for changes to cached viz properties
        self._compass = None
        self._container = None

        ytick_array = []
        ytick_num = self.frequency_intervals_compass
        zero_dist = self._zero_mesh_radius
        ytick_dist = self.frequency_spacing_hypot_distance
        # Add frequency polygon for calmrose, if exists
        if self.show_zeros and self.zero_count > 0:
            _ytick_array = [(vec1[0] * zero_dist, vec1[1] * zero_dist)
                            for (vec1, _) in self.bin_vectors]
            ytick_array.append(_ytick_array)

        # Add the regular frequency polygons
        for i in range(1, ytick_num + 1):
            _ytick_array = []
            for (vec1, _) in self.bin_vectors:
                _x = (vec1[0] * i * ytick_dist) + (vec1[0] * zero_dist)
                _y = (vec1[1] * i * ytick_dist) + (vec1[1] * zero_dist)
                _ytick_array.append((_x, _y))
            ytick_array.append(_ytick_array)

        return [self._transform(Polygon2D.from_array(vecs)) for vecs in ytick_array]

    @property
    def windrose_lines(self):
        """Get the windrose lines as Polygon2D lists."""

        if self._poly_array is None:
            # colored_mesh property computes windrose geometry with appropriate checks
            # for user-defined parameters, so all windrose geometry properties are set
            # there. If _poly_array is not set, compute colored_mesh.
            self.colored_mesh

        return [self._transform(Polygon2D(vecs)) for vecs in self._poly_array]

    @property
    def mesh_radius(self):
        """Get the radius of the windrose mesh (with zero values).

        This number will not necessarily align to the frequency spacing intervals,
        since fractional values are permitted.
        """
        return self._nonzero_mesh_radius + self._zero_mesh_radius

    @property
    def compass_radius(self):
        """Get the radius of the windrose compass.

        This value is different from the mesh_radius if the frequency_maximum is
        greater then the maximum frequency in the histogram data.
        """
        max_bar_radius = \
            self.frequency_spacing_hypot_distance * self.frequency_intervals_compass

        return max_bar_radius + self._zero_mesh_radius

    @property
    def _nonzero_mesh_radius(self):
        """Get the radius of just the base windrose (excluding the zero values)."""

        ytick_num_frac = self.real_freq_max / self.frequency_hours
        return self.frequency_spacing_hypot_distance * ytick_num_frac

    @property
    def _zero_mesh_radius(self):
        """Get the radius of just the windrose zero values."""

        zero_dist = 0.0
        if self.show_zeros:
            _ytick_num_frac = self.zeros_per_bin / self.frequency_hours
            zero_dist = self.frequency_spacing_hypot_distance * _ytick_num_frac

        return zero_dist

    @staticmethod
    def prevailing_direction_from_data(data, directions_count=8):
        """Get a the prevailing wind direction(s) from a data collection of directions.

        Args:
            data: A data collection with direction angles in them.
            directions_count: An integer for the number of directions around the
                circle to evaluate. (Default: 8).

        Returns:
            A list with at least one value for the prevailing wind direction. This
            will have multiple values in the event of a tie.
        """
        bin_array = WindRose._compute_angles(directions_count)
        hist_data = histogram_circular(data.values, bin_array, (0, 360))
        freqs = [len(b) for b in hist_data]
        dirvs = [i / directions_count * 360.0 for i in range(directions_count)]

        # to ensure ties are captured, iterate through check all values.
        max_freq = 0
        max_dirv = []
        for freq, dirv in zip(freqs, dirvs):
            if max_freq < freq:
                max_freq = freq
                max_dirv = [dirv]
            elif max_freq == freq:
                max_dirv.append(dirv)
        return max_dirv

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
    def _compute_bar_stack_vecs(base_vec_show_freq, vec1, vec2, curr_bar_radius,
                                min_bar_radius, max_bar_num, stacks):
        """Compute the bar geometry arrays for stacked histogram bars.

        Args:
            base_vec_show_freq: list of points for bottem edge of the histogram bar.
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
        si = -1

        for j, st in enumerate(stacks):
            if len(st) > 0:
                si = j
                break

        if si == -1:
            return bar_interval_vecs

        ytick_dist_inc = min_bar_radius
        for i in range(si, len(stacks)):
            # Stack vectors for interval wedges
            if len(stacks[i]) == 0:
                continue

            ytick_dist_inc += (len(stacks[i]) / max_bar_num * curr_bar_radius)

            # Vector multiplication with y_dist_inc and add to bar_coords
            bar_interval_vecs.append(
                base_vec_show_freq + [
                    (vec1[0] * ytick_dist_inc, vec1[1] * ytick_dist_inc),
                    (vec2[0] * ytick_dist_inc, vec2[1] * ytick_dist_inc)
                ])
            # Update
            base_vec_show_freq = list(reversed(bar_interval_vecs[-1][-2:]))

        return bar_interval_vecs

    @staticmethod
    def _histogram_array_radial(bin_vecs, vec_cpt, hist, hist_stacked, radius_arr,
                                show_freq):
        """Coordinates for a radial histogram as a vector array.

        Args:
            bin_vecs: Array of histogram bin edge vectors.
            vec_cpt: Centerpoint of histogram as tuple.
            hist: Histogram data as a list of lists.
            radius_arr: Minimum and maximum distance for bar radius.
            show_freq: Boolean indicating if stacked histogram.
        Returns:
            List of histogram bars as array of vector coordinates.
        """
        # Get histogram properties for plotting bars
        min_bar_radius, max_bar_radius = radius_arr
        delta_bar_radius = max_bar_radius - min_bar_radius  # does not include zeros
        max_bar_num = max([len(a) for a in hist])  # does not include zeros

        # Plot histogram bar in radial coordinates
        hist_coords = []
        for i, curr_stacks in enumerate(hist_stacked):

            if len([b for a in curr_stacks for b in a]) == 0:
                continue

            # Compute the current bar radius
            (vec2, vec1) = bin_vecs[i]  # flip vecs to be ccw

            # Compute array for bottom of the bar
            if min_bar_radius > 0.0:
                base = [(vec2[0] * min_bar_radius, vec2[1] * min_bar_radius),
                        (vec1[0] * min_bar_radius, vec1[1] * min_bar_radius)]
            else:
                base = [vec_cpt]

            if show_freq:
                bar_vecs = WindRose._compute_bar_stack_vecs(
                    base, vec1, vec2, delta_bar_radius, min_bar_radius,
                    max_bar_num, curr_stacks)
                hist_coords.extend(bar_vecs)
            else:
                curr_bar_num = len([b for a in curr_stacks for b in a])
                frac_len = curr_bar_num / max_bar_num
                curr_bar_radius = delta_bar_radius * frac_len
                bar_vecs = base + [(vec1[0] * (curr_bar_radius + min_bar_radius),
                                    vec1[1] * (curr_bar_radius + min_bar_radius)),
                                   (vec2[0] * (curr_bar_radius + min_bar_radius),
                                    vec2[1] * (curr_bar_radius + min_bar_radius))]
                hist_coords.append(bar_vecs)

        return hist_coords

    @staticmethod
    def _compute_windrose_data(direction_values, analysis_values, bin_array, bin_range,
                               is_speed_data_type):
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
        # Filter out zero values if looking at wind speed values
        if is_speed_data_type:
            _direction_values = []
            _analysis_values = []
            for d, v in zip(direction_values, analysis_values):
                if v > 1e-10:
                    _direction_values.append(d)
                    _analysis_values.append(v)
        else:
            _direction_values = direction_values
            _analysis_values = analysis_values

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
    def _histogram_data_nested(histogram_data, analysis_range, bin_count):
        """Computes histogram for each histogram bin based analysis values.

        The function takes a histogram_data structure and applies a second
        pseudo-histogram to each direction bin. In this way the distribution of the
        analysis values are represented. It is a pseudo-histogram since the final
        bin represents values greater than its minimum bounding value, and is therefore
        not bound to a fixed domain.

        Args:
            histogram_data: Histogram of the analysis values binned by direction values,
                as list of analysis arrays.
            analysis_range: Tuple of maximum and minimum analysis values.
            bin_count: The number of bins for the nested pseudo-histogram.

        Returns:
            A tuple with two items.

            - A list of binned analysis values per histogram direction bin.

            - A list of bin intervals used to bin the histogram.
        """
        _histogram_data_nested = []
        min_analy, max_analy = analysis_range[0], analysis_range[1]
        bins = linspace(min_analy, max_analy, int(bin_count))

        # add some epsilon to final bin edge. We do this because the final bin in the
        # analysis histogram is not bounded by a value, but is simply greater then
        # the its minimum bounding value. Note that this means it's not a true histogram
        # with a bounded domain. If this is not done, the final analysis value is not
        # included in the histogram (since the maximum value in a bin interval is
        # exclusive), and would need to be added in it's own bin. There is no way to
        # include the maximum value, without creating arbitrary intervals.
        eps = 1e-1
        bins[-1] += eps

        # Calculate number of hours per frequency segment
        for bar_data_vals in histogram_data:
            _analysis = histogram(bar_data_vals, bins)
            if len(_analysis) == 0:  # all values are the same
                _histogram_data_nested.append([bar_data_vals])
            else:  # it is a normal histogram
                _histogram_data_nested.append(_analysis)

        return _histogram_data_nested, bins

    @staticmethod
    def _compute_colored_mesh_array(hist_data, hist_data_stacked, bin_vecs, min_radius,
                                    max_radius, show_freq):
        """Compute a colored mesh from this object's histogram.

        Args:
            hist_data: Histogram of analysis values greater then zero.
            hist_data_stacked: Histogram of analysis values averaged by number of
                stacks.
            bin_vecs: Array of histogram bin edge vectors.
            min_radius: Minimum radius for windrose mesh.
            max_radius: Maximum radius for windrose mesh.
            show_freq: Boolean indicating if stacked histogram.
        Returns:
            A colored Mesh2D.
        """

        # Default rose is a unit circle centered at origin. We can scale and translate
        # the resulting mesh.
        vec_cpt = (0, 0)

        # Compute histogram array
        hist_coords = WindRose._histogram_array_radial(
            bin_vecs, vec_cpt, hist_data, hist_data_stacked, (min_radius, max_radius),
            show_freq)

        # Construct color array based on show_freq parameter
        color_array = []
        if show_freq:
            for stack in hist_data_stacked:
                for j in range(len(stack)):
                    try:
                        mean_val = sum(stack[j]) / len(stack[j])
                        color_array.append(mean_val)
                    except ZeroDivisionError:
                        mean_val = 0
        else:
            for stack in hist_data_stacked:
                # Value is already averaged
                vals = [b for a in stack for b in a]
                if len(vals) > 0:
                    color_array.append(vals[0])

        # Make mesh
        mesh_array = [[Point2D.from_array(vec) for vec in vecs] for vecs in hist_coords]
        return mesh_array, color_array

    def _transform(self, geometry):
        """Check if geometry defaults and apply transformations."""

        if not self.DEFAULT_BASE_POINT.is_equivalent(self.base_point, 1e-5):
            geometry = geometry.move(self.base_point)
        if abs(self.DEFAULT_NORTH - self.north) > 1e-5:
            geometry = geometry.rotate(self.north / 180.0 * math.pi, self.base_point)

        return geometry

    def __repr__(self):
        """Wind rose Collection representation."""
        return 'Wind Rose:\n\n{}\n\n{}'.format(
            self.direction_data_collection.header,
            self.analysis_data_collection.header)
