#!/usr/bin/env python3

"""Script to play prediction games.

This script requires Python 3.6 or higher."""


import sys


COMMANDS = ['result', 'stocks', 'league', 'overall']


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
        import games.result_prediction as game_module
    elif command == 'stocks':
        import games.stock_market as game_module
    elif command == 'league':
        import games.prediction_league as game_module
    elif command == 'overall':
        import games.overall as game_module
    else:
        print("Unknown command", file=sys.stderr)
    game_module.play()


def main():
    """Fetch the data."""
    command = sys.argv[1] if len(sys.argv) > 1 else ''
    if command not in COMMANDS:
        print_help()
        exit(1)
    perform(command)


if __name__ == '__main__':
    main()
