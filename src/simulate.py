"""Resources for simulating sequences of matches."""


import collections
import datetime
import itertools
import operator
import random
import sys

import football
import prediction


# For Champions League
KO_STAGES = ["Round of 16", "Quarter-finals", "Semi-finals", "Final"]
KO_STAGE_NUM_MATCHES = [16, 8, 4, 1]
BREAK_BETWEEN_STAGES = datetime.timedelta(days=7 * 7)
BREAK_BETWEEN_LEGS = datetime.timedelta(days=7)


def table(matches, fixtures, played, competition, season, predictor):
    """Return the league table after a simulated season."""
    simulated = simulate_season(
        matches, fixtures, played, competition, season, predictor
    )
    season_matches = [*played, *simulated]
    if football.is_cup(competition):
        return ko_ranking(season_matches, competition)
    return league_table(season_matches, competition)


def simulate_season(
    matches, fixtures, played, competition, season, predictor, restrict=False
):
    """Return the simulated matches after a simulated season."""

    for match in matches:
        predictor.feed_match(match)

    category_to_score = get_category_to_score(matches)
    simulated = simulate_fixtures(fixtures, predictor, category_to_score)
    if restrict or not football.is_cup(competition):
        return simulated

    return complete_cup_season(
        simulated, played, competition, season, predictor, category_to_score
    )


def complete_cup_season(
    simulated, played, competition, season, predictor, category_to_score
):
    """Return the simulated matches after an extended cup season."""

    if competition != football.Competition('europe', 'champions'):
        raise NotImplementedError("don't know how to simulate this")

    simulated = list(simulated)

    matches_by_group, matches_by_ko_stage = order_cup_matches([*played, *simulated])

    for stage_no, expected_num_matches in enumerate(KO_STAGE_NUM_MATCHES):
        stage_matches = matches_by_ko_stage[stage_no]
        if stage_matches:
            if len(stage_matches) != expected_num_matches:
                raise ValueError("unexpected number of matches for this stage")
            continue

        if stage_no == 0:
            stage_fixtures = list(
                get_first_ko_fixtures(matches_by_group, competition, season, stage_no)
            )
        else:
            stage_fixtures = list(
                get_ko_fixtures(
                    matches_by_ko_stage[stage_no - 1], competition, season, stage_no
                )
            )

        matches_by_ko_stage[stage_no] = simulate_fixtures(
            stage_fixtures, predictor, category_to_score
        )
        simulated.extend(matches_by_ko_stage[stage_no])

    return simulated


def simulate_fixtures(fixtures, predictor, category_to_score):
    """Return simulated matches and update the predictor.

    The fixtures must be sorted chronologically.  The predictor is assumed to
    have been fed with previous matches."""

    simulated = []
    groups = itertools.groupby(fixtures, key=operator.attrgetter('date'))
    for _, todays_fixtures in groups:
        todays_matches = []
        for fixture in todays_fixtures:
            probabilities = predictor.predict(fixture)
            score = sample_score(probabilities, category_to_score)
            match = football.Match(
                fixture.competition,
                fixture.date,
                fixture.season,
                fixture.home,
                fixture.away,
                *score,
                utc_time=fixture.utc_time,
                stage=fixture.stage,
            )
            todays_matches.append(match)
        for match in todays_matches:
            predictor.feed_match(match)
        simulated.extend(todays_matches)
    return simulated


def get_first_ko_fixtures(matches_by_group, competition, season, stage_no):
    """Yield the first round of KO stage fixtures."""

    # Right now, teams from the same country or group are matched up against each other.
    # This is bad because it doesn't happen in reality.

    winners = []
    seconds = []
    for _, matches in sorted(matches_by_group.items()):
        winner, second, *_ = cl_group_table(matches, competition)
        winners.append(winner)
        seconds.append(second)

    latest_date, latest_time = max(
        (match.date, match.utc_time)
        for matches in matches_by_group.values()
        for match in matches
    )

    random.shuffle(winners)
    random.shuffle(seconds)

    matchups = []
    for (*teams,) in zip(winners, seconds):
        random.shuffle(teams)
        matchups.append(teams)

    yield from get_cl_fixtures(
        matchups, latest_date, latest_time, competition, season, stage_no
    )


