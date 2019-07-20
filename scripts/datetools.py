"""Resources related to date and time."""


import datetime


UTC_OFFSETS = {
    'argentina': -3,
    'austria': +1,
    'belgium': +1,
    'brazil': -4,
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
    'mexico': -6,
    'netherlands': +1,
    'norway': +1,
    'poland': +1,
    'portugal': 0,
    'romania': +2,
    'russia': +3,
    'scotland': 0,
    'spain': +1,
    'sweden': +1,
    'switzerland': +1,
    'turkey': +3,
    'usa': -8,
}

TIMEZONES = {region: datetime.timezone(datetime.timedelta(hours=offset))
             for region, offset in UTC_OFFSETS.items()}

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
