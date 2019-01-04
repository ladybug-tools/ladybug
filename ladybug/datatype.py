# coding=utf-8
"""Ladybug data types."""
from __future__ import division

from .types.generic import Unitless, GenericType, DaysSinceLastSnowfall

from .types.percentage import Percentage, PercentagePeopleDissatisfied, \
    ThermalComfort, RelativeHumidity, TotalSkyCover, OpaqueSkyCover, \
    AerosolOpticalDepth, Albedo, LiquidPrecipitationQuantity

from .types.angle import Angle, WindDirection

from .types.distance import Distance, Visibility, CeilingHeight, \
    PrecipitableWater, SnowDepth, LiquidPrecipitationDepth

from .types.area import Area

from .types.volume import Volume

from .types.energy import Energy

from .types.energyintensity import EnergyIntensity, Radiation, \
    GlobalHorizontalRadiation, DirectNormalRadiation, DiffuseHorizontalRadiation, \
    DirectHorizontalRadiation, ExtraterrestrialHorizontalRadiation, \
    ExtraterrestrialDirectNormalRadiation

from .types.energyflux import EnergyFlux, MetabolicRate, Irradiance, \
    GlobalHorizontalIrradiance, DirectNormalIrradiance, DiffuseHorizontalIrradiance, \
    DirectHorizontalIrradiance, HorizontalInfraredRadiationIntensity

from .types.power import Power

from .types.illuminance import Illuminance, GlobalHorizontalIlluminance, \
    DirectNormalIlluminance, DiffuseHorizontalIlluminance

from .types.luminance import Luminance, ZenithLuminance

from .types.temperature import Temperature, DryBulbTemperature, DewPointTemperature, \
    SkyTemperature, AirTemperature, RadiantTemperature, OperativeTemperature, \
    MeanRadiantTemperature, StandardEffectiveTemperature, \
    UniversalThermalClimateIndex

from .types.thermalcondition import ThermalCondition, PredictedMeanVote, UTCICondition

from .types.pressure import Pressure, AtmosphericStationPressure

from .types.mass import Mass

from .types.speed import Speed, WindSpeed, AirSpeed

from .types.massflowrate import MassFlowRate

from .types.volumeflowrate import VolumeFlowRate

from .types.rvalue import RValue, ClothingInsulation

from .types.uvalue import UValue

from copy import deepcopy


