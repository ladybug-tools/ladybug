class Wrapper():
    """A Wrapper class to overwrite object __clrtype__ in Ladybug objects.

        Wrapper makes the outputs to be human readable and doesn't have any
        technical value.

        Attributes:
            data: The class to be wrapped. check __repr__ method of class to
                be set to a human readable string

        Usage:
            # wrap legend parameters class
            OUT = wrapper(legendpar.LegendParameters())

            # unwarp a wrapped legend parameter
            lp = IN[0].unwarp()
    """
    def __init__(self, data):
        self.__data = data

    def unwrap(self):
        return self.__data

    def __repr__(self):
        return self.__data.__repr__()

class A(object):
    def __repr__(self):
        return "hurray"

a = A()
b = Wrapper(a)

print isinstance(b, Wrapper)
