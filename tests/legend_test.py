# coding=utf-8
from __future__ import division

from ladybug.legend import Legend, LegendParameters, LegendParametersCategorized
from ladybug.color import Color, Colorset, ColorRange
from ladybug.datatype.thermalcondition import PredictedMeanVote

from ladybug_geometry.geometry2d.pointvector import Point2D
from ladybug_geometry.geometry2d.mesh import Mesh2D
from ladybug_geometry.geometry3d.pointvector import Point3D, Vector3D
from ladybug_geometry.geometry3d.plane import Plane
from ladybug_geometry.geometry3d.mesh import Mesh3D

import pytest


def test_init_legend_parameters():
    """Test the initialization of LegendParameter objects."""
    leg_par = LegendParameters(0, 1000)
    str(leg_par)  # Test the LegendParameters representation
    hash(leg_par)

    assert leg_par.min == 0
    assert leg_par.max == 1000
    assert leg_par.is_segment_count_default
    assert leg_par.is_title_default
    assert leg_par.is_base_plane_default
    assert leg_par.is_segment_height_default
    assert leg_par.is_segment_width_default
    assert leg_par.is_text_height_default

    leg_par_copy = leg_par.duplicate()
    assert leg_par_copy.min == leg_par.min
    assert leg_par_copy.max == leg_par.max
    assert leg_par_copy.segment_count == leg_par.segment_count


def test_equality():
    """Test the equality of legend parameters."""
    leg_par = LegendParameters(0, 1000)
    leg_par_dup = leg_par.duplicate()

    assert leg_par is not leg_par_dup
    assert leg_par == leg_par_dup
    leg_par_dup.segment_count = 3
    assert leg_par != leg_par_dup


def test_to_from_dict():
    """Test the to/from dict methods."""
    leg_par = LegendParameters(0, 1000)
    leg_par_dict = leg_par.to_dict()
    new_leg_par = LegendParameters.from_dict(leg_par_dict)
    assert new_leg_par.to_dict() == leg_par_dict


def test_colors():
    """Test the LegendParameter colors property."""
    leg_par = LegendParameters(colors=[Color(0, 0, 0), Color(255, 255, 255)])

    assert len(leg_par.colors) == 2
    assert leg_par.colors[0] == Color(0, 0, 0)
    assert leg_par.colors[1] == Color(255, 255, 255)

    leg_par_copy = leg_par.duplicate()
    assert len(leg_par_copy.colors) == 2
    assert leg_par_copy.colors[0] == Color(0, 0, 0)
    assert leg_par_copy.colors[1] == Color(255, 255, 255)

    leg_par.colors = [Color(0, 0, 0), Color(100, 100, 100)]
    assert leg_par.colors[1] == Color(100, 100, 100)

    with pytest.raises(Exception):
        leg_par = LegendParameters(colors=[0, 1])
    with pytest.raises(Exception):
        leg_par.colors = [0, 1]


def test_continuous_legend():
    """Test the LegendParameter continuous_legend property."""
    leg_par = LegendParameters()
    leg_par.continuous_legend = True

    assert leg_par.continuous_legend
    leg_par_copy = leg_par.duplicate()
    assert leg_par_copy.continuous_legend

    leg_par.continuous_legend = False
    assert not leg_par.continuous_legend

    with pytest.raises(Exception):
        leg_par = LegendParameters(continuous_legend='yes')
    with pytest.raises(Exception):
        leg_par.continuous_legend = 'yes'


def test_title():
    """Test the LegendParameter title property."""
    leg_par = LegendParameters(title='m2')

    assert leg_par.title == 'm2'
    assert not leg_par.is_title_default
    leg_par_copy = leg_par.duplicate()
    assert leg_par_copy.title == 'm2'

    leg_par.title = 'm2'
    assert leg_par.title == 'm2'

    with pytest.raises(Exception):
        leg_par = LegendParameters(title=2)
    with pytest.raises(Exception):
        leg_par.title = 2


