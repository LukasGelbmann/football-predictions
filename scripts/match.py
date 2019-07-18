"""Helpers for representing football matches."""


import datetime
import typing


class Match(typing.NamedTuple):
    """A football match."""

    date: datetime.date
    home: str
    away: str
    home_goals: int
    away_goals: int

    home_half_time: int = None
    away_half_time: int = None
    home_shots: int = None
    away_shots: int = None
    home_shots_on_target: int = None
    away_shots_on_target: int = None
    home_woodwork: int = None
    away_woodwork: int = None
    home_corners: int = None
    away_corners: int = None
    home_fouls_committed: int = None
    away_fouls_committed: int = None
    home_free_kicks_conceded: int = None
    away_free_kicks_conceded: int = None
    home_offsides: int = None
    away_offsides: int = None
    home_yellow: int = None
    away_yellow: int = None
    home_yellow_no_red: int = None
    away_yellow_no_red: int = None
    home_red: int = None
    away_red: int = None
    time: datetime.datetime = None
