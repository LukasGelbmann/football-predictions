"""Data sources for football results."""


import csv
import datetime

from match import Match
import paths


class Source:
    """A data source."""

    def __init__(self, name):
        """Initialize the source."""
        self.name = name
        self.regions = None
        self.get_competitions = None
        self.get_seasons = None
        self.fetch_season = None


def _get_football_data_local():
    """Return the source object for local data from football-data."""

    competitions = {
        'belgium': {
            'pro-league': 'B1',
        },
        'england': {
            'premier': 'E0',
            'championship': 'E1',
            'league-1': 'E2',
            'league-2': 'E3',
            'national': 'EC',
        },
        'france': {
            'ligue-1': 'F1',
            'ligue-2': 'F2',
        },
        'germany': {
            'bundesliga': 'D1',
            'zweite': 'D2',
        },
        'greece': {
            'super-league': 'G1',
        },
        'italy': {
            'serie-a': 'I1',
            'serie-b': 'I2',
        },
        'netherlands': {
            'eredivisie': 'N1',
        },
        'portugal': {
            'primeira': 'P1',
        },
        'scotland': {
            'premiership': 'SC0',
            'championship': 'SC1',
            'league-1': 'SC2',
            'league-2': 'SC3',
        },
        'spain': {
            'primera': 'SP1',
            'segunda': 'SP2',
        },
        'turkey': {
            'super-lig': 'T1',
        },
    }

    season_folders = {}
    for year in range(1994, 2020):
        start = year - 1
        end = year % 100
        season_folders[f'{start}-{end:02}'] = f'{start % 100 :02}{end:02}'

    football_data_dir = paths.DATA_DIR / 'football-data-raw'

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
                        time = datetime.datetime.strptime(date_str, format_str)
                    except ValueError:
                        pass
                    else:
                        date = time.date()
                        break

                if date is None:
                    raise ValueError(f"Unparsable date: {date_str}")

                kwargs['date'] = date
                kwargs['home'] = fields.get('HomeTeam') or fields['HT']
                kwargs['away'] = fields.get('AwayTeam') or fields['AT']
                for target_name, source_name in get_int_fields(region).items():
                    if source_name in fields and fields[source_name]:
                        kwargs[target_name] = int(fields[source_name])

                if 'home_goals' not in kwargs or 'away_goals' not in kwargs:
                    continue

                yield Match(**kwargs)

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
                'away_yellow_no_red': 'HY',
            })
        else:
            fields.update({
                'home_yellow': 'HY',
                'away_yellow': 'HY',
            })

        return fields

    source = Source('football-data')
    source.regions = list(competitions)
    source.get_competitions = get_competitions
    source.get_seasons = get_seasons
    source.fetch_season = fetch_season
    return source


football_data_local = _get_football_data_local()
