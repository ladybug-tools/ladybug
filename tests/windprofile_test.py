# coding=utf-8
from __future__ import division

import pytest

from ladybug_geometry.geometry3d import Vector3D, Point3D, LineSegment3D, \
    Plane, Polyline3D, Mesh3D

from ladybug.datacollection import HourlyContinuousCollection
from ladybug.epw import EPW
from ladybug.windprofile import WindProfile


def test_wind_profile_init():
    """Test the initialization of the wind profile and basic properties."""
    profile = WindProfile()

    str(profile)  # test the string representation
    assert profile.terrain == 'city'
    assert profile.meteorological_terrain == 'country'
    assert profile.meteorological_height == 10
    assert not profile.log_law
    assert profile.boundary_layer_height == 460
    assert profile.power_law_exponent == 0.33
    assert profile.roughness_length == 1.0
    assert profile.met_boundary_layer_height == 270
    assert profile.met_power_law_exponent == 0.14
    assert profile.met_roughness_length == 0.1

    assert profile.calculate_wind(5) == pytest.approx(1.0486989, rel=1e-3)


def test_wind_profile_calculate_wind_data():
    """Test the WindProfile.calculate_wind_data method."""
    profile = WindProfile('suburban')
    epw_file = './tests/assets/epw/chicago.epw'
    epw = EPW(epw_file)

    met_data = epw.wind_speed
    data_at_height = profile.calculate_wind_data(met_data, 1)

    assert isinstance(data_at_height, HourlyContinuousCollection)
    assert len(data_at_height) == 8760
    assert data_at_height.average < met_data.average


def test_wind_profile_polyline3d():
    """Test the profile_polyline3d."""
    profile = WindProfile('suburban')

    profile_polyline, wind_vectors, anchor_pts = profile.profile_polyline3d(5, 30, 2)

    assert isinstance(profile_polyline, Polyline3D)
    assert len(wind_vectors) == len(anchor_pts) == 16
    assert all(isinstance(vec, Vector3D) for vec in wind_vectors)
    assert all(isinstance(pt, Point3D) for pt in anchor_pts)


def test_mesh_arrow_profile():
    """Test the mesh_arrow_profile method."""
    profile = WindProfile('suburban')

    profile_polyline, mesh_arrows, wind_speeds, wind_vectors, anchor_pts = \
        profile.mesh_arrow_profile(5, 30, 2)

    assert isinstance(profile_polyline, Polyline3D)
    assert len(mesh_arrows) == len(wind_speeds) == 15
    assert all(isinstance(m, Mesh3D) for m in mesh_arrows)
    assert all(isinstance(v, (float, int)) for v in wind_speeds)
    assert len(wind_vectors) == len(anchor_pts) == 16
    assert all(isinstance(vec, Vector3D) for vec in wind_vectors)
    assert all(isinstance(pt, Point3D) for pt in anchor_pts)


def test_speed_axis():
    """Test the speed_axis method."""
    profile = WindProfile('suburban')

    axis_line, axis_arrow, axis_ticks, text_planes, text = profile.speed_axis(5)

    assert isinstance(axis_line, LineSegment3D)
    assert isinstance(axis_arrow, Mesh3D)
    assert len(axis_ticks) == 5
    assert len(text_planes) == len(text) == 6
    assert all(isinstance(t, LineSegment3D) for t in axis_ticks)
    assert all(isinstance(p, Plane) for p in text_planes)
    assert all(isinstance(t, str) for t in text)


def test_height_axis():
    """Test the height_axis method."""
    profile = WindProfile('suburban')

    axis_line, axis_arrow, axis_ticks, text_planes, text = profile.height_axis(30, 4)

    assert isinstance(axis_line, LineSegment3D)
    assert isinstance(axis_arrow, Mesh3D)
    assert len(axis_ticks) == 8
    assert len(text_planes) == len(text) == 9
    assert all(isinstance(t, LineSegment3D) for t in axis_ticks)
    assert all(isinstance(p, Plane) for p in text_planes)
    assert all(isinstance(t, str) for t in text)
