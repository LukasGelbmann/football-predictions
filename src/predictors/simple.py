"""A simple predictor."""


import collections
import datetime

import datetools
from predictors import base
import prediction


KEEP_MATCHES = datetime.timedelta(days=round(10*datetools.DAYS_PER_YEAR))


class Predictor(base.Predictor):
    """A simple prediction strategy."""

    def __init__(self, name='simple', *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.category_counts = collections.defaultdict(collections.Counter)
        self.memory = collections.deque()

    def feed_match(self, match):
        category = prediction.category(match)
        self.category_counts[match.competition][category] += 1
        self.memory.append(match)

    def predict(self, fixture):
        date = fixture.date
        while self.memory and date - self.memory[0].date > KEEP_MATCHES:
            match = self.memory.popleft()
            category = prediction.category(match)
            self.category_counts[match.competition][category] -= 1

        counts = self.category_counts[fixture.competition]
        adjusted_counts = {category: max(counts[category], 1)
                           for category in prediction.categories()}
        total = sum(adjusted_counts.values())
        return {category: count / total
                for category, count in adjusted_counts.items()}
