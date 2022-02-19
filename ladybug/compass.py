# coding=utf-8
"""Module for computing geometry for the compass used by a variety of graphics."""
from __future__ import division

from ladybug_geometry.geometry2d.pointvector import Point2D, Vector2D
from ladybug_geometry.geometry2d.line import LineSegment2D
from ladybug_geometry.geometry2d.arc import Arc2D
from ladybug_geometry.geometry3d.pointvector import Point3D

import math


class Compass(object):
    """Object for computing geometry for the compass used by a variety of graphics.

    Methods to project points to orthograhpic and stereographic projectsions are
    also within this class so that "domed" visualizations can be synchronized with
    the compass in the 2D plane.

    Args:
        radius: A positive number for the radius of the compass. (Default: 100).
        center: A ladybug_geometry Point2D for the center of the compass
            in the scene. (Default: (0, 0) for the World origin).
        north_angle: A number between -360 and 360 for the counterclockwise
            difference between the North and the positive Y-axis in degrees.
            90 is West and 270 is East (Default: 0).
        spacing_factor: A positive number for the fraction of the radius that
            labels and tick marks occupy around the compass. (Default: 0.15)

    Properties:
        * radius
        * center
        * north_angle
        * north_vector
        * spacing_factor
        * min_point
        * max_point
        * inner_boundary_circle
        * all_boundary_circles
        * major_azimuth_points
        * major_azimuth_ticks
        * minor_azimuth_points
        * minor_azimuth_ticks
        * orthographic_altitude_circles
        * orthographic_altitude_points
        * stereographic_altitude_circles
        * stereographic_altitude_points
    """
    __slots__ = ('_radius', '_center', '_north_angle', '_north_vector',
                 '_spacing_factor')

    MAJOR_AZIMUTHS = (0, 90, 180, 270)
    MAJOR_TEXT = ('N', 'E', 'S', 'W')
    MINOR_AZIMUTHS = (22.5, 45, 67.5, 112.5, 135, 157.5, 202.5, 225, 247.5,
                      292.5, 315, 337.5)
    MINOR_TEXT = ('NNE', 'NE', 'ENE', 'ESE', 'SE', 'SSE', 'SSW', 'SW', 'WSW',
                  'WNW', 'NW', 'NNW')
    ALTITUDES = (10, 20, 30, 40, 50, 60, 70, 80)
    PI = math.pi

    def __init__(self, radius=100, center=Point2D(), north_angle=0,
                 spacing_factor=0.15):
        """Initialize Compass."""
        self.radius = radius
        self.center = center
        self.north_angle = north_angle
        self.spacing_factor = spacing_factor

    @property
    def radius(self):
        """Get or set a positive number for the radius of the compass."""
        return self._radius

    @radius.setter
    def radius(self, value):
        self._radius = float(value)
        assert self._radius > 0, \
            'Compass radius must be a positive number. Got {}.'.format(value)

    @property
    def center(self):
        """Get or set a Point2D for the center of the compass in the scene."""
        return self._center

    @center.setter
    def center(self, value):
        assert isinstance(value, Point2D), 'Expected ladybug_geometry Point2D ' \
            'for Compass center. Got {}.'.format(type(value))
        self._center = value

    @property
    def north_angle(self):
        """Get or set a number between -360 and 360 for the north_angle in degrees."""
        return math.degrees(self._north_angle)

    @north_angle.setter
    def north_angle(self, value):
        self._north_angle = math.radians(float(value))
        self._north_vector = Vector2D(0, 1).rotate(math.radians(-self._north_angle))
        assert -self.PI * 2 <= self._north_angle <= self.PI * 2, \
            'north_angle value should be between -360 and 360. Got {}.'.format(value)

    @property
    def north_vector(self):
        """Get or set a ladybug_geometry Vector2D for the north direction."""
        return self._north_vector

    @north_vector.setter
    def north_vector(self, value):
        assert isinstance(value, Vector2D), \
            'Expected Vector2D for north_vector. Got {}.'.format(type(value))
        self._north_vector = value
        self._north_angle = \
            math.degrees(Vector2D(0, 1).angle_clockwise(self._north_vector))

    @property
    def spacing_factor(self):
        """Get or set a number for the fraction of radius occupied by labels and ticks.
        """
        return self._spacing_factor

    @spacing_factor.setter
    def spacing_factor(self, value):
        self._spacing_factor = float(value)
        assert self._spacing_factor > 0, \
            'Compass spacing_factor must be a positive number. Got {}.'.format(value)

    @property
    def min_point(self):
        """Get a Point2D for the minimum around the entire compass."""
        fac = (1 + self.spacing_factor) * self.radius
        return Point2D(self.center.x - fac, self.center.y - fac)

    @property
    def max_point(self):
        """Get a Point2D for the minimum around the entire compass."""
        fac = (1 + self.spacing_factor) * self.radius
        return Point2D(self.center.x + fac, self.center.y + fac)

    @property
    def inner_boundary_circle(self):
        """Get a Arc2D for the inner circle of the compass.

        This is essentially a circle with the compass radius.
        """
        return Arc2D(self.center, self.radius)

    @property
    def all_boundary_circles(self):
        """Get an array of 3 Arc2Ds for the circles of the compass."""
        arc2 = Arc2D(self.center, self.radius * (1 + self.spacing_factor * 0.1))
        arc3 = Arc2D(self.center, self.radius * (1 + self.spacing_factor * 0.3))
        return [self.inner_boundary_circle, arc2, arc3]

    @property
    def major_azimuth_points(self):
        """Get a list of Point2Ds for the major azimuth labels."""
        return self.label_points_from_angles(self.MAJOR_AZIMUTHS)

    @property
    def major_azimuth_ticks(self):
        """Get a list of LineSegment2Ds for the major azimuth labels."""
        return self.ticks_from_angles(self.MAJOR_AZIMUTHS, 0.5)

    @property
    def minor_azimuth_points(self):
        """Get a list of Point2Ds for the minor azimuth labels."""
        return self.label_points_from_angles(self.MINOR_AZIMUTHS)

    @property
    def minor_azimuth_ticks(self):
        """Get a list of LineSegment2Ds for the minor azimuth labels."""
        return self.ticks_from_angles(self.MINOR_AZIMUTHS, 0.3)

    @property
    def orthographic_altitude_circles(self):
        """Get a list of circles for the orthographic altitude labels."""
        circles = []
        for angle in self.ALTITUDES:
            circles.append(
                Arc2D(self.center, self.radius * math.cos(math.radians(angle)))
            )
        return circles

    @property
    def orthographic_altitude_points(self):
        """Get a list of Point2Ds for the orthographic altitude labels."""
        pts = []
        for angle in self.ALTITUDES:
            spacing_fac = self.radius * 0.01  # spacing factor
            add_y = (self.radius * math.cos(math.radians(angle))) - spacing_fac
            pts.append(Point2D(self.center.x, self.center.y + add_y))
        if self._north_angle != 0:
            pts = [pt.rotate(self._north_angle, self.center) for pt in pts]
        return pts

    @property
    def stereographic_altitude_circles(self):
        """Get a list of circles for the stereographic altitude labels."""
        circles = []
        for angle in self.ALTITUDES:
            ang = math.radians(angle)
            pt3d = Point3D(math.cos(ang), 0, math.sin(ang))
            radius = self.point3d_to_stereographic(pt3d, 1).x * self.radius
            circles.append(Arc2D(self.center, radius))
        return circles

    @property
    def stereographic_altitude_points(self):
        """Get a list of Point2Ds for the stereographic altitude labels."""
        pts = []
        for angle in self.ALTITUDES:
            spacing_fac = self.radius * 0.01  # spacing factor
            ang = math.radians(angle)
            pt3d = Point3D(math.cos(ang), 0, math.sin(ang))
            add_y = (self.point3d_to_stereographic(pt3d, 1).x * self.radius) \
                - spacing_fac
            pts.append(Point2D(self.center.x, self.center.y + add_y))
        if self._north_angle != 0:
            pts = [pt.rotate(self._north_angle, self.center) for pt in pts]
        return pts

    def label_points_from_angles(self, angles, factor=0.8):
        """Get a list of label points from a list of angles between 0 and 360.

        Args:
            angles: An array of numbers between 0 and 360 for the angles of
                custom angle labels to be generated for the compass.
            factor: A number between 0 and 1 for the fraction of the spacing_factor
                at which the points should be generated.
        """
        circle = Arc2D(self.center, self.radius * (1 + self.spacing_factor * factor))
        return [circle.point_at_angle(self._north_angle - math.radians(angle - 90))
                for angle in angles]

    def ticks_from_angles(self, angles, factor=0.3):
        """Get a list of Linesegment2Ds from a list of angles between 0 and 360."""
        pts_in = self.label_points_from_angles(angles, 0)
        pts_out = self.label_points_from_angles(angles, factor)
        return [LineSegment2D.from_end_points(pi, po) for pi, po in zip(pts_in, pts_out)]

    def min_point3d(self, z=0):
        """Get a Point3D for the minimum around the entire compass."""
        min_pt = self.min_point
        return Point3D(min_pt.x, min_pt.y, z)

    def max_point3d(self, z=0):
        """Get a Point3D for the minimum around the entire compass."""
        max_pt = self.max_point
        return Point3D(max_pt.x, max_pt.y, z)

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    @staticmethod
    def point3d_to_orthographic(point):
        """Get a Point2D for a given Point3D using a orthographic projection.

        Args:
            point: A ladybug_geometry Point3D to be projected into 2D space via
                stereographic projection.
        """
        return Point2D(point.x, point.y)

    @staticmethod
    def point3d_to_stereographic(point, radius=100, origin=Point3D()):
        """Get a Point2D for a given Point3D using a stereographic projection.

        Args:
            point: A ladybug_geometry Point3D to be projected into 2D space via
                stereographic projection.
            radius: A positive number for the radius of the sphere on which the
                point exists. (Default: 100).
            origin: An optional ladybug_geometry Point3D representing the origin
                of the coordinate system in which the projection is happening.
                (eg. the center of the compass).
        """
        # move the point to the world origin
        coords = ((point.x - origin.x), (point.y - origin.y), (point.z - origin.z))
        # perform the stereographic projection while scaling it to the unit sphere
        proj_pt = (coords[0] / (radius + coords[2]), coords[1] / (radius + coords[2]))
        # move the point back to its original location and scale
        return Point2D(proj_pt[0] * radius + origin.x, proj_pt[1] * radius + origin.y)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.radius, hash(self.center), self.north_angle, self.spacing_factor)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, Compass) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __copy__(self):
        return Compass(self.radius, self.center, self.north_angle, self.spacing_factor)

    def __repr__(self):
        """Compass representation."""
        return "Compass (radius:{}, center:{})".format(self.radius, self.center)
