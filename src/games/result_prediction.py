"""Resources to play in the result prediction game."""


import sys

import data
import football
import predictors
import probtools
import simulate
from games import prediction_zone


def make_predictions(matches, fixtures, predictor):
    """Make some predictions and upload them."""

    for match in matches:
        predictor.feed_match(match)

    category_to_score = simulate.get_category_to_score(matches)

    for fixture in fixtures:
        probabilities = predictor.predict(fixture)
        score_probabilities = get_score_probabilities(probabilities, category_to_score)
        home, away = predicted_score = predict_score(score_probabilities)
        print(
            f"Prediction: {fixture.date}, {fixture.home} {home} - "
            f"{away} {fixture.away}",
            file=sys.stderr,
        )
        prediction_zone.predict_score(fixture, predicted_score)


def get_score_probabilities(probabilities, category_to_score):
    """Return a probability for each score."""
    score_probabilities = {}
    for category, probability in probabilities.items():
        scores = category_to_score[category]
        for score, score_probability in scores.items():
            score_probabilities[score] = probability * score_probability
    if not probtools.is_distribution(score_probabilities.values()):
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


def play():
    """Make the next predictions."""

    pairs = [
        (football.Competition('england', 'premier'), 10),
        (football.Competition('germany', 'bundesliga'), 9),
    ]
    matches = data.matches()

    for competition, num_predictions in pairs:
        fixtures = list(data.competition_fixtures(competition))
        next_fixtures = fixtures[:num_predictions]
        predictor = predictors.strengths.Predictor()
        make_predictions(matches, next_fixtures, predictor)


def main():
    """Play in the result prediction game."""
    play()


if __name__ == '__main__':
    main()
