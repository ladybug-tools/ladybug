# coding=utf-8
from __future__ import division

from ladybug.graphic import GraphicContainer
from ladybug.legend import Legend, LegendParameters
from ladybug.datatype.thermalcondition import PredictedMeanVote
from ladybug.datatype.temperature import Temperature

from ladybug_geometry.geometry3d.pointvector import Point3D
from ladybug_geometry.geometry3d.plane import Plane
from ladybug_geometry.geometry3d.mesh import Mesh3D
from ladybug_geometry.geometry2d.mesh import Mesh2D

import pytest


def test_init_graphic_con():
    """Test the initialization of GraphicContainer objects."""
    mesh2d = Mesh2D.from_grid(num_x=2, num_y=2)
    mesh3d = Mesh3D.from_mesh2d(mesh2d)
    data = [0, 1, 2, 3]
    graphic_con = GraphicContainer(data, mesh3d.min, mesh3d.max)

    str(graphic_con)  # Test the GraphicContainer representation

    assert len(graphic_con) == 4
    assert graphic_con[0] == 0
    assert graphic_con[-1] == 3
    for item in graphic_con:
        assert isinstance(item, (float, int))

    assert len(graphic_con.values) == 4
    assert isinstance(graphic_con.legend, Legend)
    assert graphic_con.value_colors == graphic_con.legend.value_colors

    assert graphic_con.legend_parameters.is_base_plane_default
    assert graphic_con.legend_parameters.is_segment_height_default
    assert graphic_con.legend_parameters.is_segment_width_default
    assert graphic_con.legend_parameters.is_text_height_default
    assert graphic_con.legend_parameters.base_plane != Plane()

    assert isinstance(graphic_con.lower_title_location, Plane)
    assert isinstance(graphic_con.upper_title_location, Plane)
    assert graphic_con.lower_title_location != Plane()
    assert graphic_con.upper_title_location != Plane()


def test_to_from_dict():
    """Test the to/from dict methods."""
    mesh2d = Mesh2D.from_grid(num_x=2, num_y=2)
    mesh3d = Mesh3D.from_mesh2d(mesh2d)
    data = [0, 1, 2, 3]
    graphic_con = GraphicContainer(data, mesh3d.min, mesh3d.max)

    graphic_con_dict = graphic_con.to_dict()
    new_graphic_con = GraphicContainer.from_dict(graphic_con_dict)
    assert new_graphic_con.to_dict() == graphic_con_dict


def test_init_graphic_con_invalid():
    """Test the initialization of GraphicContainer objects with invalid inputs."""
    mesh2d = Mesh2D.from_grid(num_x=2, num_y=2)
    mesh3d = Mesh3D.from_mesh2d(mesh2d)
    data = [0, 1, 2, 3, 4]

    with pytest.raises(Exception):
        GraphicContainer(data, mesh3d.min, mesh3d.max,
                         data_type=Temperature(), unit='NotAUnit')


def test_init_graphic_con_vertex_based():
    """Test the initialization of GraphicContainer objects with vertex-based input."""
    mesh2d = Mesh2D.from_grid(num_x=2, num_y=2)
    mesh3d = Mesh3D.from_mesh2d(mesh2d)
    data = [0, 1, 2, 3, 4, 5, 6, 7, 8]
    graphic_con = GraphicContainer(data, mesh3d.min, mesh3d.max)

    assert len(graphic_con) == 9
    assert graphic_con[0] == 0
    assert graphic_con[-1] == 8

    assert len(graphic_con.values) == 9
    assert isinstance(graphic_con.legend_parameters, LegendParameters)
    assert isinstance(graphic_con.legend, Legend)
    assert graphic_con.value_colors == graphic_con.legend.value_colors


def test_init_graphic_con_legend_parameters():
    """Test the initialization of GraphicContainer objects with a LegendParameters."""
    mesh2d = Mesh2D.from_grid(num_x=2, num_y=2)
    mesh3d = Mesh3D.from_mesh2d(mesh2d)
    data = [-1, 0, 1, 2]
    legend_par = LegendParameters(base_plane=Plane(o=Point3D(2, 2, 0)))
    legend_par.vertical = False
    legend_par.segment_height = 0.25
    legend_par.segment_width = 0.5
    legend_par.text_height = 0.15
    graphic_con = GraphicContainer(data, mesh3d.min, mesh3d.max, legend_par)

    assert not graphic_con.legend_parameters.is_base_plane_default
    assert not graphic_con.legend_parameters.is_segment_height_default
    assert not graphic_con.legend_parameters.is_segment_width_default
    assert not graphic_con.legend_parameters.is_text_height_default
    assert not graphic_con.legend_parameters.vertical
    assert graphic_con.legend_parameters.base_plane.o == Point3D(2, 2, 0)
    assert graphic_con.legend_parameters.segment_height == 0.25
    assert graphic_con.legend_parameters.segment_width == 0.5
    assert graphic_con.legend_parameters.text_height == 0.15


def test_init_graphic_con_data_type():
    """Test the initialization of GraphicContainer objects with a DataType."""
    mesh2d = Mesh2D.from_grid(num_x=2, num_y=2)
    mesh3d = Mesh3D.from_mesh2d(mesh2d)
    data = [-1, 0, 1, 2]
    graphic_con = GraphicContainer(data, mesh3d.min, mesh3d.max,
                                   data_type=Temperature())

    assert not graphic_con.legend_parameters.is_title_default
    assert graphic_con.legend_parameters.title == 'C'

    legend_par = LegendParameters()
    legend_par.vertical = False
    graphic_con = GraphicContainer(data, mesh3d.min, mesh3d.max,
                                   legend_par, data_type=Temperature())

    assert not graphic_con.legend_parameters.is_title_default
    assert graphic_con.legend_parameters.title == 'Temperature (C)'


def test_init_graphic_con_data_type_ordinal():
    """Test the GraphicContainer objects with a DataType with unit_descr."""
    mesh2d = Mesh2D.from_grid(num_x=2, num_y=2)
    mesh3d = Mesh3D.from_mesh2d(mesh2d)
    data = [-1, 0, 1, 2]
    graphic_con = GraphicContainer(data, mesh3d.min, mesh3d.max,
                                   data_type=PredictedMeanVote(), unit='PMV')

    assert graphic_con.legend_parameters.min == -3
    assert graphic_con.legend_parameters.max == 3
    assert graphic_con.legend_parameters.segment_count == 7
    assert not graphic_con.legend_parameters.is_title_default
    assert graphic_con.legend_parameters.title == 'PMV'
    assert graphic_con.legend.segment_text == ['Cold', 'Cool', 'Slightly Cool',
                                               'Neutral',
                                               'Slightly Warm', 'Warm', 'Hot']


def test_graphic_con_data_type_ordinal_all_same():
    """Test the GraphicContainer with a DataType with unit_descr and all equal values."""
    mesh2d = Mesh2D.from_grid(num_x=2, num_y=2)
    mesh3d = Mesh3D.from_mesh2d(mesh2d)
    data = [0] * 3
    graphic_con = GraphicContainer(data, mesh3d.min, mesh3d.max,
                                   data_type=PredictedMeanVote(), unit='PMV')

    assert graphic_con.legend_parameters.min == -3
    assert graphic_con.legend_parameters.max == 3
    assert graphic_con.legend_parameters.segment_count == 7
    assert not graphic_con.legend_parameters.is_title_default
    assert graphic_con.legend_parameters.title == 'PMV'
    assert graphic_con.legend.segment_text == ['Cold', 'Cool', 'Slightly Cool',
                                               'Neutral',
                                               'Slightly Warm', 'Warm', 'Hot']
