# coding=utf-8
import os

from ladybug_geometry.geometry2d import Vector2D
from ladybug.location import Location
from ladybug.designday import DesignDay
from ladybug.projectinfo import ProjectInfo

SAMPLE_URL = 'https://energyplus-weather.s3.amazonaws.com/' \
    'north_and_central_america_wmo_region_4/USA/NY/' \
    'USA_NY_New.York-J.F.Kennedy.Intl.AP.744860_TMY3/' \
    'USA_NY_New.York-J.F.Kennedy.Intl.AP.744860_TMY3.zip'


def test_project_info_init():
    """Test the initialization of ProjectInfo and basic properties."""
    project = ProjectInfo()
    str(project)  # test the string representation

    assert project.north_angle == 0
    assert project.north_vector == Vector2D(0, 1)
    assert len(project.weather_urls) == 0
    assert project.location is None
    assert project.default_epw_file is None
    assert project.default_stat_file is None
    assert project.default_ddy_file is None
    assert len(project.default_design_days) == 0
    assert project.ashrae_climate_zone is None
    assert len(project.building_type) == 0
    assert project.gbxml_building_type == 'Unknown'
    assert len(project.vintage) == 0


def test_project_info_setability():
    """Test the setting of properties of ProjectInfo."""
    city = 'New York JFK'
    country = 'USA'
    latitude = 40.65
    longitude = -73.8
    time_zone = -5
    elevation = 5
    loc = Location(city=city, country=country, latitude=latitude,
                   longitude=longitude, time_zone=time_zone, elevation=elevation)
    project = ProjectInfo(
        15, location=loc, ashrae_climate_zone='4A',
        building_type=['LargeOffice'], vintage=['ASHRAE_2019']
    )

    assert project.north_angle == 15
    assert project.location == loc
    assert project.ashrae_climate_zone == '4A'
    assert project.building_type == ('LargeOffice',)
    assert project.vintage == ('ASHRAE_2019',)

    project.north_angle = 10
    assert project.north_angle == 10
    loc2 = Location(city='Project Site', country=country, latitude=40.7793,
                    longitude=-73.9691, time_zone=time_zone, elevation=40)
    project.location = loc2
    assert project.location == loc2
    project.ashrae_climate_zone = 4
    assert project.ashrae_climate_zone == '4A'
    project.ashrae_climate_zone = '4B'
    assert project.ashrae_climate_zone == '4B'
    project.building_type = ['LargeOffice', 'HighriseApartment']
    assert project.building_type == ('LargeOffice', 'HighriseApartment')
    project.vintage = ['ASHRAE_2019', 'DOE_Ref_1980_2004']
    assert project.vintage == ('ASHRAE_2019', 'DOE_Ref_1980_2004')


def test_project_info_defaults_from_url():
    """Test the default properties of ProjectInfo from the weather URLs."""
    latitude = 40.65
    longitude = -73.8
    time_zone = -5
    elevation = 5
    project = ProjectInfo(
        15, weather_urls=[SAMPLE_URL],
        building_type=['LargeOffice'], vintage=['ASHRAE_2019']
    )

    if os.name == 'nt':
        assert project.north_angle == 15
        assert len(project.weather_urls) == 1
        assert os.path.isfile(project.default_epw_file)
        assert os.path.isfile(project.default_stat_file)
        assert os.path.isfile(project.default_ddy_file)
        assert len(project.default_design_days) == 7
        for d_day in project.default_design_days:
            assert isinstance(d_day, DesignDay)
        assert project.location.latitude == latitude
        assert project.location.longitude == longitude
        assert project.location.time_zone == time_zone
        assert project.location.elevation == elevation
        assert project.ashrae_climate_zone == '4A'
        assert project.building_type == ('LargeOffice',)
        assert project.vintage == ('ASHRAE_2019',)


def test_project_info_equality():
    """Test the equality of ProjectInfo objects."""
    city = 'New York JFK'
    country = 'USA'
    latitude = 40.65
    longitude = -73.8
    time_zone = -5
    elevation = 5
    loc = Location(city=city, country=country, latitude=latitude,
                   longitude=longitude, time_zone=time_zone, elevation=elevation)
    loc2 = Location(city='Project Site', country=country, latitude=40.7793,
                    longitude=-73.9691, time_zone=time_zone, elevation=40)
    project = ProjectInfo(
        15, location=loc, ashrae_climate_zone='4A',
        building_type=['LargeOffice'], vintage=['ASHRAE_2019']
    )
    project_dup = project.duplicate()
    project_alt = ProjectInfo(
        15, location=loc2, ashrae_climate_zone='4A',
        building_type=['LargeOffice'], vintage=['ASHRAE_2019']
    )

    assert project is project
    assert project is not project_dup
    assert project == project_dup
    project_dup.north_angle = 10
    assert project != project_dup
    assert project != project_alt


def test_project_info_dict_methods():
    """Test the to/from dict methods."""
    city = 'New York JFK'
    country = 'USA'
    latitude = 40.65
    longitude = -73.8
    time_zone = -5
    elevation = 5
    loc = Location(city=city, country=country, latitude=latitude,
                   longitude=longitude, time_zone=time_zone, elevation=elevation)
    project = ProjectInfo(
        15, location=loc, ashrae_climate_zone='4A',
        building_type=['LargeOffice'], vintage=['ASHRAE_2019']
    )

    project_dict = project.to_dict()
    new_project = ProjectInfo.from_dict(project_dict)
    assert new_project == project
    assert project_dict == new_project.to_dict()

    pi_file = project.to_json()
    new_project = ProjectInfo.from_json(pi_file)
    assert new_project == project
