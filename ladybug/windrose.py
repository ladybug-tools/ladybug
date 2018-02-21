"""This file contains classes for the Ladybug windrose"""

from ladybug.epw import EPW


class Windrose(object):
    """Draws the windrose"""

    def __init__(self,
                 epw,
                 HOYs=range(0, 8761)):
        self.epw = EPW(epw)
        self.windDirection = self.epw.wind_direction.values
        self.windSpeed = self.epw.wind_speed.values
        self.HOYs = HOYs

    def showTheObject(self):
        return (self.windDirection, self.windSpeed, self.HOYs)
