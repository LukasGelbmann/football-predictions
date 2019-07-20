#!/usr/bin/env python3

"""Script to evaluate football prediction strategies based on historical data.

This script requires Python 3.6 or higher."""


import datetime
import itertools
import math
import operator
import statistics

import data
import prediction


def print_evaluation(predictor, all_records, prediction_start):
    """Evaluate a predictor."""
    print(f'Evaluating {predictor.name}...')
    key = operator.attrgetter('date')
    all_scores = []
    for date, records in itertools.groupby(all_records, key=key):
        records_list = list(records)
        if date >= prediction_start:
            all_scores.extend(cross_entropy_scores(records_list, predictor))
        predictor.feed_records(records_list)
    factor = math.log(prediction.num_categories())
    points = statistics.mean(all_scores) / factor + 1
    print(f'Mean points: {points:.3f}')
    print()


def cross_entropy_scores(records, predictor):
    """Yield the cross-entropy score for each prediction."""
    for record in records:
        encounter = prediction.encounter(record)
        probabilities = predictor.predict(encounter)
        yield math.log(probabilities[prediction.category(record)])


def main():
    """Evaluate all predictors."""
    all_records = data.all_records()
    for predictor in prediction.get_predictors():
        print_evaluation(predictor, all_records, datetime.date(2016, 7, 20))


if __name__ == '__main__':
    main()
