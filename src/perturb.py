"""Perturbation generators. Each takes a case dict and returns the new note text.
Everything except the one intended change stays byte-identical.
"""
import re
from src.lexicon import ABBREV, DRUGS


def _split(case):
    n = case["note"]
    s, e = case["span"]
    return n[:s], n[s:e], n[e:]  # before, allergy span (header+content), after


def baseline(case):
    return case["note"]


def control_header_case(case):
    """CONTROL: 'ALLERGIES:' -> 'Allergies:' in place. Clinically irrelevant, should not change output."""
    before, span, after = _split(case)
    return before + span.replace(case["header"], case["header"].title(), 1) + after


def move_to_fraction(case, frac):
    """Move the identical allergy span (header + content) to `frac` of the way through the note.

    frac=0 -> very start, 1 -> very end. We snap to the nearest sentence end (". " or ".,")
    so we never cut a word in half. The rest of the note is unchanged.
    """
    before, span, after = _split(case)
    rest = before + after
    target = int(frac * len(rest))
    # candidate cut points = just after a sentence end
    cuts = [0] + [m.end() for m in re.finditer(r"\.[ ,]", rest)] + [len(rest)]
    cut = min(cuts, key=lambda c: abs(c - target))
    sep = " " if cut > 0 else ""
    return rest[:cut] + sep + span.strip(" ,") + (", " if cut < len(rest) else "") + rest[cut:]


def as_hpi_sentence(case):
    """Same drug facts, but as a free-text sentence mid-note with no 'ALLERGIES:' header."""
    before, span, after = _split(case)
    rest = before + after
    sentence = "The patient has a known allergy to %s." % case["content"].strip(" ,.").lower()
    cuts = [m.end() for m in re.finditer(r"\.[ ,]", rest)] or [0]
    cut = min(cuts, key=lambda c: abs(c - len(rest) // 2))
    return rest[:cut] + " " + sentence + " " + rest[cut:]


def swap_abbrev(case):
    """Replace a generic drug name inside the allergy content with its abbreviation/brand.
    Returns None if the case has no drug we have an abbreviation for."""
    before, span, after = _split(case)
    for canon, abbr in ABBREV.items():
        plain = DRUGS[canon][0]
        whole = r"(?<![a-z])" + re.escape(plain) + r"(?![a-z])"  # whole word only: "SULFAS" must not become "BactrimS"
        if re.search(whole, span, re.I):
            return before + re.sub(whole, abbr, span, count=1, flags=re.I) + after
    return None


def move_to_start_with_title(case, title="CLINICAL NOTE:,"):
    """MECHANISM TEST: pos0 plus a neutral one-line title before the allergy section.
    Tests whether pos0 fails because the note opens abnormally (no preamble) rather than because of position."""
    return title + " " + move_to_fraction(case, 0.0)


def insert_midnote(note, sentence):
    """Insert `sentence` at the sentence end nearest the middle of the note; the rest stays byte-identical."""
    cuts = [m.end() for m in re.finditer(r"\.[ ,]", note)]
    cut = min(cuts, key=lambda c: abs(c - len(note) // 2))
    return note[:cut] + " " + sentence + " " + note[cut:]
