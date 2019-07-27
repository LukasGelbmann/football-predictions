#!/usr/bin/env python3

"""Script to evaluate football prediction strategies based on historical data.

This script requires Python 3.6 or higher."""


import collections
import datetime
import math
import statistics
import sys

import data
import datetools
import football
import prediction


DEFAULT_P = 0.005

# Date rolls over at this UTC time.
UTC_DATE_CUTOFF = datetime.time(5)

# Maximum match duration.
MAX_DURATION = datetime.timedelta(hours=3)

ONE_DAY = datetime.timedelta(1)


def print_evaluation(predictor, all_records, prediction_start):
    """Evaluate a predictor.

    `all_records` must be sorted ascending by date."""

    print(f'# Predictor {predictor.name!r} #')
    print()

    all_scores = []
    total_probabilities = collections.defaultdict(float)
    category_counts = collections.Counter()

    # 3 days: yesterday, today, tomorrow.  By latest end date / earliest start.
    records_by_end_date = collections.deque([[], [], []], maxlen=3)
    encounters_by_start_date = collections.deque([[], [], []], maxlen=3)

    correct_categories = 0
    correct_results = 0

    def get_scores():
        """Pop some encounters, let the predictor predict, then evaluate it."""
        nonlocal correct_categories
        nonlocal correct_results
        for encounter, correct_category in encounters_by_start_date.popleft():
            probabilities = predictor.predict(encounter)
            if not is_probability_distribution(probabilities.values()):
                raise ValueError("invalid probability distribution")
            probability = probabilities[correct_category]
            score = math.log(probability) if probability > 0 else -math.inf
            all_scores.append(score)
            category_counts[correct_category] += 1
            result_probabilities = collections.defaultdict(float)
            for category, probability in probabilities.items():
                total_probabilities[category] += probability
                result_probabilities[football.result(category)] += probability
            category_guess = max(probabilities, key=probabilities.get)
            if category_guess == correct_category:
                correct_categories += 1
            result_guess = max(result_probabilities,
                               key=result_probabilities.get)
            if result_guess == football.result(correct_category):
                correct_results += 1

    previous_today = None
    for record in all_records:
        today = record.date
        if previous_today is None:
            previous_today = today

        while previous_today < today:
            get_scores()
            encounters_by_start_date.append([])

            predictor.feed_records(records_by_end_date.popleft())
            records_by_end_date.append([])

            previous_today += ONE_DAY

        earliest_start, latest_end = earliest_latest(record)
        start_diff = (earliest_start - today).days
        if not -1 <= start_diff <= 1:
            print(f"Weird start date: expected {today} +/- 1 day, got "
                  f"{earliest_start}.", file=sys.stderr)
            continue
        end_diff = (latest_end - today).days
        if not -1 <= end_diff <= 1:
            print(f"Weird end date: expected {today} +/- 1 day, got "
                  f"{latest_end}.", file=sys.stderr)
            continue

        if earliest_start >= prediction_start:
            element = prediction.encounter(record), prediction.category(record)
            encounters_by_start_date[start_diff + 1].append(element)
        records_by_end_date[end_diff + 1].append(record)

    while encounters_by_start_date or records_by_end_date:
        get_scores()
        predictor.feed_records(records_by_end_date.popleft())

    factor = math.log(prediction.num_categories())
    points = statistics.mean(all_scores) / factor + 1
    print(f"Mean points: {points:.3f}")
    print()

    num_predictions = len(all_scores)

    category_ratio = correct_categories / num_predictions
    result_ratio = correct_results / num_predictions
    print(f"Guessed category: {category_ratio:.2%}")
    print(f"Guessed result (1/X/2): {result_ratio:.2%}")
    print()

    print("## Mean prediction and deviations from true percentage "
          f"(p<{DEFAULT_P:.1%}) ##")
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


def is_probability_distribution(values):
    """Return True if `values` is a valid probability distribution."""
    return math.isclose(sum(values), 1) and all(x >= 0 for x in values)


def earliest_latest(record):
    """Return the earliest start date and latest end date in UTC."""

    utc_time = record.match.utc_time
    if utc_time is not None:
        earliest_utc_start = utc_time
        latest_utc_end = utc_time + MAX_DURATION
    else:
        date = record.date
        region = record.region
        tzinfo = datetools.TIMEZONES[region]

        local_time_early = datetime.datetime.combine(
            date, football.EARLIEST_START, tzinfo)
        earliest_start = local_time_early - datetools.MAX_TIME_DIFF[region]
        earliest_utc_start = datetools.to_utc(earliest_start)

        local_time_late = datetime.datetime.combine(
            date, football.LATEST_START, tzinfo)
        latest_end = local_time_late + MAX_DURATION
        latest_utc_end = datetools.to_utc(latest_end)

    if earliest_utc_start.time() < UTC_DATE_CUTOFF:
        earliest_start = earliest_utc_start.date() - ONE_DAY
    else:
        earliest_start = earliest_utc_start.date()

    if latest_utc_end.time() <= UTC_DATE_CUTOFF:
        latest_end = latest_utc_end.date() - ONE_DAY
    else:
        latest_end = latest_utc_end.date()

    assert earliest_start <= latest_end, "a match can't end before it starts"

    return earliest_start, latest_end



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
