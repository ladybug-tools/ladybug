# coding=utf-8
from ladybug.location import Location
from ladybug.sunpath import Sunpath, Sun
from ladybug.dt import DateTime, Time
from ladybug.analysisperiod import AnalysisPeriod

from ladybug_geometry.geometry2d.pointvector import Point2D
from ladybug_geometry.geometry2d.line import LineSegment2D
from ladybug_geometry.geometry2d.polyline import Polyline2D
from ladybug_geometry.geometry3d.pointvector import Point3D, Vector3D
from ladybug_geometry.geometry3d.line import LineSegment3D
from ladybug_geometry.geometry3d.arc import Arc3D
from ladybug_geometry.geometry3d.polyline import Polyline3D

import datetime
import math
from pytest import approx


def test_init_sunpath():
    """Test the initialization of Sunpath and basic properties."""
    sunpath = Sunpath(latitude=40.72, longitude=-74.02)

    str(sunpath)  # test the string representation
    assert sunpath.latitude == 40.72
    assert sunpath.longitude == -74.02
    assert sunpath.time_zone == approx(-4.9346, rel=1e-3)
    assert sunpath.north_angle == 0
    assert sunpath.daylight_saving_period is None


def test_init_sun():
    """Test the initialization of Sun."""
    dt1 = DateTime(3, 21, 12, 30)
    sun = Sun(dt1, 45, 100, True, False, 0)
    
    str(sun)  # test the string representation
    hash(sun)  # ensure sun is hash-able
    assert sun.datetime == dt1
    assert sun.altitude == approx(45, rel=1e-2)
    assert sun.azimuth == sun.azimuth_from_y_axis == approx(100, rel=1e-2)
    assert sun.altitude_in_radians == approx(math.radians(45), rel=1e-2)
    assert sun.azimuth_in_radians == approx(math.radians(100), rel=1e-2)
    assert sun.is_solar_time
    assert not sun.is_daylight_saving
    assert sun.north_angle == 0
    assert sun.data is None
    assert sun.is_during_day
    assert isinstance(sun.sun_vector, Vector3D)
    assert isinstance(sun.sun_vector_reversed, Vector3D)
    assert isinstance(sun.position_3d(radius=1), Point3D)
    assert isinstance(sun.position_2d(radius=1), Point2D)
    assert isinstance(sun.position_2d(projection='Stereographic', radius=1), Point2D)


def test_azimuth_from_y_axis():
    """Test the azimuth_from_y_axis property of the Sun."""
    dt1 = DateTime(3, 21, 12, 30)

    sun1 = Sun(dt1, 45, 100, True, False, 10)
    assert sun1.azimuth_from_y_axis == 90
    sun1 = Sun(dt1, 45, 100, True, False, -10)
    assert sun1.azimuth_from_y_axis == 110
    sun1 = Sun(dt1, 45, 100, True, False, -270)
    assert sun1.azimuth_from_y_axis == 10

def test_from_location():
    """Test the initialization of Sunpath from a Location."""
    sydney = Location('Sydney', 'AUS', latitude=-33.87, longitude=151.22,
                      time_zone=10)
    sunpath = Sunpath.from_location(sydney)
    assert sunpath.latitude == -33.87
    assert sunpath.longitude == 151.22
    assert sunpath.time_zone == 10


def test_vs_noaa_new_york():
    """Test to be sure that the sun positions align with the NOAA formula."""
    nyc = Location('New_York', 'USA', latitude=40.72, longitude=-74.02,
                   time_zone=-5)
    sp = Sunpath.from_location(nyc)
    sun = sp.calculate_sun(month=9, day=15, hour=11.0)
    assert round(sun.altitude, 2) == 50.35
    assert round(sun.azimuth, 2) == 159.72


def test_vs_noaa_sydney():
    """Test to be sure that the sun positions align with the NOAA formula."""
    sydney = Location('Sydney', country='AUS', latitude=-33.87, longitude=151.22,
                      time_zone=10)
    sp = Sunpath.from_location(sydney)
    sun = sp.calculate_sun(month=11, day=15, hour=11.0)
    assert round(sun.altitude, 2) == 72.26
    assert round(sun.azimuth, 2) == 32.37

    sun2 = sp.calculate_sun_from_date_time(datetime.datetime(2019, 6, 21, 9))
    assert round(sun2.altitude, 2) == 18.99
    assert round(sun2.azimuth, 2) == 42.54


