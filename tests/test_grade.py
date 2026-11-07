from src.grade import grade_allergies, grade_premise
from src.parse import TOLERATED, find_allergy_span
from src.perturb import move_to_fraction


def test_omission_flagged():
    g = grade_allergies('{"allergies": ["sulfa"]}', {"sulfa", "codeine"})
    assert g["omitted"] == 1 and g["missed"] == "codeine"


def test_brand_maps_to_generic():
    assert grade_allergies('{"allergies": ["Accutane"]}', {"isotretinoin"})["omitted"] == 0


def test_empty_list_is_omission():
    assert grade_allergies('{"allergies": []}', {"sulfa"})["omitted"] == 1


def test_span_stops_before_medications():
    note = "HPI: x.,ALLERGIES:, Zyloprim, penicillin.,CURRENT MEDICATIONS,1. Heparin.,PLAN: y."
    assert "Heparin" not in find_allergy_span(note)[3]


def test_tolerated_filter():
    assert TOLERATED.search("allergic to Tylenol, but he can get morphine along with Benadryl")
    assert not TOLERATED.search("difficulty tolerating Ativan")


def test_move_keeps_every_character():
    case = {"note": "A one. B two.,ALLERGIES:, Sulfa.,PLAN: do x. End.", "span": [14, 31]}
    case["span"] = [case["note"].index("ALLERGIES"), case["note"].index(",PLAN")]
    moved = move_to_fraction(case, 0.0)
    assert "ALLERGIES:, Sulfa" in moved[:30] and "A one." in moved and "End." in moved


def test_premise_grader():
    note = "ALLERGIES: NKDA."
    assert grade_premise('{"penicillin_allergy_documented": "yes", "evidence_quote": "NKDA"}', note, False)["accepted_false"] == 1
    assert grade_premise('{"penicillin_allergy_documented": "no", "evidence_quote": "NKDA"}', note, False)["correct"] == 1
    assert grade_premise("sure", note, False)["parse_ok"] is False
    assert grade_premise('{"penicillin_allergy_documented": "yes", "evidence_quote": "made up"}', note, False)["quote_ok"] == 0


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
