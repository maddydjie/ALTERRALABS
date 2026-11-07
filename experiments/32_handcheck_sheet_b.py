"""Hand-check sheet for Failure B: 6 outputs per arm (3 listed, 3 not, where available) for YOU to label.
Fill grader_right (1/0): does listed_drug match what the model output actually says about the test drug?"""
import os

import pandas as pd

d = pd.read_csv("results/run_b_temporal_primary.csv")
parts = []
for arm, g in d.groupby("condition"):
    for flag in (1, 0):
        s = g[g.listed_drug == flag]
        parts.append(s.sample(min(len(s), 3), random_state=42))
s = pd.concat(parts)
# keep any labels already typed into an earlier copy of the sheet
old = {}
if os.path.exists("results/handcheck_b.csv"):
    old = pd.read_csv("results/handcheck_b.csv", dtype=str).fillna("").set_index("case_id").grader_right.to_dict()
s["grader_right"] = [old.get(i, "") for i in s.case_id]
s[["case_id", "condition", "drug", "listed_drug", "raw", "grader_right"]].to_csv("results/handcheck_b.csv", index=False)
print(len(s), "rows -> results/handcheck_b.csv")
