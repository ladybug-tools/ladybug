
class DataPoint(object):
    """ A Ladybug data point

        Attributes:
            value :<flot>, <integer>, <string> based on type
            isEpwData: A boolean that indicates if the data is from an epw
                file. Valid range for epw file can be differnt. For example
                Temperature range in an ewp file is -70 C - 70 C (Default: False)
            standard: class of SI or IP. (Default is SI)
    """

    def __init__(self, value, isEpwData = False, standard = None):
        if not standard: standard = SI
        self.value = value
        self.standard = standard
        self.isEpwData = isEpwData

        self.__typeErrorMsg = "%s is not a valid input type. " + \
            "Input should be from %s"
        self.__valueErrorMsg = "%s is not a valid input type. " + \
            "Input should be between %s and %s"
        self.__standardErrorMsg = "%s is not a valid standard type. " + \
            "Valid standards are SI and IP"

        #check validity of input
        self.isValid(raiseException = True)

    def isValid(self, raiseException = False):
        """Check validity of input"""
        if not(self.standard is IP or self.standard is SI):
            raise Exception(self.__standardErrorMsg%self.standard)

        if self.valueType:
            try:
                self.value = map(self.valueType, [self.value])[0]
            except:
                if raiseException:
                    raise TypeError(self.__typeErrorMsg%(self.value, self.valueType))
                return False #not a valid standard

        #check if the valus is in range
        if self.valueType is str: return True # if not a number return True

        isValid = self.__isInRange
        if not isValid and raiseException:
            raise ValueError(self.__valueErrorMsg%(self.value, self.minimum, self.maximum))
        else:
            return isValid

    @property
    def __isInRange(self):
        """Retuen True is value is in range"""
        return self.minimum <= self.value <= self.maximum

    def get_valueBasedOnCurrentStandard(self, value, valueStandard):
        """Return the value based on the current standard IP/SI

            This method makes it possible to set minimum and maximum values
            with a single number in SI or IP
        """
        if valueStandard is self.standard:
            return value # the standard is the same so return the same value
        elif self.standard is SI:
            #The value is in IP and should be converted to SI
            return self.get_valueInSI(value)
        elif self.standard is IP:
            #The value is in SI and should be converted to IP
            return self.get_valueInIP(value)

    def convertToIP(self):
        """Change to IP system

            Warning: convertToIP only and only changes this value to IP
        """
        if self.standard is IP: return True
        # If it's in SI change system and value
        self.standard = IP
        self.value = self.get_valueBasedOnCurrentStandard(self.value, SI)
        return True

    def convertToSI(self):
        """Change to SI system

            Warning: convertToSI only and only changes this value to SI
        """
        if self.standard is SI: return True
        # If it's in IP change system and value
        self.standard = SI
        self.value = self.get_valueBasedOnCurrentStandard(self.value, IP)
        return True

    def unit(self):
        raise NotImplementedError

    def valueType(self):
        raise NotImplementedError

    def minimum(self):
        raise NotImplementedError

    def maximum(self):
        raise NotImplementedError

    def __repr__(self):
        return str(self.value)

class GenericData(DataPoint):
    """Generic Data Point

        Attributes:
            value :<flot>, <integer>, <string> based on type
            isEpwData: A boolean that indicates if the data is from an epw
                file. Valid range for epw file can be differnt. For example
                Temperature range in an ewp file is -70 C - 70 C (Default: False)
            standard: SI or IP. (Default is SI)
            def __init__(self, value, isEpwData = False, standard= None):
                DataPoint.__init__(self, value, isEpwData, standard)
                #check validity of input
                self.isValid(valueType = self.valueType, raiseException = True)
    """
    def __init__(self, value, isEpwData = False, standard= None):
        DataPoint.__init__(self, value, isEpwData, standard)

    @property
    def unit(self):
        return ""

    @property
    def valueType(self):
        return str

    @property
    def minimum(self):
        """Return minimum valid value"""
        return float("-inf")

    @property
    def maximum(self):
        return float("inf")

    @staticmethod
    def get_valueInIP(value):
        """return the value in IP assuming input value is in SI"""
        return value

    @staticmethod
    def get_valueInSI(value):
        """return the value in SI assuming input value is in IP"""
        return value

class Temperature(DataPoint):
    """Base type for temperature"""

    def __init__(self, value, isEpwData = False, standard= None):
        DataPoint.__init__(self, value, isEpwData, standard)

    @property
    def unit(self):
        if self.standard is SI: return "C"
        elif self.standard is IP: return "F"

    @property
    def valueType(self):
        return float

    @property
    def minimum(self):
        """Return minimum valid value"""
        if self.isEpwData:
            return self.get_valueBasedOnCurrentStandard(-70, SI)
        else:
            return float("-inf")

    @property
    def maximum(self):
        """Return maximum valid value"""
        if self.isEpwData:
            return self.get_valueBasedOnCurrentStandard(70, SI)
        else:
            return float("inf")

    @staticmethod
    def get_valueInIP(value):
        """return the value in F assuming input value is in C"""
        return value * 9 / 5 + 32

    @staticmethod
    def get_valueInSI(value):
        """return the value in C assuming input value is in F"""
        return (value - 32) * 5 / 9

class RelativeHumidity(DataPoint):
    """Base type for Relative Humidity"""

    def __init__(self, value, isEpwData = False, standard= None):
        DataPoint.__init__(self, value, isEpwData, standard)

    @property
    def unit(self):
        return "%"

    @property
    def valueType(self):
        return float

    @property
    def minimum(self):
        """Return minimum valid value"""
        return 0

    @property
    def maximum(self):
        """Return maximum valid value"""
        return 100

    @staticmethod
    def get_valueInIP(value):
        """return the value in IP assuming input value is in SI"""
        return value

    @staticmethod
    def get_valueInSI(value):
        """return the value in SI assuming input value is in IP"""
        return value

class SI(object):
    def __repr__():
        return "SI"

class IP(object):
    def __repr__():
        return "IP"
