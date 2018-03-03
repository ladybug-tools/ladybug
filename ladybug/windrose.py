"""Ladybug windrose"""
from ladybug.epw import EPW


class WindRose(object):
    """
    Draws the Ladybug windrose
    Usage:
    """
    __slots__ = ("epw", "HOYs", "annualHourlyData",
                 "windCondition", "dataCondition",
                 "numOfDirections", "centerPoint",
                 "scale", "maxFrequency")

    def __init__(self,
                 epw_filePath,
                 HOYs=range(0, 8761),
                 annualHourlyData=None,
                 windCondition=None,
                 dataCondition=None,
                 ):
        """
        Instantiates the Ladybug WindRose Object
        """
        self.epw = EPW(epw_filePath)
        self.HOYs = HOYs
        self.annualHourlyData = annualHourlyData
        self.windCondition = self.check_condition(windCondition)
        self.dataCondition = self.check_condition(dataCondition)

    @staticmethod
    def check_condition(condition):
        """
        Checks whether the conditional statement has
        the variable 'x'
        Args:
            condition: A list of conditional statements
        Returns:
            None: if condition is None or the variable 'x' is not \
            in the conditional statement
            condition: The same list of conditional statements provided
            as arguments to the function

        """
        if condition is None:
            return None
        if isinstance(condition, str):
            if "x" in condition.lower():
                return condition
            else:
                print ("The conditon shall be a valid string with" +
                       " a variable 'x' in it.")
        else:
            xcount = 0
            for statement in condition:
                if "x" in statement.lower():
                    xcount += 1
            if len(condition) == xcount:
                return condition
            else:
                print ("All conditions shall be a valid string with" +
                       "a variable 'x' in it.")
                return None

    def data_to_HOY(self):
        """
        This function takes the list of annual hourly data
        and the list of data conditions. By taking them into consideration
        this function creates a list of HOYs that can be used to
        craft the wind data
        Args:
            The instance of the WindRose Object
        Returns:
            A sorted list of common HOYs as per provided
            annualHourlyData and the dataCondition. It is
            the list of HOYs that pass all the dataConditions
            provided.
        """
        if not len(self.annualHourlyData) == len(self.dataCondition):
            print ("Then number of condtional statements don't match" +
                   " the number of annualHourlyData provided." +
                   " Therefore, conditional statements are ignored")
            return None
        else:
            # The following is a list of lists
            # It catches HOYs for all the annualHourlyData
            # dataCondition pairs
            HOYList = []
            for i in range(len(self.annualHourlyData)):
                HOYList.append(
                    self.annualHourlyData[i].data_to_HOY(
                        self.dataCondition[i]))
            HOYSets = [set(listItem) for listItem in HOYList]
            HOYCommon = set.intersection(*HOYSets)
            return sorted(HOYCommon)

    def parse_wind_data(self):
        """
        This function filters the wind speed and the wind direction
        data based on the provided hours of the year, annual hourly data,
        conditional statement for the wind, and the conditional statement
        for the annual hourly data.
        Args:
            A Ladybug WindRose isinstance
        Returns:
            wsOut : A Ladybug DataCollection object of filtered \
                wind speed data.
            wdOut : A Ladybug DataCollection object of filtered \
                wind direction data
            annualHourlyData : A Ladybug DataCollection object of filtered \
                annualHourlyData
        """

        # Getting the full wind data from the weather file
        windSpeed = self.epw.wind_speed.filter_by_hoys(self.HOYs)
        windDirection = self.epw.wind_direction.filter_by_hoys(self.HOYs)

        # Getting the first list of HOYs
        if self.windCondition is None:
            HOYsWind = None
        else:
            HOYsWind = windSpeed.data_to_HOY(self.windCondition)

        # Getting the second list of HOYs
        if self.dataCondition is None or self.annualHourlyData is None:
            HOYsData = None
        else:
            HOYsData = self.data_to_HOY()

        # Getting the third list of HOYs
        HOYs = self.HOYs

        # HOYsList is a list of list that collects all the three
        # HOY lists as mentioned above
        # If any of the list is not present and the value is None
        # instead, then it is removed before taking intersection of
        # the lists for a list of common HOYs
        HOYsList = [item for item in [HOYs, HOYsWind, HOYsData]
                    if item is not None]
        HOYsSets = [set(listItem) for listItem in HOYsList]
        HOYsCommon = set.intersection(*HOYsSets)
        HOYs = sorted(HOYsCommon)

        wsOut, wdOut = (
            windSpeed.filter_by_hoys(HOYs),
            windDirection.filter_by_hoys(HOYs))

        if self.annualHourlyData is not None:
            annualHourlyData = [item.filter_by_hoys(HOYs)
                                for item in self.annualHourlyData]
        else:
            annualHourlyData = self.annualHourlyData

        return (wsOut, wdOut, annualHourlyData)
