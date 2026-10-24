"""Índice de problemas: relaciona cada (distribución, problema) con la función que lo resuelve."""

from intervals import (
    one_mean, paired_samples, two_means, one_proportion, two_proportions, one_variance,
    variance_ratio, sample_size,
)
from probability import probability


PROBLEMS = {
    ("z", "mean_interval"): one_mean,
    ("z", "two_means"): two_means,
    ("z", "one_proportion"): one_proportion,
    ("z", "two_proportions"): two_proportions,
    ("z", "sample_size"): sample_size,
    ("z", "probability"): probability,
    ("t", "mean_interval"): one_mean,
    ("t", "two_means"): two_means,
    ("t", "paired"): paired_samples,
    ("t", "probability"): probability,
    ("chi2", "variance_interval"): one_variance,
    ("chi2", "probability"): probability,
    ("f", "variance_ratio"): variance_ratio,
    ("f", "probability"): probability,
}


def solve(data):
    problem = PROBLEMS.get((data.get("distribution"), data.get("problem")))
    if problem is None:
        raise ValueError("Elige una distribución y un tipo de problema.")
    return problem(data)
