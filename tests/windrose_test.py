# coding=utf-8
from __future__ import division

import pytest

from ladybug.datatype.speed import Speed
from ladybug.datatype.generic import GenericType
from ladybug.datatype.fraction import Fraction
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.header import Header
from ladybug.datacollection import HourlyDiscontinuousCollection, \
    HourlyContinuousCollection
from ladybug.dt import DateTime
from ladybug.epw import EPW
from ladybug.windrose import WindRose
from ladybug.legend import LegendParameters

from ladybug_geometry.geometry2d.mesh import Mesh2D
from ladybug_geometry.geometry2d.line import LineSegment2D
from ladybug_geometry.geometry2d.polygon import Polygon2D

import os
import math
from pprint import pprint as pp


def _deg2rad(d):
    return d * math.pi / 180.


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
    dir_vals = [3, 3, 10,  # 315 - 45
                85, 90, 95,  # 45 - 135
                170, 170, 170,  # 135 - 225
                230, 285, 288]  # 225 - 315

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


def test_radial_histogram_plot():
    """ Test circular histogram"""
    # Testing vals ensure all histogram heights are equal.
    dir_vals = [3, 3, 10,  # 315 - 45
                85, 90, 95,  # 45 - 135
                170, 170, 170,  # 135 - 225
                230, 285, 288]  # 225 - 315
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
    hist = w.histogram_data

    speeds = [val for bin in w.histogram_data for val in bin]
    min_speed, max_speed = min(speeds), max(speeds)
    speed_interval = (max_speed - min_speed) / w.legend_parameters.segment_count
    histstack, _ = w._histogram_data_nested(
        hist, (min_speed, max_speed), speed_interval)

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


def test_frequency_intervals():
    """Test the distance of frequency_intervals"""

    # Plot windrose
    epw_path = os.path.join(os.getcwd(), 'tests/assets/epw/tokyo.epw')
    epw = EPW(epw_path)

    w = WindRose(epw.wind_direction, epw.wind_speed, 3)
    w.show_zeros = False
    w.show_freq = False
    w.frequency_hours = 200.0

    test_freq_int = int(math.ceil(w.real_freq_max / 200.0))
    assert w.frequency_intervals_compass == pytest.approx(test_freq_int, abs=1e-10)
    assert w.frequency_intervals_mesh == pytest.approx(test_freq_int, abs=1e-10)

    # Test changing interals from 18
    # Reduce
    w.frequency_intervals_compass = 10.0
    test_freq_int = 10.0
    assert w.frequency_maximum == pytest.approx(10 * 200.0, abs=1e-10)
    assert w.frequency_intervals_compass == pytest.approx(test_freq_int, abs=1e-10)
    assert w.frequency_intervals_mesh == pytest.approx(test_freq_int, abs=1e-10)

    # Check that resetting frequency_max works
    w._frequency_intervals_compass = None
    # w.real_freq_max: 4406
    chk_max = int(math.ceil(4406 / 200)) * 200

    assert w.frequency_maximum == pytest.approx(chk_max, abs=1e-10)
    assert w.frequency_intervals_compass == pytest.approx(23, abs=1e-10)
    assert w.frequency_intervals_mesh == pytest.approx(23, abs=1e-10)


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
    epw_path = os.path.join(os.getcwd(), 'tests/assets/epw/tokyo.epw')
    epw = EPW(epw_path)

    w = WindRose(epw.wind_direction, epw.wind_speed, 16)
    w.legend_parameters.segment_count = 3

    # Test the plot grid
    assert isinstance(w.frequency_lines[0], Polygon2D)
    assert isinstance(w.orientation_lines[0], LineSegment2D)

    # Test False, False
    w.show_zeros = False
    w.show_freq = False
    assert isinstance(w.colored_mesh, Mesh2D)

    # Test True, False
    w.show_zeros = True
    w.show_freq = False
    assert isinstance(w.colored_mesh, Mesh2D)

    # Test False, True
    w.show_zeros = False
    w.show_freq = True
    assert isinstance(w.colored_mesh, Mesh2D)

    # Test True, True
    w.show_zeros = True
    w.show_freq = True
    assert isinstance(w.colored_mesh, Mesh2D)


def test_windrose_frequency_lines():
    """Test frequency Polygon2Ds"""

    epw_path = os.path.join(os.getcwd(), 'tests/assets/epw/tokyo.epw')
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

    epw_path = os.path.join(os.getcwd(), 'tests/assets/epw/tokyo.epw')
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
    epw_path = os.path.join(os.getcwd(), 'tests/assets/epw/tokyo.epw')
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

    epw_path = os.path.join(os.getcwd(), 'tests/assets/epw/tokyo.epw')
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
    w.legend_parameters = None
    assert isinstance(w.legend_parameters, LegendParameters)
    assert w.legend_parameters.segment_count == pytest.approx(11.0, abs=1e-10)


