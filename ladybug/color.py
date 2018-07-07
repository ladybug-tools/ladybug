# coding=utf-8
"""Ladybug color, colorsets and colorrange."""


class Color(object):
    """Ladybug RGB color.

    Attributes:
        r: red value 0-255, default: 0
        g: green value 0-255, default: 0
        b: blue red value 0-255, default: 0
    """

    def __init__(self, r, g, b):
        """Generate RGB Color.

        Args:
            r: red value 0-255, default: 0
            g: green value 0-255, default: 0
            b: blue red value 0-255, default: 0
        """
        self.r = r
        self.g = g
        self.b = b

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

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """Return RGB values."""
        return "<R:%d, G:%d, B:%d>" % (self._r, self._g, self._b)


# TODO: Add support for CMYK
class Colorset(object):
    """Ladybug Color-range repository.

    A list of default Ladybug colorsets for color range:
        0 - original Ladybug
        1 - nuanced Ladybug
        2 - Multi-colored Ladybug
        3 - View Analysis 1
        4 - View Analysis 2 (Red,Green,Blue)
        5 - Sunlight Hours
        6 - ecotect
        7 - thermal Comfort Percentage
        8 - thermal Comfort Colors
        9 - thermal Comfort Colors (UTCI)
        10 - Hot Hours
        11 - Cold Hours
        12 - Shade Benefit/Harm
        13 - thermal Comfort Colors v2 (UTCI)
        14 - Shade Harm
        15 - Shade Benefit
        16 - Black to White
        17 - CFD Colors 1
        18 - CFD Colors 2
        19 - Energy Balance
        20 - THERM
        21 - Cloud Cover

    Usage:

        # initiare colorsets
        cs = Colorset()
        print(cs[0])
        >> [<R:75, G:107, B:169>, <R:115, G:147, B:202>, <R:170, G:200, B:247>,
            <R:193, G:213, B:208>, <R:245, G:239, B:103>, <R:252, G:230, B:74>,
            <R:239, G:156, B:21>, <R:234, G:123, B:0>, <R:234, G:74, B:0>,
            <R:234, G:38, B:0>]
    """
    _colors = {
        0: [(75, 107, 169), (115, 147, 202), (170, 200, 247), (193, 213, 208),
            (245, 239, 103), (252, 230, 74), (239, 156, 21), (234, 123, 0),
            (234, 74, 0), (234, 38, 0)],
        1: [(49, 54, 149), (69, 117, 180), (116, 173, 209), (171, 217, 233),
            (224, 243, 248), (255, 255, 191), (254, 224, 144), (253, 174, 97),
            (244, 109, 67), (215, 48, 39), (165, 0, 38)],
        2: [(4, 25, 145), (7, 48, 224), (7, 88, 255), (1, 232, 255),
            (97, 246, 156), (166, 249, 86), (254, 244, 1), (255, 121, 0),
            (239, 39, 0), (138, 17, 0)],
        3: [(255, 20, 147), (240, 47, 145), (203, 117, 139), (160, 196, 133),
            (132, 248, 129), (124, 253, 132), (96, 239, 160), (53, 217, 203),
            (15, 198, 240), (0, 191, 255)],
        4: [(0, 13, 255), (0, 41, 234), (0, 113, 181), (0, 194, 122),
            (0, 248, 82), (8, 247, 75), (64, 191, 58), (150, 105, 32),
            (225, 30, 9), (255, 0, 0)],
        5: [(55, 55, 55), (235, 235, 235)],
        6: [(0, 0, 255), (53, 0, 202), (107, 0, 148), (160, 0, 95), (214, 0, 41),
            (255, 12, 0), (255, 66, 0), (255, 119, 0), (255, 173, 0), (255, 226, 0),
            (255, 255, 0)],
        7: [(0, 0, 0), (110, 0, 153), (255, 0, 0), (255, 255, 102), (255, 255, 255)],
        8: [(0, 136, 255), (200, 225, 255), (255, 255, 255), (255, 230, 230),
            (255, 0, 0)],
        9: [(0, 136, 255), (67, 176, 255), (134, 215, 255), (174, 228, 255),
            (215, 242, 255), (255, 255, 255), (255, 243, 243), (255, 0, 0)],
        10: [(255, 255, 255), (255, 0, 0)],
        11: [(255, 255, 255), (0, 136, 255)],
        12: [(5, 48, 97), (33, 102, 172), (67, 147, 195), (146, 197, 222),
             (209, 229, 240), (255, 255, 255), (253, 219, 199), (244, 165, 130),
             (214, 96, 77), (178, 24, 43), (103, 0, 31)],
        13: [(5, 48, 97), (33, 102, 172), (67, 147, 195), (146, 197, 222),
             (209, 229, 240), (255, 255, 255), (244, 165, 130), (178, 24, 43)],
        14: [(255, 255, 255), (253, 219, 199), (244, 165, 130), (214, 96, 77),
             (178, 24, 43), (103, 0, 31)],
        15: [(255, 255, 255), (209, 229, 240), (146, 197, 222), (67, 147, 195),
             (33, 102, 172), (5, 48, 97)],
        16: [(0, 0, 0), (255, 255, 255)],
        17: [(0, 16, 120), (38, 70, 160), (5, 180, 222), (16, 180, 109),
             (59, 183, 35), (143, 209, 19), (228, 215, 29), (246, 147, 17),
             (243, 74, 0), (255, 0, 0)],
        18: [(69, 92, 166), (66, 128, 167), (62, 176, 168), (78, 181, 137),
             (120, 188, 59), (139, 184, 46), (197, 157, 54), (220, 144, 57),
             (228, 100, 59), (233, 68, 60)],
        19: [(138, 17, 0), (239, 39, 0), (255, 121, 0), (254, 244, 1),
             (166, 249, 86), (97, 246, 156), (1, 232, 255), (7, 88, 255),
             (4, 25, 145), (128, 102, 64)],
        20: [(0, 0, 0), (137, 0, 139), (218, 0, 218), (196, 0, 255), (0, 92, 255),
             (0, 198, 252), (0, 244, 215), (0, 220, 101), (7, 193, 0), (115, 220, 0),
             (249, 251, 0), (254, 178, 0), (253, 77, 0), (255, 15, 15),
             (255, 135, 135), (255, 255, 255)],
        21: [(0, 251, 255), (255, 255, 255), (217, 217, 217), (83, 114, 115)]
    }

    def __init__(self):
        """Initialize Color-sets."""
        pass

    @classmethod
    def original(cls):
        """original Ladybug colors."""
        return tuple(Color(*color) for color in cls._colors[0])

    @classmethod
    def nuanced(cls):
        """nuanced Ladybug colors."""
        return tuple(Color(*color) for color in cls._colors[1])

    @classmethod
    def multi_colored(cls):
        """Multi-colored legend."""
        return tuple(Color(*color) for color in cls._colors[2])

    @classmethod
    def view_analysis1(cls):
        """View analysis colors."""
        return tuple(Color(*color) for color in cls._colors[3])

    @classmethod
    def view_analysis2(cls):
        """View Analysis 2 colors."""
        return tuple(Color(*color) for color in cls._colors[4])

    @classmethod
    def sunlight_hours(cls):
        """sunlight_hours colors."""
        return tuple(Color(*color) for color in cls._colors[5])

    @classmethod
    def ecotect(cls):
        """ecotect colors."""
        return tuple(Color(*color) for color in cls._colors[6])

    @classmethod
    def thermal_comfort_percentage(cls):
        """thermal Comfort percentage."""
        return tuple(Color(*color) for color in cls._colors[7])

    @classmethod
    def thermal_comfort(cls):
        """thermal Comfort colors."""
        return tuple(Color(*color) for color in cls._colors[8])

    @classmethod
    def thermal_comfort_utci_1(cls):
        """thermal Comfort UTCI 1."""
        return tuple(Color(*color) for color in cls._colors[9])

    @classmethod
    def hot_hours(cls):
        """Hot Hours."""
        return tuple(Color(*color) for color in cls._colors[10])

    @classmethod
    def cold_hours(cls):
        """Cold Hours."""
        return tuple(Color(*color) for color in cls._colors[11])

    @classmethod
    def shade_benefit_harm(cls):
        """Shade Benefit Harm colors."""
        return tuple(Color(*color) for color in cls._colors[12])

    @classmethod
    def thermal_comfort_utci_2(cls):
        """thermal Comfort UTCI 2."""
        return tuple(Color(*color) for color in cls._colors[13])

    @classmethod
    def shade_harm(cls):
        """Shade Harm colors."""
        return tuple(Color(*color) for color in cls._colors[14])

    @classmethod
    def shade_benefit(cls):
        """Shade Benefit colors."""
        return tuple(Color(*color) for color in cls._colors[15])

    @classmethod
    def black_to_white(cls):
        """Black to white colors."""
        return tuple(Color(*color) for color in cls._colors[16])

    @classmethod
    def cfd_colors_1(cls):
        """CFD colors 1."""
        return tuple(Color(*color) for color in cls._colors[17])

    @classmethod
    def cfd_colors_2(cls):
        """CFD colors 2."""
        return tuple(Color(*color) for color in cls._colors[18])

    @classmethod
    def energy_balance(cls):
        """Energy Balance colors."""
        return tuple(Color(*color) for color in cls._colors[19])

    @classmethod
    def therm(cls):
        """THERM colors."""
        return tuple(Color(*color) for color in cls._colors[20])

    @classmethod
    def cloud_cover(cls):
        """Cloud Cover colors."""
        return tuple(Color(*color) for color in cls._colors[21])

    def __len__(self):
        """Return length of colors."""
        return len(self._colors)

    def __getitem__(self, key):
        """Return key item from the color list."""
        return [Color(*color) for color in self._colors[key]]

    def __setitem__(self, key, value):
        """Set a color to a new color in color list."""
        self._colors[key] = value

    def __delitem__(self, key):
        """Remove a color from the color list."""
        del self._colors[key]

    def __iter__(self):
        """Use colors to iterate."""
        return iter(self._colors)


