import abc
import datetime
import functools
import typing


MAX_GOALS = 7
MAX_BASE = MAX_GOALS // 2


class Encounter(typing.NamedTuple):
    """A match whose result is not given."""
    date: datetime.date    # Local date.
    home: str
    away: str
    region: str
    competition: str
    season: str


class Predictor(abc.ABC):
    """A prediction strategy."""

    def __init__(self, name):
        """Initialize the predictor."""
        self.name = name

    @abc.abstractmethod
    def feed_records(self, records):
        """Add match records to the database."""

    @abc.abstractmethod
    def predict(self, encounter):
        """Predict a match."""


def category(record):
    """Return a score category, given a record."""
    return category_from_score(record.match.score)


def category_from_score(score):
    """Return a score category, given a score."""
    home, away = score
    if home + away > MAX_GOALS:
        diff = min(abs(home - away), MAX_GOALS)
        base = MAX_BASE - diff // 2
        ceil = base + diff
        home, away = (ceil, base) if home >= away else (base, ceil)
    return home, away


@functools.lru_cache()
def categories():
    """Return an iterable of possible categories."""

    result = set()
    for home in range(0, MAX_GOALS + 1):
        for away in range(0, MAX_GOALS + 1):
            result.add(category_from_score((home, away)))

    def key(category):
        home, away = category
        return away - home, home

    return sorted(result, key=key)


def num_categories():
    """Return the number of possible categories."""
    return len(categories())
