import os
import json

from ladybug_geometry.geometry3d.face import Face3D
from ladybug_geometry.geometry3d.mesh import Mesh3D

from ladybug.location import Location
from ladybug.sunpath import Sunpath
from ladybug.solarenvelope import SolarEnvelope


def test_init_solar_envelope():
    """Test the initialization of Sunpath and basic properties."""
    # get sun positions
    sunpath = Sunpath(latitude=40.72, longitude=-74.02)
    sun_vecs = []
    for hour in range(8, 16):
        sun = sunpath.calculate_sun(12, 21, hour)
        sun_vecs.append(sun.sun_vector)

    # load the site and the context
    site_mesh_file = './tests/assets/geo/mesh.json'
    with open(site_mesh_file) as json_file:
        site_mesh_data = json.load(json_file)
    site_mesh = Mesh3D.from_dict(site_mesh_data)
    context_file = './tests/assets/geo/faces.json'
    with open(context_file) as json_file:
        context_data = json.load(json_file)
    context_faces = [Face3D.from_dict(con) for con in context_data]

    # initialize solar envelope
    envelope = SolarEnvelope(site_mesh, context_faces, sun_vecs, solar_rights=True)
    str(envelope)  # test the string representation
    envelope_mesh = envelope.envelope_mesh()
    assert isinstance(envelope_mesh, Mesh3D)
