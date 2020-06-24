# coding=utf-8
from __future__ import division

from ladybug.datatype.temperature import Temperature
from ladybug.datatype.fraction import RelativeHumidity
from ladybug.datatype.energy import Energy
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.header import Header
from ladybug.legend import Legend, LegendParameters
from ladybug.datacollection import HourlyContinuousCollection, DailyCollection, \
    MonthlyCollection, MonthlyPerHourCollection
from ladybug.datacollectionimmutable import HourlyContinuousCollectionImmutable
from ladybug.monthlychart import MonthlyChart
from ladybug.epw import EPW

from ladybug_geometry.geometry2d.pointvector import Point2D
from ladybug_geometry.geometry2d.line import LineSegment2D
from ladybug_geometry.geometry2d.polyline import Polyline2D
from ladybug_geometry.geometry2d.mesh import Mesh2D
from ladybug_geometry.geometry3d.plane import Plane


def test_monthlychart_init():
    """Test the initialization of MonthlyChart and basic properties."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = [i / 365 for i in range(8760)]
    data_coll = HourlyContinuousCollection(header, values)
    month_chart = MonthlyChart([data_coll])

    str(month_chart)  # test the string representation
    assert isinstance(month_chart.data_collections, tuple)
    assert isinstance(month_chart.data_collections[0], HourlyContinuousCollectionImmutable)
    assert isinstance(month_chart.legend_parameters, LegendParameters)
    assert month_chart.base_point == Point2D(0, 0)
    assert month_chart.x_dim == 10
    assert month_chart.y_dim == 40
    assert not month_chart.stack
    assert month_chart.percentile == 34

    meshes = month_chart.data_meshes
    assert isinstance(meshes[0], Mesh2D)
    assert len(meshes[0].faces) == 24 * 12
    plines = month_chart.data_polylines
    assert isinstance(plines[0], Polyline2D)
    assert len(plines) == 3 * 12

    border = month_chart.chart_border
    assert isinstance(border, Polyline2D)
    assert len(border.segments) == 4

    y_txt = month_chart.y_axis_labels1
    assert all(isinstance(txt, str) for txt in y_txt)
    y_lines = month_chart.y_axis_lines
    y_pts = month_chart.y_axis_label_points1
    assert len(y_lines) == len(y_txt) == len(y_pts) == 11
    assert all(isinstance(line, LineSegment2D) for line in y_lines)
    assert all(isinstance(pt, Point2D) for pt in y_pts)
    assert isinstance(month_chart.y_axis_title_text1, str)
    assert 'Temperature' in month_chart.y_axis_title_text1
    assert isinstance(month_chart.y_axis_title_location1, Plane)

    assert month_chart.y_axis_labels2 is None
    assert month_chart.y_axis_label_points2 is None
    assert month_chart.y_axis_title_text2 is None
    assert month_chart.y_axis_title_location2 is None

    month_txt = month_chart.month_labels
    assert all(isinstance(txt, str) for txt in month_txt)
    month_lines = month_chart.month_lines
    month_pts = month_chart.month_label_points
    assert len(month_txt) == len(month_pts) == 12
    assert len(month_lines) == 11
    assert all(isinstance(line, LineSegment2D) for line in month_lines)
    assert all(isinstance(pt, Point2D) for pt in month_pts)

    assert isinstance(month_chart.legend, Legend)

    assert isinstance(month_chart.title_text, str)
    assert isinstance(month_chart.lower_title_location, Plane)
    assert isinstance(month_chart.upper_title_location, Plane)


def test_monthlychart_two_axes():
    """Test the MonthlyChart with two Y-axes."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = [i for i in range(12)]
    date_t = list(range(1, 13))
    data_coll = MonthlyCollection(header, values, date_t)

    header2 = Header(RelativeHumidity(), '%', AnalysisPeriod())
    values2 = [i for i in range(10, 70, 5)]
    data_coll2 = MonthlyCollection(header2, values2, date_t)
    month_chart = MonthlyChart([data_coll, data_coll2])

    y_txt = month_chart.y_axis_labels2
    assert all(isinstance(txt, str) for txt in y_txt)
    y_lines = month_chart.y_axis_lines
    y_pts = month_chart.y_axis_label_points2
    assert len(y_lines) == len(y_txt) == len(y_pts) == 11
    assert all(isinstance(line, LineSegment2D) for line in y_lines)
    assert all(isinstance(pt, Point2D) for pt in y_pts)
    assert isinstance(month_chart.y_axis_title_text2, str)
    assert 'Fraction' in month_chart.y_axis_title_text2
    assert isinstance(month_chart.y_axis_title_location2, Plane)

    # ensure the first axis was not affected
    y_txt = month_chart.y_axis_labels1
    assert all(isinstance(txt, str) for txt in y_txt)
    y_pts = month_chart.y_axis_label_points1
    assert len(y_lines) == len(y_txt) == len(y_pts) == 11
    assert all(isinstance(pt, Point2D) for pt in y_pts)
    assert isinstance(month_chart.y_axis_title_text1, str)
    assert 'Temperature' in month_chart.y_axis_title_text1
    assert isinstance(month_chart.y_axis_title_location1, Plane)


