"""Resources related to prediction."""


from predictors import simple, strengths


def get_all():
    """Return one of each predictor."""
    return [simple.Predictor(), strengths.Predictor()]
