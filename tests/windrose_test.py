# coding=utf-8
from __future__ import division

from ladybug.datatype.temperature import Temperature
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.header import Header
from ladybug.legend import Legend, LegendParameters
from ladybug.datacollection import HourlyContinuousCollection
from ladybug.datacollectionimmutable import HourlyContinuousCollectionImmutable
from ladybug.windrose import WindRose
from ladybug.epw import EPW

from pprint import pprint as pp
import numpy as np
from math import cos, sin, pi


def _polar_to_rect(theta, radius):
    """Polar args to rectangular coordinates"""
    t = 180 / pi
    theta += 90
    return radius * cos(theta/t), radius * sin(theta/t)

def test_bin_array():
    """Test the generatin of bin array from bin range and num"""

    # Base case
    bin_arr = WindRose._bin_array(1, (0, 360))
    assert [0, 360.0] == bin_arr, bin_arr

    # Simple 2 div
    bin_arr = WindRose._bin_array(2, (0, 360))
    assert [0, 180.0, 360.0] == bin_arr, bin_arr

    # Simple 3 case
    bin_arr = WindRose._bin_array(3, (0, 360))
    assert [0.0, 120.0, 240.0, 360.0] == bin_arr, bin_arr

    # Simple 4 case
    bin_arr = WindRose._bin_array(4, (0, 360))
    assert [0.0, 90.0, 180.0, 270.0, 360.0] == bin_arr, bin_arr

    # Start from non zero
    bin_arr = WindRose._bin_array(3, (180, 360))
    assert [180.0, 240.0, 300.0, 360.0] == bin_arr, bin_arr


def test_histogram():
    """Test the windrose histogram."""

    # Test out of bounds with 3 divisions
    bin_arr = WindRose._bin_array(3, (0, 3))
    vals = [0, 0, 0, 1, 1, 1, 2, 2]
    hist = WindRose.histogram_bins(vals, bin_arr)
    assert hist == [[0, 0, 0], [1, 1, 1], [2, 2]]

    # Test out of bounds with 2 divisions
    bin_arr = WindRose._bin_array(2, (0, 3))
    vals = [-1, -2, 10, 0, 0, 0, 1, 1, 1, 2, 2, 34]
    hist = WindRose.histogram_bins(vals, bin_arr)
    assert hist == [[0, 0, 0, 1, 1, 1], [2, 2]], hist

    # Test edge bounds
    bin_arr = WindRose._bin_array(2, (0, 3))
    vals = [0, 0, 0, 1, 1, 1, 2, 2, 3, 3]
    hist = WindRose.histogram_bins(vals, bin_arr)
    assert hist == [[0, 0, 0, 1, 1, 1], [2, 2]], hist

    # Test edge bounds 2
    hist = WindRose.histogram_bins([0, 0, 0.9, 1, 1.5, 1.99, 2, 3], (0, 1, 2, 3))
    assert hist == [[0, 0, 0.9], [1, 1.5, 1.99], [2]], hist


def test_bin_polar():
    """Test polar coordinate array"""

    # Init simple dir set divided by 4
    bin_arr = (0, 90, 180, 270, 360)
    vals = [0, 0, 0, 10, 85, 90, 95, 170, 285, 288]
    hist = [[0, 0, 0, 10, 85], [90, 95, 170], [], [285, 288]]

    phist = WindRose._bin_polar(bin_arr)
    r1, r2, r3, r4 = 0.5, 0.3, 0.0, 0.2  # radius
    p2r = _polar_to_rect
    chk_phist = [
        [p2r(0, r1), p2r(90, r1)],     # 0-90
        [p2r(90, r2), p2r(180, r2)],   # 90-180
        [p2r(180, r3), p2r(270, r3)],  # 180-270
        [p2r(270, r4), p2r(360, r4)]]  # 270-360

    # for chk_coords, coords in zip(chk_phist, phist):
    #     for chk_vec, vec in zip(chk_coords, coords):
    #         # Check x, y
    #         assert abs(chk_vec[0] - vec[0]) < 1e-10
    #         assert abs(chk_vec[1] - vec[1]) < 1e-10


def test_polar_histogram():
    # Init simple dir set divided by 4
    bin_arr = (0, 90, 180, 270, 360)
    dir_vals = [0, 0, 0, 10, 85, 90, 95, 170, 285, 288]
    vel_vals = [10, 10, 30, 10, 5, 9, 9, 17, 25, 28]
    phist, xticks, yticks = WindRose.histogram_polar_coords(dir_vals, vel_vals, bin_arr)

    #pp(phist)
    #r1, r2, r3, r4 = 0.5, 0.3, 0.0, 0.2  # radius
    #pp(phist)

def test_plot_polar_histogram():
    # Plot histogram
    bin_arr = (0, 90, 180, 270, 360)
    dir_vals = [0, 0, 0, 10, 85, 90, 95, 170, 285, 288]
    vel_vals = [10, 10, 30, 10, 5, 9, 9, 17, 25, 28]
    phist, xticks, yticks = WindRose.histogram_polar_coords(dir_vals, vel_vals, bin_arr)

    #phist, xticks, yticks = WindRose.plot_histogram(phist, xyticks, yticks)


if __name__ == '__main__':
    test_bin_array()
    test_histogram()
    test_bin_polar()
    test_polar_histogram()