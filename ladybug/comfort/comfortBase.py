"""Comfort model object."""
from abc import abstractmethod


class ComfortModel(object):
    """
    Thermal Comfort Model base class.
    """

    def __init__(self):
        self.__calcLength = None
        self.__isDataAligned = False
        self.__isRelacNeeded = True

        self.__headerIncl = False
        self.__headerStr = []
        self.__singleVals = False
