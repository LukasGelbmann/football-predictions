"""Base classes related to data sources."""


import abc


class Source(abc.ABC):
    """A source of football data."""

    def __init__(self, name):
        """Initialize the source."""
        self.name = name

    @abc.abstractmethod
    def regions(self):
        """Return an iterable of regions."""

    @abc.abstractmethod
    def competitions(self, region):
        """Return an iterable of competitions for a region."""

    @abc.abstractmethod
    def matches(self, competition):
        """Return an iterable of all matches of a competition.

        Only include matches from the three-point era."""

    @abc.abstractmethod
    def fixtures(self, competition):
        """Return an iterable of all known fixtures."""
