"""Wea weather file."""
from .epw import EPW
from .dt import DateTime

import itertools


class Wea(object):
    """An annual WEA data for a location."""

    def __init__(self, location, direct_normal_radiation, diffuse_horizontal_radiation,
                 timestep=1):
        """Create a wea object."""
        assert len(direct_normal_radiation) / timestep == \
            len(diffuse_horizontal_radiation) / timestep == 8760, \
            'direct_normal_radiation and diffuse_horizontal_radiation data must be ' \
            'annual.'
        self.location = location
        self.direct_normal_radiation = direct_normal_radiation
        self.diffuse_horizontal_radiation = diffuse_horizontal_radiation
        self.timestep = timestep

    @classmethod
    def from_epw_file(cls, epwfile):
        """Create a wea object from an epw file.

        Args:
            epwfile: Full path to epw weather file.
        """
        epw = EPW(epwfile)
        return cls(epw.location, tuple(epw.direct_normal_radiation),
                   tuple(epw.diffuse_horizontal_radiation))

    @property
    def isWea(self):
        """Return True."""
        return True

    def get_radiation_values(self, month, day, hour):
        """Get direct and diffuse radiation values for a point in time."""
        dt = DateTime(month, day, hour)
        hoy = int(dt.hoy * self.timestep)
        return self.direct_normal_radiation[hoy], self.diffuse_horizontal_radiation[hoy]

    def get_radiation_values_for_hoy(self, hoy):
        """Get direct and diffuse radiation values for an hoy."""
        hoy = int(hoy * self.timestep)
        return self.direct_normal_radiation[hoy], self.diffuse_horizontal_radiation[hoy]

    @property
    def header(self):
        """Wea header."""
        return "place %s\n" % self.location.city + \
            "latitude %.2f\n" % self.location.latitude + \
            "longitude %.2f\n" % -self.location.longitude + \
            "time_zone %d\n" % (-self.location.time_zone * 15) + \
            "site_elevation %.1f\n" % self.location.elevation + \
            "weather_data_file_units %d\n" % self.timestep

    def write(self, file_path, hoys=None, write_hours=False):
        """Write the wea file.

        WEA carries radiation values from epw and is what gendaymtx uses to
        generate the sky.
        """
        hoys = hoys or xrange(8760)
        dts = (DateTime.from_hoy(h) for h in hoys)

        with open(file_path, "wb") as weaFile:
            # write header
            weaFile.write(self.header)
            # write values
            for dt, hoy in itertools.izip(dts, hoys):
                dir_rad = self.direct_normal_radiation[hoy]
                dif_rad = self.diffuse_horizontal_radiation[hoy]
                line = "%d %d %.3f %d %d\n" \
                    % (dt.month, dt.day, dt.hour + 0.5, dir_rad, dif_rad)

                weaFile.write(line)

        if write_hours:
            with open(file_path[:-4] + '.hrs', 'wb') as outf:
                outf.write(','.join(str(h) for h in hoys) + '\n')

        return file_path

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """epw file representation."""
        return "WEA [%s]" % self.location.city
