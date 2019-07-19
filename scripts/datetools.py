"""Resources related to date and time."""


import datetime


def parse_date(date_str, format_str):
    """Return a datetime.date object.

    May raise a ValueError."""

    return parse_datetime(date_str, format_str).date()


def parse_datetime(datetime_str, format_str):
    """Return a datetime.datetime object.

    May raise a ValueError."""

    return datetime.datetime.strptime(datetime_str, format_str)


def date_from_iso(date_str):
    """Return a datetime.date object.

    May raise a ValueError."""

    return parse_date(date_str, '%Y-%m-%d')