def get_ko_fixtures(last_stage_matches, competition, season, stage_no):
    """Return a round of KO stage fixtures."""

    matches_by_matchup = collections.defaultdict(list)
    for match in last_stage_matches:
        matchup = frozenset({match.home, match.away})
        matches_by_matchup[matchup].append(match)

    winners = []
    for matches in sorted(matches_by_matchup.values()):
        if len(matches) != 2:
            raise ValueError("should be home and away match")
        home_goals = {}
        away_goals = {}
        tiebreaker = {}
        for match in matches:
            home_goals[match.home] = match.home_goals
            away_goals[match.away] = match.away_goals
        tiebreak = [0, 1]
        random.shuffle(tiebreak)
        tiebreaker[match.home], tiebreaker[match.away] = tiebreak
        keys = {
            team: (
                home_goals[team] + away_goals[team],
                away_goals[team],
                tiebreaker[team],
            )
            for team in tiebreaker
        }
        winners.append(max(keys, key=keys.get))

    latest_date, latest_time = max(
        (match.date, match.utc_time) for match in last_stage_matches
    )
    random.shuffle(winners)
    winners_iter = iter(winners)
    matchups = list(zip(winners_iter, winners_iter))
    yield from get_cl_fixtures(
        matchups, latest_date, latest_time, competition, season, stage_no
    )


def get_cl_fixtures(matchups, latest_date, latest_time, competition, season, stage_no):
    """Return a round of Champions League KO stage fixtures.

    The (team A, team B) order within `matchups` will be used as-is."""

    stage = KO_STAGES[stage_no]

    first_date = latest_date + BREAK_BETWEEN_STAGES
    second_date = first_date + BREAK_BETWEEN_LEGS
    first_time = latest_time + BREAK_BETWEEN_STAGES
    second_time = first_time + BREAK_BETWEEN_LEGS

    for home, away in matchups:
        yield football.Fixture(
            competition, first_date, first_time, season, stage, home, away
        )

    if stage_no == len(KO_STAGES) - 1:
        # Only one leg in the final.
        # Currently there is no way to mark a fixture as 'no home advantage'.
        return

    for away, home in matchups:
        yield football.Fixture(
            competition, second_date, second_time, season, stage, home, away
        )


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
        category_to_score[category] = {
            score: count / total for score, count in counter.items()
        }

    return category_to_score


def sample_score(probabilities, category_to_score):
    """Return a randomly sampled score."""
    category = random.choices(list(probabilities), probabilities.values())[0]
    scores = category_to_score[category]
    return random.choices(list(scores), scores.values())[0]


def ko_ranking(matches, competition, exp_matches=None, exp_teams=None):
    """Return a ranking of teams in a cup competition."""

    if exp_matches is None:
        exp_matches = football.num_matches(competition)
    if exp_teams is None:
        exp_teams = football.num_teams(competition)

    if len(matches) != exp_matches:
        raise ValueError(
            f"unexpected number of matches: {len(matches)} (expected {exp_matches})"
        )

    matches_by_group, matches_by_ko_stage = order_cup_matches(matches)

    ranking = []
    for stage_no, expected_num_matches in reversed(
        list(enumerate(KO_STAGE_NUM_MATCHES))
    ):
        stage_matches = matches_by_ko_stage[stage_no]
        if len(stage_matches) != expected_num_matches:
            raise ValueError("unexpected number of matches for this stage")

        stage_teams = set()
        for match in stage_matches:
            stage_teams.add(match.home)
            stage_teams.add(match.away)

        if len(stage_matches) == 1:
            match = stage_matches[0]
            if match.home > match.away:
                winner, loser = match.home, match.away
            elif match.home < match.away:
                winner, loser = match.away, match.home
            else:
                teams = [match.home, match.away]
                random.shuffle(teams)
                winner, loser = teams
            ranking.append(winner)
            ranking.append(loser)
        else:
            losers = sorted(stage_teams - previous_stage_teams)
            ranking.extend(losers)

        previous_stage_teams = stage_teams

    thirds = []
    fourths = []
    for _, matches in sorted(matches_by_group.items()):
        table = cl_group_table(matches, competition)
        *_, third, fourth = [team for team in table if team not in previous_stage_teams]
        thirds.append(third)
        fourths.append(fourth)

    thirds.sort()
    fourths.sort()

    ranking.extend(thirds)
    ranking.extend(fourths)

    num_teams = len(set(ranking))
    if len(ranking) != num_teams:
        raise RuntimeError(f"have duplicate teams")

    if num_teams != exp_teams:
        raise ValueError(f"bad number of teams: {num_teams} (expected {exp_teams})")

    return ranking


