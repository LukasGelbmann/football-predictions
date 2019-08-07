"""Access to football match data."""


import csv
import operator
import sys

import datetools
import football
import functools
import paths
import prediction
import prediction_zone


def regions():
    """Return an iterable of regions."""

    try:
        subdirs = paths.subdirs(paths.CONSOLIDATED_DIR)
    except OSError as e:
        print("Couldn't list subdirectories:", e, file=sys.stderr)
        return []

    return sorted(subdir.name for subdir in subdirs)


def competitions(region):
    """Return an iterable of competitions for a region."""

    region_dir = paths.CONSOLIDATED_DIR / region
    try:
        csv_paths = paths.csv_files(region_dir)
    except OSError as e:
        print("Couldn't list CSV files:", e, file=sys.stderr)
        return []

    def key(competition):
        if competition == 'premier':
            return '1st league'
        return competition

    result_set = {paths.extract_competition(path) for path in csv_paths}
    return sorted(result_set, key=key)


def seasons(region, competition):
    """Return an iterable of seasons for a competition."""

    region_dir = paths.CONSOLIDATED_DIR / region
    try:
        csv_paths = paths.csv_files(region_dir)
    except OSError as e:
        print("Couldn't list CSV files:", e, file=sys.stderr)
        return []

    result = []
    for path in csv_paths:
        if paths.extract_competition(path) == competition:
            result.append(paths.extract_season(path))
    return sorted(result)


def all_records():
    """Return all records in chronological order."""
    result = []
    for region in regions():
        result.extend(region_records(region))
    return sorted(result, key=operator.attrgetter('date'))


def region_records(region):
    """Yield all records of a region."""
    for competition in competitions(region):
        yield from competition_records(region, competition)


def competition_records(region, competition):
    """Yield all records of a competition."""
    for season in seasons(region, competition):
        yield from season_records(region, competition, season)


def season_records(region, competition, season):
    """Yield all records of a season."""
    for match in season_matches(region, competition, season):
        yield football.MatchRecord(match, region, competition, season)


def competition_matches(region, competition):
    """Yield all matches of a competition."""
    for season in seasons(region, competition):
        yield from season_matches(region, competition, season)


def season_matches(region, competition, season):
    """Yield all matches of a season."""

    path = paths.season_csv_path(region, competition, season)
    try:
        file = open(path, encoding='utf-8', newline='')
    except OSError as e:
        print("Couldn't open CSV file:", e, file=sys.stderr)
        return

    with file:
        reader = csv.DictReader(file, football.Match._fields)
        for fields in reader:
            for name, value in fields.copy().items():
                fields[name] = parse_field(name, value)
            yield football.Match(**fields)


def season_encounters(region, competition, season):
    """Yield all future encounters of a season."""
    path = prediction_zone.file_path(region, competition, season)
    try:
        file = open(path, encoding='utf-8', newline='')
    except OSError as e:
        print("Couldn't open calendar CSV file:", e, file=sys.stderr)
        return

    with file:
        reader = csv.reader(file)
        for fields in reader:
            datetime_str, _, home, away, _, _ = fields
            date = datetools.datetime_from_iso(datetime_str).date()
            yield prediction.Encounter(date, home, away, region, competition,
                                       season)


def parse_field(name, value):
    """Convert a field to the correct data type."""
    if name == 'date':
        return datetools.date_from_iso(value)
    if name in ('home', 'away'):
        return value
    if name in ('home_goals', 'away_goals'):
        return int(value)
    if not value:
        return None
    if name == 'utc_time':
        return datetools.datetime_from_iso(value)
    if name == 'forfeited':
        if value not in {'0', '1'}:
            raise ValueError(f"Boolean field should be 0 or 1, is {value!r}")
        return bool(int(value))
    return int(value)


def username():
    """Return our username."""
    username, _ = credentials()
    return username


def password():
    """Return our password."""
    _, password = credentials()
    return password


@functools.lru_cache()
def credentials():
    """Return our username and password."""
    path = paths.DATA_DIR / 'credentials.txt'
    try:
        file = open(path, encoding='utf-8', newline='')
    except OSError as e:
        print("Couldn't open credentials file:", e, file=sys.stderr)
        raise
    return tuple(line.strip() for line in file)
