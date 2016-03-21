"""A list of useful functions for fast guess-and-test iteration"""

import math

# This function is taken from the util.js script of the CBE comfort tool page.
def bisect(a, b, fn, epsilon, target):

    while (math.abs(b - a) > 2 * epsilon):
        midpoint = (b + a) / 2
        a_T = fn(a)
        b_T = fn(b)
        midpoint_T = fn(midpoint)
        if (a_T - target) * (midpoint_T - target) < 0: b = midpoint
        elif (b_T - target) * (midpoint_T - target) < 0: a = midpoint
        else: return -999

    return midpoint

# This function is taken from the util.js script of the CBE comfort tool page.
def secant(a, b, fn, epsilon):
    # root-finding only
    f1 = fn(a)
    if math.abs(f1) <= epsilon: return a
    f2 = fn(b)
    if math.abs(f2) <= epsilon: return b
    for i in range(100):
        slope = (f2 - f1) / (b - a)
        c = b - f2 / slope
        f3 = fn(c)
        if math.abs(f3) < epsilon: return c
        a = b
        b = c
        f1 = f2
        f2 = f3

    return 'NaN'
