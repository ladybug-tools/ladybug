# coding=utf-8
from __future__ import division
import re
try:
    from collections.abc import Iterable  # python < 3.7
except ImportError:
    from collections import Iterable  # python >= 3.8
import sys
if (sys.version_info > (3, 0)):  # python 3
    xrange = range

from ladybug_geometry.geometry3d.pointvector import Point3D, Vector3D
from ladybug_geometry.geometry3d.plane import Plane
from ladybug_geometry.geometry3d.mesh import Mesh3D
from ladybug_geometry.geometry2d.pointvector import Point2D
from ladybug_geometry.geometry2d.mesh import Mesh2D

from .color import Color, Colorset, ColorRange


class Legend(object):
    """Ladybug legend used to get legend geometry, legend text, generate colors, etc.

    Args:
        values: A List or Tuple of numerical values that will be used to
            generate the legend and colors.
        legend_parameters: An Optional LegendParameter object to override
            default parameters of the legend.

    Properties:
        * legend_parameters
        * values
        * value_colors
        * title
        * title_location
        * title_location_2d
        * segment_text
        * segment_text_location
        * segment_text_location_2d
        * segment_mesh
        * segment_mesh_2d
        * color_range
        * segment_numbers
        * segment_colors
        * segment_length
        * is_min_default
        * is_max_default

    Usage:

    .. code-block:: python

        1.
        data = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        legend = Legend(data, LegendParameters(segment_count=6))
        print(legend.segment_text)
        print(legend.segment_mesh)
        print(legend.segment_colors)

        >> ['0.00', '1.80', '3.60', '5.40', '7.20', '9.00']
        >> Mesh3D (6 faces) (14 vertices)
        >> ((R:75, G:107, B:169), (R:159, G:189, B:238), (R:224, G:229, B:145),
            (R:247, G:200, B:53), (R:234, G:113, B:0), (R:234, G:38, B:0))

        2.
        data = [100, 300, 500, 1000, 2000, 3000]
        leg_colors = [Color(0, 0, 255), Color(0, 255, 0), Color(255, 0, 0)]
        legend_par = LegendParametersCategorized([300, 2000], leg_colors)
        legend_par.category_names = ['low', 'desired', 'too much']
        legend_par.continuous_colors = False  # get data in only 3 colors
        legend = Legend(data, legend_par)
        print(legend.segment_text)
        print(legend.segment_mesh)
        print(legend.segment_colors)
        print(legend.value_colors)
        >> ['low', 'desired', 'too much']
        >> Mesh3D (3 faces) (8 vertices)
        >> ((R:0, G:0, B:255), (R:0, G:255, B:0), (R:255, G:0, B:0))
        >> ((R:0, G:0, B:255), (R:0, G:255, B:0), (R:0, G:255, B:0),
            (R:0, G:255, B:0), (R:0, G:255, B:0), (R:255, G:0, B:0))

        3.
        data = [-0.5, 0, 0.5]
        legend_par = LegendParameters(min=-1, max=1, segment_count=3)
        legend_par.ordinal_dictionary = {-3: 'Cold', -2: 'Cool', -1: 'Slightly Cool',
                                         0: 'Neutral',
                                         1: 'Slightly Warm', 2: 'Warm', 3: 'Hot'}
        legend = Legend(data, legend_par)
        print(legend.segment_text)
        print(legend.segment_mesh)
        print(legend.segment_colors)
        legend.legend_parameters.segment_count = 5
        print(legend.segment_text)
        legend.legend_parameters.min = -2
        legend.legend_parameters.max = 2
        print(legend.segment_text)
        >> ['Slightly Cool', 'Neutral', 'Slightly Warm']
        >> Mesh3D (3 faces) (8 vertices)
        >> ((R:75, G:107, B:169), (R:249, G:235, B:89), (R:234, G:38, B:0))
        >> ['Slightly Cool', '', 'Neutral', '', 'Slightly Warm']
        >> ['Cool', 'Slightly Cool', 'Neutral', 'Slightly Warm', 'Warm']
    """
    __slots__ = ('_values', '_legend_par', '_is_min_default', '_is_max_default')

    def __init__(self, values, legend_parameters=None):
        """Initialize Ladybug Legend.
        """
        # check the inputs
        assert isinstance(values, Iterable) \
            and not isinstance(values, (str, dict, bytes, bytearray)), \
            'values should be a list or tuple. Got {}'.format(type(values))
        if not isinstance(values, tuple):
            values = tuple(values)
        assert len(values) != 0, 'There must be at least one value.'
        self._values = values
        if legend_parameters is not None:
            assert isinstance(legend_parameters, LegendParameters), \
                'Expected LegendParameters. Got {}.'.format(type(legend_parameters))
            self._legend_par = legend_parameters.duplicate()
        else:
            self._legend_par = LegendParameters()

        # set default min, max and segment count (if min == max)
        self._is_min_default = False
        self._is_max_default = False
        if self._legend_par.min is None:
            self._legend_par.min = min(values)
            self._is_min_default = True
        if self._legend_par.max is None:
            self._legend_par.max = max(values)
            self._is_max_default = True
        if self._legend_par.min == self._legend_par.max and not \
                isinstance(self._legend_par, LegendParametersCategorized) and \
                self._legend_par.is_segment_count_default:
            self._legend_par._segment_count = 1

        # set the default segment width if the legend is horizontal
        if not self._legend_par.vertical and self._legend_par.is_segment_width_default:
            max_len = len(str(int(self._legend_par.max)))
            self._legend_par.properties_3d.segment_width = \
                self._legend_par.text_height * \
                (max_len + self._legend_par.decimal_count + 2)
            self._legend_par.properties_3d._is_segment_width_default = True

    @classmethod
    def from_dict(cls, data):
        """Create a legend from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "values": [0, 10],
            "legend_parameters": None
            }
        """
        legend_parameters = None
        if 'legend_parameters' in data and data['legend_parameters'] is not None:
            if data['legend_parameters']['type'] == 'LegendParametersCategorized':
                legend_parameters = LegendParametersCategorized.from_dict(
                    data['legend_parameters'])
            else:
                legend_parameters = LegendParameters.from_dict(data['legend_parameters'])

        legend = cls(data['values'], legend_parameters)
        legend._is_min_default = data['is_min_default'] if 'is_min_default' in data \
            else False
        legend._is_max_default = data['is_max_default'] if 'is_max_default' in data \
            else False
        return legend

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
        _base_pl = self.legend_parameters.base_plane
        _title_pt = self._title_point_2d()
        return Plane(_base_pl.n, _base_pl.xy_to_xyz(_title_pt), _base_pl.x)

    @property
    def title_location_2d(self):
        """A Point2D for the location of the title.

        Useful for output to 2D interfaces.
        """
        _base_o = self.legend_parameters.base_plane.o
        _title_pt = self._title_point_2d()
        return Point2D(_title_pt.x + _base_o.x, _title_pt.y + _base_o.y)

    @property
    def segment_text(self):
        """A list of text strings for the segment labels of the legend."""
        _l_par = self.legend_parameters
        if isinstance(_l_par, LegendParametersCategorized):
            return _l_par.category_names
        else:
            if _l_par.ordinal_dictionary is None:
                format_str = '%.{}f'.format(_l_par.decimal_count)
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
        _base_pl = self.legend_parameters.base_plane
        _pt_2d = self._segment_point_2d()
        return [Plane(_base_pl.n, _base_pl.xy_to_xyz(pt), _base_pl.x) for pt in _pt_2d]

    @property
    def segment_text_location_2d(self):
        """A list of Point2D for the location of the legend segment text.

        Useful for output to 2D interfaces.
        """
        _base_o = self.legend_parameters.base_plane.o
        _pt_2d = self._segment_point_2d()
        return [Point2D(pt.x + _base_o.x, pt.y + _base_o.y) for pt in _pt_2d]

    @property
    def segment_mesh(self):
        """A Ladybug Mesh3D for the legend colors."""
        _mesh_2d = self._segment_mesh_2d()
        return Mesh3D.from_mesh2d(_mesh_2d, self.legend_parameters.base_plane)

    @property
    def segment_mesh_2d(self):
        """A Ladybug Mesh2D for the legend colors."""
        _o = self.legend_parameters.base_plane.o
        return self._segment_mesh_2d(Point2D(_o.x, _o.y))

    @property
    def color_range(self):
        """The color range associated with this legend."""
        _l_par = self.legend_parameters
        if isinstance(_l_par, LegendParametersCategorized):
            return ColorRange(_l_par.colors, _l_par.domain, _l_par.continuous_colors)
        else:
            return ColorRange(_l_par.colors, (_l_par.min, _l_par.max))

    @property
    def segment_numbers(self):
        """Get a list of numbers along a linear scale from the min to max."""
        _l_par = self.legend_parameters
        try:
            _seg_stp = (_l_par.max - _l_par.min) / (_l_par.segment_count - 1)
        except ZeroDivisionError:
            _seg_stp = 0
        return tuple(_l_par.min + i * _seg_stp
                     for i in xrange(_l_par.segment_count))

    @property
    def segment_colors(self):
        """A list of colors associated with the legend segments."""
        if isinstance(self.legend_parameters, LegendParametersCategorized):
            return self.legend_parameters.colors
        _color_range = self.color_range
        return tuple(_color_range.color(val) for val in self.segment_numbers)

    @property
    def segment_length(self):
        """An integer for the number of segment lengths in the legend."""
        _l_par = self.legend_parameters
        return _l_par.segment_count if not _l_par.continuous_legend else \
            _l_par.segment_count - 1

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

    def duplicate(self):
        """Return a copy of the current legend."""
        return self.__copy__()

    def to_dict(self):
        """Get legend as a dictionary."""
        return {
            'values': self.values,
            'legend_parameters': self.legend_parameters.to_dict(),
            'is_min_default': self.is_min_default,
            'is_max_default': self.is_max_default,
            'type': 'Legend'
        }

    def _title_point_2d(self):
        """Point2D for the title in the 2D space of the legend."""
        _l_par = self.legend_parameters
        if _l_par.vertical:
            offset = 0.5 if self.legend_parameters.continuous_legend else 0.25
            base = Point2D(0, _l_par.segment_height * (self.segment_length + offset))
        else:
            base = Point2D(-_l_par.segment_width * self.segment_length,
                           _l_par.segment_height * 1.25)
        ln_break_count = self.legend_parameters.title.count('\n')
        if ln_break_count != 0:  # offset the text so that it's not over the legend
            offset = ln_break_count * self.legend_parameters.text_height * 1.5
            return Point2D(base.x, base.y + offset)
        return base

    def _segment_point_2d(self):
        """Point2D for the segment text in the 2D space of the legend."""
        _l_par = self.legend_parameters
        if _l_par.vertical:  # vertical
            _pt_2d = tuple(
                Point2D(_l_par.segment_width + _l_par.text_height * 0.25, i)
                for i in Legend._frange(
                    0, _l_par.segment_height * _l_par.segment_count,
                    _l_par.segment_height))
        else:  # horizontal
            _start_val = -_l_par.segment_width * self.segment_length
            _pt_2d = tuple(
                Point2D(_start_val + i, -_l_par.text_height * 1.25)
                for i in Legend._frange(
                    0, _l_par.segment_width * _l_par.segment_count,
                    _l_par.segment_width))
        return _pt_2d

    def _segment_mesh_2d(self, base_pt=Point2D(0, 0)):
        """Mesh2D for the segments in the 2D space of the legend."""
        # get general properties
        _l_par = self.legend_parameters
        n_seg = self.segment_length
        # create the 2D mesh of the legend
        if _l_par.vertical:
            mesh2d = Mesh2D.from_grid(
                base_pt, 1, n_seg, _l_par.segment_width, _l_par.segment_height)
        else:
            _base_pt = Point2D(base_pt.x - _l_par.segment_width * n_seg, base_pt.y)
            mesh2d = Mesh2D.from_grid(
                _base_pt, n_seg, 1, _l_par.segment_width, _l_par.segment_height)
        # add colors to the mesh
        _seg_colors = self.segment_colors
        if not _l_par.continuous_legend:
            mesh2d.colors = _seg_colors
        else:
            if _l_par.vertical:
                mesh2d.colors = _seg_colors + _seg_colors
            else:
                mesh2d.colors = tuple(col for col in _seg_colors for i in (0, 1))
        return mesh2d

    @staticmethod
    def _frange(start, stop, step):
        """Range function capable of yielding float values."""
        while start < stop:
            yield start
            start += step

    def __copy__(self):
        _leg = Legend(self.values, self.legend_parameters)
        _leg._is_min_default = self._is_min_default
        _leg._is_max_default = self._is_max_default
        return _leg

    def __len__(self):
        """Return length of values on the object."""
        return len(self._values)

    def __getitem__(self, key):
        """Return one of the values."""
        return self._values[key]

    def __iter__(self):
        """Iterate through the values."""
        return iter(self._values)

    def __key(self):
        return (self._legend_par, self._is_min_default, self._is_max_default) + \
            tuple(self._values)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, Legend) and self.__key() == other.__key()

    def __ne__(self, value):
        return not self.__eq__(value)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """Legend representation."""
        return 'Ladybug Legend ({} values)'.format(len(self))


