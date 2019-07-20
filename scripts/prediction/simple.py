import collections

import prediction.common


class Predictor(prediction.common.Predictor):
    """A simple prediction strategy."""

    def __init__(self, name='simple', *args, **kwargs):
        self.category_counts = collections.Counter()
        super().__init__(name, *args, **kwargs)

    def feed_records(self, records):
        for record in records:
            self.category_counts[prediction.common.category(record)] += 1

    def predict(self, encounter):
        total = sum(self.category_counts.values())
        return {category: count / total
                for category, count in self.category_counts.items()}
