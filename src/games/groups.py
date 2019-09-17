"""Resources to make an overall prediction."""


import collections
import random
import sys

import data
import football
import predictors
import simulate
from games import prediction_zone


NUM_SIMULATIONS = 1000

CUPS = [football.Competition('europe', 'champions')]


def get_team_chances(matches, fixtures, played, competition, season, get_predictor):
    """Return the counts per position per team."""
    random.seed(0)
    # Group -> team -> position -> count
    counters = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for i in range(NUM_SIMULATIONS):
        print(f"# Simulation {i} #", file=sys.stderr)
        simulated = simulate.simulate_season(
            matches,
            fixtures,
            played,
            competition,
            season,
            get_predictor(),
            restrict=True,
        )
        matches_by_group, _ = simulate.order_cup_matches([*played, *simulated])
        for group, group_matches in sorted(matches_by_group.items()):
            table = simulate.cl_group_table(group_matches, competition)
            print(','.join(table), file=sys.stderr)
            for position, team in enumerate(table, 1):
                counters[group][team][position] += 1
    return counters


def print_group_predictions(team_chances):
    """Print the recommended overall prediction."""

    for group, group_chances in sorted(team_chances.items()):
        counts = set()
        for counter in group_chances.values():
            counts.add(sum(counter.values()))
        if len(counts) > 1:
            print("Fishy counts.", file=sys.stderr)

        teams = list(group_chances)
        random.seed(0)
        random.shuffle(teams)

        ranking = []
        cumulative = collections.Counter()
        for position in range(1, len(group_chances) + 1):
            for team, counter in group_chances.items():
                cumulative[team] += counter[position]
            next_team = max(teams, key=cumulative.get)
            ranking.append(next_team)
            teams.remove(next_team)

        print(f"# Group {group} #")
        simulate.print_ranking(ranking[:2])
        print()


def play():
    """Make an group predictions and print them."""

    season = football.current_season()
    matches = data.matches()
    get_predictor = predictors.strengths.Predictor

    for competition in CUPS:
        fixtures = list(data.season_fixtures(competition, season))
        played = [
            match
            for match in matches
            if match.competition == competition and match.season == season
        ]
        team_chances = get_team_chances(
            matches, fixtures, played, competition, season, get_predictor
        )
        print_group_predictions(team_chances)


def main():
    """Make an overall prediction."""
    play()


if __name__ == '__main__':
    main()
