"""Wea weather file."""
from .epw import EPW
from .dt import DateTime

import itertools


class Wea(object):
    """An annual WEA data for a location."""

    def __init__(self, location, directNormalRadiation, diffuseHorizontalRadiation,
                 timestep=1):
        """Create a wea object."""
        assert len(directNormalRadiation) / timestep == \
            len(diffuseHorizontalRadiation) / timestep == 8760, \
            'directNormalRadiation and diffuseHorizontalRadiation data must be annual.'
        self.location = location
        self.directNormalRadiation = directNormalRadiation
        self.diffuseHorizontalRadiation = diffuseHorizontalRadiation
        self.timestep = timestep

    @classmethod
    def fromEpwFile(cls, epwfile):
        """Create a wea object from an epw file."""
        epw = EPW(epwfile)
        return cls(epw.location, tuple(epw.directNormalRadiation),
                   tuple(epw.diffuseHorizontalRadiation))

    @property
    def isWea(self):
        """Return True."""
        return True

    def getRadiationValues(self, month, day, hour):
        """Get direct and diffuse radiation values for a point in time."""
        dt = DateTime(month, day, hour)
        hoy = int(dt.hoy * self.timestep)
        return self.directNormalRadiation[hoy], self.diffuseHorizontalRadiation[hoy]

    def getRadiationValuesForHoy(self, hoy):
        """Get direct and diffuse radiation values for an hoy."""
        hoy = int(hoy * self.timestep)
        return self.directNormalRadiation[hoy], self.diffuseHorizontalRadiation[hoy]

    @property
    def header(self):
        """Wea header."""
        return "place %s\n" % self.location.city + \
            "latitude %.2f\n" % self.location.latitude + \
            "longitude %.2f\n" % -self.location.longitude + \
            "time_zone %d\n" % (-self.location.timezone * 15) + \
            "site_elevation %.1f\n" % self.location.elevation + \
            "weather_data_file_units %d\n" % self.timestep

    def write(self, filePath, hoys=None, writeHours=False):
        """Write the wea file.

        WEA carries radiation values from epw and is what gendaymtx uses to
        generate the sky.
        """
        hoys = hoys or xrange(8760)
        dts = (DateTime.fromHoy(h) for h in hoys)

        with open(filePath, "wb") as weaFile:
            # write header
            weaFile.write(self.header)
            # write values
            for dt, hoy in itertools.izip(dts, hoys):
                dirRad = self.directNormalRadiation[hoy]
                difRad = self.diffuseHorizontalRadiation[hoy]
                line = "%d %d %.3f %d %d\n" \
                    % (dt.month, dt.day, dt.hour + 0.5, dirRad, difRad)

                weaFile.write(line)

        if writeHours:
            with open(filePath[:-4] + '.hrs', 'wb') as outf:
                outf.write(','.join(str(h) for h in hoys) + '\n')

        return filePath

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """epw file representation."""
        return "WEA [%s]" % self.location.city