def cl_group_table(matches, competition):
    """Return the table of a Champions League group."""
    return league_table(
        matches, competition, exp_matches=12, exp_teams=4, cl_rules=True
    )


def league_table(
    matches, competition, exp_matches=None, exp_teams=None, cl_rules=False
):
    """Return a league table with random positions where necessary."""

    if exp_matches is None:
        exp_matches = football.num_matches(competition)
    if exp_teams is None:
        exp_teams = football.num_teams(competition)

    positions = partial_table(matches, exp_matches, exp_teams, cl_rules)

    teams = sorted(positions)
    tiebreakers = list(range(len(teams)))
    random.shuffle(tiebreakers)

    keys = {}
    for team, tiebreaker in zip(teams, tiebreakers):
        keys[team] = positions[team], tiebreaker

    if len(keys) != exp_teams:
        raise RuntimeError(
            f"broke the number of teams: {len(teams)} (expected {exp_teams})"
        )

    return sorted(keys, key=keys.get)


def partial_table(matches, exp_matches, exp_teams, cl_rules, inside=False):
    """Return a mapping of teams to indices in ranked order.

    `inside` is True if this is not the full list of matches (we are making a
    subtable)."""

    if len(matches) != exp_matches:
        raise ValueError(
            f"unexpected number of matches: {len(matches)} (expected {exp_matches})"
        )

    points = collections.Counter()
    scored = collections.Counter()
    scored_away = collections.Counter()
    wins = collections.Counter()
    away_wins = collections.Counter()
    conceded = collections.Counter()
    for match in matches:
        result = football.result(match.score)
        if result == '1':
            points[match.home] += 3
            wins[match.home] += 1
        elif result == '2':
            points[match.away] += 3
            wins[match.away] += 1
            away_wins[match.away] += 1
        else:
            points[match.home] += 1
            points[match.away] += 1
        scored[match.home] += match.home_goals
        scored[match.away] += match.away_goals
        scored_away[match.away] += match.away_goals
        conceded[match.home] += match.away_goals
        conceded[match.away] += match.home_goals

    teams = sorted(scored)
    if len(teams) != exp_teams:
        raise ValueError(
            f"unexpected number of teams: {len(teams)} (expected {exp_teams})"
        )

    keys = {}
    if cl_rules:
        teams_by_points = collections.defaultdict(list)
        for team in teams:
            teams_by_points[points[team]].append(team)
        for _, tied_teams in sorted(teams_by_points.items()):
            num_tied = len(tied_teams)
            if num_tied == 1 or num_tied == len(teams):
                positions = {team: 0 for team in tied_teams}
            else:
                tied_teams_set = set(tied_teams)
                partial_matches = [
                    match
                    for match in matches
                    if match.home in tied_teams_set and match.away in tied_teams_set
                ]
                exp_partial_matches = num_tied * (num_tied - 1)
                positions = partial_table(
                    partial_matches,
                    exp_partial_matches,
                    num_tied,
                    cl_rules,
                    inside=True,
                )

            for team in tied_teams:
                goal_diff = scored[team] - conceded[team]
                if inside:
                    keys[team] = (
                        points[team],
                        goal_diff,
                        scored[team],
                        scored_away[team],
                        -positions[team],
                    )
                else:
                    keys[team] = (
                        points[team],
                        -positions[team],
                        goal_diff,
                        scored[team],
                        scored_away[team],
                        wins[team],
                        away_wins[team],
                    )
    else:
        for team in teams:
            goal_diff = scored[team] - conceded[team]
            keys[team] = points[team], goal_diff, scored[team]

    teams_by_key = collections.defaultdict(list)
    for team, key in keys.items():
        teams_by_key[key].append(team)

    partial = [tied for _, tied in sorted(teams_by_key.items(), reverse=True)]
    return {team: i for i, tied in enumerate(partial) for team in tied}


def order_cup_matches(matches):
    """Return a matches by group and matches by KO stage ID."""
    matches_by_group = collections.defaultdict(list)
    matches_by_ko_stage = collections.defaultdict(list)
    for match in matches:
        if match.stage.startswith('Group'):
            group = match.stage.split()[1]
            matches_by_group[group].append(match)
        else:
            stage_no = KO_STAGES.index(match.stage)
            matches_by_ko_stage[stage_no].append(match)
    return matches_by_group, matches_by_ko_stage


def print_ranking(ranking, file=sys.stdout):
    """Print a ranking of teams."""
    for position, team in enumerate(ranking, 1):
        print(f"{position:2} {team}", file=file)
