# coding=utf-8
from __future__ import division

from ladybug.datatype.temperature import Temperature
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.header import Header
from ladybug.legend import Legend, LegendParameters
from ladybug.datacollection import HourlyContinuousCollection
from ladybug.datacollectionimmutable import HourlyContinuousCollectionImmutable
from ladybug.epw import EPW
from ladybug.windrose import WindRose, linspace, histogram, histogram_circular

from pprint import pprint as pp
import os

# Simplify method names
linspace = HourlyContinuousCollection.linspace
histogram = HourlyContinuousCollection.histogram
histogram_circular = HourlyContinuousCollection.histogram_circular


# def test_linspace():
#     """Test the generation of bin array from bin range and num"""

#     # Base case
#     bin_arr = linspace(0, 360, 0)
#     assert [] == bin_arr, bin_arr

#     bin_arr = linspace(0, 360, 1)
#     assert [0] == bin_arr, bin_arr

#     bin_arr = linspace(0, 360, 2)
#     assert [0, 360.0] == bin_arr, bin_arr

#     bin_arr = linspace(0, 360, 4)
#     assert [0.0, 120.0, 240.0, 360.0] == bin_arr, bin_arr

#     bin_arr = linspace(0, 360, 5)
#     assert [0.0, 90.0, 180.0, 270.0, 360.0] == bin_arr, bin_arr

#     # Start from non zero
#     bin_arr = linspace(180, 360, 4)
#     assert [180.0, 240.0, 300.0, 360.0] == bin_arr, bin_arr

#     # Start from non zero, w/ floats
#     bin_arr = linspace(180., 360., 4)
#     assert [180., 240.0, 300.0, 360.0] == bin_arr, bin_arr


# def test_histogram():
#     """Test the windrose histogram."""

#     # Test simple 2 div
#     bin_arr = linspace(0, 2, 3)
#     assert bin_arr == [0, 1, 2]
#     vals = [0, 0, 0, 1, 1, 1, 2, 2]
#     hist = histogram(vals, bin_arr)
#     assert hist == [[0, 0, 0], [1, 1, 1]]

#     # Test out of bounds with 3 divisions
#     bin_arr = linspace(0, 3, 4)
#     vals = [0, 0, 0, 1, 1, 1, 2, 2]
#     hist = histogram(vals, bin_arr)
#     assert hist == [[0, 0, 0], [1, 1, 1], [2, 2]]

#     # Test out of bounds with 2 divisions
#     bin_arr = linspace(0, 3, 3)
#     vals = [-1, -2, 10, 0, 0, 0, 1, 1, 1, 2, 2, 34]
#     hist = histogram(vals, bin_arr)
#     assert hist == [[-2, -1, 0, 0, 0, 1, 1, 1], [2, 2]], hist

#     # Test edge bounds
#     bin_arr = linspace(0, 3, 3)
#     vals = [0, 0, 0, 1, 1, 1, 2, 2, 3, 3]
#     hist = histogram(vals, bin_arr)
#     assert hist == [[0, 0, 0, 1, 1, 1], [2, 2]], hist

#     # Test edge bounds 2
#     hist = histogram([0, 0, 0.9, 1, 1.5, 1.99, 2, 3], (0, 1, 2, 3))
#     assert hist == [[0, 0, 0.9], [1, 1.5, 1.99], [2]], hist


# def test_histogram_circular():
#     """Test the windrose histogram_circular data."""

#     # Test out of bounds with 3 divisions
#     bin_arr = linspace(-2, 2, 3)
#     assert bin_arr == [-2, 0, 2], bin_arr
#     vals = [-2, -1, 0, 0, 0, 1, 1, 1, 2, 2]
#     hist = histogram_circular(vals, bin_arr)
#     assert hist == [[-2, -1], [0, 0, 0, 1, 1, 1]], hist


# def test_bin_polar():
#     """Test polar coordinate array"""

#     # Init simple dir set divided by 4
#     bin_arr = (0, 90, 180, 270, 360)

