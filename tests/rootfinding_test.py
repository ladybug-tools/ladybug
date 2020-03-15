# coding=utf-8
from ladybug.rootfinding import secant, bisect


def test_secant():
    """Test the secant rootfinding method."""
    def funct(x):
        return (x + 1) ** 2 - 1
    
    root_val = secant(-5, 5, funct, 0.001)
    assert root_val < 1e-3


def test_bisect():
    """Test the bisect rootfinding method."""
    def funct(x):
        return (x + 1) ** 2 - 1
    
    root_val = bisect(-5, 5, funct, 0.001, 0)
    assert root_val < 1e-3
