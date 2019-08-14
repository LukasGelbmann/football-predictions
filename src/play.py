#!/usr/bin/env python3

"""Script to play prediction games.

This script requires Python 3.6 or higher."""


import sys


COMMANDS = ['result', 'market', 'league', 'overall']


def print_help():
    """Print a help message."""
    if sys.argv and sys.argv[0]:
        name = sys.argv[0]
    else:
        name = 'play.py'
    print(f"Usage: {name} command", file=sys.stderr)
    print("Valid commands:", ', '.join(COMMANDS), file=sys.stderr)


def perform(command):
    """Perform a command."""
    if command == 'result':
        import games.result_prediction
        games.result_prediction.play()
    elif command == 'market':
        import games.stock_market
        games.stock_market.play()
    elif command == 'league':
        import games.prediction_league
        games.prediction_league.play()
    elif command == 'overall':
        import games.overall
        games.overall.play()
    else:
        print("Unknown command", file=sys.stderr)


def main():
    """Fetch the data."""
    command = sys.argv[1] if len(sys.argv) > 1 else ''
    if command not in COMMANDS:
        print_help()
        exit(1)
    perform(command)


if __name__ == '__main__':
    main()
