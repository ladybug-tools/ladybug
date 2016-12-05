"""PMV Comfort object."""
import math
from collections import Iterable
from .comfortBase import ComfortModel
from ..psychrometrics import findHumidRatio
from ..psychrometrics import findSaturatedVaporPressureTorr
from ..rootFinding import secant
from ..rootFinding import bisect
from ..listoperations import duplicate
from ..epw import EPW


class PMV(ComfortModel):
    """
    PMV Comfort Object.

    Usage:
        from ladybug.comfort.pmv import PMV

        # Compute PMV for a single set of values.
        myPmvComf = PMV.fromIndividualValues(26, 26, 0.75, 80, 1.1, 0.5)
        pmv = myPmvComf.pmv

        # Compute PMV for a list of data.
        airTemp = [10, 12, 15, 18, 19]
        relHumid = [75, 70, 60, 50, 45]
        myPmvComf = PMV(airTemp, [], [], relHumid)
        pmv = myPmvComf.pmv

        # Compute PMV for all hours of an EPW file.
        epwFileAddress = "C:/ladybug/New_York_J_F_Kennedy_IntL_Ar_NY_USA/New_York_J_F_Kennedy_IntL_Ar_NY_USA.epw"
        myPmvComf = PMV.fromEPWFile(epwFileAddress, 1.4, 1.0)
        pmv = myPmvComf.pmv

    """

    def __init__(self, airTemperature=None, radTemperature=[], windSpeed=[],
                 relHumidity=[], metRate=[], cloValue=[], externalWork=[]):
        """Initialize a PMV comfort object from lists of PMV inputs."""
        # Assign all of the input values to the PMV comfort model object.
        # And assign defaults if nothing has been connected.
        self.airTemperature = airTemperature

        if radTemperature != []:
            self.__radTemperature = radTemperature
        else:
            self.__radTemperature = self.__airTemperature

        if windSpeed != []:
            self.__windSpeed = windSpeed
        else:
            self.__windSpeed = [0]
        if relHumidity != []:
            self.__relHumidity = relHumidity
        else:
            self.__relHumidity = [50]
        if metRate != []:
            self.__metRate = metRate
        else:
            self.__metRate = [1.1]
        if cloValue != []:
            self.__cloValue = cloValue
        else:
            self.__cloValue = [0.85]
        if externalWork != []:
            self.__externalWork = externalWork
        else:
            self.__externalWork = [0]

        # Default variables that all comfort models have.
        self.__calcLength = None
        self.__isDataAligned = False
        self.__isRecalcNeeded = True

        self.__headerIncl = False
        self.__headerStr = []
        self.__singleVals = False

        # Set default comfort parameters for the PMV model.
        self.__PPDComfortThresh = 10.0
        self.__humidRatioUp = 0.03
        self.__humidRatioLow = 0
        self.__stillAirThreshold = 0.1

        # Set blank values for the key returns of the class.
        self.__pmv = []
        self.__ppd = []
        self.__set = []
        self.__isComfortable = []
        self.__discomfReason = []
        self.__taAdj = []
        self.__coolingEffect = []

    @classmethod
    def fromIndividualValues(cls, airTemperature=20.0, radTemperature=None,
                             windSpeed=0.0, relHumidity=50.0, metRate=1.1,
                             cloValue=0.85, externalWork=0.0):
        """Create a PMV comfort object from individual values."""
        if airTemperature is None:
            airTemperature = 20.0
        if radTemperature is None:
            radTemperature = airTemperature
        if windSpeed is None:
            windSpeed = 0.0
        if relHumidity is None:
            relHumidity = 0.0

        pmvModel = cls([float(airTemperature)], [float(radTemperature)], [float(windSpeed)], [float(relHumidity)], [float(metRate)], [float(cloValue)], [float(externalWork)])
        pmvModel.__singleVals = True
        pmvModel.__isDataAligned = True
        pmvModel.__calcLength = 1

        return pmvModel

    @classmethod
    def fromEPWFile(cls, epwFileAddress, metRate=1.1, cloValue=0.85,
                    externalWork=0.0, inclHeader=True):
        """Create a PMV comfort object from the conditions within an EPW file.

        Args:
            metRate: A value representing the metabolic rate of the human subject in met.
                1 met = resting seated. If list is empty, default is set to 1 met.
            cloValue: A lvalue representing the clothing level of the human subject in clo.
                1 clo = three-piece suit. If list is empty, default is set to 1 clo.
            externalWork: A value representing the work done by the human subject in met.
                1 met = resting seated. If list is empty, default is set to 0 met.
            header: set to "True" to have a ladybug header included in the output and set to
                "False" to remove the header.  The default is set to "True."
        """
        epwData = EPW(epwFileAddress)
        return cls(epwData.dryBulbTemperature.values(header=inclHeader), epwData.dryBulbTemperature.values(header=inclHeader), epwData.windSpeed.values(header=inclHeader), epwData.relativeHumidity.values(header=inclHeader), [metRate], [cloValue], [externalWork])

    @property
    def isReCalculationNeeded(self):
        """Boolean value that indicates whether the comfort values need to be re-computed.

        Returns:
            True = re-calculation is needed before comfort values can be output.
            False = no re-calculation is needed.
        """
        return self.__isRecalcNeeded

    @property
    def isDataAligned(self):
        """
        Boolean value that indicates whether the input data is aligned.
            True = aligned
            False = not aligned (run the _checkAndAlignLists function to align the data)
        """
        return self.__isDataAligned

    @property
    def isHeaderIncluded(self):
        """
        Boolean value that indicates whether a header will be output on the results.
            True = header included.
            False = header not included.
        """
        return self.__headerIncl

    @property
    def singleValues(self):
        """
        Boolean value that indicates whether single values or a list of values will be output.
            True = single values output.
            False = lists of values output.
        """
        return self.__singleVals

    @property
    def airTemperature(self):
        """
        A number or list of numbers representing dry bulb temperatures in degrees Celcius.
        This can be a list with a LB header on it.  If list is empty, default is set to 20 C.
        """
        return self.__airTemperature

    @airTemperature.setter
    def airTemperature(self, value):

        self.__airTemperature = [20] if not value else value

        if not isinstance(self.__airTemperature, Iterable):
            self.__airTemperature = [self.__airTemperature]

        self.__isDataAligned = False
        self.__isRecalcNeeded = True

    @property
    def radTemperature(self):
        """
        A number or list of numbers representing mean radiant temperatures in degrees Celcius.
        This list can have a LB header on it.  If list is empty, default is set be the same as __airTemperature.
        """
        return self.__radTemperature

    @radTemperature.setter
    def radTemperature(self, value):
        try:
            self.__radTemperature = [float(value)]
        except:
            self.__radTemperature = value
        self.__isDataAligned = False
        self.__isRecalcNeeded = True

    @property
    def windSpeed(self):
        """
        A number or list of numbers representing wind speeds in m/s. This list can have a LB header on it.
        If list is empty, default is set to 0 m/s.
        """
        return self.__windSpeed

    @windSpeed.setter
    def windSpeed(self, value):
        try:
            self.__windSpeed = [float(value)]
        except:
            self.__windSpeed = value
        self.__isDataAligned = False
        self.__isRecalcNeeded = True

    @property
    def relHumidity(self):
        """
        A number or list of numbers representing relative humidities in %. This list can have a LB header on it.
        If list is empty, default is set to 50%.
        """
        return self.__relHumidity

    @relHumidity.setter
    def relHumidity(self, value):
        try:
            self.__relHumidity = [float(value)]
        except:
            self.__relHumidity = value
        self.__isDataAligned = False
        self.__isRecalcNeeded = True

    @property
    def metRate(self):
        """
        A number or list of numbers representing the metabolic rate of the human subject in met.
        1 met = resting seated. This list can have a LB header on it.
        If list is empty, default is set to 1.1 met.
        """
        return self.__metRate

    @metRate.setter
    def metRate(self, value):
        try:
            self.__metRate = [float(value)]
        except:
            self.__metRate = value
        self.__isDataAligned = False
        self.__isRecalcNeeded = True

    @property
    def cloValue(self):
        """
        A number or list of numbers representing the clothing level of the human subject in clo.
        1 clo = three-piece suit. This list can have a LB header on it.
        If list is empty, default is set to 0.85 clo.
        """
        return self.__cloValue

    @cloValue.setter
    def cloValue(self, value):
        try:
            self.__cloValue = [float(value)]
        except:
            self.__cloValue = value
        self.__isDataAligned = False
        self.__isRecalcNeeded = True

    @property
    def externalWork(self):
        """
        A number or list of numbers representing the work done by the human subject in met.
        This list can have a LB header on it.
        If list is empty, default is set to 0 met.
        """
        return self.__externalWork

    @externalWork.setter
    def externalWork(self, value):
        try:
            self.__externalWork = [float(value)]
        except:
            self.__externalWork = value
        self.__isDataAligned = False
        self.__isRecalcNeeded = True

    @property
    def PPDComfortThresh(self):
        """
        A number representing the threshold of the percentage of people dissatisfied (PPD)
        beyond which the conditions are not comfortable.  The default is 10%.
        """
        return self.__PPDComfortThresh

    @PPDComfortThresh.setter
    def PPDComfortThresh(self, value):
        self.__PPDComfortThresh = value
        self.__isRecalcNeeded = True

    @property
    def humidRatioUp(self):
        """
        A number representing the upper boundary of humidity ratio above which conditions are considered too
        humid to be comfortable.  The default is set to 0.03 kg wather/kg air.
        """
        return self.__humidRatioUp

    @humidRatioUp.setter
    def humidRatioUp(self, value):
        self.__humidRatioUp = value
        self.__isRecalcNeeded = True

    @property
    def humidRatioLow(self):
        """
        A number representing the lower boundary of humidity ratio below which conditions are considered too
        dry to be comfortable.  The default is set to 0 kg wather/kg air.
        """
        return self.__humidRatioUp

    @humidRatioLow.setter
    def humidRatioLow(self, value):
        self.__humidRatioLow = value
        self.__isRecalcNeeded = True

    @property
    def stillAirThreshold(self):
        """
        A number representing the wind speed beyond which the formula for Standard Effective Temperature (SET)
        is used to dtermine PMV/PPD (as opposed to Fanger's original equation).
        The default is set to 0.1 m/s.
        """
        return self.__humidRatioUp

    @stillAirThreshold.setter
    def stillAirThreshold(self, value):
        self.__stillAirThreshold = value
        self.__isRecalcNeeded = True

    def setComfortPar(self, PPDComfortThresh=10, humidRatioUp=0.03, humidRatioLow=0, stillAirThreshold=0.1):
        """
        Set all of the comfort parameters of the comfort model at once.  These are:
            PPDComfortThresh
            humidRatioUp
            humidRatioLow
            stillAirThreshold
        """
        self.__PPDComfortThresh = PPDComfortThresh
        self.__humidRatioUp = humidRatioUp
        self.__humidRatioLow = humidRatioLow
        self.__stillAirThreshold = stillAirThreshold

        self.__isRecalcNeeded = True

    def _checkAndAlignLists(self):
        """
        Checks to be sure that the lists of PMV input variables are aligned and fills in defaults where possible.
        """
        # Check each list to be sure that the contents are what we want.
        checkData1, airTemp, airMultVal = self._checkInputList(self.__airTemperature, [20], "airTemperature", "Temperature")
        checkData2, radTemp, radMultVal = self._checkInputList(self.__radTemperature, airTemp, "radTemperature", "Temperature")
        checkData3, windSpeed, windMultVal = self._checkInputList(self.__windSpeed, [0.0], "windSpeed", "Wind Speed")
        checkData4, relHumid, humidMultVal = self._checkInputList(self.__relHumidity, [50.0], "relHumidity", "Humidity")
        checkData5, metRate, metMultVal = self._checkInputList(self.__metRate, [1.1], "metabolicRate", "Metabolic")
        checkData6, cloLevel, cloMultVal = self._checkInputList(self.__cloValue, [0.85], "clothingValue", "Clothing")
        checkData7, exWork, exMultVal = self._checkInputList(self.__externalWork, [0.0], "externalWork", "Work")

        # Finally, for those lists of length greater than 1, check to make sure that they are all the same length.
        checkData = False
        if checkData1 is True and checkData2 is True and checkData3 is True and checkData4 is True and checkData5 is True and checkData6 is True and checkData7 is True:
            if airMultVal is True or radMultVal is True or windMultVal is True or humidMultVal is True or metMultVal is True or cloMultVal is True or exMultVal is True:
                listLenCheck = []
                if airMultVal is True:
                    listLenCheck.append(len(airTemp))
                if radMultVal is True:
                    listLenCheck.append(len(radTemp))
                if windMultVal is True:
                    listLenCheck.append(len(windSpeed))
                if humidMultVal is True:
                    listLenCheck.append(len(relHumid))
                if metMultVal is True:
                    listLenCheck.append(len(metRate))
                if cloMultVal is True:
                    listLenCheck.append(len(cloLevel))
                if exMultVal is True:
                    listLenCheck.append(len(exWork))

                if all(x == listLenCheck[0] for x in listLenCheck) is True:
                    checkData = True
                    self.__calcLength = listLenCheck[0]

                    if airMultVal is False:
                        airTemp = duplicate(airTemp[0], self.__calcLength)
                    if radMultVal is False:
                        radTemp = duplicate(radTemp[0], self.__calcLength)
                    if windMultVal is False:
                        windSpeed = duplicate(windSpeed[0], self.__calcLength)
                    if humidMultVal is False:
                        relHumid = duplicate(relHumid[0], self.__calcLength)
                    if metMultVal is False:
                        metRate = duplicate(metRate[0], self.__calcLength)
                    if cloMultVal is False:
                        cloLevel = duplicate(cloLevel[0], self.__calcLength)
                    if exMultVal is False:
                        exWork = duplicate(exWork[0], self.__calcLength)

                else:
                    self.__calcLength = None
                    raise Exception('If you have put in lists with multiple values, the lengths of these lists must match \n across the parameters or you have a single value for a given parameter to be applied to all values in the list.')
            else:
                checkData = True
                self.__calcLength = 1

        # If everything is good, re-assign the lists of input variables and set the list alignment to true.
        if checkData is True:
            # Assign all of the input values to the PMV comfort model object.
            self.__airTemperature = airTemp
            self.__radTemperature = radTemp
            self.__windSpeed = windSpeed
            self.__relHumidity = relHumid
            self.__metRate = metRate
            self.__cloValue = cloLevel
            self.__externalWork = exWork
            # Set the alighed data value to true.
            self.__isDataAligned = True
            self.__isRecalcNeeded = True

    @staticmethod
    def findPPD(pmv):
        """
        Args:
            pmv: The predicted mean vote (PMV) for which you want to know the PPD.

        Returns:
            ppd: The percentage of people dissatisfied (PPD) for the input PMV.
        """
        return 100.0 - 95.0 * math.exp(-0.03353 * pow(pmv, 4.0) - 0.2179 * pow(pmv, 2.0))

    @staticmethod
    def findPMV(ppd, ppdError=0.001):
        """
        Args:
            ppd: The percentage of people dissatisfied (PPD) for which you want to know the possible PMV.
            ppdError: The acceptable error in meeting the target PPD.  The default is set to 0.001.

        Returns:
            pmv: A list with the two predicted mean vote (PMV) values that produces the input PPD.
        """
        if not ppd < 5:
            pmvLow = -3
            pmvMid = 0
            pmvHi = 3

            def fn(pmv):
                return ((100.0 - 95.0 * math.exp(-0.03353 * pow(pmv, 4.0) - 0.2179 * pow(pmv, 2.0))) - ppd)

            # Solve for the missing lower PMV value.
            pmvLowSolution = secant(pmvLow, pmvMid, fn, ppdError)
            if pmvLowSolution == 'NaN':
                pmvLowSolution = bisect(pmvLow, pmvMid, fn, ppdError)
            # Solve for the missing higher PMV value.
            pmvHiSolution = secant(pmvMid, pmvHi, fn, ppdError)
            if pmvHiSolution == 'NaN':
                pmvHiSolution = bisect(pmvMid, pmvHi, fn, ppdError)

            return [pmvLowSolution, pmvHiSolution]
        else:
            raise Exception('A ppd lower than 5% is not achievable with the PMV model.')

    @staticmethod
    def comfPMV(ta, tr, vel, rh, met, clo, wme):
        """
        Original Fanger function to compute PMV.  Only intended for use with low air speeds (<0.1 m/s).

        Args:
            ta: air temperature (C)
            tr: mean radiant temperature (C)
            vel: relative air velocity (m/s)
            rh: relative humidity (%) Used only this way to input humidity level
            met: metabolic rate (met)
            clo: clothing (clo)
            wme: external work, normally around 0 (met)

        Returns:
            pmv: predicted mean vote
            ppd: percentage of people dissatisfied.
        """

        pa = rh * 10 * math.exp(16.6536 - 4030.183 / (ta + 235))

        icl = 0.155 * clo  # thermal insulation of the clothing in M2K/W
        m = met * 58.15  # metabolic rate in W/M2
        w = wme * 58.15  # external work in W/M2
        mw = m - w  # internal heat production in the human body
        if (icl <= 0.078):
            fcl = 1 + (1.29 * icl)
        else:
            fcl = 1.05 + (0.645 * icl)

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
        ppd = 100.0 - 95.0 * math.exp(-0.03353 * pow(pmv, 4.0) - 0.2179 * pow(pmv, 2.0))

        r = []
        r.append(pmv)
        r.append(ppd)

        return r

    @staticmethod
    def comfPierceSET(ta, tr, vel, rh, met, clo, wme):
        """
        Args:
            ta, air temperature (C)
            tr, mean radiant temperature (C)
            vel, relative air velocity (m/s)
            rh, relative humidity (%) Used only this way to input humidity level
            met, metabolic rate (met)
            clo, clothing (clo)
            wme, external work, normally around 0 (met)

        Returns:
            set, standard effective temperature
        """

        # Key initial variables.
        VaporPressure = (rh * findSaturatedVaporPressureTorr(ta)) / 100
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
            if flag is True:
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
            if SkinBloodFlow > 90.0:
                SkinBloodFlow = 90.0
            if SkinBloodFlow < 0.5:
                SkinBloodFlow = 0.5
            REGSW = CSW * WARMB * math.exp(WARMS / 10.7)
            if REGSW > 500.0:
                REGSW = 500.0
            ERSW = 0.68 * REGSW
            REA = 1.0 / (LR * FACL * CHC)  # evaporative resistance of air layer
            RECL = RCL / (LR * ICL)  # evaporative resistance of clothing (icl=.45)
            EMAX = (findSaturatedVaporPressureTorr(TempSkin) - VaporPressure) / (REA + RECL)
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
        if ECOMF < 0.0:
            ECOMF = 0.0  # from Fanger
        EMAX = EMAX * WCRIT
        W = PWET
        PSSK = findSaturatedVaporPressureTorr(TempSkin)
        # Definition of ASHRAE standard environment... denoted "S"
        CHRS = CHR
        if met < 0.85:
            CHCS = 3.0
        else:
            CHCS = 5.66 * pow((met - 0.85), 0.39)
            if CHCS < 3.0:
                CHCS = 3.0

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
            ERR1 = (HSK - HD_S * (TempSkin - X_OLD) - W * HE_S * (PSSK - 0.5 * findSaturatedVaporPressureTorr(X_OLD)))
            ERR2 = (HSK - HD_S * (TempSkin - (X_OLD + DELTA)) - W * HE_S * (PSSK - 0.5 * findSaturatedVaporPressureTorr((X_OLD + DELTA))))
            X = X_OLD - DELTA * ERR1 / (ERR2 - ERR1)
            dx = X - X_OLD
            X_OLD = X

        return X

    def _comfPMVElevatedAirspeed(self, ta, tr, vel, rh, met, clo, wme):
        """
        This function will return accurate values if the airspeed is above the sillAirThreshold.

        Args:
            ta, air temperature (C)
            tr, mean radiant temperature (C)
            vel, relative air velocity (m/s)
            rh, relative humidity (%) Used only this way to input humidity level
            met, metabolic rate (met)
            clo, clothing (clo)
            wme, external work, normally around 0 (met)

        Returns:
            pmv : Predicted mean vote
            ppd : Percent predicted dissatisfied [%]
            taAdj: Air temperature adjusted for air speed [C]
            coolingEffect : Difference between the air temperature and adjusted air temperature [C]
            set: The Standard Effective Temperature [C] (see below)
        """

        r = {}
        set = self.comfPierceSET(ta, tr, vel, rh, met, clo, wme)

        if vel <= self.__stillAirThreshold:
            pmv, ppd = self.comfPMV(ta, tr, vel, rh, met, clo, wme)
            taAdj = ta
            ce = 0
        else:
            ce_l = 0
            ce_r = 40
            eps = 0.001  # precision of ce

            def fn(ce):
                return (set - self.comfPierceSET(ta - ce, tr - ce, self.__stillAirThreshold, rh, met, clo, wme))

            ce = secant(ce_l, ce_r, fn, eps)
            if ce == 'NaN':
                ce = bisect(ce_l, ce_r, fn, eps, 0)

            pmv, ppd = self.comfPMV(ta - ce, tr - ce, self.__stillAirThreshold, rh, met, clo, wme)
            taAdj = ta - ce

        r['pmv'] = pmv
        r['ppd'] = ppd
        r['set'] = set
        r['taAdj'] = taAdj
        r['ce'] = ce

        return r

    def _calculatePMVParams(self):
        """
        Runs the input conditions through the PMV model to get pmv, ppd, and set.
        """
        # Clear any existing values from the memory.
        self.__pmv = []
        self.__ppd = []
        self.__set = []
        self.__isComfortable = []
        self.__discomfReason = []
        self.__taAdj = []
        self.__coolingEffect = []

        # If the input data has a header, put a header on the output.
        if self.__headerIncl is True:
            self.__pmv.extend(self.buildCustomHeader("Predicted Mean Vote", "PMV"))
            self.__ppd.extend(self.buildCustomHeader("Percentage of People Dissatisfied", "%"))
            self.__set.extend(self.buildCustomHeader("Standard Effective Temperature", "C"))
            self.__isComfortable.extend(self.buildCustomHeader("Comfortable Or Not", "0/1"))
            self.__discomfReason.extend(self.buildCustomHeader("Reason For Discomfort", "-2(cold), -1(dry), 0(comf), 1(humid), 2(hot)"))
            self.__taAdj.extend(self.buildCustomHeader("Perceived Air Temperature With Air Speed", "C"))
            self.__coolingEffect.extend(self.buildCustomHeader("Cooling Effect of air speed", "C"))

        # calculate the pmv, ppd, and set values.
        for i in range(self.__calcLength):
            pmvResult = self._comfPMVElevatedAirspeed(self.__airTemperature[i], self.__radTemperature[i], self.__windSpeed[i], self.__relHumidity[i], self.__metRate[i], self.__cloValue[i], self.__externalWork[i])
            self.__pmv.append(pmvResult['pmv'])
            self.__ppd.append(pmvResult['ppd'])
            self.__set.append(pmvResult['set'])
            self.__taAdj.append(pmvResult['taAdj'])
            self.__coolingEffect.append(pmvResult['ce'])

            # determine whether conditions meet the comfort criteria.
            HR, vapPress, satPress = findHumidRatio(self.__airTemperature[i], self.__relHumidity[i])
            if pmvResult['ppd'] > self.__PPDComfortThresh:
                self.__isComfortable.append(0)
                if pmvResult['pmv'] > 0:
                    self.__discomfReason.append(2)
                else:
                    self.__discomfReason.append(-2)
            elif HR > self.__humidRatioUp:
                self.__isComfortable.append(0)
                self.__discomfReason.append(1)
            elif HR < self.__humidRatioLow:
                self.__isComfortable.append(0)
                self.__discomfReason.append(-1)
            else:
                self.__isComfortable.append(1)
                self.__discomfReason.append(0)

        # Let the class know that we don't need to re-run things unless something changes.
        self.__isRecalcNeeded = False

    @property
    def pmv(self):
        """
        Predicted mean vote (PMV) values for the input conditions.
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

        if not self.__isDataAligned:
            self._checkAndAlignLists()

        if self.__isRecalcNeeded:
            self._calculatePMVParams()

        if self.__singleVals is True:
            return self.__pmv[0]
        else:
            return self.__pmv

    @property
    def ppd(self):
        """
        Percentage of people dissatisfied (PPD) values for the input conditions.
        Specifically, this is defined by the percent of people who would have a PMV less than -1 or greater than +1 under the conditions.
        Note that, with this model, the best possible PPD achievable is 5% and most standards aim to have a PPD below 10%.
        """

        if not self.__isDataAligned:
            self._checkAndAlignLists()

        if self.__isRecalcNeeded:
            self._calculatePMVParams()

        if self.__singleVals is True:
            return self.__ppd[0]
        else:
            return self.__ppd

    @property
    def set(self):
        """
        Standard effective temperature (SET) values for the input conditions.
        These temperatures describe what the given input conditions "feel like" in relation
        to a standard environment of 50% relative humidity, <0.1 m/s average air speed, and mean radiant temperature
        equal to average air temperature, in which the total heat loss from the skin of an imaginary occupant with an activity
        level of 1.0 met and a clothing level of 0.6 clo is the same as that from a person in the actual environment.
        """

        if not self.__isDataAligned:
            self._checkAndAlignLists()

        if self.__isRecalcNeeded:
            self._calculatePMVParams()

        if self.__singleVals is True:
            return self.__set[0]
        else:
            return self.__set

    @property
    def isComfortable(self):
        """
        Integer values that show whether the input conditions are comfortable according to the assigned compfortPar.
        Values are one of the following:
            0 = uncomfortable
            1 = comfortable
        """

        if not self.__isDataAligned:
            self._checkAndAlignLists()

        if self.__isRecalcNeeded:
            self._calculatePMVParams()

        if self.__singleVals is True:
            return self.__isComfortable[0]
        else:
            return self.__isComfortable

    @property
    def discomfReason(self):
        """
        Integer values that show the reason for discomfort according to the assigned compfortPar.
        Values are one of the following:
            -2 = too cold
            -1 = too dry
             0 = comfortable
             1 = too humid
             2 = too hot
        """

        if not self.__isDataAligned:
            self._checkAndAlignLists()

        if self.__isRecalcNeeded:
            self._calculatePMVParams()

        if self.__singleVals is True:
            return self.__discomfReason[0]
        else:
            return self.__discomfReason

    @property
    def taAdj(self):
        """
        Air temperatures that have been adjusted to account for the effect of air speed [C].
        """

        if not self.__isDataAligned:
            self._checkAndAlignLists()

        if self.__isRecalcNeeded:
            self._calculatePMVParams()

        if self.__singleVals is True:
            return self.__taAdj[0]
        else:
            return self.__taAdj

    @property
    def coolingEffect(self):
        """
        The temperature difference in [C] between the air temperature and the air temperature adjusted for air speed.
        """

        if not self.__isDataAligned:
            self._checkAndAlignLists()

        if self.__isRecalcNeeded:
            self._calculatePMVParams()

        if self.__singleVals is True:
            return self.__coolingEffect[0]
        else:
            return self.__coolingEffect

    def calcMissingPMVInput(self, targetPMV, missingInput=0, lowBound=0, upBound=100, error=0.001):
        """
        Sets the comfort model to return a deisred target PMV given a missingInput (out of the seven total PMV model inputs), which will be adjusted to meet this targetPMV.
        Returns the value(s) of the missingInput that makes the model obey the targetPMV.

        Args:
            targetPMV: The target pmv that you are trying to produce from the inputs to this pmv object.
            missingInput: An integer that denotes which of the 6 inputs to the PMV model you want to
            adjust to produce the targetPMV.  Choose from the following options:
                0 = airTemperature
                1 = radTemperature
                2 = windSpeed
                3 = relHumidity
                4 = metRate
                5 = cloValue
                6 = externalWork
            lowBound: The lowest possible value of the missingInput you are tying to find.
                Putting in a good value here will help the model converge to a solution faster.
            upBound: The highest possible value of the missingInput you are tying to find.
                Putting in a good value here will help the model converge to a solution faster.
            error: The acceptable error in the targetPMV. The default is set to 0.001

        Returns:
            missingVal: The value of the missingInput that will produce the targetPMV.

        """

        if not self.__isDataAligned:
            self._checkAndAlignLists()

        missingVal = []
        for i in range(self.__calcLength):

            # Determine the function that should be used given the requested missingInput.
            if missingInput == 0:
                def fn(x):
                    return (self._comfPMVElevatedAirspeed(x, self.__radTemperature[i], self.__windSpeed[i], self.__relHumidity[i], self.__metRate[i], self.__cloValue[i], self.__externalWork[i])['pmv'] - targetPMV)
            elif missingInput == 1:
                def fn(x):
                    return (self._comfPMVElevatedAirspeed(self.__airTemperature[i], x, self.__windSpeed[i], self.__relHumidity[i], self.__metRate[i], self.__cloValue[i], self.__externalWork[i])['pmv'] - targetPMV)
            elif missingInput == 2:
                def fn(x):
                    return (self._comfPMVElevatedAirspeed(self.__airTemperature[i], self.__radTemperature[i], x, self.__relHumidity[i], self.__metRate[i], self.__cloValue[i], self.__externalWork[i])['pmv'] - targetPMV)
            elif missingInput == 3:
                def fn(x):
                    return (self._comfPMVElevatedAirspeed(self.__airTemperature[i], self.__radTemperature[i], self.__windSpeed[i], x, self.__metRate[i], self.__cloValue[i], self.__externalWork[i])['pmv'] - targetPMV)
            elif missingInput == 4:
                def fn(x):
                    return (self._comfPMVElevatedAirspeed(self.__airTemperature[i], self.__radTemperature[i], self.__windSpeed[i], self.__relHumidity[i], x, self.__cloValue[i], self.__externalWork[i])['pmv'] - targetPMV)
            elif missingInput == 5:
                def fn(x):
                    return (self._comfPMVElevatedAirspeed(self.__airTemperature[i], self.__radTemperature[i], self.__windSpeed[i], self.__relHumidity[i], self.__metRate[i], x, self.__externalWork[i])['pmv'] - targetPMV)
            elif missingInput == 6:
                def fn(x):
                    return (self._comfPMVElevatedAirspeed(self.__airTemperature[i], self.__radTemperature[i], self.__windSpeed[i], self.__relHumidity[i], self.__metRate[i], self.__cloValue[i], x)['pmv'] - targetPMV)

            # Solve for the missing input using the function.
            xMissing = secant(lowBound, upBound, fn, error)
            if xMissing == 'NaN':
                xMissing = bisect(lowBound, upBound, fn, error)

            missingVal.append(xMissing)

        # Set the conditions of the comfort model to have the new missingVal.
        if missingInput == 0:
            self.__airTemperature = missingVal
        elif missingInput == 1:
            self.__radTemperature = missingVal
        elif missingInput == 2:
            self.__windSpeed = missingVal
        elif missingInput == 3:
            self.__relHumidity = missingVal
        elif missingInput == 4:
            self.__metRate = missingVal
        elif missingInput == 5:
            self.__cloValue = missingVal
        elif missingInput == 6:
            self.__externalWork = missingVal

        # Tell the comfort model to recompute now that the new values have been set.
        self.__isRecalcNeeded = True

        if self.__singleVals is True:
            return missingVal[0]
        else:
            return missingVal