def test_ordinal_dictionary():
    """Test the LegendParameter ordinal_dictionary property."""
    leg_par = LegendParameters(min=0, max=1)
    leg_par.ordinal_dictionary = {0: 'False', 1: 'True'}

    assert leg_par.ordinal_dictionary == {0: 'False', 1: 'True'}
    leg_par_copy = leg_par.duplicate()
    assert leg_par_copy.ordinal_dictionary == {0: 'False', 1: 'True'}

    leg_par.ordinal_dictionary = {0: 'No', 1: 'Yes'}
    assert leg_par.ordinal_dictionary == {0: 'No', 1: 'Yes'}

    with pytest.raises(Exception):
        leg_par = LegendParameters(ordinal_dictionary=['False', 'True'])
    with pytest.raises(Exception):
        leg_par.ordinal_dictionary = ['False', 'True']


def test_decimal_count():
    """Test the LegendParameter decimal_count property."""
    leg_par = LegendParameters()
    leg_par.decimal_count = 3

    assert leg_par.decimal_count == 3
    leg_par_copy = leg_par.duplicate()
    assert leg_par_copy.decimal_count == 3

    leg_par.decimal_count = 0
    assert leg_par.decimal_count == 0

    with pytest.raises(Exception):
        leg_par = LegendParameters(decimal_count='2')
    with pytest.raises(Exception):
        leg_par.decimal_count = '2'


def test_vertical():
    """Test the LegendParameter continuous_legend property."""
    leg_par = LegendParameters()
    leg_par.vertical = False

    assert not leg_par.vertical
    leg_par_copy = leg_par.duplicate()
    assert not leg_par_copy.vertical

    leg_par.vertical = True
    assert leg_par.vertical

    with pytest.raises(Exception):
        leg_par = LegendParameters(vertical='yes')
    with pytest.raises(Exception):
        leg_par.vertical = 'yes'


def test_base_plane():
    """Test the LegendParameter base_plane property."""
    leg_par = LegendParameters(
        base_plane=Plane(Vector3D(0, 0, 0), Point3D(10, 10, 0)))

    assert leg_par.base_plane.o == Point3D(10, 10, 0)
    assert not leg_par.is_base_plane_default
    leg_par_copy = leg_par.duplicate()
    assert leg_par_copy.base_plane.o == Point3D(10, 10, 0)

    leg_par.base_plane = Plane(Vector3D(0, 0, 0), Point3D(-10, -10, 0))
    assert leg_par.base_plane.o == Point3D(-10, -10, 0)

    with pytest.raises(Exception):
        leg_par = LegendParameters(base_plane=Point3D(-10, -10, 0))
    with pytest.raises(Exception):
        leg_par.base_plane = Point3D(-10, -10, 0)


def test_segment_height():
    """Test the LegendParameter segment_height property."""
    leg_par = LegendParameters()
    leg_par.segment_height = 3

    assert leg_par.segment_height == 3
    assert not leg_par.is_segment_height_default
    leg_par_copy = leg_par.duplicate()
    assert leg_par_copy.segment_height == 3

    leg_par.segment_height = 2
    assert leg_par.segment_height == 2

    with pytest.raises(Exception):
        leg_par = LegendParameters(segment_height=0)
    with pytest.raises(Exception):
        leg_par.segment_height = 0


def test_segment_width():
    """Test the LegendParameter segment_width property."""
    leg_par = LegendParameters()
    leg_par.segment_width = 3

    assert leg_par.segment_width == 3
    assert not leg_par.is_segment_width_default
    leg_par_copy = leg_par.duplicate()
    assert leg_par_copy.segment_width == 3

    leg_par.segment_width = 2
    assert leg_par.segment_width == 2

    with pytest.raises(Exception):
        leg_par = LegendParameters(segment_width=0)
    with pytest.raises(Exception):
        leg_par.segment_width = 0


