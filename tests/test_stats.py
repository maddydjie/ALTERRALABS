"""Sanity checks for stats.py against known values."""
from src.stats import wilson_ci, mcnemar_exact, cohen_kappa

lo, hi = wilson_ci(10, 100)
assert abs(lo - 0.0552) < 1e-3 and abs(hi - 0.1744) < 1e-3, (lo, hi)  # known Wilson value for 10/100
assert wilson_ci(0, 20)[0] == 0.0
assert abs(mcnemar_exact(10, 2) - 0.03857) < 1e-4   # 2*P(X<=2 | n=12)
assert mcnemar_exact(0, 0) == 1.0
assert cohen_kappa([1, 1, 0, 0], [1, 1, 0, 0]) == 1.0
print("stats ok")