class LegendParameters(object):
    """Ladybug legend parameters used to customize legends.

    All properties of LegendParameters are set-able (except the
    is_property_default ones).

    Args:
        min: A number to set the lower boundary of the legend. If None, the
            minimum of the values associated with the legend will be used.
        max: A number to set the upper boundary of the legend. If None, the
            maximum of the values associated with the legend will be used.
        segment_count: An integer representing the number of steps between
            the high and low boundary of the legend. The default is set to 11
            and any custom values input in here should always be greater than or
            equal to 2.
        colors: An list of color objects. Default is Ladybug's original colorset.
        title: Text string for Legend title. Typically, the units of the data are
            used here but the type of data might also be used. Default is
            an empty string.
        base_plane: A Ladybug Plane object to note the starting point from
            where the legend will be generated. The default is the world XY plane
            at origin (0, 0, 0).

    Properties:
        * min
        * max
        * segment_count
        * colors
        * continuous_legend
        * title
        * ordinal_dictionary
        * decimal_count
        * include_larger_smaller
        * vertical
        * font
        * user_data

        * properties_3d
        * base_plane
        * segment_height
        * segment_width
        * text_height
        * properties_2d
        * origin_x
        * origin_y
        * segment_height_2d
        * segment_width_2d
        * text_height_2d

        * is_segment_count_default
        * are_colors_default
        * is_title_default
        * is_base_plane_default
        * is_segment_height_default
        * is_segment_width_default
        * is_text_height_default
        * is_origin_x_default
        * is_origin_y_default
        * is_segment_height_2d_default
        * is_segment_width_2d_default
        * is_text_height_2d_default

    Usage:

    .. code-block:: python

        lp = LegendParameters(min=0, max=100, segment_count=6)
        lp.vertical = False
        lp.segment_width = 5
    """
    __slots__ = (
        '_min', '_max', '_segment_count', '_colors', '_continuous_legend',
        '_title', '_ordinal_dictionary', '_decimal_count', '_include_larger_smaller',
        '_vertical', '_font', '_user_data', '_properties_3d', '_properties_2d',
        '_is_segment_count_default', '_are_colors_default', '_is_title_default')

    def __init__(self, min=None, max=None, segment_count=None,
                 colors=None, title=None, base_plane=None):
        """Initialize Ladybug LegendParameters."""
        # set the init arguments
        self._min = None
        self._max = None
        self.min = min
        self.max = max
        self.segment_count = segment_count
        self.colors = colors
        self.title = title

        # set the other properties to None/default
        self.continuous_legend = None
        self.ordinal_dictionary = None
        self.decimal_count = None
        self.include_larger_smaller = None
        self.vertical = None
        self.font = None
        self._user_data = None

        # set the 3D and 2D properties
        self.properties_3d = Legend3DParameters(base_plane)
        self.properties_2d = Legend2DParameters()

    @classmethod
    def from_dict(cls, data):
        """Create LegendParameters from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "type": "LegendParameters",
            "min": -3,
            "max": 3,
            "segment_count": 7
            }
        """
        data = data.copy()  # copy to avoid mutating the input dictionary
        assert data['type'] == 'LegendParameters', \
            'Expected LegendParameters. Got {}.'.format(data['type'])
        default_dict = {'type': 'Default'}
        optional_keys = (
            'min', 'max', 'segment_count', 'colors', 'continuous_legend', 'title',
            'ordinal_dictionary', 'decimal_count', 'include_larger_smaller',
            'vertical', 'font', 'properties_3d', 'properties_2d')
        for key in optional_keys:
            if key not in data:
                data[key] = None
            elif data[key] == default_dict:
                data[key] = None

        colors = None
        if data['colors'] is not None:
            colors = [Color.from_dict(col) for col in data['colors']]

        leg_par = cls(data['min'], data['max'], data['segment_count'],
                      colors, data['title'])
        leg_par.continuous_legend = data['continuous_legend']
        leg_par.ordinal_dictionary = data['ordinal_dictionary']
        leg_par.decimal_count = data['decimal_count']
        leg_par.include_larger_smaller = data['include_larger_smaller']
        leg_par.vertical = data['vertical']
        leg_par.font = data['font']
        if data['properties_3d'] is not None:
            leg_par.properties_3d = Legend3DParameters.from_dict(data['properties_3d'])
        if data['properties_2d'] is not None:
            leg_par.properties_2d = Legend2DParameters.from_dict(data['properties_2d'])
        if 'user_data' in data and data['user_data'] is not None:
            leg_par.user_data = data['user_data']
        return leg_par

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
    def segment_count(self):
        """Get or set the number of segments in the legend."""
        return self._segment_count

    @segment_count.setter
    def segment_count(self, nos):
        if nos is not None:
            assert isinstance(nos, int), \
                'Expected integer for segment_count. Got {}.'.format(type(nos))
            assert nos >= 1, 'segment_count must be greater or equal to 1.' \
                ' Got {}.'.format(nos)
            self._segment_count = nos
            self._is_segment_count_default = False
        else:
            self._segment_count = 11
            self._is_segment_count_default = True

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
            self._colors = self._convert_colors(cols)
            assert len(self._colors) > 1, \
                'There must be at least two colors to make a legend.'
            self._are_colors_default = False
        else:
            self._colors = Colorset.original()
            self._are_colors_default = True

    @property
    def continuous_legend(self):
        """Boolean noting whether legend is drawn as a gradient or discrete segments.

        If True, the legend mesh will be drawn vertex-by-vertex resulting in a
        continuous gradient instead of discrete segments. If False, the mesh will be
        generated with one face for each of the segment_count.
        Default: False for depicting discrete categories.
        """
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
        """Get or set an optional dictionary that maps values to text categories.

        If None, numerical values will be used for the legend segments. If not, text
        categories will be used and the legend will be ordinal. Note that, if the
        number of items in the dictionary are less than the segment_count, some segments
        won't receive any label. Examples for possible dictionaries include:
        {-1: 'Cold', 0: 'Neutral', 1: 'Hot'}
        {0: 'False', 1: 'True'}
        """
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
    def decimal_count(self):
        """Get or set an integer for the number of decimal places in the legend text.

        Default is 2. Note that this input has no bearing on the resulting legend
        text when an ordinal_dictionary is present.
        """
        return self._decimal_count

    @decimal_count.setter
    def decimal_count(self, n_dec):
        if n_dec is not None:
            assert isinstance(n_dec, int), \
                'Expected integer for decimal_count. Got {}.'.format(type(n_dec))
            self._decimal_count = n_dec
        else:
            self._decimal_count = 2

    @property
    def include_larger_smaller(self):
        """Boolean noting whether > and < should be included in legend segment text."""
        return self._include_larger_smaller

    @include_larger_smaller.setter
    def include_larger_smaller(self, lgsm):
        self._include_larger_smaller = bool(lgsm)

    @property
    def vertical(self):
        """Boolean noting whether legend is vertical (True) or horizontal (False).

        Default: True for a vertically-oriented legend.
        """
        return self._vertical

    @vertical.setter
    def vertical(self, vertical):
        if vertical is not None:
            assert isinstance(vertical, bool), \
                'Expected boolean for vertical. Got {}.'.format(
                    type(vertical))
            self._vertical = vertical
        else:
            self._vertical = True

    @property
    def font(self):
        """Get or set the font for the legend text.

        Examples include "Arial", "Times New Roman", "Courier". Note that this
        parameter may not have an effect on certain interfaces that have limited
        access to fonts. Default is "Arial".
        """
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
    def properties_3d(self):
        """Get or set a Legend3DParameters for the properties of 3D legends."""
        return self._properties_3d

    @properties_3d.setter
    def properties_3d(self, value):
        if value is not None:
            assert isinstance(value, Legend3DParameters), 'Expected Legend3DParameters' \
                ' for properties_3d. Got {}.'.format(type(value))
        else:
            value = Legend3DParameters()
        self._properties_3d = value
        value._parent = self

    @property
    def base_plane(self):
        """Get or set a Plane for the base point and orientation of the 3D legend.
        """
        return self.properties_3d.base_plane

    @base_plane.setter
    def base_plane(self, base_pl):
        self.properties_3d.base_plane = base_pl

    @property
    def segment_height(self):
        """Get or set the height for each of the legend segments in 3D space."""
        return self.properties_3d.segment_height

    @segment_height.setter
    def segment_height(self, seg_h):
        self.properties_3d.segment_height = seg_h

    @property
    def segment_width(self):
        """Get or set the width for each of the legend segments in 3D space."""
        return self.properties_3d.segment_width

    @segment_width.setter
    def segment_width(self, seg_w):
        self.properties_3d.segment_width = seg_w

    @property
    def text_height(self):
        """Get or set the height for the legend text in 3D space."""
        return self.properties_3d.text_height

    @text_height.setter
    def text_height(self, txt_h):
        self.properties_3d.text_height = txt_h

    @property
    def properties_2d(self):
        """Get or set a Legend2DParameters for the properties of 2D legends."""
        return self._properties_2d

    @properties_2d.setter
    def properties_2d(self, value):
        if value is not None:
            assert isinstance(value, Legend2DParameters), 'Expected Legend2DParameters' \
                ' for properties_2d. Got {}.'.format(type(value))
        else:
            value = Legend2DParameters()
        self._properties_2d = value
        value._parent = self

    @property
    def origin_x(self):
        """Get or set text for the X coordinate from where the 2D legend will be drawn.
        """
        return self.properties_2d.origin_x

    @origin_x.setter
    def origin_x(self, value):
        self.properties_2d.origin_x = value

    @property
    def origin_y(self):
        """Get or set text for the Y coordinate from where the 2D legend will be drawn.
        """
        return self.properties_2d.origin_y

    @origin_y.setter
    def origin_y(self, value):
        self.properties_2d.origin_y = value

    @property
    def segment_height_2d(self):
        """Get or set the height for each of the legend segments in 2D space."""
        return self.properties_2d.segment_height

    @segment_height_2d.setter
    def segment_height_2d(self, seg_h):
        self.properties_2d.segment_height = seg_h

    @property
    def segment_width_2d(self):
        """Get or set the width for each of the legend segments in 2D space."""
        return self.properties_2d.segment_width

    @segment_width_2d.setter
    def segment_width_2d(self, seg_w):
        self.properties_2d.segment_width = seg_w

    @property
    def text_height_2d(self):
        """Get or set the height for the legend text in 2D space."""
        return self.properties_2d.text_height

    @text_height_2d.setter
    def text_height_2d(self, txt_h):
        self.properties_2d.text_height = txt_h

    @property
    def user_data(self):
        """Get or set an optional dictionary for additional meta data for this object.
        This will be None until it has been set. All keys and values of this
        dictionary should be of a standard Python type to ensure correct
        serialization of the object to/from JSON (eg. str, float, int, list, dict)
        """
        return self._user_data

    @user_data.setter
    def user_data(self, value):
        if value is not None:
            assert isinstance(value, dict), 'Expected dictionary for ' \
                'object user_data. Got {}.'.format(type(value))
        self._user_data = value

    @property
    def is_segment_count_default(self):
        """Boolean noting whether the number of segments is defaulted."""
        return self._is_segment_count_default

    @property
    def are_colors_default(self):
        """Boolean noting whether the colors are defaulted."""
        return self._are_colors_default

    @property
    def is_title_default(self):
        """Boolean noting whether the title is defaulted."""
        return self._is_title_default

    @property
    def is_base_plane_default(self):
        """Boolean noting whether the base plane in 3D space is defaulted."""
        return self.properties_3d.is_base_plane_default

    @property
    def is_segment_height_default(self):
        """Boolean noting whether the segment height in 3D space is defaulted."""
        return self.properties_3d.is_segment_height_default

    @property
    def is_segment_width_default(self):
        """Boolean noting whether the segment width in 3D space is defaulted."""
        return self.properties_3d.is_segment_width_default

    @property
    def is_text_height_default(self):
        """Boolean noting whether the text height in 3D space is defaulted."""
        return self.properties_3d.is_text_height_default

    @property
    def is_origin_x_default(self):
        """Boolean noting whether the X coordinate in 2D is defaulted."""
        return self.properties_2d.is_origin_x_default

    @property
    def is_origin_y_default(self):
        """Boolean noting whether the Y coordinate in 2D is defaulted."""
        return self.properties_2d.is_origin_y_default

    @property
    def is_segment_height_2d_default(self):
        """Boolean noting whether the segment height in 2D is defaulted."""
        return self.properties_2d.is_segment_height_default

    @property
    def is_segment_width_2d_default(self):
        """Boolean noting whether the segment width in 2D is defaulted."""
        return self.properties_2d.is_segment_width_default

    @property
    def is_text_height_2d_default(self):
        """Boolean noting whether the text height in 3D space is defaulted."""
        return self.properties_2d.is_text_height_default

    def colors_by_set(self, colorset_name):
        """Set the colors of this object using the name of a Colorset.

        This will also add the name of the color set to this LegendParameter's
        user_data.

        Args:
            colorset_name: The name of a Colorset to dictate the colors of this
                legend parameter object (eg. ecotect) (eg. benefit_harm). See
                the the ladybug Colorset object for a complete list of color sets.
        """
        col_method = getattr(Colorset, colorset_name)
        self.colors = col_method()
        if self._user_data is None:
            self.user_data = {'color_set': colorset_name}
        else:
            self._user_data['color_set'] = colorset_name

    def duplicate(self):
        """Return a copy of the current legend parameters."""
        return self.__copy__()

    def to_dict(self):
        """Get legend parameters as a dictionary."""
        base = self._base_dict()
        if self._min is not None:
            base['min'] = self.min
        if self._max is not None:
            base['max'] = self.max
        if not self.is_segment_count_default:
            base['segment_count'] = self.segment_count
        base['ordinal_dictionary'] = self.ordinal_dictionary
        base['type'] = 'LegendParameters'
        return base

    def _base_dict(self):
        """Get a dictionary with the base properties shared by all LegendParameters."""
        base = {
            'continuous_legend': self.continuous_legend,
            'decimal_count': self.decimal_count,
            'include_larger_smaller': self.include_larger_smaller,
            'vertical': self.vertical,
            'font': self.font
        }
        if not self.are_colors_default:
            base['colors'] = [c.to_dict() for c in self.colors]
        if not self.is_title_default:
            base['title'] = self.title
        if not self.properties_3d.is_default:
            base['properties_3d'] = self.properties_3d.to_dict()
        if not self.properties_2d.is_default:
            base['properties_2d'] = self.properties_2d.to_dict()
        if self.user_data is not None:
            base['user_data'] = self.user_data
        return base

    @staticmethod
    def _convert_colors(cols):
        """Convert a list of colors into ladybug Color objects."""
        try:
            cols = tuple(col if isinstance(col, Color) else Color(
                col.R, col.G, col.B) for col in cols)
        except Exception:
            try:
                cols = tuple(Color(col.Red, col.Green, col.Blue)
                             for col in cols)
            except Exception:
                raise ValueError("{} is not a valid list of colors".format(cols))
        return cols

    def __copy__(self):
        new_par = LegendParameters(
            self.min, self.max, self.segment_count, self.colors, self.title)
        new_par._continuous_legend = self._continuous_legend
        new_par._ordinal_dictionary = self._ordinal_dictionary
        new_par._decimal_count = self._decimal_count
        new_par._include_larger_smaller = self._include_larger_smaller
        new_par._vertical = self._vertical
        new_par._font = self._font
        new_par.properties_3d = self.properties_3d.duplicate()
        new_par.properties_2d = self.properties_2d.duplicate()
        new_par._user_data = None if self.user_data is None else self.user_data.copy()
        new_par._is_segment_count_default = self._is_segment_count_default
        new_par._are_colors_default = self._are_colors_default
        new_par._is_title_default = self._is_title_default
        return new_par

    def __key(self):
        return (
            self.min, self.max, self.segment_count, self.title,
            self._continuous_legend, self._ordinal_dictionary, self._decimal_count,
            self._include_larger_smaller, self._vertical, self._font,
            hash(self.properties_3d), hash(self.properties_2d),
            self._is_segment_count_default, self._are_colors_default,
            self._is_title_default
        ) + tuple(hash(col) for col in self.colors)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, LegendParameters) and self.__key() == other.__key()

    def __ne__(self, value):
        return not self.__eq__(value)

    def ToString(self):
        """Overwrite .NET ToString method."""
        return self.__repr__()

    def __repr__(self):
        """Legend parameter representation."""
        min = self.min if self.min is not None else '[default]'
        max = self.max if self.max is not None else '[default]'
        seg = '[default]' if self.is_segment_count_default \
            else self.segment_count
        title = '[default]' if self.is_title_default else self.title
        return 'Legend Parameters\n minimum: {}\n maximum: {}\n segments: {}\n' \
            ' colors:\n  {}\n continuous legend: {}\n' \
            ' title: {}\n ordinal text: {}\n number decimals: {}\n' \
            ' include < >: {}\n vertical: {}\n font: {}\n {}\n{}'.format(
                min, max, seg, '\n  '.join([str(c) for c in self.colors]),
                self.continuous_legend, title, self.ordinal_dictionary,
                self.decimal_count, self.include_larger_smaller,
                self.vertical, self.font, self.properties_3d, self.properties_2d)


