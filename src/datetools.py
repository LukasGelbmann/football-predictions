"""Resources related to date and time."""


import datetime


# Lowest possible UTC offset by region, for practical reasons.
UTC_OFFSETS = {
    'argentina': -3,
    'austria': +1,
    'belgium': +1,
    'brazil': -5,
    'china': +8,
    'denmark': +1,
    'england': 0,
    'finland': +2,
    'france': +1,
    'germany': +1,
    'greece': +2,
    'ireland': 0,
    'italy': +1,
    'japan': +9,
    'mexico': -8,
    'netherlands': +1,
    'norway': +1,
    'poland': +1,
    'portugal': 0,
    'romania': +2,
    'russia': +2,
    'scotland': 0,
    'spain': +1,
    'sweden': +1,
    'switzerland': +1,
    'turkey': +3,
    'usa': -10,
}

# Maximum possible combines timezone and daylight saving time difference.
MAX_TIMEZONE_DIFF = {
    'argentina': 1,
    'austria': 1,
    'belgium': 1,
    'brazil': 3,
    'china': 0,
    'denmark': 1,
    'england': 1,
    'finland': 1,
    'france': 1,
    'germany': 1,
    'greece': 1,
    'ireland': 1,
    'italy': 1,
    'japan': 0,
    'mexico': 4,
    'netherlands': 1,
    'norway': 1,
    'poland': 1,
    'portugal': 1,
    'romania': 1,
    'russia': 11,
    'scotland': 1,
    'spain': 1,
    'sweden': 1,
    'switzerland': 1,
    'turkey': 1,
    'usa': 6,
}

TIMEZONES = {region: datetime.timezone(datetime.timedelta(hours=offset))
             for region, offset in UTC_OFFSETS.items()}
MAX_TIME_DIFF = {region: datetime.timedelta(hours=diff)
                 for region, diff in MAX_TIMEZONE_DIFF.items()}

ISO_DATETIME_FORMAT = '%Y-%m-%d %H:%M'


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


def datetime_from_iso(datetime_str):
    """Return a datetime.datetime object.

    May raise a ValueError."""

    return parse_datetime(datetime_str, ISO_DATETIME_FORMAT)


def datetime_to_iso(datetime_obj):
    """Return a formatted string."""
    return datetime_obj.strftime(ISO_DATETIME_FORMAT)


def from_utc(utc_datetime, timezone):
    """Return an aware datetime.datetime object."""
    return timezone.fromutc(utc_datetime.replace(tzinfo=timezone))


def to_utc(aware_datetime):
    """Return a UTC datetime.datetime object."""
    return aware_datetime.astimezone(datetime.timezone.utc)
