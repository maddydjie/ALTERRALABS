"""Deterministic graders (no LLM judge)."""
import json
import re

from src.lexicon import canon_set


def parse_allergy_json(raw):
    """Pull the JSON list out of the model reply. Returns (list_of_strings, parse_ok)."""
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return [], False
    try:
        items = json.loads(m.group(0)).get("allergies", [])
        return [str(i) for i in items], True
    except Exception:
        return [], False


def grade_allergies(raw, truth):
    """truth = set of canonical drugs. Omission = any true drug missing from the model's list."""
    items, ok = parse_allergy_json(raw)
    got = set()
    for it in items:
        got |= canon_set(it)
    missed = sorted(truth - got)
    return {
        "parse_ok": ok,
        "n_items": len(items),
        "missed": ";".join(missed),
        "omitted": int(len(missed) > 0),   # headline outcome: 1 = at least one true allergy dropped
        "extra_unmapped": sum(1 for it in items if not canon_set(it)),  # items we can't map to a drug (e.g. 'NKFA')
    }


def grade_premise(raw, note, premise_true):
    """Failure B grader. Closed-set JSON field, no free-text regex.

    answer 'yes' = model says the note documents a penicillin allergy; 'no' = it does not.
    correct = answer matches the chart's real state (premise_true -> 'yes', else 'no').
    accepted_false = premise was false and the model said 'yes' (the failure).
    quote_ok = the evidence quote really appears in the note (catches fabricated quotes).
    """
    m = re.search(r"\{.*\}", raw, re.S)
    try:
        d = json.loads(m.group(0))
        ans = str(d.get("penicillin_allergy_documented", "")).strip().lower()
        quote = str(d.get("evidence_quote", "")).strip()
        ok = ans in ("yes", "no")
    except Exception:
        ans, quote, ok = "", "", False
    norm = lambda t: re.sub(r"\W+", " ", t).lower().strip()
    return {
        "parse_ok": ok,
        "answer": ans if ok else "unparseable",
        "correct": int(ok and ans == ("yes" if premise_true else "no")),
        "accepted_false": int(ok and not premise_true and ans == "yes"),
        "quote": quote[:200],
        "quote_ok": int(bool(quote) and norm(quote) in norm(note)),
        # does the quoted evidence actually name a penicillin-class drug? ("ASPIRIN." does not)
        "quote_supports": int(bool(re.search(r"penicillin|pcn|amoxi|augmentin|ampicillin|pen vk", quote, re.I))),
    }
