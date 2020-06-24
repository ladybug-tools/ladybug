# coding=utf-8
from __future__ import division

import pytest

from ladybug.datatype.speed import Speed
from ladybug.datatype.generic import GenericType
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.header import Header
from ladybug.datacollection import HourlyContinuousCollection, \
    HourlyDiscontinuousCollection
from ladybug.dt import DateTime
from ladybug.epw import EPW
from ladybug.windrose import WindRose, linspace, histogram, histogram_circular
from ladybug.legend import LegendParameters

from ladybug_geometry.geometry2d.mesh import Mesh2D
from ladybug_geometry.geometry2d.line import LineSegment2D
from ladybug_geometry.geometry2d.polygon import Polygon2D

import os
import math

def _rad2deg(r):
    return r * 180. / math.pi


def _deg2rad(d):
    return d * math.pi / 180.


def test_linspace():
    """Test the generation of bin array from bin range and num"""

    # Base case
    bin_arr = linspace(0, 360, 0)
    assert [] == bin_arr, bin_arr

    bin_arr = linspace(0, 360, 1)
    assert [0] == bin_arr, bin_arr

    bin_arr = linspace(0, 360, 2)
    assert [0, 360.0] == bin_arr, bin_arr

    bin_arr = linspace(0, 360, 4)
    assert [0.0, 120.0, 240.0, 360.0] == bin_arr, bin_arr

    bin_arr = linspace(0, 360, 5)
    assert [0.0, 90.0, 180.0, 270.0, 360.0] == bin_arr, bin_arr

    # Start from non zero
    bin_arr = linspace(180, 360, 4)
    assert [180.0, 240.0, 300.0, 360.0] == bin_arr, bin_arr

    # Start from non zero, w/ floats
    bin_arr = linspace(180., 360., 4)
    assert [180., 240.0, 300.0, 360.0] == bin_arr, bin_arr


def test_histogram():
    """Test the windrose histogram."""

    # Test simple 2 div
    bin_arr = linspace(0, 2, 3)
    assert bin_arr == [0, 1, 2]
    vals = [0, 0, 0, 1, 1, 1, 2, 2]
    hist = histogram(vals, bin_arr)
    assert hist == [[0, 0, 0], [1, 1, 1]]

    # Test out of bounds with 3 divisions
    bin_arr = linspace(0, 3, 4)
    vals = [0, 0, 0, 1, 1, 1, 2, 2]
    hist = histogram(vals, bin_arr)
    assert hist == [[0, 0, 0], [1, 1, 1], [2, 2]]

    # Test out of bounds with 2 divisions
    bin_arr = linspace(0, 3, 3)
    vals = [-1, -2, 10, 0, 0, 0, 1, 1, 1, 2, 2, 34]
    hist = histogram(vals, bin_arr)
    assert hist == [[-2, -1, 0, 0, 0, 1, 1, 1], [2, 2]], hist

    # Test edge bounds
    bin_arr = linspace(0, 3, 3)
    vals = [0, 0, 0, 1, 1, 1, 2, 2, 3, 3]
    hist = histogram(vals, bin_arr)
    assert hist == [[0, 0, 0, 1, 1, 1], [2, 2]], hist

    # Test edge bounds 2
    hist = histogram([0, 0, 0.9, 1, 1.5, 1.99, 2, 3], (0, 1, 2, 3))
    assert hist == [[0, 0, 0.9], [1, 1.5, 1.99], [2]], hist


def test_histogram_circular():
    """Test the windrose histogram_circular data."""

    # Test out of bounds with 3 divisions
    bin_arr = linspace(-2, 2, 3)
    assert bin_arr == [-2, 0, 2], bin_arr
    vals = [-2, -1, 0, 0, 0, 1, 1, 1, 2, 2]
    hist = histogram_circular(vals, bin_arr)
    assert hist == [[-2, -1], [0, 0, 0, 1, 1, 1]], hist


