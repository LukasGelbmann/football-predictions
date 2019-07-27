import collections
import datetime

import prediction.common


DAYS_PER_YEAR = 365.2425
KEEP_MATCHES = datetime.timedelta(days=round(10*DAYS_PER_YEAR))


class Predictor(prediction.common.Predictor):
    """A simple prediction strategy."""

    def __init__(self, name='simple', *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.category_counts = collections.defaultdict(collections.Counter)
        self.memory = collections.deque()

    def feed_records(self, records):
        for record in records:
            category = prediction.common.category(record)
            key = record.region, record.competition
            self.category_counts[key][category] += 1
            self.memory.append(record)

    def predict(self, encounter):
        date = encounter.date
        while self.memory and date - self.memory[0].date > KEEP_MATCHES:
            record = self.memory.popleft()
            category = prediction.common.category(record)
            key = record.region, record.competition
            self.category_counts[key][category] -= 1

        key = encounter.region, encounter.competition
        counts = self.category_counts[key]
        adjusted_counts = {category: max(counts[category], 1)
                           for category in prediction.common.categories()}
        total = sum(adjusted_counts.values())
        return {category: count / total
                for category, count in adjusted_counts.items()}
