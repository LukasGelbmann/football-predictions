"""Access to football match data."""


import csv
import operator
import sys

import datetools
import football
import paths


def matches():
    """Return all matches ordered by date."""
    result = []
    for competition in competitions():
        for match in competition_matches(competition):
            result.append(match)
    return sorted(result, key=operator.attrgetter('date'))


def competitions():
    """Return an iterable of competitions."""

    try:
        csv_paths = paths.csv_files(paths.CONSOLIDATED_DIR)
    except OSError as e:
        print("Couldn't list CSV files:", e, file=sys.stderr)
        return []

    def key(competition):
        if competition.name == 'premier':
            return football.Competition(competition.region, '1st-league')
        return competition

    result_set = {extract_competition(path) for path in csv_paths}
    return sorted(result_set, key=key)


def competition_matches(competition):
    """Yield all matches of a competition."""
    path = matches_csv_path(competition)
    for fields in get_fields(path, football.Match):
        yield football.Match(competition, **fields)


def competition_fixtures(competition):
    """Yield all future fixtures of a competition."""
    path = fixtures_csv_path(competition)
    for fields in get_fields(path, football.Fixture):
        yield football.Fixture(competition, **fields)


def season_fixtures(competition, season):
    """Yield all future fixtures of a season."""
    for fixture in competition_fixtures(competition):
        if fixture.season == season:
            yield fixture


def get_fields(path, data_type):
    """Yield all parsed fields sequences of a CSV file."""

    try:
        file = open(path, encoding='utf-8', newline='')
    except OSError as e:
        print("Couldn't open CSV file:", e, file=sys.stderr)
        return

    with file:
        reader = csv.DictReader(file, data_type._fields[1:])
        for fields in reader:
            new_fields = {}
            for name, value in fields.items():
                new_fields[name] = parse_field(name, value,
                                               new_fields.get('date'))
            yield new_fields


def parse_field(name, value, date):
    """Convert a field to the correct data type."""
    if name == 'date':
        return datetools.date_from_iso(value)
    if name == 'season':
        return football.Season.from_str(value)
    if name in ('home', 'away', 'stage'):
        return value
    if name in ('home_goals', 'away_goals'):
        # Mandatory int fields.
        return int(value)
    if not value:
        return None
    if name == 'utc_time':
        try:
            return datetools.datetime_from_time_str(value, date)
        except ValueError:
            pass
        return datetools.datetime_from_iso(value)
    if name == 'forfeited':
        if value not in {'0', '1'}:
            raise ValueError(f"Boolean field should be 0 or 1, is {value!r}")
        return bool(int(value))
    return int(value)


def extract_competition(path):
    """Return the competition, given a file path."""
    region, name, *_ = path.stem.split('_')
    return football.Competition(region, name)


def matches_csv_path(competition):
    """Return the path for a competition's CSV file."""
    filename = f'{competition.region}_{competition.name}.csv'
    return paths.CONSOLIDATED_DIR / filename


def fixtures_csv_path(competition):
    """Return the path for a competition's CSV file."""
    filename = f'{competition.region}_{competition.name}_fixtures.csv'
    return paths.CONSOLIDATED_DIR / filename
