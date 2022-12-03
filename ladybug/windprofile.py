# coding=utf-8
"""Module for visualizing and converting between meteorological and other wind speeds."""
from __future__ import division
import math

from ladybug_geometry.geometry3d import Vector3D, Point3D, Plane, LineSegment3D, \
    Polyline3D, Mesh3D
from .datacollection import HourlyContinuousCollection
from .color import Color


class WindProfile(object):
    """Object for visualizing and converting from meteorological wind speeds.

    Args:
        terrain: A text string that sets the terrain class associated with the
            location that the wind profile represents. (Default: city). Values
            must be one the following:

            * city - 50% of buildings above 21m over a distance of at least 2000m upwind.
            * suburban - suburbs, wooded areas.
            * country - open, with scattered objects generally less than 10m high.
            * water - flat areas downwind of a large water body (max 500m inland).

        meteorological_terrain: A text string that sets the terrain class associated
            with the meteorological wind speed. (Default: country, which is typical
            of most airports where wind measurements are taken).
        meteorological_height: A number for the height above the ground at which
            the meteorological wind speed is measured in meters. (Default: 10 meters).
        log_law: A boolean to note whether the wind profile should use a logarithmic
            law to determine wind speeds instead of the default power law, which
            is used by EnergyPlus. (Default: False).

    Properties:
        * terrain
        * meteorological_terrain
        * meteorological_height
        * log_law
        * boundary_layer_height
        * power_law_exponent
        * roughness_length
        * met_boundary_layer_height
        * met_power_law_exponent
        * met_roughness_length
    """
    __slots__ = (
        '_terrain', '_meteorological_terrain', '_meteorological_height', '_log_law',
        '_boundary_layer_height', '_power_law_exponent', '_roughness_length',
        '_met_boundary_layer_height', '_met_power_law_exponent', '_met_roughness_length',
        '_met_power_denom', '_met_log_denom')

    TERRAINS = ('city', 'suburban', 'country', 'water')
    TERRAIN_PARAMETERS = {
        'city': (460, 0.33, 1.0),
        'suburban': (370, 0.22, 0.5),
        'country': (270, 0.14, 0.1),
        'water': (210, 0.10, 0.03)
    }
    BLACK = Color(0, 0, 0)

    def __init__(self, terrain='city', meteorological_terrain='country',
                 meteorological_height=10, log_law=False):
        """Initialize wind profile."""
        self._meteorological_height = 10  # set a default to ensure checks pass
        self.terrain = terrain
        self.meteorological_terrain = meteorological_terrain
        self.meteorological_height = meteorological_height
        self.log_law = log_law

    @property
    def terrain(self):
        """Get or set text for the terrain class for the wind profile location.

        Setting this will set all of the properties of the boundary layer,
        roughness length, etc. Choose from the following options.

        * city
        * suburban
        * country
        * water
        """
        return self._terrain

    @terrain.setter
    def terrain(self, value):
        value = self._check_terrain(value)
        self._terrain = value
        self._boundary_layer_height, self._power_law_exponent, self._roughness_length = \
            self.TERRAIN_PARAMETERS[value]

    @property
    def meteorological_terrain(self):
        """Get or set text for the terrain class for the meteorological location.

        Setting this will set all of the properties of the boundary layer,
        roughness length, etc. Choose from the following options.

        * city
        * suburban
        * country
        * water
        """
        return self._meteorological_terrain

    @meteorological_terrain.setter
    def meteorological_terrain(self, value):
        value = self._check_terrain(value)
        self._meteorological_terrain = value
        self._met_boundary_layer_height, self._met_power_law_exponent, \
            self._met_roughness_length = self.TERRAIN_PARAMETERS[value]
        self._compute_met_power_denom()
        self._compute_met_log_denom()

    @property
    def meteorological_height(self):
        """Get or set the measurement height of the meteorological wind speed [m]."""
        return self._meteorological_height

    @meteorological_height.setter
    def meteorological_height(self, value):
        assert isinstance(value, (float, int)), 'Expected number for ' \
            'WindProfile meteorological_height. Got {}.'.format(type(value))
        assert value > 0, 'WindProfile meteorological_height must be ' \
            'greater than 0. Got {}.'.format(value)
        self._meteorological_height = value
        self._compute_met_power_denom()
        self._compute_met_log_denom()

    @property
    def log_law(self):
        """A boolean to note whether the wind profile should be using a logarithmic law.
        """
        return self._log_law

    @log_law.setter
    def log_law(self, value):
        self._log_law = bool(value)

    @property
    def boundary_layer_height(self):
        """Get or set the boundary layer height of the wind profile location [m]."""
        return self._boundary_layer_height

    @boundary_layer_height.setter
    def boundary_layer_height(self, value):
        assert isinstance(value, (float, int)), 'Expected number for ' \
            'WindProfile boundary_layer_height. Got {}.'.format(type(value))
        assert value > 0, 'WindProfile boundary_layer_height must be ' \
            'greater than 0. Got {}.'.format(value)
        self._boundary_layer_height = value

    @property
    def power_law_exponent(self):
        """Get or set the power law exponent of the wind profile location."""
        return self._power_law_exponent

    @power_law_exponent.setter
    def power_law_exponent(self, value):
        assert isinstance(value, (float, int)), 'Expected number for ' \
            'WindProfile power_law_exponent. Got {}.'.format(type(value))
        assert 1 > value > 0, 'WindProfile power_law_exponent must be ' \
            'between 0 and 1. Got {}.'.format(value)
        self._power_law_exponent = value

    @property
    def roughness_length(self):
        """Get or set the roughness length of the wind profile location [m]."""
        return self._roughness_length

    @roughness_length.setter
    def roughness_length(self, value):
        assert isinstance(value, (float, int)), 'Expected number for ' \
            'WindProfile roughness_length. Got {}.'.format(type(value))
        assert value > 0, 'WindProfile roughness_length must be ' \
            'greater than 0. Got {}.'.format(value)
        self._roughness_length = value

    @property
    def met_boundary_layer_height(self):
        """Get or set the boundary layer height of the meteorological location [m]."""
        return self._met_boundary_layer_height

    @met_boundary_layer_height.setter
    def met_boundary_layer_height(self, value):
        assert isinstance(value, (float, int)), 'Expected number for ' \
            'WindProfile met_boundary_layer_height. Got {}.'.format(type(value))
        assert value > 0, 'WindProfile met_boundary_layer_height must be ' \
            'greater than 0. Got {}.'.format(value)
        self._met_boundary_layer_height = value
        self._compute_met_power_denom()

    @property
    def met_power_law_exponent(self):
        """Get or set the power law exponent of the meteorological location."""
        return self._met_power_law_exponent

    @met_power_law_exponent.setter
    def met_power_law_exponent(self, value):
        assert isinstance(value, (float, int)), 'Expected number for ' \
            'WindProfile met_power_law_exponent. Got {}.'.format(type(value))
        assert 1 > value > 0, 'WindProfile met_power_law_exponent must be ' \
            'between 0 and 1. Got {}.'.format(value)
        self._met_power_law_exponent = value
        self._compute_met_power_denom()

    @property
    def met_roughness_length(self):
        """Get or set the roughness length of the meteorological location [m]."""
        return self._met_roughness_length

    @met_roughness_length.setter
    def met_roughness_length(self, value):
        assert isinstance(value, (float, int)), 'Expected number for ' \
            'WindProfile met_roughness_length. Got {}.'.format(type(value))
        assert value > 0, 'WindProfile met_roughness_length must be ' \
            'greater than 0. Got {}.'.format(value)
        self._met_roughness_length = value
        self._compute_met_log_denom()

    def calculate_wind(self, meteorological_wind_speed, height=1):
        """Calculate the wind speed at a given height above the ground.

        Args:
            meteorological_wind_speed: A number for the meteorological
                wind speed [m/s].
            height: The height above the ground to be evaluated in
                meters. (Default: 1).
        """
        if self._log_law:
            if height > self._roughness_length:
                met_log_num = math.log(height / self._roughness_length)
                return meteorological_wind_speed * (met_log_num / self._met_log_denom)
            return 0
        else:
            h_ratio = (height / self._boundary_layer_height) ** self._power_law_exponent
            return h_ratio * (meteorological_wind_speed * self._met_power_denom)

    def calculate_wind_data(self, meteorological_wind_data, height=1):
        """Get a data collection of wind speed at a given height above the ground.

        Args:
            meteorological_wind_data: A data collection of meteorological
                wind speed [m/s].
            height: The height above the ground to be evaluated in
                meters. (Default: 1).
        """
        vals = tuple(self.calculate_wind(v, height) for v in meteorological_wind_data)
        new_header = meteorological_wind_data.header.duplicate()
        new_header.metadata['height'] = '{}m'.format(round(height, 1))
        if isinstance(meteorological_wind_data, HourlyContinuousCollection):
            return HourlyContinuousCollection(new_header, vals)
        else:
            dts = meteorological_wind_data.datetimes
            return meteorological_wind_data.__class__(new_header, vals, dts)

    def wind_vector(
            self, meteorological_wind_speed, height, direction=None,
            length_dimension=1, scale_factor=1):
        """Get a Vector3D for a wind profile arrow at a given height above the ground.

        Args:
            meteorological_wind_speed: A number for the meteorological wind speed [m/s].
            height: The height above the ground to be evaluated in meters.
            direction: An optional number between 0 and 360 that represents the
                cardinal direction that the wind vector is facing in the XY
                plane. 0 = North, 90 = East, 180 = South, 270 = West. If None,
                the wind vector will simply be placed in the XY plane. (Default: None).
            length_dimension: A number to denote the length dimension of a 1 m/s
                wind vector in meters. This will be used to set the length of the
                wind vector. (Default: 1).
            scale_factor: An optional number that will be multiplied by all dimensions
                to account for the fact that the wind profile may be displaying in
                a units system other than meters. (Default: 1).

        Returns:
            A ladybug-geometry Vector3D representing the wind vector.
        """
        direction = self._flip_direction(direction)
        wind_speed = self.calculate_wind(meteorological_wind_speed, height)
        vec_mag = wind_speed * length_dimension * scale_factor
        if direction is None:
            return Vector3D(vec_mag, 0, 0)
        else:
            base_vec = Vector3D(0, vec_mag, 0)
            return base_vec.rotate_xy(-math.radians(direction))

    def profile_polyline3d(
            self, meteorological_wind_speed, max_height=30, vector_spacing=2,
            direction=None, base_point=Point3D(0, 0, 0), length_dimension=5,
            scale_factor=1):
        """Get a Polyline3D for a wind profile curve at a meteorological wind speed.

        Args:
            meteorological_wind_speed: A number for the meteorological wind speed [m/s].
            max_height: A number in meters to specify the maximum height of the
                wind profile curve. (Default: 30 meters).
            vector_spacing: A number in meters to specify the difference in height
                between each of the wind vectors that is used to build the
                profile curve. Lower numbers will result in smoother looking
                curves. (Default 2 meters).
            direction: An optional number between 0 and 360 that represents the
                cardinal direction that the wind profile is facing in the XY
                plane. 0 = North, 90 = East, 180 = South, 270 = West. If None,
                the wind profile will simply be placed in the XY plane. (Default: None).
            base_point: A ladybug-geometry Point3D that represents the ground
                location of the wind profile. (Default, (0, 0, 0)).
            length_dimension: A number to denote the length dimension of a 1 m/s
                wind vector in meters. (Default: 5).
            scale_factor: An optional number that will be multiplied by all dimensions
                to account for the fact that the wind profile may be displaying in
                a units system other than meters. (Default: 1).

        Returns:
            A tuple with three values.

            - profile_polyline: A ladybug-geometry Polyline3D representing the
                wind profile.

            - wind_vectors: A list of ladybug-geometry Vector3D representing the
                wind vectors that built the profile.

            - anchor_pts: A list of ladybug-geometry Point3D representing the
                anchor points for the wind vectors.
        """
        self._check_profile_inputs(max_height, vector_spacing)
        bp = base_point
        profile_pts, wind_vectors, anchor_pts = [bp], [Vector3D(0, 0, 0)], [bp]
        m_val = max_height + vector_spacing
        for h in self._frange(vector_spacing, m_val, vector_spacing):
            a_pt = Point3D(bp.x, bp.y + (h * scale_factor), bp.z) \
                if direction is None else Point3D(bp.x, bp.y, bp.z + (h * scale_factor))
            w_vec = self.wind_vector(
                meteorological_wind_speed, h, direction,
                length_dimension, scale_factor)
            profile_pts.append(a_pt.move(w_vec))
            wind_vectors.append(w_vec)
            anchor_pts.append(a_pt)
        profile_polyline = Polyline3D(profile_pts)
        return profile_polyline, wind_vectors, anchor_pts

    def mesh_arrow(
            self, meteorological_wind_speed, height, direction=None,
            base_point=Point3D(0, 0, 0), length_dimension=5, height_dimension=1,
            scale_factor=1):
        """Get a Mesh3D for an arrow at a given height above the ground.

        Args:
            meteorological_wind_speed: A number for the meteorological wind speed [m/s].
            height: The height above the ground to be evaluated in meters.
            direction: An optional number between 0 and 360 that represents the
                cardinal direction that the mesh arrow is facing in the XY
                plane. 0 = North, 90 = East, 180 = South, 270 = West. If None,
                the wind vector and mesh arrow will simply be placed in the XY
                plane. (Default: None).
            base_point: A ladybug-geometry Point3D that represents the ground
                location of the wind profile. (Default, (0, 0, 0)).
            length_dimension: A number to denote the length dimension of a 1 m/s
                wind vector in meters. This will be used to set the length of the
                wind vector arrow. (Default: 5).
            height_dimension: A number to denote the height dimension of the
                wind vector in meters. (Default: 1).
            scale_factor: An optional number that will be multiplied by all dimensions
                to account for the fact that the wind profile may be displaying in
                a units system other than meters. (Default: 1).

        Returns:
            A tuple with four values.

            - mesh_arrow: A Mesh3D object that represents the wind speed at the
                height above the ground.

            - wind_vector: A ladybug-geometry Vector3D representing the wind vector.

            - anchor_pt: A ladybug-geometry Point3D representing the anchor point
                for the wind vector.

            - wind_speed: A number for the wind speed associated with the mesh arrow.
        """
        direction = self._flip_direction(direction)
        # get an anchor point that represents the wind arrow
        bp = base_point
        if direction is None:
            y_val = bp.y + height * scale_factor
            anchor_pt = Point3D(bp.x, y_val, bp.z)
        else:
            z_val = bp.z + height * scale_factor
            anchor_pt = Point3D(bp.x, bp.y, z_val)
        # calculate the wind speed and vector at the height
        wind_speed = self.calculate_wind(meteorological_wind_speed, height)
        vec_mag = wind_speed * length_dimension
        vm_scaled = vec_mag * scale_factor
        # build the mesh vertices and with arrow facing the X-axis from the anchor point
        x_vec = Vector3D(vm_scaled, 0, 0)
        max_arrow = length_dimension / 2
        if vec_mag >= length_dimension:
            ar_vec = Vector3D(scale_factor * max_arrow, 0, 0)
            ar_x = (vec_mag - max_arrow) * scale_factor
        else:
            mid_val = ar_x = vm_scaled * 0.5
            ar_vec = Vector3D(mid_val, 0, 0)
        if direction is None:
            ar_pt = Point3D(bp.x + ar_x, bp.y + (height * scale_factor), bp.z)
        else:
            ar_pt = Point3D(bp.x + ar_x, bp.y, bp.z + (height * scale_factor))
        ad = (height_dimension * scale_factor) / 2
        hd = (height_dimension * scale_factor) / 4
        stem_mvs = (Vector3D(0, hd, hd), Vector3D(0, -hd, hd),
                    Vector3D(0, -hd, -hd), Vector3D(0, hd, -hd))
        ar_mvs = (Vector3D(0, ad, ad), Vector3D(0, -ad, ad),
                  Vector3D(0, -ad, -ad), Vector3D(0, ad, -ad))
        verts = []
        for mv in stem_mvs + (x_vec,):
            verts.append(anchor_pt.move(mv))
        for mv in ar_mvs + (ar_vec,):
            verts.append(ar_pt.move(mv))
        # rotate the vertices if the direction is specified
        if direction is not None:
            v_ang, rad90 = -math.radians(direction), math.radians(90)
            verts = [v.rotate_xy(v_ang + rad90, base_point) for v in verts]
            base_vec = Vector3D(0, vec_mag, 0)
            wind_vector = base_vec.rotate_xy(v_ang)
        else:
            wind_vector = Vector3D(vec_mag, 0, 0)
        # specify the faces and return the final Mesh3D
        faces = [
            (0, 1, 2, 3), (0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4),
            (5, 6, 7, 8), (5, 6, 9), (6, 7, 9), (7, 8, 9), (8, 5, 9)
        ]
        mesh_arrow = Mesh3D(verts, faces)
        return mesh_arrow, wind_vector, anchor_pt, wind_speed

    def mesh_arrow_profile(
            self, meteorological_wind_speed, max_height=30, vector_spacing=2,
            direction=None, base_point=Point3D(0, 0, 0), length_dimension=5,
            height_dimension=1, scale_factor=1):
        """Get a Polyline3D for a wind profile curve at a meteorological wind speed.

        Args:
            meteorological_wind_speed: A number for the meteorological wind speed [m/s].
            max_height: A number in meters to specify the maximum height of the
                wind profile curve. (Default: 30 meters).
            vector_spacing: A number in meters to specify the difference in height
                between each of the mesh arrows. (Default 2 meters).
            direction: An optional number between 0 and 360 that represents the
                cardinal direction that the wind profile is facing in the XY
                plane. 0 = North, 90 = East, 180 = South, 270 = West. If None,
                the wind profile will simply be placed in the XY plane. (Default: None).
            base_point: A ladybug-geometry Point3D that represents the ground
                location of the wind profile. (Default, (0, 0, 0)).
            length_dimension: A number to denote the length dimension of a 1 m/s
                wind vector in meters. (Default: 5).
            height_dimension: A number to denote the height dimension of the
                wind vector in meters. (Default: 1).
            scale_factor: An optional number that will be multiplied by all dimensions
                to account for the fact that the wind profile may be displaying in
                a units system other than meters. (Default: 1).

        Returns:
            A tuple with five values

            - profile_polyline: A ladybug-geometry Polyline3D representing the
                wind profile.

            - mesh_arrows: A list of ladybug-geometry Mesh3D objects that
                represent the wind speed along with wind profile.

            - wind_speeds: A list of numbers for the wind speed associated with
                the mesh arrows.

            - wind_vectors: A list of ladybug-geometry Vector3D representing the
                wind vectors that built the profile.

            - anchor_pts: A list of ladybug-geometry Point3D representing the
                anchor points for the wind vectors.
        """
        self._check_profile_inputs(max_height, vector_spacing)
        bp = base_point
        mesh_arrows, wind_speeds = [], []
        profile_pts, wind_vectors, anchor_pts = [bp], [Vector3D(0, 0, 0)], [bp]
        m_val = max_height + vector_spacing
        for h in self._frange(vector_spacing, m_val, vector_spacing):
            m_ar, w_vec, a_pt, ws = self.mesh_arrow(
                meteorological_wind_speed, h, direction,
                base_point, length_dimension, height_dimension, scale_factor)
            mesh_arrows.append(m_ar)
            wind_speeds.append(ws)
            profile_pts.append(a_pt.move(w_vec))
            wind_vectors.append(w_vec)
            anchor_pts.append(a_pt)
        profile_polyline = Polyline3D(profile_pts)
        return profile_polyline, mesh_arrows, wind_speeds, wind_vectors, anchor_pts

    def speed_axis(
            self, max_speed=5, direction=None, base_point=Point3D(0, 0, 0),
            length_dimension=5, scale_factor=1, text_height=None):
        """Get a several objects for representing the X axis for wind speed.

        Args:
            max_speed: A number for the maximum wind speed along the axis
                in [m/s]. (Default: 5)
            direction: An optional number between 0 and 360 that represents the
                cardinal direction that the axis is facing in the XY
                plane. 0 = North, 90 = East, 180 = South, 270 = West. If None,
                the axis will simply be placed in the XY plane. (Default: None).
            base_point: A ladybug-geometry Point3D that represents the origin
                of the axis. (Default, (0, 0, 0)).
            length_dimension: A number to denote the length dimension of a 1 m/s
                wind vector in meters. (Default: 5).
            scale_factor: An optional number that will be multiplied by all dimensions
                to account for the fact that the wind profile may be displaying in
                a units system other than meters. (Default: 1).
            text_height: An optional number for the height of the text in the axis
                label. If None, the text height will be inferred based on the
                length_dimension. (Default: None).

        Returns:
            A tuple with three values.

            - axis_line: A ladybug-geometry Linesegment3D representing the axis.

            - axis_arrow: A ladybug-geometry Mesh3D representing the arrow head.

            - axis_ticks: A list of ladybug-geometry LineSegment3D representing the
                marks of speeds along the axis.

            - text_planes: A list of ladybug-geometry Planes for the axis text labels.

            - text: A list of text strings tha align with the text_planes for the
                text to display in the 3D scene.
        """
        # construct the axis line along the world X axis
        direction = self._flip_direction(direction)
        bp, max_speed = base_point, int(max_speed)
        end_x = bp.x + ((max_speed + 1) * length_dimension * scale_factor)
        ax_end_pt = Point3D(end_x, bp.y, bp.z)
        axis_line = LineSegment3D.from_end_points(bp, ax_end_pt)
        step_d = length_dimension * scale_factor
        # create the arrow at the end of the axis as a mesh
        a_d = step_d / 8
        ea_pt = Point3D(end_x + a_d * 3, bp.y, bp.z)
        if direction is None:
            m_pts = (Point3D(end_x, bp.y + a_d, bp.z),
                     Point3D(end_x, bp.y - a_d, bp.z), ea_pt)
        else:
            m_pts = (Point3D(end_x, bp.y, bp.z + a_d),
                     Point3D(end_x, bp.y, bp.z - a_d), ea_pt)
        axis_arrow = Mesh3D(m_pts, ((0, 1, 2),), colors=(self.BLACK,))
        # create the axis ticks and text planes
        tick_d = step_d / 6
        axis_ticks, text_planes, text = [], [], []
        for i in range(1, max_speed + 1):
            pt_x = bp.x + (step_d * i)
            pt_1 = Point3D(pt_x, bp.y, bp.z)
            if direction is None:
                pt_2 = Point3D(pt_x, bp.y - tick_d, bp.z)
                pt_3 = Point3D(pt_x, bp.y - (tick_d * 2), bp.z)
                txt_p = Plane(n=Vector3D(0, 0, 1), o=pt_3, x=Vector3D(1, 0, 0))
            else:
                pt_2 = Point3D(pt_x, bp.y, bp.z - tick_d)
                pt_3 = Point3D(pt_x, bp.y, bp.z - (tick_d * 2))
                txt_p = Plane(n=Vector3D(0, -1, 0), o=pt_3, x=Vector3D(1, 0, 0))
            axis_ticks.append(LineSegment3D.from_end_points(pt_1, pt_2))
            text_planes.append(txt_p)
            text.append(str(i))
        # add a text plane and string for the axis title
        txt_height = length_dimension / 2 if text_height is None else text_height
        sub_d = (tick_d * 2) + (txt_height * 2)
        ti_x = axis_line.midpoint.x
        if direction is None:
            pt_4 = Point3D(ti_x, bp.y - sub_d, bp.z)
            text_planes.append(Plane(n=Vector3D(0, 0, 1), o=pt_4, x=Vector3D(1, 0, 0)))
        else:
            pt_4 = Point3D(ti_x, bp.y, bp.z - sub_d)
            text_planes.append(Plane(n=Vector3D(0, -1, 0), o=pt_4, x=Vector3D(1, 0, 0)))
        text.append('Wind Speed (m/s)')
        # rotate the whole axis if a direction is specified
        if direction is not None:
            dir_radians = math.radians(90) - math.radians(direction)
            axis_line = axis_line.rotate_xy(dir_radians, bp)
            axis_arrow = axis_arrow.rotate_xy(dir_radians, bp)
            axis_ticks = [t.rotate_xy(dir_radians, bp) for t in axis_ticks]
            text_planes = [p.rotate_xy(dir_radians, bp) for p in text_planes]
        return axis_line, axis_arrow, axis_ticks, text_planes, text

    def height_axis(
            self, max_height=30, tick_spacing=4, direction=None,
            base_point=Point3D(0, 0, 0), scale_factor=1, text_height=None,
            feet_labels=False):
        """Get a several objects for representing the Y axis for height above the ground.

        Args:
            max_height: A number in meters to specify the maximum height of the
                wind profile curve. (Default: 30 meters).
            tick_spacing: A number in meters to specify the difference between
                each of axis ticks. (Default 4 meters).
            direction: An optional number between 0 and 360 that represents the
                cardinal direction that the wind profile is facing in the XY
                plane. 0 = North, 90 = East, 180 = South, 270 = West. If None,
                the axis will simply be placed in the XY plane. (Default: None).
            base_point: A ladybug-geometry Point3D that represents the ground
                location of the wind profile. (Default, (0, 0, 0)).
            scale_factor: An optional number that will be multiplied by all dimensions
                to account for the fact that the wind profile may be displaying in
                a units system other than meters. (Default: 1).
            text_height: An optional number for the height of the text in the axis
                label. If None, the text height will be inferred based on the
                tick_spacing. (Default: None).
            feet_labels: A boolean to note whether the text labels should be in
                feet (True) or meters (False). (Default: False).

        Returns:
            A tuple with three values.

            - axis_line: A ladybug-geometry Linesegment3D representing the axis.

            - axis_arrow: A ladybug-geometry Mesh3D representing the arrow head.

            - axis_ticks: A list of ladybug-geometry LineSegment3D representing the
                marks of heights along the axis.

            - text: A list of text strings tha align with the text_planes for the
                text to display in the 3D scene.
        """
        # construct the axis line
        direction = self._flip_direction(direction)
        bp = base_point
        end_v = (max_height + (tick_spacing / 2)) * scale_factor
        ax_end_pt = Point3D(bp.x, bp.y + end_v, bp.z) if direction is None \
            else Point3D(bp.x, bp.y, bp.z + end_v)
        axis_line = LineSegment3D.from_end_points(bp, ax_end_pt)
        step_d = tick_spacing * scale_factor
        # create the arrow at the end of the axis as a mesh
        a_d = step_d / 10
        if direction is None:
            ea_pt = Point3D(bp.x, ax_end_pt.y + (a_d * 3), bp.z)
            m_pts = (Point3D(bp.x + a_d, ax_end_pt.y, bp.z),
                     Point3D(bp.x - a_d, ax_end_pt.y, bp.z), ea_pt)
        else:
            ea_pt = Point3D(bp.x, bp.y, ax_end_pt.z + (a_d * 3))
            m_pts = (Point3D(bp.x + a_d, bp.y, ax_end_pt.z),
                     Point3D(bp.x - a_d, bp.y, ax_end_pt.z), ea_pt)
        axis_arrow = Mesh3D(m_pts, ((0, 1, 2),), colors=(self.BLACK,))
        # create the axis ticks and text planes
        tick_d = step_d / 6
        axis_ticks, text_planes, text = [], [], []
        mh = max_height + tick_spacing if max_height % tick_spacing == 0 else max_height
        for i in self._frange(0, mh, tick_spacing):
            pt_v = i * scale_factor
            if direction is None:
                pt_1 = Point3D(bp.x, bp.y + pt_v, bp.z)
                pt_2 = Point3D(bp.x - tick_d, bp.y + pt_v, bp.z)
                pt_3 = Point3D(bp.x - (tick_d * 2), bp.y + pt_v, bp.z)
                txt_p = Plane(n=Vector3D(0, 0, 1), o=pt_3, x=Vector3D(1, 0, 0))
            else:
                pt_1 = Point3D(bp.x, bp.y, bp.z + pt_v)
                pt_2 = Point3D(bp.x - tick_d, bp.y, bp.z + pt_v)
                pt_3 = Point3D(bp.x - (tick_d * 2), bp.y, bp.z + pt_v)
                txt_p = Plane(n=Vector3D(0, -1, 0), o=pt_3, x=Vector3D(1, 0, 0))
            axis_ticks.append(LineSegment3D.from_end_points(pt_1, pt_2))
            text_planes.append(txt_p)
            txt_str = str(int(i)) if not feet_labels else str(int(i * 3.28084))
            text.append(txt_str)
        # add a text plane and string for the axis title
        txt_height = tick_spacing / 2 if text_height is None else text_height
        sub_d = (tick_d * 2) + (txt_height * 4)
        if direction is None:
            ti_v = axis_line.midpoint.y
            pt_4 = Point3D(bp.x - sub_d, ti_v, bp.z)
            text_planes.append(Plane(n=Vector3D(0, 0, 1), o=pt_4, x=Vector3D(0, 1, 0)))
        else:
            ti_v = axis_line.midpoint.z
            pt_4 = Point3D(bp.x - sub_d, bp.y, ti_v)
            text_planes.append(Plane(n=Vector3D(0, -1, 0), o=pt_4, x=Vector3D(0, 0, 1)))
        units = 'ft' if feet_labels else 'm'
        text.append('Height ({})'.format(units))
        # rotate the whole axis if a direction is specified
        if direction is not None:
            dir_radians = math.radians(90) - math.radians(direction)
            axis_line = axis_line.rotate_xy(dir_radians, bp)
            axis_arrow = axis_arrow.rotate_xy(dir_radians, bp)
            axis_ticks = [t.rotate_xy(dir_radians, bp) for t in axis_ticks]
            text_planes = [p.rotate_xy(dir_radians, bp) for p in text_planes]
        return axis_line, axis_arrow, axis_ticks, text_planes, text

    def legend_plane(
            self, max_speed=5, direction=None, base_point=Point3D(0, 0, 0),
            length_dimension=5, scale_factor=1):
        """Get a recommended Plane for the default base plane of the legend.

        Args:
            max_speed: A number for the maximum wind speed along the axis
                in [m/s]. (Default: 5)
            direction: An optional number between 0 and 360 that represents the
                cardinal direction that the axis is facing in the XY
                plane. 0 = North, 90 = East, 180 = South, 270 = West. If None,
                the axis will simply be placed in the XY plane. (Default: None).
            base_point: A ladybug-geometry Point3D that represents the origin
                of the axis. (Default, (0, 0, 0)).
            length_dimension: A number to denote the length dimension of a 1 m/s
                wind vector in meters. (Default: 5).
            scale_factor: An optional number that will be multiplied by all dimensions
                to account for the fact that the wind profile may be displaying in
                a units system other than meters. (Default: 1).

        Returns:
            A ladybug-geometry Plane for the recommended legend plane.
        """
        direction = self._flip_direction(direction)
        bp, max_speed = base_point, int(max_speed)
        end_x = bp.x + ((max_speed + 2) * length_dimension * scale_factor)
        origin_pt = Point3D(end_x, bp.y, bp.z)
        if direction is None:
            return Plane(n=Vector3D(0, 0, 1), o=origin_pt, x=Vector3D(1, 0, 0))
        else:
            st_pl = Plane(n=Vector3D(0, -1, 0), o=origin_pt, x=Vector3D(1, 0, 0))
            dir_radians = math.radians(90) - math.radians(direction)
            return st_pl.rotate_xy(dir_radians, bp)

    def title_plane(
            self, direction=None, base_point=Point3D(0, 0, 0),
            length_dimension=5, scale_factor=1, text_height=None):
        """Get a recommended Plane for the default base plane of the title.

        Args:
            max_speed: A number for the maximum wind speed along the axis
                in [m/s]. (Default: 5)
            direction: An optional number between 0 and 360 that represents the
                cardinal direction that the axis is facing in the XY
                plane. 0 = North, 90 = East, 180 = South, 270 = West. If None,
                the axis will simply be placed in the XY plane. (Default: None).
            base_point: A ladybug-geometry Point3D that represents the origin
                of the axis. (Default, (0, 0, 0)).
            length_dimension: A number to denote the length dimension of a 1 m/s
                wind vector in meters. (Default: 5).
            scale_factor: An optional number that will be multiplied by all dimensions
                to account for the fact that the wind profile may be displaying in
                a units system other than meters. (Default: 1).
            text_height: An optional number for the height of the text in the axis
                label. If None, the text height will be inferred based on the
                length_dimension. (Default: None).

        Returns:
            A ladybug-geometry Plane for the recommended title plane.
        """
        direction = self._flip_direction(direction)
        bp = base_point
        step_d = length_dimension * scale_factor
        tick_d = step_d / 6
        txt_height = length_dimension / 2 if text_height is None else text_height
        sub_d = (tick_d * 2) + (txt_height * 5)
        if direction is None:
            origin_pt = Point3D(bp.x, bp.y - sub_d, bp.z)
            return Plane(n=Vector3D(0, 0, 1), o=origin_pt, x=Vector3D(1, 0, 0))
        else:
            origin_pt = Point3D(bp.x, bp.y, bp.z - sub_d)
            st_pl = Plane(n=Vector3D(0, -1, 0), o=origin_pt, x=Vector3D(1, 0, 0))
            dir_radians = math.radians(90) - math.radians(direction)
            return st_pl.rotate_xy(dir_radians, bp)

    def _check_terrain(self, value):
        """Check any string input for the terrain."""
        clean_input = value.lower()
        for key in self.TERRAINS:
            if key.lower() == clean_input:
                value = key
                break
        else:
            raise ValueError(
                'terrain {} is not recognized.\nChoose from the '
                'following:\n{}'.format(value, self.TERRAINS))
        return value

    def _compute_met_power_denom(self):
        """Compute the denominator of the power function."""
        h_ratio = self._met_boundary_layer_height / self._meteorological_height
        self._met_power_denom = h_ratio ** self._met_power_law_exponent

    def _compute_met_log_denom(self):
        """Compute the denominator of the logarithmic function."""
        h_ratio = self._meteorological_height / self._met_roughness_length
        self._met_log_denom = math.log(h_ratio)

    @staticmethod
    def _flip_direction(direction):
        """Flip the direction of a wind so it notes the orientation of arrows."""
        if direction is not None:
            if direction < 180:
                return direction + 180
            else:
                return direction - 180

    @staticmethod
    def _check_profile_inputs(max_height, vector_spacing):
        assert vector_spacing > 0, 'WindProfile vector spacing must be greater ' \
            'than zero. Got {}.'.format(vector_spacing)
        assert max_height > vector_spacing, 'WindProfile max height [{}] must be ' \
            'greater than vector spacing [{}].'.format(max_height, vector_spacing)

    @staticmethod
    def _frange(start, stop, step):
        """Range function capable of yielding float values."""
        while start < stop:
            yield start
            start += step

    def ToString(self):
        """Overwrite .NET ToString method."""
        return self.__repr__()

    def __repr__(self):
        """WindProfile representation."""
        return "WindProfile (terrain: {})".format(self.terrain)
