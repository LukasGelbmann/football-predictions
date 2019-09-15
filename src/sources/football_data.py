"""'Football Data' data source."""


import csv
import functools
import itertools
import pathlib
import pprint
import sys

import datetools
import football
import paths
from sources import base


NAME = 'football-data'

BASE_DIR = f'{paths.DATA_DIR}/{NAME}'

START_YEAR = 1993

TEAM_SYNONYMS = {
    'england': {
        "Brighton": "Brighton & Hove Albion",
        "Cardiff": "Cardiff City",
        "Huddersfield": "Huddersfield Town",
        "Hull": "Hull City",
        "Leicester": "Leicester City",
        "Man City": "Manchester City",
        "Man United": "Manchester United",
        "Middlesboro": "Middlesbrough",
        "Newcastle": "Newcastle United",
        "Norwich": "Norwich City",
        "Nott'm Forest": "Nottingham Forest",
        "QPR": "Queens Park Rangers",
        "Sheffield Weds": "Sheffield Wednesday",
        "Stoke": "Stoke City",
        "Swansea": "Swansea City",
        "Tottenham": "Tottenham Hotspur",
        "West Brom": "West Bromwich Albion",
        "West Ham": "West Ham United",
        "Wolves": "Wolverhampton",
    },
    'germany': {
        "Augsburg": "FC Augsburg",
        "Bayern Munich": "Bayern München",
        "Dortmund": "Borussia Dortmund",
        "Dusseldorf": "Fortuna Düsseldorf",
        "Ein Frankfurt": "Eintracht Frankfurt",
        "F Koln": "1. FC Köln",
        "FC Koln": "1. FC Köln",
        "Fortuna Dusseldorf": "Fortuna Düsseldorf",
        "Freiburg": "SC Freiburg",
        "Greuther Furth": "Greuther Fürth",
        "Hamburg": "Hamburger SV",
        "Hannover": "Hannover 96",
        "Hertha": "Hertha BSC",
        "Hoffenheim": "1899 Hoffenheim",
        "Leverkusen": "Bayer Leverkusen",
        "M'gladbach": "Borussia Mönchengladbach",
        "Mainz": "Mainz 05",
        "Munich 1860": "1860 München",
        "Nurnberg": "1. FC Nürnberg",
        "Paderborn": "SC Paderborn",
        "St Pauli": "St. Pauli",
        "Stuttgart": "VfB Stuttgart",
        "Wolfsburg": "VfL Wolfsburg",
    },
}

LEAGUE_STRS = {
    'belgium': ['B1'],
    'england': ['E0', 'E1', 'E2', 'E3', 'EC'],
    'france': ['F1', 'F2'],
    'germany': ['D1', 'D2'],
    'greece': ['G1'],
    'italy': ['I1', 'I2'],
    'netherlands': ['N1'],
    'portugal': ['P1'],
    'scotland': ['SC0', 'SC1', 'SC2', 'SC3'],
    'spain': ['SP1', 'SP2'],
    'turkey': ['T1'],
}

EXTRA_REGIONS = {
    'argentina': 'ARG',
    'austria': 'AUT',
    'brazil': 'BRA',
    'china': 'CHN',
    'denmark': 'DNK',
    'finland': 'FIN',
    'ireland': 'IRL',
    'japan': 'JPN',
    'mexico': 'MEX',
    'norway': 'NOR',
    'poland': 'POL',
    'romania': 'ROU',
    'russia': 'RUS',
    'sweden': 'SWE',
    'switzerland': 'SWZ',
    'usa': 'USA',
}

TEAM_FIELDS = {'home': ['HomeTeam', 'Home', 'HT'], 'away': ['AwayTeam', 'Away', 'AT']}

SCORE_FIELDS = {'home_goals': ['FTHG', 'HG'], 'away_goals': ['FTAG', 'AG']}

INT_FIELDS = {
    'home_half_time': 'HTHG',
    'away_half_time': 'HTAG',
    'home_shots': 'HS',
    'away_shots': 'AS',
    'home_shots_on_target': 'HST',
    'away_shots_on_target': 'AST',
    'home_woodwork': 'HHW',
    'away_woodwork': 'AHW',
    'home_corners': 'HC',
    'away_corners': 'AC',
    'home_fouls_committed': 'HF',
    'away_fouls_committed': 'AF',
    'home_free_kicks_conceded': 'HFKC',
    'away_free_kicks_conceded': 'AFKC',
    'home_offsides': 'HO',
    'away_offsides': 'AO',
    'home_yellow': 'HY',
    'away_yellow': 'AY',
    'home_red': 'HR',
    'away_red': 'AR',
}


