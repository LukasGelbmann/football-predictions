#!/usr/bin/env python3

"""Script to load historical result data from the Internet.

This script requires Python 3.6 or higher."""


import csv
import sys

import paths
import sources


def store_all_as_csv(source):
    """Load all seasons from a source and and store them in CSV files."""
    num_seasons = 0
    for region in source.regions:
        for competition in source.get_competitions(region):
            for season in source.get_seasons(region, competition):
                store_as_csv(region, competition, season, source)
                num_seasons += 1
    print(f"Stored {num_seasons} season{'s' if num_seasons != 0 else ''}",
          file=sys.stderr)


def store_as_csv(region, competition, season, source):
    """Load a season's results and store them in a CSV file."""

    file_dir = paths.DATA_DIR / source.name / region
    path = file_dir / f'{competition}_{season}.csv'

    try:
        file_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print("Couldn't make directory:", e, file=sys.stderr)
        return

    try:
        file = open(path, 'w', encoding='utf-8', newline='')
    except OSError as e:
        print("Couldn't open CSV file:", e, file=sys.stderr)
        return

    with file:
        writer = csv.writer(file, lineterminator='\n')
        matches = source.fetch_season(region, competition, season)
        writer.writerows(matches)

    print(f"Stored {source.name}, {region}, {competition}, {season}",
          file=sys.stderr)


def main():
    """Load the data."""
    store_all_as_csv(sources.football_data_local)


if __name__ == '__main__':
    main()