def test_windrose_set_north():
    """Test setting north property"""

    epw_path = os.path.join(os.getcwd(), 'tests/assets/epw/tokyo.epw')
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


def test_windrose_mesh_size():
    # Testing mesh scaling
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

    # Test the size of the windrose
    w = WindRose(dir_data, spd_data, 4)
    w.legend_parameters.segment_count = 3
    w.show_zeros = False
    w.show_freq = True
    w.frequency_spacing_distance = 200.0
    _ = w.colored_mesh
    hdist = w.frequency_spacing_hypot_distance
    intervals = w.real_freq_max / w.frequency_hours
    assert w.mesh_radius == pytest.approx(intervals * hdist, abs=1e-10)

    # Add calmrose
    w.show_zeros = True
    zero_dist = w._zero_mesh_radius
    _ = w.colored_mesh
    hdist = w.frequency_spacing_hypot_distance
    intervals = w.real_freq_max / w.frequency_hours
    assert w.mesh_radius == pytest.approx(zero_dist + (intervals * hdist))

    # Test size with windrose from actual epw data
    epw_path = os.path.join(os.getcwd(), 'tests/assets/epw/chicago.epw')
    epw = EPW(epw_path)
    w = WindRose(epw.wind_direction, epw.wind_speed, 3)


def test_prevailing_direction():
    """Test prevailing direction getter"""

    # Test with single prevailing dir
    dir_vals = [0, 3, 10,  # 315 - 45
                85, 90,  95,  # 45 - 135
                140, 170, 170, 170,  # 135 - 225
                230, 285, 288]  # 225 - 315

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
    test_prev_dir = 180

    assert w.prevailing_direction[0] == test_prev_dir

    # Testing with two max prevailing values
    dir_vals = [3, 3, 10,  # 315 - 45
                85, 90, 90, 100,  # 45 - 135
                170, 170, 170, 180,  # 135 - 225
                230, 285, 288]  # 225 - 315

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
    test_prev_dir = set((90, 180))

    assert set(w.prevailing_direction) == test_prev_dir

    # Test with epw
    epw_path = os.path.join(os.getcwd(), 'tests/assets/epw/chicago.epw')
    epw = EPW(epw_path)

    # Test 5 directions
    w = WindRose(epw.wind_direction, epw.wind_speed, 5)
    assert w.prevailing_direction[0] == 216.0


