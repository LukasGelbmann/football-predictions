from prediction.common import (Encounter, category, category_from_score,
                               categories, num_categories, MAX_GOALS)
import prediction.simple


def get_predictors():
    """Return one of each predictor."""
    return [prediction.simple.Predictor()]


def encounter(record):
    """Return an Encounter, given a record."""
    return Encounter(record.date, record.match.home, record.match.away,
                     record.region, record.competition, record.season)
