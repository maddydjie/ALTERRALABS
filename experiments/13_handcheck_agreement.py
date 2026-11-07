"""Agreement between the grader and Madhavi's hand labels, with Wilson 95% CIs.

Reads the filled sheets (results/handcheck_a.csv, results/handcheck_b.csv), plus
results/handcheck_a_firstpass.csv: sheet A before 3 labels were revised on second review.
Writes results/handcheck_agreement.csv. Stops if any label is blank or not 1/0.
"""
import pandas as pd

from src.stats import wilson_ci

rows = []
for name in ["a_firstpass", "a", "b"]:
    sheet = pd.read_csv(f"results/handcheck_{name}.csv", dtype=str)
    labels = sheet.grader_right.fillna("").str.strip()
    bad = sheet[~labels.isin(["0", "1"])]
    if len(bad):
        raise SystemExit(f"handcheck_{name}: invalid labels in {bad.case_id.tolist()}")
    k, n = int((labels == "1").sum()), len(sheet)
    lo, hi = wilson_ci(k, n)
    rows.append({
        "sheet": f"handcheck_{name}",
        "agree": k,
        "n": n,
        "rate": round(k / n, 4),
        "ci_lo": round(lo, 4),
        "ci_hi": round(hi, 4),
        "disagree_case_ids": ";".join(sheet[labels == "0"].case_id),
    })

out = pd.DataFrame(rows)
out.to_csv("results/handcheck_agreement.csv", index=False)
print(out.to_string(index=False))
