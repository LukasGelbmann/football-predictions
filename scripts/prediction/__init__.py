from prediction.common import (Encounter, category, category_from_score,
                               categories, num_categories, MAX_GOALS)
import prediction.simple
import prediction.strength_model


def get_predictors():
    """Return one of each predictor."""
    return [prediction.strength_model.Predictor(),
            prediction.simple.Predictor()]


def encounter(record):
    """Return an Encounter, given a record."""
    return Encounter(record.date, record.match.home, record.match.away,
                     record.region, record.competition, record.season)


def category_to_str(category):
    """Return a string representation."""
    home, away = category
    sep = ':' if home + away < MAX_GOALS - 1 else '~'
    return f'{home}{sep}{away}'
