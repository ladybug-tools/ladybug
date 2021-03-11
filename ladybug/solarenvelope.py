# coding=utf-8
"""Module for computing solar envelopes."""
from __future__ import division
import math
try:
    from itertools import izip as zip  # python 2
except:
    pass

from ladybug_geometry.geometry2d.pointvector import Point2D, Vector2D
from ladybug_geometry.geometry2d.ray import Ray2D
from ladybug_geometry.geometry2d.polygon import Polygon2D
from ladybug_geometry.geometry3d.pointvector import Point3D, Vector3D
from ladybug_geometry.geometry3d.face import Face3D
from ladybug_geometry.geometry3d.mesh import Mesh3D


class SolarEnvelope(object):
    """Calculate a Solar Envelope boundary for a given site.

    Args:
        geometry_mesh: A ladybug geometry Mesh3D for which a solar envelope boundary
            is computed.
        obstacle_faces: A list of horizontal planar ladybug geometry Face3D
            indicating the tops (in the case of solar collection) or bottoms
            (in the case of solar rights) of context geometries. Being above a
            solar collection boundary ensures these top surfaces don't block
            the sun vectors to ones position. Being below a solar rights
            boundary ensures these bottom surfaces are protected from shade.
        sun_vectors: A list of ladybug geometry Vector3D for the sun vectors, which
            determine the hours of the year when sun should be accessible. These
            can be obtained from the ladybug.sunpath module.
        height_limit: A positive number for the minimum distance below (for collections)
            or maximum distance above (for rights) the average geometry_mesh height
            that the envelope points can be. This is used when there are no
            vectors blocked for a given point. (Default: 100).
        solar_rights: Set to True to compute a solar rights boundary and False to compute
            a solar collection boundary. Solar rights boundaries represent the
            boundary below which one can build without shading the surrounding
            obstacles from any of the sun_vectors. Solar collection boundaries
            represent the boundary above which the one will have direct solar
            access to all of the input sun_vectors. (Default: False).

    Properties:
        * geometry_mesh
        * obstacle_faces
        * sun_vectors
        * height_limit
        * max_height
        * solar_rights
        * geometry_point2ds
        * obstacle_polygon2ds
        * sun_vector2ds
        * sun_vector2ds_reversed
    """
    __slots__ = ('_geometry_mesh', '_obstacle_faces', '_sun_vectors',
                 '_height_limit', '_solar_rights')

    def __init__(self, geometry_mesh, obstacle_faces, sun_vectors,
                 height_limit=100, solar_rights=False):
        self.geometry_mesh = geometry_mesh
        self.obstacle_faces = obstacle_faces
        self.sun_vectors = sun_vectors
        self.height_limit = height_limit
        self.solar_rights = solar_rights

    @property
    def geometry_mesh(self):
        """Get or set a Mesh3D for the site for which a solar envelope is computed."""
        return self._geometry_mesh

    @geometry_mesh.setter
    def geometry_mesh(self, value):
        assert isinstance(value, Mesh3D), 'Expected ladybug_geometry ' \
            'Mesh3D. Got {}.'.format(type(value))
        self._geometry_mesh = value

    @property
    def obstacle_faces(self):
        """Get or set a tuple of Face3D for the context obstacles."""
        return self._obstacle_faces

    @obstacle_faces.setter
    def obstacle_faces(self, value):
        if not isinstance(value, tuple):
            value = tuple(value)
        assert len(value) > 0, 'There must be at least 1 obstacle face.'
        for face in value:
            assert isinstance(face, Face3D), \
                'Expected Face3D for obstacle_faces. Got {}.'.format(type(face))
        self._obstacle_faces = value

    @property
    def sun_vectors(self):
        """Get or set a tuple of Vector3D for the sun vectors for solar access."""
        return self._sun_vectors

    @sun_vectors.setter
    def sun_vectors(self, value):
        if not isinstance(value, tuple):
            value = tuple(value)
        assert len(value) > 0, 'There must be at least 1 sun vector.'
        for vec in value:
            assert isinstance(vec, Vector3D), \
                'Expected Vector3D for sun_vector. Got {}.'.format(type(vec))
        self._sun_vectors = value

    @property
    def height_limit(self):
        """Get or set a number for the height limit below or above the geometry_mesh."""
        return self._height_limit

    @height_limit.setter
    def height_limit(self, value):
        assert isinstance(value, (float, int)), \
            'Expected number for height_limit. Got {}.'.format(type(value))
        assert value > 0, 'The height_limit must be greater than zero.'
        self._height_limit = value

    @property
    def base_height(self):
        """Get a number for the absolute Z value of max/min acceptable height."""
        return self._geometry_mesh.center.z + self._height_limit \
            if self.solar_rights else \
            self._geometry_mesh.center.z - self._height_limit

    @property
    def solar_rights(self):
        """Get or set a boolean for whether a solar rights boundary is computed.

        If True, the evelope represents the boundary below which one can build]
        without shading the surrounding obstacles from any of the sun_vectors.
        If False, the envelope represents the boundary above which the one will
        have direct solar access to all of the input sun_vectors.
        """
        return self._solar_rights

    @solar_rights.setter
    def solar_rights(self, value):
        self._solar_rights = bool(value)

    @property
    def geometry_point2ds(self):
        """Get a list of Point2Ds for the vertices of the geometry_mesh."""
        return [Point2D(pt.x, pt.y) for pt in self._geometry_mesh]

    @property
    def obstacle_polygon2ds(self):
        """Get a list of Polygon2Ds for the obstacle boundaries in 2D space."""
        return [Polygon2D([Point2D(pt.x, pt.y) for pt in face.boundary])
                for face in self._obstacle_faces]

    @property
    def sun_vector2ds(self):
        """Get a list of Vector2Ds for the sun vectors in 2D space."""
        return [Vector2D(vec.x, vec.y) for vec in self._sun_vectors]

    @property
    def sun_vector2ds_reversed(self):
        """Get a list of Vector2Ds for the reversed sun vectors in 2D space."""
        return [Vector2D(-vec.x, -vec.y) for vec in self._sun_vectors]

    def envelope_mesh(self):
        """Compute a Mesh3D representing the solar envelope boundary."""
        # extract the relevant proprties from the input geometry
        pt2ds, poly2ds = self.geometry_point2ds, self.obstacle_polygon2ds
        vec2ds = self.sun_vector2ds if self.solar_rights else self.sun_vector2ds_reversed
        altitudes = self._sun_altitudes()
        obs_heights = [face[0].z for face in self._obstacle_faces]
        base_height = self.base_height

        # loop through the points to get the height of each one
        pt_heights = self._compute_point_heights(
            pt2ds, poly2ds, obs_heights, vec2ds, altitudes, base_height)

        # turn the mesh point heights into a full Mesh3D
        new_vertices = [Point3D(pt.x, pt.y, h) for pt, h in zip(pt2ds, pt_heights)]
        return Mesh3D(new_vertices, self._geometry_mesh.faces)

    def _sun_altitudes(self):
        """Get the altitudes of the sun_vectors in radians."""
        return [vec.angle(Vector3D(vec.x, vec.y, 0)) for vec in self._sun_vectors]

    def _compute_point_heights(
            self, pt2ds, obs_poly2ds, obs_heights, vec2ds, vec_altitudes, base_height):
        """Get Z heights for each of the points in the envelope mesh.

        Args:
            pt2ds: List of Point2D objects for each of the vertices of the mesh
            obs_poly2ds: List of Polygon2D objects for each of the obstacles.
            obs_heights: List of heights for each of the obstacles.
            vec2ds: List of Vector2Ds for each of the sun vectors. These should
                be reversed sun vectors when computing a solar collection.
            vec_altitudes: List of numbers for the altitude of each sun vector
                in radians.
            base_height: The starting height of the envelope points. This should
                be below the geometry_mesh for a collection boundary and above it
                for a rights boundary.
        """
        height_method = self._point_height_rights if self.solar_rights \
            else self._point_height_collection
        heights = []
        for point in pt2ds:
            pt_height = base_height
            for obs_poly, obs_h in zip(obs_poly2ds, obs_heights):
                for vec, alt in zip(vec2ds, vec_altitudes):
                    pt_height = height_method(
                        point, vec, alt, obs_poly, obs_h, pt_height)
            heights.append(pt_height)
        return heights

    @staticmethod
    def _point_height_collection(
            point, vector_2d, altitude, obstacle_poly, obstacle_height, default):
        """Get the height of a given 2D point and sun vector for a collection boundary.

        This will return None if the obstacle has no effect on the height.
        """
        int_pts = obstacle_poly.intersect_line_ray(Ray2D(point, vector_2d))
        if len(int_pts) != 0:
            pt_dist = min([point.distance_to_point(pt) for pt in int_pts])
            new_height = obstacle_height - pt_dist * math.tan(altitude)
            if new_height > default:
                return new_height
        return default

    @staticmethod
    def _point_height_rights(
            point, vector_2d, altitude, obstacle_poly, obstacle_height, default):
        """Get the height of a given 2D point and sun vector for a rights boundary.

        This will return None if the obstacle has no effect on the height.
        """
        int_pts = obstacle_poly.intersect_line_ray(Ray2D(point, vector_2d))
        if len(int_pts) != 0:
            pt_dist = min([point.distance_to_point(pt) for pt in int_pts])
            new_height = pt_dist * math.tan(altitude) + obstacle_height
            if new_height < default:
                return new_height
        return default

    def __repr__(self):
        """SolarEnvelope representation."""
        return "SolarEnvelope [{}]".format(self.geometry_mesh)
