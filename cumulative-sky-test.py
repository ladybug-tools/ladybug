from ladybug import sky, core, skyvector


epwfile = r"C:\EnergyPlusV8-3-0\WeatherData\USA_CO_Golden-NREL.724666_TMY3.epw"
cSky = sky.CumulativeSkyMtx(epwfile, workingDir = "c:\\ladybug")
cSky.epw2wea()
cSky.calculateMtx()
cSky.loadMtxFiles()
res = cSky.skyMtx()

print res['diffuse'].values
print res['direct'].values

# # check number of vectors for skies
# vectors = skyvector.Skyvectors(0)
# assert len(vectors) == 146
#
# # check number of vectors for skies
# vectors = skyvector.Skyvectors(1)
# assert len(vectors) == 580
#
# patchData = core.LBPatchData(20, vectors[0])
# assert patchData.value == 20
# assert patchData.vector.x == 0
# assert patchData.vector.y == 0
# assert patchData.vector.z == -1
