"""Methods for drawing windrose geometry."""
import ladybug.geometry as lg
import rhinoscriptsyntax as rs


def windrose(windSpeed, windDirection, annualHourlyData, north=0,
             numOfDirections=16, centerPoint={0.0, 0.0, 0.0},
             scale=1, maxFrequency=100, legendPar=None):
    """This function draws windrose"""

    # checking the scale
    conversionFactor = lg.check_units()
    if scale != 0:
        scale = float(scale) / conversionFactor
    else:
        scale = 1 / conversionFactor

    # Getting the angles for the wind rose as per provided number of directions
    segAngle = 360/numOfDirections
    roseAngles = rs.frange(0, 360, segAngle)
    if round(roseAngles[-1]) == 360:
        roseAngles.remove(roseAngles[-1])

    print "The windrose function ran successfully"
    return (conversionFactor, roseAngles)
