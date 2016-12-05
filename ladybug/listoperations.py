"""Useful functions for list operations."""
import collections


def flatten(inputList):
    """Return a flattened genertor from an input list.

    Usage:

        inputList = [['a'], ['b', 'c', 'd'], [['e']], ['f']]
        list(flatten(inputList))
        >> ['a', 'b', 'c', 'd', 'e', 'f']
    """
    for el in inputList:
        if isinstance(el, collections.Iterable) \
                and not isinstance(el, basestring):
            for sub in flatten(el):
                yield sub
        else:
                yield el


def unflatten(guide, falttenedInput):
    """Unflatten a falttened generator.

    Args:
        guide: A guide list to follow the structure
        falttenedInput: A flattened iterator object

    Usage:

        guide = [["a"], ["b","c","d"], [["e"]], ["f"]]
        inputList = [0, 1, 2, 3, 4, 5, 6, 7]
        unflatten(guide, iter(inputList))
        >> [[0], [1, 2, 3], [[4]], [5]]
    """
    return [unflatten(subList, falttenedInput) if isinstance(subList, list)
            else next(falttenedInput) for subList in guide]


def duplicate(value, listLength):
    """Take a single value and duplicate it a certain number of times.

    Args:
        value: A value that you want to duplicate
        listLength: The number of times to duplicate the object.

    Usage:

        value = 1.2
        listLength = 5
        duplicate(value, listLength)
        >> [ 1.2, 1.2, 1.2, 1.2, 1.2]
    """
    return [value] * listLength
