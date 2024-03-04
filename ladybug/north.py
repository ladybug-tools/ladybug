# coding=utf-8
"""Module converting between magnetic and true North."""
from __future__ import division

import math
import os


class WorldMagneticModel(object):
    """World Magnetic Model (WMM) that can convert from magnetic to true North.

     Args:
        cof_file: The full path to a .COF file containing the coefficients that
            form the inputs for the World Magnetic Model (WMM). A new set of coefficients
            is published roughly every 5 years as the magnetic poles continue to
            move. If None, coefficients will be derived from the WMM.COF file contained
            within this Python package, which should be for the most recent model.
            If not, the most recent coefficients are available at
            https://www.ncei.noaa.gov/products/world-magnetic-model/wmm-coefficients
    """

    def __init__(self, cof_file=None):
        """Initialize WorldMagneticModel."""
        # use the .COF file in this package if not specified
        if cof_file is None:
            cof_file = os.path.join(os.path.dirname(__file__), 'WMM.COF')

        # parse the coefficients from the file contents
        wmm = []
        with open(cof_file) as wmm_file:
            for line in wmm_file:
                vals = line.strip().split()
                if len(vals) == 3:
                    self.epoch = float(vals[0])
                    self.model = vals[1]
                    self.modeldate = vals[2]
                elif len(vals) == 6:
                    line_dict = {
                        'n': int(float(vals[0])),
                        'm': int(float(vals[1])),
                        'gnm': float(vals[2]),
                        'hnm': float(vals[3]),
                        'dgnm': float(vals[4]),
                        'dhnm': float(vals[5])
                    }
                    wmm.append(line_dict)

        # set the global constants used by the WMM
        z = [0.0] * 15
        self.maxord = 12
        self.tc = []
        for _ in range(14):
            self.tc.append(z[0:13])
        self.sp = z[0:14]
        self.cp = z[0:14]
        self.cp[0] = 1.0
        self.pp = z[0:13]
        self.pp[0] = 1.0
        self.p = []
        for _ in range(14):
            self.p.append(z[0:14])
        self.p[0][0] = 1.0
        self.dp = []
        for _ in range(14):
            self.dp.append(z[0:13])
        self.a = 6378.137
        self.b = 6356.7523142
        self.re = 6371.2
        self.a2 = self.a*self.a
        self.b2 = self.b*self.b
        self.c2 = self.a2-self.b2
        self.a4 = self.a2*self.a2
        self.b4 = self.b2*self.b2
        self.c4 = self.a4 - self.b4

        self.c = []
        self.cd = []
        for _ in range(14):
            self.c.append(z[0:14])
            self.cd.append(z[0:14])

        # adjust C and CD from the file contents
        for wmmnm in wmm:
            m = wmmnm['m']
            n = wmmnm['n']
            gnm = wmmnm['gnm']
            hnm = wmmnm['hnm']
            dgnm = wmmnm['dgnm']
            dhnm = wmmnm['dhnm']
            if (m <= n):
                self.c[m][n] = gnm
                self.cd[m][n] = dgnm
                if (m != 0):
                    self.c[n][m - 1] = hnm
                    self.cd[n][m - 1] = dhnm

        # convert schmidt normalized gauss coefficients to un-normalized
        self.snorm = []
        for _ in range(13):
            self.snorm.append(z[0:13])
        self.snorm[0][0] = 1.0
        self.k = []
        for _ in range(13):
            self.k.append(z[0:13])
        self.k[1][1] = 0.0
        self.fn = [float(i) for i in range(14)]
        self.fm = [float(i) for i in range(13)]
        for n in range(1, self.maxord + 1):
            self.snorm[0][n] = self.snorm[0][n - 1] * (2.0 * n - 1) / n
            j = 2.0
            m = 0
            d_1 = 1
            d_2 = (n - m + d_1) / d_1
            while (d_2 > 0):
                self.k[m][n] = (((n - 1) * (n - 1)) - (m * m)) / \
                    ((2.0 * n - 1) * (2.0 * n - 3.0))
                if (m > 0):
                    flnmj = ((n - m + 1.0) * j) / (n + m)
                    self.snorm[m][n] = self.snorm[m - 1][n] * math.sqrt(flnmj)
                    j = 1.0
                    self.c[n][m - 1] = self.snorm[m][n] * self.c[n][m - 1]
                    self.cd[n][m - 1] = self.snorm[m][n] * self.cd[n][m - 1]
                self.c[m][n] = self.snorm[m][n] * self.c[m][n]
                self.cd[m][n] = self.snorm[m][n] * self.cd[m][n]
                d_2 = d_2 - 1
                m = m + d_1

        # set default lat, lon and altitude, which will be overwritten as used
        self.otime = -1000.0
        self.oalt = -1000.0
        self.olat = -1000.0
        self.olon = -1000.0

    def magnetic_declination(self, latitude=0, longitude=0, elevation=0, year=2025):
        """Compute the magnetic declination using the World Magnetic Model (WMM).

        Magnetic declination is the difference between magnetic North and true North at
        a given location on the globe (expressed in terms of degrees). The function
        here uses the same method that underlies the NOAA Magnetic Declination
        calculator.

        Args:
            latitude: A number between -90 and 90 for the latitude of the location
                in degrees. (Default: 0 for the equator).
            longitude: A number between -180 and 180 for the longitude of the location
                in degrees (Default: 0 for the prime meridian).
            elevation: A number for elevation of the location in meters. (Default: 0).
            year: A number for the year in which the magnetic declination is
                being evaluated. Decimal values are accepted. (Default: 2025).

        Returns:
            A number for the magnetic declination in degrees.
        """
        # set up the properties given the location and year information
        alt = elevation / 1000   # to kilometers
        dt = year - self.epoch
        glat = latitude
        glon = longitude
        rlat = math.radians(glat)
        rlon = math.radians(glon)
        srlon = math.sin(rlon)
        srlat = math.sin(rlat)
        crlon = math.cos(rlon)
        crlat = math.cos(rlat)
        srlat2 = srlat * srlat
        crlat2 = crlat * crlat
        self.sp[1] = srlon
        self.cp[1] = crlon

        # convert from geodetic to spherical coordinates
        if (alt != self.oalt or glat != self.olat):
            q = math.sqrt(self.a2 - self.c2 * srlat2)
            q1 = alt * q
            q2 = ((q1 + self.a2) / (q1 + self.b2)) * ((q1 + self.a2) / (q1 + self.b2))
            ct = srlat / math.sqrt(q2 * crlat2 + srlat2)
            st = math.sqrt(1.0 - (ct * ct))
            r2 = (alt * alt) + 2.0 * q1 + (self.a4 - self.c4 * srlat2) / (q * q)
            r = math.sqrt(r2)
            d = math.sqrt(self.a2 * crlat2 + self.b2 * srlat2)
            ca = (alt + d) / r
            sa = self.c2 * crlat * srlat / (r * d)

        if (glon != self.olon):
            for m in range(2, self.maxord + 1):
                self.sp[m] = self.sp[1] * self.cp[m - 1] + self.cp[1] * self.sp[m - 1]
                self.cp[m] = self.cp[1] * self.cp[m - 1] - self.sp[1] * self.sp[m - 1]

        aor = self.re / r
        ar = aor * aor
        br = bt = bp = bpp = 0.0
        for n in range(1, self.maxord + 1):
            ar = ar * aor
            m = 0
            D4 = (n + m + 1)
            while D4 > 0:
                # compute un-normalized associated polynomials and derivatives
                if (alt != self.oalt or glat != self.olat):
                    if (n == m):
                        self.p[m][n] = st * self.p[m - 1][n - 1]
                        self.dp[m][n] = \
                            st * self.dp[m - 1][n - 1] + ct * self.p[m - 1][n - 1]

                    elif (n == 1 and m == 0):
                        self.p[m][n] = ct * self.p[m][n-1]
                        self.dp[m][n] = ct * self.dp[m][n - 1] - st * self.p[m][n - 1]

                    elif (n > 1 and n != m):
                        if (m > n - 2):
                            self.p[m][n - 2] = 0
                        if (m > n - 2):
                            self.dp[m][n - 2] = 0.0
                        self.p[m][n] = \
                            ct * self.p[m][n - 1] - self.k[m][n] * self.p[m][n - 2]
                        self.dp[m][n] = ct * self.dp[m][n - 1] - \
                            st * self.p[m][n - 1]-self.k[m][n] * self.dp[m][n - 2]

                # time adjust the gauss coefficients
                if (year != self.otime):
                    self.tc[m][n] = self.c[m][n] + dt * self.cd[m][n]
                    if (m != 0):
                        self.tc[n][m - 1] = self.c[n][m - 1] + dt * self.cd[n][m - 1]

                # accumulate terms of the spherical harmonic expansions
                par = ar * self.p[m][n]
                if (m == 0):
                    temp1 = self.tc[m][n] * self.cp[m]
                    temp2 = self.tc[m][n] * self.sp[m]
                else:
                    temp1 = self.tc[m][n] * self.cp[m] + self.tc[n][m - 1] * self.sp[m]
                    temp2 = self.tc[m][n] * self.sp[m] - self.tc[n][m - 1] * self.cp[m]

                bt = bt - ar * temp1 * self.dp[m][n]
                bp = bp + (self.fm[m] * temp2 * par)
                br = br + (self.fn[n] * temp1 * par)

                # special case: north/south geographic poles
                if (st == 0.0 and m == 1):
                    if (n == 1):
                        self.pp[n] = self.pp[n - 1]
                    else:
                        self.pp[n] = ct * self.pp[n - 1] - self.k[m][n] * self.pp[n - 2]
                    parp = ar * self.pp[n]
                    bpp = bpp + (self.fm[m] * temp2 * parp)
                D4 = D4 - 1
                m = m + 1

        if (st == 0.0):
            bp = bpp
        else:
            bp = bp/st

        # rotate magnetic vector components from spherical to geodetic coordinates
        bx = -bt * ca - br * sa
        by = bp
        declination = math.degrees(math.atan2(by, bx))

        # set the location attributes that the model has been aligned to
        self.otime = year
        self.oalt = alt
        self.olat = glat
        self.olon = glon

        return declination

    def magnetic_to_true_north(self, location, magnetic_north=0, year=2025):
        """Compute true North from a magnetic North vector.

        Args:
            location: A Ladybug Location object that will be used to determine the
                magnetic declination.
            magnetic_north: A number between -360 and 360 for the counterclockwise
                difference between the North and the positive Y-axis in degrees.
                90 is West and 270 is East (Default: 0).
            year: A number for the year in which the magnetic declination is
                being evaluated. Decimal values are accepted. (Default: 2025).

        Returns:
            A number between -360 and 360 for the true North angle in degrees.
        """
        declination = self.magnetic_declination(
            location.latitude, location.longitude, location.elevation, year)
        true_north = magnetic_north + declination
        if true_north > 360:
            true_north = true_north - 360
        elif true_north < -360:
            true_north = 360 + true_north
        return true_north

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """Return WorldMagneticModel as a string."""
        return 'WorldMagneticModel: {}'.format(self.epoch)
