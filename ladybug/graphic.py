# coding=utf-8
from __future__ import division

from .legend import Legend, LegendParameters, LegendParametersCategorized

from .datatype.base import DataTypeBase

from ladybug_geometry.geometry2d.pointvector import Point2D
from ladybug_geometry.geometry3d.pointvector import Point3D
from ladybug_geometry.geometry3d.plane import Plane


class GraphicContainer(object):
    """Graphic container used to get legends, title locations, and colors for a graphic.

    Args:
        values: A List or Tuple of numerical values that will be used to
            generate the legend and colors.
        min_point: A Point3D object for the minimum of the bounding box around
            the graphic geometry.
        max_point: A Point3D object for the maximum of the  bounding box around
            the graphic geometry.
        legend_parameters: An Optional LegendParameter object to override default
            parameters of the legend. None indicates that default legend parameters
            will be used. (Default: None).
        data_type: Optional DataType from the ladybug datatype subpackage (ie.
            Temperature()) , which will be used to assign default legend properties.
            If None, the legend associated with this object will contain no units
            unless a unit below is specified. (Default: None).
        unit: Optional text string for the units of the values. (ie. 'C'). If None,
            the default units of the data_type will be used. (Default: None).

    Properties:
        * values
        * min_point
        * max_point
        * legend_parameters
        * data_type
        * unit
        * legend
        * value_colors
        * lower_title_location
        * upper_title_location
    """
    __slots__ = ('_legend', '_min_point', '_max_point', '_data_type', '_unit')

    def __init__(self, values, min_point, max_point,
                 legend_parameters=None, data_type=None, unit=None):
        """Initialize graphic container."""
        # check the input points and legend information
        if isinstance(min_point, Point2D):
            min_point = Point3D(min_point.x, min_point.y)
        if isinstance(max_point, Point2D):
            max_point = Point3D(max_point.x, max_point.y)
        assert isinstance(min_point, Point3D), \
            'min_point should be a ladybug Point3D. Got {}'.format(type(min_point))
        assert isinstance(max_point, Point3D), \
            'max_point should be a ladybug Point3D. Got {}'.format(type(max_point))
        self._legend = Legend(values, legend_parameters)
        self._min_point = min_point
        self._max_point = max_point

        # set default legend parameters based on input data_type and unit
        self._data_type = data_type
        self._unit = unit
        if data_type is not None:
            assert isinstance(data_type, DataTypeBase), \
                'data_type should be a ladybug DataType. Got {}'.format(type(data_type))
            if self.legend_parameters.is_title_default:
                unit = unit if unit else data_type.units[0]
                data_type.is_unit_acceptable(unit)
                self.legend_parameters.title = unit if \
                    self.legend_parameters.vertical \
                    else '{} ({})'.format(data_type.name, unit)
            if data_type.unit_descr is not None and \
                    self.legend_parameters.ordinal_dictionary is None and not \
                    isinstance(self.legend_parameters, LegendParametersCategorized):
                self.legend_parameters.ordinal_dictionary = data_type.unit_descr
                sorted_keys = sorted(data_type.unit_descr.keys())
                if self.legend.is_min_default:
                    self.legend_parameters._min = sorted_keys[0]
                if self.legend.is_max_default:
                    self.legend_parameters._max = sorted_keys[-1]
                assert self.legend_parameters._min <= self.legend_parameters._max, \
                    'Legend min is greater than legend max. {} > {}.'.format(
                        self.legend_parameters._min, self.legend_parameters._max)
                if self.legend_parameters.is_segment_count_default:
                    try:  # try to set the number of segments to align with ordinal text
                        min_i = sorted_keys.index(self.legend_parameters.min)
                        max_i = sorted_keys.index(self.legend_parameters.max)
                        self.legend_parameters.segment_count = \
                            len(sorted_keys[min_i:max_i + 1])
                    except IndexError:
                        pass
        elif unit and self.legend_parameters.is_title_default:
            assert isinstance(unit, str), \
                'Expected string for unit. Got {}.'.format(type(unit))
            self.legend_parameters.title = unit

        # set the default segment_height
        if self.legend_parameters.is_segment_height_default:
            s_count = self.legend_parameters.segment_count
            denom = s_count if s_count >= 8 else 8
            if self.legend_parameters.vertical:
                seg_height = float((self._max_point.y - self._min_point.y) / denom)
                if seg_height == 0:
                    seg_height = float((self._max_point.x - self._min_point.x) / denom)
            else:
                seg_height = float((self._max_point.x - self._min_point.x) / (denom * 2))
                if seg_height == 0:
                    seg_height = float((self._max_point.y - self._min_point.y) / denom)
            self.legend_parameters.properties_3d.segment_height = seg_height
            self.legend_parameters.properties_3d._is_segment_height_default = True

        # set the default segment_width
        if self.legend_parameters.is_segment_width_default:
            if self.legend_parameters.vertical:
                seg_width = self.legend_parameters.segment_height / 2
            else:
                seg_width = self.legend_parameters.text_height * \
                    (len(str(int(self.legend_parameters.max))) +
                     self.legend_parameters.decimal_count + 2)
            self.legend_parameters.properties_3d.segment_width = seg_width
            self.legend_parameters.properties_3d._is_segment_width_default = True

        # set the default base point
        if self.legend_parameters.is_base_plane_default:
            if self.legend_parameters.vertical:
                base_pt = Point3D(
                    self._max_point.x + self.legend_parameters.segment_width,
                    self._min_point.y, self._min_point.z)
            else:
                base_pt = Point3D(
                    self._max_point.x,
                    self._max_point.y + 3 * self.legend_parameters.text_height,
                    self._min_point.z)
            self.legend_parameters.properties_3d.base_plane = Plane(o=base_pt)
            self.legend_parameters.properties_3d._is_base_plane_default = True

    @classmethod
    def from_dict(cls, data):
        """Create a graphic container from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "values": [0, 10],
            "min_point": {"x": 0, "y": 0, "z": 0},
            "max_point": {"x": 10, "y": 10, "z": 0},
            "legend_parameters": {},  # optional LegendParameter specification
            "data_type": {},  # optional DataType object
            "unit": "C"  # optional text for the units
            }
        """
        legend_parameters = None
        if 'legend_parameters' in data and data['legend_parameters'] is not None:
            if data['legend_parameters']['type'] == 'LegendParametersCategorized':
                legend_parameters = LegendParametersCategorized.from_dict(
                    data['legend_parameters'])
            else:
                legend_parameters = LegendParameters.from_dict(data['legend_parameters'])

        data_type = None
        if 'data_type' in data and data['data_type'] is not None:
            data_type = DataTypeBase.from_dict(data['data_type'])
        unit = data['unit'] if 'unit' in data else None

        return cls(data['values'], Point3D.from_dict(data['min_point']),
                   Point3D.from_dict(data['max_point']),
                   legend_parameters, data_type, unit)

    @property
    def values(self):
        """The assigned data set of values."""
        return self._legend.values

    @property
    def min_point(self):
        """Point3D for the minimum of the bounding box around referenced geometry."""
        return self._min_point

    @property
    def max_point(self):
        """Point3D for the maximum of the bounding box around referenced geometry."""
        return self._max_point

    @property
    def legend_parameters(self):
        """The legend parameters assigned to this graphic."""
        return self._legend._legend_par

    @property
    def data_type(self):
        """The data_type input to this object (if it exists)."""
        return self._data_type

    @property
    def unit(self):
        """The unit input to this object (if it exists)."""
        return self._unit

    @property
    def legend(self):
        """The legend assigned to this graphic."""
        return self._legend

    @property
    def value_colors(self):
        """A List of colors associated with the assigned values."""
        return self._legend.value_colors

    @property
    def lower_title_location(self):
        """A Plane for the lower location of title text."""
        return Plane(o=Point3D(
            self._min_point.x,
            self._min_point.y - 2.5 * self._legend.legend_parameters.text_height,
            self._min_point.z))

    @property
    def upper_title_location(self):
        """A Plane for the upper location of title text."""
        return Plane(o=Point3D(
            self._min_point.x,
            self._max_point.y + self._legend.legend_parameters.text_height,
            self._min_point.z))

    def to_dict(self):
        """Get graphic container as a dictionary."""
        base = {
            'type': 'GraphicContainer',
            'values': self.values,
            'min_point': self.min_point.to_dict(),
            'max_point': self.max_point.to_dict(),
            'legend_parameters': self.legend_parameters.to_dict()
        }
        if self.data_type is not None:
            base['data_type'] = self.data_type.to_dict()
        if self.unit is not None:
            base['unit'] = self.unit
        return base

    def __len__(self):
        """Return length of values on the object."""
        return len(self._legend._values)

    def __getitem__(self, key):
        """Return one of the values."""
        return self._legend._values[key]

    def __iter__(self):
        """Iterate through the values."""
        return iter(self._legend._values)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """GraphicContainer representation."""
        return 'Graphic Container ({} values)'.format(len(self))