class LegendParametersCategorized(LegendParameters):
    """Ladybug legend parameters used to customize legends.

    These legend parameters have more limitations than the base LegendParameters
    class. However, these legend parameters will do auto-categorization of data,
    binning values into groups based on custom ranges.

    Args:
        domain: A list of one or more numbers noting the boundaries of the data
            categories. For example, [100, 2000] creates three categories of
            (<100, 100-2000, >2000). Values must always be ordered from lowest
            to highest.
        colors: An list of color objects with a length equal to the number of items
            in the domain + 1. These are used to color each of the categories of data.
        category_names: An optional list of text strings with a length equal to the
            colors. These will be used to name each of the categories in the legend.
            If None, the legend text will simply mark the numerical ranges of the
            categories. (Default: None).
        title: Text string for Legend title. Typically, the units of the data are
            used here but the type of data might also be used. Default is
            an empty string.
        base_plane: A Ladybug Plane object to note the starting point from
            where the legend will be generated. The default is the world XY plane
            at origin (0, 0, 0).

    Properties:
        * domain
        * colors
        * category_names
        * continuous_colors
        * continuous_legend
        * title
        * ordinal_dictionary
        * decimal_count
        * include_larger_smaller
        * vertical
        * font
        * user_data

        * properties_3d
        * base_plane
        * segment_height
        * segment_width
        * text_height
        * properties_2d
        * origin_x
        * origin_y
        * segment_height_2d
        * segment_width_2d
        * text_height_2d

        * min
        * max
        * segment_count

        * is_title_default
        * is_base_plane_default
        * is_segment_height_default
        * is_segment_width_default
        * is_text_height_default
    """
    __slots__ = ('_domain', '_category_names', '_continuous_colors')

    def __init__(self, domain, colors, category_names=None, title=None, base_plane=None):
        """Initialize Ladybug Legend Parameters Categorized."""
        # set the domain after verifying that it is correct
        assert isinstance(domain, Iterable) \
            and not isinstance(domain, (str, dict, bytes, bytearray)), \
            'Domain should be a list or tuple. Got {}'.format(type(domain))
        self._domain = tuple(float(x) for x in sorted(domain))
        assert len(self._domain) > 0, \
            'LegendParametersCategorized domain must have at least one value.'
        self._min = self._domain[0]
        self._max = self._domain[-1]
        self._segment_count = len(self._domain) + 1

        # set the other init arguments
        self.colors = colors
        self.category_names = category_names
        self.title = title

        # set all of the other inputs to None/default
        self.continuous_colors = None
        self.continuous_legend = None
        self.decimal_count = None
        self.include_larger_smaller = None
        self.vertical = None
        self.font = None
        self._user_data = None

        # set the 3D and 2D properties
        self.properties_3d = Legend3DParameters(base_plane)
        self.properties_2d = Legend2DParameters()

        # properties that have no meaning for this class
        self._ordinal_dictionary = None
        self._is_segment_count_default = True
        self._are_colors_default = False

    @classmethod
    def from_dict(cls, data):
        """Create LegendParametersCategorized from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "type": "LegendParametersCategorized",
            "domain": [100, 2000],
            "colors": [{'r': 0, 'g': 0, 'b': 0},
                       {'r': 0, 'g': 0, 'b': 100},
                       {'r': 255, 'g': 0, 'b': 0}],
            "category_names": ["low", "desired", "high"]
            }
        """
        data = data.copy()  # copy to avoid mutating the input dictionary
        assert data['type'] == 'LegendParametersCategorized', \
            'Expected LegendParametersCategorized. Got {}.'.format(data['type'])
        default_dict = {'type': 'Default'}
        optional_keys = (
            'category_names', 'continuous_legend', 'continuous_colors', 'title',
            'decimal_count', 'include_larger_smaller', 'vertical', 'font',
            'properties_3d', 'properties_2d')
        for key in optional_keys:
            if key not in data:
                data[key] = None
            elif data[key] == default_dict:
                data[key] = None

        colors = [Color.from_dict(col) for col in data['colors']]

        leg_par = cls(data['domain'], colors, data['category_names'], data['title'])
        leg_par.continuous_colors = data['continuous_colors']
        leg_par.continuous_legend = data['continuous_legend']
        leg_par.decimal_count = data['decimal_count']
        leg_par.include_larger_smaller = data['include_larger_smaller']
        leg_par.vertical = data['vertical']
        leg_par.font = data['font']
        if data['properties_3d'] is not None:
            leg_par.properties_3d = Legend3DParameters.from_dict(data['properties_3d'])
        if data['properties_2d'] is not None:
            leg_par.properties_2d = Legend2DParameters.from_dict(data['properties_2d'])
        if 'user_data' in data and data['user_data'] is not None:
            leg_par.user_data = data['user_data']
        return leg_par

    @property
    def domain(self):
        """Get or set a list of numbers noting the boundaries of the data categories."""
        return self._domain

    @domain.setter
    def domain(self, dom):
        assert isinstance(dom, Iterable) \
            and not isinstance(dom, (str, dict, bytes, bytearray)), \
            'Domain should be a list or tuple. Got {}'.format(type(dom))
        self._domain = tuple(float(x) for x in sorted(dom))
        assert len(self._domain) == len(self._colors) - 1, 'The length of domain must' \
            'be one less than length of the colors for a LegendParametersCategorized.' \
            '{} != {} - 1'.format(len(self._domain), len(self._colors))
        self._min = self._domain[0]
        self._max = self._domain[-1]
        self._segment_count = len(self._domain) + 1

    @property
    def colors(self):
        """Get or set the colors defining the legend."""
        return self._colors

    @colors.setter
    def colors(self, cols):
        assert isinstance(cols, Iterable) \
            and not isinstance(cols, (str, dict, bytes, bytearray)), \
            'Colors should be a list or tuple. Got {}'.format(type(cols))
        self._colors = self._convert_colors(cols)
        assert len(self._colors) == len(self._domain) + 1, 'The length of colors must ' \
            'be one more than the length of domain for a LegendParametersCategorized.' \
            '{} != {} + 1'.format(len(self._colors), len(self._domain))

    @property
    def category_names(self):
        """Get or set a list of text for the names of the categories."""
        if self._category_names:  # user-specified category names
            return self._category_names
        # generate the category names based on the domain
        format_str = '%.{}f'.format(self.decimal_count)
        nums = [format_str % x for x in self.domain]
        mid_nums = tuple('{} - {}'.format(nums[i], nums[i + 1])
                         for i in xrange(len(nums) - 1))
        if self.include_larger_smaller:
            return ('<' + nums[0],) + mid_nums + ('>' + nums[-1],)
        return (nums[0],) + mid_nums + (nums[-1],)

    @category_names.setter
    def category_names(self, categories):
        if categories is not None:
            assert isinstance(categories, Iterable) \
                and not isinstance(categories, (str, dict, bytes, bytearray)), \
                'Category names should be a list or tuple. Got {}'.format(
                    type(categories))
            self._category_names = tuple(str(x) for x in categories)
            assert len(self._category_names) == len(self._domain) + 1, 'The length of ' \
                'category_names must be one more than length of the colors for a ' \
                'LegendParametersCategorized.{} != {} - 1'.format(
                    len(self._domain), len(self._colors))
        else:
            self._category_names = None

    @property
    def continuous_colors(self):
        """Boolean noting whether colors generated are continuous or discrete.

        If True, the colors generated from the corresponding legend will be in a
        continuous gradient. If False, they will be categorized in incremental
        groups according to the segment_count. (Default: False).
        """
        return self._continuous_colors

    @continuous_colors.setter
    def continuous_colors(self, cont_cols):
        if cont_cols is not None:
            assert isinstance(cont_cols, bool), \
                'Expected boolean for continuous_colors. Got {}.'.format(type(cont_cols))
            self._continuous_colors = cont_cols
        else:
            self._continuous_colors = False

    @property
    def include_larger_smaller(self):
        """Boolean noting whether > and < should be included in legend segment text."""
        return self._include_larger_smaller

    @include_larger_smaller.setter
    def include_larger_smaller(self, lg_sm):
        if lg_sm is not None:
            assert isinstance(lg_sm, bool), 'Expected boolean for ' \
                'include_larger_smaller. Got {}.'.format(type(lg_sm))
            self._include_larger_smaller = lg_sm
        else:
            self._include_larger_smaller = True

    @property
    def min(self):
        """Get legend minimum. This is derived from the domain."""
        return self._min

    @property
    def max(self):
        """Get legend maximum. This is derived from the domain."""
        return self._max

    @property
    def segment_count(self):
        """Get the number of segments in the legend.

        This is always equal to one more than the length of the domain."""
        return self._segment_count

    @property
    def ordinal_dictionary(self):
        """Always None for a LegendParametersCategorized."""
        return self._ordinal_dictionary

    def to_dict(self):
        """Get legend parameters categorized as a dictionary."""
        base = self._base_dict()
        base['type'] = 'LegendParametersCategorized'
        base['domain'] = self.domain
        base['category_names'] = self.category_names
        base['continuous_colors'] = self.continuous_colors
        return base

    def __copy__(self):
        new_par = LegendParametersCategorized(
            self._domain, self._colors, self._category_names, self.title)
        new_par._continuous_colors = self._continuous_colors
        new_par._continuous_legend = self._continuous_legend
        new_par._decimal_count = self._decimal_count
        new_par._include_larger_smaller = self._include_larger_smaller
        new_par._vertical = self._vertical
        new_par._font = self._font
        new_par.properties_3d = self.properties_3d.duplicate()
        new_par.properties_2d = self.properties_2d.duplicate()
        new_par._user_data = None if self.user_data is None else self.user_data.copy()
        new_par._is_title_default = self._is_title_default
        return new_par

    def __key(self):
        return (
            self._domain, self._category_names, self.title,
            self._continuous_colors, self._continuous_legend, self._decimal_count,
            self._include_larger_smaller, self._vertical, self._font,
            hash(self.properties_3d), hash(self.properties_2d), self._is_title_default
        ) + tuple(hash(col) for col in self.colors)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, LegendParametersCategorized) and \
            self.__key() == other.__key()

    def __ne__(self, value):
        return not self.__eq__(value)

    def __repr__(self):
        """Legend parameter representation."""
        title = '[default]' if self.is_title_default else self.title
        return 'Legend Parameters Categorized\n domain: {}\n colors:\n  {}\n' \
            ' category names\n  {}\n continuous colors: {}\n continuous legend: {}\n' \
            ' title: {}\n number decimals: {}\n' \
            ' include < >: {}\n vertical: {}\n font: {}\n {}\n{}'.format(
                self.domain,
                '\n  '.join([str(c) for c in self.colors]),
                '\n  '.join([str(c) for c in self.category_names]),
                self.continuous_colors, self.continuous_legend, title,
                self.decimal_count, self.include_larger_smaller, self.vertical,
                self.font, self.properties_3d, self.properties_2d)


