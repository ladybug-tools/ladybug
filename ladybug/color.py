# coding=utf-8
"""Ladybug color, colorsets and colorrange."""
from __future__ import division

try:
    from collections.abc import Iterable  # python < 3.7
except ImportError:
    from collections import Iterable  # python >= 3.8


class Color(object):
    """Ladybug RGBA color.

    Args:
        r: red value 0-255, default: 0
        g: green value 0-255, default: 0
        b: blue red value 0-255, default: 0
        a: alpha value 0-255. Alpha defines the opacity as a number between 0 (fully
            transparent) and 255 (fully opaque). Default 255.

    Properties:
        * r
        * g
        * b
        * a
    """

    __slots__ = ("_r", "_g", "_b", "_a")

    def __init__(self, r=0, g=0, b=0, a=255):
        """Generate RGB Color.
        """
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    @classmethod
    def from_dict(cls, data):
        """Create a color from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

                {
                "r": 255,
                "g": 0,
                "b": 150,
                "a": 255
                }
        """
        a = data['a'] if 'a' in data else 255
        return cls(data['r'], data['g'], data['b'], a)

    @property
    def r(self):
        """Return R value."""
        return self._r

    @r.setter
    def r(self, value):
        assert 0 <= int(value) <= 255, "%d is out of range. " % value + \
            "R value should be between 0-255"
        self._r = int(value)

    @property
    def g(self):
        """Return G value."""
        return self._g

    @g.setter
    def g(self, value):
        assert 0 <= int(value) <= 255, "%d is out of range. " % value + \
            "G value should be between 0-255"
        self._g = int(value)

    @property
    def b(self):
        """Return B value."""
        return self._b

    @b.setter
    def b(self, value):
        assert 0 <= int(value) <= 255, "%d is out of range. " % value + \
            "B value should be between 0-255"
        self._b = int(value)

    @property
    def a(self):
        """Return A value."""
        return self._a

    @a.setter
    def a(self, value):
        assert 0 <= int(value) <= 255, "%d is out of range. " % value + \
            "B value should be between 0-255"
        self._a = int(value)

    def duplicate(self):
        """Return a copy of the current color."""
        return self.__copy__()

    def to_dict(self):
        """Get color as a dictionary."""
        return {
            'r': self.r,
            'g': self.g,
            'b': self.b,
            'a': self.a,
            'type': 'Color'
        }

    def __copy__(self):
        return self.__class__(self.r, self.g, self.b, self.a)

    def __eq__(self, other):
        if isinstance(other, Color):
            return self.r == other.r and self.g == other.g and self.b == other.b and \
                self.a == other.a
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.r, self.g, self.b, self.a))

    def __len__(self):
        return 4

    def __getitem__(self, key):
        return (self.r, self.g, self.b, self.a)[key]

    def __iter__(self):
        return iter((self.r, self.g, self.b, self.a))

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """Return RGB values."""
        return "(R:%d, G:%d, B:%d, A:%d)" % (self._r, self._g, self._b, self._a)


