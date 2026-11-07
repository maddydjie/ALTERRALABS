"""Make a hand-check sheet: a stratified random sample of raw outputs for YOU to label.

Columns you fill: my_missed (drugs in the allergy section that the output left out, or blank),
grader_right (1/0: does the grader's omitted flag match what you see in the note).
Usage: python experiments/12_handcheck_sheet.py [results/run_a_primary.csv] [n_per_condition]
"""
import json
import os
import sys

import pandas as pd

from src.parse import find_allergy_span

path = sys.argv[1] if len(sys.argv) > 1 else "results/run_a_primary.csv"
k = int(sys.argv[2]) if len(sys.argv) > 2 else 6
d = pd.read_csv(path)
notes = {}
for line in open("data/cases/failure_a.jsonl"):
    c = json.loads(line)
    notes[c["case_id"]] = c["note"]

# sample k per condition, half from omitted=1 and half from omitted=0, so errors in both directions get checked
parts = []
for cond, g in d.groupby("condition"):
    for flag in (1, 0):
        s = g[g.omitted == flag]
        parts.append(s.sample(min(len(s), k // 2), random_state=42))
s = pd.concat(parts)


def allergy_text(case_id):
    """The allergy text as the model saw it.

    The section regex misses it when the header is title-cased (ctrl_header_case), removed (hpi_sentence)
    or moved to where its end isn't matched (some pos50/pos100). All of these carry the base note's
    allergy content unchanged, so fall back to the base note's section.
    """
    span = find_allergy_span(notes[case_id])
    if span is not None:
        return span[3].strip()[:300]
    pid, cond = case_id.split("_", 1)
    content = find_allergy_span(notes[pid + "_base"])[3]
    if cond == "hpi_sentence":  # same wording as src/perturb.py::as_hpi_sentence
        return ("[sentence] The patient has a known allergy to %s." % content.strip(" ,.").lower())[:300]
    return content.strip()[:300]


s["allergy_section"] = [allergy_text(i) for i in s.case_id]
# keep any labels already typed into an earlier copy of the sheet
old = {}
if os.path.exists("results/handcheck_a.csv"):
    old = pd.read_csv("results/handcheck_a.csv", dtype=str).fillna("").set_index("case_id").to_dict("index")
s["my_missed"] = [old.get(i, {}).get("my_missed", "") for i in s.case_id]
s["grader_right"] = [old.get(i, {}).get("grader_right", "") for i in s.case_id]
s[["case_id", "condition", "truth", "omitted", "missed", "raw", "allergy_section", "my_missed", "grader_right"]].to_csv(
    "results/handcheck_a.csv", index=False)
print(len(s), "rows -> results/handcheck_a.csv")