class Legend3DParameters(object):
    """Object to customize the properties of legends in the 3D scene.

    Args:
        base_plane: A Ladybug Plane object to note the starting point from where
            the legend will be generated. If None, the default is the world XY plane
            at origin (0, 0, 0) unless the legend is assigned to a specific geometry,
            in which case the origin is in the lower right corner of the geometry
            bounding box for vertical legends and the upper right corner for
            horizontal legends.
        segment_height: A number to set the height for each of the legend segments. If
            None, the default is 1 unless the legend is assigned to a specific geometry,
            in which case it is automatically set to a value on an appropriate scale
            (some fraction of the bounding box around the geometry).
        segment_width: A number to set the width for each of the legend segments. If
            None, the default is 1 unless the legend is assigned to a specific geometry,
            in which case it is automatically set to a value on an appropriate scale
            (some fraction of the bounding box around the geometry).
        text_height: A number to set the height for the legend text. If None,
            the default is 1/3 of the segment_height.

    Properties:
        * base_plane
        * segment_height
        * segment_width
        * text_height

        * is_default
        * is_base_plane_default
        * is_segment_height_default
        * is_segment_width_default
        * is_text_height_default
    """
    __slots__ = (
        '_base_plane', '_segment_height', '_segment_width', '_text_height',
        '_is_base_plane_default', '_is_segment_height_default',
        '_is_segment_width_default', '_is_text_height_default', '_parent')

    def __init__(self, base_plane=None, segment_height=None, segment_width=None,
                 text_height=None):
        """Initialize Legend3DParameters."""
        self.base_plane = base_plane
        self.segment_height = segment_height
        self.segment_width = segment_width
        self.text_height = text_height
        self._parent = None

    @classmethod
    def from_dict(cls, data):
        """Create Legend3DParameters from a dictionary.

    Args:
        data: A python dictionary in the following format

    .. code-block:: python

            {
            "type": "Legend3DParameters",
            "base_plane": {"type": "Plane", "o": [11, 0, 0], "n": [0, 0, 1]},
            "segment_height": 0.5,
            "segment_width": 0.25,
            "text_height": 0.25
            }
        """
        data = data.copy()  # copy to avoid mutating the input dictionary
        assert data['type'] == 'Legend3DParameters', \
            'Expected Legend3DParameters. Got {}.'.format(data['type'])
        default_dict = {'type': 'Default'}
        optional_keys = ('base_plane', 'segment_height', 'segment_width', 'text_height')
        for key in optional_keys:
            if key not in data:
                data[key] = None
            elif data[key] == default_dict:
                data[key] = None
        base_plane = None
        if data['base_plane'] is not None:
            base_plane = Plane.from_dict(data['base_plane'])
        return cls(base_plane, data['segment_height'],
                   data['segment_width'], data['text_height'])

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
        """Get or set the height for each of the legend segments.

        The default is 1 unless the legend is assigned to a specific geometry,
        in which case it is automatically set to a value on an appropriate scale
        (some fraction of the bounding box around the geometry).
        """
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
        """Get or set the width for each of the legend segments.

        Default is 1 when legend is vertical. When horizontal, the default is
        text_height * (max_number_of_digits + 2) where max_number_of_digits is
        the number of digits displaying in the legend parameter max.
        """
        if self.is_segment_width_default and self._parent is not None and \
                not self._parent.vertical:
            return self.text_height * 5
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
        """Get or set the height for the legend text.

        Default is 1/3 of the segment_height.
        """
        if self.is_text_height_default:
            return self.segment_height * 0.33
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
    def is_base_plane_default(self):
        """Boolean noting whether the base plane is defaulted."""
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

    @property
    def is_default(self):
        """Boolean noting whether all properties are defaulted."""
        return all((
            self._is_base_plane_default, self._is_segment_height_default,
            self._is_segment_width_default, self._is_text_height_default
        ))

    def duplicate(self):
        """Return a copy of the current Legend3DParameters."""
        return self.__copy__()

    def to_dict(self):
        """Get Legend3DParameters as a dictionary."""
        base = {'type': 'Legend3DParameters'}
        if not self.is_base_plane_default:
            base['base_plane'] = self.base_plane.to_dict()
        if not self.is_segment_height_default:
            base['segment_height'] = self.segment_height
        if not self.is_segment_width_default:
            base['segment_width'] = self.segment_width
        if not self.is_text_height_default:
            base['text_height'] = self.text_height
        return base

    def __copy__(self):
        new_par = Legend3DParameters(
            self._base_plane, self._segment_height,
            self._segment_width, self._text_height)
        new_par._is_base_plane_default = self._is_base_plane_default
        new_par._is_segment_height_default = self._is_segment_height_default
        new_par._is_segment_width_default = self._is_segment_width_default
        new_par._is_text_height_default = self._is_text_height_default
        return new_par

    def __key(self):
        return (
            hash(self.base_plane), self._segment_height, self._segment_width,
            self._text_height, self._is_base_plane_default,
            self._is_segment_height_default, self._is_segment_width_default,
            self._is_text_height_default
        )

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, Legend3DParameters) and self.__key() == other.__key()

    def __ne__(self, value):
        return not self.__eq__(value)

    def ToString(self):
        """Overwrite .NET ToString method."""
        return self.__repr__()

    def __repr__(self):
        """Legend3DParameters representation."""
        base_pt = '[default]' if self.is_base_plane_default else self.base_plane.o
        seg_h = '[default]' if self.is_segment_height_default else self.segment_height
        seg_w = '[default]' if self.is_segment_width_default else self.segment_width
        txt_h = '[default]' if self.is_text_height_default else self.text_height
        return '3D Parameters\n  base point: {}\n' \
            '  segment height: {}\n  segment width: {}\n' \
            '  text height: {}'.format(base_pt, seg_h, seg_w, txt_h)