def test_monthlychart_set_min_max_by_index():
    """Test the set_minimum_by_index amd set_maximum_by_index methods."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = [i for i in range(12)]
    date_t = list(range(1, 13))
    data_coll = MonthlyCollection(header, values, date_t)
    header2 = Header(RelativeHumidity(), '%', AnalysisPeriod())
    values2 = [i for i in range(10, 70, 5)]
    data_coll2 = MonthlyCollection(header2, values2, date_t)
    l_par = LegendParameters(min=-20, max=40)
    l_par.decimal_count = 0

    month_chart = MonthlyChart([data_coll, data_coll2], legend_parameters=l_par)

    assert month_chart.y_axis_labels1[0] == '-20'
    assert month_chart.y_axis_labels1[-1] == '40'

    month_chart.set_minimum_by_index(0, 1)
    assert month_chart.y_axis_labels2[0] == '0'
    month_chart.set_maximum_by_index(100, 1)
    assert month_chart.y_axis_labels2[-1] == '100'


def test_monthlychart_hourly_stack():
    """Test the initialization of MonthlyChart with hourly stacked data collections."""
    header = Header(Energy(), 'kWh', AnalysisPeriod())
    values = [i / 365 for i in range(20, 8780)]
    data_coll = HourlyContinuousCollection(header, values)
    month_chart = MonthlyChart([data_coll])

    meshes = month_chart.data_meshes
    assert len(meshes) == 1
    assert isinstance(meshes[0], Mesh2D)
    assert len(meshes[0].faces) == 24 * 12
    assert month_chart.y_axis_labels1[0] == '0.00'

    header2 = Header(Energy(), 'kWh', AnalysisPeriod())
    values2 = [i / 365 for i in range(8760, 0, -1)]
    data_coll2 = HourlyContinuousCollection(header2, values2)
    month_chart = MonthlyChart([data_coll, data_coll2])

    meshes = month_chart.data_meshes
    assert len(meshes) == 2
    assert isinstance(meshes[1], Mesh2D)
    assert len(meshes[1].faces) == 24 * 12

    month_chart = MonthlyChart([data_coll, data_coll2], stack=True)
    meshes = month_chart.data_meshes
    assert len(meshes) == 2
    assert isinstance(meshes[1], Mesh2D)
    assert len(meshes[1].faces) == 24 * 12
    plines = month_chart.data_polylines
    assert isinstance(plines[0], Polyline2D)
    assert len(plines) == 2 * 12 * 2


def test_monthlychart_monthly():
    """Test the initialization of MonthlyChart with monthly data collections."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = [i for i in range(12)]
    date_t = list(range(1, 13))
    data_coll = MonthlyCollection(header, values, date_t)
    month_chart = MonthlyChart([data_coll])

    meshes = month_chart.data_meshes
    assert len(meshes) == 1
    assert isinstance(meshes[0], Mesh2D)
    assert len(meshes[0].faces) == 12
    assert month_chart.data_polylines is None

    header2 = Header(RelativeHumidity(), '%', AnalysisPeriod())
    values2 = [i for i in range(10, 70, 5)]
    data_coll2 = MonthlyCollection(header2, values2, date_t)
    month_chart = MonthlyChart([data_coll, data_coll2])

    meshes = month_chart.data_meshes
    assert len(meshes) == 2
    assert isinstance(meshes[1], Mesh2D)
    assert len(meshes[1].faces) == 12

    month_chart = MonthlyChart([data_coll, data_coll2], stack=True)
    meshes = month_chart.data_meshes
    assert len(meshes) == 2
    assert isinstance(meshes[1], Mesh2D)
    assert len(meshes[1].faces) == 12


