"""Resources to play in the prediction league."""


import collections
import random
import sys

import data
import football
from games import prediction_zone
import predictors
import probtools


def make_predictions(matches, fixtures, competition, predictor):
    """Make some predictions and upload them."""

    if not fixtures:
        return

    for match in matches:
        predictor.feed_match(match)

    season = fixtures[0].season
    league_size = prediction_zone.get_league_size(competition, season)

    for fixture in fixtures:
        probabilities = predictor.predict(fixture)
        result_probabilities = get_result_probabilities(probabilities)
        predicted_result = get_prediction(result_probabilities, fixture,
                                          league_size)
        print(f"Prediction: {fixture.date}, {fixture.home} - {fixture.away}, "
              f"{predicted_result}", file=sys.stderr)
        prediction_zone.predict_result(fixture, predicted_result)


def get_result_probabilities(probabilities):
    """Return a probability for each result."""
    result_probabilities = collections.defaultdict(float)
    for category, probability in probabilities.items():
        result_probabilities[football.result(category)] += probability
    if not probtools.is_distribution(result_probabilities.values()):
        print("Fishy probabilities.", file=sys.stderr)
    return result_probabilities


def get_prediction(result_probabilities, fixture, league_size):
    """Return a good random prediction."""

    if league_size <= 2:
        return max(sorted(result_probabilities), key=result_probabilities.get)

    probabilities = sorted(result_probabilities.items())
    random.seed(str(fixture))
    return random.choices(*zip(*probabilities))[0]


def play():
    """Make the next predictions."""

    pairs = [(football.Competition('england', 'premier'), 10),
             (football.Competition('germany', 'bundesliga'), 9)]
    matches = data.matches()

    for competition, num_predictions in pairs:
        fixtures = list(data.competition_fixtures(competition))
        next_fixtures = fixtures[:num_predictions]
        predictor = predictors.strengths.Predictor()
        make_predictions(matches, next_fixtures, competition, predictor)


def main():
    """Play in the prediction league game."""
    play()


if __name__ == '__main__':
    main()
