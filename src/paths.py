"""Path-related resources."""


import os
import pathlib


# Path().resolve() isn't used here because it doesn't work in PyPy 3.6 for
# Windows.
HERE = pathlib.Path(os.path.realpath(__file__)).parent
DATA_DIR = HERE.parent / 'data'
CONSOLIDATED_DIR = DATA_DIR / 'consolidated'


def stem(path):
    """Return the final path component, minus it's last suffix.

    Same as `pathlib.Path(path).stem`."""

    name = os.path.basename(path)
    i = name.rfind('.')
    if 0 < i < len(name) - 1:
        return name[:i]
    return name


def csv_files(path, start=''):
    """Return an iterable of CSV files in a directory.

    May raise an OSError."""

    return sorted(item for item in path.glob(start + '*.csv')
                  if item.is_file())
