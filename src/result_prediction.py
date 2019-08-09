#!/usr/bin/env python3

"""Script to make predictions in the result prediction game.

This script requires Python 3.6 or higher."""


import sys

import data
import football
import evaluate
import prediction_zone
import prediction
import simulate


NUM_PREDICTIONS = 10


def make_predictions(records, encounters,
                     get_predictor=prediction.strength_model.Predictor):
    """Make some predictions and upload them."""

    predictor = get_predictor()
    for record in records:
        predictor.feed_record(record)

    category_to_score = simulate.get_category_to_score(records)

    for encounter in encounters:
        probabilities = predictor.predict(encounter)
        score_probabilities = get_score_probabilities(probabilities,
                                                      category_to_score)
        predicted_score = predict_score(score_probabilities)
        prediction_zone.predict_score(encounter, predicted_score)


def get_score_probabilities(probabilities, category_to_score):
    """Return a probability for each score."""
    score_probabilities = {}
    for category, probability in probabilities.items():
        scores = category_to_score[category]
        for score, score_probability in scores.items():
            score_probabilities[score] = probability * score_probability
    if not evaluate.is_probability_distribution(score_probabilities.values()):
        print("Fishy probabilities.", file=sys.stderr)
    return score_probabilities


def predict_score(score_probabilities):
    """Return the best prediction."""

    def expected_points(predicted):
        """Return the expected points for a prediction."""
        total = 0.0
        for score, probability in score_probabilities.items():
            if score == predicted:
                total += 3 * probability
            elif score[1] - score[0] == predicted[1] - predicted[0]:
                total += 2 * probability
            elif football.result(score) == football.result(predicted):
                total += 1 * probability
        return total, sum(predicted), predicted

    return max(score_probabilities, key=expected_points)


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
