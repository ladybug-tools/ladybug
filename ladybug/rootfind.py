# coding=utf-8
"""
A list of useful functions for rapid guess-and-test (or root-finding) situations.

For more information on these functions, see the wikidepia page on root finding:
https://en.wikipedia.org/wiki/Root-finding_algorithm
"""
from __future__ import division


def secant(a, b, fn, epsilon):
    """
     One of the fasest root-finding algorithms.
     The method calculates the slope of the function fn and this enables it to converge
     to a solution very fast. However, if started too far away from a root, the method
     may not converge (returning a None). For this reason, it is recommended that this
     function be used first in any guess-and-check workflow and, if it fails to find a
     root, the bisect() method should be used.

     Args:
        a: The lowest possible boundary of the value you are tying to find.
        b: The highest possible boundary of the value you are tying to find.
        fn: A function representing the relationship between the value you are
            trying to find and the target condition you are trying to satisfy.
            It should typically be structured in the following way:
            `def fn(value_trying_to_find):
                funct(value_trying_to_find) - target_desired_from_funct`
            ...but the subtraction should be swtiched if value_trying_to_find
            has a negative relationship with the funct.
        epsilon: The acceptable error in the target_desired_from_funct.

    Returns:
        root: The value that gives the target_desired_from_funct.

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

    return None


def bisect(a, b, fn, epsilon, target):
    """
    The simplest root-finding algorithm.

    It is extremely reliable. However, it converges slowly for this reason,
    it is recommended that this only be used after the secant() method has
    returned None.

    Args:
        a: A lower guess of the value you are tying to find.
        b: A higher guess of the value you are tying to find.
        fn: A function representing the relationship between the value you are
            trying to find and the target condition you are trying to satisfy.
            It should typically be structured in the following way:
            `def fn(value_trying_to_find):
                funct(value_trying_to_find) - target_desired_from_funct`
            ...but the subtraction should be swtiched if value_trying_to_find
            has a negative relationship with the funct.
        epsilon: The acceptable error in the target_desired_from_funct.
        target: The target slope (typically 0 for a local minima or maxima).

    Returns:
        root: The value that gives the target_desired_from_funct.

    """
    while (abs(b - a) > 2 * epsilon):
        midpoint = (b + a) / 2
        a_t = fn(a)
        b_t = fn(b)
        midpoint_t = fn(midpoint)
        if (a_t - target) * (midpoint_t - target) < 0:
            b = midpoint
        elif (b_t - target) * (midpoint_t - target) < 0:
            a = midpoint
        else:
            return -999

    return midpoint
