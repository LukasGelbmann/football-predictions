"""Helpers for representing football matches."""


import datetime
import typing


# We assume that all matches start at this local time at the earliest, if the
# time is not specified.
EARLIEST_START = datetime.time(9)

LATEST_START = datetime.time.max

THREE_POINTS_ERA = {
    'argentina': 1995,
    'austria': 1995,
    'belgium': 1995,     # Second division was 1993.
    'brazil': 1995,
    'china': 1995,
    'denmark': 1995,
    'england': 1981,
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

LEAGUES = {
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


class Match(typing.NamedTuple):
    """A football match."""

    date: datetime.date    # Local date.
    home: str
    away: str
    home_goals: int
    away_goals: int

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
    utc_time: datetime.datetime = None
    forfeited: bool = None

    @property
    def score(self):
        """The full time score of the match."""
        return self.home_goals, self.away_goals


class MatchRecord(typing.NamedTuple):
    """A football match record with contextualizing data."""
    match: Match
    region: str
    competition: str
    season: str

    @property
    def date(self):
        """The date on which the match took place."""
        return self.match.date


def result(score):
    """Return 1, X or 2."""
    home, away = score
    if home > away:
        return '1'
    if home < away:
        return '2'
    return 'X'