# TODO: Add support for CMYK
class Colorset(object):
    """Ladybug Color-range repository.

    A list of default Ladybug colorsets for color range:
        * 0 - original Ladybug
        * 1 - nuanced Ladybug
        * 2 - Multi-colored Ladybug
        * 3 - View Analysis 1
        * 4 - View Analysis 2 (Red,Green,Blue)
        * 5 - Sunlight Hours
        * 6 - ecotect
        * 7 - thermal Comfort Percentage
        * 8 - thermal Comfort Colors
        * 9 - thermal Comfort Colors (UTCI)
        * 10 - Hot Hours
        * 11 - Cold Hours
        * 12 - Shade Benefit/Harm
        * 13 - thermal Comfort Colors v2 (UTCI)
        * 14 - Shade Harm
        * 15 - Shade Benefit
        * 16 - Black to White
        * 17 - CFD Colors 1
        * 18 - CFD Colors 2
        * 19 - Energy Balance
        * 20 - THERM
        * 21 - Cloud Cover

    Usage:

    .. code-block:: python

        # initialize colorsets
        cs = Colorset()
        print(cs[0])
        >> [<R:75, G:107, B:169>, <R:115, G:147, B:202>, <R:170, G:200, B:247>,
            <R:193, G:213, B:208>, <R:245, G:239, B:103>, <R:252, G:230, B:74>,
            <R:239, G:156, B:21>, <R:234, G:123, B:0>, <R:234, G:74, B:0>,
            <R:234, G:38, B:0>]
    """
    # base color sets for which there are several variations
    _multicolored = [(4, 25, 145), (7, 48, 224), (7, 88, 255), (1, 232, 255),
                     (97, 246, 156), (166, 249, 86), (254, 244, 1), (255, 121, 0),
                     (239, 39, 0), (138, 17, 0)]
    _thermalcomfort = [(0, 136, 255), (200, 225, 255), (255, 255, 255),
                       (255, 230, 230), (255, 0, 0)]
    _benefitharm = [(0, 191, 48), (255, 238, 184), (255, 0, 0)]
    _shadebenefitharm = [(5, 48, 97), (33, 102, 172), (67, 147, 195), (146, 197, 222),
                         (209, 229, 240), (255, 255, 255), (253, 219, 199),
                         (244, 165, 130), (214, 96, 77), (178, 24, 43), (103, 0, 31)]

    # dictionary of all color sets together
    _colors = {
        0: [(75, 107, 169), (115, 147, 202), (170, 200, 247), (193, 213, 208),
            (245, 239, 103), (252, 230, 74), (239, 156, 21), (234, 123, 0),
            (234, 74, 0), (234, 38, 0)],
        1: [(49, 54, 149), (69, 117, 180), (116, 173, 209), (171, 217, 233),
            (224, 243, 248), (255, 255, 191), (254, 224, 144), (253, 174, 97),
            (244, 109, 67), (215, 48, 39), (165, 0, 38)],
        2: _multicolored,
        3: [(0, 0, 255), (53, 0, 202), (107, 0, 148), (160, 0, 95), (214, 0, 41),
            (255, 12, 0), (255, 66, 0), (255, 119, 0), (255, 173, 0), (255, 226, 0),
            (255, 255, 0)],
        4: [(255, 20, 147), (240, 47, 145), (203, 117, 139), (160, 196, 133),
            (132, 248, 129), (124, 253, 132), (96, 239, 160), (53, 217, 203),
            (15, 198, 240), (0, 191, 255)],
        5: [(55, 55, 55), (235, 235, 235)],
        6: [(156, 217, 255), (255, 243, 77), (255, 115, 0), (255, 0, 0), (0, 0, 0)],
        7: [(0, 0, 0), (110, 0, 153), (255, 0, 0), (255, 255, 102), (255, 255, 255)],
        8: _thermalcomfort,
        9: [(255, 251, 0), (255, 0, 0), (148, 24, 24), (135, 178, 224),
            (255, 175, 46), (255, 242, 140), (204, 204, 204)],
        10: _thermalcomfort[2:],
        11: list(reversed(_thermalcomfort[:3])),
        12: _benefitharm,
        13: _benefitharm[1:],
        14: list(reversed(_benefitharm[:2])),
        15: _shadebenefitharm,
        16: _shadebenefitharm[5:],
        17: list(reversed(_shadebenefitharm[:6])),
        18: list(reversed(_multicolored)),
        19: list(reversed(_multicolored)) + [(128, 102, 64)],
        20: [(0, 0, 0), (137, 0, 139), (218, 0, 218), (196, 0, 255), (0, 92, 255),
             (0, 198, 252), (0, 244, 215), (0, 220, 101), (7, 193, 0), (115, 220, 0),
             (249, 251, 0), (254, 178, 0), (253, 77, 0), (255, 15, 15),
             (255, 135, 135), (255, 255, 255)],
        21: [(0, 251, 255), (255, 255, 255), (217, 217, 217), (83, 114, 115)],
        22: [(0, 0, 0), (255, 255, 255)],
        23: [(0, 0, 255), (0, 255, 100), (255, 0, 0)],
        24: [(0, 16, 120), (38, 70, 160), (5, 180, 222), (16, 180, 109),
             (59, 183, 35), (143, 209, 19), (228, 215, 29), (246, 147, 17),
             (243, 74, 0), (255, 0, 0)],
        25: [(69, 92, 166), (66, 128, 167), (62, 176, 168), (78, 181, 137),
             (120, 188, 59), (139, 184, 46), (197, 157, 54), (220, 144, 57),
             (228, 100, 59), (233, 68, 60)],
        26: [(230, 180, 60), (230, 215, 150), (165, 82, 0),
             (128, 20, 20), (255, 128, 128), (64, 128, 128),
             (128, 128, 128), (255, 128, 128), (128, 64, 0),
             (64, 180, 255), (160, 150, 100), (120, 75, 190), (255, 255, 200),
             (0, 128, 0)]
    }

    def __init__(self):
        """Initialize Color-sets."""
        pass

    @classmethod
    def original(cls):
        """Original Ladybug colors."""
        return tuple(Color(*color) for color in cls._colors[0])

    @classmethod
    def nuanced(cls):
        """Nuanced Ladybug colors."""
        return tuple(Color(*color) for color in cls._colors[1])

    @classmethod
    def multi_colored(cls):
        """Multi-colored legend."""
        return tuple(Color(*color) for color in cls._colors[2])

    @classmethod
    def ecotect(cls):
        """Ecotect colors."""
        return tuple(Color(*color) for color in cls._colors[3])

    @classmethod
    def view_study(cls):
        """View analysis colors."""
        return tuple(Color(*color) for color in cls._colors[4])

    @classmethod
    def shadow_study(cls):
        """Shadow study colors (dark to light grey)."""
        return tuple(Color(*color) for color in cls._colors[5])

    @classmethod
    def glare_study(cls):
        """Useful for depicting spatial glare (light blue to yellow, red, black)."""
        return tuple(Color(*color) for color in cls._colors[6])

    @classmethod
    def annual_comfort(cls):
        """Good for annual metrics like UDI and thermal comfort percent."""
        return tuple(Color(*color) for color in cls._colors[7])

    @classmethod
    def thermal_comfort(cls):
        """Thermal comfort colors (blue to white to red)."""
        return tuple(Color(*color) for color in cls._colors[8])

    @classmethod
    def peak_load_balance(cls):
        """Colors for the typical terms of a peak load balance."""
        return tuple(Color(*color) for color in cls._colors[9])

    @classmethod
    def heat_sensation(cls):
        """Red colors for heat sensation."""
        return tuple(Color(*color) for color in cls._colors[10])

    @classmethod
    def cold_sensation(cls):
        """Blue colors for cold sensation."""
        return tuple(Color(*color) for color in cls._colors[11])

    @classmethod
    def benefit_harm(cls):
        """Benefit / harm study colors (red to light yellow to green)."""
        return tuple(Color(*color) for color in cls._colors[12])

    @classmethod
    def harm(cls):
        """Harm colors (light yellow to red)."""
        return tuple(Color(*color) for color in cls._colors[13])

    @classmethod
    def benefit(cls):
        """Benefit colors (light yellow to green)."""
        return tuple(Color(*color) for color in cls._colors[14])

    @classmethod
    def shade_benefit_harm(cls):
        """Shade benefit / harm colors (dark red to white to dark blue)."""
        return tuple(Color(*color) for color in cls._colors[15])

    @classmethod
    def shade_harm(cls):
        """Shade harm colors (white to dark red)."""
        return tuple(Color(*color) for color in cls._colors[16])

    @classmethod
    def shade_benefit(cls):
        """Shade benefit colors (white to dark blue)."""
        return tuple(Color(*color) for color in cls._colors[17])

    @classmethod
    def energy_balance(cls):
        """Energy Balance colors."""
        return tuple(Color(*color) for color in cls._colors[18])

    @classmethod
    def energy_balance_storage(cls):
        """Energy Balance colors with a brown color for storage term."""
        return tuple(Color(*color) for color in cls._colors[19])

    @classmethod
    def therm(cls):
        """THERM colors."""
        return tuple(Color(*color) for color in cls._colors[20])

    @classmethod
    def cloud_cover(cls):
        """Cloud cover colors."""
        return tuple(Color(*color) for color in cls._colors[21])

    @classmethod
    def black_to_white(cls):
        """Black to white colors."""
        return tuple(Color(*color) for color in cls._colors[22])

    @classmethod
    def blue_green_red(cls):
        """Blue to Green to Red colors."""
        return tuple(Color(*color) for color in cls._colors[23])

    @classmethod
    def multicolored_2(cls):
        """Multi-colored colors with less saturation."""
        return tuple(Color(*color) for color in cls._colors[24])

    @classmethod
    def multicolored_3(cls):
        """Multi-colored colors with the least saturation."""
        return tuple(Color(*color) for color in cls._colors[25])

    @classmethod
    def openstudio_palette(cls):
        """Standard color set for the OpenStudio surface types. Ordered as follows.

        Exterior Wall, Interior Wall, Underground Wall,
        Roof, Ceiling, Underground Roof,
        Exposed Floor, Interior Floor, Ground Floor,
        Window, Door, Shade, Air
        """
        return tuple(Color(*color) for color in cls._colors[26])

    def __len__(self):
        """Return length of currently installed color sets."""
        return len(self._colors)

    def __getitem__(self, key):
        """Return one of the color sets."""
        return tuple(Color(*color) for color in self._colors[key])

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """Colorset representation."""
        return "{} currently installed Colorsets".format(len(self))


