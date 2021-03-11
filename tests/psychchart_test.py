from ladybug.legend import Legend, LegendParameters
from ladybug.graphic import GraphicContainer
from ladybug.epw import EPW
from ladybug.psychchart import PsychrometricChart

from ladybug_geometry.geometry2d.pointvector import Point2D
from ladybug_geometry.geometry2d.line import LineSegment2D
from ladybug_geometry.geometry2d.polyline import Polyline2D
from ladybug_geometry.geometry2d.mesh import Mesh2D


def test_psychchart_init():
    """Test the initialization of PsychrometricChart and basic properties."""
    psych_chart = PsychrometricChart(20, 50)

    str(psych_chart)  # test the string representation
    assert psych_chart.temperature == 20
    assert psych_chart.relative_humidity == 50
    assert psych_chart.average_pressure == 101325
    assert isinstance(psych_chart.legend_parameters, LegendParameters)
    assert psych_chart.base_point == Point2D(0, 0)
    assert psych_chart.x_dim == 1
    assert psych_chart.y_dim == 1500
    assert psych_chart.min_temperature == -20
    assert psych_chart.max_temperature == 50
    assert psych_chart.max_humidity_ratio == 0.03
    assert not psych_chart.use_ip

    mesh = psych_chart.colored_mesh
    assert isinstance(mesh, Mesh2D)
    assert len(mesh.faces) == 1
    data_points = psych_chart.data_points
    assert all(isinstance(pt, Point2D) for pt in data_points)
    hour_values = psych_chart.hour_values
    assert all(isinstance(pt, (float, int)) for pt in hour_values)
    time_matrix = psych_chart.time_matrix
    assert all(isinstance(pt, tuple) for pt in time_matrix)

    sat_line = psych_chart.saturation_line
    assert isinstance(sat_line, Polyline2D)
    border = psych_chart.chart_border
    assert isinstance(border, Polyline2D)
    assert len(border.segments) == 4

    temp_txt = psych_chart.temperature_labels
    assert all(isinstance(txt, str) for txt in temp_txt)
    temp_lines = psych_chart.temperature_lines
    temp_pts = psych_chart.temperature_label_points
    assert len(temp_lines) == len(temp_txt) == len(temp_pts)
    assert all(isinstance(line, LineSegment2D) for line in temp_lines)
    assert all(isinstance(pt, Point2D) for pt in temp_pts)

    rh_txt = psych_chart.rh_labels
    assert all(isinstance(txt, str) for txt in rh_txt)
    rh_lines = psych_chart.rh_lines
    rh_pts = psych_chart.rh_label_points
    assert len(rh_txt) == len(rh_pts)
    assert len(rh_lines) == 10
    assert all(isinstance(line, Polyline2D) for line in rh_lines)
    assert all(isinstance(pt, Point2D) for pt in rh_pts)

    hr_txt = psych_chart.hr_labels
    assert all(isinstance(txt, str) for txt in hr_txt)
    hr_lines = psych_chart.hr_lines
    hr_pts = psych_chart.hr_label_points
    assert len(hr_lines) == len(hr_txt) == len(hr_pts)
    assert all(isinstance(line, LineSegment2D) for line in hr_lines)
    assert all(isinstance(pt, Point2D) for pt in hr_pts)

    enthalpy_txt = psych_chart.enthalpy_labels
    assert all(isinstance(txt, str) for txt in enthalpy_txt)
    enthalpy_lines = psych_chart.enthalpy_lines
    enthalpy_pts = psych_chart.enthalpy_label_points
    assert len(enthalpy_lines) == len(enthalpy_txt) == len(enthalpy_pts)
    assert all(isinstance(line, LineSegment2D) for line in enthalpy_lines)
    assert all(isinstance(pt, Point2D) for pt in enthalpy_pts)

    wb_txt = psych_chart.wb_labels
    assert all(isinstance(txt, str) for txt in wb_txt)
    wb_lines = psych_chart.wb_lines
    wb_pts = psych_chart.wb_label_points
    assert len(wb_lines) == len(wb_txt) == len(wb_pts)
    assert all(isinstance(line, LineSegment2D) for line in wb_lines)
    assert all(isinstance(pt, Point2D) for pt in wb_pts)

    assert isinstance(psych_chart.legend, Legend)
    assert isinstance(psych_chart.container, GraphicContainer)

    assert isinstance(psych_chart.title_text, str)
    assert isinstance(psych_chart.y_axis_text, str)
    assert isinstance(psych_chart.x_axis_text, str)
    assert isinstance(psych_chart.title_location, Point2D)
    assert isinstance(psych_chart.x_axis_location, Point2D)
    assert isinstance(psych_chart.y_axis_location, Point2D)


def test_psychchart_from_epw():
    """Test the initialization of PsychrometricChart from an EPW file."""
    path = './tests/assets/epw/tokyo.epw'
    psych_chart = PsychrometricChart.from_epw(
        path, base_point=Point2D(100, 100), min_temperature=-10, max_temperature=40)

    mesh = psych_chart.colored_mesh
    assert isinstance(mesh, Mesh2D)
    assert len(mesh.faces) > 1


def test_data_mesh():
    """Test the data_mesh meshod."""
    path = './tests/assets/epw/tokyo.epw'
    epw = EPW(path)
    psych_chart = PsychrometricChart(epw.dry_bulb_temperature, epw.relative_humidity)

    test_pt = psych_chart.plot_point(20, 50)
    assert isinstance(test_pt, Point2D)

    mesh = psych_chart.colored_mesh
    assert isinstance(mesh, Mesh2D)
    assert len(mesh.faces) > 1

    data_mesh, container = psych_chart.data_mesh(epw.wind_speed)
    assert isinstance(data_mesh, Mesh2D)
    assert len(mesh.faces) == len(data_mesh.faces) > 1
    assert isinstance(container, GraphicContainer)


def test_psychchart_to_from_dict():
    """Test the initialization of PsychrometricChart and basic properties."""
    psych_chart = PsychrometricChart(20, 50, 101000, None, Point2D(100, 100),
                                     1.5, 1000, 0, 110, 0.025, True)

    chart_dict = psych_chart.to_dict()
    new_chart = PsychrometricChart.from_dict(chart_dict)
    assert new_chart.to_dict() == chart_dict

    assert new_chart.temperature == 20
    assert new_chart.relative_humidity == 50
    assert new_chart.average_pressure == 101000
    assert new_chart.base_point == Point2D(100, 100)
    assert new_chart.x_dim == 1.5
    assert new_chart.y_dim == 1000
    assert new_chart.min_temperature == 0
    assert new_chart.max_temperature == 110
    assert new_chart.max_humidity_ratio == 0.025
    assert new_chart.use_ip
