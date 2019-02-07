# coding=utf-8
"""Module for computing thermal comfort.

Properties:
    SOLARCALSPLINES: A dictionary with two keys: 'standing' and 'seated'.
        Each value for these keys is a 2D matrix of projection factors
        for human geometry.  Each row refers to an degree of azimuth and each
        colum refers to a degree of altitude.
"""

from ._loadmannequin import load_solarcal_splines

SOLARCALSPLINES = load_solarcal_splines()
