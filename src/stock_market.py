#!/usr/bin/env python3

"""Script to participate in the stock market prediction game.

This script requires Python 3.6 or higher."""


import collections
import itertools
import operator
import random

import data
import football
import prediction_zone
import prediction


NUM_SIMULATIONS = 200

VALUES_PREMIER = [1000, 800, 650, 550, 450, 400, 360, 330, 300, 280, 260, 240,
                  220, 210, 200, 190, 180, 120, 110, 100]

ORDER_SIZE = 999
CASH_TARGET = 150000


def buy_sets(region, competition, season):
    """Buy sets, if needed."""
    set_price = prediction_zone.get_set_price(region, competition, season)
    cash = prediction_zone.get_cash(region, competition, season)
    num_sets = (cash - CASH_TARGET) // set_price
    if num_sets > 0:
        prediction_zone.buy_sets(region, competition, season, num_sets)


def get_team_values(records, encounters, region,
                    get_predictor=prediction.strength_model.Predictor):
    """Return the average values per team."""
    random.seed(0)
    totals = collections.Counter()
    for i in range(NUM_SIMULATIONS):
        print(f"# Simulation {i} #")
        values = simulate_season(records, encounters, get_predictor(), region)
        for team, value in values.items():
            totals[team] += value
    return {team: total / NUM_SIMULATIONS for team, total in totals.items()}


def simulate_season(records, encounters, predictor, region):
    """Return the value of the teams after a simpulated season."""

    for record in records:
        predictor.feed_record(record)

    category_to_score = get_category_to_score(records)

    matches = []
    groups = itertools.groupby(encounters, key=operator.attrgetter('date'))
    for date, todays_encounters in groups:
        todays_records = []
        for encounter in todays_encounters:
            probabilities = predictor.predict(encounter)
            score = sample_score(probabilities, category_to_score)
            match = football.Match(encounter.date, encounter.home,
                                   encounter.away, *score)
            record = football.MatchRecord(match, encounter.region,
                                          encounter.competition,
                                          encounter.season)
            matches.append(match)
            todays_records.append(record)
        for record in todays_records:
            predictor.feed_record(record)

    return team_values_from_matches(matches, region)


def get_category_to_score(records):
    """Return a mapping from categories to score-probability mappings."""

    counters = collections.defaultdict(collections.Counter)
    for record in records:
        score = record.match.score
        category = prediction.category_from_score(score)
        counters[category][score] += 1

    category_to_score = {}
    for category, counter in counters.items():
        total = sum(counter.values())
        category_to_score[category] = {score: count / total
                                       for score, count in counter.items()}

    return category_to_score


def sample_score(probabilities, category_to_score):
    """Return a randomly sampled score."""
    category = random.choices(list(probabilities), probabilities.values())[0]
    scores = category_to_score[category]
    return random.choices(list(scores), scores.values())[0]


def team_values_from_matches(matches, region):
    """Return teams' values at the end of the season."""

    if region != 'england':
        raise NotImplementedError("league tables for non-england competitions "
                                  "aren't implemented")

    points = collections.Counter()
    scored = collections.Counter()
    conceded = collections.Counter()
    for match in matches:
        result = football.result(match.score)
        if result == '1':
            points[match.home] += 3
        elif result == '2':
            points[match.away] += 3
        else:
            points[match.home] += 1
            points[match.away] += 1
        scored[match.home] += match.home_goals
        scored[match.away] += match.away_goals
        conceded[match.home] += match.away_goals
        conceded[match.away] += match.home_goals

    tiebreakers = list(range(len(scored)))
    random.shuffle(tiebreakers)

    keys = {}
    for team, tiebreaker in zip(scored, tiebreakers):
        goal_diff = scored[team] - conceded[team]
        keys[team] = points[team], goal_diff, scored[team], tiebreaker

    if len(keys) != len(VALUES_PREMIER):
        raise ValueError("unexpected number of teams")

    teams = sorted(keys, key=keys.get, reverse=True)
    values = {}
    for team, value in zip(teams, VALUES_PREMIER):
        values[team] = value

    return values


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
