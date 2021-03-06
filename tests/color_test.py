# coding=utf-8
from __future__ import division

from ladybug.color import Color, Colorset, ColorRange

import pytest


def test_init_color():
    """Test the initialization of color objects."""
    color = Color(255, 0, 100)
    str(color)  # Test the color representation

    assert color.r == 255
    assert color.g == 0
    assert color.b == 100
    assert color.a == 255

    color.r = 100
    assert color.r == 100

    assert len(color) == 4
    assert color == Color(100, 0, 100)
    assert color != Color(100, 0, 0)
    assert color == color.duplicate()

    for c in color:
        assert isinstance(c, int)


def test_init_color_invalid():
    """Test the initialization of invalid color objects."""
    with pytest.raises(Exception):
        Color(256, 0, 100)
    with pytest.raises(Exception):
        Color(-1, 0, 100)
    with pytest.raises(Exception):
        Color(0, 256, 100)
    with pytest.raises(Exception):
        Color(0, -1, 100)
    with pytest.raises(Exception):
        Color(0, 0, 256)
    with pytest.raises(Exception):
        Color(0, 0, -1)


def test_from_dict():
    """Test the from dict method."""
    sample_dict = {'r': '255',
                   'g': '0',
                   'b': '100'}
    color = Color.from_dict(sample_dict)
    assert isinstance(color, Color)
    assert color.r == 255
    assert color.g == 0
    assert color.b == 100


def test_to_from_dict():
    """Test the to/from dict methods."""
    color = Color(255, 0, 100)
    color_dict = color.to_dict()
    new_color = Color.from_dict(color_dict)
    assert new_color.to_dict() == color_dict


def test_init_colorset():
    """Test the initialization of colorset objects."""
    colorset = Colorset()
    str(colorset)  # Test the color representation

    assert len(colorset) > 20
    assert len(colorset[0]) == 10
    for i in range(len(colorset)):
        assert len(colorset[i]) > 1

    for key in colorset._colors.keys():
        for col in colorset._colors[key]:
            assert len(col) == 3


def test_init_colorset_by_name():
    """Test the initialization of colorset objects by name."""
    assert len(Colorset.original()) > 1
    assert len(Colorset.nuanced()) > 1
    assert len(Colorset.multi_colored()) > 1
    assert len(Colorset.ecotect()) > 1
    assert len(Colorset.view_study()) > 1
    assert len(Colorset.shadow_study()) > 1
    assert len(Colorset.glare_study()) > 1
    assert len(Colorset.annual_comfort()) > 1
    assert len(Colorset.thermal_comfort()) > 1
    assert len(Colorset.peak_load_balance()) > 1
    assert len(Colorset.heat_sensation()) > 1
    assert len(Colorset.cold_sensation()) > 1
    assert len(Colorset.benefit_harm()) > 1
    assert len(Colorset.harm()) > 1
    assert len(Colorset.benefit()) > 1
    assert len(Colorset.shade_benefit_harm()) > 1
    assert len(Colorset.shade_harm()) > 1
    assert len(Colorset.shade_benefit()) > 1
    assert len(Colorset.energy_balance()) > 1
    assert len(Colorset.energy_balance_storage()) > 1
    assert len(Colorset.therm()) > 1
    assert len(Colorset.cloud_cover()) > 1
    assert len(Colorset.black_to_white()) > 1
    assert len(Colorset.blue_green_red()) > 1
    assert len(Colorset.multicolored_2()) > 1
    assert len(Colorset.multicolored_3()) > 1


def test_init_color_range():
    """Test the initialization of color range objects."""
    color_range = ColorRange([Color(75, 107, 169), Color(245, 239, 103),
                              Color(234, 38, 0)])
    str(color_range)  # Test the color representation

    assert len(color_range) == 3
    assert isinstance(color_range.colors, tuple)
    assert isinstance(color_range.domain, tuple)
    assert color_range[0] == Color(75, 107, 169)


def test_color_range_discontinuous():
    """Test color range objects with discontinuous colors."""
    color_range = ColorRange(continuous_colors=False)
    color_range.domain = [100, 2000]
    color_range.colors = [Color(75, 107, 169), Color(245, 239, 103),
                          Color(234, 38, 0)]

    assert color_range.color(99) == Color(75, 107, 169)
    assert color_range.color(100) == Color(245, 239, 103)
    assert color_range.color(2000) == Color(245, 239, 103)
    assert color_range.color(2001) == Color(234, 38, 0)


def test_color_range_continuous():
    """Test color range objects with continuous colors."""
    color_range = ColorRange([Color(0, 100, 0), Color(100, 200, 100)], [0, 1000])

    assert color_range.color(-100) == Color(0, 100, 0)
    assert color_range.color(0) == Color(0, 100, 0)
    assert color_range.color(500) == Color(50, 150, 50)
    assert color_range.color(250) == Color(25, 125, 25)
    assert color_range.color(1000) == Color(100, 200, 100)
    assert color_range.color(1100) == Color(100, 200, 100)


def test_color_range_from_dict():
    """Test the from_dict method."""
    sample_dict = {'colors': [{'r': '0', 'g': '0', 'b': '0'},
                              {'r': '0', 'g': '255', 'b': '100'}]}
    color_range = ColorRange.from_dict(sample_dict)
    assert isinstance(color_range, ColorRange)
    assert color_range[0] == Color(0, 0, 0)
    assert color_range[1] == Color(0, 255, 100)


def test_color_range_to_from_dict():
    """Test the to/from dict methods."""
    color_range = ColorRange([Color(0, 100, 0), Color(100, 200, 100)], [0, 1000])
    color_range_dict = color_range.to_dict()
    new_color = ColorRange.from_dict(color_range_dict)
    assert new_color.to_dict() == color_range_dict
