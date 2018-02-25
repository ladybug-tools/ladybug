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
        self.windCondition = windCondition
        self.dataCondition = dataCondition

    def parse_wind_data(self):
        """
        This function outputs filtered wind speed data, wind direction data,
        and annualHourlyData based on
        HOYs,
        conditional statement for the wind data,
        annual hourly data,
        and,
        conditional statement for the annual hourly data
        Args:
            The inistance of the WindRose object
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

        if self.windCondition is None \
            and self.annualHourlyData is None \
                and self.dataCondition is None:
                print "Conditional statement for wind data is missing"
                print "Annual hourly data is missing"
                print "Conditional statement for annual hourly data is missing"
                wsOut, wdOut, annualHourlyData = (
                    windSpeed,
                    windDirection,
                    self.annualHourlyData
                )
                return (wsOut, wdOut, annualHourlyData)

        elif self.windCondition is None \
            and self.annualHourlyData is not None \
                and self.dataCondition is None:
                print "Conditional statement for wind data is missing"
                print "Annual hourly data is recognized"
                print "Conditional statement for annual hourly data is missing"
                wsOut, wdOut, annualHourlyData = (
                    windSpeed,
                    windDirection,
                    self.annualHourlyData.filter_by_hoys(self.HOYs)
                )
                return (wsOut, wdOut, annualHourlyData)

        elif self.windCondition is not None \
            and self.annualHourlyData is None \
                and self.dataCondition is None:
                print "Conditional statement for wind data is recognized"
                print "Annual hourly data is missing"
                print "Conditional statement for annual hourly data is missing"
                HOYs = windSpeed.data_to_HOY(self.windCondition)
                wsOut, wdOut, annualHourlyData = (
                    windSpeed.filter_by_hoys(HOYs),
                    windDirection.filter_by_hoys(HOYs),
                    self.annualHourlyData
                )
                return (wsOut, wdOut, annualHourlyData)

        elif self.windCondition is not None \
            and self.annualHourlyData is not None \
                and self.dataCondition is None:
                print "Conditional statement for wind data is recognized"
                print "Annual hourly data is recognized"
                print "Conditional statement for annual hourly data is missing"
                HOYs = windSpeed.data_to_HOY(self.windCondition)
                wsOut, wdOut, annualHourlyData = (
                    windSpeed.filter_by_hoys(HOYs),
                    windDirection.filter_by_hoys(HOYs),
                    self.annualHourlyData.filter_by_hoys(HOYs)
                )
                return (wsOut, wdOut, annualHourlyData)

        elif self.windCondition is not None \
            and self.annualHourlyData is not None \
                and self.dataCondition is not None:
                print "Conditional statement for wind data is recognized"
                print "Annual hourly data is recognized"
                print ("Conditional statement for annual hourly data" +
                       "is recognized")
                HOYwindCond = windSpeed.data_to_HOY(self.windCondition)
                HOYdataCond = self.annualHourlyData.data_to_HOY(
                    self.dataCondition
                )
                HOYs = set(HOYwindCond).intersection(HOYdataCond)
                wsOut, wdOut, annualHourlyData = (
                    windSpeed.filter_by_hoys(HOYs),
                    windDirection.filter_by_hoys(HOYs),
                    self.annualHourlyData.filter_by_hoys(HOYs))
                return (wsOut, wdOut, annualHourlyData)

        else:
            return ("Something went wrong. Ladybug failed to parse the data" +
                    "with the provided inputs")