def test_monthlychart_monthly_stack():
    """Test the initialization of MonthlyChart with monthly stacked data collections."""
    header = Header(Energy(), 'kWh', AnalysisPeriod())
    values = [i for i in range(12, 24)]
    date_t = list(range(1, 13))
    data_coll = MonthlyCollection(header, values, date_t)
    month_chart = MonthlyChart([data_coll])

    meshes = month_chart.data_meshes
    assert len(meshes) == 1
    assert isinstance(meshes[0], Mesh2D)
    assert len(meshes[0].faces) == 12
    assert month_chart.y_axis_labels1[0] == '0.00'

    header2 = Header(Energy(), 'kWh', AnalysisPeriod())
    values2 = [i for i in range(24, 36)]
    data_coll2 = MonthlyCollection(header2, values2, date_t)
    month_chart = MonthlyChart([data_coll, data_coll2])

    meshes = month_chart.data_meshes
    assert len(meshes) == 2
    assert isinstance(meshes[1], Mesh2D)
    assert len(meshes[1].faces) == 12

    month_chart = MonthlyChart([data_coll, data_coll2], stack=True)
    meshes = month_chart.data_meshes
    assert len(meshes) == 2
    assert isinstance(meshes[1], Mesh2D)
    assert len(meshes[1].faces) == 12


def test_monthlychart_monthly_per_hour():
    """Test the initialization of MonthlyChart with monthly-per-hour data collections."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(range(12 * 24))
    date_t = AnalysisPeriod().months_per_hour
    data_coll = MonthlyPerHourCollection(header, values, date_t)
    month_chart = MonthlyChart([data_coll])

    assert month_chart.data_meshes is None
    plines = month_chart.data_polylines
    assert isinstance(plines[0], Polyline2D)
    assert len(plines) == 12

    header2 = Header(RelativeHumidity(), '%', AnalysisPeriod())
    values2 = [x / 10 for x in range(12 * 24)]
    data_coll2 = MonthlyPerHourCollection(header2, values2, date_t)
    month_chart = MonthlyChart([data_coll, data_coll2])

    plines = month_chart.data_polylines
    assert isinstance(plines[0], Polyline2D)
    assert len(plines) == 12 * 2


def test_monthlychart_monthly_per_hour_stack():
    """Test the initialization of MonthlyChart with monthly-per-hour stacked collections."""
    header = Header(Energy(), 'kWh', AnalysisPeriod())
    values = list(range(20, 12 * 24 + 20))
    date_t = AnalysisPeriod().months_per_hour
    data_coll = MonthlyPerHourCollection(header, values, date_t)
    month_chart = MonthlyChart([data_coll])

    assert month_chart.data_meshes is None
    plines = month_chart.data_polylines
    assert isinstance(plines[0], Polyline2D)
    assert len(plines) == 12
    assert month_chart.y_axis_labels1[0] == '0.00'

    header2 = Header(Energy(), 'kWh', AnalysisPeriod())
    values2 = [x / 10 for x in range(12 * 24)]
    data_coll2 = MonthlyPerHourCollection(header2, values2, date_t)
    month_chart = MonthlyChart([data_coll, data_coll2])

    plines = month_chart.data_polylines
    assert isinstance(plines[0], Polyline2D)
    assert len(plines) == 12 * 2

    month_chart = MonthlyChart([data_coll, data_coll2], stack=True)
    plines = month_chart.data_polylines
    assert isinstance(plines[0], Polyline2D)
    assert len(plines) == 12 * 2


def test_monthlychart_daily():
    """Test the initialization of MonthlyChart with daily data collections."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = [i / 31 for i in range(365)]
    date_t = list(range(1, 366))
    data_coll = DailyCollection(header, values, date_t)
    month_chart = MonthlyChart([data_coll])

    meshes = month_chart.data_meshes
    assert len(meshes) == 1
    assert isinstance(meshes[0], Mesh2D)
    assert len(meshes[0].faces) == 365
    assert month_chart.data_polylines is None

    header2 = Header(RelativeHumidity(), '%', AnalysisPeriod())
    values2 = [i / 31 for i in range(365)]
    data_coll2 = DailyCollection(header2, values2, date_t)
    month_chart = MonthlyChart([data_coll, data_coll2])

    meshes = month_chart.data_meshes
    assert len(meshes) == 2
    assert isinstance(meshes[1], Mesh2D)
    assert len(meshes[1].faces) == 365

    month_chart = MonthlyChart([data_coll, data_coll2], stack=True)
    meshes = month_chart.data_meshes
    assert len(meshes) == 2
    assert isinstance(meshes[1], Mesh2D)
    assert len(meshes[1].faces) == 365


