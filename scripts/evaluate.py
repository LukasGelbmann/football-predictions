#!/usr/bin/env python3

"""Script to evaluate football prediction strategies based on historical data.

This script requires Python 3.6 or higher."""


import collections
import datetime
import itertools
import math
import operator
import statistics

import data
import prediction


DEFAULT_P = 0.005


def print_evaluation(predictor, all_records, prediction_start):
    """Evaluate a predictor."""

    print(f'# Predictor {predictor.name!r} #')
    print()

    all_scores = []
    total_probabilities = collections.defaultdict(float)
    category_counts = collections.Counter()
    key = operator.attrgetter('date')
    for date, records in itertools.groupby(all_records, key=key):
        records_list = list(records)
        if date >= prediction_start:
            for record in records_list:
                encounter = prediction.encounter(record)
                probabilities = predictor.predict(encounter)
                category = prediction.category(record)
                score = math.log(probabilities[category])
                all_scores.append(score)
                category_counts[category] += 1
                for category, probability in probabilities.items():
                    total_probabilities[category] += probability
        predictor.feed_records(records_list)

    factor = math.log(prediction.num_categories())
    points = statistics.mean(all_scores) / factor + 1
    print(f'Mean points: {points:.3f}')
    print()

    num_predictions = len(all_scores)

    print("Mean prediction and deviations from true percentage "
          f"(p<{DEFAULT_P:.1%}):")
    for category in prediction.categories():
        average_prob = total_probabilities[category] / num_predictions
        count = category_counts[category]
        bias_str = get_bias_str(average_prob, count, num_predictions)
        prediction_str = prediction.category_to_str(category)
        if bias_str:
            suffix = f' ({bias_str})'
        else:
            suffix = ''
        print(f'{prediction_str} {average_prob:6.2%}{suffix}')
    print()


def get_bias_str(average_prob, count, num_predictions, p=DEFAULT_P):
    """Return a string describing the bias, after doing a hypothesis test."""
    true_mean = count / num_predictions
    if binomial_cdf(count, num_predictions, average_prob) < p / 2:
        return f"overestimate: reality={true_mean:.2%}"
    if 1 - binomial_cdf(count - 1, num_predictions, average_prob) < p / 2:
        return f"underestimate: reality={true_mean:.2%}"
    return ''


def binomial_cdf(x, n, p):
    """Return the cumulative distribution of a binomial distribution."""
    # See https://stackoverflow.com/a/45869209
    result = 0
    b = 0
    for k in range(x+1):
        if k > 0:
            b += math.log(n-k+1) - math.log(k)
        log_pmf_k = b + k * math.log(p) + (n-k) * math.log(1-p)
        result += math.exp(log_pmf_k)
    return result


def main():
    """Evaluate all predictors."""
    all_records = data.all_records()
    for predictor in prediction.get_predictors():
        print_evaluation(predictor, all_records, datetime.date(2016, 7, 20))


if __name__ == '__main__':
    main()