def test_bin_vectors():
    """Bin vectors"""

    # Testing vals
    dir_vals = [3, 3, 3, 10, 85, 90, 95, 170, 230, 285, 288]
    spd_vals = dir_vals

    # Make into fake data collections
    a_per = AnalysisPeriod(6, 21, 12, 6, 21, 13)
    dates = [DateTime(6, 21, i) for i in range(len(dir_vals))]
    spd_header = Header(Speed(), 'm/s', a_per)
    dir_header = Header(GenericType('Direction', 'deg'), 'deg', a_per)
    spd_data = HourlyDiscontinuousCollection(spd_header, spd_vals, dates)
    dir_data = HourlyDiscontinuousCollection(dir_header, dir_vals, dates)

    # Init simple dir set divided by 4
    w = WindRose(dir_data, spd_data, 4)
    f = _deg2rad
    cos, sin = math.cos, math.sin

    # Testing
    # Check angles
    a = w.angles
    chk_a = [315, 45, 135, 225, 315]
    for _a, _chk_a in zip(a, chk_a):
        assert abs(_a - _chk_a) < 1e-10, (_a, _chk_a)

    # Check vectors
    bin_vecs = w.bin_vectors
    a = [_deg2rad(_a) for _a in a]
    chk_bin_vecs = [[(cos(f(225)),  -sin(f(225))),   # 0
                     (cos(f(-45)),  -sin(f(-45)))],
                    [(cos(f(-45)),  -sin(f(-45))),   # 1
                     (cos(f(45)),   -sin(f(45)))],
                    [(cos(f(45)),   -sin(f(45))),    # 2
                     (cos(f(135)),  -sin(f(135)))],
                    [(cos(f(135)),  -sin(f(135))),   # 3
                     (cos(f(225)),  -sin(f(225)))]]

    # Check len
    assert len(bin_vecs) == len(chk_bin_vecs)

    # Check coords
    for i, (chk_vec, vec) in enumerate(zip(chk_bin_vecs, bin_vecs)):
        # left vec
        assert abs(chk_vec[0][0] - vec[0][0]) < 1e-5, (i, chk_vec[0][0], vec[0][0])
        assert abs(chk_vec[0][1] - vec[0][1]) < 1e-5, (i, chk_vec[0][1], vec[0][1])
        # right vec
        assert abs(chk_vec[1][0] - vec[1][0]) < 1e-5, (i, chk_vec[1][0], vec[1][0])
        assert abs(chk_vec[1][1] - vec[1][1]) < 1e-5, (i, chk_vec[1][1], vec[1][1])


def test_xticks_radial():
    """Test polar coordinate array"""

    # Testing vals ensure all histogram heights are equal.
    dir_vals = [3, 3, 10,       #  315 - 45
                85, 90, 95,     #  45 - 135
                170, 170, 170,  #  135 - 225
                230, 285, 288]  #  225 - 315

    spd_vals = dir_vals

    # Make into fake data collections
    a_per = AnalysisPeriod(6, 21, 12, 6, 21, 13)
    dates = [DateTime(6, 21, i) for i in range(len(dir_vals))]
    spd_header = Header(Speed(), 'm/s', a_per)
    dir_header = Header(GenericType('Direction', 'deg'), 'deg', a_per)
    spd_data = HourlyDiscontinuousCollection(spd_header, spd_vals, dates)
    dir_data = HourlyDiscontinuousCollection(dir_header, dir_vals, dates)

    # Init simple dir set divided by 4
    w = WindRose(dir_data, spd_data, 4)
    f = _deg2rad
    cos, sin = math.cos, math.sin

    # Testing
    bin_vecs = w.bin_vectors
    xticks = w.orientation_lines
    xticks = [xtick.scale(1 / w.compass_radius) for xtick in xticks]
    # w.angles - 90: [225, -45, 45, 135, 225]

    # Since frequencies are for xticks, no need to scale vectors.
    chk_xticks = [
        [(0, 0), (cos(f(225)), -sin(f(225)))],  # v0
        [(0, 0), (cos(f(-45)), -sin(f(-45)))],  # v1 bin 0
        [(0, 0), (cos(f(-45)), -sin(f(-45)))],  # v2
        [(0, 0), (cos(f(45)),  -sin(f(45)))],   # v3 bin 1
        [(0, 0), (cos(f(45)),  -sin(f(45)))],   # v4
        [(0, 0), (cos(f(135)), -sin(f(135)))],  # v5 bin 2
        [(0, 0), (cos(f(135)), -sin(f(135)))],  # v6
        [(0, 0), (cos(f(225)), -sin(f(225)))]]  # v7 bin 3

    for i, (chk_xtick, xtick) in enumerate(zip(chk_xticks, xticks)):
        # Check x, y
        # print(chk_xtick[1][0], xtick.to_array()[1][0])
        # print(chk_xtick[1][1], xtick.to_array()[1][1])
        assert abs(chk_xtick[1][0] - xtick.to_array()[1][0]) < 1e-10
        assert abs(chk_xtick[1][1] - xtick.to_array()[1][1]) < 1e-10


