# coding=utf-8
"""Utilities for finding roots of continuous functions."""
from __future__ import division


def secant(a, b, fn, epsilon):
    """Solve for a root using one of the fastest root-finding algorithms.

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

            .. code-block:: python

                def fn(value_trying_to_find):
                    funct(value_trying_to_find) - target_desired_from_funct

            ...but the subtraction should be switched if value_trying_to_find
            has a negative relationship with the funct.
        epsilon: The acceptable error in the target_desired_from_funct.

    Returns:
        root -- The value that gives the target_desired_from_funct in the sample
        above (aka. the value that returns 0 from the fn).

    References
    ----------
    [1] Wikipedia contributors. (2018, December 29). Root-finding algorithm.
    In Wikipedia, The Free Encyclopedia. Retrieved 18:16, December 30, 2018,
    from https://en.wikipedia.org/wiki/Root-finding_algorithm#Secant_method
    """
    f1 = fn(a)
    if abs(f1) <= epsilon:
        return a
    f2 = fn(b)
    if abs(f2) <= epsilon:
        return b
    for _ in range(100):
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


def bisect(a, b, fn, epsilon, target=0):
    """Solve for a root using the simplest root-finding algorithm.

    It is extremely reliable. However, it converges slowly for this reason,
    it is recommended that this only be used after the secant() method has
    returned None.

    Args:
        a: A lower guess of the value you are tying to find.
        b: A higher guess of the value you are tying to find.
        fn: A function representing the relationship between the value you are
            trying to find and the target condition you are trying to satisfy.
            It should typically be structured in the following way:

            .. code-block:: python

                def fn(value_trying_to_find):
                    funct(value_trying_to_find) - target_desired_from_funct

            ...but the subtraction should be switched if value_trying_to_find
            has a negative relationship with the funct.
        epsilon: The acceptable error in the target_desired_from_funct.
        target: The target slope (typically 0 for a local minima or maxima).

    Returns:
        root -- The value that gives the target_desired_from_funct.

    References
    ----------
    [1] Wikipedia contributors. (2018, December 29). Root-finding algorithm.
    In Wikipedia, The Free Encyclopedia. Retrieved 18:16, December 30, 2018,
    from https://en.wikipedia.org/wiki/Root-finding_algorithm#Bisection_method
    """
    max_e = 2 * epsilon
    while (abs(b - a) > max_e):
        midpoint = (b + a) / 2
        a_t = fn(a)
        b_t = fn(b)
        midpoint_t = fn(midpoint)
        if (a_t - target) * (midpoint_t - target) < 0:
            b = midpoint
        elif (b_t - target) * (midpoint_t - target) < 0:
            a = midpoint
        else:
            return midpoint
    return midpoint


def secant_three_var(a, b, fn, epsilon, other_args):
    """Solve the roots of a 3-variable function with one of the fastest algorithms.

    Args:
        a: A tuple with 3 numbers for the the lowest boundary of the roots.
        b: A tuple with 3 numbers for the the highest boundary of the roots.
        fn: A function for which roots are to be solved. That is, where the output
            of the function is a tuple of three zeros.
        epsilon: The acceptable error in the resulting root.
        other_args: Other input arguments for the fn other than the ones being
            adjusted to solve the root.

    Returns:
        root -- a tuple of 3 values that return a vector of zeros from the fn.
    """
    args_1 = (a,) + other_args
    f1 = fn(*args_1)
    if all(abs(v) <= epsilon for v in f1):
        return a
    args_2 = (b,) + other_args
    f2 = fn(*args_2)
    if all(abs(v) <= epsilon for v in f2):
        return b

    for _ in range(1000):
        try:
            slope = tuple((v2 - v1) / (bv - av) for v1, v2, av, bv in zip(f1, f2, a, b))
        except ZeroDivisionError:
            return None  # failed to converge
        try:
            c = tuple(bv - v2 / s for bv, v2, s in zip(b, f2, slope))
        except ZeroDivisionError:  # zero slope was found
            return None  # failed to converge
        args_3 = (c,) + other_args
        f3 = fn(*args_3)
        if all(abs(v) <= epsilon for v in f3):
            return c
        a = b
        b = c
        f1 = f2
        f2 = f3

    return None
