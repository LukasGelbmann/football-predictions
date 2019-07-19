"""Path-related resources."""


import pathlib


HERE = pathlib.Path(__file__).resolve().parent
DATA_DIR = HERE.parent / 'data'
CONSOLIDATED_DIR = DATA_DIR / 'consolidated'
