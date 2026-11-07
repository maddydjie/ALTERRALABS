# Preregistration (written 2026-10-21, BEFORE any full run)

Pilot seen so far: 12 cases from 2 notes, 0 omissions (results/pilot_a.csv). Nothing else has been run.
Model: medgemma:4b (Ollama, Q4_K_M, digest 9fe4e9a6c9bd), temperature 0, seed 42.
Data: 120 MTSamples notes (>=150 words, explicit ALLERGIES section naming a drug in src/lexicon.py).

## Failure A: allergy omission
Outcome: `omitted` = 1 if any true allergy (per lexicon on the original allergy section) is missing from the model's list.
Conditions (paired within note): base | ctrl_header_case | pos0 | pos50 | pos100 | hpi_sentence | abbrev (subset).

Predictions:
- P1 (control): ctrl_header_case vs base differ by <=2 discordant notes. If larger, the model is generally fragile and the A effects are not specific.
- P2 (section vs position): hpi_sentence (no header) omits MORE than base. I expect the header to act as a retrieval cue.
- P3 (position): pos50 omits more than pos0 and pos100 (lost-in-the-middle, Liu et al. 2023). I am LESS sure of this: notes are short (150-1000 words), so I expect a weak or null position effect.
- P4 (abbreviation): abbrev omits more than base for PCN/ASA/Bactrim-type swaps.
- Null result is acceptable and will be reported as such.

Decision rule for "failure": omission rate in a perturbed condition >= 10 percentage points above base, with the paired exact McNemar p < 0.05 after Holm correction across the 5 perturbed conditions.
Mechanism test (if a failure is found): padding the note to ~4k tokens with irrelevant real-note text; if the effect is position/length-driven omission should rise with padding, if header-driven it should not.

## Failure B (false premise, chart-contradicted): design only, to be preregistered separately before running.

## Probe accounting
All probes (including clean ones) go in results/probe_log.csv.

## Amendment 1 (2026-11-02, after 200-case sanity run, BEFORE the full run)
What I had seen: sanity run on 31 notes (results/sanity_a_primary.csv): pos0 omitted 5/30 vs base 0/30; ctrl, pos50, pos100, hpi_sentence all 0/30. P3 (pos50 worst) looks wrong; pos0 looks worst. Not changing the predictions above, just recording them as seen to be wrong at the extreme.
Label fixes found by hand-auditing all 120 allergy sections:
- note 3121 dropped: "can get morphine along with Benadryl" = tolerated, truth ambiguous (new TOLERATED filter in src/parse.py).
- allergy-span regex now stops at "CURRENT MEDICATIONS," / ROS / PHYSICAL EXAM / FAMILY HISTORY without a colon. Before, notes 3437 and 1867 leaked medication-list drugs (lisinopril, heparin, baby aspirin) into truth and into the moved span.
- Result: 119 notes, 792 cases (was 120/799). Case order changed; old cache still valid (keyed by prompt).
Added prediction P5 (written before the full run): pos0 omission >= 10pp above base. The empty-list outputs (`{"allergies": []}`) are counted as omissions and reported separately as the clinically worst form.
Planned mechanism tests for pos0 (not yet run): (a) pos0 with a neutral one-line preamble before the allergy section (position vs unusual structure); (b) pos0 with the section header renamed; (c) qwen3.5:9b same cases (does medical tuning change it).
Known limitations: truth lexicon covers ~40 drugs, so unmapped drugs in the truth sentence are not scored; note 2274 moves a short narrative tail with its allergy span.

## Amendment 2 (2026-11-02, after the full 792-case run, BEFORE the mechanism run)
Full run seen (results/run_a_primary.csv, results/failure_a_summary.csv): base 5/119 omitted; pos0 26/119 (+17.6 pp, 24 worse / 3 better, Holm p < 0.001); ctrl, pos50, pos100, hpi_sentence, abbrev all within noise of base. 14 of 26 pos0 omissions are empty lists; 3 pos0 "omissions" are parse failures (correct answer, non-JSON). Sensitivity excluding the 3 notes with parse failures: +16.4 pp, p = 0.00016.
Verdicts on earlier predictions: P1 control held (1 discordant). P2 (hpi_sentence omits more) NOT supported (1/119 vs base 5/119). P3 (pos50 worst) NOT supported. P4 (abbrev omits more) NOT supported (2/78). P5 pos0 >= +10 pp held.
Hypotheses for why pos0 fails:
- H-position (primacy/start of document): the allergy section sits before any clinical context.
- H-structure: the note opens with a bare header line and the model treats it as metadata/title, not content.
Mechanism conditions (each paired with base, same 119 notes): pos5, pos10, pos25 (allergy section moved to 5/10/25% of the note) and pos0_title (pos0 plus a neutral line "CLINICAL NOTE:," before it).
Predictions, written before running:
- M1: omission falls with distance from the start: pos10 <= pos0 - 8 pp and pos25 <= base + 5 pp. A cliff (pos5 already near base) means the failure is specific to the very first lines.
- M2: pos0_title <= pos0 - 8 pp. If true, mechanism = unusual note opening (structure), not position as such. If pos0_title ~ pos0, primacy position itself is the cause.
My own expectation: M1 holds, M2 partially holds (title halves the rate, does not remove it). Either result is reported.
Call budget: 4 x 119 = 476 local medgemma calls. Qwen comparison on base+pos0 (238 calls) is a separate run after this.

## Amendment 3 (2026-11-04, after code review; no prediction changed)
- swap_abbrev matched the generic name inside longer words; for note 3273 "SULFAS" became "BactrimS". Fixed with whole-word matching; that note no longer has an abbrev case. Abbrev is now 2/77 (was 2/78); verdict on P4 unchanged. All other conditions byte-identical, 0 new model calls.
- Known artifact, not fixed (would re-run ~1,500 calls): moving the allergy section leaves a ",," seam where it was removed in every moved condition (pos0..pos100, pos0_title, hpi_sentence). pos5-pos100 carry the same seam and stay at base, so the seam does not explain pos0.
- Holm family size: the text above says "5 perturbed conditions"; the code (experiments/10) corrects across all 6 (abbrev added later), which is more conservative. No verdict changes.