def test_text_height():
    """Test the LegendParameter text_height property."""
    leg_par = LegendParameters()
    leg_par.text_height = 0.25

    assert leg_par.text_height == 0.25
    assert not leg_par.is_text_height_default
    leg_par_copy = leg_par.duplicate()
    assert leg_par_copy.text_height == 0.25

    leg_par.text_height = 2
    assert leg_par.text_height == 2

    with pytest.raises(Exception):
        leg_par = LegendParameters(text_height=0)
    with pytest.raises(Exception):
        leg_par.text_height = 0


def test_font():
    """Test the LegendParameter font property."""
    leg_par = LegendParameters()
    leg_par.font = 'Times'

    assert leg_par.font == 'Times'
    leg_par_copy = leg_par.duplicate()
    assert leg_par_copy.font == 'Times'

    leg_par.font = 'Courier'
    assert leg_par.font == 'Courier'

    with pytest.raises(Exception):
        leg_par = LegendParameters(font=0)
    with pytest.raises(Exception):
        leg_par.font = 0


def test_init_legend():
    """Test the initialization of Legend objects."""
    legend = Legend([0, 10])
    str(legend)  # Test the Legend representation
    hash(legend)

    assert len(legend) == 2
    assert legend[0] == 0
    assert legend[1] == 10
    for item in legend:
        assert isinstance(item, (float, int))

    assert len(legend.values) == 2
    assert legend.legend_parameters.min == 0
    assert legend.legend_parameters.max == 10
    assert legend.is_min_default
    assert legend.is_max_default
    assert legend.legend_parameters.is_segment_count_default
    assert legend.legend_parameters.is_title_default
    assert legend.legend_parameters.is_base_plane_default
    assert legend.legend_parameters.is_segment_height_default
    assert legend.legend_parameters.is_segment_width_default
    assert legend.legend_parameters.is_text_height_default

    legend_copy = legend.duplicate()
    assert legend_copy.values == legend.values
    assert legend_copy.legend_parameters.min == legend.legend_parameters.min
    assert legend_copy.legend_parameters.max == legend.legend_parameters.max
    assert legend_copy.legend_parameters.segment_count == \
        legend.legend_parameters.segment_count
    assert legend_copy.is_min_default
    assert legend_copy.is_max_default
    assert legend_copy.legend_parameters.is_segment_count_default
    assert legend_copy.legend_parameters.is_title_default
    assert legend_copy.legend_parameters.is_base_plane_default
    assert legend_copy.legend_parameters.is_segment_height_default
    assert legend_copy.legend_parameters.is_segment_width_default
    assert legend_copy.legend_parameters.is_text_height_default

    assert legend_copy == legend
    legend_copy.legend_parameters.segment_count = 3
    assert legend_copy != legend


def test_init_legend_with_parameter():
    """Test the initialization of Legend with LegendParameter objects."""
    legend = Legend([0, 10], LegendParameters(2, 8))

    assert len(legend.values) == 2
    assert legend.legend_parameters.min == 2
    assert legend.legend_parameters.max == 8
    assert not legend.is_min_default
    assert not legend.is_max_default


def test_legend_to_from_dict():
    """Test the to/from dict methods."""
    legend = Legend([0, 10], LegendParameters(2, 8))
    legend_dict = legend.to_dict()
    new_legend = Legend.from_dict(legend_dict)
    assert new_legend.to_dict() == legend_dict


def test_legend_value_colors():
    """Test the color_range, value_colors, and segment_colors property."""
    legend = Legend(range(5), LegendParameters(segment_count=10))

    for i, color in enumerate(legend.color_range):
        assert color == ColorRange()[i]
    assert legend.color_range.domain == ColorRange(domain=(0, 4)).domain

    assert len(legend.values) == 5
    assert len(legend.value_colors) == 5
    assert legend.value_colors[0] == Colorset.original()[0]
    assert legend.segment_colors == Colorset.original()


