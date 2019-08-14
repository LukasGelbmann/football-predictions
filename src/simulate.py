"""Resources for simulating sequences of matches."""


import collections
import itertools
import operator
import random

import football
import prediction


def table(matches, fixtures, played, competition, predictor):
    """Return the league table after a simulated season."""
    simulated = simulate_season(matches, fixtures, competition, predictor)
    matches = [*played, *simulated]
    return table_from_matches(matches, competition)


def simulate_season(matches, fixtures, competition, predictor):
    """Return the matches after a simulated season."""

    for match in matches:
        predictor.feed_match(match)

    category_to_score = get_category_to_score(matches)

    simulated = []
    groups = itertools.groupby(fixtures, key=operator.attrgetter('date'))
    for _, todays_fixtures in groups:
        todays_matches = []
        for fixture in todays_fixtures:
            probabilities = predictor.predict(fixture)
            score = sample_score(probabilities, category_to_score)
            match = football.Match(fixture.competition, fixture.date,
                                   fixture.season, fixture.home, fixture.away,
                                   *score)
            simulated.append(match)
            todays_matches.append(match)
        for match in todays_matches:
            predictor.feed_match(match)

    return simulated


def get_category_to_score(matches):
    """Return a mapping from categories to score-probability mappings."""

    counters = collections.defaultdict(collections.Counter)
    for match in matches:
        score = match.score
        category = prediction.category_from_score(score)
        counters[category][score] += 1

    category_to_score = {}
    for category, counter in counters.items():
        total = sum(counter.values())
        category_to_score[category] = {score: count / total
                                       for score, count in counter.items()}

    return category_to_score


def sample_score(probabilities, category_to_score):
    """Return a randomly sampled score."""
    category = random.choices(list(probabilities), probabilities.values())[0]
    scores = category_to_score[category]
    return random.choices(list(scores), scores.values())[0]


def table_from_matches(matches, competition):
    """Return a league table."""

    if len(matches) != football.num_matches(competition):
        raise ValueError("unexpected number of matches")

    points = collections.Counter()
    scored = collections.Counter()
    conceded = collections.Counter()
    for match in matches:
        result = football.result(match.score)
        if result == '1':
            points[match.home] += 3
        elif result == '2':
            points[match.away] += 3
        else:
            points[match.home] += 1
            points[match.away] += 1
        scored[match.home] += match.home_goals
        scored[match.away] += match.away_goals
        conceded[match.home] += match.away_goals
        conceded[match.away] += match.home_goals

    tiebreakers = list(range(len(scored)))
    random.shuffle(tiebreakers)

    keys = {}
    for team, tiebreaker in zip(scored, tiebreakers):
        goal_diff = scored[team] - conceded[team]
        keys[team] = points[team], goal_diff, scored[team], tiebreaker

    if len(keys) != football.league_size(competition):
        raise ValueError("unexpected number of teams")

    return sorted(keys, key=keys.get, reverse=True)