#     #vals = [0, 0, 0, 10, 85, 90, 95, 170, 285, 288]
#     #hist = [[0, 0, 0, 10, 85], [90, 95, 170], [], [285, 288]]

#     # WindRose._histogram_array_radial(bin_vecs, vec_cpt, hist, radius_arr, ytick_num,
#     #                             show_stack):
#     # phist = WindRose._bin_polar(bin_arr)
#     # r1, r2, r3, r4 = 0.5, 0.3, 0.0, 0.2  # radius
#     # p2r = _polar_to_rect
#     # chk_phist = [
#     #     [p2r(0, r1), p2r(90, r1)],     # 0-90
#     #     [p2r(90, r2), p2r(180, r2)],   # 90-180
#     #     [p2r(180, r3), p2r(270, r3)],  # 180-270
#     #     [p2r(270, r4), p2r(360, r4)]]  # 270-360

#     # # for chk_coords, coords in zip(chk_phist, phist):
#     #     for chk_vec, vec in zip(chk_coords, coords):
#     #         # Check x, y
#     #         assert abs(chk_vec[0] - vec[0]) < 1e-10
#     #         assert abs(chk_vec[1] - vec[1]) < 1e-10


# # def test_polar_histogram():
# #     # Init simple dir set divided by 4
# #     bin_arr = (0, 90, 180, 270, 360)
# #     dir_vals = [0, 0, 0, 10, 85, 90, 95, 170, 285, 288]
# #     vel_vals = [10, 10, 30, 10, 5, 9, 9, 17, 25, 28]
# #     phist, xticks, yticks = WindRose.histogram_polar_coords(dir_vals, vel_vals, bin_arr)

# #     #pp(phist)
# #     #r1, r2, r3, r4 = 0.5, 0.3, 0.0, 0.2  # radius
# #     #pp(phist)


# # def test_plot_polar_histogram():
# #     # Plot histogram
# #     bin_arr  = (0, 90, 180, 270, 360)
# #     dir_vals = [0, 0, 0, 10, 85, 90, 95, 170, 285, 288]
# #     vel_vals = [10, 10, 30, 10, 5, 9, 9, 17, 25, 28]

# #     phist, xticks, yticks = WindRose.histogram_polar_coords(dir_vals, vel_vals, bin_arr)

# #     #phist, xticks, yticks = WindRose.plot_histogram(phist, xyticks, yticks)


# # def test_histogram_interval_color():

# #     bin_arr = (0, 90, 180, 270, 360)
# #     dir_vals = [0, 0, 0, 10, 85, 90, 95, 170, 285, 288]
# #     vel_vals = [10, 10, 30, 10, 5, 9, 9, 17, 25, 28]
# #     yticks = 3

# #     # Compute
# #     hist_data = WindRose.histogram_data(zip(dir_vals, vel_vals), bin_arr,
# #                                         key=lambda v: v[0])
# #     hist_coords, xgrid, ygrid = WindRose.histogram_coords_polar(
# #         hist_data, vel_vals, bin_arr, yticks)

# #     # Bins
# #     # 0-90:    [10, 10, 30, 10, 5]
# #     # 90-180:  [9, 9, 17]
# #     # 180-270: []
# #     # 270-360: [25, 28]

# #     # Colors
# #     colors = WindRose._compute_bar_interval_colors(hist_data, hist_coords)

# def test_windrose_mesh():
#     # Plot windrose
#     epw_path = os.path.join(os.getcwd(), 'tests/fixtures/epw/tokyo.epw')
#     epw = EPW(epw_path)

#     w = WindRose(epw.wind_direction, epw.wind_speed, 16)
#     mesh = w.colored_mesh

if __name__ == '__main__':
    # test_linspace()
    # test_histogram()
    # test_histogram_circular()
    # test_bin_polar()
    # # # test_polar_histogram()
    # # # test_histogram_interval_color()
    # test_windrose_mesh()
    pass