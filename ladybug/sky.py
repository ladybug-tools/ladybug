import epw
import core
import skyvector

import os
import json
import subprocess
import sys

class CumulativeSkyMtx(object):
    """Cumulative Sky

        Attributes:
            epwFileAddress: Path to EPW file.
            skyDensity: Density of the sky. 0 generates a Tregenza sky, which will
                divide up the sky dome with a coarse density of 145 sky patches.
                Set to 1 to generate a Reinhart sky, which will divide up the sky dome
                using a density of 580 sky patches.
            workingDir: A local directory to run the study and write the results

        Usage:
            epwfile = r"C:\EnergyPlusV8-3-0\WeatherData\USA_CO_Golden-NREL.724666_TMY3.epw"
            cumSky = CumulativeSkyMtx(epwfile) #calculate the sky
            # annual results
            cumSky.annualResults()

            # results for an anlysis period
            ap = AnalysisPeriod(startMonth = 2, endMonth = 12)
            results = cumSky.filterByAnalysisPeriod(ap)
            print results.diffuseValues
    """

    def __init__(self, epwFileAddress, skyDensity = 0, workingDir = None):
        self.__epw = epw.EPW(epwFileAddress)
        self.__data = {"diffuse": {}, "direct": {}}
        self.__results = {}
        self.skyDensity = skyDensity
        self.__isCalculated = False
        self.__isLoaded = False
        self.workingDir = workingDir

    @property
    def skyDensity(self):
        "Return sky density. 0: Tregenza, 1: Reinhart"
        return self.__skyDensity

    @skyDensity.setter
    def skyDensity(self, density):
        assert int(density) <= 1, "Sky density is should be 0: Tregenza sky, 1: Reinhart sky"
        self.__skyDensity = int(density)
        #prepare place holder for patches
        for patch in range(self.numberOfPatches):
            self.__data['diffuse'] = {}
            self.__data['direct'] = {}

    @property
    def workingDir(self):
        "A local directory to run the study and write the results"
        return self.__workingDir

    @workingDir.setter
    def workingDir(self, workingDir):
        # update addresses
        if not hasattr(self, "__workingDir"):
            # user has initiated the class
            self.__workingDir = workingDir

        if not self.__workingDir:
            self.__workingDir = self.__epw.filePath

        # add name of city to path
        if not self.__workingDir.endswith(self.__epw.location.city):
            self.__workingDir = os.path.join(self.__workingDir, self.__epw.location.city.replace(" ", "_"))

        # create the folder is it's not created
        if not os.path.isdir(self.__workingDir):
            os.mkdir(self.__workingDir)
        # update path for other files if it's a new workingDir
        # naming convention is weatherFileName_[diffuse/direct]_[skyDensity].mtx
        __name = self.__epw.fileName[:-4] + "_%s_%d.mtx"
        self.__diffuseMtxFileAddress = os.path.join(self.__workingDir, __name%("dif", self.__skyDensity))
        self.__directMtxFileAddress = os.path.join(self.__workingDir, __name%("dir", self.__skyDensity))
        self.__jsonFileAddress= os.path.join(self.__workingDir, self.__epw.fileName[:-4] + \
            "_" + str(self.__skyDensity) + ".json")

    @property
    def numberOfPatches(self):
        return self.__patchData("numberOfPatches")

    @property
    def skyDiffuseRadiation(self):
        """Diffuse values for sky patches as a LBDataList"""

        assert self.__isCalculated, "You need to calculate the materix first before" + \
            " loading the results.\nUse calculateMtx method. If you see this error from inside " + \
            "Dynamo reconnect one of the inputs and re-run the file!\nFiles are created under %s"%self.workingDir

        assert self.__isLoaded, "The values are not loaded. Use skyMtx method."

        return self.__results["diffuse"]

    @property
    def skyDirectRadiation(self):
        """Direct values for sky patches as a LBDataList"""

        assert self.__isCalculated, "You need to calculate the materix first before" + \
            " loading the results.\nUse calculateMtx method. If you see this error from inside " + \
            "Dynamo reconnect one of the inputs and re-run the file!\nFiles are created under %s"%self.workingDir

        assert self.__isLoaded, "The values are not loaded. Use skyMtx method."

        return self.__results["direct"]

    @property
    def skyTotalRadiation(self):
        """Total values for sky patches as a LBDataList"""

        assert self.__isCalculated, "You need to calculate the materix first before" + \
            " loading the results.\nUse calculateMtx method. If you see this error from inside " + \
            "Dynamo reconnect one of the inputs and re-run the file!\nFiles are created under %s"%self.workingDir

        assert self.__isLoaded, "The values are not loaded. Use skyMtx method."

        return self.__results["total"]

    def steradianConversionFactor(self, patchNumber):
        "Steradian Conversion Factor"
        rowNumber = self.__calculateRowNumber(patchNumber)
        strConv = self.__patchData("steradianConversionFactor")[rowNumber]
        return strConv

    def __patchData(self, key):
        """
            Return data for sky patches based on key

            Args:
                key: valid keys are numberOfPatches, numberOfPatchesInEachRow and steradianConversionFactor.

            Return:
                Data for this sky based on the sky density. Depending on the key it can be a number or a list of numbers

            Usage:
                self.__patchesData("numberOfPatches")
                >> 146
        """

        # first row is horizon and last row is values for the zenith
        # first patch is the ground. I put 0 on conversion
        __data = {
            "numberOfPatches": {0 : 146, 1 : 578},
            "numOfPatchesInEachRow": {0: [1, 30, 30, 24, 24, 18, 12, 6, 1], \
                        1: [1, 60, 60, 60, 60, 48, 48, 48, 48, 36, 36, 24, 24, 12, 12, 1]},
            "steradianConversionFactor": {0 : [0, 0.0435449227, 0.0416418006, 0.0473984151, \
                0.0406730411, 0.0428934136, 0.0445221864, 0.0455168385, 0.0344199465],
                1: [0, 0.0113221971, 0.0111894547, 0.0109255262, 0.0105335058, 0.0125224872, \
                    0.0117312774, 0.0108025291, 0.00974713106, 0.011436609, 0.00974295956, \
                    0.0119026242, 0.00905126163, 0.0121875626, 0.00612971396, 0.00921483254]}
        }

        assert key in __data, "Invalid key: %s"%key
        return __data[key][self.__skyDensity]

    def __calculateRowNumber(self, patchNumber):
        """Calculate number of row for sky patch"""

        if patchNumber ==0 : return 0
        __numOfPatchesInEachRow = self.__patchData(key = "numOfPatchesInEachRow")

        for rowCount, patchCountInRow in enumerate(__numOfPatchesInEachRow):
            if patchNumber < sum(__numOfPatchesInEachRow[:rowCount+1]):
                return rowCount

    def epw2wea(self, filePath = None):
        if not filePath:
            filePath = os.path.join(self.__workingDir, self.__epw.fileName[:-4] + ".wea")
        self.__weaFileAddress = self.__epw.epw2wea(filePath)

    def calculateMtx(self, pathToRadianceBinaries = r"c:\radiance\bin", recalculate = False):
        """use Radiance gendaymtx to generate the sky

            Args:
                pathToRadianceBinaries: Path to Radiance libraries. Default is C:\radiance\bin.
                recalculate: Set to True if you want the sky to be recalculated even it has been calculated already
        """

        #check if the result is already calculated
        if not recalculate:
            if os.path.isfile(self.__diffuseMtxFileAddress) \
                and os.path.isfile(self.__directMtxFileAddress):
                self.__isCalculated = True
                return

        if not pathToRadianceBinaries: pathToRadianceBinaries = r"c:\radiance\bin"

        assert os.path.isfile(os.path.join(pathToRadianceBinaries, "gendaymtx.exe")) \
            and os.path.isfile(os.path.join(pathToRadianceBinaries, "rcollate.exe")), \
            "Can't find gendaymtx.exe or rcollate.exe in radiance binary folder."

        # make sure daymtx and rcollate can be executed
        assert os.access(os.path.join(pathToRadianceBinaries, "gendaymtx.exe"), os.X_OK), \
            "%s is blocked by system! Right click on the file,"%os.path.join(pathToRadianceBinaries, "gendaymtx.exe") + \
            " select properties and unblock it."

        assert os.access(os.path.join(pathToRadianceBinaries, "rcollate.exe"), os.X_OK), \
            "%s is blocked by system! Right click on the file,"%os.path.join(pathToRadianceBinaries, "rcollate.exe") + \
            " select properties and unblock it."

        # assure wea file is calculated
        if not hasattr(self, "__weaFileAddress"): self.epw2wea()

        __name = self.__epw.fileName[:-4] + "_calculate_sky_mtx.bat"
        batchFileAddress = os.path.join(self.__workingDir, __name)

        batchFile = """
        @echo off
        echo.
        echo HELLO #username! DO NOT CLOSE THIS WINDOW.
        echo.
        echo IT WILL BE CLOSED AUTOMATICALLY WHEN THE CALCULATION IS OVER!
        echo.
        echo AND MAY TAKE FEW MINUTES...
        echo.
        echo CALCULATING DIFFUSE COMPONENT OF THE SKY...
        #pathToRadianceBinaries\\gendaymtx -m #skyDensity -s -O1 #weaFileAddress | #pathToRadianceBinaries\\rcollate -t > #diffuseMtxFileAddress
        echo.
        echo CALCULATING DIRECT COMPONENT OF THE SKY...
        #pathToRadianceBinaries\\gendaymtx -m #skyDensity -d -O1 #weaFileAddress | #pathToRadianceBinaries\\rcollate -t > #directMtxFileAddress
        """.replace("#pathToRadianceBinaries", pathToRadianceBinaries) \
           .replace("#skyDensity", str(self.skyDensity + 1)) \
           .replace("#weaFileAddress", self.__weaFileAddress) \
           .replace("#diffuseMtxFileAddress", self.__diffuseMtxFileAddress) \
           .replace("#directMtxFileAddress", self.__directMtxFileAddress)

        # write batch file
        with open(batchFileAddress, "w") as genskymtxbatfile:
            genskymtxbatfile.write(batchFile)

        subprocess.Popen(batchFileAddress, shell = True)

    def __calculateLuminanceFromRGB(self, R, G, B, patchNumber):
        return (.265074126 * float(R) + .670114631 * float(G) + .064811243 * float(B)) * self.steradianConversionFactor(patchNumber)

    def __loadMtxFiles(self):
        """load the values from .mtx files. use self.skyMtx to get the results
        """

        if self.__isLoaded:
            print "Matrix has been already loaded!"
            return

        assert self.__isCalculated, "You need to calculate the materix first before" + \
            " loading the results. Use calculateMtx method. If you see this error from inside " + \
            "Dynamo reconnect one of the inputs and re-run the file!"

        assert os.path.getsize(self.__diffuseMtxFileAddress) > 0 and \
            os.path.getsize(self.__directMtxFileAddress) > 0, \
            "Size of matrix files is 0. Try to recalculate cumulative sky matrix."

        try:
            # open files and read the lines
            diffSkyFile = open(self.__diffuseMtxFileAddress, "rb")
            dirSkyFile = open(self.__directMtxFileAddress, "rb")

            # pass header
            for i in range(9):
                diffSkyFile.readline()
                dirSkyFile.readline()

            # import hourly data
            analysisPeriod = core.AnalysisPeriod()

            for patchNumber in range(self.numberOfPatches):
                # create header for each patch
                difHeader = core.LBHeader(city = self.__epw.location.city, frequency ='Hourly', \
                        analysisPeriod = analysisPeriod, \
                        dataType = "Patch #%d diffuse radiation"%patchNumber, unit = "Wh")

                dirHeader = core.LBHeader(city = self.__epw.location.city, frequency ='Hourly', \
                        analysisPeriod = analysisPeriod, \
                        dataType = "Patch #%d direct radiation"%patchNumber, unit = "Wh")

                # create an empty data list with the header
                self.__data['diffuse'][patchNumber] = core.DataList(header =difHeader)
                self.__data['direct'][patchNumber] = core.DataList(header =dirHeader)

            for HOY in range(8760):

                diffLine = diffSkyFile.readline()
                dirLine = dirSkyFile.readline()

                timestamp = core.LBDateTime.fromHOY(HOY + 1)

                for patchNumber, (diffData, dirData) in enumerate(zip(diffLine.split("\t"), dirLine.split("\t"))):

                    _difR, _difG, _difB =  diffData.split(" ")
                    _dirR, _dirG, _dirB =  dirData.split(" ")

                    _difValue = self.__calculateLuminanceFromRGB(_difR, _difG, _difB, patchNumber)
                    _dirValue = self.__calculateLuminanceFromRGB(_dirR, _dirG, _dirB, patchNumber)

                    self.__data["diffuse"][patchNumber].append(core.LBData(_difValue, timestamp))
                    self.__data["direct"][patchNumber].append(core.LBData(_dirValue, timestamp))

            self.__isLoaded = True

        except Exception, e:
            print e
        finally:
            diffSkyFile.close()
            dirSkyFile.close()
            del(diffLine)
            del(dirLine)

    # TODO: Analysis perios in headers should be adjusted based on the input
    def gendaymtx(self, pathToRadianceBinaries = None, diffuse = True, direct = True, \
        recalculate = False, analysisPeriod = None):
        """Get sky matrix for direct, diffuse and total radiation as three separate lists

            Args:
                pathToRadianceBinaries: Path to Radiance libraries. Default is C:\radiance\bin.
                diffuse: Set to True to include diffuse radiation
                direct: Set to True to iclude direct radiation
                recalculate: Set to True if you want the sky to be recalculated even it has been calculated already
                analysisPeriod: An analysis period or a list of integers between 1-8760 for hours of the year. Default is All the hours of the year
        """

        # calculate sky if it's not already calculated
        if not self.__isCalculated or recalculate:
            self.calculateMtx(pathToRadianceBinaries = pathToRadianceBinaries, recalculate = recalculate)

        # load matrix files if it's not loaded
        if not self.__isLoaded:
            self.__loadMtxFiles()

        if not analysisPeriod:
            HOYs = range(1, 8761)
        else:
            if isinstance(analysisPeriod, list):
                HOYs = [h if 0 < h < 8761 else -1 for h in analysisPeriod]
                assert (not -1 in HOYs), "Hour should be between 1-8760"

            elif isinstance(analysisPeriod, core.AnalysisPeriod):
                HOYs = analysisPeriod.HOYs
            else:
                raise ValueError("Analysis period should be a list of integers or an analysis period.")

        # calculate values and return them as 3 lists
        # put 0 value for all the patches
        __cumulativeRaditionValues = {"diffuse": [0] * self.numberOfPatches, \
                "direct": [0] * self.numberOfPatches}

        for patchNumber in range(self.numberOfPatches):
            for HOY in HOYs:
                __cumulativeRaditionValues["diffuse"][patchNumber] += self.__data["diffuse"][patchNumber][HOY - 1]
                __cumulativeRaditionValues["direct"][patchNumber] += self.__data["direct"][patchNumber][HOY - 1]

        # create header for each patch
        difHeader = core.LBHeader(city = self.__epw.location.city, frequency ='NA', \
                analysisPeriod = None, \
                dataType = "Sky Patches' Diffues Radiation", unit = "Wh")

        dirHeader = core.LBHeader(city = self.__epw.location.city, frequency ='NA', \
                analysisPeriod = None, \
                dataType = "Sky Patches' Direct Radiation", unit = "Wh")

        totalHeader = core.LBHeader(city = self.__epw.location.city, frequency ='NA', \
                analysisPeriod = None, \
                dataType = "Sky Patches' Total Radiation", unit = "Wh")

        # create an empty data list with the header
        __skyVectors = skyvector.Skyvectors(self.__skyDensity)

        self.__results = {}

        self.__results['diffuse'] = core.DataList(header =difHeader)
        self.__results['direct'] = core.DataList(header =dirHeader)
        self.__results['total'] = core.DataList(header =totalHeader)

        for patchNumber in range(self.numberOfPatches):

            __diff = __cumulativeRaditionValues["diffuse"][patchNumber] if diffuse else 0
            __dir = __cumulativeRaditionValues["direct"][patchNumber] if direct else 0

            self.__results['diffuse'].append(core.LBPatchData( __diff, __skyVectors[patchNumber]))

            self.__results['direct'].append(core.LBPatchData( __dir, __skyVectors[patchNumber]))

            self.__results['total'].append(core.LBPatchData( __diff + __dir, __skyVectors[patchNumber]))

        del(__cumulativeRaditionValues)

    def mtx2json(self):
        "convert sky matrix files to json object"
        raise NotImplementedError()

    def __repr__(self):
        return "Ladybug.SkyMatrix > %s"%self.__epw.location.city