def test_histogram_data_nested():

    # Testing vals
    dir_vals = [0, 0, 0, 0, 10, 10, 10, 85, 90, 90, 90, 95, 170, 285, 310]
    spd_vals = [0, 0, 0, 0, 1, 145, 189, 15, 10, 150, 299, 259, 100, 5, 301]

    # Make into fake data collections
    a_per = AnalysisPeriod(6, 21, 12, 6, 21, 13)
    dates = [DateTime(6, 21, i) for i in range(len(dir_vals))]
    spd_header = Header(Speed(), 'm/s', a_per)
    dir_header = Header(GenericType('Direction', 'deg'), 'deg', a_per)
    spd_data = HourlyDiscontinuousCollection(spd_header, spd_vals, dates)
    dir_data = HourlyDiscontinuousCollection(dir_header, dir_vals, dates)

    # Init complex dir set divided by 4, and 2 hourly intervals
    w = WindRose(dir_data, spd_data, 4)
    w.frequency_hours = 2
    w.legend_parameters.segment_count = 7

    # Bin values to divide into 6 intervals = 10 - 310 = 300 / 6 = 50 m/s
    # intervals: [1-50, 51-100, 101-150, 151-200, 201-250, 251-300, 301-350]
    #
    # each frequency interval = 1/6 ~ 0.166 of total speed
    # 315-45:  [1, 145, 189];           3 bands [0-49, 100-149, 150-199]
    # 45-135:  [15, 10, 150, 299, 259]; 3 bands, [0-49, 150-199,, 250-299]
    # 135-225: [100];                   1 bands, [100-149]
    # 225-315: [5, 300];                2 bands, [0-49, 300, 249]

    # interval_num: [3, 3, 1, 2]
    chk_histstack = [
        [[1], [], [145], [189], [], []],  # 0-49, 100-149, 150-199
        [[10, 15], [], [150], [], [], [259, 299]],  # 0-49, 150-199,, 250-299
        [[], [100], [], [], [], []],  # 100-149
        [[5], [], [], [], [], [301]]]  # 0-49, 300-349

    # Testing
    speeds = [val for bin in w.histogram_data for val in bin]
    min_speed, max_speed = min(speeds), max(speeds)
    histstack, bins = WindRose._histogram_data_nested(
        w.histogram_data, (min_speed, max_speed), w.legend_parameters.segment_count)

    # Check
    assert len(chk_histstack) == len(histstack)
    for cbins, bins in zip(chk_histstack, histstack):
        assert len(cbins) == len(bins)
        for cbin, bin in zip(cbins, bins):
            assert len(cbin) == len(bin)
            for cval, val in zip(cbin, bin):
                assert abs(cval - val) <= 1e-10, (cval, val)

    # Check with zeros
    w.show_zeros = True
    w.frequency_hours = 1.0
    w.frequency_spacing_distance = 25.0
    hypot_dist = w.frequency_spacing_hypot_distance
    assert abs(w._zero_mesh_radius - hypot_dist) < 1e-10

    # Check with zeros 2
    # Testing vals
    dir_vals = [0, 0, 0, 0, 0, 0, 10, 10, 10, 85, 90, 90, 90, 95, 170, 285, 310]
    spd_vals = [0, 0, 0, 0, 0, 0, 1, 145, 189, 15, 10, 150, 299, 259, 100, 5, 301]

    # Make into fake data collections
    a_per = AnalysisPeriod(6, 21, 12, 6, 21, 13)
    dates = [DateTime(6, 21, i) for i in range(len(dir_vals))]
    spd_header = Header(Speed(), 'm/s', a_per)
    dir_header = Header(GenericType('Direction', 'deg'), 'deg', a_per)
    spd_data = HourlyDiscontinuousCollection(spd_header, spd_vals, dates)
    dir_data = HourlyDiscontinuousCollection(dir_header, dir_vals, dates)

    # Init complex dir set divided by 4, and 2 hourly intervals
    w = WindRose(dir_data, spd_data, 4)

    w.show_zeros = True
    w.frequency_hours = 1.0
    w.frequency_spacing_distance = 25.0
    hypot_dist = w.frequency_spacing_hypot_distance * 1.5
    assert abs(w._zero_mesh_radius - hypot_dist) < 1e-10


def test_color_array():
    """Test colors for different windrose types."""

    # Testing vals
    dir_vals = [0, 0, 0, 0, 10, 10, 10, 85, 90, 90, 90, 95, 170, 285, 310]
    spd_vals = [0, 0, 0, 0, 1, 145, 189, 15, 10, 150, 300, 259, 100, 5, 301]

    # Make into fake data collections
    a_per = AnalysisPeriod(6, 21, 12, 6, 21, 13)
    dates = [DateTime(6, 21, i) for i in range(len(dir_vals))]
    spd_header = Header(Speed(), 'm/s', a_per)
    dir_header = Header(GenericType('Direction', 'deg'), 'deg', a_per)
    spd_data = HourlyDiscontinuousCollection(spd_header, spd_vals, dates)
    dir_data = HourlyDiscontinuousCollection(dir_header, dir_vals, dates)
    data_step = 50.0
    min_val = 1

    # Bin values to divide into 6 intervals = 10 - 310 = 300 / 6 = 50 m/s
    # intervals: [1-50, 51-100, 101-150, 151-200, 201-250, 251-300, 301-350]
    #
    # [[1], [], [145], [189], [], [],  # 0-49, 100-149, 150-199
    # [[10, 15], [], [150], [], [], [259, 300]],  # 0-49, 150-199,, 250-299
    # [[], [100], [], [], [], []],  # 100-149
    # [[5], [], [], [], [], [301]]  # 0-49, 300-349

    # Check freq=True, zeros=False
    w = WindRose(dir_data, spd_data, 4)
    w.show_freq, w.show_zeros = True, False
    w.frequency_hours = 2
    w.legend_parameters = LegendParameters(segment_count=7)
    w.colored_mesh

    # color index corresponds to hourly interval indices
    # [1-50, 51-100, 101-150, 151-200, 201-250, 251-300, 301-350]
    chk_color_array = [0, 2, 3, 0, 2, 5, 1, 0, 5]
    chk_color_array = [(c * data_step) + min_val for c in chk_color_array]

    assert len(chk_color_array) == len(w._color_array)
    for cc, c in zip(chk_color_array, w._color_array):
        assert abs(cc - c) < 1e-10

    # Check freq=True, zeros=True
    # Modify range for easier calcs
    dir_vals = [0, 0, 0, 0, 10, 10, 10, 85, 90, 90, 90, 95, 170, 285, 310]
    spd_vals = [0, 0, 0, 0, 1, 145, 189, 15, 10, 149, 299, 259, 99, 5, 300]
    zero_spd_data = HourlyDiscontinuousCollection(spd_header, spd_vals, dates)
    zero_dir_data = HourlyDiscontinuousCollection(dir_header, dir_vals, dates)
    zero_data_step = 50
    zero_min_val = 0

    w = WindRose(zero_dir_data, zero_spd_data, 4)
    w.show_freq, w.show_zeros = True, True
    w.frequency_hours = 2
    w.legend_parameters = LegendParameters(segment_count=7)
    w.colored_mesh

    # color index corresponds to hourly interval indices
    chk_color_array = [1, 3, 4, 1, 3, 6, 2, 1, 6]
    chk_color_array = [(c * zero_data_step) + zero_min_val for c in chk_color_array]
    chk_color_array += [0, 0, 0, 0]
    assert len(chk_color_array) == len(w._color_array)
    for cc, c in zip(chk_color_array, w._color_array):
        assert abs(cc - c) < 1e-10

    # Check freq=False, zeros=False
    w = WindRose(dir_data, spd_data, 4)
    w.show_freq, w.show_zeros = False, False
    w.frequency_hours = 2
    w.legend_parameters = LegendParameters(segment_count=7)
    w.colored_mesh

    # color index corresponds to hourly interval indices
    chk_color_array = [111 + 2/3, 146.8, 100, 153]
    assert len(chk_color_array) == len(w._color_array)
    for cc, c in zip(chk_color_array, w._color_array):
        assert abs(cc - c) < 1e-10

    # Check freq=False, zeros=True
    w = WindRose(dir_data, spd_data, 4)
    w.show_freq, w.show_zeros = False, True
    w.frequency_hours = 2
    w.legend_parameters = LegendParameters(segment_count=7)
    w.colored_mesh

    # color index corresponds to hourly interval indices
    chk_color_array = [111 + 2/3, 146.8, 100, 153]
    chk_color_array += [0, 0, 0, 0]

    assert len(chk_color_array) == len(w._color_array)
    for cc, c in zip(chk_color_array, w._color_array):
        assert abs(cc - c) < 1e-10


