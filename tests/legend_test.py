# coding=utf-8
from __future__ import division

from ladybug.legend import Legend, LegendParameters
from ladybug.color import Color, Colorset, ColorRange
from ladybug.datatype.thermalcondition import PredictedMeanVote

from ladybug_geometry.geometry3d.pointvector import Point3D, Vector3D
from ladybug_geometry.geometry3d.plane import Plane

import unittest
import pytest


class LegendParametersTestCase(unittest.TestCase):
    """Test for LegendParameters"""

    def test_init_legend_parameters(self):
        """Test the initialization of LegendParameter objects."""
        leg_par = LegendParameters(0, 1000)
        str(leg_par)  # Test the LegendParameters representation

        assert leg_par.min == 0
        assert leg_par.max == 1000
        assert leg_par.is_number_of_segments_default is True
        assert leg_par.is_title_default is True
        assert leg_par.is_base_plane_default is True
        assert leg_par.is_segment_height_default is True
        assert leg_par.is_segment_width_default is True
        assert leg_par.is_text_height_default is True

        leg_par_copy = leg_par.duplicate()
        assert leg_par_copy.min == leg_par.min
        assert leg_par_copy.max == leg_par.max
        assert leg_par_copy.number_of_segments == leg_par.number_of_segments

    def test_to_from_json(self):
        """Test the to/from json methods."""
        leg_par = LegendParameters(0, 1000)
        leg_par_json = leg_par.to_json()
        new_leg_par = LegendParameters.from_json(leg_par_json)
        assert new_leg_par.to_json() == leg_par_json

    def test_colors(self):
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

    def test_continuous_colors(self):
        """Test the LegendParameter continuous_colors property."""
        leg_par = LegendParameters(continuous_colors=False)

        assert leg_par.continuous_colors is False
        leg_par_copy = leg_par.duplicate()
        assert leg_par_copy.continuous_colors is False

        leg_par.continuous_colors = True
        assert leg_par.continuous_colors is True

        with pytest.raises(Exception):
            leg_par = LegendParameters(continuous_colors='yes')
        with pytest.raises(Exception):
            leg_par.continuous_colors = 'yes'

    def test_continuous_legend(self):
        """Test the LegendParameter continuous_legend property."""
        leg_par = LegendParameters(continuous_legend=True)

        assert leg_par.continuous_legend is True
        leg_par_copy = leg_par.duplicate()
        assert leg_par_copy.continuous_legend is True

        leg_par.continuous_legend = False
        assert leg_par.continuous_legend is False

        with pytest.raises(Exception):
            leg_par = LegendParameters(continuous_legend='yes')
        with pytest.raises(Exception):
            leg_par.continuous_legend = 'yes'

    def test_title(self):
        """Test the LegendParameter title property."""
        leg_par = LegendParameters(title='m2')

        assert leg_par.title == 'm2'
        assert leg_par.is_title_default is False
        leg_par_copy = leg_par.duplicate()
        assert leg_par_copy.title == 'm2'

        leg_par.title = 'm2'
        assert leg_par.title == 'm2'

        with pytest.raises(Exception):
            leg_par = LegendParameters(title=2)
        with pytest.raises(Exception):
            leg_par.title = 2

    def test_ordinal_dictionary(self):
        """Test the LegendParameter ordinal_dictionary property."""
        leg_par = LegendParameters(
            min=0, max=1, ordinal_dictionary={0: 'False', 1: 'True'})

        assert leg_par.ordinal_dictionary == {0: 'False', 1: 'True'}
        leg_par_copy = leg_par.duplicate()
        assert leg_par_copy.ordinal_dictionary == {0: 'False', 1: 'True'}

        leg_par.ordinal_dictionary = {0: 'No', 1: 'Yes'}
        assert leg_par.ordinal_dictionary == {0: 'No', 1: 'Yes'}

        with pytest.raises(Exception):
            leg_par = LegendParameters(ordinal_dictionary=['False', 'True'])
        with pytest.raises(Exception):
            leg_par.ordinal_dictionary = ['False', 'True']

    def test_number_decimal_places(self):
        """Test the LegendParameter number_decimal_places property."""
        leg_par = LegendParameters(number_decimal_places=3)

        assert leg_par.number_decimal_places == 3
        leg_par_copy = leg_par.duplicate()
        assert leg_par_copy.number_decimal_places == 3

        leg_par.number_decimal_places = 0
        assert leg_par.number_decimal_places == 0

        with pytest.raises(Exception):
            leg_par = LegendParameters(number_decimal_places='2')
        with pytest.raises(Exception):
            leg_par.number_decimal_places = '2'

    def test_vertical_or_horizontal(self):
        """Test the LegendParameter continuous_legend property."""
        leg_par = LegendParameters(vertical_or_horizontal=False)

        assert leg_par.vertical_or_horizontal is False
        leg_par_copy = leg_par.duplicate()
        assert leg_par_copy.vertical_or_horizontal is False

        leg_par.vertical_or_horizontal = True
        assert leg_par.vertical_or_horizontal is True

        with pytest.raises(Exception):
            leg_par = LegendParameters(vertical_or_horizontal='yes')
        with pytest.raises(Exception):
            leg_par.vertical_or_horizontal = 'yes'

    def test_base_plane(self):
        """Test the LegendParameter base_plane property."""
        leg_par = LegendParameters(
            base_plane=Plane(Vector3D(0, 0, 0), Point3D(10, 10, 0)))

        assert leg_par.base_plane.o == Point3D(10, 10, 0)
        assert leg_par.is_base_plane_default is False
        leg_par_copy = leg_par.duplicate()
        assert leg_par_copy.base_plane.o == Point3D(10, 10, 0)

        leg_par.base_plane = Plane(Vector3D(0, 0, 0), Point3D(-10, -10, 0))
        assert leg_par.base_plane.o == Point3D(-10, -10, 0)

        with pytest.raises(Exception):
            leg_par = LegendParameters(base_plane=Point3D(-10, -10, 0))
        with pytest.raises(Exception):
            leg_par.base_plane = Point3D(-10, -10, 0)

    def test_segment_height(self):
        """Test the LegendParameter segment_height property."""
        leg_par = LegendParameters(segment_height=3)

        assert leg_par.segment_height == 3
        assert leg_par.is_segment_height_default is False
        leg_par_copy = leg_par.duplicate()
        assert leg_par_copy.segment_height == 3

        leg_par.segment_height = 2
        assert leg_par.segment_height == 2

        with pytest.raises(Exception):
            leg_par = LegendParameters(segment_height=0)
        with pytest.raises(Exception):
            leg_par.segment_height = 0

    def test_segment_width(self):
        """Test the LegendParameter segment_width property."""
        leg_par = LegendParameters(segment_width=3)

        assert leg_par.segment_width == 3
        assert leg_par.is_segment_width_default is False
        leg_par_copy = leg_par.duplicate()
        assert leg_par_copy.segment_width == 3

        leg_par.segment_width = 2
        assert leg_par.segment_width == 2

        with pytest.raises(Exception):
            leg_par = LegendParameters(segment_width=0)
        with pytest.raises(Exception):
            leg_par.segment_width = 0

    def test_text_height(self):
        """Test the LegendParameter text_height property."""
        leg_par = LegendParameters(text_height=0.25)

        assert leg_par.text_height == 0.25
        assert leg_par.is_text_height_default is False
        leg_par_copy = leg_par.duplicate()
        assert leg_par_copy.text_height == 0.25

        leg_par.text_height = 2
        assert leg_par.text_height == 2

        with pytest.raises(Exception):
            leg_par = LegendParameters(text_height=0)
        with pytest.raises(Exception):
            leg_par.text_height = 0

    def test_font(self):
        """Test the LegendParameter font property."""
        leg_par = LegendParameters(font='Times')

        assert leg_par.font == 'Times'
        leg_par_copy = leg_par.duplicate()
        assert leg_par_copy.font == 'Times'

        leg_par.font = 'Courier'
        assert leg_par.font == 'Courier'

        with pytest.raises(Exception):
            leg_par = LegendParameters(font=0)
        with pytest.raises(Exception):
            leg_par.font = 0


