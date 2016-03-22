"""PMV Comfort object.

"""
import math
import psychrometrics
import util
import comfortBase
from ..epw import EPW
from ..listoperations import duplicate

class PMV(object):
    """PMV Comfort Object

        Attributes:
            airTemperature: A list of numbers representing dry bulb temperatures
                in degrees Celcius.
            radTemperature: A list of numbers representing mean radiant temperatures
                in degrees Celcius.
            windSpeed: A list of numbers representing wind speeds in m/s.
            relHumidity: A list of numbers representing relative humidities in %.
            metRate: A list of numbers representing the metabolic rate of the
                human subject in met. 1 met = resting seated.
            cloValues: A list of numbers representing the clothing level of the
                human subject in clo. 1 clo = three-piece suit.
            externalWork: A list of numbers representing the work done by the
                human subject in met. 1 met = resting seated.

        Usage:
            #Compute PMV for a single set of values.
            myPmvComf = pmv.fromIndividualValues(26, 26, 0.75, 80, 1.1, 0.5)
            myPMV, myPPD, mySET, myComf, myReason = myPmvComf.GetFullPMV()

            #Compute PMV for a list of data.
            airTemp = [10, 12, 15, 18, 19]
            relHumid = [75, 70, 60, 50, 45]
            myPmvComf = pmv.PMV(airTemp, [], [], relHumid)
            myPMV, myPPD, mySET, myComf, myReason = myPmvComf.GetFullPMV()
    """


    def __init__(self, airTemperature=[], radTemperature=[], windSpeed=[], relHumidity=[], metRate=[], cloValues=[], externalWork=[], headerIncl=None):
        """
        Initialize a PMV comfort object from lists of PMV inputs.

        airTemperature: A list of numbers representing dry bulb temperatures
            in degrees Celcius. If list is empty, default is set to 20 C.
        radTemperature: A list of numbers representing mean radiant temperatures
            in degrees Celcius. If list is empty, default is set be the same as airTemperature.
        windSpeed: A list of numbers representing wind speeds in m/s.
            If list is empty, default is set to 0 m/s.
        relHumidity: A list of numbers representing relative humidities in %.
            If list is empty, default is set to 50%.
        metRate: A list of numbers representing the metabolic rate of the
            human subject in met. 1 met = resting seated. If list is empty, default
            is set to 1 met.
        cloValues: A list of numbers representing the clothing level of the
            human subject in clo. 1 clo = three-piece suit. If list is empty,
            default is set to 1 clo.
        externalWork: A list of numbers representing the work done by the
            human subject in met. 1 met = resting seated. If list is empty,
            default is set to 0 met.

        """
        # Assign all of the input values to the PMV comfort model object.
        if airTemperature != []: self.airTemperature = airTemperature
        else: self.airTemperature = [20]
        if radTemperature != []: self.radTemperature = radTemperature
        else: self.radTemperature = self.airTemperature
        if windSpeed != []: self.windSpeed = windSpeed
        else: self.windSpeed = [0]
        if relHumidity != []: self.relHumidity = relHumidity
        else: self.relHumidity = [50]
        if metRate != []: self.metRate = metRate
        else: self.metRate = [1]
        if cloValues != []: self.cloValues = cloValues
        else: self.cloValues = [1]
        if externalWork != []: self.externalWork = externalWork
        else: self.externalWork = [0]

        # Varialbes that tells us the length of the input data and whether there is a header on the input data.
        self.calcLength = None
        self.headerIncl = headerIncl
        self.headerStr = []

        # Quick check to see if all lists are aligned.
        listLen = len(self.airTemperature)
        if len(self.radTemperature) == listLen and len(self.windSpeed) == listLen and \
            len(self.relHumidity) == listLen and len(self.metRate) == listLen and \
                len(self.cloValues) == listLen and len(self.externalWork) == listLen and headerIncl == False:
                    self.__isDataAligned = True
        else:
            self.__isDataAligned = False

        # Set default comfort parameters.
        self.comfortPar = {
            'PPDComfortThresh': 10.0,
            'humidRatioUp': 0.03,
            'humidRatioLow': 0,
            'stillAirThreshold': 0.1
        }

        # Set blank values for PMV, PPD, and SET.
        self._pmv = []
        self._ppd = []
        self._set = []
        self._isComfortable = []
        self._discomfReason = []
        self._ta_adj = []
        self._cooling_effect = []


    @classmethod
    def fromIndividualValues(cls, airTemperature=20, radTemperature=None, windSpeed=0, relHumidity=50, metRate=1, cloValues=1, externalWork=0):
        """Create and PMV comfort object from individual values instead of listis of values.
        """
        if radTemperature == None: radTemperature = airTemperature

        return cls(airTemperature, radTemperature, windSpeed, relHumidity, metRate, cloValues, externalWork, False)

    @classmethod
    def fromEPWFile(cls, epwFileAddress, metRate=1, cloValue=1, externalWork=0):
        """
        Create and PMV comfort object from the conditions within an EPW file.
        metRate: A value representing the metabolic rate of the human subject in met.
            1 met = resting seated. If list is empty, default is set to 1 met.
        cloValue: A lvalue representing the clothing level of the human subject in clo.
            1 clo = three-piece suit. If list is empty, default is set to 1 clo.
        externalWork: A value representing the work done by the human subject in met.
            1 met = resting seated. If list is empty, default is set to 0 met.
        """
        metRates = duplicate(metRate, 8760)
        cloValues = duplicate(cloValue, 8760)
        externalWorks = duplicate(externalWork, 8760)

        epwData = EPW(epwFileAddress)
        return cls(epwData.dryBulbTemperature.values(header=True), epwData.dryBulbTemperature.values(header=True), epwData.windSpeed.values(header=True), epwData.relativeHumidity.values(header=True), metRates, cloValues, externalWorks, True)


    @staticmethod
    def checkAndAlignLists(self, airTemperature, radTemperature, windSpeeds, relHumidity, metabolicRate, clothingValues, externalWork):
        """ Checks to be sure that the lists of PMV input variables are aligned and fills in defaults where possible."""
        # Check lenth of the airTemperature list and evaluate the contents.
        checkData1 = False
        airTemp = []
        airMultVal = False
        if len(airTemperature) != 0:
            try:
                if "Temperature" in airTemperature[2]:
                    airTemp = airTemperature[7:]
                    checkData1 = True
                    self.headerIncl = True
                    self.headerStr = airTemperature[0:7]
            except: pass
            if checkData1 == False:
                for item in airTemperature:
                    try:
                        airTemp.append(float(item))
                        checkData1 = True
                    except: checkData1 = False
            if len(airTemp) > 1: airMultVal = True
            if checkData1 == False:
                raise Exception("airTemperature input does not contain valid temperature values in degrees Celcius.")

        # Check lenth of the radTemperature list and evaluate the contents.
        checkData2 = False
        radTemp = []
        radMultVal = False
        if len(radTemperature) != 0:
            try:
                if "Temperature" in radTemperature[2]:
                    radTemp = radTemperature[7:]
                    checkData2 = True
                    self.headerIncl = True
                    self.headerStr = radTemperature[0:7]
            except: pass
            if checkData2 == False:
                for item in radTemperature:
                    try:
                        radTemp.append(float(item))
                        checkData2 = True
                    except: checkData2 = False
            if len(radTemp) > 1: radMultVal = True
            if checkData2 == False:
                raise Exception("radTemperature input does not contain valid temperature values in degrees Celcius.")
        else:
            checkData2 = True
            radTemp = airTemp
            if len(radTemp) > 1: radMultVal = True

        # Check lenth of the windSpeeds list and evaluate the contents.
        checkData3 = False
        windSpeed = []
        windMultVal = False
        nonPositive = True
        if len(windSpeeds) != 0:
            try:
                if windSpeeds[2] == 'Wind Speed':
                    windSpeed = windSpeeds[7:]
                    checkData3 = True
                    self.headerIncl = True
                    self.headerStr = windSpeeds[0:7]
            except: pass
            if checkData3 == False:
                for item in windSpeeds:
                    try:
                        if float(item) >= 0:
                            windSpeed.append(float(item))
                            checkData3 = True
                        else: nonPositive = False
                    except: checkData3 = False
            if nonPositive == False: checkData3 = False
            if len(windSpeed) > 1: windMultVal = True
            if checkData3 == False:
                raise Exception('windSpeeds input does not contain valid wind speed in meters per second.  Note that wind speed must be positive.')
        else:
            checkData3 = True
            windSpeed = [0]

        # Check lenth of the relHumidity list and evaluate the contents.
        checkData4 = False
        relHumid = []
        humidMultVal = False
        nonValue = True
        if len(relHumidity) != 0:
            try:
                if "Humidity" in relHumidity[2]:
                    relHumid = relHumidity[7:]
                    checkData4 = True
                    self.headerIncl = True
                    self.headerStr = relHumidity[0:7]
            except: pass
            if checkData4 == False:
                for item in relHumidity:
                    try:
                        if 0 <= float(item) <= 100:
                            relHumid.append(float(item))
                            checkData4 = True
                        else: nonValue = False
                    except: checkData4 = False
            if nonValue == False: checkData4 = False
            if len(relHumid) > 1: humidMultVal = True
            if checkData4 == False:
                raise Exception('relHumidity input does not contain valid value.')

        # Check lenth of the metabolicRate list and evaluate the contents.
        checkData5 = False
        metRate = []
        metMultVal = False
        nonVal = True
        if len(metabolicRate) != 0:
            for item in metabolicRate:
                try:
                    if 0.5 <= float(item) <= 10:
                        metRate.append(float(item))
                        checkData5 = True
                    else: nonVal = False
                except: checkData5 = False
            if len(metRate) > 0: checkData5 = True
            if nonVal == False: checkData5 = False
            if len(metRate) > 1: metMultVal = True
            if checkData5 == False:
                raise Exception('metabolicRate input does not contain valid value. Note that metabolicRate must be a value between 0.5 and 10. Any thing outside of that is frankly not human.')
        else:
            checkData5 = True
            metRate = [1]

        # Check lenth of the clothingValues list and evaluate the contents.
        checkData6 = False
        cloLevel = []
        cloMultVal = False
        noVal = True
        if len(clothingValues) != 0:
            for item in clothingValues:
                try:
                    if 0 <= float(item):
                        cloLevel.append(float(item))
                        checkData6 = True
                    else: noVal = False
                except: checkData6 = False
            if noVal == False: checkData6 = False
            if len(cloLevel) > 1: cloMultVal = True
            if checkData6 == False:
                raise Exception('clothingValues input does not contain valid value. Note that clothingValues must be greater than 0.')
        else:
            checkData6 = True
            cloLevel = [1]

        # Check lenth of the externalWork list and evaluate the contents.
        checkData7 = False
        exWork = []
        exMultVal = False
        noVal = True
        if len(externalWork) != 0:
            for item in externalWork:
                try:
                    if 0 <= float(item):
                        exWork.append(float(item))
                        checkData7 = True
                    else: noVal = False
                except: checkData7 = False
            if noVal == False: checkData7 = False
            if len(cloLevel) > 1: exMultVal = True
            if checkData7 == False:
                raise Exception('externalWork input does not contain valid value. Note that externalWork must be greater than 0.')
        else:
            checkData6 = True
            exWork = [0]


        # Finally, for those lists of length greater than 1, check to make sure that they are all the same length.
        checkData = False
        if checkData1 == True and checkData2 == True and checkData3 == True and checkData4 == True and checkData5 == True and checkData6 == True and checkData7 == True:
            if airMultVal == True or radMultVal == True or windMultVal == True or humidMultVal == True or metMultVal == True or cloMultVal == True or exMultVal == True:
                listLenCheck = []
                if airMultVal == True: listLenCheck.append(len(airTemp))
                if radMultVal == True: listLenCheck.append(len(radTemp))
                if windMultVal == True: listLenCheck.append(len(windSpeed))
                if humidMultVal == True: listLenCheck.append(len(relHumid))
                if metMultVal == True: listLenCheck.append(len(metRate))
                if cloMultVal == True: listLenCheck.append(len(cloLevel))
                if exMultVal == True: listLenCheck.append(len(exWork))

                if all(x == listLenCheck[0] for x in listLenCheck) == True:
                    checkData = True
                    calcLength = listLenCheck[0]


                    if airMultVal == False: airTemp = duplicate(airTemp, calcLength)
                    if radMultVal == False: radTemp = duplicate(radTemp, calcLength)
                    if windMultVal == False: windSpeed = duplicate(windSpeed, calcLength)
                    if humidMultVal == False: relHumid = duplicate(relHumid, calcLength)
                    if metMultVal == False: metRate = duplicate(metRate, calcLength)
                    if cloMultVal == False: cloLevel = duplicatea(cloLevel, calcLength)
                    if exMultVal == False: exWork = duplicate(exWork, calcLength)

                else:
                    calcLength = None
                    raise Exception('If you have put in lists with multiple values, the lengths of these lists must match \n across the parameters or you have a single value for a given parameter to be applied to all values in the list.')
            else:
                checkData = True
                calcLength = 1

        # If everything is good, re-assign the lists of input variables and set the list alignment to true.
        if checkData == True:
            # Assign all of the input values to the PMV comfort model object.
            self.airTemperature = airTemp
            self.radTemperature = radTemp
            self.windSpeed = windSpeed
            self.relHumidity = relHumid
            self.metRate = metRate
            self.cloValues = cloLevel
            self.externalWork = exWork
            # Assign calc length and aligned variable data.
            self.calcLength = calcLength
            self.__isDataAligned = True


    def setComfortPar(self, PPDComfortThresh=10, humidRatioUp=0.03, humidRatioLow=0, stillAirThreshold=0.1):
        """
        Set the parameters of the comfort model including the following:
            PPDComfortThresh = The threshold of the percentage of people dissatisfied (PPD)
                beyond which the conditions are not comfortable.  The default is 10%.
            humidRatioUp = An optional upper boundary of humidity ratio above which conditions
                are considered too humid to be comfortable.  The default is set to 0.03 kg wather/kg air.
            humidRatioUp = An optional lower boundary of humidity ratio below which conditions
                are considered too dry to be comfortable.  The default is set to 0 kg wather/kg air.
            stillAirThreshold = An optional wind speed beyond which the formula for Standard Effective
                Temperature (SET) is used to dtermine PMV/PPD (as opposed to Fanger's original equation).
                The default is set to 0.1 m/s.
        """
        self.comfortPar = {
            'PPDComfortThresh': PPDComfortThresh,
            'humidRatioUp': humidRatioUp,
            'humidRatioLow': humidRatioLow,
            'stillAirThreshold': stillAirThreshold
        }



    # Functions that returns the PPD for a given PMV.
    def findPPD(pmv):
        return 100.0 - 95.0 * math.exp(-0.03353 * pow(pmv, 4.0) - 0.2179 * pow(pmv, 2.0))

    # Original Fanger function to compute PMV.
    def comfPMV(self, ta, tr, vel, rh, met, clo, wme):
        # returns [pmv, ppd]
        # ta, air temperature (C)
        # tr, mean radiant temperature (C)
        # vel, relative air velocity (m/s)
        # rh, relative humidity (%) Used only this way to input humidity level
        # met, metabolic rate (met)
        # clo, clothing (clo)
        # wme, external work, normally around 0 (met)

        pa = rh * 10 * math.exp(16.6536 - 4030.183 / (ta + 235))

        icl = 0.155 * clo  # thermal insulation of the clothing in M2K/W
        m = met * 58.15  # metabolic rate in W/M2
        w = wme * 58.15  # external work in W/M2
        mw = m - w  # internal heat production in the human body
        if (icl <= 0.078): fcl = 1 + (1.29 * icl)
        else: fcl = 1.05 + (0.645 * icl)

        # heat transf. coeff. by forced convection
        hcf = 12.1 * math.sqrt(vel)
        taa = ta + 273
        tra = tr + 273
        tcla = taa + (35.5 - ta) / (3.5 * icl + 0.1)

        p1 = icl * fcl
        p2 = p1 * 3.96
        p3 = p1 * 100
        p4 = p1 * taa
        p5 = (308.7 - 0.028 * mw) + (p2 * math.pow(tra / 100, 4))
        xn = tcla / 100
        xf = tcla / 50
        eps = 0.00015

        n = 0
        while abs(xn - xf) > eps:
            xf = (xf + xn) / 2
            hcn = 2.38 * math.pow(abs(100.0 * xf - taa), 0.25)
            if (hcf > hcn):
                hc = hcf
            else:
                hc = hcn
            xn = (p5 + p4 * hc - p2 * math.pow(xf, 4)) / (100 + p3 * hc)
            n += 1
            if (n > 150):
                print 'Max iterations exceeded'
                return 1


        tcl = 100 * xn - 273

        # heat loss diff. through skin
        hl1 = 3.05 * 0.001 * (5733 - (6.99 * mw) - pa)
        # heat loss by sweating
        if mw > 58.15:
            hl2 = 0.42 * (mw - 58.15)
        else:
            hl2 = 0
        # latent respiration heat loss
        hl3 = 1.7 * 0.00001 * m * (5867 - pa)
        # dry respiration heat loss
        hl4 = 0.0014 * m * (34 - ta)
        # heat loss by radiation
        hl5 = 3.96 * fcl * (math.pow(xn, 4) - math.pow(tra / 100, 4))
        # heat loss by convection
        hl6 = fcl * hc * (tcl - ta)

        ts = 0.303 * math.exp(-0.036 * m) + 0.028
        pmv = ts * (mw - hl1 - hl2 - hl3 - hl4 - hl5 - hl6)
        ppd = self.findPPD(pmv)

        r = []
        r.append(pmv)
        r.append(ppd)

        return r

    # Function to compute standard effective temperature (SET).
    def comfPierceSET(self, ta, tr, vel, rh, met, clo, wme):
        # returns standard effective temperature

        # Key initial variables.
        VaporPressure = (rh * psychrometrics.findSaturatedVaporPressureTorr(ta)) / 100
        AirVelocity = max(vel, 0.1)
        KCLO = 0.25
        BODYWEIGHT = 69.9
        BODYSURFACEAREA = 1.8258
        METFACTOR = 58.2
        SBC = 0.000000056697  # Stefan-Boltzmann constant (W/m2K4)
        CSW = 170
        CDIL = 120
        CSTR = 0.5

        TempSkinNeutral = 33.7  # setpoint (neutral) value for Tsk
        TempCoreNeutral = 36.49  # setpoint value for Tcr
        TempBodyNeutral = 36.49  # setpoint for Tb (.1*TempSkinNeutral + .9*TempCoreNeutral)
        SkinBloodFlowNeutral = 6.3  # neutral value for SkinBloodFlow

        # INITIAL VALUES - start of 1st experiment
        TempSkin = TempSkinNeutral
        TempCore = TempCoreNeutral
        SkinBloodFlow = SkinBloodFlowNeutral
        MSHIV = 0.0
        ALFA = 0.1
        ESK = 0.1 * met

        # Start new experiment here (for graded experiments)
        # UNIT CONVERSIONS (from input variables)

        p = 101325.0 / 1000  # This variable is the pressure of the atmosphere in kPa and was taken from the psychrometrics.js file of the CBE comfort tool.

        PressureInAtmospheres = p * 0.009869
        LTIME = 60
        RCL = 0.155 * clo
        # AdjustICL(RCL, Conditions);  TH: I don't think this is used in the software

        FACL = 1.0 + 0.15 * clo  # % INCREASE IN BODY SURFACE AREA DUE TO CLOTHING
        LR = 2.2 / PressureInAtmospheres  # Lewis Relation is 2.2 at sea level
        RM = met * METFACTOR
        M = met * METFACTOR

        if clo <= 0:
            WCRIT = 0.38 * pow(AirVelocity, -0.29)
            ICL = 1.0
        else:
            WCRIT = 0.59 * pow(AirVelocity, -0.08)
            ICL = 0.45

        CHC = 3.0 * pow(PressureInAtmospheres, 0.53)
        CHCV = 8.600001 * pow((AirVelocity * PressureInAtmospheres), 0.53)
        CHC = max(CHC, CHCV)

        # initial estimate of Tcl
        CHR = 4.7
        CTC = CHR + CHC
        RA = 1.0 / (FACL * CTC)  # resistance of air layer to dry heat transfer
        TOP = (CHR * tr + CHC * ta) / CTC
        TCL = TOP + (TempSkin - TOP) / (CTC * (RA + RCL))

        # ========================  BEGIN ITERATION
        #
        # Tcl and CHR are solved iteratively using: H(Tsk - To) = CTC(Tcl - To),
        # where H = 1/(Ra + Rcl) and Ra = 1/Facl*CTC

        TCL_OLD = TCL
        TIME = range(LTIME)
        flag = True
        for TIM in TIME:
            if flag == True:
                while abs(TCL - TCL_OLD) > 0.01:
                    TCL_OLD = TCL
                    CHR = 4.0 * SBC * pow(((TCL + tr) / 2.0 + 273.15), 3.0) * 0.72
                    CTC = CHR + CHC
                    RA = 1.0 / (FACL * CTC)  # resistance of air layer to dry heat transfer
                    TOP = (CHR * tr + CHC * ta) / CTC
                    TCL = (RA * TempSkin + RCL * TOP) / (RA + RCL)
            flag = False
            DRY = (TempSkin - TOP) / (RA + RCL)
            HFCS = (TempCore - TempSkin) * (5.28 + 1.163 * SkinBloodFlow)
            ERES = 0.0023 * M * (44.0 - VaporPressure)
            CRES = 0.0014 * M * (34.0 - ta)
            SCR = M - HFCS - ERES - CRES - wme
            SSK = HFCS - DRY - ESK
            TCSK = 0.97 * ALFA * BODYWEIGHT
            TCCR = 0.97 * (1 - ALFA) * BODYWEIGHT
            DTSK = (SSK * BODYSURFACEAREA) / (TCSK * 60.0)  # deg C per minute
            DTCR = SCR * BODYSURFACEAREA / (TCCR * 60.0)  # deg C per minute
            TempSkin = TempSkin + DTSK
            TempCore = TempCore + DTCR
            TB = ALFA * TempSkin + (1 - ALFA) * TempCore
            SKSIG = TempSkin - TempSkinNeutral
            WARMS = (SKSIG > 0) * SKSIG
            COLDS = ((-1.0 * SKSIG) > 0) * (-1.0 * SKSIG)
            CRSIG = (TempCore - TempCoreNeutral)
            WARMC = (CRSIG > 0) * CRSIG
            COLDC = ((-1.0 * CRSIG) > 0) * (-1.0 * CRSIG)
            BDSIG = TB - TempBodyNeutral
            WARMB = (BDSIG > 0) * BDSIG
            SkinBloodFlow = (SkinBloodFlowNeutral + CDIL * WARMC) / (1 + CSTR * COLDS)
            if SkinBloodFlow > 90.0: SkinBloodFlow = 90.0
            if SkinBloodFlow < 0.5: SkinBloodFlow = 0.5
            REGSW = CSW * WARMB * math.exp(WARMS / 10.7)
            if REGSW > 500.0: REGSW = 500.0
            ERSW = 0.68 * REGSW
            REA = 1.0 / (LR * FACL * CHC)  # evaporative resistance of air layer
            RECL = RCL / (LR * ICL)  # evaporative resistance of clothing (icl=.45)
            EMAX = (psychrometrics.findSaturatedVaporPressureTorr(TempSkin) - VaporPressure) / (REA + RECL)
            PRSW = ERSW / EMAX
            PWET = 0.06 + 0.94 * PRSW
            EDIF = PWET * EMAX - ERSW
            ESK = ERSW + EDIF
            if PWET > WCRIT:
                PWET = WCRIT
                PRSW = WCRIT / 0.94
                ERSW = PRSW * EMAX
                EDIF = 0.06 * (1.0 - PRSW) * EMAX
                ESK = ERSW + EDIF
            if EMAX < 0:
                EDIF = 0
                ERSW = 0
                PWET = WCRIT
                PRSW = WCRIT
                ESK = EMAX
            ESK = ERSW + EDIF
            MSHIV = 19.4 * COLDS * COLDC
            M = RM + MSHIV
            ALFA = 0.0417737 + 0.7451833 / (SkinBloodFlow + .585417)


        # Define new heat flow terms, coeffs, and abbreviations
        HSK = DRY + ESK  # total heat loss from skin
        RN = M - wme  # net metabolic heat production
        ECOMF = 0.42 * (RN - (1 * METFACTOR))
        if ECOMF < 0.0: ECOMF = 0.0  # from Fanger
        EMAX = EMAX * WCRIT
        W = PWET
        PSSK = psychrometrics.findSaturatedVaporPressureTorr(TempSkin)
        # Definition of ASHRAE standard environment... denoted "S"
        CHRS = CHR
        if met < 0.85:
            CHCS = 3.0
        else:
            CHCS = 5.66 * pow((met - 0.85), 0.39)
            if CHCS < 3.0: CHCS = 3.0

        CTCS = CHCS + CHRS
        RCLOS = 1.52 / ((met - wme / METFACTOR) + 0.6944) - 0.1835
        RCLS = 0.155 * RCLOS
        FACLS = 1.0 + KCLO * RCLOS
        FCLS = 1.0 / (1.0 + 0.155 * FACLS * CTCS * RCLOS)
        IMS = 0.45
        ICLS = IMS * CHCS / CTCS * (1 - FCLS) / (CHCS / CTCS - FCLS * IMS)
        RAS = 1.0 / (FACLS * CTCS)
        REAS = 1.0 / (LR * FACLS * CHCS)
        RECLS = RCLS / (LR * ICLS)
        HD_S = 1.0 / (RAS + RCLS)
        HE_S = 1.0 / (REAS + RECLS)

        # SET* (standardized humidity, clo, Pb, and CHC)
        # determined using Newton's iterative solution
        # FNERRS is defined in the GENERAL SETUP section above

        DELTA = .0001
        dx = 100.0
        X_OLD = TempSkin - HSK / HD_S  # lower bound for SET
        while abs(dx) > .01:
            ERR1 = (HSK - HD_S * (TempSkin - X_OLD) - W * HE_S * (PSSK - 0.5 * psychrometrics.findSaturatedVaporPressureTorr(X_OLD)))
            ERR2 = (HSK - HD_S * (TempSkin - (X_OLD + DELTA)) - W * HE_S * (PSSK - 0.5 * psychrometrics.findSaturatedVaporPressureTorr((X_OLD + DELTA))))
            X = X_OLD - DELTA * ERR1 / (ERR2 - ERR1)
            dx = X - X_OLD
            X_OLD = X

        return X


    def comfPMVElevatedAirspeed(self, ta, tr, vel, rh, met, clo, wme):
        # This function accepts any input conditions (including low air speeds) but will return accurate values if the airspeed is above (>0.15m/s).
        # The function will return the following:
        # pmv : Predicted mean vote
        # ppd : Percent predicted dissatisfied [%]
        # ta_adj: Air temperature adjusted for air speed [C]
        # cooling_effect : The difference between the air temperature and adjusted air temperature [C]
        # set: The Standard Effective Temperature [C] (see below)

        r = []
        set = self.comfPierceSET(ta, tr, vel, rh, met, clo, wme)

        if vel <= self.comfortPar['stillAirThreshold']:
            pmv, ppd = self.comfPMV(ta, tr, vel, rh, met, clo, wme)
            ta_adj = ta
            ce = 0
        else:
            ce_l = 0
            ce_r = 40
            eps = 0.001  # precision of ce
            def fn(ce):
                return (set - self.comfPierceSET(ta - ce, tr - ce, self.comfortPar['stillAirThreshold'], rh, met, clo, wme))

            ce = util.secant(ce_l, ce_r, fn, eps)
            if ce == 'NaN':
                ce = util.bisect(ce_l, ce_r, fn, eps, 0)

            pmv, ppd = self.comfPMV(ta - ce, tr - ce, self.comfortPar['stillAirThreshold'], rh, met, clo, wme)
            ta_adj = ta - ce

        r.append(pmv)
        r.append(ppd)
        r.append(set)
        r.append(ta_adj)
        r.append(ce)

        return r



    def getFullPMV(self):
        """
        Calculates all PMV variables for the assigned input data
        Returns the following four lists:
            _pmv = Predicted Mean Vote
            _ppd = Percentage of People Dissatisfied [%]
            _set = Standard Effective Temperature [C]
            _isComfortable = 1 if comforable, 0 if uncomfortable
            _discomfReason = -2 if too cold, -1 if too dry, 0 if comfortable, 1 if too humid, 2 if too hot

        The function will also compute the folowing properties but will not return them from the function:
            _ta_adj: Air temperature adjusted for air speed [C]
            _cooling_effect: The difference between the air temperature and adjusted air temperature [C]
        """

        # Check the data to make sure that all lists are aligned.
        if self.__isDataAligned == False:
            self.checkAndAlignLists(self.airTemperature, self.radTemperature, self.windSpeed, self.relHumidity, self.metRate, self.cloValues, self.externalWork)

        # If the incoming data has a header on it, add headers to the final lists.


        # Compute pmv for each of the values in the list.
        for i in range(self.calcLength):
            ipmv, ippd, iset, ita_adj, ice = self.comfPMVElevatedAirspeed(self.airTemperature[i], self.radTemperature[i], self.windSpeed[i], self.relHumidity[i], self.metRate[i], self.cloValues[i], self.externalWork[i])
            self._pmv.append(ipmv)
            self._ppd.append(ippd)
            self._set.append(iset)
            self._ta_adj.append(ita_adj)
            self._cooling_effect.append(ice)

            if self.comfortPar['humidRatioUp'] != 0.03 or self.comfortPar['humidRatioLow'] != 0:
                HR, vapPress, satPress = psychrometrics.calcHumidRatio(self.airTemperature[i], self.relHumidity[i])
                if ippd > self.comfortPar['PPDComfortThresh']:
                    self._isComfortable.append(0)
                    if ipmv > 0: self._discomfReason.append(2)
                    else: self._discomfReason.append(-2)
                elif HR > self.comfortPar['humidRatioUp']:
                    self._isComfortable.append(0)
                    self._discomfReason.append(1)
                elif HR < self.comfortPar['humidRatioLow']:
                    self._isComfortable.append(0)
                    self._discomfReason.append(-1)
                else:
                    self._isComfortable.append(1)
                    self._discomfReason.append(0)
            else:
                if ippd > self.comfortPar['PPDComfortThresh']:
                    self._isComfortable.append(0)
                    if ipmv > 0: self._discomfReason.append(2)
                    else: self._discomfReason.append(-2)
                else: self._isComfortable.append(1)

        return self._pmv, self._ppd, self._set, self._isComfortable, self._discomfReason




    @property
    def isDataAligned(self):
        """
        Boolean value that states wether the input data is aligned.
            True = aligned
            False = not aligned (run the checkAndAlignLists function to align the data)
        """
        return self.__isDataAligned

    @property
    def comfortPar(self):
        """
        Dictionary of parameters that dictate whether a given set of conditions is comfortable.
        These include:
            PPDComfortThresh = The threshold of the percentage of people dissatisfied (PPD)
                beyond which the conditions are not comfortable.  The default is 10%.
            humidRatioUp = An optional upper boundary of humidity ratio above which conditions
                are considered too humid to be comfortable.  The default is set to 0.03 kg wather/kg air.
            humidRatioUp = An optional lower boundary of humidity ratio below which conditions
                are considered too dry to be comfortable.  The default is set to 0 kg wather/kg air.
            stillAirThreshold = An optional wind speed beyond which the formula for Standard Effective
                Temperature (SET) is used to dtermine PMV/PPD (as opposed to Fanger's original equation).
                The default is set to 0.1 m/s.
        """
        return self.comfortPar

    @property
    def _pmv(self):
        """
        List of predicted mean vote (PMV) values for the input conditions.
        PMV is a seven-point scale from cold (-3) to hot (+3) that was used in comfort surveys of P.O. Fanger.
        Each interger value of the scale indicates the following:
            -3 = Cold
            -2 = Cool
            -1 = Slightly Cool
             0 = Neutral
            +1 = Slightly Warm
            +2 = Warm
            +3 = Hot
        Exceeding +1 will result in an uncomfortably warm occupant while dropping below -1 will result in an uncomfortably cool occupant.
        For detailed information on the PMV scale, see P.O. Fanger's original paper:
        Fanger, P Ole (1970). Thermal Comfort: Analysis and applications in environmental engineering.
        """
        return self._pmv

    @property
    def _ppd(self):
        """
        List of percentage of people dissatisfied (PPD) values for the input conditions.
        Specifically, this is defined by the percent of people who would have a PMV less than -1 or greater than +1 under the conditions.
        Note that, with this model, the best possible PPD achievable is 5% and most engineers just aim to have a PPD below 10%.
        """
        return self._ppd

    @property
    def _set(self):
        """
        List of standard effective temperature (SET) values for the input conditions.
        Specifically, this is defined by the percent of people who would have a PMV less than -1 or greater than +1 under the conditions.
        Note that, with this model, the best possible PPD achievable is 5% and most engineers just aim to have a PPD below 10%.
        """
        return self._set

    @property
    def _isComfortable(self):
        """
        List of integer values that show whether the input conditions are comfortable.  Values are one of the following:
            0 = uncomfortable
            1 = comfortable
        """
        return self._isComfortable

    @property
    def _discomfReason(self):
        """
        List of integer values that the reason for discomfort.  Values are one of the following:
            -2 = too cold
            -1 = too dry
             0 = comfortable
             1 = too humid
             2 = too hot
        """
        return self._discomfReason

    @property
    def _ta_adj(self):
        """
        List of air temperatures adjusted for air speed in [C].
        """
        return self._ta_adj

    @property
    def _cooling_effect(self):
        """
        The difference between the air temperature and adjusted air temperature [C].
        """
        return self._cooling_effect
