# coding=utf-8
import math

from ladybug.compass import Compass

from ladybug_geometry.geometry2d.pointvector import Point2D, Vector2D
from ladybug_geometry.geometry2d.line import LineSegment2D
from ladybug_geometry.geometry2d.arc import Arc2D
from ladybug_geometry.geometry3d.pointvector import Point3D


def test_init_compass():
    """Test the initialization of Compass and basic properties."""
    compass = Compass()

    str(compass)  # test the string representation
    hash(compass)  # test to be sure the compass is hash-able
    assert compass.radius == 100
    assert compass.center == Point2D()
    assert compass.north_angle == 0
    assert compass.north_vector == Vector2D(0, 1)
    assert compass.spacing_factor == 0.15
    assert compass.min_point.is_equivalent(Point2D(-115.0, -115.0), 0.01)
    assert compass.max_point.is_equivalent(Point2D(115.0, 115.0), 0.01)
    assert isinstance(compass.inner_boundary_circle, Arc2D)
    assert len(compass.all_boundary_circles) == 3
    for circ in compass.all_boundary_circles:
        assert isinstance(circ, Arc2D)
    assert len(compass.major_azimuth_points) == len(compass.MAJOR_AZIMUTHS)
    for pt in compass.major_azimuth_points:
        assert isinstance(pt, Point2D)
    assert len(compass.major_azimuth_ticks) == len(compass.MAJOR_AZIMUTHS)
    for lin in compass.major_azimuth_ticks:
        assert isinstance(lin, LineSegment2D)
    assert len(compass.minor_azimuth_points) == len(compass.MINOR_AZIMUTHS)
    for pt in compass.minor_azimuth_points:
        assert isinstance(pt, Point2D)
    assert len(compass.minor_azimuth_ticks) == len(compass.MINOR_AZIMUTHS)
    for lin in compass.minor_azimuth_ticks:
        assert isinstance(lin, LineSegment2D)
    assert isinstance(compass.min_point3d(), Point3D)
    assert isinstance(compass.max_point3d(), Point3D)


def test_compass_orthographic():
    """Test the orthographic properties of the Compass."""
    compass = Compass()

    assert len(compass.orthographic_altitude_points) == len(compass.ALTITUDES)
    for pt in compass.orthographic_altitude_points:
        assert isinstance(pt, Point2D)
    assert len(compass.orthographic_altitude_circles) == len(compass.ALTITUDES)
    for lin in compass.orthographic_altitude_circles:
        assert isinstance(lin, Arc2D)


def test_compass_stereographic():
    """Test the stereographic properties of the Compass."""
    compass = Compass()

    assert len(compass.stereographic_altitude_points) == len(compass.ALTITUDES)
    for pt in compass.stereographic_altitude_points:
        assert isinstance(pt, Point2D)
    assert len(compass.stereographic_altitude_circles) == len(compass.ALTITUDES)
    for lin in compass.stereographic_altitude_circles:
        assert isinstance(lin, Arc2D)


def test_point3d_to_equidistant():
    """Test the equidistant projection of 3D points to a 2D plane."""
    assert Compass.point3d_to_equidistant(Point3D(0, 0, 100)).is_equivalent(
        Point2D(0, 0), 0.01)
    assert Compass.point3d_to_equidistant(Point3D(100, 0, 0)).is_equivalent(
        Point2D(100, 0), 0.01)
    assert Compass.point3d_to_equidistant(Point3D(0, 100, 0)).is_equivalent(
        Point2D(0, 100), 0.01)

    half_radius = math.sqrt(0.5) * 100
    assert Compass.point3d_to_equidistant(
        Point3D(half_radius, 0, half_radius)).is_equivalent(
            Point2D(50, 0), 0.01)

    origin = Point3D(10, 20, 30)
    assert Compass.point3d_to_equidistant(
        Point3D(110, 20, 30), origin=origin).is_equivalent(
            Point2D(110, 20), 0.01)
    half_large_radius = math.sqrt(0.5) * 200
    assert Compass.point3d_to_equidistant(
        Point3D(0, half_large_radius, half_large_radius), radius=200).is_equivalent(
            Point2D(0, 100), 0.01)


def test_point3d_to_equisolid():
    """Test the equisolid projection of 3D points to a 2D plane."""
    assert Compass.point3d_to_equisolid(Point3D(0, 0, 100)).is_equivalent(
        Point2D(0, 0), 0.01)
    assert Compass.point3d_to_equisolid(Point3D(100, 0, 0)).is_equivalent(
        Point2D(100, 0), 0.01)
    assert Compass.point3d_to_equisolid(Point3D(0, 100, 0)).is_equivalent(
        Point2D(0, 100), 0.01)

    half_radius = math.sqrt(0.5) * 100
    expected_radius = \
        100 * math.sin(math.radians(45) / 2) / math.sin(math.pi / 4)
    assert Compass.point3d_to_equisolid(
        Point3D(half_radius, 0, half_radius)).is_equivalent(
            Point2D(expected_radius, 0), 0.01)

    origin = Point3D(10, 20, 30)
    assert Compass.point3d_to_equisolid(
        Point3D(110, 20, 30), origin=origin).is_equivalent(
            Point2D(110, 20), 0.01)
    half_large_radius = math.sqrt(0.5) * 200
    expected_large_radius = \
        200 * math.sin(math.radians(45) / 2) / math.sin(math.pi / 4)
    assert Compass.point3d_to_equisolid(
        Point3D(0, half_large_radius, half_large_radius), radius=200).is_equivalent(
            Point2D(0, expected_large_radius), 0.01)


def test_set_properties():
    """Test the initialization of Compass and basic properties."""
    compass = Compass()

    compass.radius = 200
    assert compass.radius == 200
    compass.center = Point2D(200, 0)
    assert compass.center == Point2D(200, 0)
    compass.north_angle = 10
    assert compass.north_angle == 10
    assert compass.north_vector != Vector2D(0, 1)
    compass.spacing_factor = 0.2
    assert compass.spacing_factor == 0.2
    assert compass.min_point.is_equivalent(Point2D(-40.0, -240.0), 0.01)
    assert compass.max_point.is_equivalent(Point2D(440.0, 240.0), 0.01)


def test_equality():
    """Test the equality and duplicatiion of of Compass objects."""
    compass = Compass(radius=100)
    compass_dup = compass.duplicate()
    compass_alt = Compass(radius=200)

    assert compass is compass
    assert compass is not compass_dup
    assert compass == compass_dup
    assert compass != compass_alt


def test_label_points_from_angles():
    """Test the label_points_from_angles method."""
    compass = Compass()
    angles = list(range(0, 360, 30))

    pts = compass.label_points_from_angles(angles)
    assert len(pts) == len(angles)
    for pt in pts:
        assert isinstance(pt, Point2D)

    lines = compass.ticks_from_angles(angles)
    assert len(lines) == len(angles)
    for lin in lines:
        assert isinstance(lin, LineSegment2D)
