"""Resources for fetching football match data."""


import csv
import itertools
import pprint
import sys

import datetools
import football
import paths


class Source:
    """A data source."""

    def __init__(self, name):
        """Initialize the source."""
        self.name = name
        self.regions = None
        self.competitions = None
        self.seasons = None
        self.fetch_season = None


def print_fields(fields, explanation):
    """Pretty print fields to stderr."""
    print(f'{explanation}:', file=sys.stderr)
    pprint.pprint(fields, stream=sys.stderr)
    print(file=sys.stderr)


def _get_football_data():
    """Return the source object for local data from football-data."""

    core = {
        'belgium': ['B1'],
        'england': ['E0', 'E1', 'E2', 'E3', 'EC'],
        'france': ['F1', 'F2'],
        'germany': ['D1', 'D2'],
        'greece': ['G1'],
        'italy': ['I1', 'I2'],
        'netherlands': ['N1'],
        'portugal': ['P1'],
        'scotland': ['SC0', 'SC1', 'SC2', 'SC3'],
        'spain': ['SP1', 'SP2'],
        'turkey': ['T1'],
    }

    competitions = {region: dict(zip(football.LEAGUES[region], names))
                    for region, names in core.items()}

    extra_regions = {
        'argentina': 'ARG',
        'austria': 'AUT',
        'brazil': 'BRA',
        'china': 'CHN',
        'denmark': 'DNK',
        'finland': 'FIN',
        'ireland': 'IRL',
        'japan': 'JPN',
        'mexico': 'MEX',
        'norway': 'NOR',
        'poland': 'POL',
        'romania': 'ROU',
        'russia': 'RUS',
        'sweden': 'SWE',
        'switzerland': 'SWZ',
        'usa': 'USA',
    }

    str_fields = {
        'home': ['HomeTeam', 'Home', 'HT'],
        'away': ['AwayTeam', 'Away', 'AT'],
    }

    score_fields = {
        'home_goals': ['FTHG', 'HG'],
        'away_goals': ['FTAG', 'AG'],
    }

    int_fields_general = {
        'home_half_time': 'HTHG',
        'away_half_time': 'HTAG',
        'home_shots': 'HS',
        'away_shots': 'AS',
        'home_shots_on_target': 'HST',
        'away_shots_on_target': 'AST',
        'home_woodwork': 'HHW',
        'away_woodwork': 'AHW',
        'home_corners': 'HC',
        'away_corners': 'AC',
        'home_fouls_committed': 'HF',
        'away_fouls_committed': 'AF',
        'home_free_kicks_conceded': 'HFKC',
        'away_free_kicks_conceded': 'AFKC',
        'home_offsides': 'HO',
        'away_offsides': 'AO',
        'home_yellow': 'HY',
        'away_yellow': 'AY',
        'home_red': 'HR',
        'away_red': 'AR',
    }

    int_fields_uk = int_fields_general.copy()
    del int_fields_uk['home_yellow']
    del int_fields_uk['away_yellow']
    int_fields_uk['home_yellow_no_red'] = 'HY'
    int_fields_uk['away_yellow_no_red'] = 'AY'

    kwargs_keys = (set(str_fields) | set(score_fields)
                   | set(int_fields_general) | set(int_fields_uk))
    kwargs_keys_home = {key for key in kwargs_keys if key.startswith('home')}
    kwargs_keys_away = {key for key in kwargs_keys if key.startswith('away')}

    kwarg_pairs = list(zip(sorted(kwargs_keys_home), sorted(kwargs_keys_away)))
    assert all(home[4:] == away[4:] for home, away in kwarg_pairs)

    season_folders = {}
    for year in range(1994, 2020):
        start = year - 1
        end = year % 100
        season_folders[f'{start}-{end:02}'] = f'{start % 100 :02}{end:02}'

    football_data_dir = paths.DATA_DIR / 'football-data-raw'

    def get_regions():
        """Return an iterable of regions."""
        return sorted(itertools.chain(competitions, extra_regions))

    def get_competitions(region):
        """Return an iterable of competitions for a region."""
        if region in competitions:
            return list(competitions[region])
        if region in extra_regions:
            return football.LEAGUES[region][:1]
        return []

    def get_seasons(region, competition):
        """Yield all seasons for a region and a competition."""

        if region in extra_regions:
            yield from extra_region_seasons(region, competition)
            return

        for season in season_folders:
            path = get_path(region, competition, season)
            try:
                season_exists = path.is_file()
            except OSError as e:
                print("Couldn't check for file existence:", e, file=sys.stderr)
                continue

            if season_exists:
                yield season

    def extra_region_seasons(region, competition):
        """Return a competition's seasons for an extra region."""

        if competition != football.LEAGUES[region][0]:
            return []

        seasons = set()
        path = get_extra_path(region)
        for fields in raw_fields(path):
            season = season_from_raw(fields)
            seasons.add(season)
        return sorted(seasons)

    def fetch_season(region, competition, season):
        """Fetch and yield all matches of a season from football-data."""

        if region in extra_regions:
            yield from fetch_extra_season(region, competition, season)
            return

        path = get_path(region, competition, season)
        for fields in raw_fields(path):
            match = match_from_fields(fields, region)
            if match:
                yield match

    def fetch_extra_season(region, competition, season):
        """Yield all matches of an extra region's season from football-data."""

        if competition != football.LEAGUES[region][0]:
            return

        path = get_extra_path(region)
        for fields in raw_fields(path):
            if season_from_raw(fields) == season:
                match = match_from_fields(fields, region)
                if match:
                    yield match

    def match_from_fields(fields, region, check_consistency=False):
        """Return a football.Match object."""

        int_fields = get_int_fields(region)

        forfeited = None
        half_time_is_full_time = False

        kwargs = {}

        for target_name, source_names in score_fields.items():
            for name in source_names:
                value = fields.get(name)
                if value:
                    kwargs[target_name] = int(value)
                    break

        if len(kwargs) == 1:
            print_fields(fields, "Score fields are inconsistent")
            return None

        if not kwargs:
            home_half_time = None
            home_half_time_str = fields.get(int_fields['home_half_time'])
            if home_half_time_str:
                home_half_time = int(home_half_time_str)

            away_half_time = None
            away_half_time_str = fields.get(int_fields['away_half_time'])
            if away_half_time_str:
                away_half_time = int(away_half_time_str)

            if home_half_time is None or away_half_time is None:
                if home_half_time is not None or away_half_time is not None:
                    print_fields(fields, "Half time fields are inconsistent")
                return None

            if {home_half_time, away_half_time} == {3, 0}:
                half_time_is_full_time = True
                forfeited = True
                print_fields(fields, "Treating match as forfeited")
            else:
                print_fields(fields, "Match seems abandoned")
                return None

        kwargs['date'], kwargs['utc_time'] = date_and_utc_time(fields, region)

        for target_name, source_names in str_fields.items():
            for name in source_names:
                value = fields.get(name)
                if value:
                    kwargs[target_name] = value.strip()
                    break

        for target_name, source_name in int_fields.items():
            value = fields.get(source_name)
            if value:
                kwargs[target_name] = int(value)

        kwargs['forfeited'] = forfeited

        if half_time_is_full_time:
            kwargs['home_goals'] = kwargs.pop('home_half_time')
            kwargs['away_goals'] = kwargs.pop('away_half_time')

        if check_consistency:
            for home_name, away_name in kwarg_pairs:
                if (home_name in kwargs) != (away_name in kwargs):
                    print_fields(fields, "Field pairs are inconsistent")
                    break

        return football.Match(**kwargs)

    def raw_fields(path):
        """Yield the fields of a CSV file as mappings."""

        try:
            file = open(path, encoding='utf-8', errors='ignore', newline='')
        except OSError as e:
            print("Couldn't open CSV file:", e, file=sys.stderr)
            return

        with file:
            yield from csv.DictReader(file)

    def date_and_utc_time(fields, region, check_plausibility=True):
        """Return local date and UTC datetime."""

        date_str = fields['Date']
        time_str = fields.get('Time')

        if time_str:
            datetime_str = f'{date_str} {time_str}'
            utc_time = datetools.parse_datetime(datetime_str, '%d/%m/%Y %H:%M')
            timezone = datetools.TIMEZONES[region]
            region_time = datetools.from_utc(utc_time, timezone)
            if check_plausibility:
                earliest_local_time = region_time.replace(tzinfo=None)
                max_time_diff = datetools.MAX_TIME_DIFF[region]
                latest_local_time = earliest_local_time + max_time_diff
                if (earliest_local_time.date() == latest_local_time.date()
                    and latest_local_time.time() < football.EARLIEST_START):
                    print_fields(fields, "Strange time to play football")
            date = region_time.date()
            return date, utc_time

        date = None
        for format_str in '%d/%m/%y', '%d/%m/%Y':
            try:
                date = datetools.parse_date(date_str, format_str)
            except ValueError:
                pass
            else:
                break

        if date is None:
            raise ValueError(f"Couldn't parse date: {date_str!r}")

        return date, None

    def get_path(region, competition, season):
        """Return the path where the raw data of a season is stored."""
        filename = competitions[region][competition] + '.csv'
        return football_data_dir / season_folders[season] / filename

    def get_extra_path(region):
        """Return the path where the raw data of an extra region is stored."""
        filename = extra_regions[region] + '.csv'
        return football_data_dir / filename

    def season_from_raw(fields):
        """Return the season, given a fields mapping."""
        start, _, end = fields['Season'].partition('/')
        if end:
            return start + '-' + end[-2:]
        return start

    def get_int_fields(region):
        """Return a mapping from target field names to source field names."""
        if region in {'england', 'scotland'}:
            return int_fields_uk
        return int_fields_general

    source = Source('football-data')
    source.regions = get_regions
    source.competitions = get_competitions
    source.seasons = get_seasons
    source.fetch_season = fetch_season
    return source


football_data = _get_football_data()

sources = [football_data]