class Source(base.Source):
    """The Prediction Zone match data source."""

    def __init__(self, name=NAME):
        super().__init__(name)

    @staticmethod
    def regions():
        return itertools.chain(LEAGUE_STRS, EXTRA_REGIONS)

    @staticmethod
    def competitions(region):
        if region in LEAGUE_STRS:
            yield from strs_by_competition(region)
        elif region in EXTRA_REGIONS:
            yield football.leagues(region)[0]

    @staticmethod
    def matches(competition):
        region = competition.region
        if region in EXTRA_REGIONS:
            if competition != football.leagues(region)[0]:
                return
            path = f'{BASE_DIR}/{EXTRA_REGIONS[region]}.csv'
            yield from matches_from_csv(path, competition)
            return

        if region not in LEAGUE_STRS:
            return

        league_str = strs_by_competition(competition.region).get(competition)
        if league_str is None:
            return

        final_year = football.latest_season_start()
        for season, season_str in season_strs(final_year):
            if season.start < football.THREE_POINTS_ERA[region]:
                continue

            path = f'{BASE_DIR}/{season_str}/{league_str}.csv'
            try:
                season_exists = pathlib.Path(path).is_file()
            except OSError as exc:
                print("Couldn't check for file existence:", exc, file=sys.stderr)
                continue

            if season_exists:
                yield from matches_from_csv(path, competition, season)

    @staticmethod
    def fixtures(competition):
        return []


@functools.lru_cache()
def strs_by_competition(region):
    """Return a mapping from competition to string."""
    return dict(zip(football.leagues(region), LEAGUE_STRS[region]))


def matches_from_csv(path, competition, season=None):
    """Yield all matches, given a path to a CSV file."""

    try:
        file = open(path, encoding='utf-8', errors='ignore', newline='')
    except OSError as exc:
        print("Couldn't open CSV file:", exc, file=sys.stderr)
        return

    with file:
        reader = csv.DictReader(file)
        for fields in reader:
            match = match_from_fields(fields, competition, season)
            if match:
                yield match


def match_from_fields(fields, competition, season, check_consistency=False):
    """Return a football.Match object."""

    region = competition.region
    int_fields = get_int_fields(region)
    half_time_is_full_time = False
    kwargs = {}

    for target_name, source_names in SCORE_FIELDS.items():
        for name in source_names:
            value = fields.get(name)
            if value:
                kwargs[target_name] = int(value)
                break

    if len(kwargs) == 1:
        print_fields(fields, "Score fields are inconsistent")
        return None

    if not kwargs:
        home_half_time = None
        home_half_time_str = fields.get(int_fields['home_half_time'])
        if home_half_time_str:
            home_half_time = int(home_half_time_str)

        away_half_time = None
        away_half_time_str = fields.get(int_fields['away_half_time'])
        if away_half_time_str:
            away_half_time = int(away_half_time_str)

        if home_half_time is None or away_half_time is None:
            if home_half_time is not None or away_half_time is not None:
                print_fields(fields, "Half time fields are inconsistent")
            return None

        if {home_half_time, away_half_time} == {3, 0}:
            half_time_is_full_time = True
            kwargs['forfeited'] = True
        else:
            print_fields(fields, "Match seems abandoned")
            return None

    kwargs['date'], kwargs['utc_time'] = date_and_utc_time(fields, region)

    for target_name, source_names in TEAM_FIELDS.items():
        for name in source_names:
            value = fields.get(name)
            if not value:
                continue
            value = value.strip()
            if region in TEAM_SYNONYMS:
                value = TEAM_SYNONYMS[region].get(value, value)
            kwargs[target_name] = value
            break

    for target_name, source_name in int_fields.items():
        value = fields.get(source_name)
        if value:
            kwargs[target_name] = int(value)

    if half_time_is_full_time:
        kwargs['home_goals'] = kwargs.pop('home_half_time')
        kwargs['away_goals'] = kwargs.pop('away_half_time')

    if check_consistency:
        for home_name, away_name in kwarg_pairs():
            if (home_name in kwargs) != (away_name in kwargs):
                print_fields(fields, "Field pairs are inconsistent")
                break

    if kwargs.get('forfeited'):
        print(
            f"Treating match as forfeited: {kwargs['date']}, {kwargs['home']} "
            f"- {kwargs['away']} ({kwargs['home_goals']}:{kwargs['away_goals']})",
            file=sys.stderr,
        )

    season_str = fields.get('Season')
    if season_str:
        parsed_season = kwargs['season'] = season_from_str(season_str, fields)
        if season is not None and season != parsed_season:
            print_fields(fields, "Unexpected season")
    else:
        kwargs['season'] = season

    if kwargs['season'].start < football.THREE_POINTS_ERA[region]:
        print_fields(fields, "Before three-points era")
        return None

    return football.Match(competition, **kwargs)


