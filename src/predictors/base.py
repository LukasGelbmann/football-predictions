"""Prediction resources common to all modules in this package."""


import abc


class Predictor(abc.ABC):
    """A prediction strategy."""

    def __init__(self, name):
        """Initialize the predictor."""
        self.name = name

    @abc.abstractmethod
    def feed_match(self, match):
        """Add a match to the database."""

    @abc.abstractmethod
    def predict(self, fixture):
        """Predict a match."""
