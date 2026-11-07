"""Small drug lexicon: canonical name -> surface forms found in notes (lowercase).

Used for (1) ground truth: which drugs does the note's allergy section name?
(2) grading: map whatever the model returns back to a canonical drug.
First form in each list is the plain generic name; `ABBREV` gives a swap-in
form for the abbreviation/brand perturbation.
"""
import re

DRUGS = {
    "penicillin": ["penicillin", "penicillins", "pcn", "pen vk", "pen-vk"],
    "amoxicillin": ["amoxicillin", "amoxil", "augmentin", "amoxicillin-clavulanate"],
    "ampicillin": ["ampicillin"],
    "cephalosporin": ["cephalosporin", "cephalosporins", "keflex", "cephalexin", "cefzil", "cefaclor", "ceftin", "cefuroxime", "ancef", "cefazolin"],
    "sulfa": ["sulfa", "sulfonamide", "sulfonamides", "bactrim", "septra", "sulfamethoxazole"],
    "codeine": ["codeine"],
    "morphine": ["morphine"],
    "meperidine": ["meperidine", "demerol"],
    "hydrocodone": ["hydrocodone", "vicodin", "norco"],
    "oxycodone": ["oxycodone", "percocet", "oxycontin"],
    "aspirin": ["aspirin", "asa"],
    "nsaid": ["nsaid", "nsaids", "ibuprofen", "motrin", "advil", "naproxen", "naprosyn", "toradol", "ketorolac"],
    "erythromycin": ["erythromycin"],
    "tetracycline": ["tetracycline", "doxycycline"],
    "ciprofloxacin": ["ciprofloxacin", "cipro", "levaquin", "levofloxacin", "quinolone", "quinolones"],
    "vancomycin": ["vancomycin"],
    "gentamicin": ["gentamicin", "garamycin"],
    "clindamycin": ["clindamycin", "cleocin"],
    "iodine": ["iodine", "betadine", "contrast dye", "iodinated contrast"],
    "latex": ["latex"],
    "acetaminophen": ["acetaminophen", "tylenol"],
    "lisinopril": ["lisinopril", "ace inhibitor", "ace inhibitors"],
    "phenytoin": ["phenytoin", "dilantin"],
    "carbamazepine": ["carbamazepine", "tegretol"],
    "isotretinoin": ["isotretinoin", "accutane"],
    "metoclopramide": ["metoclopramide", "reglan"],
    "promethazine": ["promethazine", "phenergan"],
    "tramadol": ["tramadol", "ultram"],
    "lidocaine": ["lidocaine", "xylocaine"],
    "allopurinol": ["allopurinol", "zyloprim"],
    "heparin": ["heparin"],
    "metronidazole": ["metronidazole", "flagyl"],
    "prochlorperazine": ["prochlorperazine", "compazine"],
    "diphenhydramine": ["diphenhydramine", "benadryl"],
    "azathioprine": ["azathioprine", "imuran"],
    "nabumetone": ["relafen", "nabumetone"],
    "lorazepam": ["lorazepam", "ativan"],
    "diazepam": ["diazepam", "valium"],
    "ceftriaxone": ["ceftriaxone", "rocephin"],
    "statin": ["lipitor", "zocor", "simvastatin", "atorvastatin"],
}

# surface form -> canonical; longest forms first so "augmentin" beats "asa" inside words etc.
_FORMS = sorted(((f, c) for c, fs in DRUGS.items() for f in fs), key=lambda x: -len(x[0]))
_RE = re.compile(r"(?<![a-z])(" + "|".join(re.escape(f) for f, _ in _FORMS) + r")(?![a-z])", re.I)
_TO_CANON = dict(_FORMS)


def canon_set(text):
    """Set of canonical drugs mentioned anywhere in `text`."""
    return {_TO_CANON[m.group(1).lower()] for m in _RE.finditer(text)}


# Perturbation targets: plain generic -> abbreviation/brand the note could have used instead.
ABBREV = {
    "penicillin": "PCN",
    "aspirin": "ASA",
    "sulfa": "Bactrim",
    "meperidine": "Demerol",
    "amoxicillin": "Augmentin",
    "acetaminophen": "Tylenol",
}