def test_wind_polygons():
    """Test colors for different windrose types."""

    # Testing vals
    dir_vals = [0, 0, 0, 0, 10, 10, 10, 85, 90, 90, 90, 95, 170, 285, 310]
    spd_vals = [0, 0, 0, 0, 1, 145, 189, 15, 10, 150, 300, 259, 100, 5, 301]

    # Make into fake data collections
    a_per = AnalysisPeriod(6, 21, 12, 6, 21, 13)
    dates = [DateTime(6, 21, i) for i in range(len(dir_vals))]
    spd_header = Header(Speed(), 'm/s', a_per)
    dir_header = Header(GenericType('Direction', 'deg'), 'deg', a_per)
    spd_data = HourlyDiscontinuousCollection(spd_header, spd_vals, dates)
    dir_data = HourlyDiscontinuousCollection(dir_header, dir_vals, dates)

    # Bin values to divide into 6 intervals = 10 - 310 = 300 / 6 = 50 m/s
    # intervals: [1-50, 51-100, 101-150, 151-200, 201-250, 251-300, 301-350]
    #
    # [[1], [], [145], [189], [], []],  # 0-49, 100-149, 150-199
    # [[10, 15], [], [150], [], [], [259, 300]],  # 0-49, 150-199,, 250-299
    # [[], [100], [], [], [], []],  # 100-149
    # [[5], [], [], [], [], [301]]  # 0-49, 300-349

    # Check freq=True, zeros=False
    w = WindRose(dir_data, spd_data, 4)
    w.show_freq, w.show_zeros = True, False
    w.frequency_hours = 2
    w.legend_parameters = LegendParameters(segment_count=6)

    chk_poly_num = sum([3, 3, 1, 2])
    assert chk_poly_num == len(w.windrose_lines)

    # For averaged
    w.show_freq = False
    chk_poly_num = 4
    w.colored_mesh
    assert chk_poly_num == len(w.windrose_lines)


def test_with_constant_values():
    """Test drawing of a wind rose with constant values."""
    epw_path = os.path.join(os.getcwd(), 'tests/assets/epw/tokyo.epw')
    epw = EPW(epw_path)

    header = Header(Fraction(), 'fraction', AnalysisPeriod())
    values = [0] * 8760
    data = HourlyContinuousCollection(header, values)

    wind_rose = WindRose(epw.wind_direction, epw.wind_speed)
    wind_rose = WindRose(epw.wind_direction, data)

    assert isinstance(wind_rose.colored_mesh, Mesh2D)