def test_monthlychart_daily_stack():
    """Test the initialization of MonthlyChart with daily stacked data collections."""
    header = Header(Energy(), 'kWh', AnalysisPeriod())
    values = [i / 31 for i in range(365)]
    date_t = list(range(1, 366))
    data_coll = DailyCollection(header, values, date_t)
    month_chart = MonthlyChart([data_coll])

    meshes = month_chart.data_meshes
    assert len(meshes) == 1
    assert isinstance(meshes[0], Mesh2D)
    assert len(meshes[0].faces) == 365
    assert month_chart.data_polylines is None

    header2 = Header(Energy(), 'kWh', AnalysisPeriod())
    values2 = [i / 31 for i in range(365)]
    data_coll2 = DailyCollection(header2, values2, date_t)
    month_chart = MonthlyChart([data_coll, data_coll2])

    meshes = month_chart.data_meshes
    assert len(meshes) == 2
    assert isinstance(meshes[1], Mesh2D)
    assert len(meshes[1].faces) == 365

    month_chart = MonthlyChart([data_coll, data_coll2], stack=True)
    meshes = month_chart.data_meshes
    assert len(meshes) == 2
    assert isinstance(meshes[1], Mesh2D)
    assert len(meshes[1].faces) == 365


def test_hourlyplot_sub_hourly():
    """Test the initialization of MonthlyChart with a sub-hourly collection."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(range(8760))
    dc1 = HourlyContinuousCollection(header, values)
    data_coll = dc1.interpolate_to_timestep(4)
    month_chart = MonthlyChart([data_coll])

    meshes = month_chart.data_meshes
    assert len(meshes) == 1
    assert isinstance(meshes[0], Mesh2D)
    assert len(meshes[0].faces) == 24 * 12 * 4
    assert meshes[0].min == Point2D(0, 0)


def test_hourlyplot_analysis_period():
    """Test the initialization of MonthlyChart with an analysis period."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(range(8760))
    data_coll = HourlyContinuousCollection(header, values)
    period1 = AnalysisPeriod(3, 1, 0, 3, 31, 23)
    data_coll1 = data_coll.filter_by_analysis_period(period1)
    month_chart = MonthlyChart([data_coll1])

    assert month_chart.analysis_period == period1
    meshes = month_chart.data_meshes
    assert len(meshes) == 1
    assert isinstance(meshes[0], Mesh2D)
    assert len(meshes[0].faces) == 24

    period2 = AnalysisPeriod(3, 1, 0, 6, 30, 23)
    data_coll2 = data_coll.filter_by_analysis_period(period2)
    month_chart = MonthlyChart([data_coll2])

    assert month_chart.analysis_period == period2
    meshes = month_chart.data_meshes
    assert len(meshes) == 1
    assert isinstance(meshes[0], Mesh2D)
    assert len(meshes[0].faces) == 24 * 4


def test_hourlyplot_reversed_analysis_period():
    """Test the initialization of MonthlyChart with a reversed analysis period."""
    header = Header(Temperature(), 'C', AnalysisPeriod())
    values = list(range(8760))
    data_coll = HourlyContinuousCollection(header, values)
    period = AnalysisPeriod(12, 1, 0, 1, 31, 23)
    data_coll = data_coll.filter_by_analysis_period(period)
    month_chart = MonthlyChart([data_coll])

    assert month_chart.analysis_period == period
    meshes = month_chart.data_meshes
    assert len(meshes) == 1
    assert isinstance(meshes[0], Mesh2D)
    assert len(meshes[0].faces) == 2 * 24
