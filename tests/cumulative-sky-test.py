from ladybug import sky, core, skyvector

# # check number of vectors for skies
# vectors = skyvector.Skyvectors(0)
# assert len(vectors) == 146
#
# # check number of vectors for skies
# vectors = skyvector.Skyvectors(1)
# assert len(vectors) == 578
#
# patchData = core.LBPatchData(20, vectors[0])
# assert patchData.value == 20
# assert patchData.vector.x == 0
# assert patchData.vector.y == 0
# assert patchData.vector.z == -1

epwfile = r"C:\EnergyPlusV8-3-0\WeatherData\USA_CO_Golden-NREL.724666_TMY3.epw"
cSky = sky.CumulativeSkyMtx(epwfile, workingDir = "c:\\ladybug")
cSky.gendaymtx()

assert len(cSky.skyDiffuseRadiation.values()) == cSky.numberOfPatches

# get the sky only for January
ap = core.AnalysisPeriod(endMonth=1)
cSky.gendaymtx(analysisPeriod = ap)

assert len(cSky.skyDirectRadiation.values(header = True)) == cSky.numberOfPatches + 6
