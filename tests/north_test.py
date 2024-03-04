# coding=utf-8
from __future__ import division

import pytest
import datetime

from ladybug.north import WorldMagneticModel


def test_world_magnetic_model_defaults():
    """Test the defaults of the WorldMagneticModel."""
    wmm_obj = WorldMagneticModel()
    dec_val = wmm_obj.magnetic_declination(80, 0, 0, 2015)

    assert dec_val == pytest.approx(-3.7947, rel=1e-2)


def test_world_magnetic_model_results():
    """Test that the WorldMagneticModel returns correct results."""
    d1 = datetime.date(2015, 1, 1)
    d2 = datetime.date(2017, 7, 2)
    y1 = d1.year + ((d1 - datetime.date(d1.year, 1, 1)).days / 365.0)
    y2 = d2.year + ((d2 - datetime.date(d2.year, 1, 1)).days / 365.0)

    test_values = (
        # date, alt, lat, lon, var
        (y1, 0, 80, 0, -3.85),
        (y1, 0, 0, 120, 0.57),
        (y1, 0, -80, 240,  69.81),
        (y1, 100000.0, 80, 0, -4.27),
        (y1, 100000.0, 0, 120, 0.56),
        (y1, 100000.0, -80, 240, 69.22),
        (y2, 0, 80, 0, -2.75),
        (y2, 0, 0, 120, 0.32),
        (y2, 0, -80, 240, 69.58),
        (y2, 100000.0, 80, 0, -3.17),
        (y2, 100000.0, 0, 120, 0.32),
        (y2, 100000.0, -80, 240, 69.00),
    )

    wmm_2015 = './tests/assets/txt/WMM.COF'
    wmm_obj = WorldMagneticModel(wmm_2015)

    for values in test_values:
        dec_val = wmm_obj.magnetic_declination(
            values[2], values[3], values[1], values[0])
        assert dec_val == pytest.approx(values[4], rel=1e-2)
