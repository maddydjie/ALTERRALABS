"""Failure B analysis: acceptance of a false penicillin-allergy premise, paired within chart.

Reads a run csv from src.run_b. Writes results/failure_b_summary.csv.
Usage: python experiments/21_failure_b.py [results/pilot_b_primary.csv]
Gate (preregistration_b.md): false-premise charts only where the model reads the chart correctly:
correct in P_neutral AND no penicillin listed in R.
"""
import sys

import pandas as pd

from src.stats import mcnemar_exact, wilson_ci

path = sys.argv[1] if len(sys.argv) > 1 else "results/pilot_b_primary.csv"
d = pd.read_csv(path)
print("rows", len(d), "unparseable", int((~d.parse_ok).sum()), "(%.1f%%)" % (100 * (~d.parse_ok).mean()))

false_d = d[~d.premise_true]
wide = false_d.pivot(index="parent_id", columns="arm", values="accepted_false")
strata = false_d.drop_duplicates("parent_id").set_index("parent_id").stratum

# reading gate: neutral question answered correctly ('no') and R lists no penicillin
gate = (wide.P_neutral == 0) & (wide.R == 0)
print("charts:", len(wide), "pass reading gate:", int(gate.sum()), "excluded:", int((~gate).sum()))
g = wide[gate]

rows = []
for arm in ["P_neutral", "P_false", "P_false_verify", "P_false_nochart"]:
    col = wide[arm] if arm == "P_false_nochart" else g[arm]   # no chart -> no gate possible
    k, n = int(col.sum()), int(col.notna().sum())
    lo, hi = wilson_ci(k, n)
    r = {"arm": arm, "n": n, "accepted_false": k, "rate": k / n, "ci_lo": lo, "ci_hi": hi}
    if arm in ("P_false", "P_false_verify"):
        w = int(((g.P_neutral == 0) & (g[arm] == 1)).sum())    # neutral ok, premise accepted
        b = int(((g.P_neutral == 1) & (g[arm] == 0)).sum())    # (0 by construction of the gate, kept for honesty)
        r.update({"worse_vs_neutral": w, "better_vs_neutral": b, "mcnemar_p": mcnemar_exact(w, b)})
    rows.append(r)
out = pd.DataFrame(rows)

# guard arm: true premise on penicillin-listed charts, should be answered 'yes'
t = d[d.premise_true]
guard = t.groupby("arm").correct.agg(["sum", "count"]).reset_index()
print("\nGuard (premise TRUE, correct = said yes):")
for r in guard.itertuples():
    lo, hi = wilson_ci(int(r.sum), int(r.count))
    print("  %-16s %d/%d = %.2f [%.2f, %.2f]" % (r.arm, r.sum, r.count, r.sum / r.count, lo, hi))

print("\nBy stratum (P_false acceptance, gated charts):")
for s, ids in g.groupby(strata.reindex(g.index)).groups.items():
    k, n = int(g.loc[ids, "P_false"].sum()), len(ids)
    print("  %-8s %d/%d" % (s, k, n))

print("\nVerbatim-quote check on 'yes' answers (fabricated quotes):")
y = false_d[(false_d.answer == "yes") & (false_d.arm != "R")]
print("  yes answers: %d, quote found in note: %d" % (len(y), int(pd.to_numeric(y.quote_ok, errors="coerce").sum())))
out.to_csv("results/failure_b_summary.csv", index=False)
print("\n", out.round(3).to_string(index=False))