def test_radial_histogram():
    """ Test circular histogram"""
    # Testing vals ensure all histogram heights are equal.
    dir_vals = [3, 3, 10,       #  315 - 45
                85, 90, 95,     #  45 - 135
                170, 170, 170,  #  135 - 225
                230, 285, 288]  #  225 - 315
    spd_vals = dir_vals

    # Make into fake data collections
    a_per = AnalysisPeriod(6, 21, 12, 6, 21, 13)
    dates = [DateTime(6, 21, i) for i in range(len(dir_vals))]
    spd_header = Header(Speed(), 'm/s', a_per)
    dir_header = Header(GenericType('Direction', 'deg'), 'deg', a_per)
    spd_data = HourlyDiscontinuousCollection(spd_header, spd_vals, dates)
    dir_data = HourlyDiscontinuousCollection(dir_header, dir_vals, dates)

    # Init simple dir set divided by 4
    w = WindRose(dir_data, spd_data, 4)
    f = _deg2rad
    cos, sin = math.cos, math.sin

    # Testing
    bin_vecs = w.bin_vectors
    vec_cpt = (0, 0)
    radius_arr = (0., 1.)
    ytick_num = 1
    hist = w.histogram_data
    histstack = w._histogram_data_nested(hist, ytick_num)
    print(histstack)
    show_freq = False
    vecs = WindRose._histogram_array_radial(bin_vecs, vec_cpt, hist, histstack,
                                            radius_arr, show_freq)

    # Make bins of equal height (unit circle)
    chk_bin_vecs = [[(cos(f(225)),  -sin(f(225))),   # 0 west
                     (cos(f(-45)),  -sin(f(-45)))],
                    [(cos(f(-45)),  -sin(f(-45))),   # 1 north
                     (cos(f(45)),   -sin(f(45)))],
                    [(cos(f(45)),   -sin(f(45))),    # 2 east
                     (cos(f(135)),  -sin(f(135)))],
                    [(cos(f(135)),  -sin(f(135))),   # 3 south
                     (cos(f(225)),  -sin(f(225)))]]

    for i in range(len(chk_bin_vecs)):
        vec2, vec1 = chk_bin_vecs[i][0], chk_bin_vecs[i][1]
        chk_pts = [vec1, vec2]
        pts = vecs[i][1:]  # Get rid of cpt (0, 0)

        for p, cp in zip(pts, chk_pts):
            assert abs(p[0] - cp[0]) < 1e-10, (p[0], cp[0])
            assert abs(p[1] - cp[1]) < 1e-10, (p[1], cp[1])


