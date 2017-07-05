from color import ColorRange
from listoperations import flatten, unflatten


class LegendParameters(object):
    """Ladybug lagend parameters.

    Attributes:
        legendRange: Input a list of numbers or strings to set the boundary of
            legend. The default is ['min', 'max']
        numberOfSegments: An interger representing the number of steps between
            the high and low boundary of the legend. The default is set to 11
            and any custom values put in here should always be greater than or
            equal to 2.
        colors: An optional list of colors. Default is Ladybug's default colorset
        chartType: 0: continuous, 1: segmented, 2: ordinal. Default: 0.
            Ordinal values can be strings and well as numericals
        title:  Legend title. It's usually analysis unit
        font: An optional text string that sets the font of the text. Examples
            include "Arial", "Times New Roman" or "Courier" (all without
            quotations). The text input here can be any font that is on your
            computer but the font must be of an Editable file type (as seen in
            the font folder off of your control panel).  Font files that are
            Print and Preview will not work.  If you wish to use a Bold version
            of the font, include a ", Bold" at the end of the font name
            (example: "Arial, Bold").
        fontSize: An optional number to set the size of the text in model's units.
        scale: Input a number here to change the scale of the legend.
            The default is set to 1.
        basePlane: Input a plane to change the location and orientation of the
            legend. The default is set to the right of the analysis scene in
            XY plane.
        vertical: Set to False to get a horizontal legend. Default is vertical.

    Usage:

        lp = LegendParameters(legendRange = [2, 28])
        print lp.color(10)

    """

    _cType = {0: 'continuous', 1: 'segmented', 2: 'ordinal'}

    # TODO: Add textual and geometry parts
    def __init__(self, legendRange=None, numberOfSegments=11,
                 colors=None, chartType=0):
        """Init the class."""
        legendRange = legendRange or ['min', 'max']
        self.numberOfSegments = numberOfSegments or 11
        self.colorRange = ColorRange(colors=colors, domain=legendRange,
                                     chartType=chartType)

    @property
    def colors(self):
        """Get or set list of colors."""
        return self.colorRange.colors

    @colors.setter
    def colors(self, cols):
        self.colorRange.colors = cols

    @property
    def domain(self):
        """Get or set color range domain."""
        return self.colorRange.domain

    # TODO: set the domain based on the number of segments
    @domain.setter
    def domain(self, dom):
        self.colorRange.domain = dom

    @property
    def isDomainSet(self):
        """Check if the domain is set."""
        return self.colorRange.isDomainSet

    def setDomain(self, values):
        """Set domain of the colors based on min and max of a list of values."""
        _flattenedList = list(flatten(values))
        _flattenedList.sort()
        self.domain = tuple(_flattenedList[0] if d == 'min' else d for d in self.domain)
        self.domain = tuple(_flattenedList[-1] if d == 'max' else d for d in self.domain)

    def calculateColors(self, values):
        """Return a list (or list of lists) of colors based on input values."""
        # set domain if it is not set
        _flattenedList = list(flatten(values))
        if not self.isDomainSet:
            self.setDomain(_flattenedList)

        _flattenedColors = range(len(_flattenedList))
        for count, value in enumerate(_flattenedList):
            _flattenedColors[count] = self.calculateColor(value)

        return unflatten(values, iter(_flattenedColors))

    def calculateColor(self, value):
        """Calculate color for a specific value."""
        return self.colorRange.color(value)

    def geometry(self):
        """Calculate legend geometry."""
        raise NotImplementedError()

    def text(self):
        """Return legend text."""
        raise NotImplementedError()

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """Legend representation."""
        return "{} legend parameters".format(self._cType[self.colorRange.ctype])
