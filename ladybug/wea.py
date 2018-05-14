"""Wea weather file."""
from .epw import EPW
from .dt import DateTime
from .location import Location
from .datacollection import DataCollection
from .stat import STAT
from .sunpath import Sunpath

import itertools
import math

class Wea(object):
    """An annual WEA data for a location."""

    def __init__(self, location, direct_normal_radiation, diffuse_horizontal_radiation,
                 timestep=1):
        """Create a wea object."""
        timestep = timestep or 1
        assert len(direct_normal_radiation) / timestep == \
            len(diffuse_horizontal_radiation) / timestep == 8760, \
            'direct_normal_radiation and diffuse_horizontal_radiation data must be ' \
            'annual.'
        self.location = location
        self.direct_normal_radiation = direct_normal_radiation
        self.diffuse_horizontal_radiation = diffuse_horizontal_radiation
        self.timestep = timestep

    @classmethod
    def from_json(cls, data):
        """ Create Wea from json file
            {
            "location": {} , // ladybug location schema
            "direct_normal_radiation": [], // List of hourly direct normal
                radiation data points
            "diffuse_horizontal_radiation": [], // List of hourly diffuse
                horizontal radiation data points
            "timestep": float //timestep between measurements, default is 1
            }
        """
        required_keys = ('location', 'direct_normal_radiation',
                         'diffuse_horizontal_radiation')
        optional_keys = ('timestep',)

        for key in required_keys:
            assert key in data, 'Required key "{}" is missing!'.format(key)

        for key in optional_keys:
            if key not in data:
                data[key] = None

        location = Location.from_json(data['location'])
        direct_normal_radiation = \
            DataCollection.from_json(data['direct_normal_radiation'])
        diffuse_horizontal_radiation = \
            DataCollection.from_json(data['diffuse_horizontal_radiation'])
        timestep = data['timestep']

        return cls(location, direct_normal_radiation, diffuse_horizontal_radiation,
                   timestep)

    @classmethod
    def from_epw_file(cls, epwfile):
        """Create a wea object from an epw file.

        Args:
            epwfile: Full path to epw weather file.
        """
        epw = EPW(epwfile)
        return cls(epw.location,
                   epw.direct_normal_radiation,
                   epw.diffuse_horizontal_radiation)

    @classmethod
    def from_stat_file(cls, statfile, timestep=1):
        """Create a wea object from a .stat file.

        This wea object represents an ASHRAE Revised Clear Sky ("Tau Model"), which
        is intended to determine peak solar load and sizing parmeters for HVAC systems.
        The "Tau Model" uses monthly optical depths found within a .stat file.

        Args:
            statfile: Full path to the .stat file.
            timestep: An optional integer to set the number of time steps per hour.
                Default is 1 for one value per hour.
        """
        stat = STAT(statfile)

        sp = Sunpath.from_location(stat.location)

        altitudes = []
        months = []
        for h in range(8760*timestep):
            sun = sp.calculate_sun_from_hoy(h/timestep)
            months.append(sun.datetime.month-1)
            altitudes.append(sun.altitude)

        # Calculate the hourly air mass between the sun at the top of the atmosphere and the surface of the earth.
        airMasses = []
        for alt in altitudes:
            airMass = 0
            if alt > 0:
                airMass = 1/(math.sin(math.radians(alt)) + (0.50572 * math.pow((6.07995 + alt), -1.6364)))
            airMasses.append(airMass)

        # Calculate monthly air mass exponents.
        beamEpxs = []
        diffuseExps = []
        for count, tb in enumerate(stat.monthly_tau_beam):
            td = stat.monthly_tau_diffuse[count]
            ab = 1.219 - (0.043*tb) - (0.151*td) - (0.204*tb*td)
            ad = 0.202 + (0.852*tb) - (0.007*td) - (0.357*tb*td)
            beamEpxs.append(ab)
            diffuseExps.append(ad)

        # compute the clear sky radiation values
        directNormRad, diffuseHorizRad = [], []
        for i, airMass in enumerate(airMasses):
            alt = altitudes[i]
            if alt > 0:
                m = months[i]
                eBeam = 1415 * math.exp(-stat.monthly_tau_beam[m] * math.pow(airMass, beamEpxs[m]))
                eDiff = 1415 * math.exp(-stat.monthly_tau_diffuse[m] * math.pow(airMass, diffuseExps[m]))
                eGlob = eDiff + eBeam*math.cos(math.radians(90-alt))
                directNormRad.append(eBeam)
                diffuseHorizRad.append(eDiff)
            else:
                directNormRad.append(0)
                diffuseHorizRad.append(0)

        return cls(stat.location, directNormRad, diffuseHorizRad, timestep)

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

    def to_json(self):
        """Write Wea to json file
            {
            "location": {} , // ladybug location schema
            "direct_normal_radiation": (), // Tuple of hourly direct normal
                radiation
            "diffuse_horizontal_radiation": (), // Tuple of hourly diffuse
                horizontal radiation
            "timestep": float //timestep between measurements, default is 1
            }
        """
        return {
            'location': self.location.to_json(),
            'direct_normal_radiation': self.direct_normal_radiation.to_json(),
            'diffuse_horizontal_radiation': self.diffuse_horizontal_radiation.to_json(),
            'timestep': self.timestep
        }

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