class LegendTestCase(unittest.TestCase):
    """Test for Legend"""

    def test_init_legend(self):
        """Test the initialization of Legend objects."""
        legend = Legend([0, 10])
        str(legend)  # Test the Legend representation

        assert len(legend) == 2
        assert legend[0] == 0
        assert legend[1] == 10
        for item in legend:
            assert isinstance(item, (float, int))

        assert len(legend.values) == 2
        assert legend.legend_parameters.min == 0
        assert legend.legend_parameters.max == 10
        assert legend.is_min_default is True
        assert legend.is_max_default is True
        assert legend.legend_parameters.is_number_of_segments_default is True
        assert legend.legend_parameters.is_title_default is True
        assert legend.legend_parameters.is_base_plane_default is True
        assert legend.legend_parameters.is_segment_height_default is True
        assert legend.legend_parameters.is_segment_width_default is True
        assert legend.legend_parameters.is_text_height_default is True

        legend_copy = legend.duplicate()
        assert legend_copy.values == legend.values
        assert legend_copy.legend_parameters.min == legend.legend_parameters.min
        assert legend_copy.legend_parameters.max == legend.legend_parameters.max
        assert legend_copy.legend_parameters.number_of_segments == \
            legend.legend_parameters.number_of_segments
        assert legend_copy.is_min_default is True
        assert legend_copy.is_max_default is True
        assert legend_copy.legend_parameters.is_number_of_segments_default is True
        assert legend_copy.legend_parameters.is_title_default is True
        assert legend_copy.legend_parameters.is_base_plane_default is True
        assert legend_copy.legend_parameters.is_segment_height_default is True
        assert legend_copy.legend_parameters.is_segment_width_default is True
        assert legend_copy.legend_parameters.is_text_height_default is True

    def test_init_legend_with_parameter(self):
        """Test the initialization of Legend with LegendParameter objects."""
        legend = Legend([0, 10], LegendParameters(2, 8))

        assert len(legend.values) == 2
        assert legend.legend_parameters.min == 2
        assert legend.legend_parameters.max == 8
        assert legend.is_min_default is False
        assert legend.is_max_default is False

    def test_to_from_json(self):
        """Test the to/from json methods."""
        legend = Legend([0, 10], LegendParameters(2, 8))
        legend_json = legend.to_json()
        new_legend = Legend.from_json(legend_json)
        assert new_legend.to_json() == legend_json

    def test_value_colors(self):
        """Test the color_range, value_colors, and segment_colors property."""
        legend = Legend(range(5), LegendParameters(number_of_segments=10))

        for i, color in enumerate(legend.color_range):
            assert color == ColorRange()[i]
        assert legend.color_range.domain == ColorRange(domain=(0, 4)).domain

        assert len(legend.values) == 5
        assert len(legend.value_colors) == 5
        assert legend.value_colors[0] == Colorset.original()[0]
        assert legend.segment_colors == Colorset.original()

    def test_title(self):
        """Test the title property."""
        legend = Legend(range(5))
        assert legend.title == ''
        assert legend.legend_parameters.is_title_default is True
        assert legend.title_location.o == Point3D(0, 11.25, 0)

        legend = Legend(range(5), LegendParameters(number_of_segments=5, title='C'))
        assert legend.title == 'C'
        assert legend.legend_parameters.is_title_default is False
        assert legend.title_location.o == Point3D(0, 5.25, 0)

    def test_segment_text(self):
        """Test the segment_text property."""
        legend = Legend(range(10), LegendParameters(number_of_segments=6))

        assert len(legend.segment_text_location) == len(legend.segment_text) == 6
        assert legend.segment_text == ['0.00', '1.80', '3.60', '5.40', '7.20', '9.00']
        for pl in legend.segment_text_location:
            assert isinstance(pl, Plane)
        seg_num = [0, 1.8, 3.6, 5.4, 7.2, 9]
        for i, num in enumerate(legend.segment_numbers):
            assert num == pytest.approx(seg_num[i], rel=1e-3)

        legend = Legend(range(10), LegendParameters(number_of_segments=6,
                                                    vertical_or_horizontal=False))

        assert len(legend.segment_text_location) == len(legend.segment_text) == 6
        assert legend.segment_text == ['0.00', '1.80', '3.60', '5.40', '7.20', '9.00']
        for pl in legend.segment_text_location:
            assert isinstance(pl, Plane)

    def test_segment_text_ordinal_dictionary(self):
        """Test the segment_text property with ordinal dictionary."""
        results = list(range(3000))
        ordinal_dict = {300: 'low', 1150: 'desired', 2000: 'too much'}
        legend = Legend(results, LegendParameters(min=300, max=2000,
                                                  number_of_segments=3,
                                                  ordinal_dictionary=ordinal_dict))

        assert len(legend.segment_text_location) == len(legend.segment_text) == 3
        assert legend.segment_text == ['low', 'desired', 'too much']
        assert len(set(legend.value_colors)) > 100

        legend = Legend(results, LegendParameters(min=300, max=2000,
                                                  number_of_segments=3,
                                                  ordinal_dictionary=ordinal_dict,
                                                  continuous_colors=False))

        assert len(legend.segment_text_location) == len(legend.segment_text) == 3
        assert legend.segment_text == ['low', 'desired', 'too much']
        assert len(set(legend.value_colors)) == 3

    def test_segment_text_ordinal_dictionary2(self):
        """Test the segment_text property with another ordinal dictionary."""
        results = list(range(-4, 5))
        ordinal_dict = PredictedMeanVote().unit_descr
        legend = Legend(results, LegendParameters(min=-3, max=3,
                                                  number_of_segments=7,
                                                  ordinal_dictionary=ordinal_dict))
        assert legend.segment_text == ['Cold', 'Cool', 'Slightly Cool', 'Neutral',
                                       'Slightly Warm', 'Warm', 'Hot']

        legend.legend_parameters.min = -2
        legend.legend_parameters.max = 2
        legend.legend_parameters.number_of_segments = 5
        assert legend.segment_text == ['Cool', 'Slightly Cool', 'Neutral',
                                       'Slightly Warm', 'Warm']

    def test_segment_mesh(self):
        """Test the segment_mesh property."""
        legend = Legend(range(10), LegendParameters(number_of_segments=6))

        assert len(legend.segment_mesh.faces) == 6
        assert len(legend.segment_mesh.vertices) == 14
        legend.legend_parameters.vertical_or_horizontal = False
        assert len(legend.segment_mesh.faces) == 6
        assert len(legend.segment_mesh.vertices) == 14

        legend.legend_parameters.continuous_legend = True
        assert len(legend.segment_mesh.faces) == 5
        assert len(legend.segment_mesh.vertices) == 12
        legend.legend_parameters.vertical_or_horizontal = True
        assert len(legend.segment_mesh.faces) == 5
        assert len(legend.segment_mesh.vertices) == 12


if __name__ == "__main__":
    unittest.main()
