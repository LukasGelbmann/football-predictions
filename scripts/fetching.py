"""Resources for fetching football match data."""


import csv
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


def _get_football_data_local():
    """Return the source object for local data from football-data."""

    competitions = {
        'belgium': {
            '1st-league': 'B1',
        },
        'england': {
            'premier': 'E0',
            '2nd-league': 'E1',
            '3rd-league': 'E2',
            '4th-league': 'E3',
            '5th-league': 'EC',
        },
        'france': {
            '1st-league': 'F1',
            '2nd-league': 'F2',
        },
        'germany': {
            'bundesliga': 'D1',
            'zweite': 'D2',
        },
        'greece': {
            '1st-league': 'G1',
        },
        'italy': {
            'serie-a': 'I1',
            'serie-b': 'I2',
        },
        'netherlands': {
            'eredivisie': 'N1',
        },
        'portugal': {
            '1st-league': 'P1',
        },
        'scotland': {
            '1st-league': 'SC0',
            '2nd-league': 'SC1',
            '3rd-league': 'SC2',
            '4th-league': 'SC3',
        },
        'spain': {
            'primera': 'SP1',
            'segunda': 'SP2',
        },
        'turkey': {
            '1st-league': 'T1',
        },
    }

    season_folders = {}
    for year in range(1994, 2020):
        start = year - 1
        end = year % 100
        season_folders[f'{start}-{end:02}'] = f'{start % 100 :02}{end:02}'

    football_data_dir = paths.DATA_DIR / 'football-data-raw'

    def get_regions():
        """Return an iterable of regions."""
        return list(competitions)

    def get_competitions(region):
        """Return an iterable of competitions for a region."""
        return list(competitions[region])

    def get_seasons(region, competition):
        """Yield all seasons for a region and competition."""

        for season in season_folders:
            path = get_path(region, competition, season)

            try:
                season_exists = path.is_file()
            except OSError as e:
                print("Couldn't check for file existence:", e, file=sys.stderr)
                continue

            if season_exists:
                yield season

    def fetch_season(region, competition, season):
        """Fetch and yield all matches of a season from football-data."""

        path = get_path(region, competition, season)

        try:
            file = open(path, encoding='utf-8', errors='ignore', newline='')
        except OSError as e:
            print("Couldn't open CSV file:", e, file=sys.stderr)
            return

        with file:
            reader = csv.DictReader(file)
            for fields in reader:
                kwargs = {}

                date_str = fields['Date']

                if not date_str:
                    continue

                date = None
                for format_str in '%d/%m/%y', '%d/%m/%Y':
                    try:
                        date = datetools.parse_date(date_str, format_str)
                    except ValueError:
                        pass
                    else:
                        break

                if date is None:
                    raise ValueError(f"Couldn't parse date: {date_str}")

                kwargs['date'] = date
                kwargs['home'] = fields.get('HomeTeam') or fields['HT']
                kwargs['away'] = fields.get('AwayTeam') or fields['AT']
                for target_name, source_name in get_int_fields(region).items():
                    value = fields.get(source_name)
                    if value:
                        kwargs[target_name] = int(value)

                if 'home_goals' not in kwargs or 'away_goals' not in kwargs:
                    continue

                yield football.Match(**kwargs)

    def get_path(region, competition, season):
        """Return the path where the raw data of a season is stored."""
        filename = competitions[region][competition] + '.csv'
        return football_data_dir / season_folders[season] / filename

    def get_int_fields(region):
        """Return a mapping from target field names to source field names."""

        fields = {
            'home_goals': 'FTHG',
            'away_goals': 'FTAG',
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
            'home_red': 'HR',
            'away_red': 'AR',
        }

        if region in ('england', 'scotland'):
            fields.update({
                'home_yellow_no_red': 'HY',
                'away_yellow_no_red': 'AY',
            })
        else:
            fields.update({
                'home_yellow': 'HY',
                'away_yellow': 'AY',
            })

        return fields

    source = Source('football-data')
    source.regions = get_regions
    source.competitions = get_competitions
    source.seasons = get_seasons
    source.fetch_season = fetch_season
    return source


football_data_local = _get_football_data_local()

sources = [football_data_local]
