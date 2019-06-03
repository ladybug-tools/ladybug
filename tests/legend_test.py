# coding=utf-8
from __future__ import division

from ladybug.legend import Legend, LegendParameters
from ladybug.color import Color

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


if __name__ == "__main__":
    unittest.main()
