# coding=utf-8
from __future__ import division

from .color import Color, Colorset, ColorRange

from ladybug_geometry.geometry3d.pointvector import Point3D, Vector3D
from ladybug_geometry.geometry3d.plane import Plane
from ladybug_geometry.geometry3d.mesh import Mesh3D
from ladybug_geometry.geometry2d.pointvector import Point2D
from ladybug_geometry.geometry2d.mesh import Mesh2D

from collections import Iterable
import sys
if (sys.version_info > (3, 0)):  # python 3
    xrange = range


class Legend(object):
    """Ladybug legend, including associated numerical data.

    Used to draw legend, generate colors, etc.

    Properties:
        legend_parameters
        values
        value_colors
        title
        title_location
        segment_text
        segment_text_location
        segment_mesh
        color_range
        segment_numbers
        segment_colors
        segment_length
        is_min_default
        is_max_default
    """

    def __init__(self, values, legend_parameters=None):
        """Initalize Ladybug Legend.

        Args:
            values: A List or Tuple of numerical values that will be used to
                generate the legend and colors.
            legend_parameters: An Optional LegendParameter object to override
                default parameters of the legend.
            """
        # check the inputs
        assert isinstance(values, Iterable) \
            and not isinstance(values, (str, dict, bytes, bytearray)), \
            'values should be a list or tuple. Got {}'.format(type(values))
        self._values = values
        if legend_parameters is not None:
            assert isinstance(legend_parameters, LegendParameters), \
                'Expected LegendParameters. Got {}.'.format(type(legend_parameters))
            self._legend_par = legend_parameters.duplicate()
        else:
            self._legend_par = LegendParameters()

        # calculate min, max and number of segments
        self._is_min_default = False
        self._is_max_default = False
        if self._legend_par.min is None:
            self._legend_par.min = min(values)
            self._is_min_default = True
        if self._legend_par.max is None:
            self._legend_par.max = max(values)
            self._is_max_default = True

    @property
    def legend_parameters(self):
        """The legend parameters assigned to this legend."""
        return self._legend_par

    @property
    def values(self):
        """The data set assigned to the legend."""
        return self._values

    @property
    def value_colors(self):
        """A List of colors associated with the assigned values."""
        _color_range = self.color_range
        return tuple(_color_range.color(val) for val in self.values)

    @property
    def title(self):
        """A text string for the title of the legend."""
        return self.legend_parameters.title

    @property
    def title_location(self):
        """A Plane for the location and orientation of the legend title."""
        _l_par = self.legend_parameters
        if _l_par.vertical_or_horizontal:
            _title_pt = Point2D(0, _l_par.segment_height *
                                (self.segment_length + 0.25))
        else:
            _title_pt = Point2D(-_l_par.segment_width * self.segment_length,
                                _l_par.segment_height * 1.25)
        return Plane(_l_par.base_plane.n,
                     _l_par.base_plane.xy_to_xyz(_title_pt),
                     _l_par.base_plane.x)

    @property
    def segment_text(self):
        """A list of text strings for the segment labels of the legend."""
        _l_par = self.legend_parameters
        if _l_par.ordinal_dictionary is None:
            format_str = '%.{}f'.format(_l_par.number_decimal_places)
            seg_txt = [format_str % x for x in self.segment_numbers]
            if _l_par.include_larger_smaller:
                seg_txt[0] = '<' + seg_txt[0]
                seg_txt[-1] = '>' + seg_txt[-1]
            return seg_txt
        else:
            seg_txt = []
            for x in self.segment_numbers:
                try:
                    seg_txt.append(_l_par.ordinal_dictionary[x])
                except KeyError:
                    seg_txt.append('')
        return seg_txt

    @property
    def segment_text_location(self):
        """A list of Plane objects for the location of the legend segment text."""
        _l_par = self.legend_parameters
        if _l_par.vertical_or_horizontal:  # vertical
            _pt_2d = tuple(
                Point2D(_l_par.segment_width + _l_par.text_height * 0.25, i)
                for i in Legend._frange(0, _l_par.segment_height *
                                        _l_par.number_of_segments + 1,
                                        _l_par.segment_height))
        else:  # horizontal
            _start_val = -_l_par.segment_width * self.segment_length
            _pt_2d = tuple(
                Point2D(_start_val + i, -_l_par.text_height * 1.25)
                for i in Legend._frange(0, _l_par.segment_width *
                                        _l_par.number_of_segments + 1,
                                        _l_par.segment_width))
        return [Plane(_l_par.base_plane.n,
                      _l_par.base_plane.xy_to_xyz(pt),
                      _l_par.base_plane.x) for pt in _pt_2d]

    @property
    def segment_mesh(self):
        """A Ladybug Mesh3D for the legend colors."""
        # get general properties
        _l_par = self.legend_parameters
        n_seg = self.segment_length
        # create the 2D mesh of the legend
        if _l_par.vertical_or_horizontal:
            mesh2d = Mesh2D.from_grid(
                Point2D(0, 0), 1, n_seg, _l_par.segment_width, _l_par.segment_height)
        else:
            _base_pt = Point2D(-_l_par.segment_width * n_seg, 0)
            mesh2d = Mesh2D.from_grid(
                _base_pt, n_seg, 1, _l_par.segment_width, _l_par.segment_height)
        # add colors to the mesh
        _seg_colors = self.segment_colors
        if not _l_par.continuous_legend:
            mesh2d.colors = _seg_colors
        else:
            if _l_par.vertical_or_horizontal:
                mesh2d.colors = _seg_colors + _seg_colors
            else:
                mesh2d.colors = tuple(col for col in _seg_colors for i in (0, 1))
        # return 3D mesh
        return Mesh3D.from_mesh2d(mesh2d, _l_par.base_plane)

    @property
    def color_range(self):
        """The color range associated with this legend."""
        _l_par = self.legend_parameters
        return ColorRange(_l_par.colors, (_l_par.min, _l_par.max),
                          _l_par.continuous_colors)

    @property
    def segment_numbers(self):
        _l_par = self.legend_parameters
        _seg_stp = (_l_par.max - _l_par.min) / (_l_par.number_of_segments - 1)
        return tuple(_l_par.min + i * _seg_stp
                     for i in xrange(_l_par.number_of_segments))

    @property
    def segment_colors(self):
        """A List of colors associated with the legend segments."""
        _color_range = self.color_range
        return tuple(_color_range.color(val) for val in self.segment_numbers)

    @property
    def segment_length(self):
        """An integer for the number of segment lengths in the legend."""
        _l_par = self.legend_parameters
        return _l_par.number_of_segments if not _l_par.continuous_legend else \
            _l_par.number_of_segments - 1

    @property
    def is_min_default(self):
        """Boolean noting whether the min is default.

        Useful when deciding whether to override the legend to properly display an
        ordinal dictionary.
        """
        return self._is_min_default

    @property
    def is_max_default(self):
        """Boolean noting whether the max is default.

        Useful when deciding whether to override the legend to properly display an
        ordinal dictionary.
        """
        return self._is_max_default

    @staticmethod
    def _frange(start, stop, step):
        """Range function capable of yielding float values."""
        while start < stop:
            yield start
            start += step


