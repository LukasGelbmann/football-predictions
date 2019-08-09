#!/usr/bin/env python3

"""Script to make an overall prediction.

This script requires Python 3.6 or higher."""


import collections
import random

import data
import prediction
import prediction_zone
import simulate


NUM_SIMULATIONS = 250


def get_team_chances(records, encounters, region,
                     get_predictor=prediction.strength_model.Predictor):
    """Return the average values per team."""
    random.seed(0)
    counters = collections.defaultdict(collections.Counter)
    for i in range(NUM_SIMULATIONS):
        print(f"# Simulation {i} #")
        values = simulate.simulate_season_table(records, encounters,
                                                get_predictor(), region)
        for position, team in enumerate(values, 1):
            counters[team][position] += 1
    return counters


def print_overall_prediction(team_chances):
    """Print the recommended overall prediction."""
    teams = list(team_chances)
    random.seed(0)
    random.shuffle(teams)
    cumulative = collections.Counter()
    for position in range(1, len(team_chances) + 1):
        for team, counter in team_chances.items():
            cumulative[team] += counter[position]
        next_team = max(teams, key=cumulative.get)
        print(f"{position:2} {next_team}")
        teams.remove(next_team)


def main():
    """Make an overall prediction and print it."""

    region = 'england'
    competition = 'premier'
    season = '2019-20'

    prediction_zone.download_calendar(region, competition, season)

    records = data.all_records()
    encounters = list(data.season_encounters(region, competition, season))
    team_chances = get_team_chances(records, encounters, region)

    print_overall_prediction(team_chances)


if __name__ == '__main__':
    main()
