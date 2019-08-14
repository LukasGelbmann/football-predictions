"""Resources to play in the stock market."""


import collections
import random
import sys

import data
import football
from games import prediction_zone
import predictors
import simulate


NUM_SIMULATIONS = 400

ORDER_SIZE = 999
CASH_TARGET = 150000

VALUES = {
    football.Competition('england', 'premier'):
        [1000, 800, 650, 550, 450, 400, 360, 330, 300, 280, 260, 240, 220, 210,
         200, 190, 180, 120, 110, 100],
    football.Competition('germany', 'bundesliga'):
        [1000, 800, 650, 550, 450, 400, 360, 320, 290, 260, 240, 220, 200, 190,
         180, 140, 110, 100],
}


def buy_sets(competition, season):
    """Buy sets, if needed."""

    cash = prediction_zone.get_cash(competition, season)
    extra_cash = cash - CASH_TARGET

    if extra_cash < 0:
        print(f"Cash level is {-extra_cash} below target.")
        return

    if extra_cash == 0:
        print("Cash level is exactly at target.")
        return

    print(f"Cash level is {extra_cash} above target.")
    set_price = prediction_zone.get_set_price(competition, season)
    num_sets = extra_cash // set_price
    print(f"Need {num_sets} sets.")
    if num_sets > 0:
        bought = prediction_zone.buy_sets(num_sets, competition, season)
        print(f"Bought {bought} sets.")


def get_team_values(matches, fixtures, played, competition, get_predictor):
    """Return the average values per team."""
    random.seed(0)
    totals = collections.defaultdict(int)
    for i in range(NUM_SIMULATIONS):
        print(f"# Simulation {i} #", file=sys.stderr)
        table = simulate.table(matches, fixtures, played, competition,
                               get_predictor())
        values = dict(zip(table, VALUES[competition]))
        for team, value in values.items():
            totals[team] += value
    return {team: total / NUM_SIMULATIONS for team, total in totals.items()}


def update_orders(competition, season, team_values):
    """Update orders on Prediction Zone."""
    min_value = min(VALUES[competition])
    max_value = max(VALUES[competition])
    for team, value in team_values.items():
        margin = ((value - min_value) * (max_value - value)) ** 0.8 / 210
        low = round(value - margin)
        high = round(value + margin)
        prediction_zone.buy(competition, season, team, low, ORDER_SIZE)
        prediction_zone.sell(competition, season, team, high, ORDER_SIZE)


def print_team_values(team_values):
    """Print the recommended overall prediction."""
    def key(team):
        return -team_values[team], team
    teams = sorted(team_values, key=key)
    for team in teams:
        print(f"{team_values[team]:4.0f} {team}")


def play():
    """Buy sets and update orders."""

    season = football.current_season()
    competitions = [football.Competition('england', 'premier'),
                    football.Competition('germany', 'bundesliga')]
    matches = data.matches()
    get_predictor = predictors.strengths.Predictor

    for competition in competitions:
        buy_sets(competition, season)
        fixtures = list(data.season_fixtures(competition, season))
        played = [match for match in matches
                  if (match.competition == competition
                      and match.season == season)]
        team_values = get_team_values(matches, fixtures, played, competition,
                                      get_predictor)
        print_team_values(team_values)
        update_orders(competition, season, team_values)


def main():
    """Play in the stock market game."""
    play()


if __name__ == '__main__':
    main()
