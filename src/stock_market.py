#!/usr/bin/env python3

"""Script to participate in the stock market prediction game.

This script requires Python 3.6 or higher."""


import collections
import random

import data
import football
import prediction_zone
import prediction
import simulate


NUM_SIMULATIONS = 200

ORDER_SIZE = 999
CASH_TARGET = 150000


def buy_sets(region, competition, season):
    """Buy sets, if needed."""
    set_price = prediction_zone.get_set_price(region, competition, season)
    cash = prediction_zone.get_cash(region, competition, season)
    num_sets = (cash - CASH_TARGET) // set_price
    print(f"Need {num_sets} sets.")
    if num_sets > 0:
        prediction_zone.buy_sets(region, competition, season, num_sets)


def get_team_values(records, encounters, region,
                    get_predictor=prediction.strength_model.Predictor):
    """Return the average values per team."""
    random.seed(0)
    totals = collections.Counter()
    for i in range(NUM_SIMULATIONS):
        print(f"# Simulation {i} #")
        values = simulate.simulate_season_values(records, encounters,
                                                 get_predictor(), region)
        for team, value in values.items():
            totals[team] += value
    return {team: total / NUM_SIMULATIONS for team, total in totals.items()}


def update_orders(region, competition, season, team_values):
    """Update orders on Prediction Zone."""

    if region != 'england':
        raise NotImplementedError("stock market orders for non-england "
                                  "competitions aren't implemented")

    min_value = min(VALUES_PREMIER)
    max_value = max(VALUES_PREMIER)
    for team, value in team_values.items():
        margin = ((value - min_value) * (max_value - value)) ** 0.8 / 210
        low = round(value - margin)
        high = round(value + margin)
        prediction_zone.place_order(region, competition, season, team, 'buy',
                                    low, ORDER_SIZE)
        prediction_zone.place_order(region, competition, season, team, 'sell',
                                    high, ORDER_SIZE)


def main():
    """Buy sets and update orders."""

    region = 'england'
    competition = 'premier'
    season = '2019-20'

    # prediction_zone.download_calendar(region, competition, season)

    buy_sets(region, competition, season)

    records = data.all_records()
    encounters = list(data.season_encounters(region, competition, season))
    team_values = get_team_values(records, encounters, region)

    update_orders(region, competition, season, team_values)


if __name__ == '__main__':
    main()
