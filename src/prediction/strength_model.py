"""A strength-based predictor."""


import collections
import datetime
import math
import sys

import football
import prediction.common


HOME_ADVANTAGE = 0.42

ITERATIONS = range(100)
ITERATIONS_UPDATE = range(5)

KEEP_MATCHES = datetime.timedelta(
    days=round(10*prediction.common.DAYS_PER_YEAR))


class Predictor(prediction.common.Predictor):
    """A prediction strategy based on modeling teams' strengths."""

    def __init__(self, name='strength model', *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.memory = collections.defaultdict(collections.deque)
        self.category_counts = collections.defaultdict(collections.Counter)
        self.valid_caches = set()
        self.strengths_caches = {}

    def feed_record(self, record):
        self.memory[record.region].append(record)
        self.valid_caches.discard(record.region)
        key = record.region, record.competition
        category = prediction.common.category(record)
        result = football.result(category)
        self.category_counts[key][category] += 1

    def predict(self, encounter):
        self.update_cache(encounter.region, encounter.date)
        strengths = self.strengths_caches[encounter.region]
        strength_diff_naive = (strengths[encounter.home]
                               - strengths[encounter.away])
        strength_diff = strength_diff_naive + HOME_ADVANTAGE
        result_probabilities = {}
        draw = 0.29 * math.exp(-0.5 * (strength_diff*0.65)**2)
        home = (1-draw) / (1 + math.exp(-strength_diff))
        result_probabilities = {'1': home, 'X': draw, '2': 1 - home - draw}
        key = encounter.region, encounter.competition
        probabilities = {}
        counts = self.category_counts[key]
        adjusted_counts = {category: max(counts[category], 1)
                           for category in prediction.common.categories()}
        result_counts = collections.Counter()
        for category, count in adjusted_counts.items():
            result_counts[football.result(category)] += count
        for category in prediction.common.categories():
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
            record = region_memory.popleft()
            category = prediction.common.category(record)
            key = record.region, record.competition
            self.category_counts[key][category] -= 1

        if region in self.strengths_caches:
            strengths = self.strengths_caches[region]
            iterations = ITERATIONS_UPDATE
        else:
            strengths = collections.defaultdict(float)
            iterations = ITERATIONS

        print(region, target)

        for _ in iterations:
            new_strengths = strengths.copy()
            for record in region_memory:
                match = record.match
                if target < match.date:
                    print(f"Target date {target} before match date "
                          f"{match.date}.", file=sys.stderr)
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
