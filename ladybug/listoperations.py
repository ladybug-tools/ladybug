"""Useful functions for list operations."""
import collections


def flatten(input_list):
    """Return a flattened genertor from an input list.

    Usage:

        input_list = [['a'], ['b', 'c', 'd'], [['e']], ['f']]
        list(flatten(input_list))
        >> ['a', 'b', 'c', 'd', 'e', 'f']
    """
    for el in input_list:
        if isinstance(el, collections.Iterable) \
                and not isinstance(el, basestring):
            for sub in flatten(el):
                yield sub
        else:
            yield el


def unflatten(guide, falttened_input):
    """Unflatten a falttened generator.

    Args:
        guide: A guide list to follow the structure
        falttened_input: A flattened iterator object

    Usage:

        guide = [["a"], ["b","c","d"], [["e"]], ["f"]]
        input_list = [0, 1, 2, 3, 4, 5, 6, 7]
        unflatten(guide, iter(input_list))
        >> [[0], [1, 2, 3], [[4]], [5]]
    """
    return [unflatten(sub_list, falttened_input) if isinstance(sub_list, list)
            else next(falttened_input) for sub_list in guide]


def duplicate(value, list_length):
    """Take a single value and duplicate it a certain number of times.

    Args:
        value: A value that you want to duplicate
        list_length: The number of times to duplicate the object.

    Usage:

        value = 1.2
        list_length = 5
        duplicate(value, list_length)
        >> [ 1.2, 1.2, 1.2, 1.2, 1.2]
    """
    return [value] * list_length