def test_legend_title():
    """Test the title property."""
    legend = Legend(range(5))
    assert legend.title == ''
    assert legend.legend_parameters.is_title_default
    assert legend.title_location.o == Point3D(0, 11.25, 0)
    assert legend.title_location_2d == Point2D(0, 11.25)

    legend = Legend(range(5), LegendParameters(segment_count=5, title='C'))
    assert legend.title == 'C'
    assert not legend.legend_parameters.is_title_default
    assert legend.title_location.o == Point3D(0, 5.25, 0)
    assert legend.title_location_2d == Point2D(0, 5.25)


def test_segment_text():
    """Test the segment_text property."""
    legend = Legend(range(10), LegendParameters(segment_count=6))

    assert len(legend.segment_text_location) == len(legend.segment_text) == 6
    assert legend.segment_text == ['0.00', '1.80', '3.60', '5.40', '7.20', '9.00']
    for pl in legend.segment_text_location:
        assert isinstance(pl, Plane)
    for pt in legend.segment_text_location_2d:
        assert isinstance(pt, Point2D)
    seg_num = [0, 1.8, 3.6, 5.4, 7.2, 9]
    for i, num in enumerate(legend.segment_numbers):
        assert num == pytest.approx(seg_num[i], rel=1e-3)

    legend = Legend(range(10), LegendParameters(segment_count=6))
    legend.legend_parameters.vertical = False

    assert len(legend.segment_text_location) == len(legend.segment_text) == 6
    assert legend.segment_text == ['0.00', '1.80', '3.60', '5.40', '7.20', '9.00']
    for pl in legend.segment_text_location:
        assert isinstance(pl, Plane)


def test_segment_text_ordinal_dictionary():
    """Test the segment_text property with ordinal dictionary."""
    results = list(range(3000))
    ordinal_dict = {300: 'low', 1150: 'desired', 2000: 'too much'}
    legend = Legend(results, LegendParameters(min=300, max=2000, segment_count=3))
    legend.legend_parameters.ordinal_dictionary = ordinal_dict

    assert len(legend.segment_text_location) == len(legend.segment_text) == 3
    assert legend.segment_text == ['low', 'desired', 'too much']
    assert len(set(legend.value_colors)) > 100


def test_segment_text_ordinal_dictionary_large():
    """Test the segment_text property with another larger ordinal dictionary."""
    results = list(range(-4, 5))
    ordinal_dict = PredictedMeanVote().unit_descr
    legend = Legend(results, LegendParameters(min=-3, max=3, segment_count=7))
    legend.legend_parameters.ordinal_dictionary = ordinal_dict
    assert legend.segment_text == ['Cold', 'Cool', 'Slightly Cool', 'Neutral',
                                   'Slightly Warm', 'Warm', 'Hot']

    legend.legend_parameters.min = -2
    legend.legend_parameters.max = 2
    legend.legend_parameters.segment_count = 5
    assert legend.segment_text == ['Cool', 'Slightly Cool', 'Neutral',
                                   'Slightly Warm', 'Warm']


def test_segment_mesh():
    """Test the segment_mesh property."""
    legend = Legend(range(10), LegendParameters(segment_count=6))

    assert isinstance(legend.segment_mesh, Mesh3D)
    assert len(legend.segment_mesh.faces) == 6
    assert len(legend.segment_mesh.vertices) == 14
    legend.legend_parameters.vertical = False
    assert len(legend.segment_mesh.faces) == 6
    assert len(legend.segment_mesh.vertices) == 14

    legend.legend_parameters.continuous_legend = True
    assert len(legend.segment_mesh.faces) == 5
    assert len(legend.segment_mesh.vertices) == 12
    legend.legend_parameters.vertical = True
    assert len(legend.segment_mesh.faces) == 5
    assert len(legend.segment_mesh.vertices) == 12


