"""A strength-based predictor."""


import collections
import functools
import math
import sys

import football
import prediction.common


HOME_ADVANTAGE = 0.4

ITERATIONS = range(100)
ITERATIONS_UPDATE = range(5)


class Predictor(prediction.common.Predictor):
    """A prediction strategy based on modeling teams' strengths."""

    def __init__(self, name='strength model', *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.stored_matches = collections.defaultdict(list)
        self.valid_caches = set()
        self.strengths_caches = {}

    def feed_record(self, record):
        self.stored_matches[record.region].append(record.match)
        self.valid_caches.discard(record.region)

    def predict(self, encounter):
        self.update_cache(encounter.region, encounter.date)
        strengths = self.strengths_caches[encounter.region]
        strength_diff_naive = (strengths[encounter.home]
                               - strengths[encounter.away])
        strength_diff = strength_diff_naive + HOME_ADVANTAGE
        result_probabilities = {}
        draw = 0.28 * math.exp(-0.5 * (strength_diff*0.65)**2)
        home = (1-draw) / (1 + math.exp(-strength_diff))
        result_probabilities = {'1': home, 'X': draw, '2': 1 - home - draw}
        return {category: result_probabilities[result] * factor
                for category, result, factor in category_factors()}

    def update_cache(self, region, target_date):
        """Update the strengths cache for a region."""

        if region in self.valid_caches:
            return

        if region in self.strengths_caches:
            strengths = self.strengths_caches[region]
            iterations = ITERATIONS_UPDATE
        else:
            strengths = collections.defaultdict(float)
            iterations = ITERATIONS

        for _ in iterations:
            new_strengths = strengths.copy()
            for match in self.stored_matches[region]:
                if target_date < match.date:
                    print(f"Target date {target_date} before match date "
                          f"{match.date}.", file=sys.stderr)
                goal_diff = match.home_goals - match.away_goals
                strength_diff = strengths[match.home] - strengths[match.away]
                change = strength_change(goal_diff, strength_diff)
                adjustment = devaluation(target_date - match.date) * change
                new_strengths[match.home] += adjustment
                new_strengths[match.away] -= adjustment
            strengths = new_strengths

        print(region, target_date)

        self.strengths_caches[region] = strengths
        self.valid_caches.add(region)


def strength_change(goal_diff, strength_diff):
    """Return how much stronger the home team was than expected."""
    return 0.05 * goal_diff - 0.046 * (strength_diff + HOME_ADVANTAGE)


def devaluation(timedelta):
    """Return the relative weight given to a match."""
    return 0.88 ** timedelta.days ** 0.45


@functools.lru_cache()
def category_factors():
    """Return a list of categories and the factors we need to apply."""
    result_counts = collections.Counter(
        football.result(category)
        for category in prediction.common.categories())
    factors = []
    for category in prediction.common.categories():
        result = football.result(category)
        factors.append((category, result, 1 / result_counts[result]))
    return factors
