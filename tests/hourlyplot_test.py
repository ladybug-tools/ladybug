# coding=utf-8
from __future__ import division

from ladybug.datatype.temperature import Temperature
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.header import Header
from ladybug.legend import Legend, LegendParameters
from ladybug.datacollection import HourlyContinuousCollection
from ladybug.datacollectionimmutable import HourlyContinuousCollectionImmutable
from ladybug.hourlyplot import HourlyPlot
from ladybug.epw import EPW

from ladybug_geometry.geometry2d.pointvector import Point2D
from ladybug_geometry.geometry2d.line import LineSegment2D
from ladybug_geometry.geometry2d.polyline import Polyline2D
from ladybug_geometry.geometry2d.mesh import Mesh2D
from ladybug_geometry.geometry3d.pointvector import Point3D
from ladybug_geometry.geometry3d.plane import Plane
from ladybug_geometry.geometry3d.line import LineSegment3D
from ladybug_geometry.geometry3d.polyline import Polyline3D
from ladybug_geometry.geometry3d.mesh import Mesh3D


def test_hourlyplot_init():
    """Test the initialization of HourlyPlot and basic properties."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(range(8760))
    data_coll = HourlyContinuousCollection(header, values)
    hour_plot = HourlyPlot(data_coll)

    str(hour_plot)  # test the string representation
    assert isinstance(hour_plot.data_collection, HourlyContinuousCollectionImmutable)
    assert isinstance(hour_plot.legend_parameters, LegendParameters)
    assert hour_plot.base_point == Point3D(0, 0, 0)
    assert hour_plot.x_dim == 1
    assert hour_plot.y_dim == 4
    assert hour_plot.z_dim == 0
    assert hour_plot.values == data_coll.values

    mesh = hour_plot.colored_mesh2d
    assert isinstance(mesh, Mesh2D)
    assert len(mesh.faces) == 8760
    mesh = hour_plot.colored_mesh3d
    assert isinstance(mesh, Mesh3D)
    assert len(mesh.faces) == 8760

    border = hour_plot.chart_border2d
    assert isinstance(border, Polyline2D)
    assert len(border.segments) == 4
    border = hour_plot.chart_border3d
    assert isinstance(border, Polyline3D)
    assert len(border.segments) == 4

    hour_txt = hour_plot.hour_labels
    assert all(isinstance(txt, str) for txt in hour_txt)
    hour_lines = hour_plot.hour_lines2d
    hour_pts = hour_plot.hour_label_points2d
    assert len(hour_lines) == len(hour_txt) == len(hour_pts) == 5
    assert all(isinstance(line, LineSegment2D) for line in hour_lines)
    assert all(isinstance(pt, Point2D) for pt in hour_pts)
    hour_lines = hour_plot.hour_lines3d
    hour_pts = hour_plot.hour_label_points3d
    assert len(hour_lines) == len(hour_txt) == len(hour_pts) == 5
    assert all(isinstance(line, LineSegment3D) for line in hour_lines)
    assert all(isinstance(pt, Point3D) for pt in hour_pts)

    month_txt = hour_plot.month_labels
    assert all(isinstance(txt, str) for txt in month_txt)
    month_lines = hour_plot.month_lines2d
    month_pts = hour_plot.month_label_points2d
    assert len(month_txt) == len(month_pts) == 12
    assert len(month_lines) == 11
    assert all(isinstance(line, LineSegment2D) for line in month_lines)
    assert all(isinstance(pt, Point2D) for pt in month_pts)
    month_lines = hour_plot.month_lines3d
    month_pts = hour_plot.month_label_points3d
    assert len(month_txt) == len(month_pts) == 12
    assert len(month_lines) == 11
    assert all(isinstance(line, LineSegment3D) for line in month_lines)
    assert all(isinstance(pt, Point3D) for pt in month_pts)

    assert isinstance(hour_plot.legend, Legend)

    assert isinstance(hour_plot.title_text, str)
    assert 'Temperature' in hour_plot.title_text
    assert isinstance(hour_plot.lower_title_location, Plane)
    assert isinstance(hour_plot.upper_title_location, Plane)


def test_hourlyplot_custom():
    """Test the initialization of HourlyPlot with custom properties."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(range(8760))
    data_coll = HourlyContinuousCollection(header, values)
    hour_plot = HourlyPlot(data_coll, LegendParameters(), Point3D(10, 10, 10), 2, 2, 100)

    assert hour_plot.base_point == Point3D(10, 10, 10)
    assert hour_plot.x_dim == 2
    assert hour_plot.y_dim == 2
    assert hour_plot.z_dim == 100

    mesh = hour_plot.colored_mesh3d
    assert isinstance(mesh, Mesh3D)
    assert len(mesh.faces) == 8760
    assert mesh.min == Point3D(10, 10, 10)
    assert mesh.max == Point3D(2 * 365 + 10, 2 * 24 + 10, 110)