def test_histogram_data_nested():

    # Testing vals
    dir_vals = [0, 0, 0, 10, 10, 10, 85, 90, 90, 90, 95, 170, 285, 288]
    spd_vals = dir_vals

    # Make into fake data collections
    a_per = AnalysisPeriod(6, 21, 12, 6, 21, 13)
    dates = [DateTime(6, 21, i) for i in range(len(dir_vals))]
    spd_header = Header(Speed(), 'm/s', a_per)
    dir_header = Header(GenericType('Direction', 'deg'), 'deg', a_per)
    spd_data = HourlyDiscontinuousCollection(spd_header, spd_vals, dates)
    dir_data = HourlyDiscontinuousCollection(dir_header, dir_vals, dates)

    # Init simple example w segs == bin num
    w = WindRose(dir_data, spd_data, 4)
    w.legend_parameters = LegendParameters(segment_count=5)

    # Bin values to divide into colors
    # 315-45:  [10, 10, 10];         2 intervals, [10, 10, 10]
    # 45-135:  [85, 90, 90, 90, 95]; 3 intervals, [85, 90, 90, 90, 95]
    # 135-225: [170];                1 intervals, [170];
    # 225-315: [285, 288];           2 intervals, [285, 288]

    # interval_num: [2, 3, 1, 2]
    chk_histstack = [
        [10, 10, 10],
        [85, 90, 90, 90, 95],
        [170.],
        [285, 288]]

    # Testing
    histstack = WindRose._histogram_data_nested(w.histogram_data, 5)
    for chkh, h in zip(chk_histstack, histstack):
        for c, _h in zip(chkh, h):
            assert abs(c - _h) <= 1e-10

    # Init complex dir set divided by 4
    w = WindRose(dir_data, spd_data, 4)
    w.legend_parameters = LegendParameters(segment_count=3)

    # Bin values to divide into colors
    # 315-45:  [10, 10, 10];         2 intervals, [10, 10]
    # 45-135:  [85, 90, 90, 90, 95]; 3 intervals, [87.5, 90, 95. ]
    # 135-225: [170];                1 intervals, [170]
    # 225-315: [285, 288];           2 intervals, [286.5]

    # interval_num: [2, 3, 1, 2]
    chk_histstack = [
        [10, 10],
        [87.5, 90, 95.],
        [170.],
        [286.5]]

    # Testing
    histstack = WindRose._histogram_data_nested(w.histogram_data, 3)
    for chkh, h in zip(chk_histstack, histstack):
        for c, _h in zip(chkh, h):
            assert abs(c - _h) <= 1e-10
    #assert False


def test_simple_windrose_mesh():
    # Testing vals
    dir_vals = [0, 0, 0, 10, 10, 10, 85, 90, 90, 90, 95, 170, 285, 288]
    spd_vals = dir_vals

    # Make into fake data collections
    a_per = AnalysisPeriod(6, 21, 12, 6, 21, 13)
    dates = [DateTime(6, 21, i) for i in range(len(dir_vals))]
    spd_header = Header(Speed(), 'm/s', a_per)
    dir_header = Header(GenericType('Direction', 'deg'), 'deg', a_per)
    spd_data = HourlyDiscontinuousCollection(spd_header, spd_vals, dates)
    dir_data = HourlyDiscontinuousCollection(dir_header, dir_vals, dates)

    # Init simple dir set divided by 4
    w = WindRose(dir_data, spd_data, 4)
    w.legend_parameters.segment_count = 3
    w.show_zeros = False
    w.show_freq = False
    mesh = w.colored_mesh
    assert isinstance(mesh, Mesh2D)

    # All true
    w = WindRose(dir_data, spd_data, 4)
    w.legend_parameters.segment_count = 10
    w.show_zeros = True
    w.show_freq = True
    mesh = w.colored_mesh
    assert isinstance(mesh, Mesh2D)

    # Init simple dir set divided by 8
    w = WindRose(dir_data, spd_data, 4)
    w.legend_parameters.segment_count = 3
    w.show_zeros = False
    w.show_freq = False
    mesh = w.colored_mesh
    assert isinstance(mesh, Mesh2D)


def test_windrose_mesh():
    # Plot windrose
    epw_path = os.path.join(os.getcwd(), 'tests/fixtures/epw/tokyo.epw')
    epw = EPW(epw_path)

    w = WindRose(epw.wind_direction, epw.wind_speed, 16)
    w.legend_parameters.segment_count = 3
    w.show_zeros = False
    w.show_freq = False
    assert isinstance(w.colored_mesh, Mesh2D)

    # Test the plot grid
    assert isinstance(w.frequency_lines[0], Polygon2D)
    assert isinstance(w.orientation_lines[0], LineSegment2D)


