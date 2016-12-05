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

    def _checkInputList(self, inputValue, defaultValue, inputValName, headerValName):
        """
        Check length of the inputValue list and evaluate the contents.
        """
        checkData = False
        finalVals = []
        multVal = False
        if len(inputValue) != 0:
            try:
                if headerValName in inputValue[2]:
                    finalVals = inputValue[7:]
                    checkData = True
                    self.__headerIncl = True
                    self.__headerStr = inputValue[0:7]
            except:
                pass
            if checkData is False:
                for item in inputValue:
                    try:
                        finalVals.append(float(item))
                        checkData = True
                    except:
                        checkData = False
            if len(finalVals) > 1:
                multVal = True
            if checkData is False:
                raise Exception(inputValName + " input is not of a valid input type.")
        else:
            checkData = True
            finalVals = defaultValue
            if len(finalVals) > 1:
                multVal = True

        return checkData, finalVals, multVal

    def buildCustomHeader(self, headerName, headerUnits):
        """
        Builds a customized header for a certain data type given the header on the inputs.
        """
        newHeadStr = self.__headerStr
        newHeadStr[2] = headerName
        newHeadStr[3] = headerUnits
        return newHeadStr
