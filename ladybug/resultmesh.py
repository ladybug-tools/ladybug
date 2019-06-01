# coding=utf-8
from __future__ import division

from .legend import Legend

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
        self._mesh = mesh
        self._legend = Legend(values, legend_parameters)
        if data_type is not None:
            assert isinstance(data_type, DataTypeBase), \
                'data_type should be a ladybug DataType. Got {}'.format(type(data_type))
            if self._legend._legend_par.is_title_default:
                unit = data_type.units[0] if unit is None else unit
                data_type.is_unit_acceptable(unit)
                self._legend._legend_par.title = unit
            if data_type.unit_descr is not None and \
                    self._legend._legend_par.ordinal_dictionary is None:
                self._legend._legend_par.minordinal_dictionary = data_type.unit_descr
                sorted_keys = sorted(data_type.unit_descr.keys())
                if legend_parameters.min is None:
                    self._legend._legend_par.min = sorted_keys[0]
                if legend_parameters.max is None:
                    self._legend._legend_par.max = sorted_keys[-1]
        elif unit is not None and self._legend._legend_par.is_title_default:
            self._legend._legend_par.title = unit

        # get min and max points around the ladybug mesh
        self._min_pt = mesh.min
        self._max_pt = mesh.max

        # set the default segment_height
        if self._legend._legend_par.is_segment_height_default:
            if self._legend._legend_par.vertical_or_horizontal:
                seg_height = float((self._max_pt.y - self._min_pt.y) / 20)
            else:
                seg_height = float((self._max_pt.x - self._min_pt.x) / 20)
            self._legend._legend_par.segment_height = seg_height

        # set the default base point
        if self._legend._legend_par.is_base_plane_default:
            if self._legend._legend_par.vertical_or_horizontal:
                base_pt = Point3D(
                    self._max_pt.x + self._legend._legend_par.segment_width,
                    self._min_pt.y, self._min_pt.z)
            else:
                base_pt = Point3D(
                    self._max_pt.x, self._max_pt.y +
                    3 * self._legend._legend_par.text_height,
                    self._min_pt.z)
            self._legend._legend_par.base_plane = Plane(o=base_pt)

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

    def __len__(self):
        """Return length of values on the object."""
        return len(self._values)

    def __getitem__(self, key):
        """Return one of the values."""
        return self._values[key]

    def __iter__(self):
        """Iterate through the values."""
        return iter(self._values)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """ResultMesh representation."""
        return 'Ladybug Result Mesh ({} values)'.format(len(self))
