# coding=utf-8
"""Load data that accounts for human geometry.

This includes mannequin geometry and solarcal splines.
"""

from ..futil import csv_to_num_matrix

from os.path import dirname, abspath
import inspect


def load_solarcal_splines():
    try:
        cur_dir = dirname(abspath(inspect.getfile(inspect.currentframe())))
        solarcal_splines = {
            'seated': csv_to_num_matrix(cur_dir + '/mannequindata/seatedspline.csv'),
            'standing': csv_to_num_matrix(cur_dir + '/mannequindata/standingspline.csv')}
    except IOError:
        solarcal_splines = {}
        print ('Failed to import projection factor splines from CSV.'
               '\nA simpler interoplation method for Solarcal will be used.')
    return solarcal_splines
