#!/usr/bin/env python3

"""Script to fetch historical football data from the Internet.

This script requires Python 3.6 or higher."""


import sources


def main():
    """Fetch the data."""
    for fetch in sources.FETCHERS:
        fetch()


if __name__ == '__main__':
    main()
