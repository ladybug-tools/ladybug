# coding=utf-8
"""Comfort datacollection base object."""


class ComfortDataCollection(object):
    """Thermal comfort datacollection base class."""
    _model = None

    def __init__(self):
        self._calc_length = 0
        self._is_computed = False

    @property
    def comfort_model(self):
        """Return the name of the model to which the comfort datacollection belongs."""
        return self._model
