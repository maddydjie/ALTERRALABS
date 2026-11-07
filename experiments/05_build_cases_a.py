"""Build Failure-A test cases from MTSamples: one jsonl row per (note, condition)."""
import json
import os

from src import perturb

from src.cases_a import load_bases

bases = load_bases(int(os.environ.get("MIN_WORDS", 150)), int(os.environ.get("N_NOTES", 200)))
print("usable base notes:", len(bases))

conditions = {
    "base": perturb.baseline,
    "ctrl_header_case": perturb.control_header_case,
    "pos0": lambda c: perturb.move_to_fraction(c, 0.0),
    "pos50": lambda c: perturb.move_to_fraction(c, 0.5),
    "pos100": lambda c: perturb.move_to_fraction(c, 1.0),
    "hpi_sentence": perturb.as_hpi_sentence,
    "abbrev": perturb.swap_abbrev,   # None for notes without an abbreviable drug
}
os.makedirs("data/cases", exist_ok=True)
n = 0
with open("data/cases/failure_a.jsonl", "w") as f:
    for b in bases:
        for name, fn in conditions.items():
            text = fn(b)
            if text is None:
                continue
            # base/control keep the real text; moved/rewritten versions are perturbed real notes
            src = "real" if name == "base" else "perturbed_real"
            f.write(json.dumps({"case_id": "%d_%s" % (b["parent_id"], name), "parent_id": b["parent_id"],
                                "condition": name, "source": src, "note": text, "truth": b["truth"]}) + "\n")
            n += 1
print("cases written:", n)
