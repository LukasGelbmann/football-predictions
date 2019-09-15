"""A strength-based predictor."""


import collections
import datetime
import math
import sys

import datetools
import football
import prediction
from predictors import base


HOME_ADVANTAGE = 0.43

ITERATIONS = range(100)
ITERATIONS_UPDATE = range(5)

KEEP_MATCHES = datetime.timedelta(days=round(10 * datetools.DAYS_PER_YEAR))


class Predictor(base.Predictor):
    """A prediction strategy based on modeling teams' strengths."""

    def __init__(self, name='strength model', *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.memory = collections.defaultdict(collections.deque)
        self.category_counts = collections.defaultdict(collections.Counter)
        self.valid_caches = set()
        self.strengths_caches = {}

    def feed_match(self, match):
        region = match.competition.region
        self.memory[region].append(match)
        self.valid_caches.discard(region)
        category = prediction.category(match)
        self.category_counts[match.competition][category] += 1

    def predict(self, fixture):
        region = fixture.competition.region
        self.update_cache(region, fixture.date)
        strengths = self.strengths_caches[region]
        strength_diff_naive = strengths[fixture.home] - strengths[fixture.away]
        strength_diff = strength_diff_naive + HOME_ADVANTAGE
        result_probabilities = {}
        draw = 0.29 * math.exp(-0.5 * (strength_diff * 0.65) ** 2)
        home = (1 - draw) / (1 + math.exp(-strength_diff))
        result_probabilities = {'1': home, 'X': draw, '2': 1 - home - draw}
        probabilities = {}
        counts = self.category_counts[fixture.competition]
        adjusted_counts = {
            category: max(counts[category], 1) for category in prediction.categories()
        }
        result_counts = collections.Counter()
        for category, count in adjusted_counts.items():
            result_counts[football.result(category)] += count
        for category in prediction.categories():
            result = football.result(category)
            factor = adjusted_counts[category] / result_counts[result]
            probabilities[category] = result_probabilities[result] * factor
        return probabilities

    def update_cache(self, region, target):
        """Update the strengths cache for a region."""

        if region in self.valid_caches:
            return

        region_memory = self.memory[region]
        while region_memory and target - region_memory[0].date > KEEP_MATCHES:
            match = region_memory.popleft()
            category = prediction.category(match)
            self.category_counts[match.competition][category] -= 1

        if region in self.strengths_caches:
            strengths = self.strengths_caches[region]
            iterations = ITERATIONS_UPDATE
        else:
            strengths = collections.defaultdict(float)
            iterations = ITERATIONS

        # print(target, region, file=sys.stderr)

        for _ in iterations:
            new_strengths = strengths.copy()
            for match in region_memory:
                if target < match.date:
                    print(
                        f"Target date {target} before match date " f"{match.date}.",
                        file=sys.stderr,
                    )
                goal_diff = match.home_goals - match.away_goals
                strength_diff = strengths[match.home] - strengths[match.away]
                change = strength_change(goal_diff, strength_diff)
                adjustment = devaluation(target - match.date) * change
                new_strengths[match.home] += adjustment
                new_strengths[match.away] -= adjustment
            strengths = new_strengths

        self.strengths_caches[region] = strengths
        self.valid_caches.add(region)


def strength_change(goal_diff, strength_diff):
    """Return how much stronger the home team was than expected."""
    return 0.05 * goal_diff - 0.046 * (strength_diff + HOME_ADVANTAGE)


def devaluation(timedelta):
    """Return the relative weight given to a match."""
    return 0.88 ** timedelta.days ** 0.45
