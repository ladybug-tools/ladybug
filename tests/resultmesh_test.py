# coding=utf-8
from __future__ import division

from ladybug.resultmesh import ResultMesh
from ladybug.legend import Legend, LegendParameters
from ladybug.datatype.thermalcondition import PredictedMeanVote
from ladybug.datatype.temperature import Temperature

from ladybug_geometry.geometry3d.pointvector import Point3D
from ladybug_geometry.geometry3d.plane import Plane
from ladybug_geometry.geometry3d.mesh import Mesh3D
from ladybug_geometry.geometry2d.mesh import Mesh2D

import unittest
import pytest


class ResultMeshTestCase(unittest.TestCase):
    """Test for ResultMesh"""

    def test_init_result_mesh(self):
        """Test the initialization of ResultMesh objects."""
        mesh2d = Mesh2D.from_grid(num_x=2, num_y=2)
        mesh3d = Mesh3D.from_mesh2d(mesh2d)
        data = [0, 1, 2, 3]
        result_mesh = ResultMesh(data, mesh3d)

        str(result_mesh)  # Test the ResultMesh representation

        assert len(result_mesh) == 4
        assert result_mesh[0] == 0
        assert result_mesh[-1] == 3
        for item in result_mesh:
            assert isinstance(item, (float, int))

        assert len(result_mesh.values) == 4
        assert isinstance(result_mesh.colored_mesh, Mesh3D)
        assert isinstance(result_mesh.legend, Legend)
        assert result_mesh.colored_mesh.colors == result_mesh.legend.value_colors
        assert result_mesh.colored_mesh.is_color_by_face is True

        assert result_mesh.legend_parameters.is_base_plane_default is False
        assert result_mesh.legend_parameters.is_segment_height_default is False
        assert result_mesh.legend_parameters.is_segment_width_default is True
        assert result_mesh.legend_parameters.is_text_height_default is True
        assert result_mesh.legend_parameters.base_plane != Plane()

        assert isinstance(result_mesh.lower_title_location, Plane)
        assert isinstance(result_mesh.upper_title_location, Plane)
        assert result_mesh.lower_title_location != Plane()
        assert result_mesh.upper_title_location != Plane()

    def test_to_from_dict(self):
        """Test the to/from dict methods."""
        mesh2d = Mesh2D.from_grid(num_x=2, num_y=2)
        mesh3d = Mesh3D.from_mesh2d(mesh2d)
        data = [0, 1, 2, 3]
        result_mesh = ResultMesh(data, mesh3d)

        result_mesh_dict = result_mesh.to_dict()
        new_result_mesh = ResultMesh.from_dict(result_mesh_dict)
        assert new_result_mesh.to_dict() == result_mesh_dict

    def test_init_result_mesh_invalid(self):
        """Test the initialization of ResultMesh objects with invalid inputs."""
        mesh2d = Mesh2D.from_grid(num_x=2, num_y=2)
        mesh3d = Mesh3D.from_mesh2d(mesh2d)
        data = [0, 1, 2, 3, 4]

        with pytest.raises(Exception):
            ResultMesh(data, mesh3d)
        with pytest.raises(Exception):
            ResultMesh(data, mesh3d, data_type=Temperature(), unit='NotAUnit')

    def test_init_result_mesh_vertex_based(self):
        """Test the initialization of ResultMesh objects with vertex-based input."""
        mesh2d = Mesh2D.from_grid(num_x=2, num_y=2)
        mesh3d = Mesh3D.from_mesh2d(mesh2d)
        data = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        result_mesh = ResultMesh(data, mesh3d)

        assert len(result_mesh) == 9
        assert result_mesh[0] == 0
        assert result_mesh[-1] == 8

        assert len(result_mesh.values) == 9
        assert isinstance(result_mesh.colored_mesh, Mesh3D)
        assert isinstance(result_mesh.legend_parameters, LegendParameters)
        assert isinstance(result_mesh.legend, Legend)
        assert result_mesh.colored_mesh.colors == result_mesh.legend.value_colors
        assert result_mesh.colored_mesh.is_color_by_face is False

    def test_init_result_mesh_legend_parameters(self):
        """Test the initialization of ResultMesh objects with a LegendParameters."""
        mesh2d = Mesh2D.from_grid(num_x=2, num_y=2)
        mesh3d = Mesh3D.from_mesh2d(mesh2d)
        data = [-1, 0, 1, 2]
        legend_par = LegendParameters(vertical_or_horizontal=False,
                                      base_plane=Plane(o=Point3D(2, 2, 0)),
                                      segment_height=0.25, segment_width=0.5,
                                      text_height=0.15)
        result_mesh = ResultMesh(data, mesh3d, legend_par)

        assert result_mesh.legend_parameters.is_base_plane_default is False
        assert result_mesh.legend_parameters.is_segment_height_default is False
        assert result_mesh.legend_parameters.is_segment_width_default is False
        assert result_mesh.legend_parameters.is_text_height_default is False
        assert result_mesh.legend_parameters.vertical_or_horizontal is False
        assert result_mesh.legend_parameters.base_plane.o == Point3D(2, 2, 0)
        assert result_mesh.legend_parameters.segment_height == 0.25
        assert result_mesh.legend_parameters.segment_width == 0.5
        assert result_mesh.legend_parameters.text_height == 0.15

    def test_init_result_mesh_data_type(self):
        """Test the initialization of ResultMesh objects with a DataType."""
        mesh2d = Mesh2D.from_grid(num_x=2, num_y=2)
        mesh3d = Mesh3D.from_mesh2d(mesh2d)
        data = [-1, 0, 1, 2]
        result_mesh = ResultMesh(data, mesh3d, data_type=Temperature())

        assert result_mesh.legend_parameters.is_title_default is False
        assert result_mesh.legend_parameters.title == 'C'

        legend_par = LegendParameters(vertical_or_horizontal=False)
        result_mesh = ResultMesh(data, mesh3d, legend_par, data_type=Temperature())

        assert result_mesh.legend_parameters.is_title_default is False
        assert result_mesh.legend_parameters.title == 'Temperature (C)'

    def test_init_result_mesh_data_type_ordinal(self):
        """Test the ResultMesh objects with a DataType with unit_descr."""
        mesh2d = Mesh2D.from_grid(num_x=2, num_y=2)
        mesh3d = Mesh3D.from_mesh2d(mesh2d)
        data = [-1, 0, 1, 2]
        result_mesh = ResultMesh(data, mesh3d, data_type=PredictedMeanVote(), unit='PMV')

        assert result_mesh.legend_parameters.min == -3
        assert result_mesh.legend_parameters.max == 3
        assert result_mesh.legend_parameters.number_of_segments == 7
        assert result_mesh.legend_parameters.is_title_default is False
        assert result_mesh.legend_parameters.title == 'PMV'
        assert result_mesh.legend.segment_text == ['Cold', 'Cool', 'Slightly Cool',
                                                   'Neutral',
                                                   'Slightly Warm', 'Warm', 'Hot']


if __name__ == "__main__":
    unittest.main()
