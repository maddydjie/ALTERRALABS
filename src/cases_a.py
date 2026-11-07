"""Pick the base MTSamples notes for Failure A (shared by the main and mechanism case builders)."""
import os
import random

import pandas as pd

from src.lexicon import canon_set
from src.parse import TOLERATED, find_allergy_span, is_positive


def load_bases(min_words=150, n_notes=200, seed=42):
    random.seed(seed)
    df = pd.read_csv("data/raw/mtsamples.csv").dropna(subset=["transcription"]).drop_duplicates("transcription")
    bases = []
    for idx, row in df.iterrows():
        note = row.transcription
        hit = find_allergy_span(note)
        if not hit:
            continue
        s, e, header, content = hit
        truth = canon_set(content)
        if TOLERATED.search(content):
            continue  # truth label would be ambiguous (found by hand audit, 2026-11-02)
        if not (is_positive(content) and truth and len(note.split()) >= min_words):
            continue
        bases.append({"parent_id": int(idx), "note": note, "span": [s, e], "header": header,
                      "content": content, "truth": sorted(truth)})
    random.shuffle(bases)
    return bases[:n_notes]
