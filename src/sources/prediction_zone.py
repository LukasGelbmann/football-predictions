"""Prediction Zone data source."""


import csv
import functools
import pathlib
import os
import re
import sys
import urllib.request

import datetools
import football
import paths
from sources import base


NAME = 'prediction-zone'

BASE_URL = 'https://prediction.zone/api'
BASE_DIR = f'{paths.DATA_DIR}/{NAME}'

START_YEAR = 2014

COMPETITION_STRS = {
    football.Competition('england', 'premier'): 'premierleague',
    football.Competition('europe', 'champions'): 'championsleague',
    football.Competition('germany', 'bundesliga'): 'bundesliga',
}

COMPETITION_NAMES = {
    'germany': ['bundesliga'],
    'europe': ['champions'],
    'england': ['premier'],
}


class Source(base.Source):
    """The Prediction Zone match data source."""

    def __init__(self, name=NAME):
        super().__init__(name)

    @staticmethod
    def regions():
        yield from COMPETITION_NAMES

    @staticmethod
    def competitions(region):
        for name in COMPETITION_NAMES.get(region, []):
            yield football.Competition(region, name)

    @staticmethod
    def matches(competition):
        for fields, season in get_fields(competition):
            match = match_from_fields(fields, competition, season)
            if match:
                yield match

    @staticmethod
    def fixtures(competition):
        for fields, season in get_fields(competition):
            fixture = fixture_from_fields(fields, competition, season)
            if fixture:
                yield fixture


def fetch(older_than=None):
    """Fetch raw data from the Internet."""

    if older_than is not None:
        raise NotImplementedError("age check")

    try:
        os.makedirs(BASE_DIR, exist_ok=True)
    except OSError as e:
        print("Couldn't make directory for downloads:", e, file=sys.stderr)
        return

    final_year = football.latest_season_start()
    for competition_str in COMPETITION_STRS.values():
        for season_str in season_strs(final_year):
            name = competition_str + season_str
            url = f'{BASE_URL}/{name}/get_matches?content=tnmr&all'
            path = f'{BASE_DIR}/{name}.csv'
            try:
                urllib.request.urlretrieve(url, path)
            except OSError as e:
                print("Couldn't fetch results:", e, file=sys.stderr)


def get_fields(competition):
    """Yield a (fields, season) pair for each row for a competition."""

    filepaths = paths.csv_files(pathlib.Path(BASE_DIR),
                                start=COMPETITION_STRS[competition])
    seasons = {path: extract_season(path) for path in filepaths}
    filepaths.sort(key=seasons.get)
    region = competition.region

    for path in filepaths:
        season = seasons[path]
        if season.start < football.THREE_POINTS_ERA[region]:
            print(f"Season {season} was before the three-points era in "
                  f"{region}.", file=sys.stderr)
            continue

        try:
            file = open(path, encoding='utf-8', newline='')
        except OSError as e:
            print("Couldn't open CSV file:", e, file=sys.stderr)
            continue

        with file:
            reader = csv.reader(file)
            for fields in reader:
                yield fields, season


def match_from_fields(fields, competition, season):
    """Return the corresponding match."""

    _, _, home, away, home_goals_str, away_goals_str = fields
    kwargs = get_kwargs(fields, competition, season)

    if not home_goals_str or not away_goals_str:
        if home_goals_str or away_goals_str:
            print(f"Only half a score: {kwargs['date']}, {home} - {away}",
                  file=sys.stderr)
        return None

    return football.Match(competition, **kwargs)


def fixture_from_fields(fields, competition, season):
    """Return the corresponding match."""

    *_, home_goals_str, away_goals_str = fields

    if home_goals_str or away_goals_str:
        return None

    kwargs = get_kwargs(fields, competition, season)
    return football.Fixture(competition, **kwargs)


def get_kwargs(fields, competition, season):
    """Return a keyword arguments mapping."""

    datetime_str, stage, home, away, home_goals_str, away_goals_str = fields
    kwargs = {}
    kwargs['season'] = season
    utc_time = kwargs['utc_time'] = datetools.datetime_from_iso(datetime_str)
    kwargs['date'] = datetools.date_from_utc_time(utc_time, competition.region)

    if '\ufeff' in stage:
        print(f"Contains BOM in stage: {kwargs['date']}, {home} - {away}",
              file=sys.stderr)
        stage = stage.replace('\ufeff', '')
    match = re.fullmatch(r"Round (\d+)", stage)
    if match:
        kwargs['stage'] = match[1]
    else:
        kwargs['stage'] = stage

    kwargs['home'] = home
    kwargs['away'] = away

    if home_goals_str:
        kwargs['home_goals'] = int(home_goals_str)
    if away_goals_str:
        kwargs['away_goals'] = int(away_goals_str)

    return kwargs


def extract_season(path):
    """Return the season, given a path."""
    stem = paths.stem(path)
    season_str = stem[-4:]
    start_short = int(season_str[:2])
    end_short = int(season_str[2:])
    if end_short != (start_short + 1) % 100:
        raise ValueError(f"can't make sense of season string {season_str!r}")
    if start_short >= 70:
        start = 1900 + start_short
    else:
        start = 2000 + start_short
    return football.Season(start, ends_following_year=True)


@functools.lru_cache()
def season_strs(final_year):
    """Return all valid season strings."""
    result = []
    for year in range(START_YEAR, final_year + 1):
        season_str = f'{year % 100 :02}{(year + 1) % 100 :02}'
        result.append(season_str)
    return result
