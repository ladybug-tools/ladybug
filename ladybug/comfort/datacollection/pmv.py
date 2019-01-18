# coding=utf-8
"""Object for calculating PMV comfort from DataCollections."""
from __future__ import division

from ._base import ComfortDataCollection
from ..parameter.pmv import PMVParameter
from ...datacollection import DataCollection
from ...epw import EPW
from ...psychrometrics import humid_ratio_from_db_rh


class PMV(ComfortDataCollection):
    """PMV comfort DataCollection object.

    Properties:
        air_temperature
        rad_temperature
        air_speed
        rel_humidity
        met_rate
        clo_value
        external_work
        pmv
        ppd
        standard_effective_temperature
        is_comfortable
        thermal_condition
        discomfort_reason
        percent_comfortable
        percent_uncomfortable
        percent_neutral
        percent_hot
        percent_cold
        percent_dry
        percent_humid
        humidity_ratio
        adjusted_air_temperature
        heat_loss_conduction
        heat_loss_sweating
        heat_loss_latent_respiration
        heat_loss_dry_respiration
        heat_loss_radiation
        heat_loss_convection
    """
    _model = 'Predicted Mean Vote'

    def __init__(self, air_temperature, rel_humidity,
                 rad_temperature=None, air_speed=None,
                 met_rate=None, clo_value=None, external_work=None,
                 comfort_parameters=None):
        """Initialize a PMV comfort object from DataCollections of PMV inputs.

        Args:
            air_temperature: DataCollection of air temperature values in degrees Celcius.
            rel_humidity: DataCollection of relative humidity values in %.
            rad_temperature: DataCollection of mean radiant temperature (MRT)
                values in degrees Celcius. If None, this will be the same as
                the air_temperature.
            air_speed: DataCollection of air speed values in m/s. If None, this
                will default to 0.1 m/s.
            met_rate: DataCollection of metabolic rate in met. If none, default is set
                to 1.1 met (for seated, typing).
            clo_value:
            external_work:
            comfort_parameters:
        """
        raise NotImplementedError('PMV ComfortModel is not yet implemented.')

        self._air_temperature = air_temperature
        self._rel_humidity = rel_humidity

        if rad_temperature is not None:
            self._rad_temperature = rad_temperature
        else:
            self._rad_temperature = self._air_temperature

        if air_speed is not None:
            self._air_speed = air_speed
        else:
            self._air_speed = DataCollection.from_duplicated_value(0.1)

        if met_rate is not None:
            self._met_rate = met_rate
        else:
            self._met_rate = DataCollection.from_single_value(1.1)

        if clo_value is not None:
            self._clo_value = clo_value
        else:
            self._clo_value = DataCollection.from_single_value(0.85)

        if external_work is not None:
            self._external_work = external_work
        else:
            self._external_work = DataCollection.from_single_value(0.0)

        # Set default comfort parameters for the PMV model.
        self._comfort_parameters = comfort_parameters
        if comfort_parameters is None:
            self._comfort_parameters = PMVParameter()

    @classmethod
    def from_epw_file(cls, epw_file_address, include_wind=False, include_sun=False,
                      met_rate=None, clo_value=None, external_work=None):
        """Create a PMV comfort object from the conditions within an EPW file.

        Args:
            epw_file_address: Address to an EPW file on your system.
            include_wind: Set to True to include the epw wind speed in the calculation.
                Default is False. Note that, if set to True, an autmatic conversion
                will be done from the meteorological wind speed at 10 meters to
                human height at 1 meter.
            include_sun: Set to True to include the MRT delta from sun directly
                shining on people in the PMV calculation.  Default is False.
                Note that this calculation will assume no surrounding context
                and an human geometry that always has their left or right
                side facing the sun.
            met_rate: A value representing the metabolic rate of the human subject in
                met. 1 met = resting seated. If list is empty, default is set to 1 met.
            clo_value: A lvalue representing the clothing level of the human subject in
                clo. 1 clo = three-piece suit. If list is empty, default is set to 1 clo.
            external_work: A value representing the work done by the human subject in
                met. 1 met = resting seated. If list is empty, default is set to 0 met.
        """
        epw_data = EPW(epw_file_address)
        return cls(
            epw_data.dryBulbTemperature.values,
            epw_data.dryBulbTemperature.values,
            epw_data.air_speed.values,
            epw_data.relativeHumidity.values,
            met_rate, clo_value, external_work)

    @property
    def air_temperature(self):
        """DataCollection of air temperature values in degrees Celcius."""
        return self._air_temperature

    @property
    def rad_temperature(self):
        """DataCollection of mean radiant temperature (MRT) values in degrees Celcius.

        If left blank, this will be the same as the air_temperature property.
        """
        return self._rad_temperature

    @property
    def air_speed(self):
        """DataCollection of air speed values in m/s.

        If left blank, default is set to 0.1 m/s.
        """
        return self._air_speed

    @property
    def rel_humidity(self):
        """DataCollection of relative humidity values in %."""
        return self._rel_humidity

    @property
    def met_rate(self):
        """DataCollection of metabolic rate in met.

        1 met = Metabolic rate of a resting seated person
        1.2 met = Metabolic rate of a standing person
        2 met = Metabolic rate of a wlaking person
        If left blank, default is set to 1.1 met (for seated, typing).
        """
        return self._met_rate

    @property
    def clo_value(self):
        """DataCollection of clothing level of the human subject in clo.

        1 clo = Three-piece suit
        0.5 clo = Shorts + T-shirt
        0 clo = No clothing
        If left blank, default is set to 0.85 clo.
        """
        return self._clo_value

    @property
    def external_work(self):
        """DataCollection of the work done by the human subject in met.

        If left blank, default is set to 0 met.
        """
        return self._external_work

    @property
    def pmv(self):
        """DataCollection of predicted mean vote (PMV) for the input conditions.

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
        """
        return self._pmv

    @property
    def ppd(self):
        """DataCollection of percentage of people dissatisfied (PPD) for the input conditions.

        Specifically, this is defined by the percent of people who would have
        a PMV of -1 or less or a PMV of +1 or greater under the conditions.
        Note that, with the PMV model, the best possible PPD achievable is 5%
        and most standards aim to have a PPD below 10%.
        """
        return self._ppd

    @property
    def standard_effective_temperature(self):
        """DataCollection of standard effective temperature (SET) for the input conditions.

        These temperatures describe what the given input conditions "feel like" in
        relation to a standard environment of 50% relative humidity, <0.1 m/s average
        air speed, and mean radiant temperature equal to average air temperature, in
        which the total heat loss from the skin of an imaginary occupant with an activity
        level of 1.0 met and a clothing level of 0.6 clo is the same as that from a
        person in the actual environment.
        """
        return self._set

    @property
    def is_comfortable(self):
        """DataCollection of integers noting whether the input conditions are
        acceptable according to the assigned comfort_parameters.

        Values are one of the following:
            0 = uncomfortable
            1 = comfortable
        """
        return self._is_comfortable

    @property
    def thermal_condition(self):
        """DataCollection of integers noting the thermal status of a subject
        according to the assigned comfort_parameters.

        Values are one of the following:
            -1 = cold
             0 = netural
            +1 = hot
        """
        return self._is_comfortable

    @property
    def discomfort_reason(self):
        """DataCollection of integers noting the reason for discomfort
        according to the assigned comfort_parameters.

        Values are one of the following:
            -2 = too dry
            -1 = too cold
             0 = comfortable
            +1 = too hot
            +2 = too humid
        """
        return self._discomfort_reason

    @property
    def percent_comfortable(self):
        """The percent of time that is comfortabe according to
        the assigned comfort_parameters."""
        return self._percent_comfortable

    @property
    def percent_uncomfortable(self):
        """The percent of time that is not comfortabe according to
        the assigned comfort_parameters."""
        return self._percent_uncomfortable

    @property
    def percent_neutral(self):
        """The percent of time that the thermal_condiiton is neutral."""
        return self._percent_neutral

    @property
    def percent_cold(self):
        """The percent of time that the thermal_condiiton is cold."""
        return self._percent_cold

    @property
    def percent_hot(self):
        """The percent of time that the thermal_condiiton is hot."""
        return self._percent_hot

    @property
    def percent_dry(self):
        """The percent of time that the thermal_condiiton is too dry."""
        return self._percent_dry

    @property
    def percent_humid(self):
        """The percent of time that the thermal_condiiton is too humid."""
        return self._percent_humid

    @property
    def humidity_ratio(self):
        """DataCollection of humidity ratio for the input dry bulb and relative humidity.
        """
        return [humid_ratio_from_db_rh(db, rh) for db, rh in zip(
            self.air_temperature, self.rel_humidity)]

    @property
    def adjusted_air_temperature(self):
        """DataCollection of air temperatures that have been adjusted by the SET model
        to account for the effect of air speed [C].
        """
        return self._ta_adj

    @property
    def cooling_effect(self):
        """DataCollection of the cooling effect of the air speed in degrees Celcius.

        This is the difference between the air temperature and the
        adjusted air temperature [C].
        """
        return self._cooling_effect

    @property
    def heat_loss_conduction(self):
        """DataCollection of heat loss by conduction in [W]."""
        return self._heat_loss_conduction

    @property
    def heat_loss_sweating(self):
        """DataCollection of heat loss by sweating in [W]."""
        return self._heat_loss_sweating

    @property
    def heat_loss_latent_respiration(self):
        """DataCollection of heat loss by latent respiration in [W]."""
        return self._heat_loss_latent_respiration

    @property
    def heat_loss_dry_respiration(self):
        """DataCollection of heat loss by dry respiration in [W]."""
        return self._heat_loss_dry_respiration

    @property
    def heat_loss_radiation(self):
        """DataCollection of heat loss by radiation in [W]."""
        return self._heat_loss_radiation

    @property
    def heat_loss_convection(self):
        """DataCollection of heat loss by convection in [W]."""
        return self._heat_loss_convection

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """PMV comfort model representation."""
        return "PMV Comfort Model: {} values".format(self._calc_length)
