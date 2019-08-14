"""Helpers for representing football matches."""


import datetime
import functools
import typing

import datetools


# We assume that all matches start at this local time at the earliest, if the
# time is not specified.
EARLIEST_START = datetime.time(9)

LATEST_START = datetime.time.max

SEASON_START_DATE = 7, 1    # Earliest start date for summer-to-summer seasons,
                            # with a few days in hand.

THREE_POINTS_ERA = {
    'argentina': 1995,
    'austria': 1995,
    'belgium': 1995,     # Second division was 1993.
    'brazil': 1995,
    'china': 1995,
    'denmark': 1995,
    'england': 1981,
    'europe': 2013,
    'finland': 1991,
    'france': 1994,      # Also in 1988-89.
    'germany': 1995,
    'greece': 1992,
    'ireland': 1993,     # Also in 1982-83.
    'italy': 1994,       # Serie A and Serie B.
    'japan': 1988,
    'mexico': 1995,
    'netherlands': 1995,
    'norway': 1988,
    'poland': 1995,
    'portugal': 1995,
    'romania': 1994,
    'russia': 1995,
    'scotland': 1994,    # Earlier for non-professional leagues.
    'spain': 1995,
    'sweden': 1990,
    'switzerland': 1995,
    'turkey': 1987,
    'usa': 1996,
}

LEAGUE_NAMES = {
    'argentina': ['primera'],
    'austria': ['bundesliga'],
    'belgium': ['1st-league'],
    'brazil': ['serie-a'],
    'china': ['super-league'],
    'denmark': ['superliga'],
    'england': ['premier', '2nd-league', '3rd-league', '4th-league',
                '5th-league'],
    'finland': ['veikkausliiga'],
    'france': ['1st-league', '2nd-league'],
    'germany': ['bundesliga', 'zweite'],
    'greece': ['1st-league'],
    'ireland': ['premier'],
    'italy': ['serie-a', 'serie-b'],
    'japan': ['j1'],
    'mexico': ['liga-mx'],
    'netherlands': ['eredivisie'],
    'norway': ['1st-league'],
    'poland': ['ekstraklasa'],
    'portugal': ['1st-league'],
    'romania': ['liga-1'],
    'russia': ['premier'],
    'scotland': ['1st-league', '2nd-league', '3rd-league', '4th-league'],
    'spain': ['primera', 'segunda'],
    'sweden': ['allsvenskan'],
    'switzerland': ['super-league'],
    'turkey': ['1st-league'],
    'usa': ['mls'],
}


class Competition(typing.NamedTuple):
    """A football competition."""
    region: str
    name: str


class Season(typing.NamedTuple):
    """A season of a competition."""

    start: int
    ends_following_year: bool = False

    @property
    def end(self):
        """The year when the season ends."""
        if self.ends_following_year:
            return self.start + 1
        return self.start

    def __str__(self):
        if self.start == self.end:
            return str(self.start)
        return f'{self.start}-{self.end % 100 :02}'

    @classmethod
    def from_str(cls, season_str):
        """Return the corresponding season."""

        start_str, sep, end_str = season_str.partition('-')
        start = int(start_str)

        if not sep:
            return cls(start)

        if int(end_str) != (start + 1) % 100:
            raise ValueError(f"weird season string {season_str!r}")
        return cls(start, ends_following_year=True)


class Match(typing.NamedTuple):
    """A football match."""

    competition: Competition
    date: datetime.date    # Local date.
    season: Season
    home: str
    away: str
    home_goals: int
    away_goals: int

    utc_time: datetime.datetime = None
    home_half_time: int = None
    away_half_time: int = None
    home_shots: int = None
    away_shots: int = None
    home_shots_on_target: int = None
    away_shots_on_target: int = None
    home_woodwork: int = None
    away_woodwork: int = None
    home_corners: int = None
    away_corners: int = None
    home_fouls_committed: int = None
    away_fouls_committed: int = None
    home_free_kicks_conceded: int = None
    away_free_kicks_conceded: int = None
    home_offsides: int = None
    away_offsides: int = None
    home_yellow: int = None
    away_yellow: int = None
    home_yellow_no_red: int = None
    away_yellow_no_red: int = None
    home_red: int = None
    away_red: int = None
    stage: str = None
    forfeited: bool = None

    @property
    def score(self):
        """The full time score of the match."""
        return self.home_goals, self.away_goals


class Fixture(typing.NamedTuple):
    """A scheduled football match."""

    competition: Competition
    date: datetime.date    # Local date.
    utc_time: datetime.datetime
    season: Season
    stage: str
    home: str
    away: str

    @classmethod
    def from_match(cls, match):
        """Return a Fixture, given a match."""
        return cls(match.competition, match.date, match.utc_time, match.season,
                   match.stage, match.home, match.away)


def result(score):
    """Return 1, X or 2."""
    home, away = score
    if home > away:
        return '1'
    if home < away:
        return '2'
    return 'X'


@functools.lru_cache()
def leagues(region):
    """Return a list of leagues."""
    return [Competition(region, name) for name in LEAGUE_NAMES[region]]


def current_season():
    """Return the latest season (summer-to-summer)."""
    return Season(latest_season_start(), ends_following_year=True)


def latest_season_start():
    """Return the year in which the latest season (summer-to-summer) starts.

    Switches to the next season with a few days in hand."""

    now = datetools.canonical_now()
    if (now.month, now.day) >= SEASON_START_DATE:
        return now.year
    return now.year - 1


@functools.lru_cache()
def league_size(competition):
    """Return a mapping from leagues to number of teams."""
    return {
        Competition('england', 'premier'): 20,
        Competition('germany', 'bundesliga'): 18,
    }[competition]


@functools.lru_cache()
def num_matches(competition):
    """Return a mapping from leagues to number of teams."""
    return {
        Competition('england', 'premier'): 38 * 10,
        Competition('germany', 'bundesliga'): 34 * 9,
    }[competition]
