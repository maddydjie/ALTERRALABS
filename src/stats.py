"""Small, dependency-free stats helpers. Every function is explainable in a sentence."""
import math
import random


def wilson_ci(k, n, z=1.96):
    """Wilson 95% CI for a proportion k/n.

    Better than the naive p +/- z*sqrt(p(1-p)/n) when p is near 0 or 1 or n is small:
    it never leaves [0, 1] and has more honest coverage.
    """
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def mcnemar_exact(b, c):
    """Exact McNemar test for paired binary outcomes.

    b = pairs correct in condition 1 but wrong in condition 2
    c = pairs wrong in condition 1 but correct in condition 2
    Only these discordant pairs carry information. Under H0 (no effect) each
    discordant pair is a fair coin flip, so p = two-sided binomial(b+c, 0.5) test.
    Returns the p-value.
    """
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    # P(X <= k) for X ~ Binomial(n, 0.5), doubled for two-sided, capped at 1
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def bootstrap_ci(values, stat=None, n_boot=2000, seed=0, alpha=0.05):
    """Percentile bootstrap CI: resample with replacement, take the middle 95% of the statistic."""
    rng = random.Random(seed)
    stat = stat or (lambda xs: sum(xs) / len(xs))
    boots = sorted(stat([rng.choice(values) for _ in values]) for _ in range(n_boot))
    lo = boots[int(alpha / 2 * n_boot)]
    hi = boots[int((1 - alpha / 2) * n_boot) - 1]
    return (lo, hi)


def cohen_kappa(a, b):
    """Agreement between two label lists (e.g. grader vs my hand labels), corrected for chance."""
    n = len(a)
    labels = set(a) | set(b)
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(l) / n) * (b.count(l) / n) for l in labels)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)
