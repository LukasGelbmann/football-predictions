#!/usr/bin/env python3

"""Script to make predictions in the result prediction game.

This script requires Python 3.6 or higher."""


import collections
import random
import sys

import data
import football
import evaluate
import prediction_zone
import prediction


NUM_PREDICTIONS = 10


def make_predictions(region, competition, season, records, encounters,
                     get_predictor=prediction.strength_model.Predictor):
    """Make some predictions and upload them."""

    predictor = get_predictor()
    for record in records:
        predictor.feed_record(record)

    league_size = prediction_zone.get_league_size(region, competition, season)

    for encounter in encounters:
        probabilities = predictor.predict(encounter)
        result_probabilities = get_result_probabilities(probabilities)
        predicted_result = get_prediction(result_probabilities, encounter,
                                          league_size)
        prediction_zone.predict_result(encounter, predicted_result)


def get_result_probabilities(probabilities):
    """Return a probability for each result."""
    result_probabilities = collections.defaultdict(float)
    for category, probability in probabilities.items():
        result_probabilities[football.result(category)] += probability
    if not evaluate.is_probability_distribution(result_probabilities.values()):
        print("Fishy probabilities.", file=sys.stderr)
    return result_probabilities


def get_prediction(result_probabilities, encounter, league_size):
    """Return a good random prediction."""

    if league_size <= 2:
        return max(sorted(result_probabilities), key=result_probabilities.get)

    probabilities = sorted(result_probabilities.items())
    random.seed(str(encounter))
    return random.choices(*zip(*probabilities))[0]


def main():
    """Buy sets and update orders."""

    region = 'england'
    competition = 'premier'
    season = '2019-20'

    # prediction_zone.download_calendar(region, competition, season)

    records = data.all_records()
    encounters = list(data.season_encounters(region, competition, season))
    next_encounters = encounters[:NUM_PREDICTIONS]

    make_predictions(region, competition, season, records, next_encounters)


if __name__ == '__main__':
    main()