class ColorRange(object):
    """Ladybug Color Range. Used to generate colors from numerical values.

    Args:
        colors: A list of colors. Colors should be input as objects with
            R, G, B values. Default is Ladybug's original colorset.
        domain: A list of at least two numbers to set the lower and upper
            boundary of the color range. This can also be a list of more than
            two values, which can be used to approximate logarithmic or other types
            of color scales. However, the number of values in the domain must
            always be less than or equal to the number of colors.
            Default: [0, 1].
        continuous_colors: Boolean. If True, the colors generated from the
            color range will be in a continuous gradient. If False,
            they will be categorized in incremental groups according to the
            number_of_segments. Default: True for continuous colors.

    Properties:
        * colors
        * continuous_colors
        * domain

    Usage:

    .. code-block:: python

        1.
            color_range = ColorRange(continuous_colors=False)
            color_range.domain = [100, 2000]
            color_range.colors = [Color(75, 107, 169), Color(245, 239, 103),
                Color(234, 38, 0)]
            print(color_range.color(99))
            print(color_range.color(100))
            print(color_range.color(2000))
            print(color_range.color(2001))
            >> (R:75, G:107, B:169)
            >> (R:245, G:239, B:103)
            >> (R:245, G:239, B:103)
            >> (R:234, G:38, B:0)

        2.
            color_range = ColorRange(continuous_colors=False)
            color_range.domain = [100, 2000]
            color_range.colors = [Color(75, 107, 169), Color(245, 239, 103),
                Color(234, 38, 0)]
            color_range.color(300)
            >> (R:245, G:239, B:103)
    """

    def __init__(self, colors=None, domain=None, continuous_colors=True):
        """Initiate Ladybug color range.
        """
        self._continuous_colors = True if continuous_colors is None \
            else continuous_colors
        assert isinstance(self._continuous_colors, bool), \
            "continuous_colors should be a Boolean.\nGot {}.".format(
                type(continuous_colors))
        self._is_domain_set = False
        self.colors = colors
        self.domain = domain

    @classmethod
    def from_dict(cls, data):
        """Create a color range from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "colors": [{'r': 0, 'g': 0, 'b': 0}, {'r': 255, 'g': 255, 'b': 255}],
            "domain": [0, 100],
            "continuous_colors": True
            }
        """
        optional_keys = ('colors', 'domain', 'continuous_colors')
        for key in optional_keys:
            if key not in data:
                data[key] = None
        colors = None
        if data['colors'] is not None:
            colors = [Color.from_dict(col) for col in data['colors']]

        return cls(colors, data['domain'], data['continuous_colors'])

    @property
    def colors(self):
        """Get or set the colors defining the color range."""
        return self._colors

    @colors.setter
    def colors(self, cols):
        if not cols:
            self._colors = Colorset.original()
        else:
            assert isinstance(cols, Iterable) \
                and not isinstance(cols, (str, dict, bytes, bytearray)), \
                'Colors should be a list or tuple. Got {}'.format(type(cols))
            try:
                cols = tuple(col if isinstance(col, Color) else Color(
                    col.R, col.G, col.B) for col in cols)
            except AttributeError:
                try:
                    cols = tuple(Color(col.Red, col.Green, col.Blue) for col in cols)
                except AttributeError:
                    raise ValueError("{} is not a valid list of colors".format(cols))
            if self._is_domain_set:
                self.domain = self.domain  # re-check the domain against new colors
            self._colors = cols

    @property
    def domain(self):
        """Get or set the domain defining the color range."""
        return self._domain

    @domain.setter
    def domain(self, dom):
        # check and prepare domain
        if not dom:
            dom = (0, 1)
        else:
            assert isinstance(dom, Iterable) \
                and not isinstance(dom, (str, dict, bytes, bytearray)), \
                'Domain should be a list or tuple. Got {}'.format(type(dom))
            for val in dom:
                assert isinstance(val, (float, int)), 'Values of a domain must be ' \
                    'numbers. Got {}.'.format(type(val))
            dom = sorted(map(float, dom))

        if self._continuous_colors:  # continuous
            # if type is continuous domain can only be 2 values
            # or at least 1 value less than number of colors
            if len(dom) == 2:
                # remap domain based on colors
                _step = float(dom[1] - dom[0]) / (len(self._colors) - 1)
                _n = dom[0]
                dom = tuple(_n + c * _step for c in range(len(self._colors)))
            else:
                assert len(self._colors) >= len(dom), \
                    "For a continuous color range, the length of the domain should " \
                    "be 2 or greater than the number of colors."
        else:  # segmented
            # Number of colors should be at least one more than number of domain values
            assert len(self._colors) > len(dom), \
                "For a segmented color range, the length of colors " + \
                "should be more than the number of domain values ."

        self._is_domain_set = True
        self._domain = tuple(dom)

    @property
    def continuous_colors(self):
        """Boolean noting whether colors generated are continuous or discrete."""
        return self._continuous_colors

    def color(self, value):
        """Calculate a color along the range for an input value."""
        if value < self._domain[0]:
            return self._colors[0]
        if value > self._domain[-1]:
            return self._colors[-1]

        # find the index of the value in domain
        for count, d in enumerate(self._domain):
            if d <= value <= self._domain[count + 1]:
                if self._continuous_colors:
                    return self._cal_color(value, count)
                else:
                    return self._colors[count + 1]

    def duplicate(self):
        """Return a copy of the current color range."""
        return self.__copy__()

    def to_dict(self):
        """Get color range as a dictionary."""
        return {
            'colors': [col.to_dict() for col in self.colors],
            'domain': self.domain,
            'continuous_colors': self.continuous_colors,
            'type': 'ColorRange'
        }

    def _cal_color(self, value, color_index):
        """Blend between two colors based on input value."""
        range_min_p = self._domain[color_index]
        range_p = self._domain[color_index + 1] - range_min_p
        try:
            factor = (value - range_min_p) / range_p
        except ZeroDivisionError:
            factor = 0

        min_color = self.colors[color_index]
        max_color = self.colors[color_index + 1]
        red = round(factor * (max_color.r - min_color.r) + min_color.r)
        green = round(factor * (max_color.g - min_color.g) + min_color.g)
        blue = round(factor * (max_color.b - min_color.b) + min_color.b)

        return Color(red, green, blue)

    def __copy__(self):
        return self.__class__(self.colors, self.domain, self.continuous_colors)

    def __len__(self):
        """Return length of colors."""
        return len(self._colors)

    def __getitem__(self, key):
        """Return key item from the color list."""
        return self._colors[key]

    def __iter__(self):
        """Use colors to iterate."""
        return iter(self._colors)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """Color Range representation."""
        return "Color Range ({} colors) (domain {})".format(len(self), self.domain)