class Legend2DParameters(object):
    """Object to customize the properties of legends in the 2D plane of a screen.

    Args:
        origin_x: A text string to note the X coordinate of the base point from
            where the legend will be generated (assuming an origin in the upper-left
            corner of the screen with higher positive values of X moving to the right).
            Text must be formatted as an integer followed by either "px" (to denote
            the number of screen pixels) or "%" (to denote the percentage of the
            screen). Examples include 10px, 5%. The default is set to make the legend
            clearly visible on the screen (10px).
        origin_y: A text string to note the Y coordinate of the base point from
            where the legend will be generated (assuming an origin in the upper-left
            corner of the screen with higher positive values of Y moving downward).
            Text must be formatted as an integer followed by either "px" (to denote
            the number of screen pixels) or "%" (to denote the percentage of the
            screen). Examples include 10px, 5%. The default is set to make the legend
            clearly visible on the screen (50px).
        segment_height: A text string to note the height for each of the legend segments.
            Text must be formatted as an integer followed by either "px" (to
            denote the number of screen pixels) or "%" (to denote the percentage of the
            screen). Examples include 10px, 5%. The default is set to make most
            legends readable (25px for horizontal and 36px for vertical).
        segment_width: A text string to set the width for each of the legend segments.
            Text must be formatted as an integer followed by either "px" (to denote
            the number of screen pixels) or "%" (to denote the percentage of the
            screen). Examples include 10px, 5%. The default is set to make most
            legends readable (36px for horizontal and 25px for vertical).
        text_height: A text string to set the height for the legend text.
            Text must be formatted as an integer followed by either "px" (to denote
            the number of screen pixels) or "%" (to denote the percentage of the
            screen). Examples include 10px, 5%. Default is 12px.

    Properties:
        * origin_x
        * origin_y
        * segment_height
        * segment_width
        * text_height

        * is_default
        * is_origin_x_default
        * is_origin_y_default
        * is_segment_height_default
        * is_segment_width_default
        * is_text_height_default
    """
    __slots__ = (
        '_origin_x', '_origin_y', '_segment_height', '_segment_width', '_text_height',
        '_is_origin_x_default', '_is_origin_y_default', '_is_segment_height_default',
        '_is_segment_width_default', '_is_text_height_default', '_parent')
    VALID_DIM = re.compile(r'^\d*px|\d*%$')

    def __init__(self, origin_x=None, origin_y=None, segment_height=None,
                 segment_width=None, text_height=None):
        """Initialize Legend2DParameters."""
        self.origin_x = origin_x
        self.origin_y = origin_y
        self.segment_height = segment_height
        self.segment_width = segment_width
        self.text_height = text_height
        self._parent = None

    @classmethod
    def from_dict(cls, data):
        """Create Legend2DParameters from a dictionary.

    Args:
        data: A python dictionary in the following format

    .. code-block:: python

            {
            "type": "Legend2DParameters",
            "origin_x": "20px",
            "origin_y": "20px",
            "segment_height": "5%",
            "segment_width": "2%",
            "text_height": "3%"
            }
        """
        data = data.copy()  # copy to avoid mutating the input dictionary
        assert data['type'] == 'Legend2DParameters', \
            'Expected Legend2DParameters. Got {}.'.format(data['type'])
        default_dict = {'type': 'Default'}
        optional_keys = (
            'origin_x', 'origin_y', 'segment_height', 'segment_width', 'text_height')
        for key in optional_keys:
            if key not in data:
                data[key] = None
            elif data[key] == default_dict:
                data[key] = None
        return cls(data['origin_x'], data['origin_y'], data['segment_height'],
                   data['segment_width'], data['text_height'])

    @property
    def origin_x(self):
        """Get or set text to note the X coordinate from where the legend will be drawn.

        The default is set to make the legend clearly visible on the screen (10px).
        """
        return self._origin_x

    @origin_x.setter
    def origin_x(self, value):
        if value is not None:
            self.valid_dim_string(value, 'origin_x')
            self._origin_x = value
            self._is_origin_x_default = False
        else:
            self._origin_x = '10px'
            self._is_origin_x_default = True

    @property
    def origin_y(self):
        """Get or set text to note the Y coordinate from where the legend will be drawn.

        The default is set to make the legend clearly visible on the screen (50px).
        """
        return self._origin_y

    @origin_y.setter
    def origin_y(self, value):
        if value is not None:
            self.valid_dim_string(value, 'origin_y')
            self._origin_y = value
            self._is_origin_y_default = False
        else:
            self._origin_y = '50px'
            self._is_origin_y_default = True

    @property
    def segment_height(self):
        """Get or set the height for each of the legend segments.

        The default is set to make most legends readable (25px for horizontal
        and 36px for vertical).
        """
        if self.is_segment_height_default and self._parent is not None and \
                not self._parent.vertical:
            return '25px'
        return self._segment_height

    @segment_height.setter
    def segment_height(self, value):
        if value is not None:
            self.valid_dim_string(value, 'segment_height')
            self._segment_height = value
            self._is_segment_height_default = False
        else:
            self._segment_height = '36px'
            self._is_segment_height_default = True

    @property
    def segment_width(self):
        """Get or set the width for each of the legend segments.

        The default is set to make most legends readable (36px for horizontal
        and 25px for vertical).
        """
        if self.is_segment_width_default and self._parent is not None and \
                not self._parent.vertical:
            return '36px'
        return self._segment_width

    @segment_width.setter
    def segment_width(self, value):
        if value is not None:
            self.valid_dim_string(value, 'segment_width')
            self._segment_width = value
            self._is_segment_width_default = False
        else:
            self._segment_width = '25px'
            self._is_segment_width_default = True

    @property
    def text_height(self):
        """Get or set the height for the legend text."""
        return self._text_height

    @text_height.setter
    def text_height(self, value):
        if value is not None:
            self.valid_dim_string(value, 'text_height')
            self._text_height = value
            self._is_text_height_default = False
        else:
            self._text_height = '12px'
            self._is_text_height_default = True

    @property
    def is_origin_x_default(self):
        """Boolean noting whether the origin X coordinate is defaulted."""
        return self._is_origin_x_default

    @property
    def is_origin_y_default(self):
        """Boolean noting whether the origin Y coordinate is defaulted."""
        return self._is_origin_y_default

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

    @property
    def is_default(self):
        """Boolean noting whether all properties are defaulted."""
        return all((
            self._is_origin_x_default, self._is_origin_y_default,
            self._is_segment_height_default, self._is_segment_width_default,
            self._is_text_height_default
        ))

    def duplicate(self):
        """Return a copy of the current Legend2DParameters."""
        return self.__copy__()

    def to_dict(self):
        """Get Legend2DParameters as a dictionary."""
        base = {'type': 'Legend2DParameters'}
        if not self.is_origin_x_default:
            base['origin_x'] = self.origin_x
        if not self.is_origin_y_default:
            base['origin_y'] = self.origin_y
        if not self.is_segment_height_default:
            base['segment_height'] = self.segment_height
        if not self.is_segment_width_default:
            base['segment_width'] = self.segment_width
        if not self.is_text_height_default:
            base['text_height'] = self.text_height
        return base

    @staticmethod
    def valid_dim_string(dim_string, invalid_obj='Legend2DParameters',
                         raise_exception=True):
        """Check if a string is in a valid format for assigning 2D dimensions.

        Args:
            dim_string: Text to check if it fits the format for 2D dimensions.
            invalid_obj: An optional name of the object to be reported in the
                error message when raise_exception is True.
            raise_exception: Boolean to note whether an exception should be
                raised if the dim_string is not in the correct format. Otherwise,
                this method will simply return True/False for whether the string
                meets the format.
        """
        if Legend2DParameters.VALID_DIM.match(dim_string) is None:
            if not raise_exception:
                return False
            msg = 'Invalid specification for {}.\nString "{}" does not match the ' \
                'format expected for 2D dimensions. (eg. 10px, 5%)'.format(
                    invalid_obj, dim_string)
            raise ValueError(msg)
        return True

    def __copy__(self):
        new_par = Legend2DParameters(
            self._origin_x, self._origin_y, self._segment_height,
            self._segment_width, self._text_height)
        new_par._is_origin_x_default = self._is_origin_x_default
        new_par._is_origin_y_default = self._is_origin_y_default
        new_par._is_segment_height_default = self._is_segment_height_default
        new_par._is_segment_width_default = self._is_segment_width_default
        new_par._is_text_height_default = self._is_text_height_default
        return new_par

    def __key(self):
        return (
            self._origin_x, self._origin_y, self._segment_height, self._segment_width,
            self._text_height, self._is_origin_x_default, self._is_origin_y_default,
            self._is_segment_height_default, self._is_segment_width_default,
            self._is_text_height_default
        )

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, Legend2DParameters) and self.__key() == other.__key()

    def __ne__(self, value):
        return not self.__eq__(value)

    def ToString(self):
        """Overwrite .NET ToString method."""
        return self.__repr__()

    def __repr__(self):
        """Legend2DParameters representation."""
        origin_x = '[default]' if self.is_origin_x_default else self.origin_x
        origin_y = '[default]' if self.is_origin_y_default else self.origin_y
        seg_h = '[default]' if self.is_segment_height_default else self.segment_height
        seg_w = '[default]' if self.is_segment_width_default else self.segment_width
        txt_h = '[default]' if self.is_text_height_default else self.text_height
        return '2D Parameters\n  base point: ({}, {})\n' \
            '  segment height: {}\n  segment width: {}\n' \
            '  text height: {}'.format(origin_x, origin_y, seg_h, seg_w, txt_h)
