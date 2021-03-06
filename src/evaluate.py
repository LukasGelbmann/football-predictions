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
import predictors
import probtools


DEFAULT_P = 0.005

# Date rolls over at this UTC time.
UTC_DATE_CUTOFF = datetime.time(5)

# Maximum match duration.
MAX_DURATION = datetime.timedelta(hours=3)

ONE_DAY = datetime.timedelta(1)


def print_evaluation(predictor, all_matches, prediction_start):
    """Evaluate a predictor.

    `all_matches` must be sorted ascending by date."""

    print(f'# Predictor {predictor.name!r} #')
    print()

    all_scores = []
    total_probabilities = collections.defaultdict(float)
    total_result_probabilities = collections.defaultdict(float)
    category_counts = collections.Counter()
    result_counts = collections.Counter()

    # 3 days: yesterday, today, tomorrow.  By latest end date / earliest start.
    matches_by_end_date = collections.deque([[], [], []], maxlen=3)
    fixtures_by_start_date = collections.deque([[], [], []], maxlen=3)

    correct_categories = 0
    correct_results = 0

    def get_scores():
        """Pop some fixtures, let the predictor predict, then evaluate it."""
        nonlocal correct_categories
        nonlocal correct_results
        fixtures_list = fixtures_by_start_date.popleft()
        for fixture, correct_category in fixtures_list:
            probabilities = predictor.predict(fixture)
            if not probtools.is_distribution(probabilities.values()):
                raise ValueError("invalid probability distribution")
            probability = probabilities[correct_category]
            score = math.log(probability) if probability > 0 else -math.inf
            all_scores.append(score)
            category_counts[correct_category] += 1
            result_counts[football.result(correct_category)] += 1
            result_probabilities = collections.defaultdict(float)
            for category, probability in probabilities.items():
                total_probabilities[category] += probability
                result_probabilities[football.result(category)] += probability
            for result, probability in result_probabilities.items():
                total_result_probabilities[result] += probability
            category_guess = max(probabilities, key=probabilities.get)
            if category_guess == correct_category:
                correct_categories += 1
            result_guess = max(result_probabilities, key=result_probabilities.get)
            if result_guess == football.result(correct_category):
                correct_results += 1

    previous_today = None
    for match in all_matches:
        today = match.date
        if previous_today is None:
            previous_today = today

        while previous_today < today:
            get_scores()
            fixtures_by_start_date.append([])

            for stored_match in matches_by_end_date.popleft():
                predictor.feed_match(stored_match)
            matches_by_end_date.append([])

            previous_today += ONE_DAY

        earliest_start, latest_end = earliest_latest(match)
        start_diff = (earliest_start - today).days
        if not -1 <= start_diff <= 1:
            print(
                f"Weird start date: expected {today} +/- 1 day, got {earliest_start}.",
                file=sys.stderr,
            )
            exit()
            continue
        end_diff = (latest_end - today).days
        if not -1 <= end_diff <= 1:
            print(
                f"Weird end date: expected {today} +/- 1 day, got {latest_end}.",
                file=sys.stderr,
            )
            continue

        if earliest_start >= prediction_start:
            fixture = football.Fixture.from_match(match)
            element = fixture, prediction.category(match)
            fixtures_by_start_date[start_diff + 1].append(element)
        matches_by_end_date[end_diff + 1].append(match)

    while fixtures_by_start_date or matches_by_end_date:
        get_scores()
        for match in matches_by_end_date.popleft():
            predictor.feed_match(match)

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

    print(
        f"## Mean prediction and deviations from true percentage (p<{DEFAULT_P:.1%}) ##"
    )

    for result in '1', 'X', '2':
        average_prob = total_result_probabilities[result] / num_predictions
        count = result_counts[result]
        bias_str = get_bias_str(average_prob, count, num_predictions)
        if bias_str:
            suffix = f' ({bias_str})'
        else:
            suffix = ''
        print(f'{result} {average_prob:6.2%}{suffix}')

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


def earliest_latest(match):
    """Return the earliest start date and latest end date in UTC."""

    region = match.competition.region

    utc_time = match.utc_time
    if utc_time is not None:
        earliest_utc_start = utc_time
        latest_utc_end = utc_time + MAX_DURATION
    else:
        date = match.date
        tzinfo = datetools.TIMEZONES[region]

        local_time_early = datetime.datetime.combine(
            date, football.EARLIEST_START, tzinfo
        )
        earliest_start = local_time_early - datetools.MAX_TIME_DIFF[region]
        earliest_utc_start = datetools.to_utc(earliest_start)

        local_time_late = datetime.datetime.combine(date, football.LATEST_START, tzinfo)
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
    if probtools.binomial_cdf(count, num_predictions, average_prob) < p / 2:
        return f"overestimate: reality={true_mean:.2%}"
    if 1 - probtools.binomial_cdf(count - 1, num_predictions, average_prob) < p / 2:
        return f"underestimate: reality={true_mean:.2%}"
    return ''


def main():
    """Evaluate all predictors."""
    matches = data.matches()
    for predictor in predictors.get_all():
        print_evaluation(predictor, matches, datetime.date(2016, 7, 20))


if __name__ == '__main__':
    main()
