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


def get_team_chances(matches, fixtures, played, competition, season, get_predictor):
    """Return the counts per position per team."""
    random.seed(0)
    counters = collections.defaultdict(collections.Counter)
    for i in range(NUM_SIMULATIONS):
        print(f"# Simulation {i} #", file=sys.stderr)
        table = simulate.table(
            matches, fixtures, played, competition, season, get_predictor()
        )
        simulate.print_ranking(table, file=sys.stderr)
        for position, team in enumerate(table, 1):
            counters[team][position] += 1
    return counters


def print_overall_prediction(team_chances):
    """Print the recommended overall prediction."""

    counts = set()
    for counter in team_chances.values():
        counts.add(sum(counter.values()))
    if len(counts) > 1:
        print("Fishy counts.", file=sys.stderr)

    teams = list(team_chances)
    random.seed(0)
    random.shuffle(teams)

    ranking = []
    cumulative = collections.Counter()
    for position in range(1, len(team_chances) + 1):
        for team, counter in team_chances.items():
            cumulative[team] += counter[position]
        next_team = max(teams, key=cumulative.get)
        ranking.append(next_team)
        teams.remove(next_team)

    print("# Overall #")
    simulate.print_ranking(ranking)


def play():
    """Make an overall prediction and print it."""

    season = football.current_season()
    matches = data.matches()
    get_predictor = predictors.strengths.Predictor

    for competition in prediction_zone.COMPETITIONS:
        fixtures = list(data.season_fixtures(competition, season))
        played = [
            match
            for match in matches
            if match.competition == competition and match.season == season
        ]
        team_chances = get_team_chances(
            matches, fixtures, played, competition, season, get_predictor
        )
        print_overall_prediction(team_chances)


def main():
    """Make an overall prediction."""
    play()


if __name__ == '__main__':
    main()
