"""Find the allergy section inside an MTSamples note.

MTSamples sections are inline and comma-delimited, e.g.
  "...,ALLERGIES:,  Penicillin.,MEDICATIONS:,  ..."
so a section runs from its header up to the next ",UPPERCASE HEADER:".
"""
import re

SECTION = re.compile(
    r"(?:^|,)\s*((?:MEDICATION |DRUG )?ALLERG(?:Y|IES))\s*:,?(.*?)(?=,[A-Z][A-Z /&\-]{3,}:|,(?:CURRENT |HOME )?MEDICATIONS?\b|,REVIEW OF SYSTEMS|,PHYSICAL EXAM|,FAMILY HISTORY|$)", re.S
)
# sections that say "no allergy" or are unusable -> not a positive drug allergy
NEGATIVE = re.compile(r"NKDA|NKA|no known|none|denie|not allergic|no allerg|no medication|no drug|unknown|refer to chart", re.I)


# a drug named as tolerated is NOT an allergy ("he can get morphine along with Benadryl")
TOLERATED = re.compile(r"\bcan (?:get|take|tolerate|have)\b|\btolerates\b|\bno problem", re.I)


def find_allergy_span(note):
    """Return (start, end, header, content) of the allergy section, or None."""
    m = SECTION.search(note)
    if not m:
        return None
    # start at the header itself (skip the leading comma/space the regex may have eaten)
    start = m.start(1)
    return start, m.end(), m.group(1), m.group(2)


def is_positive(content):
    return bool(content.strip(" ,.*")) and not NEGATIVE.search(content)