class DataTypes(object):
    """Available data type classes organized by full name of the data type."""
    TYPES = {
        'Percentage': Percentage,
        'Temperature': Temperature,
        'Distance': Distance,
        'Area': Area,
        'Volume': Volume,
        'Pressure': Pressure,
        'Energy': Energy,
        'EnergyIntensity': EnergyIntensity,
        'Power': Power,
        'EnergyFlux': EnergyFlux,
        'Illuminance': Illuminance,
        'Luminance': Luminance,
        'Angle': Angle,
        'Mass': Mass,
        'Speed': Speed,
        'VolumeFlowRate': VolumeFlowRate,
        'MassFlowRate': MassFlowRate,
        'UValue': UValue,
        'RValue': RValue,
        'ThermalCondition': ThermalCondition,
        'DryBulbTemperature': DryBulbTemperature,
        'DewPointTemperature': DewPointTemperature,
        'SkyTemperature': SkyTemperature,
        'AirTemperature': AirTemperature,
        'RadiantTemperature': RadiantTemperature,
        'OperativeTemperature': OperativeTemperature,
        'MeanRadiantTemperature': MeanRadiantTemperature,
        'StandardEffectiveTemperature': StandardEffectiveTemperature,
        'UniversalThermalClimateIndex': UniversalThermalClimateIndex,
        'PredictedMeanVote': PredictedMeanVote,
        'UTCICondition': UTCICondition,
        'ThermalComfort': ThermalComfort,
        'PercentagePeopleDissatisfied': PercentagePeopleDissatisfied,
        'RelativeHumidity': RelativeHumidity,
        'TotalSkyCover': TotalSkyCover,
        'OpaqueSkyCover': OpaqueSkyCover,
        'AerosolOpticalDepth': AerosolOpticalDepth,
        'Albedo': Albedo,
        'LiquidPrecipitationQuantity': LiquidPrecipitationQuantity,
        'AtmosphericStationPressure': AtmosphericStationPressure,
        'Radiation': Radiation,
        'GlobalHorizontalRadiation': GlobalHorizontalRadiation,
        'DirectNormalRadiation': DirectNormalRadiation,
        'DiffuseHorizontalRadiation': DiffuseHorizontalRadiation,
        'DirectHorizontalRadiation': DirectHorizontalRadiation,
        'ExtraterrestrialHorizontalRadiation': ExtraterrestrialHorizontalRadiation,
        'ExtraterrestrialDirectNormalRadiation': ExtraterrestrialDirectNormalRadiation,
        'Irradiance': Irradiance,
        'GlobalHorizontalIrradiance': GlobalHorizontalIrradiance,
        'DirectNormalIrradiance': DirectNormalIrradiance,
        'DiffuseHorizontalIrradiance': DiffuseHorizontalIrradiance,
        'DirectHorizontalIrradiance': DirectHorizontalIrradiance,
        'HorizontalInfraredRadiationIntensity': HorizontalInfraredRadiationIntensity,
        'GlobalHorizontalIlluminance': GlobalHorizontalIlluminance,
        'DirectNormalIlluminance': DirectNormalIlluminance,
        'DiffuseHorizontalIlluminance': DiffuseHorizontalIlluminance,
        'ZenithLuminance': ZenithLuminance,
        'WindDirection': WindDirection,
        'WindSpeed': WindSpeed,
        'AirSpeed': AirSpeed,
        'Visibility': Visibility,
        'CeilingHeight': CeilingHeight,
        'PrecipitableWater': PrecipitableWater,
        'SnowDepth': SnowDepth,
        'LiquidPrecipitationDepth': LiquidPrecipitationDepth,
        'DaysSinceLastSnowfall': DaysSinceLastSnowfall,
        'ClothingInsulation': ClothingInsulation,
        'MetabolicRate': MetabolicRate
        }
    BASETYPES = (
        Temperature(),
        Percentage(),
        Distance(),
        Area(),
        Volume(),
        Pressure(),
        Energy(),
        EnergyIntensity(),
        Power(),
        EnergyFlux(),
        Illuminance(),
        Luminance(),
        Angle(),
        Mass(),
        Speed(),
        VolumeFlowRate(),
        MassFlowRate(),
        UValue(),
        RValue(),
        ThermalCondition()
    )

    @classmethod
    def all_possible_units(cls):
        """Return a text string indicating all possible units."""
        unit_txt = []
        for base_d_type in cls.BASETYPES:
            unit_list = ', '.join(base_d_type.units)
            unit_txt.append('{}: {}'.format(base_d_type.name, unit_list))
        return '\n'.join(unit_txt)

    @classmethod
    def type_by_name(cls, type_name):
        """Return a class instance of a given data type using the name of the type.

        The type_name can be either the class name or the name property of the type.
        """
        assert isinstance(type_name, str), \
            'type_name must be a text string got {}'.format(type(type_name))
        data_types = cls.TYPES
        formatted_name = type_name.title().replace(' ', '')
        d_type = None

        if type_name in data_types:
            statement = 'd_type = {}()'.format(type_name)
            exec(statement, data_types)
            d_type = data_types['d_type']
        elif formatted_name in data_types:
            statement = 'd_type = {}()'.format(formatted_name)
            exec(statement, data_types)
            d_type = data_types['d_type']
        return d_type

    @classmethod
    def type_by_unit(cls, unit_name):
        """Return a class instance of a given data type using the name of the unit.

        Note this method can only return fundamental classes (those that inherit
        directly from DataTypeBase).
        """
        assert isinstance(unit_name, str), \
            'unit_name must be a text string got {}'.format(type(unit_name))
        d_type = None
        for base_d_type in cls.BASETYPES:
            if unit_name in base_d_type.units:
                d_type = deepcopy(base_d_type)
        return d_type

    @classmethod
    def type_by_name_and_unit(cls, type_name, unit=None):
        """Return a class instance of a given data type using the tpye_name and unit.

        This method will always return a DataType object.  If an existing one cannot be
        found by name, it will be found by unit, and if neither methods find an
        existing DataType, a generic one will be returned.
        """
        d_type = cls.type_by_name(type_name)
        if d_type:
            d_type.is_unit_acceptable(unit, True)
            return d_type
        elif unit:
            d_type = cls.type_by_unit(unit)
            if d_type:
                d_type.name = type_name
                return d_type
            else:
                return GenericType(type_name, unit)
        else:
            return Unitless(type_name)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """DataTypes representation."""
        types = ('{}'.format(key) for key in self.TYPES)
        return '\n'.join(types)