def test_calculate_sun():
    """Test the varios calculate_sun methods to be sure they all give the same result."""
    nyc = Location('New_York', 'USA', latitude=40.72, longitude=-74.02, time_zone=-5)
    sp = Sunpath.from_location(nyc)

    dt1 = DateTime(3, 21, 9, 30)
    sun1 = sp.calculate_sun(dt1.month, dt1.day, dt1.float_hour)
    sun2 = sp.calculate_sun_from_hoy(dt1.hoy)
    sun3 = sp.calculate_sun_from_moy(dt1.moy)
    sun4 = sp.calculate_sun_from_date_time(dt1)

    assert sun1 == sun2 == sun3 == sun4
    assert round(sun1.altitude, 2) == 36.90
    assert round(sun1.azimuth, 2) == 129.23


def test_sunrise_sunset():
    """Test to be sure that the sunrise/sunset aligns with the NOAA formula."""
    sydney = Location('Sydney', country='AUS', latitude=-33.87, longitude=151.22,
                      time_zone=10)
    sp = Sunpath.from_location(sydney)

    # use the depression for apparent sunrise/sunset
    srss_dict = sp.calculate_sunrise_sunset(6, 21, depression=0.8333)
    
    assert srss_dict['sunrise'] == DateTime(6, 21, 7, 0)
    assert srss_dict['noon'] == DateTime(6, 21, 11, 57)
    assert srss_dict['sunset'] == DateTime(6, 21, 16, 54)

    # use the depression for actual sunrise/sunset
    srss_dict = sp.calculate_sunrise_sunset(6, 21, depression=0.5334)
    assert srss_dict['sunrise'] == DateTime(6, 21, 7, 2)
    assert srss_dict['noon'] == DateTime(6, 21, 11, 57)
    assert srss_dict['sunset'] == DateTime(6, 21, 16, 52)


def test_solar_time():
    """Test to be sure that solar time is being computed correctly."""
    loc = Location('SHANGHAI', None, 'HONGQIAO', 31.17, 121.43, 8.0, 7.00)
    sp = Sunpath.from_location(loc)

    sun = sp.calculate_sun(3, 21, 12, True)
    assert sun.azimuth == approx(180, rel=1e-2)
    sun = sp.calculate_sun(3, 21, 6, True)
    assert sun.azimuth == approx(90, rel=1e-2)
    sun = sp.calculate_sun(3, 21, 18, True)
    assert sun.azimuth == approx(270, rel=1e-2)


def test_daylight_saving():
    """Test the applicaiton of daylight saving time."""
    nyc = Location('New_York', country='USA', latitude=40.72, longitude=-74.02,
                   time_zone=-5)
    daylight_saving = AnalysisPeriod(st_month=3, st_day=8, st_hour=2,
                                     end_month=11, end_day=1, end_hour=2)
    sp = Sunpath.from_location(nyc, daylight_saving_period=daylight_saving)
    dt1 = DateTime(6, 21, 12, 0)
    dt2 = DateTime(12, 21, 12, 0)
    dt3 = DateTime(6, 21, 0)
    dt4 = DateTime(12, 21, 0)

    assert sp.is_daylight_saving_hour(dt1)
    assert not sp.is_daylight_saving_hour(dt2)
    assert sp.is_daylight_saving_hour(dt3)
    assert not sp.is_daylight_saving_hour(dt4)

    sun1ds = sp.calculate_sun_from_date_time(dt1)
    sun2ds = sp.calculate_sun_from_date_time(dt2)
    sun3ds = sp.calculate_sun_from_date_time(dt3)
    sun4ds = sp.calculate_sun_from_date_time(dt4)

    sp.daylight_saving_period = None

    assert sun1ds != sp.calculate_sun_from_date_time(dt1)
    assert sun3ds != sp.calculate_sun_from_date_time(dt3)
    assert sun1ds.altitude == \
        approx(sp.calculate_sun_from_date_time(dt1.sub_hour(1)).altitude, rel=1e-2)
    assert sun3ds.altitude == \
        approx(sp.calculate_sun_from_date_time(dt3.sub_hour(1)).altitude, rel=1e-2)

    sun2 = sp.calculate_sun_from_date_time(dt2)
    sun4 = sp.calculate_sun_from_date_time(dt4)
    assert sun2 == sun2ds
    assert sun4 == sun4ds


def test_leap_year():
    """Test the use of the sunpath with leap years."""
    nyc = Location('New_York', country='USA', latitude=40.72, longitude=-74.02,
                   time_zone=-5)
    sp = Sunpath.from_location(nyc)
    sp.is_leap_year = True
    sun = sp.calculate_sun(month=2, day=29, hour=11.0)
    assert sun.datetime == DateTime(2, 29, 11, leap_year=True)
    assert sun.datetime.year == 2016
    assert sun.datetime.month == 2
    assert sun.datetime.day == 29
    assert sun.datetime.hour == 11