def test_windrose_frequency_lines():
    """Test frequency Polygon2Ds"""

    epw_path = os.path.join(os.getcwd(), 'tests/fixtures/epw/tokyo.epw')
    epw = EPW(epw_path)

    w = WindRose(epw.wind_direction, epw.wind_speed, 5)

    # Without calmrose
    w.show_zeros = False
    w.show_freq = True
    _ = w.colored_mesh

    freqs = w.frequency_lines

    assert isinstance(freqs[0], Polygon2D)
    assert not freqs[0].vertices[0].is_equivalent(freqs[0].vertices[-1], 1e-10)

    # With calmrose
    w.show_zeros = True
    w.show_freq = True
    _ = w.colored_mesh

    freqs = w.frequency_lines

    assert isinstance(freqs[0], Polygon2D)
    assert not freqs[0].vertices[0].is_equivalent(freqs[0].vertices[-1], 1e-10)


def test_windrose_mesh_number_of_directions():
    # Test if mesh number of directions

    epw_path = os.path.join(os.getcwd(), 'tests/fixtures/epw/tokyo.epw')
    epw = EPW(epw_path)

    # Test 16 directions
    w = WindRose(epw.wind_direction, epw.wind_speed, 16)
    w.legend_parameters.segment_count = 3
    w.show_zeros = True
    w.show_freq = True

    assert len(w.histogram_data) == 16

    # Test error if number of directions < 0
    with pytest.raises(AssertionError):
        WindRose(epw.wind_direction, epw.wind_speed, 0)

    # Test error if number of directions < 3
    w = WindRose(epw.wind_direction, epw.wind_speed, 2)
    with pytest.raises(AssertionError):
        w.colored_mesh

    w = WindRose(epw.wind_direction, epw.wind_speed, 3)
    assert isinstance(w.colored_mesh, Mesh2D)


def test_windrose_graphic_analysis_values():
    """Test visualization analysis values"""

    # Test w/ zeros
    epw_path = os.path.join(os.getcwd(), 'tests/fixtures/epw/tokyo.epw')
    epw = EPW(epw_path)

    # Test 16 directions
    w1 = WindRose(epw.wind_direction, epw.wind_speed, 16)
    w1.legend_parameters.segment_count = 3
    w1.show_zeros = True
    w1.show_freq = True
    _ = w1.colored_mesh
    assert min(w1.container.values) < 1e-10

    # Test 16 directions
    w2 = WindRose(epw.wind_direction, epw.wind_speed, 16)
    w2.legend_parameters.segment_count = 3
    w2.show_zeros = False
    w2.show_freq = False
    _ = w2.colored_mesh
    assert min(w2.container.values) > 1e-10


def test_windrose_set_legend_parameters():
    """Test setting legend params property"""

    epw_path = os.path.join(os.getcwd(), 'tests/fixtures/epw/tokyo.epw')
    epw = EPW(epw_path)
    w = WindRose(epw.wind_direction, epw.wind_speed, 5)

    # Default
    assert w._legend_parameters is None
    assert isinstance(w.legend_parameters, LegendParameters)
    assert w.legend_parameters.segment_count == pytest.approx(11.0, abs=1e-10)

    # Check setting wrong input
    with pytest.raises(AssertionError):
        w.legend_parameters = 'string'

    # Check setting
    w.legend_parameters = LegendParameters(segment_count=16)
    assert w.legend_parameters.segment_count == pytest.approx(16, abs=1e-10)

    # Check resetting
    w._legend_parameters = None
    assert isinstance(w.legend_parameters, LegendParameters)
    assert w.legend_parameters.segment_count == pytest.approx(11.0, abs=1e-10)


def test_windrose_set_north():
    """Test setting north property"""

    epw_path = os.path.join(os.getcwd(), 'tests/fixtures/epw/tokyo.epw')
    epw = EPW(epw_path)
    w = WindRose(epw.wind_direction, epw.wind_speed, 5)

    assert abs(w.north) < 1e-10

    with pytest.raises(AssertionError):
        w.north = 'string'

    # Ensure modulo works
    w.north = 365.0
    assert w.north == pytest.approx(5.0, abs=1e-10)

    # Check compass orientation
    assert w.compass.north_angle == pytest.approx(5.0, abs=1e-10)
