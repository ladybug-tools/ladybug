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
    hist = WindRose.histogram(vals, bin_arr)
    assert hist == [[0, 0, 0], [1, 1, 1], [2, 2]]

    # Test out of bounds with 2 divisions
    bin_arr = WindRose._bin_array(2, (0, 3))
    vals = [-1, -2, 10, 0, 0, 0, 1, 1, 1, 2, 2, 34]
    hist = WindRose.histogram(vals, bin_arr)
    assert hist == [[0, 0, 0, 1, 1, 1], [2, 2]]


def test_windrose():
    # Init
    #path = './tests/fixtures/epw/tokyo.epw'
    #epw = EPW(path)

    # epw.wind_direction.values
    # epw.wind_speed.values

    pass


if __name__ == '__main__':

    test_bin_array()
    test_histogram()
