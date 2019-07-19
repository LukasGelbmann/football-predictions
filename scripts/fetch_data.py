#!/usr/bin/env python3

"""Script to fetch historical result data from disk and from the Internet.

This script requires Python 3.6 or higher."""


import csv
import collections
import shutil
import sys

import fetching
import football
import paths


def store_all_as_csv(source):
    """Load all seasons from a source and and store them in CSV files."""
    total_seasons = 0
    for region in source.regions():
        num_seasons = 0
        for competition in source.competitions(region):
            for season in source.seasons(region, competition):
                store_as_csv(region, competition, season, source)
                num_seasons += 1
        print(f"Stored {num_seasons} "
              f"season{'s' if num_seasons != 1 else ''} from {source.name} "
              f"in {region}")
        total_seasons += num_seasons
    print(f"Done storing {total_seasons} "
          f"season{'s' if total_seasons != 1 else ''}")
    print()


def store_as_csv(region, competition, season, source):
    """Load a season's results and store them in a CSV file."""

    file_dir = paths.DATA_DIR / source.name / region
    path = file_dir / f'{competition}_{season}.csv'

    try:
        file_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print("Couldn't make directory for results:", e, file=sys.stderr)
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


def consolidate(sources):
    """Consolidate and store all seasons from the three-point era."""

    regions = set()
    sources_by_region = collections.defaultdict(list)
    for source in sources:
        source_dir = paths.DATA_DIR / source.name

        try:
            contents = source_dir.iterdir()
        except OSError as e:
            print("Couldn't list directory contents:", e, file=sys.stderr)
            return

        new_regions = set()
        for path in contents:
            try:
                is_dir = path.is_dir()
            except OSError as e:
                print("Couldn't check is_dir():", e, file=sys.stderr)
                return

            if is_dir:
                new_regions.add(path.name)

        regions.update(new_regions)
        for region in new_regions:
            sources_by_region[region].append(source)

    num_regions = 0
    for region in sorted(regions):
        consolidate_region(region, sources_by_region[region])
        num_regions += 1

    print(f"Done consolidating {num_regions} "
          f"region{'s' if num_regions != 1 else ''}")



def consolidate_region(region, sources):
    """Consolidate and store a region's seasons from the three-point era."""

    target_dir = paths.CONSOLIDATED_DIR / region
    num_seasons = 0

    for source in sources:
        # Lazy implementation for now.

        source_dir = paths.DATA_DIR / source.name / region

        try:
            csv_contents = source_dir.glob('*.csv')
        except OSError as e:
            print("Couldn't list directory's CSV files:", e, file=sys.stderr)
            return

        for source_path in csv_contents:
            try:
                is_file = source_path.is_file()
            except OSError as e:
                print("Couldn't check is_file():", e, file=sys.stderr)
                return

            if not is_file:
                continue

            parts = source_path.stem.split('_')
            start = int(parts[-1][:4])
            if start < football.THREE_POINTS_ERA[region]:
                continue

            try:
                target_dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                print("Couldn't make target directory:", e, file=sys.stderr)
                return

            target_path = target_dir / source_path.name
            try:
                shutil.copy(source_path, target_path)
            except OSError as e:
                print("Couldn't copy CSV file:", e, file=sys.stderr)
                return

            num_seasons += 1

        break

    print(f"Consolidated {num_seasons} "
          f"season{'s' if num_seasons != 1 else ''} in {region}")


def main():
    """Fetch the data."""
    for source in fetching.sources:
        store_all_as_csv(source)
    consolidate(fetching.sources)


if __name__ == '__main__':
    main()
