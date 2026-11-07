"""Run a jsonl case file through a model, grade, and write a csv (one row per case)."""
import csv
import json
import sys
import time

from src.grade import grade_allergies, parse_allergy_json
from src.lexicon import canon_set
from src.models import generate
from src.prompts import EXTRACT_ALLERGIES


def run_failure_a(case_file, out_csv, model_key="primary", limit=None):
    rows = [json.loads(l) for l in open(case_file)]
    if limit:
        rows = rows[:limit]
    out = []
    t0 = time.time()
    for i, c in enumerate(rows):
        raw = generate(EXTRACT_ALLERGIES.format(note=c["note"]), model_key=model_key)
        g = grade_allergies(raw, set(c["truth"]))
        if "drug" in c:  # Failure B (temporal): was the inserted test drug put on the allergy list?
            items, _ = parse_allergy_json(raw)
            g["drug"] = c["drug"]
            g["fresh"] = c["fresh"]
            g["listed_drug"] = int(any(c["drug"] in canon_set(x) for x in items))
        out.append({"case_id": c["case_id"], "parent_id": c["parent_id"], "condition": c["condition"],
                    "source": c["source"], "model": model_key, "truth": ";".join(c["truth"]), **g,
                    "raw": raw.replace("\n", " ")[:300]})
        if i % 20 == 0:
            print(i, len(rows), "%.0fs" % (time.time() - t0), flush=True)
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    return out


if __name__ == "__main__":
    # usage: python -m src.run CASES.jsonl OUT.csv [primary|comparison] [limit]
    key = sys.argv[3] if len(sys.argv) > 3 else "primary"
    lim = int(sys.argv[4]) if len(sys.argv) > 4 else None
    run_failure_a(sys.argv[1], sys.argv[2], model_key=key, limit=lim)
