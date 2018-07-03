"""PMV Comfort object."""
import math
from collections import Iterable
from .comfortBase import ComfortModel
from ..psychrometrics import find_humid_ratio
from ..psychrometrics import find_saturated_vapor_pressure_torr
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
        myPmvComf = PMV.from_individual_values(26, 26, 0.75, 80, 1.1, 0.5)
        pmv = myPmvComf.pmv

        # Compute PMV for a list of data.
        air_temp = [10, 12, 15, 18, 19]
        rel_humid = [75, 70, 60, 50, 45]
        myPmvComf = PMV(air_temp, [], [], rel_humid)
        pmv = myPmvComf.pmv

        # Compute PMV for all hours of an EPW file.
        epw_file_address = "C:/ladybug/New_York_J_F_Kennedy_IntL_Ar_NY_USA/New_York_JF" \
            "Kennedy_IntL_Ar_NY_USA.epw"
        myPmvComf = PMV.from_epw_file(epw_file_address, 1.4, 1.0)
        pmv = myPmvComf.pmv

    """

    def __init__(self, air_temperature=None, rad_temperature=[], wind_speed=[],
                 rel_humidity=[], met_rate=[], clo_value=[], external_work=[]):
        """Initialize a PMV comfort object from lists of PMV inputs."""
        # Assign all of the input values to the PMV comfort model object.
        # And assign defaults if nothing has been connected.
        self.air_temperature = air_temperature

        if rad_temperature != []:
            self.__rad_temperature = rad_temperature
        else:
            self.__rad_temperature = self.__air_temperature

        if wind_speed != []:
            self.__wind_speed = wind_speed
        else:
            self.__wind_speed = [0]
        if rel_humidity != []:
            self.__rel_humidity = rel_humidity
        else:
            self.__rel_humidity = [50]
        if met_rate != []:
            self.__met_rate = met_rate
        else:
            self.__met_rate = [1.1]
        if clo_value != []:
            self.__clo_value = clo_value
        else:
            self.__clo_value = [0.85]
        if external_work != []:
            self.__external_work = external_work
        else:
            self.__external_work = [0]

        # Default variables that all comfort models have.
        self.__calcLength = None
        self.__isDataAligned = False
        self.__isRecalcNeeded = True

        self.__headerIncl = False
        self.__headerStr = []
        self.__singleVals = False

        # Set default comfort parameters for the PMV model.
        self.__ppd_comfort_thresh = 10.0
        self.__humid_ratio_up = 0.03
        self.__humid_ratio_low = 0
        self.__still_air_threshold = 0.1

        # Set blank values for the key returns of the class.
        self.__pmv = []
        self.__ppd = []
        self.__set = []
        self.__isComfortable = []
        self.__discomfReason = []
        self.__ta_adj = []
        self.__coolingEffect = []

    @classmethod
    def from_individual_values(cls, air_temperature=20.0, rad_temperature=None,
                               wind_speed=0.0, rel_humidity=50.0, met_rate=1.1,
                               clo_value=0.85, external_work=0.0):
        """Create a PMV comfort object from individual values."""
        if air_temperature is None:
            air_temperature = 20.0
        if rad_temperature is None:
            rad_temperature = air_temperature
        if wind_speed is None:
            wind_speed = 0.0
        if rel_humidity is None:
            rel_humidity = 0.0

        pmv_model = cls(
            [
                float(air_temperature)], [
                float(rad_temperature)], [
                float(wind_speed)], [
                    float(rel_humidity)], [
                        float(met_rate)], [
                            float(clo_value)], [
                                float(external_work)])
        pmv_model.__singleVals = True
        pmv_model.__isDataAligned = True
        pmv_model.__calcLength = 1

        return pmv_model

    @classmethod
    def from_epw_file(cls, epw_file_address, met_rate=1.1, clo_value=0.85,
                      external_work=0.0, incl_header=True):
        """Create a PMV comfort object from the conditions within an EPW file.

        Args:
            met_rate: A value representing the metabolic rate of the human subject in
                met. 1 met = resting seated. If list is empty, default is set to 1 met.
            clo_value: A lvalue representing the clothing level of the human subject in
                clo. 1 clo = three-piece suit. If list is empty, default is set to 1 clo.
            external_work: A value representing the work done by the human subject in
                met. 1 met = resting seated. If list is empty, default is set to 0 met.
            header: set to "True" to have a ladybug header included in the output and
                set to "False" to remove the header.  The default is set to "True."
        """
        epw_data = EPW(epw_file_address)
        return cls(
            epw_data.dryBulbTemperature.values(header=incl_header),
            epw_data.dryBulbTemperature.values(header=incl_header),
            epw_data.wind_speed.values(header=incl_header),
            epw_data.relativeHumidity.values(header=incl_header),
            [met_rate], [clo_value], [external_work])

    @property
    def is_re_calculation_needed(self):
        """Boolean value that indicates whether the comfort values need to be
        re-computed.

        Returns:
            True = re-calculation is needed before comfort values can be output.
            False = no re-calculation is needed.
        """
        return self.__isRecalcNeeded

    @property
    def is_data_aligned(self):
        """
        Boolean value that indicates whether the input data is aligned.
            True = aligned
            False = not aligned (run the _check_and_align_lists function to align the data)
        """
        return self.__isDataAligned

    @property
    def is_header_included(self):
        """
        Boolean value that indicates whether a header will be output on the results.
            True = header included.
            False = header not included.
        """
        return self.__headerIncl

    @property
    def single_values(self):
        """
        Boolean value that indicates whether single values or a list of values will be
        output.
            True = single values output.
            False = lists of values output.
        """
        return self.__singleVals

    @property
    def air_temperature(self):
        """
        A number or list of numbers representing dry bulb temperatures in degrees
        Celcius. This can be a list with a LB header on it.  If list is empty, default
        is set to 20 C.
        """
        return self.__air_temperature

    @air_temperature.setter
    def air_temperature(self, value):

        self.__air_temperature = [20] if not value else value

        if not isinstance(self.__air_temperature, Iterable):
            self.__air_temperature = [self.__air_temperature]

        self.__isDataAligned = False
        self.__isRecalcNeeded = True

    @property
    def rad_temperature(self):
        """
        A number or list of numbers representing mean radiant temperatures in degrees
        Celcius.

        This list can have a LB header on it.  If list is empty, default is set be the
        same as __air_temperature.
        """
        return self.__rad_temperature

    @rad_temperature.setter
    def rad_temperature(self, value):
        try:
            self.__rad_temperature = [float(value)]
        except BaseException:
            self.__rad_temperature = value
        self.__isDataAligned = False
        self.__isRecalcNeeded = True

    @property
    def wind_speed(self):
        """
        A number or list of numbers representing wind speeds in m/s. This list can have
        a LB header on it. If list is empty, default is set to 0 m/s.
        """
        return self.__wind_speed

    @wind_speed.setter
    def wind_speed(self, value):
        try:
            self.__wind_speed = [float(value)]
        except BaseException:
            self.__wind_speed = value
        self.__isDataAligned = False
        self.__isRecalcNeeded = True

    @property
    def rel_humidity(self):
        """
        A number or list of numbers representing relative humidities in %. This list can
        have a LB header on it. If list is empty, default is set to 50%.
        """
        return self.__rel_humidity

    @rel_humidity.setter
    def rel_humidity(self, value):
        try:
            self.__rel_humidity = [float(value)]
        except BaseException:
            self.__rel_humidity = value
        self.__isDataAligned = False
        self.__isRecalcNeeded = True

    @property
    def met_rate(self):
        """
        A number or list of numbers representing the metabolic rate of the human subject
        in met.
        1 met = resting seated. This list can have a LB header on it.
        If list is empty, default is set to 1.1 met.
        """
        return self.__met_rate

    @met_rate.setter
    def met_rate(self, value):
        try:
            self.__met_rate = [float(value)]
        except BaseException:
            self.__met_rate = value
        self.__isDataAligned = False
        self.__isRecalcNeeded = True

    @property
    def clo_value(self):
        """
        A number or list of numbers representing the clothing level of the human subject
        in clo.
        1 clo = three-piece suit. This list can have a LB header on it.
        If list is empty, default is set to 0.85 clo.
        """
        return self.__clo_value

    @clo_value.setter
    def clo_value(self, value):
        try:
            self.__clo_value = [float(value)]
        except BaseException:
            self.__clo_value = value
        self.__isDataAligned = False
        self.__isRecalcNeeded = True

    @property
    def external_work(self):
        """
        A number or list of numbers representing the work done by the human subject in
        met.
        This list can have a LB header on it.
        If list is empty, default is set to 0 met.
        """
        return self.__external_work

    @external_work.setter
    def external_work(self, value):
        try:
            self.__external_work = [float(value)]
        except BaseException:
            self.__external_work = value
        self.__isDataAligned = False
        self.__isRecalcNeeded = True

    @property
    def ppd_comfort_thresh(self):
        """
        A number representing the threshold of the percentage of people dissatisfied
        (PPD) beyond which the conditions are not comfortable.  The default is 10%.
        """
        return self.__ppd_comfort_thresh

    @ppd_comfort_thresh.setter
    def ppd_comfort_thresh(self, value):
        self.__ppd_comfort_thresh = value
        self.__isRecalcNeeded = True

    @property
    def humid_ratio_up(self):
        """
        A number representing the upper boundary of humidity ratio above which conditions
        are considered too humid to be comfortable.  The default is set to 0.03 kg
        wather/kg air.
        """
        return self.__humid_ratio_up

    @humid_ratio_up.setter
    def humid_ratio_up(self, value):
        self.__humid_ratio_up = value
        self.__isRecalcNeeded = True

    @property
    def humid_ratio_low(self):
        """
        A number representing the lower boundary of humidity ratio below which conditions
        are considered too dry to be comfortable.  The default is set to 0 kg wather/kg
        air.
        """
        return self.__humid_ratio_low

    @humid_ratio_low.setter
    def humid_ratio_low(self, value):
        self.__humid_ratio_low = value
        self.__isRecalcNeeded = True

    @property
    def still_air_threshold(self):
        """
        A number representing the wind speed beyond which the formula for Standard
        Effective Temperature (SET) is used to dtermine PMV/PPD (as opposed to Fanger's
        original equation). The default is set to 0.1 m/s.
        """
        return self.__still_air_threshold

    @still_air_threshold.setter
    def still_air_threshold(self, value):
        self.__still_air_threshold = value
        self.__isRecalcNeeded = True

    def set_comfort_par(self, ppd_comfort_thresh=10, humid_ratio_up=0.03,
                        humid_ratio_low=0, still_air_threshold=0.1):
        """
        Set all of the comfort parameters of the comfort model at once.  These are:
            ppd_comfort_thresh
            humid_ratio_up
            humid_ratio_low
            still_air_threshold
        """
        self.__ppd_comfort_thresh = ppd_comfort_thresh
        self.__humid_ratio_up = humid_ratio_up
        self.__humid_ratio_low = humid_ratio_low
        self.__still_air_threshold = still_air_threshold

        self.__isRecalcNeeded = True

    def _check_and_align_lists(self):
        """
        Checks to be sure that the lists of PMV input variables are aligned and fills in
        defaults where possible.
        """
        # Check each list to be sure that the contents are what we want.
        check_data1, air_temp, airMultVal = self._check_input_list(
            self.__air_temperature, [20], "air_temperature", "Temperature")
        check_data2, rad_temp, radMultVal = self._check_input_list(
            self.__rad_temperature, air_temp, "rad_temperature", "Temperature")
        check_data3, wind_speed, windMultVal = self._check_input_list(
            self.__wind_speed, [0.0], "wind_speed", "Wind Speed")
        check_data4, rel_humid, humidMultVal = self._check_input_list(
            self.__rel_humidity, [50.0], "rel_humidity", "Humidity")
        check_data5, met_rate, metMultVal = self._check_input_list(
            self.__met_rate, [1.1], "metabolicRate", "Metabolic")
        check_data6, clo_level, cloMultVal = self._check_input_list(
            self.__clo_value, [0.85], "clothingValue", "Clothing")
        check_data7, ex_work, exMultVal = self._check_input_list(
            self.__external_work, [0.0], "external_work", "Work")

        # Finally, for those lists of length greater than 1, check to make sure
        # that they are all the same length.
        check_data = False
        if check_data1 is True and check_data2 is True and check_data3 is True and \
            check_data4 is True and check_data5 is True and check_data6 is True and \
                check_data7 is True:
            if airMultVal is True or radMultVal is True or windMultVal is True or \
                    humidMultVal is True or metMultVal is True or cloMultVal is True or \
                    exMultVal is True:
                list_len_check = []
                if airMultVal is True:
                    list_len_check.append(len(air_temp))
                if radMultVal is True:
                    list_len_check.append(len(rad_temp))
                if windMultVal is True:
                    list_len_check.append(len(wind_speed))
                if humidMultVal is True:
                    list_len_check.append(len(rel_humid))
                if metMultVal is True:
                    list_len_check.append(len(met_rate))
                if cloMultVal is True:
                    list_len_check.append(len(clo_level))
                if exMultVal is True:
                    list_len_check.append(len(ex_work))

                if all(x == list_len_check[0] for x in list_len_check) is True:
                    check_data = True
                    self.__calcLength = list_len_check[0]

                    if airMultVal is False:
                        air_temp = duplicate(air_temp[0], self.__calcLength)
                    if radMultVal is False:
                        rad_temp = duplicate(rad_temp[0], self.__calcLength)
                    if windMultVal is False:
                        wind_speed = duplicate(wind_speed[0], self.__calcLength)
                    if humidMultVal is False:
                        rel_humid = duplicate(rel_humid[0], self.__calcLength)
                    if metMultVal is False:
                        met_rate = duplicate(met_rate[0], self.__calcLength)
                    if cloMultVal is False:
                        clo_level = duplicate(clo_level[0], self.__calcLength)
                    if exMultVal is False:
                        ex_work = duplicate(ex_work[0], self.__calcLength)

                else:
                    self.__calcLength = None
                    raise Exception(
                        'If you have put in lists with multiple values, the lengths of'
                        'these lists must match \n across the parameters or you have a'
                        ' single value for a given parameter to be applied to all values'
                        ' in the list.')
            else:
                check_data = True
                self.__calcLength = 1

        # If everything is good, re-assign the lists of input variables and set
        # the list alignment to true.
        if check_data is True:
            # Assign all of the input values to the PMV comfort model object.
            self.__air_temperature = air_temp
            self.__rad_temperature = rad_temp
            self.__wind_speed = wind_speed
            self.__rel_humidity = rel_humid
            self.__met_rate = met_rate
            self.__clo_value = clo_level
            self.__external_work = ex_work
            # Set the alighed data value to true.
            self.__isDataAligned = True
            self.__isRecalcNeeded = True

    @staticmethod
    def find_ppd(pmv):
        """
        Args:
            pmv: The predicted mean vote (PMV) for which you want to know the PPD.

        Returns:
            ppd: The percentage of people dissatisfied (PPD) for the input PMV.
        """
        return 100.0 - 95.0 * math.exp(-0.03353 * pow(pmv, 4.0) - 0.2179 * pow(pmv, 2.0))

    @staticmethod
    def find_pmv(ppd, ppd_error=0.001):
        """
        Args:
            ppd: The percentage of people dissatisfied (PPD) for which you want to know
                the possible PMV.
            ppd_error: The acceptable error in meeting the target PPD.  The default is
                set to 0.001.

        Returns:
            pmv: A list with the two predicted mean vote (PMV) values that produces the
                input PPD.
        """
        if not ppd < 5:
            pmv_low = -3
            pmv_mid = 0
            pmv_hi = 3

            def fn(pmv):
                return (
                    (100.0 - 95.0 *
                     math.exp(-0.03353 * pow(pmv, 4.0) - 0.2179 * pow(pmv, 2.0))) - ppd)

            # Solve for the missing lower PMV value.
            pmv_low_solution = secant(pmv_low, pmv_mid, fn, ppd_error)
            if pmv_low_solution == 'NaN':
                pmv_low_solution = bisect(pmv_low, pmv_mid, fn, ppd_error)
            # Solve for the missing higher PMV value.
            pmv_hi_solution = secant(pmv_mid, pmv_hi, fn, ppd_error)
            if pmv_hi_solution == 'NaN':
                pmv_hi_solution = bisect(pmv_mid, pmv_hi, fn, ppd_error)

            return [pmv_low_solution, pmv_hi_solution]
        else:
            raise Exception('A ppd lower than 5% is not achievable with the PMV model.')

    @staticmethod
    def comf_pmv(ta, tr, vel, rh, met, clo, wme):
        """
        Original Fanger function to compute PMV.  Only intended for use with low air
        speeds (<0.1 m/s).

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
                print('Max iterations exceeded')
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
    def comf_pierce_set(ta, tr, vel, rh, met, clo, wme):
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
        vapor_pressure = (rh * find_saturated_vapor_pressure_torr(ta)) / 100
        air_velocity = max(vel, 0.1)
        kclo = 0.25
        bodyweight = 69.9
        bodysurfacearea = 1.8258
        metfactor = 58.2
        sbc = 0.000000056697  # Stefan-Boltzmann constant (W/m2K4)
        csw = 170
        cdil = 120
        cstr = 0.5

        temp_skin_neutral = 33.7  # setpoint (neutral) value for Tsk
        temp_core_neutral = 36.49  # setpoint value for Tcr
        # setpoint for Tb (.1*temp_skin_neutral + .9*temp_core_neutral)
        temp_body_neutral = 36.49
        skin_blood_flow_neutral = 6.3  # neutral value for skin_blood_flow

        # INITIAL VALUES - start of 1st experiment
        temp_skin = temp_skin_neutral
        temp_core = temp_core_neutral
        skin_blood_flow = skin_blood_flow_neutral
        mshiv = 0.0
        alfa = 0.1
        esk = 0.1 * met

        # Start new experiment here (for graded experiments)
        # UNIT CONVERSIONS (from input variables)

        # This variable is the pressure of the atmosphere in kPa and was taken
        # from the psychrometrics.js file of the CBE comfort tool.
        p = 101325.0 / 1000

        pressure_in_atmospheres = p * 0.009869
        ltime = 60
        rcl = 0.155 * clo
        # Adjusticl(rcl, Conditions);  TH: I don't think this is used in the software

        facl = 1.0 + 0.15 * clo  # % INCreaSE IN BODY SURFACE Area DUE TO CLOTHING
        LR = 2.2 / pressure_in_atmospheres  # Lewis Relation is 2.2 at sea level
        RM = met * metfactor
        M = met * metfactor

        if clo <= 0:
            wcrit = 0.38 * pow(air_velocity, -0.29)
            icl = 1.0
        else:
            wcrit = 0.59 * pow(air_velocity, -0.08)
            icl = 0.45

        chc = 3.0 * pow(pressure_in_atmospheres, 0.53)
        chcV = 8.600001 * pow((air_velocity * pressure_in_atmospheres), 0.53)
        chc = max(chc, chcV)

        # initial estimate of Tcl
        chr = 4.7
        ctc = chr + chc
        RA = 1.0 / (facl * ctc)  # resistance of air layer to dry heat transfer
        top = (chr * tr + chc * ta) / ctc
        tcl = top + (temp_skin - top) / (ctc * (RA + rcl))

        # ========================  BEGIN ITERATION
        #
        # Tcl and chr are solved iteratively using: H(Tsk - To) = ctc(Tcl - To),
        # where H = 1/(Ra + Rcl) and Ra = 1/Facl*ctc

        tcl_old = tcl
        time = range(ltime)
        flag = True
        for TIM in time:
            if flag is True:
                while abs(tcl - tcl_old) > 0.01:
                    tcl_old = tcl
                    chr = 4.0 * sbc * pow(((tcl + tr) / 2.0 + 273.15), 3.0) * 0.72
                    ctc = chr + chc
                    # resistance of air layer to dry heat transfer
                    RA = 1.0 / (facl * ctc)
                    top = (chr * tr + chc * ta) / ctc
                    tcl = (RA * temp_skin + rcl * top) / (RA + rcl)
            flag = False
            dry = (temp_skin - top) / (RA + rcl)
            hfcs = (temp_core - temp_skin) * (5.28 + 1.163 * skin_blood_flow)
            eres = 0.0023 * M * (44.0 - vapor_pressure)
            cres = 0.0014 * M * (34.0 - ta)
            scr = M - hfcs - eres - cres - wme
            ssk = hfcs - dry - esk
            tcsk = 0.97 * alfa * bodyweight
            tccr = 0.97 * (1 - alfa) * bodyweight
            dtsk = (ssk * bodysurfacearea) / (tcsk * 60.0)  # deg C per minute
            dtcr = scr * bodysurfacearea / (tccr * 60.0)  # deg C per minute
            temp_skin = temp_skin + dtsk
            temp_core = temp_core + dtcr
            TB = alfa * temp_skin + (1 - alfa) * temp_core
            sksig = temp_skin - temp_skin_neutral
            warms = (sksig > 0) * sksig
            colds = ((-1.0 * sksig) > 0) * (-1.0 * sksig)
            crsig = (temp_core - temp_core_neutral)
            warmc = (crsig > 0) * crsig
            coldc = ((-1.0 * crsig) > 0) * (-1.0 * crsig)
            bdsig = TB - temp_body_neutral
            warmb = (bdsig > 0) * bdsig
            skin_blood_flow = (skin_blood_flow_neutral + cdil *
                               warmc) / (1 + cstr * colds)
            if skin_blood_flow > 90.0:
                skin_blood_flow = 90.0
            if skin_blood_flow < 0.5:
                skin_blood_flow = 0.5
            regsw = csw * warmb * math.exp(warms / 10.7)
            if regsw > 500.0:
                regsw = 500.0
            ersw = 0.68 * regsw
            rea = 1.0 / (LR * facl * chc)  # evaporative resistance of air layer
            recl = rcl / (LR * icl)  # evaporative resistance of clothing (icl=.45)
            emax = (find_saturated_vapor_pressure_torr(
                temp_skin) - vapor_pressure) / (rea + recl)
            prsw = ersw / emax
            pwet = 0.06 + 0.94 * prsw
            edif = pwet * emax - ersw
            esk = ersw + edif
            if pwet > wcrit:
                pwet = wcrit
                prsw = wcrit / 0.94
                ersw = prsw * emax
                edif = 0.06 * (1.0 - prsw) * emax
                esk = ersw + edif
            if emax < 0:
                edif = 0
                ersw = 0
                pwet = wcrit
                prsw = wcrit
                esk = emax
            esk = ersw + edif
            mshiv = 19.4 * colds * coldc
            M = RM + mshiv
            alfa = 0.0417737 + 0.7451833 / (skin_blood_flow + .585417)

        # Define new heat flow terms, coeffs, and abbreviations
        hsk = dry + esk  # total heat loss from skin
        RN = M - wme  # net metabolic heat production
        ecomf = 0.42 * (RN - (1 * metfactor))
        if ecomf < 0.0:
            ecomf = 0.0  # from Fanger
        emax = emax * wcrit
        W = pwet
        pssk = find_saturated_vapor_pressure_torr(temp_skin)
        # Definition of ASHRAE standard environment... denoted "S"
        chrS = chr
        if met < 0.85:
            chcS = 3.0
        else:
            chcS = 5.66 * pow((met - 0.85), 0.39)
            if chcS < 3.0:
                chcS = 3.0

        ctcs = chcS + chrS
        rclos = 1.52 / ((met - wme / metfactor) + 0.6944) - 0.1835
        rcls = 0.155 * rclos
        facls = 1.0 + kclo * rclos
        fcls = 1.0 / (1.0 + 0.155 * facls * ctcs * rclos)
        ims = 0.45
        icls = ims * chcS / ctcs * (1 - fcls) / (chcS / ctcs - fcls * ims)
        ras = 1.0 / (facls * ctcs)
        reaS = 1.0 / (LR * facls * chcS)
        reclS = rcls / (LR * icls)
        hd_s = 1.0 / (ras + rcls)
        he_s = 1.0 / (reaS + reclS)

        # SET* (standardized humidity, clo, Pb, and chc)
        # determined using Newton's iterative solution
        # FNERRS is defined in the GENERAL SETUP section above

        delta = .0001
        dx = 100.0
        x_old = temp_skin - hsk / hd_s  # lower bound for SET
        while abs(dx) > .01:
            err1 = (hsk - hd_s * (temp_skin - x_old) - W * he_s *
                    (pssk - 0.5 * find_saturated_vapor_pressure_torr(x_old)))
            err2 = (hsk - hd_s * (temp_skin - (x_old + delta)) - W * he_s *
                    (pssk - 0.5 * find_saturated_vapor_pressure_torr((x_old + delta))))
            x = x_old - delta * err1 / (err2 - err1)
            dx = x - x_old
            x_old = x

        return x

    def _comf_pmv_elevated_airspeed(self, ta, tr, vel, rh, met, clo, wme):
        """
        This function will return accurate values if the airspeed is above the
            sillAirThreshold.

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
            ta_adj: Air temperature adjusted for air speed [C]
            coolingEffect : Difference between the air temperature and adjusted air
                temperature [C]
            set: The Standard Effective Temperature [C] (see below)
        """

        r = {}
        set = self.comf_pierce_set(ta, tr, vel, rh, met, clo, wme)

        if vel <= self.__still_air_threshold:
            pmv, ppd = self.comf_pmv(ta, tr, vel, rh, met, clo, wme)
            ta_adj = ta
            ce = 0
        else:
            ce_l = 0
            ce_r = 40
            eps = 0.001  # precision of ce

            def fn(ce):
                return (set - self.comf_pierce_set(
                    ta - ce, tr - ce,
                    self.__still_air_threshold, rh, met, clo, wme))

            ce = secant(ce_l, ce_r, fn, eps)
            if ce == 'NaN':
                ce = bisect(ce_l, ce_r, fn, eps, 0)

            pmv, ppd = self.comf_pmv(
                ta - ce, tr - ce, self.__still_air_threshold, rh, met, clo, wme)
            ta_adj = ta - ce

        r['pmv'] = pmv
        r['ppd'] = ppd
        r['set'] = set
        r['ta_adj'] = ta_adj
        r['ce'] = ce

        return r

    def _calculate_pmv_params(self):
        """
        Runs the input conditions through the PMV model to get pmv, ppd, and set.
        """
        # Clear any existing values from the memory.
        self.__pmv = []
        self.__ppd = []
        self.__set = []
        self.__isComfortable = []
        self.__discomfReason = []
        self.__ta_adj = []
        self.__coolingEffect = []

        # If the input data has a header, put a header on the output.
        if self.__headerIncl is True:
            self.__pmv.extend(self.buildCustomHeader("Predicted Mean Vote", "PMV"))
            self.__ppd.extend(
                self.buildCustomHeader(
                    "Percentage of People Dissatisfied", "%"))
            self.__set.extend(
                self.buildCustomHeader(
                    "Standard Effective Temperature", "C"))
            self.__isComfortable.extend(
                self.buildCustomHeader(
                    "Comfortable Or Not", "0/1"))
            self.__discomfReason.extend(
                self.buildCustomHeader(
                    "Reason For Discomfort",
                    "-2(cold), -1(dry), 0(comf), 1(humid), 2(hot)"))
            self.__ta_adj.extend(
                self.buildCustomHeader(
                    "Perceived Air Temperature With Air Speed", "C"))
            self.__coolingEffect.extend(
                self.buildCustomHeader(
                    "Cooling Effect of air speed", "C"))

        # calculate the pmv, ppd, and set values.
        for i in range(self.__calcLength):
            pmv_result = self._comf_pmv_elevated_airspeed(
                self.__air_temperature[i],
                self.__rad_temperature[i],
                self.__wind_speed[i],
                self.__rel_humidity[i],
                self.__met_rate[i],
                self.__clo_value[i],
                self.__external_work[i])
            self.__pmv.append(pmv_result['pmv'])
            self.__ppd.append(pmv_result['ppd'])
            self.__set.append(pmv_result['set'])
            self.__ta_adj.append(pmv_result['ta_adj'])
            self.__coolingEffect.append(pmv_result['ce'])

            # determine whether conditions meet the comfort criteria.
            HR, vapPress, satPress = find_humid_ratio(
                self.__air_temperature[i], self.__rel_humidity[i])
            if pmv_result['ppd'] > self.__ppd_comfort_thresh:
                self.__isComfortable.append(0)
                if pmv_result['pmv'] > 0:
                    self.__discomfReason.append(2)
                else:
                    self.__discomfReason.append(-2)
            elif HR > self.__humid_ratio_up:
                self.__isComfortable.append(0)
                self.__discomfReason.append(1)
            elif HR < self.__humid_ratio_low:
                self.__isComfortable.append(0)
                self.__discomfReason.append(-1)
            else:
                self.__isComfortable.append(1)
                self.__discomfReason.append(0)

        # Let the class know that we don't need to re-run things unless something
        # changes.
        self.__isRecalcNeeded = False

    @property
    def pmv(self):
        """
        Predicted mean vote (PMV) values for the input conditions.
        PMV is a seven-point scale from cold (-3) to hot (+3) that was used in comfort
        surveys of P.O. Fanger.
        Each interger value of the scale indicates the following:
            -3 = Cold
            -2 = Cool
            -1 = Slightly Cool
             0 = Neutral
            +1 = Slightly Warm
            +2 = Warm
            +3 = Hot
        Exceeding +1 will result in an uncomfortably warm occupant while dropping below
        -1 will result in an uncomfortably cool occupant.
        For detailed information on the PMV scale, see P.O. Fanger's original paper:
        Fanger, P Ole (1970). Thermal Comfort: Analysis and applications in environmental
        engineering.
        """

        if not self.__isDataAligned:
            self._check_and_align_lists()

        if self.__isRecalcNeeded:
            self._calculate_pmv_params()

        if self.__singleVals is True:
            return self.__pmv[0]
        else:
            return self.__pmv

    @property
    def ppd(self):
        """
        Percentage of people dissatisfied (PPD) values for the input conditions.
        Specifically, this is defined by the percent of people who would have a PMV less
        than -1 or greater than +1 under the conditions. Note that, with this model, the
        best possible PPD achievable is 5% and most standards aim to have a PPD below
        10%.
        """

        if not self.__isDataAligned:
            self._check_and_align_lists()

        if self.__isRecalcNeeded:
            self._calculate_pmv_params()

        if self.__singleVals is True:
            return self.__ppd[0]
        else:
            return self.__ppd

    @property
    def set(self):
        """
        Standard effective temperature (SET) values for the input conditions.
        These temperatures describe what the given input conditions "feel like" in
        relation to a standard environment of 50% relative humidity, <0.1 m/s average
        air speed, and mean radiant temperature equal to average air temperature, in
        which the total heat loss from the skin of an imaginary occupant with an activity
        level of 1.0 met and a clothing level of 0.6 clo is the same as that from a
        person in the actual environment.
        """

        if not self.__isDataAligned:
            self._check_and_align_lists()

        if self.__isRecalcNeeded:
            self._calculate_pmv_params()

        if self.__singleVals is True:
            return self.__set[0]
        else:
            return self.__set

    @property
    def is_comfortable(self):
        """
        Integer values that show whether the input conditions are comfortable according
        to the assigned compfortPar.
        Values are one of the following:
            0 = uncomfortable
            1 = comfortable
        """

        if not self.__isDataAligned:
            self._check_and_align_lists()

        if self.__isRecalcNeeded:
            self._calculate_pmv_params()

        if self.__singleVals is True:
            return self.__isComfortable[0]
        else:
            return self.__isComfortable

    @property
    def discomf_reason(self):
        """
        Integer values that show the reason for discomfort according to the assigned
        compfortPar.
        Values are one of the following:
            -2 = too cold
            -1 = too dry
             0 = comfortable
             1 = too humid
             2 = too hot
        """

        if not self.__isDataAligned:
            self._check_and_align_lists()

        if self.__isRecalcNeeded:
            self._calculate_pmv_params()

        if self.__singleVals is True:
            return self.__discomfReason[0]
        else:
            return self.__discomfReason

    @property
    def ta_adj(self):
        """
        Air temperatures that have been adjusted to account for the effect of air speed
        [C].
        """

        if not self.__isDataAligned:
            self._check_and_align_lists()

        if self.__isRecalcNeeded:
            self._calculate_pmv_params()

        if self.__singleVals is True:
            return self.__ta_adj[0]
        else:
            return self.__ta_adj

    @property
    def cooling_effect(self):
        """
        The temperature difference in [C] between the air temperature and the air
        temperature adjusted for air speed.
        """

        if not self.__isDataAligned:
            self._check_and_align_lists()

        if self.__isRecalcNeeded:
            self._calculate_pmv_params()

        if self.__singleVals is True:
            return self.__coolingEffect[0]
        else:
            return self.__coolingEffect

    def calc_missing_pmv_input(self, target_pmv, missing_input=0,
                               low_bound=0, up_bound=100, error=0.001):
        """
        Sets the comfort model to return a deisred target PMV given a missing_input
        (out of the seven total PMV model inputs), which will be adjusted to meet this
        target_pmv.

        Returns the value(s) of the missing_input that makes the model obey the
        target_pmv.

        Args:
            target_pmv: The target pmv that you are trying to produce from the inputs to
                this pmv object.
            missing_input: An integer that denotes which of the 6 inputs to the PMV
                model you want to
            adjust to produce the target_pmv.  Choose from the following options:
                0 = air_temperature
                1 = rad_temperature
                2 = wind_speed
                3 = rel_humidity
                4 = met_rate
                5 = clo_value
                6 = external_work
            low_bound: The lowest possible value of the missing_input you are tying to
                find. Putting in a good value here will help the model converge to a
                solution faster.
            up_bound: The highest possible value of the missing_input you are tying to
                find. Putting in a good value here will help the model converge to a
                solution faster.
            error: The acceptable error in the target_pmv. The default is set to 0.001

        Returns:
            missing_val: The value of the missing_input that will produce the target_pmv.

        """

        if not self.__isDataAligned:
            self._check_and_align_lists()

        missing_val = []
        for i in range(self.__calcLength):

            # Determine the function that should be used given the requested
            # missing_input.
            if missing_input == 0:
                def fn(x):
                    return (self._comf_pmv_elevated_airspeed(
                        x, self.__rad_temperature[i], self.__wind_speed[i],
                        self.__rel_humidity[i], self.__met_rate[i], self.__clo_value[i],
                        self.__external_work[i])['pmv'] - target_pmv)
            elif missing_input == 1:
                def fn(x):
                    return (self._comf_pmv_elevated_airspeed(
                        self.__air_temperature[i], x, self.__wind_speed[i],
                        self.__rel_humidity[i], self.__met_rate[i], self.__clo_value[i],
                        self.__external_work[i])['pmv'] - target_pmv)
            elif missing_input == 2:
                def fn(x):
                    return (self._comf_pmv_elevated_airspeed(
                        self.__air_temperature[i], self.__rad_temperature[i], x,
                        self.__rel_humidity[i], self.__met_rate[i], self.__clo_value[i],
                        self.__external_work[i])['pmv'] - target_pmv)
            elif missing_input == 3:
                def fn(x):
                    return (self._comf_pmv_elevated_airspeed(
                        self.__air_temperature[i], self.__rad_temperature[i],
                        self.__wind_speed[i], x, self.__met_rate[i], self.__clo_value[i],
                        self.__external_work[i])['pmv'] - target_pmv)
            elif missing_input == 4:
                def fn(x):
                    return (
                        self._comf_pmv_elevated_airspeed(
                            self.__air_temperature[i], self.__rad_temperature[i],
                            self.__wind_speed[i], self.__rel_humidity[i], x,
                            self.__clo_value[i],
                            self.__external_work[i])['pmv'] - target_pmv)
            elif missing_input == 5:
                def fn(x):
                    return (
                        self._comf_pmv_elevated_airspeed(
                            self.__air_temperature[i], self.__rad_temperature[i],
                            self.__wind_speed[i], self.__rel_humidity[i],
                            self.__met_rate[i], x,
                            self.__external_work[i])['pmv'] - target_pmv)
            elif missing_input == 6:
                def fn(x):
                    return (
                        self._comf_pmv_elevated_airspeed(
                            self.__air_temperature[i],
                            self.__rad_temperature[i],
                            self.__wind_speed[i],
                            self.__rel_humidity[i],
                            self.__met_rate[i],
                            self.__clo_value[i], x)['pmv'] - target_pmv)

            # Solve for the missing input using the function.
            x_missing = secant(low_bound, up_bound, fn, error)
            if x_missing == 'NaN':
                x_missing = bisect(low_bound, up_bound, fn, error)

            missing_val.append(x_missing)

        # Set the conditions of the comfort model to have the new missing_val.
        if missing_input == 0:
            self.__air_temperature = missing_val
        elif missing_input == 1:
            self.__rad_temperature = missing_val
        elif missing_input == 2:
            self.__wind_speed = missing_val
        elif missing_input == 3:
            self.__rel_humidity = missing_val
        elif missing_input == 4:
            self.__met_rate = missing_val
        elif missing_input == 5:
            self.__clo_value = missing_val
        elif missing_input == 6:
            self.__external_work = missing_val

        # Tell the comfort model to recompute now that the new values have been set.
        self.__isRecalcNeeded = True

        if self.__singleVals is True:
            return missing_val[0]
        else:
            return missing_val
