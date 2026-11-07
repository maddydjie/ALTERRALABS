"""Failure A mechanism: pos0 vs position sweep (pos5/10/25) and pos0_title, paired on the same notes.

Joins the mechanism run with base/pos0 from the main run. Checks the preregistered predictions
(results/preregistration.md, Amendment 2) and writes results/failure_a_mechanism.csv.
"""
import pandas as pd

from src.stats import mcnemar_exact, wilson_ci

main = pd.read_csv("results/run_a_primary.csv")
mech = pd.read_csv("results/run_a_mech_primary.csv")
d = pd.concat([main[main.condition.isin(["base", "pos0"])], mech])
wide = d.pivot(index="parent_id", columns="condition", values="omitted").dropna()

rows = []
for cond in ["base", "pos0", "pos5", "pos10", "pos25", "pos0_title"]:
    k, n = int(wide[cond].sum()), len(wide)
    lo, hi = wilson_ci(k, n)
    row = {"condition": cond, "n": n, "omitted": k, "rate": k / n, "ci_lo": lo, "ci_hi": hi}
    if cond != "base":
        w = int(((wide.base == 0) & (wide[cond] == 1)).sum())    # worse than base
        b = int(((wide.base == 1) & (wide[cond] == 0)).sum())    # better than base
        row.update({"vs_base_worse": w, "vs_base_better": b, "diff_vs_base_pp": 100 * (wide[cond].mean() - wide.base.mean()),
                    "p_vs_base": mcnemar_exact(w, b)})
    if cond not in ("base", "pos0"):
        w = int(((wide.pos0 == 0) & (wide[cond] == 1)).sum())
        b = int(((wide.pos0 == 1) & (wide[cond] == 0)).sum())
        row.update({"vs_pos0_worse": w, "vs_pos0_better": b, "diff_vs_pos0_pp": 100 * (wide[cond].mean() - wide.pos0.mean()),
                    "p_vs_pos0": mcnemar_exact(w, b)})
    rows.append(row)
out = pd.DataFrame(rows)
out.to_csv("results/failure_a_mechanism.csv", index=False)
print(out.round(3).to_string(index=False))

r = out.set_index("condition").rate * 100
base, pos0 = r["base"], r["pos0"]
print("\nPreregistered predictions:")
print("M1a pos10 <= pos0 - 8pp :", r["pos10"] <= pos0 - 8, "(%.1f vs %.1f)" % (r["pos10"], pos0))
print("M1b pos25 <= base + 5pp :", r["pos25"] <= base + 5, "(%.1f vs %.1f)" % (r["pos25"], base))
print("M2  pos0_title <= pos0 - 8pp:", r["pos0_title"] <= pos0 - 8, "(%.1f vs %.1f)" % (r["pos0_title"], pos0))
