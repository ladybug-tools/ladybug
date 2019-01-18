# coding=utf-8
"""Comfort parameter base object."""


class ComfortParameter(object):
    """Thermal comfort parameter base class."""
    _model = None

    @property
    def comfort_model(self):
        """Return the name of the comfort model to which the parameters belong."""
        return self._model
