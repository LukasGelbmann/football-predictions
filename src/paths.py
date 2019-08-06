"""Path-related resources."""


import os
import pathlib


# Path().resolve() isn't used here because it doesn't work in PyPy 3.6 for
# Windows.
HERE = pathlib.Path(os.path.realpath(__file__)).parent
DATA_DIR = HERE.parent / 'data'
CONSOLIDATED_DIR = DATA_DIR / 'consolidated'


def subdirs(path):
    """Return an iterable of subdirectory paths.

    May raise an OSError."""

    return sorted(item for item in path.iterdir() if item.is_dir())


def csv_files(path):
    """Return an iterable of CSV files in a directory.

    May raise an OSError."""

    return sorted(item for item in path.glob('*.csv') if item.is_file())


def season_csv_path(region, competition, season, source_dir=CONSOLIDATED_DIR):
    """Return the path for a season's CSV file."""
    filename = f'{competition}_{season}.csv'
    return source_dir / region / filename


def extract_competition(path):
    """Return the competition, given a file path."""
    return path.stem.split('_')[0]


def extract_season(path):
    """Return the season, given a file path."""
    return path.stem.split('_')[1]


def extract_start_year(path):
    """Return the season's start year, given a file path."""
    return int(extract_season(path)[:4])
