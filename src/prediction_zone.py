"""Resources for Prediction Zone."""


import sys
import urllib.parse
import urllib.request

import data
import paths


BASE_URL = 'https://prediction.zone/api'

RAW_DIR = paths.DATA_DIR / 'prediction-zone-raw'

COMPETITIONS = {('england', 'premier'): 'premierleague'}


def download_calendar(region, competition, season):
    """Store the match calendar on disk."""

    try:
        RAW_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print("Couldn't make target directory:", e, file=sys.stderr)
        return

    name = season_name(region, competition, season)
    url = f'{BASE_URL}/{name}/get_matches?content=tnmr&all'
    urllib.request.urlretrieve(url, file_path(region, competition, season))


def season_name(region, competition, season):
    """Return the canonical string for a season."""
    name = COMPETITIONS[region, competition]
    start, end = season.split('-')
    season_str = start[-2:] + end
    return name + season_str


def file_path(region, competition, season):
    """Return the path for a calendar CSV file."""
    filename = season_name(region, competition, season) + '.csv'
    return RAW_DIR / filename


def place_order(region, competition, season, team, order, price, limit):
    """Place an order online."""
    name = season_name(region, competition, season)
    data_dict = {'username': data.username(), 'password': data.password(),
                 'team': team, 'order': order, 'price': price, 'limit': limit,
                 'expires': 'm'}
    data_bytes = urllib.parse.urlencode(data_dict).encode()
    url = f'{BASE_URL}/stockmarket2/{name}/order'
    with urllib.request.urlopen(url, data_bytes) as response:
        if response.getcode() != 200:
            print("Couldn't place order:", response.read(), file=sys.stderr)


def get_set_price(region, competition, season):
    """Return the set price."""
    name = season_name(region, competition, season)
    url = f'{BASE_URL}/stockmarket2/{name}/get_setprice'
    with urllib.request.urlopen(url) as response:
        if response.getcode() != 200:
            print("Couldn't get set price:", response.read(), file=sys.stderr)
            raise NotImplementedError("don't know how to handle this")
        return int(response.read())


def get_cash(region, competition, season):
    """Return the cash owned."""
    name = season_name(region, competition, season)
    data_dict = {'username': data.username(), 'password': data.password()}
    data_str = urllib.parse.urlencode(data_dict)
    url = f'{BASE_URL}/stockmarket2/{name}/get_cash'
    with urllib.request.urlopen(url + '?' + data_str) as response:
        if response.getcode() != 200:
            print("Couldn't get cash:", response.read(), file=sys.stderr)
            raise NotImplementedError("don't know how to handle this")
        return int(response.read())


def buy_sets(region, competition, season, amount):
    """Attempt to buy sets and return the number bought."""
    name = season_name(region, competition, season)
    data_dict = {'username': data.username(), 'password': data.password(),
                 'sets': amount}
    data_bytes = urllib.parse.urlencode(data_dict).encode()
    url = f'{BASE_URL}/stockmarket2/{name}/buy_set'
    with urllib.request.urlopen(url, data_bytes) as response:
        if response.getcode() != 200:
            print("Couldn't buy sets:", response.read(), file=sys.stderr)
            raise NotImplementedError("don't know how to handle this")
        return int(response.read().split()[0])
