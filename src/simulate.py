"""Resources for simulating sequences of matches."""


import collections
import itertools
import operator
import random

import football
import prediction


VALUES_PREMIER = [1000, 800, 650, 550, 450, 400, 360, 330, 300, 280, 260, 240,
                  220, 210, 200, 190, 180, 120, 110, 100]


def simulate_season_table(records, encounters, predictor, region):
    """Return the league table after a simulated season."""
    matches = simulate_season(records, encounters, predictor, region)
    return table_from_matches(matches, region)


def simulate_season_values(records, encounters, predictor, region):
    """Return the value of the teams after a simulated season."""
    matches = simulate_season(records, encounters, predictor, region)
    return team_values_from_matches(matches, region)


def simulate_season(records, encounters, predictor, region):
    """Return the matches after a simulated season."""

    for record in records:
        predictor.feed_record(record)

    category_to_score = get_category_to_score(records)

    matches = []
    groups = itertools.groupby(encounters, key=operator.attrgetter('date'))
    for date, todays_encounters in groups:
        todays_records = []
        for encounter in todays_encounters:
            probabilities = predictor.predict(encounter)
            score = sample_score(probabilities, category_to_score)
            match = football.Match(encounter.date, encounter.home,
                                   encounter.away, *score)
            record = football.MatchRecord(match, encounter.region,
                                          encounter.competition,
                                          encounter.season)
            matches.append(match)
            todays_records.append(record)
        for record in todays_records:
            predictor.feed_record(record)

    return matches


def get_category_to_score(records):
    """Return a mapping from categories to score-probability mappings."""

    counters = collections.defaultdict(collections.Counter)
    for record in records:
        score = record.match.score
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


def team_values_from_matches(matches, region):
    """Return teams' values at the end of the season."""
    teams = table_from_matches(matches, region)
    import pprint;pprint.pprint(teams)
    return dict(zip(teams, VALUES_PREMIER))


def table_from_matches(matches, region):
    """Return a league table."""

    if region != 'england':
        raise NotImplementedError("league tables for non-england competitions "
                                  "aren't implemented")

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

    if len(keys) != len(VALUES_PREMIER):
        raise ValueError("unexpected number of teams")

    return sorted(keys, key=keys.get, reverse=True)
