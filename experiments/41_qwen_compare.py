"""MedGemma-4B vs qwen3.5:9b on the same cases (results/preregistration_qwen.md).

Reads the medgemma runs (run_a_primary.csv, run_b_temporal_primary.csv) and the qwen runs
(run_a_qwen.csv, run_b_qwen.csv). Writes results/qwen_compare.csv.
Outcome per case: A = omitted (1 = dropped a documented allergy), B = listed_drug (1 = test drug put on list).
"""
import pandas as pd

from src.stats import mcnemar_exact, wilson_ci

TASKS = [
    ("A", "omitted", "results/run_a_primary.csv", "results/run_a_qwen.csv", ["base", "pos0"]),
    ("B", "listed_drug", "results/run_b_temporal_primary.csv", "results/run_b_qwen.csv",
     ["base", "resolved", "active_history"]),
]

rows = []
for task, outcome, med_csv, qwen_csv, conds in TASKS:
    med, qw = pd.read_csv(med_csv), pd.read_csv(qwen_csv)
    print(task, "qwen parse failures:", int((~qw.parse_ok).sum()), "of", len(qw))
    # one row per (parent_id, condition), one column per model
    m = med[med.condition.isin(conds)].set_index(["parent_id", "condition"])[outcome].rename("medgemma")
    q = qw.set_index(["parent_id", "condition"])[outcome].rename("qwen")
    both = pd.concat([m, q], axis=1).dropna()
    for cond in conds:
        sub = both.xs(cond, level="condition")
        n = len(sub)
        r = {"task": task, "condition": cond, "n": n}
        for model in ["medgemma", "qwen"]:
            k = int(sub[model].sum())
            lo, hi = wilson_ci(k, n)
            r.update({model + "_k": k, model + "_rate": k / n, model + "_lo": lo, model + "_hi": hi})
        # across models, same case: medgemma wrong & qwen right vs qwen wrong & medgemma right
        r["med_only"] = int(((sub.medgemma == 1) & (sub.qwen == 0)).sum())
        r["qwen_only"] = int(((sub.medgemma == 0) & (sub.qwen == 1)).sum())
        r["p_models"] = mcnemar_exact(r["med_only"], r["qwen_only"])
        if cond != "base":
            # within qwen, paired vs its own base (same test as the medgemma headline)
            wide = sub.join(both.xs("base", level="condition").qwen.rename("qwen_base"))
            r["qwen_worse"] = int(((wide.qwen_base == 0) & (wide.qwen == 1)).sum())
            r["qwen_better"] = int(((wide.qwen_base == 1) & (wide.qwen == 0)).sum())
            r["qwen_p_vs_base"] = mcnemar_exact(r["qwen_worse"], r["qwen_better"])
        rows.append(r)

out = pd.DataFrame(rows)
out.to_csv("results/qwen_compare.csv", index=False)
print(out.round(3).to_string(index=False))

a = out.set_index(["task", "condition"])
pct = lambda t, c, mdl: 100 * a.loc[(t, c), mdl + "_rate"]
print("\nPreregistered predictions:")
print("Q1 qwen pos0 < medgemma pos0  :", pct("A", "pos0", "qwen") < pct("A", "pos0", "medgemma"),
      "(%.1f vs %.1f, p=%.2g)" % (pct("A", "pos0", "qwen"), pct("A", "pos0", "medgemma"), a.loc[("A", "pos0"), "p_models"]))
print("   qwen pos0 >= base+10pp     :", pct("A", "pos0", "qwen") >= pct("A", "base", "qwen") + 10)
print("Q2 qwen resolved < medgemma   :", pct("B", "resolved", "qwen") < pct("B", "resolved", "medgemma"),
      "(%.1f vs %.1f, p=%.2g)" % (pct("B", "resolved", "qwen"), pct("B", "resolved", "medgemma"), a.loc[("B", "resolved"), "p_models"]))
print("Q3 guard qwen vs medgemma     : %.1f vs %.1f, p=%.2g" % (pct("B", "active_history", "qwen"),
      pct("B", "active_history", "medgemma"), a.loc[("B", "active_history"), "p_models"]))
print("base A qwen <= 5%             :", pct("A", "base", "qwen") <= 5, "(%.1f)" % pct("A", "base", "qwen"))
print("base B qwen <= 5%             :", pct("B", "base", "qwen") <= 5, "(%.1f)" % pct("B", "base", "qwen"))
