from ladybug import epw

class SkyDensity:
    """docstring for SkyDensity"""
    def __init__(self, density = 0):
        self.density = density
        self.numOfPatches = get_numberOfPatches

    @property
    def get_numberOfPatches(self):
        return

    @staticmethod
    def __numberOfPatches():
        return

class CumulativeSkyMtx:
    """Cumulative Sky

        EPW: A ladybug epw object. Use ladybug.epw.EPW to generate the file
        skyDensity: Density of the sky. 0 generates a Tregenza sky, which will
            divide up the sky dome with a coarse density of 145 sky patches.
            Set to 1 to generate a Reinhart sky, which will divide up the sky dome
            using a density of 580 sky patches.
    """

    def __init__(self, EPW, skyDensity = 0):
        self.EPW = epw.EPW(EPW)
        self.skyDensity = skyDensity
