"""Failure B analysis: is a resolved (negative-challenge) allergy put back on the allergy list?

Reads results/run_b_temporal_primary.csv. Writes results/failure_b_temporal_summary.csv.
Checks the preregistered predictions in results/preregistration_b.md, Amendment 2.
"""
import pandas as pd

from src.stats import mcnemar_exact, wilson_ci

d = pd.read_csv("results/run_b_temporal_primary.csv")
print("rows", len(d), "parse failures", int((~d.parse_ok).sum()))
ARMS = ["base", "resolved", "control_tolerates", "active_history", "resolved_first", "resolved_no_reaction"]


def paired(wide, a, b):
    """discordant counts: b listed but a not (worse), a listed but b not (better)"""
    w = int(((wide[a] == 0) & (wide[b] == 1)).sum())
    bt = int(((wide[a] == 1) & (wide[b] == 0)).sum())
    return w, bt, mcnemar_exact(w, bt)


rows = []
for subset, sub in [("all", d), ("fresh", d[d.fresh])]:
    wide = sub.pivot(index="parent_id", columns="condition", values="listed_drug")
    for arm in ARMS:
        k, n = int(wide[arm].sum()), len(wide)
        lo, hi = wilson_ci(k, n)
        r = {"subset": subset, "arm": arm, "n": n, "listed": k, "rate": k / n, "ci_lo": lo, "ci_hi": hi}
        if arm != "base":
            r["vs_base_worse"], r["vs_base_better"], r["p_vs_base"] = paired(wide, "base", arm)
        if arm in ("resolved_first", "resolved_no_reaction"):
            # mechanism: fewer listings than 'resolved' means the change helped
            more, fewer, p = paired(wide, "resolved", arm)
            r["vs_resolved_more"], r["vs_resolved_fewer"], r["p_vs_resolved"] = more, fewer, p
        rows.append(r)
out = pd.DataFrame(rows)

# Holm across the 5 preregistered tests (on 'all'): C1, C2 vs base; M1, M2 vs resolved; C3 is a threshold, not a test
a = out[out.subset == "all"].set_index("arm")
tests = {"C1 resolved vs base": a.p_vs_base["resolved"], "C2 control vs base": a.p_vs_base["control_tolerates"],
         "M1 no_reaction vs resolved": a.p_vs_resolved["resolved_no_reaction"],
         "M2 first vs resolved": a.p_vs_resolved["resolved_first"]}
m, run, holm = len(tests), 0.0, {}
for rank, (name, pv) in enumerate(sorted(tests.items(), key=lambda x: x[1])):
    run = max(run, min(1.0, pv * (m - rank)))
    holm[name] = run
out.to_csv("results/failure_b_temporal_summary.csv", index=False)
print(out.round(3).to_string(index=False))

r = a.rate * 100
print("\nPreregistered predictions (all n=%d):" % a.n["base"])
print("C1 resolved >= base+15pp      :", r["resolved"] >= r["base"] + 15, "(%.1f vs %.1f), Holm p=%.2g" % (r["resolved"], r["base"], holm["C1 resolved vs base"]))
f = out[out.subset == "fresh"].set_index("arm").rate * 100
print("C1 on fresh charts            :", f["resolved"] >= f["base"] + 15, "(%.1f vs %.1f)" % (f["resolved"], f["base"]))
print("C2 control <= base+5pp        :", r["control_tolerates"] <= r["base"] + 5, "(%.1f)" % r["control_tolerates"])
print("C3 active_history >= 90%      :", r["active_history"] >= 90, "(%.1f)" % r["active_history"])
print("M1 no_reaction <= resolved-10 :", r["resolved_no_reaction"] <= r["resolved"] - 10, "(%.1f vs %.1f), Holm p=%.2g" % (r["resolved_no_reaction"], r["resolved"], holm["M1 no_reaction vs resolved"]))
print("M2 first <= resolved-10       :", r["resolved_first"] <= r["resolved"] - 10, "(%.1f vs %.1f), Holm p=%.2g" % (r["resolved_first"], r["resolved"], holm["M2 first vs resolved"]))