class LegendParameters(object):
    """Ladybug legend parameters.

    Attributes:
        min
        max
        number_of_segments
        colors
        continuous_colors
        continuous_legend
        title
        ordinal_dictionary
        number_decimal_places
        include_larger_smaller
        vertical_or_horizontal
        base_plane
        segment_height
        segment_width
        text_height
        font

        is_number_of_segments_default
        is_title_default
        is_base_plane_default
        is_segment_height_default
        is_segment_width_default
        is_text_height_default
    """

    def __init__(self, min=None, max=None, number_of_segments=None,
                 colors=None, continuous_colors=None, continuous_legend=None,
                 title=None, ordinal_dictionary=None, number_decimal_places=None,
                 include_larger_smaller=None, vertical_or_horizontal=None,
                 base_plane=None, segment_height=None, segment_width=None,
                 text_height=None, font=None):
        """Initalize Ladybug Legend Parameters.

        Args:
            min: A number to set the lower boundary of the legend. If None, the
                minimum of the values associated with the legend will be used.
            max: A number to set the upper boundary of the legend. If None, the
                maximum of the values associated with the legend will be used.
            number_of_segments: An interger representing the number of steps between
                the high and low boundary of the legend. The default is set to 11
                and any custom values input in here should always be greater than or
                equal to 2.
            colors: An list of color objects. Default is Ladybug's original colorset.
            continuous_colors: Boolean. If True, the colors generated from the
                corresponding legend will be in a continuous gradient. If False,
                they will be categorized in incremental groups according to the
                number_of_segments. Default is True for continuous colors.
            continuous_legend: Boolean. If True, the legend mesh will be drawn
                vertex-by-vertex resulting in a continuous gradient instead of discrete
                segments. If False, the mesh will be generated with one face for each
                for each of the number_of_segments, resulting in discrete categories.
                Default is False for depicting discrete categories.
            title: Text string for Legend title. Typically, the units of the data are
                used here but the type of data might also be used. Default is
                an empty string.
            ordinal_dictionary: Optional dictionary to map numerical values
                to categories of text. If None, numerical values will be used in
                the legend segment . If not, text categories will be used and the
                legend will be ordinal. Note that, if the number if items in
                the dictionary are less than the number_of_segments, some segments
                won't recieve any label. Examples for possible dictiionaries include:
                {-1: 'Cold', 0: 'Neutral', 1: 'Hot'}
                {0: 'False', 1: 'True'}
            number_decimal_places: An optional integer to set the number of decimal
                places for the numbers in the legend text. Default is 2. Note that
                this inpput has no bearing on the resulting legend text when an
                ordinal_dictionary is present.
            include_larger_smaller: Boolean noting whether to include larger than and
                smaller than (> and <) values after the upper and lower legend segment
                text. Default is False.
            vertical_or_horizontal: Boolean. If True, the legend mesh and text points
                will be generated vertically.  If False, they will genrate a
                horizontal legend. Default is True for a vertically-oriented legend.
            base_plane: A Ladybug Plane object to note the starting point from
                where the legend will be genrated. The default is the world XY plane
                at origin (0, 0, 0).
            segment_height: An optional number to set the height of each of the legend
                segments. Default is 1.
            segment_width: An optional number to set the width of each of the legend
                segments. Default is 1 when legend is vertical. When horizontal, the
                default is (text_height * (number_decimal_places + 2)).
            text_height: An optional number to set the size of the text in model units.
                Default is half of the segment_height.
            font: An optional text string to specify the font to be used for the text.
                Examples include "Arial", "Times New Roman", "Courier" (all without
                quotations). Note that this parameter may not have an effect on certain
                interfaces that have limited access to fonts. Default is "Arial".
        """
        self._min = None
        self._max = None
        self.min = min
        self.max = max
        self.number_of_segments = number_of_segments
        self.colors = colors
        self.continuous_colors = continuous_colors
        self.continuous_legend = continuous_legend
        self.title = title
        self.ordinal_dictionary = ordinal_dictionary
        self.number_decimal_places = number_decimal_places
        self.include_larger_smaller = include_larger_smaller
        self.vertical_or_horizontal = vertical_or_horizontal
        self.base_plane = base_plane
        self.segment_height = segment_height
        self.segment_width = segment_width
        self.text_height = text_height
        self.font = font

    @property
    def min(self):
        """Get or set legend minimum."""
        return self._min

    @min.setter
    def min(self, minimum):
        if minimum is not None:
            assert isinstance(minimum, (float, int)), \
                'Expected number for min. Got {}.'.format(type(minimum))
            if self._max is not None:
                assert minimum <= self._max, \
                    'Input min is greater than input max. {} > {}.'.format(
                        minimum, self._max)
        self._min = minimum

    @property
    def max(self):
        """Get or set legend maximum."""
        return self._max

    @max.setter
    def max(self, maximum):
        if maximum is not None:
            assert isinstance(maximum, (float, int)), \
                'Expected number for max. Got {}.'.format(type(maximum))
            if self._min is not None:
                assert maximum >= self._min, \
                    'Input max is less than input min. {} < {}.'.format(
                        maximum, self._min)
        self._max = maximum

    @property
    def number_of_segments(self):
        """Get or set the number of segments in the legend."""
        return self._number_of_segments

    @number_of_segments.setter
    def number_of_segments(self, nos):
        if nos is not None:
            assert isinstance(nos, int), \
                'Expected integer for number_of_segments. Got {}.'.format(type(nos))
            assert nos >= 2, 'number_of_segments must be greater or equal to 2.' \
                ' Got {}.'.format(nos)
            self._number_of_segments = nos
            self._is_number_of_segments_default = False
        else:
            self._number_of_segments = 11
            self._is_number_of_segments_default = True

    @property
    def colors(self):
        """Get or set the colors defining the legend."""
        return self._colors

    @colors.setter
    def colors(self, cols):
        if cols is not None:
            assert isinstance(cols, Iterable) \
                and not isinstance(cols, (str, dict, bytes, bytearray)), \
                'Colors should be a list or tuple. Got {}'.format(type(cols))
            assert len(cols) > 1, 'There must be at least two colors to make a legend.'
            try:
                cols = tuple(col if isinstance(col, Color) else Color(
                    col.R, col.G, col.B) for col in cols)
            except Exception:
                try:
                    cols = tuple(Color(col.Red, col.Green, col.Blue)
                                 for col in cols)
                except Exception:
                    raise ValueError("{} is not a valid list of colors".format(cols))
            self._colors = cols
        else:
            self._colors = Colorset.original()

    @property
    def continuous_colors(self):
        """Boolean noting whether colors generated are continuous or discrete."""
        return self._continuous_colors

    @continuous_colors.setter
    def continuous_colors(self, cont_cols):
        if cont_cols is not None:
            assert isinstance(cont_cols, bool), \
                'Expected boolean for continuous_colors. Got {}.'.format(type(cont_cols))
            self._continuous_colors = cont_cols
        else:
            self._continuous_colors = True

    @property
    def continuous_legend(self):
        """Boolean noting whether legend is drawn as a gradient or discrete segments."""
        return self._continuous_legend

    @continuous_legend.setter
    def continuous_legend(self, cont_leg):
        if cont_leg is not None:
            assert isinstance(cont_leg, bool), \
                'Expected boolean for continuous_legend. Got {}.'.format(type(cont_leg))
            self._continuous_legend = cont_leg
        else:
            self._continuous_legend = False

    @property
    def title(self):
        """Get or set the text for the title of the legend."""
        return self._title

    @title.setter
    def title(self, title):
        if title is not None:
            assert isinstance(title, str), \
                'Expected string for title. Got {}.'.format(type(title))
            self._title = title
            self._is_title_default = False
        else:
            self._title = ''
            self._is_title_default = True

    @property
    def ordinal_dictionary(self):
        """Get or set a dictionary that maps values to text categories."""
        return self._ordinal_dictionary

    @ordinal_dictionary.setter
    def ordinal_dictionary(self, o_dict):
        if o_dict is not None:
            assert isinstance(o_dict, dict), \
                'Expected dictionary for ordinal_dictionary. Got {}.'.format(
                    type(o_dict))
            for key in o_dict.keys():
                assert isinstance(key, int), \
                    'Expected integer for ordinal_dictionary key. Got {}.'.format(
                        type(key))
        self._ordinal_dictionary = o_dict

    @property
    def number_decimal_places(self):
        """Get or set the number of decimal places in the legend text."""
        return self._number_decimal_places

    @number_decimal_places.setter
    def number_decimal_places(self, n_dec):
        if n_dec is not None:
            assert isinstance(n_dec, int), \
                'Expected integer for number_decimal_places. Got {}.'.format(type(n_dec))
            self._number_decimal_places = n_dec
        else:
            self._number_decimal_places = 2

    @property
    def include_larger_smaller(self):
        """Boolean noting whether > and < should be included in legend segment text."""
        return self._include_larger_smaller

    @include_larger_smaller.setter
    def include_larger_smaller(self, lgsm):
        if lgsm is not None:
            assert isinstance(lgsm, bool), \
                'Expected boolean for include_larger_smaller. Got {}.'.format(type(lgsm))
            self._include_larger_smaller = lgsm
        else:
            self._include_larger_smaller = False

    @property
    def vertical_or_horizontal(self):
        """Boolean noting whether legend is vertical (True) of horizontal (False).
        """
        return self._vertical_or_horizontal

    @vertical_or_horizontal.setter
    def vertical_or_horizontal(self, vertical):
        if vertical is not None:
            assert isinstance(vertical, bool), \
                'Expected boolean for vertical_or_horizontal. Got {}.'.format(
                    type(vertical))
            self._vertical_or_horizontal = vertical
        else:
            self._vertical_or_horizontal = True

    @property
    def base_plane(self):
        """Get or set a Ladybug Point3D for the base point of the legend."""
        return self._base_plane

    @base_plane.setter
    def base_plane(self, base_pl):
        if base_pl is not None:
            assert isinstance(base_pl, Plane), \
                'Expected Ladybug Plane for base_plane. Got {}.'.format(type(base_pl))
            self._base_plane = base_pl
            self._is_base_plane_default = False
        else:
            self._base_plane = Plane(Vector3D(0, 0, 1), Point3D(0, 0, 0))
            self._is_base_plane_default = True

    @property
    def segment_height(self):
        """Get or set the height for each of the legend segments."""
        return self._segment_height

    @segment_height.setter
    def segment_height(self, seg_h):
        if seg_h is not None:
            assert isinstance(seg_h, (float, int)), \
                'Expected number for segment_height. Got {}.'.format(type(seg_h))
            assert seg_h > 0, 'segment_height must be greater than 0.' \
                ' Got {}.'.format(seg_h)
            self._segment_height = seg_h
            self._is_segment_height_default = False
        else:
            self._segment_height = 1
            self._is_segment_height_default = True

    @property
    def segment_width(self):
        """Get or set the width for each of the legend segments."""
        if not self.vertical_or_horizontal and self.is_segment_width_default:
            return self.text_height * (self.number_decimal_places + 2)
        return self._segment_width

    @segment_width.setter
    def segment_width(self, seg_w):
        if seg_w is not None:
            assert isinstance(seg_w, (float, int)), \
                'Expected number for segment_width. Got {}.'.format(type(seg_w))
            assert seg_w > 0, 'segment_width must be greater than 0.' \
                ' Got {}.'.format(seg_w)
            self._segment_width = seg_w
            self._is_segment_width_default = False
        else:
            self._segment_width = 1
            self._is_segment_width_default = True

    @property
    def text_height(self):
        """Get or set the height for the legend text."""
        if self.is_text_height_default:
            return self.segment_height * 0.5
        return self._text_height

    @text_height.setter
    def text_height(self, txt_h):
        if txt_h is not None:
            assert isinstance(txt_h, (float, int)), \
                'Expected number for text_height. Got {}.'.format(type(txt_h))
            assert txt_h > 0, 'text_height must be greater than 0.' \
                ' Got {}.'.format(txt_h)
            self._is_text_height_default = False
        else:
            self._is_text_height_default = True
        self._text_height = txt_h

    @property
    def font(self):
        """Get or set the font for the legend text."""
        return self._font

    @font.setter
    def font(self, font):
        if font is not None:
            assert isinstance(font, str), \
                'Expected string for font. Got {}.'.format(type(font))
            self._font = font
        else:
            self._font = 'Arial'

    @property
    def is_number_of_segments_default(self):
        """Boolean noting whether the number of segments is defaulted."""
        return self._is_number_of_segments_default

    @property
    def is_title_default(self):
        """Boolean noting whether the title is defaulted."""
        return self._is_title_default

    @property
    def is_base_plane_default(self):
        """Boolean noting whether the base point is defaulted."""
        return self._is_base_plane_default

    @property
    def is_segment_height_default(self):
        """Boolean noting whether the segment height is defaulted."""
        return self._is_segment_height_default

    @property
    def is_segment_width_default(self):
        """Boolean noting whether the segment width is defaulted."""
        return self._is_segment_width_default

    @property
    def is_text_height_default(self):
        """Boolean noting whether the text height is defaulted."""
        return self._is_text_height_default

    def duplicate(self):
        """Return a copy of the current legend parameters."""
        new_par = LegendParameters(
            self.min, self.max, self.number_of_segments, self.colors,
            self.continuous_colors, self.continuous_legend, self.title,
            self.ordinal_dictionary, self.number_decimal_places,
            self.include_larger_smaller, self.vertical_or_horizontal,
            self.base_plane, self.segment_height, self.segment_width, self.text_height,
            self.font)
        new_par._is_number_of_segments_default = self._is_number_of_segments_default
        new_par._is_title_default = self._is_title_default
        new_par._is_base_plane_default = self._is_base_plane_default
        new_par._is_segment_height_default = self._is_segment_height_default
        new_par._is_segment_width_default = self._is_segment_width_default
        new_par._is_text_height_default = self._is_text_height_default
        return new_par

    def ToString(self):
        """Overwrite .NET ToString method."""
        return self.__repr__()

    def __repr__(self):
        """Legend parameter representation."""
        return 'Legend Parameters\n min: {}\n max: {}\n # segments: {}' \
            '\n continuous legend: {}\n vertical: {}\n base plane: {}' \
            '\n font: {}'.format(
                self.min, self.max, self.number_of_segments, self.continuous_legend,
                self.vertical_or_horizontal, self.base_plane, self.font)
