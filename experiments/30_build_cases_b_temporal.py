"""Failure B (resolved allergy re-listed): build paired cases on real NKDA charts.

Each chart gets one test drug it never mentions; one sentence about that drug is inserted mid-note.
Design and predictions: results/preregistration_b.md, Amendment 2. Writes data/cases/failure_b_temporal.jsonl.
"""
import json
import random
import re

import pandas as pd

from src.lexicon import canon_set
from src.parse import find_allergy_span
from src.perturb import insert_midnote

random.seed(42)
N_TOTAL = 116
DRUGS = ["penicillin", "sulfa", "codeine", "aspirin"]
NKDA = re.compile(r"\b(NKDA|NKA|no known (drug )?allergies|no known)\b", re.I)
SENTENCES = {
    "base": None,
    "resolved": "The patient had a rash with {d} as a child; a negative challenge in 2019 showed the patient is no longer allergic to it.",
    "control_tolerates": "The patient takes {d} regularly without any problems.",
    "active_history": "The patient had a rash with {d} as a child.",
    "resolved_first": "A negative challenge in 2019 showed the patient is not allergic to {d}, despite a rash with it as a child.",
    "resolved_no_reaction": "A negative challenge to {d} in 2019 showed the patient is not allergic to it.",
}
used_in_probe = {json.loads(l)["parent_id"] for l in open("results/probes_cases.jsonl")}

df = pd.read_csv("data/raw/mtsamples.csv").dropna(subset=["transcription"]).drop_duplicates("transcription")
fresh, old = [], []
for idx, row in df.iterrows():
    note = row.transcription
    hit = find_allergy_span(note)
    if len(note.split()) < 150 or not hit or not NKDA.search(hit[3]) or canon_set(hit[3]):
        continue
    options = [d for d in DRUGS if d not in canon_set(note)]   # never insert a drug the note already mentions
    if options:
        (old if int(idx) in used_in_probe else fresh).append((int(idx), note, options))
random.shuffle(fresh)
random.shuffle(old)
charts = [(c, True) for c in fresh] + [(c, False) for c in old]
charts = charts[:N_TOTAL]

n = 0
with open("data/cases/failure_b_temporal.jsonl", "w") as f:
    for i, ((idx, note, options), is_fresh) in enumerate(charts):
        drug = options[i % len(options)]
        for arm, s in SENTENCES.items():
            text = note if s is None else insert_midnote(note, s.format(d=drug))
            f.write(json.dumps({"case_id": "%d_%s" % (idx, arm), "parent_id": idx, "condition": arm, "drug": drug,
                                "fresh": is_fresh, "source": "real" if s is None else "perturbed_real",
                                "note": text, "truth": [drug] if arm == "active_history" else []}) + "\n")
            n += 1
print("charts", len(charts), "fresh", sum(f for _, f in charts), "cases", n)
