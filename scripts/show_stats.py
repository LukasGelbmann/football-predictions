#!/usr/bin/env python3

"""Script to show statistics of historical football data.

This script requires Python 3.6 or higher."""


import collections
import statistics

import data
import football
import prediction


UPPERCASE_REGIONS = {'USA'}


def print_region_stats(region, matches_by_competition):
    """Print statistics for a region."""

    if len(matches_by_competition) == 1:
        print_title(region.title())
    else:
        match_lists = matches_by_competition.values()
        all_matches = [match for matches in match_lists for match in matches]
        print_stats(region.title(), all_matches)

    for competition, matches in matches_by_competition.items():
        print_stats(competition, matches, level=2)


def print_stats(title, matches, level=1):
    """Print statistics for a set of matches."""

    print_title(title, level)

    teams = set()
    for match in matches:
        teams.add(match.home)
        teams.add(match.away)
    print("Number of teams:", len(teams))

    print_result_frequencies(matches)

    for name, field_type in football.Match._field_types.items():
        if not issubclass(field_type, int) or issubclass(field_type, bool):
            continue
        values = (getattr(match, name) for match in matches)
        valid = [value for value in values if value is not None]
        if not valid:
            continue
        mean = float(statistics.mean(valid))
        print(f'{name} (count={len(valid)}): mean={mean:.3}', end='')
        if len(valid) > 1:
            stdev = statistics.stdev(valid)
            print(f', st.dev.={stdev:.3}', end='')
        print()
    print()


def print_result_frequencies(matches):
    """Print a frequency for each result."""

    results = (football.result(match.score) for match in matches)
    result_counts = collections.Counter(results)
    for result in '1', 'X', '2':
        frequency = result_counts[result] / len(matches)
        print(f'{result} {frequency:6.2%}')


def print_score_frequencies(matches, level=2):
    """Print a frequency for each score."""

    counts = collections.Counter(match.score for match in matches)

    def key(item):
        """Score sorting key."""
        score, count = item
        return -count, score

    print_title('Score frequencies', level)
    score_counts = iter(sorted(counts.items(), key=key))

    running_sum = 0
    for score, count in score_counts:
        home, away = score
        frequency = count / len(matches)
        print(f'{home}:{away} {frequency:7.3%}')
        running_sum += count
        if 1 - running_sum / len(matches) < 0.0005:
            break

    rest = sum(count for _, count in score_counts)
    if rest > 0:
        frequency = rest / len(matches)
        print(f'rest {frequency:6.3%}')
    print()

    print_title('Category frequencies', level)
    category_counts = collections.Counter()
    for score, count in counts.items():
        category_counts[prediction.category_from_score(score)] += count
    for category, count in sorted(category_counts.items(), key=key):
        home, away = category
        frequency = count / len(matches)
        sep = ':' if home + away < prediction.MAX_GOALS - 1 else '~'
        print(f'{home}{sep}{away} {frequency:6.2%}')
    print()


def print_title(title, level=1):
    """Print a title."""
    if title.upper() in UPPERCASE_REGIONS:
        title = title.upper()
    marker = '#' * level
    print(marker, title, marker)


def main():
    """Show all statistics."""

    matches_by_competition = collections.defaultdict(dict)
    all_matches = []
    for region in data.regions():
        for competition in data.competitions(region):
            matches = list(data.competition_matches(region, competition))
            matches_by_competition[region][competition] = matches
            all_matches.extend(matches)

    print_stats('Overall', all_matches)
    print_score_frequencies(all_matches)
    for region, match_dict in matches_by_competition.items():
        print_region_stats(region, match_dict)


if __name__ == '__main__':
    main()