def test_north_angle():
    """Test the north_angle property on the sun path."""
    nyc = Location('New_York', country='USA', latitude=40.72, longitude=-74.02,
                   time_zone=-5)
    sp = Sunpath.from_location(nyc)

    sp.north_angle = 90
    assert sp.north_angle == 90

    sun = sp.calculate_sun(3, 21, 6, True)
    assert sun.azimuth == approx(90, rel=1e-2)
    assert sun.is_solar_time
    assert sun.north_angle == 90
    assert sun.position_3d(radius=1).y == approx(1, rel=1e-2)
    assert sun.position_3d(radius=1).x < 1e-9


def test_analemma_suns():
    """Test the analemma_suns method."""
    nyc = Location('New_York', country='USA', latitude=40.72, longitude=-74.02,
                   time_zone=-5)
    sp = Sunpath.from_location(nyc)

    assert len(sp.analemma_suns(Time(12), True, True)) == 12
    assert len(sp.analemma_suns(Time(6), True, True)) == 7
    assert len(sp.analemma_suns(Time(0), True, True)) == 0
    assert len(sp.analemma_suns(Time(6), False, True)) == 12
    assert len(sp.analemma_suns(Time(0), False, True)) == 12

    for sun in sp.analemma_suns(Time(12)):
        assert isinstance(sun, Sun)
    
    assert len(sp.hourly_analemma_suns()) == 24
    for hr in sp.hourly_analemma_suns():
        for sun in hr:
            assert isinstance(sun, Sun)


def test_analemma_geometry():
    """Test the analemma_suns method."""
    nyc = Location('New_York', country='USA', latitude=40.72, longitude=-74.02,
                   time_zone=-5)
    sp = Sunpath.from_location(nyc)

    radius = 100
    analemma_geo = sp.hourly_analemma_polyline3d(radius=radius)
    assert len(analemma_geo) == 15
    for pline in analemma_geo:
        assert isinstance(pline, Polyline3D)

    analemma_geo = sp.hourly_analemma_polyline2d(radius=radius)
    assert len(analemma_geo) == 15
    for pline in analemma_geo:
        assert isinstance(pline, Polyline2D)


def test_analemma_daytime_with_linesegment():
    """Test the hourly_analemma_polyline3d with a latitude that yields a line segment."""
    test_loc = Location('Test Location', latitude=51, longitude=0)
    sp = Sunpath.from_location(test_loc)

    l_seg_count = 0
    for pline in sp.hourly_analemma_polyline3d():
        if isinstance(pline, LineSegment3D):
            l_seg_count += 1
    assert l_seg_count == 0

    l_seg_count = 0
    for pline in sp.hourly_analemma_polyline2d():
        if isinstance(pline, LineSegment2D):
            l_seg_count += 1
    assert l_seg_count == 0


def test_day_arc_geometry():
    """Test the day_arc3d method."""
    nyc = Location('New_York', country='USA', latitude=40.72, longitude=-74.02,
                   time_zone=-5)
    sp = Sunpath.from_location(nyc)

    radius = 100

    arc_geo = sp.day_arc3d(3, 21, radius=radius)
    assert isinstance(arc_geo, Arc3D)
    assert arc_geo.length == approx(math.pi * radius, rel=1e-2)

    arc_geo = sp.day_polyline2d(3, 21, radius=radius)
    assert isinstance(arc_geo, Polyline2D)

    arc_geo = sp.monthly_day_arc3d(radius=radius)
    assert len(arc_geo) == 12
    for pline in arc_geo:
        assert isinstance(pline, Arc3D)

    arc_geo = sp.monthly_day_polyline2d(radius=radius)
    assert len(arc_geo) == 12
    for pline in arc_geo:
        assert isinstance(pline, Polyline2D)


def test_exact_solar_noon():
    """Test to be sure we don't get a math domain error at solar noon."""
    loc = Location('SHANGHAI', None, 'HONGQIAO', 31.17, 121.43, 8.0, 7.00)
    sp = Sunpath.from_location(loc)
    
    suns = []
    for i in range(1, 13):
        sun = sp.calculate_sun(i, 21, 12, True)
        assert sun.azimuth == approx(180, rel=1e-2)
        suns.append(sun.sun_vector)
    assert len(suns) == 12


def test_north_south_pole():
    """Test to be sure we don't get a math domain error at the poles."""
    loc = Location("Santa's House", None, 'North Pole', 90, 0, 0, 0)
    sp = Sunpath.from_location(loc)
    suns = sp.hourly_analemma_suns()
    assert len(suns) == 24

    loc = Location("Santa's Other House", None, 'South Pole', -90, 0, 0, 0)
    sp = Sunpath.from_location(loc)
    suns = sp.hourly_analemma_suns()
    assert len(suns) == 24
