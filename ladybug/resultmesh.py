# coding=utf-8
from __future__ import division

from .legend import Legend, LegendParameters

from .datatype.base import DataTypeBase

from ladybug_geometry.geometry3d.pointvector import Point3D
from ladybug_geometry.geometry3d.plane import Plane
from ladybug_geometry.geometry3d.mesh import Mesh3D


class ResultMesh(object):
    """Ladybug colored result mesh with legend.

    Properties:
        values
        colored_mesh
        legend_parameters
        legend
        value_colors
        lower_title_location
        upper_title_location
        data_type
        unit
    """

    def __init__(self, values, mesh, legend_parameters=None, data_type=None, unit=None):
        """Initialize result mesh.

        Initializing a legend and colored mesh this way will generate default
        legend base points, text points, and general scaling that makes sense
        given the input mesh.

        Args:
            values: A List or Tuple of numerical values that will be used to
                generate the legend and colors.
            mesh: A Mesh3D object, with a number of faces or vertices that
                match the number of input values and will be colored with
                restults.
            legend_parameters: An Optional LegendParameter object to override
                default parameters of the legend.
        """
        # check the inputs
        assert isinstance(mesh, Mesh3D), \
            'mesh should be a ladybug Mesh3D. Got {}'.format(type(mesh))
        assert len(values) == len(mesh.faces) or len(values) == len(mesh.vertices), \
            'Number of values ({}) does not match the number of' \
            ' mesh faces ({}) nor the number of vertices ({}).'.format(
                len(values), len(mesh.faces), len(mesh.vertices))
        self._mesh = mesh
        self._legend = Legend(values, legend_parameters)

        # set default legend parameters based on input data_type and unit
        self._data_type = data_type
        self._unit = unit
        if data_type is not None:
            assert isinstance(data_type, DataTypeBase), \
                'data_type should be a ladybug DataType. Got {}'.format(type(data_type))
            if self.legend_parameters.is_title_default:
                unit = data_type.units[0] if unit is None else unit
                data_type.is_unit_acceptable(unit)
                self.legend_parameters.title = unit if \
                    self.legend_parameters.vertical_or_horizontal is True \
                    else '{} ({})'.format(data_type.name, unit)
            if data_type.unit_descr is not None and \
                    self.legend_parameters.ordinal_dictionary is None:
                self.legend_parameters.ordinal_dictionary = data_type.unit_descr
                sorted_keys = sorted(data_type.unit_descr.keys())
                if self.legend.is_min_default is True:
                    self.legend_parameters.min = sorted_keys[0]
                if self.legend.is_max_default is True:
                    self.legend_parameters.max = sorted_keys[-1]
                if self.legend_parameters.is_number_of_segments_default:
                    try:  # try to set the number of segments to align with ordinal text
                        min_i = sorted_keys.index(self.legend_parameters.min)
                        max_i = sorted_keys.index(self.legend_parameters.max)
                        self.legend_parameters.number_of_segments = \
                            len(sorted_keys[min_i:max_i + 1])
                    except IndexError:
                        pass
        elif unit is not None and self.legend_parameters.is_title_default:
            assert isinstance(unit, str), \
                'Expected string for unit. Got {}.'.format(type(unit))
            self.legend_parameters.title = unit

        # get min and max points around the ladybug mesh
        self._min_pt = mesh.min
        self._max_pt = mesh.max

        # set the default segment_height
        if self.legend_parameters.is_segment_height_default:
            if self.legend_parameters.vertical_or_horizontal:
                seg_height = float((self._max_pt.y - self._min_pt.y) / 20)
            else:
                seg_height = float((self._max_pt.x - self._min_pt.x) / 20)
            self.legend_parameters.segment_height = seg_height

        # set the default base point
        if self.legend_parameters.is_base_plane_default:
            if self.legend_parameters.vertical_or_horizontal:
                base_pt = Point3D(
                    self._max_pt.x + self.legend_parameters.segment_width,
                    self._min_pt.y, self._min_pt.z)
            else:
                base_pt = Point3D(
                    self._max_pt.x, self._max_pt.y +
                    3 * self.legend_parameters.text_height,
                    self._min_pt.z)
            self.legend_parameters.base_plane = Plane(o=base_pt)

    @classmethod
    def from_json(cls, data):
        """Create a result mesh from a dictionary.

        Args:
            data: {
            "values": (0, 10),
            "mesh": {
                "vertices": [{"x": 0, "y": 0, "z": 0}, {"x": 10, "y": 0, "z": 0},
                             {"x": 0, "y": 10, "z": 0}, {"x": 10, "y": 10, "z": 0}],
                "faces": [(0, 1, 2), (3, 2, 1)]}
            "legend_parameters": None,
            "data_type": None,
            "unit": None}
        """
        optional_keys = ('legend_parameters', 'data_type', 'unit')
        for key in optional_keys:
            if key not in data:
                data[key] = None
        legend_parameters = None
        if data['legend_parameters'] is not None:
            legend_parameters = LegendParameters.from_json(data['legend_parameters'])
        data_type = None
        if data['data_type'] is not None:
            data_type = DataTypeBase.from_json(data['data_type'])

        return cls(data['values'], Mesh3D.from_dict(data['mesh']),
                   legend_parameters, data_type, data['unit'])

    @property
    def values(self):
        """The data set assigned to the mesh."""
        return self._legend.values

    @property
    def colored_mesh(self):
        """The input mesh colored with results."""
        self._mesh.colors = self.value_colors
        return self._mesh

    @property
    def legend_parameters(self):
        """The legend parameters assigned to this mesh."""
        return self._legend._legend_par

    @property
    def legend(self):
        """The legend assigned to this mesh."""
        return self._legend

    @property
    def value_colors(self):
        """A List of colors associated with the assigned values."""
        return self._legend.value_colors

    @property
    def lower_title_location(self):
        """A Plane for the lower location of title text."""
        return Plane(o=Point3D(
            self._min_pt.x,
            self._min_pt.y - 2 * self._legend.legend_parameters.text_height,
            self._min_pt.z))

    @property
    def upper_title_location(self):
        """A Plane for the upper location of title text."""
        return Plane(o=Point3D(
            self._min_pt.x,
            self._max_pt.y + self._legend.legend_parameters.text_height,
            self._min_pt.z))

    @property
    def data_type(self):
        """The data_type input to this object (if it exists)."""
        return self._data_type

    @property
    def unit(self):
        """The unit input to this object (if it exists)."""
        return self._unit

    def to_json(self):
        """Get result mesh as a dictionary."""
        self._mesh.colors = None  # we don't need to send the colors as they regenerate
        leg_par = None if self.legend.is_legend_parameters_default is True \
            else self.legend_parameters.to_json()
        data_type = None if self.data_type is None else self.data_type.to_json()
        return {'values': self.values,
                'mesh': self._mesh.to_dict(),
                'legend_parameters': leg_par,
                'data_type': data_type,
                'unit': self.unit}

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
        """ResultMesh representation."""
        return 'Ladybug Result Mesh ({} values)'.format(len(self))
