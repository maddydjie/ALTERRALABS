"""Pick the conditions for the qwen3.5:9b comparison out of the existing case files (no new cases).

Writes data/cases/qwen_a.jsonl and data/cases/qwen_b.jsonl. See results/preregistration_qwen.md.
"""
import json

SUBSETS = [
    ("data/cases/failure_a.jsonl", "data/cases/qwen_a.jsonl", {"base", "pos0"}),
    ("data/cases/failure_b_temporal.jsonl", "data/cases/qwen_b.jsonl", {"base", "resolved", "active_history"}),
]

for src, dst, keep in SUBSETS:
    rows = [json.loads(l) for l in open(src)]
    rows = [r for r in rows if r["condition"] in keep]
    with open(dst, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(dst, len(rows))
