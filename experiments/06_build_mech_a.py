"""Mechanism conditions for the pos0 failure: pos5/pos10/pos25 sweep and pos0_title. Same notes as 05."""
import json
import os

from src import perturb
from src.cases_a import load_bases

bases = load_bases(int(os.environ.get("MIN_WORDS", 150)), int(os.environ.get("N_NOTES", 200)))
conditions = {
    "pos5": lambda c: perturb.move_to_fraction(c, 0.05),
    "pos10": lambda c: perturb.move_to_fraction(c, 0.10),
    "pos25": lambda c: perturb.move_to_fraction(c, 0.25),
    "pos0_title": perturb.move_to_start_with_title,
}
n = 0
with open("data/cases/failure_a_mech.jsonl", "w") as f:
    for b in bases:
        for name, fn in conditions.items():
            f.write(json.dumps({"case_id": "%d_%s" % (b["parent_id"], name), "parent_id": b["parent_id"],
                                "condition": name, "source": "perturbed_real", "note": fn(b), "truth": b["truth"]}) + "\n")
            n += 1
print("mechanism cases written:", n)
