"""Ensure that the running version of Python is good."""


import sys


def check(minimal):
    """Exit if we are not running the right Python version."""
    if sys.version_info < minimal:
        message = "Error: this is Python {}.{}, need {}.{} or higher.".format(
            sys.version_info.major, sys.version_info.minor, *minimal
        )
        print(message, file=sys.stderr)
        exit(1)


if __name__ == '__main__':
    check(minimal=(3, 6))