def test_hourlyplot_init_from_z_dim_per_unit():
    """Test the initialization of HourlyPlot from_z_dim_per_unit."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(range(8760))
    data_coll = HourlyContinuousCollection(header, values)
    hour_plot = HourlyPlot.from_z_dim_per_unit(
        data_coll, LegendParameters(), Point3D(10, 10, 10), 2, 2, 1)

    assert hour_plot.base_point == Point3D(10, 10, 10)
    assert hour_plot.x_dim == 2
    assert hour_plot.y_dim == 2
    assert hour_plot.z_dim == 8759

    mesh = hour_plot.colored_mesh3d
    assert isinstance(mesh, Mesh3D)
    assert len(mesh.faces) == 8760
    assert mesh.min == Point3D(10, 10, 10)
    assert mesh.max == Point3D(2 * 365 + 10, 2 * 24 + 10, 8759 + 10)


def test_hourlyplot_sub_hourly():
    """Test the initialization of HourlyPlot and basic properties."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(range(8760))
    dc1 = HourlyContinuousCollection(header, values)
    data_coll = dc1.interpolate_to_timestep(4)
    hour_plot = HourlyPlot(data_coll, y_dim=1)

    mesh = hour_plot.colored_mesh2d
    assert isinstance(mesh, Mesh2D)
    assert len(mesh.faces) == 8760 * 4
    assert mesh.min == Point2D(0, 0)
    assert mesh.max == Point2D(365, 4 * 24)


def test_hourlyplot_analysis_period():
    """Test the initialization of HourlyPlot with an analysis period."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(range(8760))
    data_coll = HourlyContinuousCollection(header, values)
    period = AnalysisPeriod(1, 1, 8, 1, 31, 17)
    data_coll = data_coll.filter_by_analysis_period(period)
    hour_plot = HourlyPlot(data_coll, y_dim=1)

    assert hour_plot.analysis_period == period
    mesh = hour_plot.colored_mesh2d
    assert isinstance(mesh, Mesh2D)
    assert len(mesh.faces) == 31 * (17 - 8 + 1)
    assert mesh.min == Point2D(0, 0)
    assert mesh.max == Point2D(31, 17 - 8 + 1)


def test_hourlyplot_reversed_analysis_period():
    """Test the initialization of HourlyPlot with a reversed analysis period."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(range(8760))
    data_coll = HourlyContinuousCollection(header, values)
    period = AnalysisPeriod(12, 1, 0, 1, 31, 23)
    data_coll = data_coll.filter_by_analysis_period(period)
    hour_plot = HourlyPlot(data_coll, y_dim=1)

    assert hour_plot.analysis_period == period
    mesh = hour_plot.colored_mesh2d
    assert isinstance(mesh, Mesh2D)
    assert len(mesh.faces) == 31 * 2 * 24
    assert mesh.min == Point2D(0, 0)
    assert mesh.max == Point2D(31 * 2, 24)


def test_hourlyplot_conditional_statement():
    """Test the initialization of HourlyPlot with a conditional statement."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(range(8760))
    data_coll = HourlyContinuousCollection(header, values)
    data_coll = data_coll.filter_by_conditional_statement('a >= 60')
    hour_plot = HourlyPlot(data_coll, y_dim=1)

    mesh = hour_plot.colored_mesh2d
    assert len(mesh.faces) == 8700
    assert mesh.min == Point2D(0, 0)
    assert mesh.max == Point2D(365, 24)


def test_hourlyplot_custom_hour_labels():
    """Test the initialization of HourlyPlot and basic properties."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(range(8760))
    data_coll = HourlyContinuousCollection(header, values)
    hour_plot = HourlyPlot(data_coll)

    custom_labels = [0, 3, 6, 9, 12, 15, 18, 21, 24]

    hour_txt = hour_plot.custom_hour_labels(custom_labels)
    assert all(isinstance(txt, str) for txt in hour_txt)
    hour_lines = hour_plot.custom_hour_lines2d(custom_labels)
    hour_pts = hour_plot.custom_hour_label_points2d(custom_labels)
    assert len(hour_lines) == len(hour_txt) == len(hour_pts) == 9
    assert all(isinstance(line, LineSegment2D) for line in hour_lines)
    assert all(isinstance(pt, Point2D) for pt in hour_pts)
    hour_lines = hour_plot.custom_hour_lines3d(custom_labels)
    hour_pts = hour_plot.custom_hour_label_points3d(custom_labels)
    assert len(hour_lines) == len(hour_txt) == len(hour_pts) == 9
    assert all(isinstance(line, LineSegment3D) for line in hour_lines)
    assert all(isinstance(pt, Point3D) for pt in hour_pts)


def test_hourlyplot_epw():
    """Test the initialization of HourlyPlot with EPW data collections."""
    path = './tests/assets/epw/tokyo.epw'
    epw = EPW(path)

    hour_plot = HourlyPlot(epw.dry_bulb_temperature)
    mesh = hour_plot.colored_mesh2d
    assert len(mesh.faces) == 8760
    assert 'Dry Bulb Temperature' in hour_plot.title_text
    assert 'C' in hour_plot.legend.title

    hour_plot = HourlyPlot(epw.global_horizontal_radiation)
    mesh = hour_plot.colored_mesh2d
    assert len(mesh.faces) == 8760
    assert 'Global Horizontal Radiation' in hour_plot.title_text
    assert 'Wh/m2' in hour_plot.legend.title