def date_and_utc_time(fields, region, check_plausibility=True):
    """Return local date and UTC datetime."""

    date_str = fields['Date']
    time_str = fields.get('Time')

    if time_str:
        datetime_str = f'{date_str} {time_str}'
        utc_time = datetools.parse_datetime(datetime_str, '%d/%m/%Y %H:%M')
        timezone = datetools.TIMEZONES[region]
        region_time = datetools.from_utc(utc_time, timezone)
        if check_plausibility:
            earliest_local_time = region_time.replace(tzinfo=None)
            max_time_diff = datetools.MAX_TIME_DIFF[region]
            latest_local_time = earliest_local_time + max_time_diff
            dates_match = earliest_local_time.date() == latest_local_time.date()
            if dates_match and latest_local_time.time() < football.EARLIEST_START:
                print_fields(fields, "Strange time to play football")
        date = region_time.date()
        return date, utc_time

    date = None
    for format_str in '%d/%m/%y', '%d/%m/%Y':
        try:
            date = datetools.parse_date(date_str, format_str)
        except ValueError:
            pass
        else:
            break

    if date is None:
        raise ValueError(f"Couldn't parse date: {date_str!r}")

    return date, None


def season_from_str(season_str, fields):
    """Return the season, given a fields mapping."""
    start, _, end = season_str.partition('/')
    start = int(start)
    if not end:
        return football.Season(start)
    end = int(end)
    if end != start + 1:
        print_fields(fields, "Weird season string")
    return football.Season(start, ends_following_year=True)


def print_fields(fields, explanation):
    """Pretty print fields to stderr."""
    print(f'{explanation}:', file=sys.stderr)
    pprint.pprint(fields, stream=sys.stderr)
    print(file=sys.stderr)


@functools.lru_cache()
def get_int_fields(region):
    """Return a mapping from target field names to source field names."""
    if region in {'england', 'scotland'}:
        return int_fields_uk()
    return INT_FIELDS


@functools.lru_cache()
def int_fields_uk():
    """Return a mapping from UK target field names to source field names."""
    int_fields = INT_FIELDS.copy()
    del int_fields['home_yellow']
    del int_fields['away_yellow']
    int_fields['home_yellow_no_red'] = 'HY'
    int_fields['away_yellow_no_red'] = 'AY'
    return int_fields


@functools.lru_cache()
def kwarg_pairs():
    """Return (home, away) pairs for all match keyword argument names."""
    kwargs_keys = (
        set(TEAM_FIELDS) | set(SCORE_FIELDS) | set(INT_FIELDS) | set(int_fields_uk())
    )
    kwargs_keys_home = {key for key in kwargs_keys if key.startswith('home')}
    kwargs_keys_away = {key for key in kwargs_keys if key.startswith('away')}
    pairs = list(zip(sorted(kwargs_keys_home), sorted(kwargs_keys_away)))
    assert all(home[4:] == away[4:] for home, away in pairs)
    return pairs


@functools.lru_cache()
def season_strs(final_year):
    """Return all valid seasons and strings."""
    result = []
    for year in range(START_YEAR, final_year + 1):
        season = football.Season(year, ends_following_year=True)
        season_str = f'{year % 100 :02}{(year + 1) % 100 :02}'
        result.append((season, season_str))
    return result