def test_segment_mesh_2d():
    """Test the segment_mesh_2d property."""
    legend = Legend(range(10), LegendParameters(segment_count=6))

    assert isinstance(legend.segment_mesh_2d, Mesh2D)
    assert len(legend.segment_mesh_2d.faces) == 6
    assert len(legend.segment_mesh_2d.vertices) == 14
    legend.legend_parameters.vertical = False
    assert len(legend.segment_mesh_2d.faces) == 6
    assert len(legend.segment_mesh_2d.vertices) == 14

    legend.legend_parameters.continuous_legend = True
    assert len(legend.segment_mesh_2d.faces) == 5
    assert len(legend.segment_mesh_2d.vertices) == 12
    legend.legend_parameters.vertical = True
    assert len(legend.segment_mesh_2d.faces) == 5
    assert len(legend.segment_mesh_2d.vertices) == 12


def test_init_legend_parameters_categorized():
    """Test the initialization of LegendParametersCategorized objects."""
    leg_colors = [Color(0, 0, 255), Color(0, 255, 0), Color(255, 0, 0)]
    leg_par = LegendParametersCategorized([300, 2000], leg_colors)
    leg_par.decimal_count = 0
    str(leg_par)  # Test the LegendParametersCategorized representation
    hash(leg_par)

    assert leg_par.domain == (300, 2000)
    assert leg_par.colors == tuple(leg_colors)
    assert leg_par.category_names == ('<300', '300 - 2000', '>2000')
    assert leg_par.min == 300
    assert leg_par.max == 2000
    assert leg_par.is_segment_count_default
    assert leg_par.is_title_default
    assert leg_par.is_base_plane_default
    assert leg_par.is_segment_height_default
    assert leg_par.is_segment_width_default
    assert leg_par.is_text_height_default

    leg_par_copy = leg_par.duplicate()
    assert leg_par_copy.domain == leg_par.domain
    assert leg_par_copy.colors == leg_par.colors
    assert leg_par_copy.category_names == leg_par.category_names

    assert leg_par_copy == leg_par
    leg_par_copy.segment_height = 0.5
    assert leg_par_copy != leg_par


def test_categorized_to_from_dict():
    """Test the LegendParametersCategorized to/from dict methods."""
    leg_colors = [Color(0, 0, 255), Color(0, 255, 0), Color(255, 0, 0)]
    leg_par = LegendParametersCategorized([300, 2000], leg_colors)
    leg_par_dict = leg_par.to_dict()
    new_leg_par = LegendParametersCategorized.from_dict(leg_par_dict)
    assert new_leg_par.to_dict() == leg_par_dict


def test_categorized_colors():
    """Test the LegendParametersCategorized colors property."""
    data = [100, 300, 500, 1000, 2000, 3000]
    leg_colors = [Color(0, 0, 255), Color(0, 255, 0), Color(255, 0, 0)]
    legend_par = LegendParametersCategorized([300, 2000], leg_colors)

    legend = Legend(data, legend_par)
    assert legend.segment_colors == tuple(leg_colors)
    assert legend.value_colors == \
        (Color(0, 0, 255), Color(0, 255, 0), Color(0, 255, 0), Color(0, 255, 0),
         Color(0, 255, 0), Color(255, 0, 0))

    legend.legend_parameters.continuous_colors = True
    assert legend.value_colors == \
        (Color(0, 0, 255), Color(0, 0, 255), Color(0, 60, 195), Color(0, 210, 45),
         Color(255, 0, 0), Color(255, 0, 0))


def test_categorized_category_names():
    """Test the LegendParametersCategorized category_names property."""
    data = [100, 300, 500, 1000, 2000, 3000]
    leg_colors = [Color(0, 0, 255), Color(0, 255, 0), Color(255, 0, 0)]
    legend_par = LegendParametersCategorized([300, 2000], leg_colors)
    cat_names = ['low', 'desired', 'too much']
    legend_par.category_names = cat_names
    legend = Legend(data, legend_par)

    assert legend_par.category_names == tuple(cat_names)
    assert legend.segment_text == tuple(cat_names)

    with pytest.raises(AssertionError):
        legend_par.category_names = ['low', 'desired', 'too much', 'not a category']
