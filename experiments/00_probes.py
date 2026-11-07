"""Broad probes (negation, temporality) on real NKDA charts. Same extraction prompt as Failure A.

Base      : the real chart, allergy section says NKDA          -> correct output is an empty list
negation  : base + one sentence "She denies any allergy to <drug>."   -> correct output still empty
temporal  : base + one sentence "As a child she had a rash with <drug>; a negative challenge in 2019 showed she is no longer allergic."
            -> correct output still empty (resolved allergy is not an active allergy)
Outcome (false positive) = the model lists the named drug as an allergy.
Writes results/probes_cases.jsonl (cases, source labels) and results/probes_summary.csv.
Usage: python experiments/00_probes.py [n_charts]
"""
import json
import random
import re
import sys

import pandas as pd

from src.grade import parse_allergy_json
from src.lexicon import canon_set
from src.models import generate
from src.parse import find_allergy_span
from src.prompts import EXTRACT_ALLERGIES
from src.stats import mcnemar_exact, wilson_ci

N = int(sys.argv[1]) if len(sys.argv) > 1 else 60
random.seed(42)
DRUGS = ["penicillin", "sulfa", "codeine", "aspirin"]
BL = re.compile(r"penicillin|pcn|amoxi|augmentin|ampicillin|cephalo|keflex|cef|sulfa|bactrim|codeine|aspirin|asa\b", re.I)
NKDA = re.compile(r"\b(NKDA|NKA|no known (drug )?allergies|no known)\b", re.I)
SENTENCES = {
    "negation": "She denies any allergy to {d}.",
    "temporal": "As a child she had a rash with {d}; a negative challenge in 2019 showed she is no longer allergic.",
}


def insert_midnote(note, sentence):
    """Insert `sentence` at the sentence end nearest the middle of the note (rest byte-identical)."""
    cuts = [m.end() for m in re.finditer(r"\.[ ,]", note)]
    cut = min(cuts, key=lambda c: abs(c - len(note) // 2))
    return note[:cut] + " " + sentence + " " + note[cut:]


df = pd.read_csv("data/raw/mtsamples.csv").dropna(subset=["transcription"]).drop_duplicates("transcription")
charts = []
for idx, row in df.iterrows():
    n = row.transcription
    hit = find_allergy_span(n)
    if len(n.split()) >= 150 and hit and NKDA.search(hit[3]) and not canon_set(hit[3]) and not BL.search(n):
        charts.append((int(idx), n))
random.shuffle(charts)
charts = charts[:N]

cases = []
for i, (idx, note) in enumerate(charts):
    drug = DRUGS[i % len(DRUGS)]
    cases.append({"parent_id": idx, "probe": "base", "drug": drug, "source": "real", "note": note})
    for probe, s in SENTENCES.items():
        cases.append({"parent_id": idx, "probe": probe, "drug": drug, "source": "perturbed_real",
                      "note": insert_midnote(note, s.format(d=drug))})
with open("results/probes_cases.jsonl", "w") as f:
    for c in cases:
        f.write(json.dumps({k: c[k] for k in ("parent_id", "probe", "drug", "source")}) + "\n")  # no note text: re-derivable

rows = []
for c in cases:
    raw = generate(EXTRACT_ALLERGIES.format(note=c["note"]))
    items, ok = parse_allergy_json(raw)
    listed = int(any(c["drug"] in canon_set(x) for x in items))
    rows.append({"parent_id": c["parent_id"], "probe": c["probe"], "drug": c["drug"], "parse_ok": ok,
                 "false_positive": listed, "any_item": int(len(items) > 0), "raw": raw.replace("\n", " ")[:200]})
d = pd.DataFrame(rows)
d.to_csv("results/probes_raw.csv", index=False)

wide = d.pivot(index="parent_id", columns="probe", values="false_positive")
out = []
for probe in ["base", "negation", "temporal"]:
    k, n = int(wide[probe].sum()), len(wide)
    lo, hi = wilson_ci(k, n)
    r = {"probe": probe, "n": n, "false_positive": k, "rate": k / n, "ci_lo": lo, "ci_hi": hi}
    if probe != "base":
        w = int(((wide.base == 0) & (wide[probe] == 1)).sum())
        b = int(((wide.base == 1) & (wide[probe] == 0)).sum())
        r.update({"worse": w, "better": b, "mcnemar_p": mcnemar_exact(w, b)})
    out.append(r)
out = pd.DataFrame(out)
out.to_csv("results/probes_summary.csv", index=False)
print(out.round(3).to_string(index=False))
