"""Resources related to data sources."""


from sources import football_data, prediction_zone


FETCHERS = [prediction_zone.fetch]

# Ordered by trustworthyness.
SOURCES = [football_data.Source(), prediction_zone.Source()]
