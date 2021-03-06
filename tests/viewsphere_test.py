from ladybug_geometry.geometry3d.pointvector import Vector3D
from ladybug_geometry.geometry3d.mesh import Mesh3D

from ladybug.viewsphere import view_sphere

import pytest


def test_init_view_sphere():
    """Test the basic properties of the View Sphere."""
    str(view_sphere)  # Test the srt representation

    assert len(view_sphere.tregenza_dome_vectors) == 145
    assert all(isinstance(vec, Vector3D) for vec in view_sphere.tregenza_dome_vectors)
    assert len(view_sphere.tregenza_sphere_vectors) == 290
    assert isinstance(view_sphere.tregenza_dome_mesh, Mesh3D)
    assert len(view_sphere.tregenza_dome_mesh.faces) == 144 + 6
    assert isinstance(view_sphere.tregenza_dome_mesh_high_res, Mesh3D)
    assert len(view_sphere.tregenza_dome_mesh_high_res.faces) == 144 * 9 + 18
    assert isinstance(view_sphere.tregenza_sphere_mesh, Mesh3D)
    assert len(view_sphere.tregenza_sphere_mesh.faces) == (144 + 6) * 2
    assert len(view_sphere.reinhart_dome_vectors) == 577
    assert len(view_sphere.reinhart_sphere_vectors) == 577 * 2
    assert isinstance(view_sphere.reinhart_dome_mesh, Mesh3D)
    assert len(view_sphere.reinhart_dome_mesh.faces) == 576 + 12
    assert isinstance(view_sphere.reinhart_sphere_mesh, Mesh3D)
    assert len(view_sphere.reinhart_sphere_mesh.faces) == (576 + 12) * 2


def test_patch_weights():
    """Test the various patch_weights methods."""
    horiz_weights = view_sphere.horizontal_radial_patch_weights(30, 2)
    assert len(horiz_weights) == 576
    assert sum(horiz_weights) / len(horiz_weights) == pytest.approx(1, rel=1e-3)

    dome_weights = view_sphere.dome_patch_weights()
    assert len(dome_weights) == 145
    assert sum(dome_weights) / len(dome_weights) == pytest.approx(1, rel=1e-3)

    sphere_weights = view_sphere.sphere_patch_weights()
    assert len(sphere_weights) == 290
    assert sum(sphere_weights) / len(sphere_weights) == pytest.approx(1, rel=1e-3)


def test_horizontal_radial_vectors():
    view_vec = view_sphere.horizontal_radial_vectors(30)

    assert len(view_vec) == 30
    assert all(isinstance(vec, Vector3D) for vec in view_vec)


def test_horizontal_radial_patches():
    view_mesh, view_vec = view_sphere.horizontal_radial_patches(30, 2)

    assert len(view_vec) == 576
    assert all(isinstance(vec, Vector3D) for vec in view_vec)
    assert isinstance(view_mesh, Mesh3D)

    view_mesh, view_vec = view_sphere.horizontal_radial_patches(30, 2, True)

    assert len(view_vec) == 576
    assert all(isinstance(vec, Vector3D) for vec in view_vec)
    assert isinstance(view_mesh, Mesh3D)


def test_dome_radial_patches():
    view_mesh, view_vec = view_sphere.dome_radial_patches()
    assert len(view_vec) == 1296
    assert all(isinstance(vec, Vector3D) for vec in view_vec)
    assert isinstance(view_mesh, Mesh3D)

    view_mesh, view_vec = view_sphere.dome_radial_patches(72 * 2, 18 * 2)
    assert len(view_vec) == 1296 * 4
    assert all(isinstance(vec, Vector3D) for vec in view_vec)
    assert isinstance(view_mesh, Mesh3D)

    view_weights = view_sphere.dome_radial_patch_weights()
    assert len(view_weights) == 1296
    assert sum(view_weights) == pytest.approx(1, rel=1e-3)
