"""Build Failure-B cases: same real chart, different question (premise) per arm.

Strata (chosen from the chart's own allergy section):
  nkda      - chart says NKDA, no beta-lactam mentioned anywhere   -> premise 'penicillin allergy' is FALSE
  other     - chart lists non-penicillin drugs, no beta-lactam anywhere -> premise FALSE
  penicillin- chart lists penicillin                                 -> premise TRUE (guard arm T)
Env: N_PER_STRATUM (default 20 for the pilot; 100+ for the headline run).
"""
import json
import os
import random
import re

import pandas as pd

from src.lexicon import canon_set
from src.parse import TOLERATED, find_allergy_span
from src.prompts import B_PROMPT, B_PROMPT_NO_CHART, B_QUESTIONS

random.seed(42)
N = int(os.environ.get("N_PER_STRATUM", 20))
BL = re.compile(r"penicillin|pcn|amoxi|augmentin|ampicillin|cephalo|keflex|cef|beta.?lactam|pen vk|unasyn|zosyn|pip", re.I)
NKDA = re.compile(r"\b(NKDA|NKA|no known (drug )?allergies|no known)\b", re.I)

df = pd.read_csv("data/raw/mtsamples.csv").dropna(subset=["transcription"]).drop_duplicates("transcription")
pools = {"nkda": [], "other": [], "penicillin": []}
for idx, row in df.iterrows():
    note = row.transcription
    hit = find_allergy_span(note)
    if len(note.split()) < 150 or not hit or TOLERATED.search(hit[3]):
        continue
    truth = canon_set(hit[3])
    if "penicillin" in truth:
        pools["penicillin"].append((idx, note))
    elif BL.search(note):
        continue  # beta-lactam talk elsewhere would make "false premise" ambiguous
    elif NKDA.search(hit[3]) and not truth:
        pools["nkda"].append((idx, note))
    elif truth:
        pools["other"].append((idx, note))

# arms per stratum: false-premise strata get all arms; penicillin stratum gets the true-premise guard arms
ARMS = {"nkda": ["R", "P_neutral", "P_false", "P_false_verify", "P_false_nochart"],
        "other": ["R", "P_neutral", "P_false", "P_false_verify", "P_false_nochart"],
        "penicillin": ["P_neutral", "P_false", "P_false_verify"]}   # premise is TRUE here (guard arm T)
n = 0
with open("data/cases/failure_b.jsonl", "w") as f:
    for stratum, pool in pools.items():
        random.shuffle(pool)
        for idx, note in pool[:N]:
            for arm in ARMS[stratum]:
                if arm == "P_false_nochart":
                    prompt = B_PROMPT_NO_CHART.format(question=B_QUESTIONS["P_false"])
                    source = "perturbed_real"   # real parent chart removed entirely
                else:
                    prompt = B_PROMPT.format(note=note, question=B_QUESTIONS[arm])
                    source = "real"             # note text untouched, only the question differs
                f.write(json.dumps({"case_id": "%d_%s" % (idx, arm), "parent_id": int(idx), "arm": arm,
                                    "stratum": stratum, "premise_true": stratum == "penicillin",
                                    "source": source, "prompt": prompt}) + "\n")
                n += 1
print({k: len(v) for k, v in pools.items()}, "cases written:", n)
