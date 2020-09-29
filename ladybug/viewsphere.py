# coding=utf-8
"""Class to subdivide the sphere and hemisphere for view-based and radiation studies."""
from __future__ import division

import math

from ladybug_geometry.geometry3d.pointvector import Point3D, Vector3D
from ladybug_geometry.geometry3d.mesh import Mesh3D


class ViewSphere(object):
    """Class for subdividing the sphere and hemisphere for view-based studies.

    Note:
        [1] Tregenza, Peter. (1987). Subdivision of the sky hemisphere for luminance
        measurements. Lighting Research & Technology - LIGHTING RES TECHNOL.
        19. 13-14. 10.1177/096032718701900103.

    Properties:
        * tregenza_dome_vectors
        * tregenza_sphere_vectors
        * tregenza_dome_mesh
        * tregenza_dome_mesh_high_res
        * tregenza_sphere_mesh
        * tregenza_solid_angles
        * reinhart_dome_vectors
        * reinhart_sphere_vectors
        * reinhart_dome_mesh
        * reinhart_sphere_mesh
        * reinhart_solid_angles
    """
    # number of patches in each row of the most-used sky domes
    TREGENZA_PATCHES_PER_ROW = (30, 30, 24, 24, 18, 12, 6)
    REINHART_PATCHES_PER_ROW = (60, 60, 60, 60, 48, 48, 48, 48, 36, 36, 24, 24, 12, 12)
    # number of steradians for the patches of each row of the most-used sky domes
    TREGENZA_COEFFICIENTS = \
        (0.0435449227, 0.0416418006, 0.0473984151, 0.0406730411, 0.0428934136,
         0.0445221864, 0.0455168385, 0.0344199465)
    REINHART_COEFFICIENTS = \
        (0.0113221971, 0.0111894547, 0.0109255262, 0.0105335058, 0.0125224872,
         0.0117312774, 0.0108025291, 0.00974713106, 0.011436609, 0.00974295956,
         0.0119026242, 0.00905126163, 0.0121875626, 0.00612971396, 0.00921483254)

    __slots__ = ('_tregenza_dome_vectors', '_tregenza_sphere_vectors',
                 '_tregenza_dome_mesh', '_tregenza_dome_mesh_high_res',
                 '_tregenza_sphere_mesh', '_tregenza_solid_angles',
                 '_reinhart_dome_vectors', '_reinhart_sphere_vectors',
                 '_reinhart_dome_mesh', '_reinhart_sphere_mesh',
                 '_reinhart_solid_angles')

    def __init__(self):
        """Create the ViewSphere."""
        # everything starts with None and properties are generated as requested
        self._tregenza_dome_vectors = None
        self._tregenza_sphere_vectors = None
        self._tregenza_dome_mesh = None
        self._tregenza_dome_mesh_high_res = None
        self._tregenza_sphere_mesh = None
        self._tregenza_solid_angles = None
        self._reinhart_dome_vectors = None
        self._reinhart_sphere_vectors = None
        self._reinhart_dome_mesh = None
        self._reinhart_sphere_mesh = None
        self._reinhart_solid_angles = None

    @property
    def tregenza_dome_vectors(self):
        """An array of 145 vectors representing the Tregenza sky dome."""
        if self._tregenza_dome_vectors is None:
            self._tregenza_dome_mesh, self._tregenza_dome_vectors = self.dome_patches()
        return self._tregenza_dome_vectors

    @property
    def tregenza_sphere_vectors(self):
        """An array of 290 vectors representing a sphere of Tregenza vectors."""
        if self._tregenza_sphere_vectors is None:
            self._tregenza_sphere_mesh, self._tregenza_sphere_vectors = \
                self.sphere_patches()
        return self._tregenza_sphere_vectors

    @property
    def tregenza_dome_mesh(self):
        """An Mesh3D representing the Tregenza sky dome.

        There is one quad face per patch except for the last circular patch, which
        is represented by 6 triangles.
        """
        if self._tregenza_dome_mesh is None:
            self._tregenza_dome_mesh, self._tregenza_dome_vectors = self.dome_patches()
        return self._tregenza_dome_mesh

    @property
    def tregenza_dome_mesh_high_res(self):
        """An high-resolution Mesh3D representing the Tregenza sky dome.

        Each patch is represented by a 3x3 set of quad faces except for the last
        circular patch, which is represented by 18 triangles.
        """
        if self._tregenza_dome_mesh_high_res is None:
            self._tregenza_dome_mesh_high_res, _ = self.dome_patches(3, True)
        return self._tregenza_dome_mesh_high_res

    @property
    def tregenza_sphere_mesh(self):
        """An Mesh3D representing a Tregenza sphere.

        There is one quad face per patch except for the two circular patches, which
        are each represented by 6 triangles.
        """
        if self._tregenza_sphere_mesh is None:
            self._tregenza_sphere_mesh, self._tregenza_sphere_vectors = \
                self.sphere_patches()
        return self._tregenza_sphere_mesh

    @property
    def tregenza_solid_angles(self):
        """Get a list of solid angles that align with the tregenza_dome_vectors."""
        if self._reinhart_solid_angles is None:
            angles = view_sphere.TREGENZA_COEFFICIENTS
            patch_rows = view_sphere.TREGENZA_PATCHES_PER_ROW + (1,)
            patch_angles = []
            for ang, p_count in zip(angles, patch_rows):
                patch_angles.extend([ang] * p_count)
            self._reinhart_solid_angles = tuple(patch_angles)
        return self._reinhart_solid_angles

    @property
    def reinhart_dome_vectors(self):
        """An array of 577 vectors representing the Reinhart sky dome."""
        if self._reinhart_dome_vectors is None:
            self._reinhart_dome_mesh, self._reinhart_dome_vectors = self.dome_patches(2)
        return self._reinhart_dome_vectors

    @property
    def reinhart_sphere_vectors(self):
        """An array of 1154 vectors representing a sphere of Reinhart vectors."""
        if self._reinhart_sphere_vectors is None:
            self._reinhart_sphere_mesh, self._reinhart_sphere_vectors = \
                self.sphere_patches(2)
        return self._reinhart_sphere_vectors

    @property
    def reinhart_dome_mesh(self):
        """An Mesh3D representing the Reinhart sky dome.

        There is one quad face per patch except for the last circular patch, which
        is represented by 12 triangles.
        """
        if self._reinhart_dome_mesh is None:
            self._reinhart_dome_mesh, self._reinhart_dome_vectors = self.dome_patches(2)
        return self._reinhart_dome_mesh

    @property
    def reinhart_sphere_mesh(self):
        """An Mesh3D representing a Reinhart sphere.

        There is one quad face per patch except for the two circular patches, which
        are each represented by 12 triangles.
        """
        if self._reinhart_sphere_mesh is None:
            self._reinhart_sphere_mesh, self._reinhart_sphere_vectors = \
                self.sphere_patches(2)
        return self._reinhart_sphere_mesh

    @property
    def reinhart_solid_angles(self):
        """Get a list of solid angles that align with the reinhart_dome_vectors."""
        if self._reinhart_solid_angles is None:
            angles = view_sphere.REINHART_COEFFICIENTS
            patch_rows = view_sphere.REINHART_PATCHES_PER_ROW + (1,)
            patch_angles = []
            for ang, p_count in zip(angles, patch_rows):
                patch_angles.extend([ang] * p_count)
            self._reinhart_solid_angles = tuple(patch_angles)
        return self._reinhart_solid_angles

    def horizontal_radial_vectors(self, vector_count):
        """Get perfectly horizontal Vector3Ds radiating outward in a circle.

        Args:
            vector_count: An integer for the number of vectors to generate in the
                horizontal plane. This can align with any of the dome or sphere
                patches by setting this to 30 * division_count.

        Returns:
            A list of ladybug_geometry horizontal Vector3D radiating outward in
            a circle. All vectors are unit vectors.
        """
        base_vec = Vector3D(0, 1, 0)
        horiz_angle = -2 * math.pi / vector_count
        return tuple(base_vec.rotate_xy(horiz_angle * i) for i in range(vector_count))

    def horizontal_radial_patches(self, offset_angle=30, division_count=1,
                                  subdivide_in_place=False):
        """Get a Vector3Ds within a certain angle offset from the horizontal plane.

        Args:
            offset_angle: A number between 0 and 90 for the angle offset from the
                horizontal plane at which vectors will be included. Vectors both
                above and below this angle will be included (Default: 30 for the
                rough vertical limit of human peripheral vision).
            division_count: A positive integer for the number of times that the
                original Tregenza patches are subdivided. 1 indicates that the
                original Tregenza patches will be used, 2 indicates
                the Reinhart patches will be used, and so on. (Default: 1).
            subdivide_in_place: A boolean to note whether patches should be
                subdivided according to the extension of Tregenza's original
                logic through the Reinhart method (False) or they should be
                simply divided into 4 in place (True).

        Returns:
            A tuple with two elements

            -   patch_mesh: A ladybug_geometry Mesh3D that represents the patches at
                the input division_count. There is one quad face per patch.

            -   patch_vectors: A list of ladybug_geometry Vector3D with one vector
                per patch. These will align with the faces of the patch_mesh.
                All vectors are unit vectors.
        """
        # figure out how many rows and patches should be in the output
        patch_row_count = self._patch_row_count_array(division_count)
        patch_count = self._patch_count_in_radial_offset(
            offset_angle, division_count, patch_row_count, subdivide_in_place)

        # get the dome and vectors and remove faces up tot the patch count
        m_all, v_all = self.dome_patches(division_count, subdivide_in_place)
        pattern = [True] * patch_count + \
            [False] * (sum(patch_row_count) - patch_count + 6 * division_count)
        m_top, v_pattern = m_all.remove_faces(pattern)
        v_top = tuple(vec for vec, val in zip(v_all, pattern) if val)

        # reverse the vectors and negate all the z values of the sky patch mesh
        return self._generate_bottom_from_top(m_top, v_top)

    def horizontal_radial_patch_weights(self, offset_angle=30, division_count=1):
        """Get a list of numbers corresponding to the area weight of each radial patch.

        Args:
            offset_angle: A number between 0 and 90 for the angle offset from the
                horizontal plane at which vectors will be included. Vectors both
                above and below this angle will be included (Default: 30).
            division_count: A positive integer for the number of times that the
                original Tregenza patches are subdivided. (Default: 1).

        Returns:
            A list of numbers with a value for each patch that corresponds to the
            area of that patch. The aveage value of all the patches is equal to 1.
        """
        # get the areas of the patches and the number of patches to include in the offset
        patch_areas, patch_row_count = self._dome_patch_areas(division_count)
        patch_count = self._patch_count_in_radial_offset(
            offset_angle, division_count, patch_row_count)
        # normalize the patch areas so that they average to 1
        relevant_patches = patch_areas[:patch_count]
        avg_patch_area = sum(relevant_patches) / len(relevant_patches)
        return [p_area / avg_patch_area for p_area in relevant_patches] * 2

    def dome_patches(self, division_count=1, subdivide_in_place=False):
        """Get a Vector3Ds and a correcponding Mesh3D for a dome.

        Args:
            division_count: A positive integer for the number of times that the
                original Tregenza patches are subdivided. 1 indicates that the
                original Tregenza patches will be used, 2 indicates
                the Reinhart patches will be used, and so on. (Default: 1).
            subdivide_in_place: A boolean to note whether patches should be
                subdivided according to the extension of Tregenza's original
                logic through the Reinhart method (False) or they should be
                simply divided into 4 in place (True). The latter is useful
                for making higher resolution Mesh visualizations of an
                inherently low-resolution dome.

        Returns:
            A tuple with two elements

            -   patch_mesh: A ladybug_geometry Mesh3D that represents the dome at
                the input division_count. There is one quad face per patch except
                for the last circular patch, which is represented by a number of
                triangles equal to division_count * 6.

            -   patch_vectors: A list of ladybug_geometry Vector3D with one vector
                per patch. These will align with the faces of the patch_mesh up
                until the last circular patch, which will have a single vector
                for the several triangular faces. All vectors are unit vectors.
        """
        # compute constants to be used in the generation of patch points
        patch_row_count = self._patch_row_count_array(division_count)
        base_vec = Vector3D(0, 1, 0)
        rotate_axis = Vector3D(1, 0, 0)
        vertical_angle = math.pi / (2 * len(patch_row_count) + division_count) if \
            subdivide_in_place else math.pi / (2 * len(patch_row_count) + 1)

        # loop through the patch values and generate points for each vertex
        vertices = []
        faces = []
        pt_i = -2  # track the number of vertices in the mesh
        for row_i, row_count in enumerate(patch_row_count):
            pt_i += 2  # advance the number of vertices by two
            horiz_angle = -2 * math.pi / row_count  # horizontal angle of each patch
            vec01 = base_vec.rotate(rotate_axis, vertical_angle * row_i)
            vec02 = vec01.rotate(rotate_axis, vertical_angle)
            correction_angle = -horiz_angle / 2
            if subdivide_in_place:
                correction_angle * division_count
            vec1 = vec01.rotate_xy(correction_angle)
            vec2 = vec02.rotate_xy(correction_angle)
            vertices.extend((Point3D(v.x, v.y, v.z) for v in (vec1, vec2)))
            for patch_i in range(row_count):  # generate the row of patches
                vec3 = vec1.rotate_xy(horiz_angle)
                vec4 = vec2.rotate_xy(horiz_angle)
                vertices.extend((Point3D(v.x, v.y, v.z) for v in (vec3, vec4)))
                faces.append((pt_i, pt_i + 1, pt_i + 3, pt_i + 2))
                pt_i += 2  # advance the number of vertices by two
                vec1, vec2 = vec3, vec4  # reset vec1 and vec2 for the next patch

        # add triangular faces to represent the last circular patch
        end_vert_i = len(vertices)
        start_vert_i = len(vertices) - patch_row_count[-1] * 2 - 1
        vertices.append(Point3D(0, 0, 1))
        for tr_i in range(0, patch_row_count[-1] * 2, 2):
            faces.append((start_vert_i + tr_i, end_vert_i, start_vert_i + tr_i + 2))

        # create the Mesh3D object and derive the patch vectors from the mesh
        patch_mesh = Mesh3D(vertices, faces)
        patch_vectors = patch_mesh.face_normals[:-patch_row_count[-1]] + \
            (Vector3D(0, 0, 1),)
        return patch_mesh, patch_vectors

    def dome_patch_weights(self, division_count=1):
        """Get a list of numbers corresponding to the area weight of each dome patch.

        Args:
            division_count: A positive integer for the number of times that the
                original Tregenza patches are subdivided. (Default: 1).

        Returns:
            A list of numbers with a value for each patch that corresponds to the
            area of that patch. The aveage value of all the patches is equal to 1.
        """
        # get the areas of the patches
        patch_areas, patch_row_count = self._dome_patch_areas(division_count)
        # normalize the patch areas so that they average to 1
        avg_patch_area = 2 * math.pi / len(patch_areas)
        return [p_area / avg_patch_area for p_area in patch_areas]

    def sphere_patches(self, division_count=1, subdivide_in_place=False):
        """Get a Vector3Ds and a correcponding Mesh3D for a sphere.

        Args:
            division_count: A positive integer for the number of times that the
                original Tregenza patches are subdivided. 1 indicates that the
                original Tregenza patches will be used, 2 indicates
                the Reinhart patches will be used, and so on. (Default: 1).
            subdivide_in_place: A boolean to note whether patches should be
                subdivided according to the extension of Tregenza's original
                logic through the Reinhart method (False) or they should be
                simply divided into 4 in place (True). The latter is useful
                for making higher resolution Mesh visualizations of an
                inherently low-resolution dome.

        Returns:
            A tuple with two elements

            -   patch_mesh: A ladybug_geometry Mesh3D that represents the sphere at
                the input division_count. There is one quad face per patch except
                for the last circular patch of each hemisphere, which is represented
                by a number of triangles equal to division_count * 6.

            -   patch_vectors: A list of ladybug_geometry Vector3D with one vector
                per patch. These will align with the faces of the patch_mesh except
                for the two circular patches, which will have a single vector
                for the several triangular faces. All vectors are unit vectors.
        """
        # generate patches for the hemisphere
        m_top, v_top = self.dome_patches(division_count, subdivide_in_place)
        # reverse the vectors and negate all the z values of the sky patch mesh
        return self._generate_bottom_from_top(m_top, v_top)

    def sphere_patch_weights(self, division_count=1):
        """Get a list of numbers corresponding to the area weight of each sphere patch.

        Args:
            division_count: A positive integer for the number of times that the
                original Tregenza patches are subdivided. (Default: 1).

        Returns:
            A list of numbers with a value for each patch that corresponds to the
            area of that patch. The aveage value of all the patches is equal to 1.
        """
        # get the areas of the patches
        patch_areas, patch_row_count = self._dome_patch_areas(division_count)
        # normalize the patch areas so that they average to 1
        avg_patch_area = 2 * math.pi / len(patch_areas)
        return [p_area / avg_patch_area for p_area in patch_areas] * 2

    @staticmethod
    def _dome_patch_areas(division_count):
        """Get the area of each patch in a dome from a division_count."""
        # get the areas of each spherical cap moving up the unit dome
        patch_row_count = ViewSphere._patch_row_count_array(division_count)
        vert_angle = math.pi / (2 * len(patch_row_count) + division_count)
        cap_areas = [2 * math.pi]
        current_angle = vert_angle
        for i in range(len(patch_row_count)):
            cap_areas.append(2 * math.pi * (1 - math.sin(current_angle)))
            current_angle += vert_angle

        # get the area of each row and subdivide it by the patch count of the row
        row_areas = [cap_areas[i] - cap_areas[i + 1] for i in range(len(cap_areas) - 1)]
        patch_areas = []
        for row_count, row_area in zip(patch_row_count, row_areas):
            patch_areas.extend([row_area / row_count] * row_count)
        patch_areas.append(cap_areas[-1])
        return patch_areas, patch_row_count

    @staticmethod
    def _patch_count_in_radial_offset(offset_angle, division_count, patch_row_count,
                                      subdivide_in_place=False):
        """Get the number of patches within a radial offset from the horizontal plane."""
        rad_angle = math.radians(offset_angle)
        patch_rows = len(patch_row_count)
        vert_angle = math.pi / (2 * patch_rows + division_count) if subdivide_in_place \
            else math.pi / (2 * patch_rows + 1)
        row_count = int(round(rad_angle / vert_angle))
        return sum(patch_row_count[:row_count])

    @staticmethod
    def _patch_row_count_array(division_count):
        """Get an array of the number of patches in each dome row from division_count."""
        patch_row_count = ViewSphere.TREGENZA_PATCHES_PER_ROW
        if division_count != 1:
            patch_row_count = [init_ct * division_count for init_ct in patch_row_count
                               for i in range(division_count)]
        return patch_row_count

    @staticmethod
    def _generate_bottom_from_top(m_top, v_top):
        """Get a joined mesh and vectors for top and bottom from only top vectors."""
        # reverse the vectors and negate all the z values of the sky patch mesh
        verts = tuple(Point3D(pt.x, pt.y, -pt.z) for pt in m_top.vertices)
        faces = tuple(face[::-1] for face in m_top.faces)
        m_bottom = Mesh3D(verts, faces)
        v_bottom = tuple(Vector3D(v.x, v.y, -v.z) for v in v_top)

        # join everything together
        patch_mesh = Mesh3D.join_meshes([m_top, m_bottom])
        patch_vectors = v_top + v_bottom
        return patch_mesh, patch_vectors

    def __repr__(self):
        """ViewSphere representation."""
        return 'ViewSphere'


# make a single object that can be reused throughout the library
view_sphere = ViewSphere()
