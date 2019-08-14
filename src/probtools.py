"""Resources related to probability."""


import math


def is_distribution(values):
    """Return True if `values` is a valid probability distribution."""
    return math.isclose(sum(values), 1) and all(x >= 0 for x in values)


def binomial_cdf(x, n, p):
    """Return the cumulative distribution of a binomial distribution."""
    # See https://stackoverflow.com/a/45869209
    result = 0
    b = 0
    for k in range(x+1):
        if k > 0:
            b += math.log(n-k+1) - math.log(k)
        log_pmf_k = b + k * math.log(p) + (n-k) * math.log(1-p)
        result += math.exp(log_pmf_k)
    return result