class ColorRange(object):
    """Ladybug Color-range repository.

    A list of default Ladybug colorRanges

    Args:
        range:
        colors: A list of colors. Colors should be input as R, G, B values.
            Default: Colorset[1]
        domain: A list of numbers or strings. For numerical values it should be
            sorted from min to max. Default: ['min', 'max']
        chart_type: 0: continuous, 1: segmented, 2: ordinal. Default: 0
            In segmented and ordinal mode number of values should match number of colors
            Ordinal values can be strings and well as numericals
    Usage:
        ##
        colorRange = ColorRange(chart_type = 1)
        colorRange.domain = [100, 2000]
        colorRange.colors = [Color(75, 107, 169), Color(245, 239, 103),
            Color(234, 38, 0)]
        print(colorRange.color(99))
        print(colorRange.color(100))
        print(colorRange.color(2000))
        print(colorRange.color(2001))
        >> <R:75, G:107, B:169>
        >> <R:245, G:239, B:103>
        >> <R:245, G:239, B:103>
        >> <R:234, G:38, B:0>

        ##
        colorRange = ColorRange(chart_type = 1)
        colorRange.domain = [100, 2000]
        colorRange.colors = [Color(75, 107, 169), Color(245, 239, 103),
            Color(234, 38, 0)]
        colorRange.color(300)
        >> <R:245, G:239, B:103>

        ##
        colorRange = ColorRange(chart_type = 2)
        colorRange.domain = ["cold", "comfortable", "hot"]
        colorRange.colors = [Color(75, 107, 169), Color(245, 239, 103),
            Color(234, 38, 0)]
        colorRange.color("comfortable")
        >> <R:245, G:239, B:103>

    """

    # TODO: write a Color object
    def __init__(self, colors=None, domain=None, chart_type=0):
        """Initiate Ladybug color range."""
        self.ctype = chart_type
        self._is_domain_set = False
        self.colors = colors
        self.domain = domain

    @property
    def is_domain_set(self):
        """Return if Domain is set for this color-range."""
        return self._is_domain_set

    @property
    def domain(self):
        """Return domain."""
        return self._domain

    @domain.setter
    def domain(self, dom):
        # check and prepare domain
        if not dom:
            dom = [0, 1]

        if 'min' in dom or 'max' in dom:
            self._domain = dom
            self._is_domain_set = False
        else:
            assert hasattr(dom, "__iter__"), "Domain should be an iterable type."
            # if domain is numerical it should be sorted
            try:
                dom = sorted(map(float, dom))
            except ValueError:
                if self._ctype != 2:
                    print("Text domains can only be used in ordinal mode.\n" +
                          "Type is changed to ordinal.")
                    self.ctype == 2

            if self._ctype == 0:
                # continuous
                # if type is continuous domain can only be 2 values
                # or at least 1 value less than number of colors
                if len(dom) == 2:
                    # remap domain based on colors
                    _step = float(dom[1] - dom[0]) / (len(self._colors) - 1)
                    _n = dom[0]
                    dom = [_n + c * _step for c in range(len(self._colors))]

                assert len(self._colors) >= len(dom), \
                    "For continuous colors length of domain should be 2 or equal" \
                    " to number of colors"

            elif self._ctype == 1:
                # segmented
                # Number of colors should be at least one more than number
                # of domain Values
                assert len(self._colors) > len(dom), "Length of colors " + \
                    "should be more than domain values for segmented colors"

            self._domain = dom
            self._is_domain_set = True

    @property
    def colors(self):
        """Return list of colors."""
        return self._colors

    @colors.setter
    def colors(self, cols):
        if not cols:
            self._colors = Colorset()[1]
        else:
            assert hasattr(cols, "__iter__"), "Colors should be an iterable type"
            try:
                cols = [col if isinstance(col, Color) else Color(
                    col.R, col.G, col.B) for col in cols]
            except Exception:
                try:
                    cols = [Color(col.Red, col.Green, col.Blue) for col in cols]
                except Exception:
                    raise ValueError("%s is not a vlid color" % str(cols))
            self._colors = cols

    @property
    def ctype(self):
        """Chart type."""
        return self._ctype

    @ctype.setter
    def ctype(self, t):
        assert 0 <= int(t) <= 2, "Chart Type should be between 0-2\n" + \
            "0: continuous, 1: segmented, 2: ordinal"
        self._ctype = int(t)

    def color(self, value):
        """Return color for an input value."""
        assert self._is_domain_set, \
            "Domain is not set. Use self.domain to set the domain."

        if self._ctype == 2:
            # if ordinal map the value and color
            try:
                return self._colors[self._domain.index(value)]
            except ValueError:
                raise ValueError(
                    "%s is not a valid input for ordinal type.\n" % str(value) +
                    "List of valid values are %s" % ";".join(map(str, self._domain))
                )

        if value < self._domain[0]:
            return self._colors[0]
        if value > self._domain[-1]:
            return self._colors[-1]

        # find the index of the value in domain
        for count, d in enumerate(self._domain):
            if d <= value <= self._domain[count + 1]:
                if self._ctype == 0:
                    return self._cal_color(value, count)
                if self._ctype == 1:
                    return self._colors[count + 1]

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

    def __len__(self):
        """Return length of colors."""
        return len(self._colors)

    def __getitem__(self, key):
        """Return key item from the color list."""
        return self._colors[key]

    def __setitem__(self, key, value):
        """Set a color to a new color in color list."""
        self._colors[key] = value

    def __delitem__(self, key):
        """Remove a color from the color list."""
        del self._colors[key]

    def __iter__(self):
        """Use colors to iterate."""
        return iter(self._colors)
