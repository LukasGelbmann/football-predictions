#!/usr/bin/env python3

"""Script to consolidate historical result data on disk.

This script requires Python 3.6 or higher."""


import collections
import csv
import datetime
import sys

import datetools
import football
import paths
import sources


def consolidate(all_sources):
    """Consolidate and store all seasons from the three-points era."""

    sources_by_region = collections.defaultdict(list)
    for source in all_sources:
        for region in source.regions():
            sources_by_region[region].append(source)

    num_regions = len(sources_by_region)

    print(f"Found {num_regions} region{'s' if num_regions != 1 else ''}.", flush=True)

    num_competitions = 0
    for region, region_sources in sorted(sources_by_region.items()):
        sources_by_competition = collections.defaultdict(list)
        for source in region_sources:
            for competition in source.competitions(region):
                sources_by_competition[competition].append(source)
        num_competitions += len(sources_by_competition)

        for competition, sources_seq in sorted(sources_by_competition.items()):
            consolidate_matches(competition, sources_seq)
            consolidate_fixtures(competition, sources_seq)

    print(
        f"Done consolidating {num_competitions} "
        f"competition{'s' if num_competitions != 1 else ''}.",
        flush=True,
    )


def consolidate_matches(competition, sources_iter):
    """Consolidate and store all matches from the three-points era."""

    filename = f'{competition.region}_{competition.name}.csv'
    path = paths.CONSOLIDATED_DIR / filename

    try:
        paths.CONSOLIDATED_DIR.mkdir(exist_ok=True)
    except OSError as exc:
        print("Couldn't make target directory:", exc, file=sys.stderr)
        return

    matches = collections.defaultdict(list)
    for source in sources_iter:
        for match in source.matches(competition):
            key = match.date, match.home, match.away
            matches[key].append(match)

    if not matches:
        return

    matches_iter = (
        consolidate_single(replicas, football.Match) for replicas in matches.values()
    )

    try:
        file = open(path, 'w', encoding='utf-8', newline='')
    except OSError as exc:
        print("Couldn't open CSV file to write to:", exc, file=sys.stderr)
        return

    with file:
        writer = csv.writer(file)
        for match in sorted(matches_iter, key=sort_key):
            writer.writerow(row_from_match(match))


def consolidate_fixtures(competition, sources_iter):
    """Consolidate and store all fixtures."""

    filename = f'{competition.region}_{competition.name}_fixtures.csv'
    path = paths.CONSOLIDATED_DIR / filename

    try:
        paths.CONSOLIDATED_DIR.mkdir(exist_ok=True)
    except OSError as exc:
        print("Couldn't make target directory:", exc, file=sys.stderr)
        return

    fixtures = collections.defaultdict(list)
    for source in sources_iter:
        for fixture in source.fixtures(competition):
            key = fixture.date, fixture.home, fixture.away
            fixtures[key].append(fixture)

    if not fixtures:
        return

    fixtures_iter = (
        consolidate_single(replicas, football.Fixture) for replicas in fixtures.values()
    )

    try:
        file = open(path, 'w', encoding='utf-8', newline='')
    except OSError as exc:
        print("Couldn't open CSV file for fixtures:", exc, file=sys.stderr)
        return

    with file:
        writer = csv.writer(file)
        for fixture in sorted(fixtures_iter, key=sort_key):
            writer.writerow(row_from_fixture(fixture))


def consolidate_single(replicas, data_type):
    """Consolidate a single item."""

    replicas_iter = iter(replicas)
    kwargs = next(replicas_iter)._asdict()
    for replica in replicas_iter:
        for key, value in replica._asdict().items():
            if value is None:
                continue

            if kwargs[key] is None:
                kwargs[key] = value
            elif kwargs[key] != value:
                print(
                    f"Conflict in {key}: {replica.date}, {replica.home} - "
                    f"{replica.away}",
                    file=sys.stderr,
                )

    return data_type(**kwargs)


def sort_key(item):
    """Return the sorting key for a match or fixture."""
    utc_time = item.utc_time or datetime.datetime.max
    return item.date, utc_time, item.home, item.away


def row_from_match(match):
    """Return an iterable that can be used to write a match to a CSV file."""
    replacements = {'utc_time': time_replacement(match.utc_time, match.date)}
    if match.forfeited is not None:
        replacements['forfeited'] = int(match.forfeited)
    return match._replace(**replacements)[1:]


def row_from_fixture(fixture):
    """Return an iterable that can be used to write a fixture to a CSV file."""
    utc_time_replacement = time_replacement(fixture.utc_time, fixture.date)
    return fixture._replace(utc_time=utc_time_replacement)[1:]


def time_replacement(utc_time, date):
    """Return a formatted string."""
    if utc_time is None:
        return None
    if utc_time.date() == date:
        return datetools.datetime_to_time_str(utc_time)
    return datetools.datetime_to_iso(utc_time)


def main():
    """Consolidate the data."""
    consolidate(sources.SOURCES)


if __name__ == '__main__':
    main()
