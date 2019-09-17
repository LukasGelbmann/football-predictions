"""Resources for Prediction Zone."""


import functools
import sys
import urllib.error
import urllib.parse
import urllib.request

import football
import paths


BASE_URL = 'https://prediction.zone/api'

COMPETITION_NAMES = {
    football.Competition('england', 'premier'): 'premierleague',
    football.Competition('europe', 'champions'): 'championsleague',
    football.Competition('germany', 'bundesliga'): 'bundesliga',
}

COMPETITIONS = sorted(COMPETITION_NAMES)


def buy(competition, season, team, price, limit):
    """Place a buy order online."""
    place_order(competition, season, team, 'buy', price, limit)


def sell(competition, season, team, price, limit):
    """Place a sell order online."""
    place_order(competition, season, team, 'sell', price, limit)


def place_order(competition, season, team, order, price, limit):
    """Place an order online."""
    name = season_name(competition, season)
    data = {
        'team': team,
        'order': order,
        'price': price,
        'limit': limit,
        'expires': 'm',
    }
    post_to(f'stockmarket2/{name}/order', data)


def get_set_price(competition, season):
    """Return the set price."""

    name = season_name(competition, season)
    url = f'{BASE_URL}/stockmarket2/{name}/get_setprice'

    try:
        response = urllib.request.urlopen(url)
    except urllib.error.HTTPError:
        print("Couldn't reach", url, file=sys.stderr)
        raise NotImplementedError("don't know how to handle this")

    with response:
        code = response.getcode()
        if code != 200:
            print(f"Got HTTP status code {code} from {url}", file=sys.stderr)
        return int(response.read())


def get_cash(competition, season):
    """Return the cash owned."""
    name = season_name(competition, season)
    response_text = post_and_retrieve(f'stockmarket2/{name}/get_cash')
    return int(response_text)


def buy_sets(amount, competition, season):
    """Attempt to buy sets and return the number bought."""
    name = season_name(competition, season)
    data = {'sets': amount}
    response_text = post_and_retrieve(f'stockmarket2/{name}/buy_set', data)
    return int(response_text.split()[0])


def predict_score(fixture, score):
    """Place a score prediction."""
    name = season_name(fixture.competition, fixture.season)
    home_goals, away_goals = score
    data = {
        'hometeam': fixture.home,
        'awayteam': fixture.away,
        'homegoals': home_goals,
        'awaygoals': away_goals,
    }
    post_to(f'resultprediction/{name}/match', data)


def predict_result(fixture, result):
    """Place a result prediction."""
    name = season_name(fixture.competition, fixture.season)
    data = {'hometeam': fixture.home, 'awayteam': fixture.away, 'prediction': result}
    post_to(f'predictionleague/{name}/match', data)


def get_league_size(competition, season):
    """Return the size of our league."""
    name = season_name(competition, season)
    response_text = post_and_retrieve(f'predictionleague/{name}/get_ranking')
    return len(response_text.splitlines())


def post_to(endpoint, data=None):
    """Make a post request."""

    if data is None:
        data = {}

    try:
        response = post(endpoint, data)
    except urllib.error.HTTPError:
        print("Couldn't reach endpoint", endpoint, file=sys.stderr)
        return

    with response:
        code = response.getcode()
        if code != 200:
            print(
                f"Got HTTP status code {code} from endpoint {endpoint}", file=sys.stderr
            )


def post_and_retrieve(endpoint, data=None):
    """Make a post request."""

    if data is None:
        data = {}

    try:
        response = post(endpoint, data)
    except urllib.error.HTTPError:
        print("Couldn't reach endpoint", endpoint, file=sys.stderr)
        raise NotImplementedError("don't know how to handle this")

    with response:
        code = response.getcode()
        if code != 200:
            print(
                f"Got HTTP status code {code} from endpoint {endpoint}", file=sys.stderr
            )
        return response.read()


def post(endpoint, data):
    """Make a post request."""
    data_dict = {**credentials(), **data}
    data_bytes = urllib.parse.urlencode(data_dict).encode()
    url = BASE_URL + '/' + endpoint
    return urllib.request.urlopen(url, data_bytes)


def season_name(competition, season):
    """Return the canonical string for a season."""
    name = COMPETITION_NAMES[competition]
    return f'{name}{season.start % 100 :02}{season.end % 100 :02}'


@functools.lru_cache()
def credentials():
    """Return our username and password."""

    path = paths.DATA_DIR / 'credentials.txt'

    try:
        file = open(path, encoding='utf-8')
    except OSError as exc:
        print("Couldn't open credentials file:", exc, file=sys.stderr)
        raise

    with file:
        username, password = (line.strip() for line in file)

    return {'username': username, 'password': password}
