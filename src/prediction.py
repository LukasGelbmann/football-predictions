"""Resources related to prediction."""


import functools


MAX_GOALS = 7
MAX_BASE = MAX_GOALS // 2


def category(match):
    """Return a score category, given a match."""
    return category_from_score(match.score)


def category_from_score(score):
    """Return a score category, given a score."""
    home, away = score
    if home + away <= MAX_GOALS:
        return score
    diff = min(abs(home - away), MAX_GOALS)
    base = MAX_BASE - diff // 2
    ceil = base + diff
    if home >= away:
        return ceil, base
    return base, ceil


@functools.lru_cache()
def categories():
    """Return an iterable of possible categories."""

    result = set()
    for home in range(0, MAX_GOALS + 1):
        for away in range(0, MAX_GOALS + 1):
            result.add(category_from_score((home, away)))

    def key(this_category):
        home, away = this_category
        return away - home, home

    return sorted(result, key=key)


def num_categories():
    """Return the number of possible categories."""
    return len(categories())


def category_to_str(match_category):
    """Return a string representation."""
    home, away = match_category
    sep = ':' if home + away < MAX_GOALS - 1 else '~'
    return f'{home}{sep}{away}'
