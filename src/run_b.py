"""Run Failure-B cases (data/cases/failure_b.jsonl) through a model, grade, write a csv."""
import csv
import json
import sys
import time

from src.grade import grade_premise, parse_allergy_json
from src.lexicon import canon_set
from src.models import generate


def run_failure_b(case_file, out_csv, model_key="primary", limit=None):
    rows = [json.loads(l) for l in open(case_file)]
    if limit:
        rows = rows[:limit]
    out, t0 = [], time.time()
    for i, c in enumerate(rows):
        raw = generate(c["prompt"], model_key=model_key)
        base = {"case_id": c["case_id"], "parent_id": c["parent_id"], "arm": c["arm"], "stratum": c["stratum"],
                "premise_true": c["premise_true"], "source": c["source"], "model": model_key}
        if c["arm"] == "R":
            # reading control: does the model's allergy list wrongly contain a penicillin-class drug?
            items, ok = parse_allergy_json(raw)
            listed_pcn = int(any("penicillin" in canon_set(x) for x in items))
            g = {"parse_ok": ok, "answer": "listed_pcn" if listed_pcn else "no_pcn",
                 "correct": int(ok and not listed_pcn), "accepted_false": listed_pcn, "quote": "", "quote_ok": "", "quote_supports": ""}
        else:
            note = c["prompt"].split("NOTE:\n", 1)[-1].split("\n\nQUESTION:", 1)[0] if "NOTE:" in c["prompt"] else ""
            g = grade_premise(raw, note, c["premise_true"])
        out.append({**base, **g, "raw": raw.replace("\n", " ")[:300]})
        if i % 20 == 0:
            print(i, len(rows), "%.0fs" % (time.time() - t0), flush=True)
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    return out


if __name__ == "__main__":
    # usage: python -m src.run_b CASES.jsonl OUT.csv [primary|comparison] [limit]
    key = sys.argv[3] if len(sys.argv) > 3 else "primary"
    lim = int(sys.argv[4]) if len(sys.argv) > 4 else None
    run_failure_b(sys.argv[1], sys.argv[2], model_key=key, limit=lim)
