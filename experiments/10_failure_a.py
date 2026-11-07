"""Failure A analysis: omission rate per condition, paired against base.

Reads results/run_a_primary.csv (written by src.run), writes results/failure_a_summary.csv.
Usage: python experiments/10_failure_a.py [results/run_a_primary.csv]
"""
import sys

import pandas as pd

from src.stats import mcnemar_exact, wilson_ci

path = sys.argv[1] if len(sys.argv) > 1 else "results/run_a_primary.csv"
d = pd.read_csv(path)
d["empty_list"] = ((d.n_items == 0) & (d.omitted == 1)).astype(int)  # worst form: "no allergies"

wide = d.pivot(index="parent_id", columns="condition", values="omitted")
perturbed = [c for c in wide.columns if c != "base"]

rows = []
for cond in ["base"] + perturbed:
    sub = d[d.condition == cond]
    k, n = int(sub.omitted.sum()), len(sub)
    lo, hi = wilson_ci(k, n)
    row = {"condition": cond, "n": n, "omitted": k, "rate": k / n, "ci_lo": lo, "ci_hi": hi,
           "empty_list": int(sub.empty_list.sum()), "parse_fail": int((~sub.parse_ok).sum())}
    if cond != "base":
        # paired: only notes that have both base and this condition (abbrev exists for a subset)
        both = wide[["base", cond]].dropna()
        worse = int(((both.base == 0) & (both[cond] == 1)).sum())   # base ok, perturbed omitted
        better = int(((both.base == 1) & (both[cond] == 0)).sum())  # base omitted, perturbed ok
        row.update({"paired_n": len(both), "worse": worse, "better": better,
                    "diff_pp": 100 * (both[cond].mean() - both.base.mean()),
                    "mcnemar_p": mcnemar_exact(worse, better)})
    rows.append(row)

out = pd.DataFrame(rows)
# Holm correction across the perturbed conditions (preregistered): sort p, multiply by (m - rank), keep monotone
p = out.mcnemar_p.dropna().sort_values()
m, running, holm = len(p), 0.0, {}
for rank, (i, pv) in enumerate(p.items()):
    running = max(running, min(1.0, pv * (m - rank)))
    holm[i] = running
out["holm_p"] = pd.Series(holm)
out.to_csv("results/failure_a_summary.csv", index=False)
print(out.round(3).to_string(index=False))
