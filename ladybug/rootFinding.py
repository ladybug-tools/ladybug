"""
A list of very useful functions for rapid guess-and-test (or root-finding) situations.
Using these functions will typically be much faster than a custom-built guess-and-check with a while() loop.


For more information on these functions, see the wikidepia page on root finding:
https://en.wikipedia.org/wiki/Root-finding_algorithm
"""


def secant(a, b, fn, epsilon):
    """
     One of the fasest root-finding algorithms.
     The method calculates a finite difference slope of the function fn and this enables it to converge to a solution very fast.
     However, if started too far away from a root, the method may not converge (returning a 'Nan').
     For this reason, it is recommended that this function be used first and, if it fails to find a root, the bisect() method should be used.
    """
    f1 = fn(a)
    if abs(f1) <= epsilon:
        return a
    f2 = fn(b)
    if abs(f2) <= epsilon:
        return b
    for i in range(100):
        slope = (f2 - f1) / (b - a)
        c = b - f2 / slope
        f3 = fn(c)
        if abs(f3) < epsilon:
            return c
        a = b
        b = c
        f1 = f2
        f2 = f3

    return 'NaN'


def bisect(a, b, fn, epsilon, target):
    """
    The simplest root-finding algorithm.
    It is extremely reliable and is gauranteed to converge to a solution as long as a solution exists.
    However, it converges slowly and, for this reason, it is recommended that this only be used
    after the secant() method has returned a 'NaN'.
    """
    while (abs(b - a) > 2 * epsilon):
        midpoint = (b + a) / 2
        a_T = fn(a)
        b_T = fn(b)
        midpoint_T = fn(midpoint)
        if (a_T - target) * (midpoint_T - target) < 0:
            b = midpoint
        elif (b_T - target) * (midpoint_T - target) < 0:
            a = midpoint
        else:
            return -999

    return midpoint
