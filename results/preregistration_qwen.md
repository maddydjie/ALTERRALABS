# Preregistration: qwen3.5:9b comparison (written 2026-11-04, BEFORE any qwen call on these cases)

Question: does medical tuning help or hurt? Same cases, same prompts, same grader, second model.
Comparison model: qwen3.5:9b, Ollama Q4_K_M, digest 6488c96fa5fa, think=false, temperature 0, seed 42.
Caveat: different size (9.7B vs 4B) and family, so a difference is "this general model vs this medical model", not a clean test of medical tuning.

Cases (subset of the existing case files, built by experiments/40_build_qwen_subset.py):
- Failure A: base + pos0, 119 notes (238 calls).
- Failure B: base + resolved + active_history, 116 charts (348 calls).
- Total 586 local calls (approved by Madhavi 2026-11-04).

Analysis (experiments/41_qwen_compare.py):
- Per model: rate + Wilson 95% CI; within-model paired McNemar vs base (same as before).
- Across models: paired exact McNemar on the same case (medgemma wrong / qwen right vs the reverse).

Predictions (my expectation, either outcome reported):
- Q1 (A): qwen pos0 omission < medgemma pos0 omission (21.8%). A bigger general model is less thrown by layout. If qwen also shows pos0 >= base + 10 pp, the failure is not MedGemma-specific.
- Q2 (B): qwen resolved listing < medgemma (25.0%). General instruction-tuned models read qualifiers better.
- Q3 (B guard): qwen active_history listing differs from medgemma 59.5%; no direction predicted.
- Base rates: qwen base A omission and base B listing both <= 5%, otherwise the comparison is confounded by a weaker baseline.

## Outcome (2026-11-04, after the run; predictions above unchanged)
Run: results/run_a_qwen.csv, results/run_b_qwen.csv; analysis results/qwen_compare.csv. 0/586 parse failures.
- Q1 NOT supported, opposite direction: qwen pos0 omission 42/119 = 35.3% [27.3, 44.2] vs medgemma 26/119 (15 medgemma-only / 31 qwen-only, p = 0.026). Within qwen: base 1/119, 41 worse / 0 better (p = 9e-13). 40 of 42 are empty lists. Failure A is not MedGemma-specific.
- Q2 held: qwen resolved 13/116 = 11.2% [6.7, 18.2] vs medgemma 29/116 (24 / 8, p = 0.007). But qwen still re-lists: base 0/116, 13 worse / 0 better (p = 2.4e-4).
- Q3: guard 75/116 (64.7%) vs medgemma 69/116 (59.5%), p = 0.51, no difference.
- Base rates both <= 5% (A 0.8%, B 0%), so the comparison is not confounded by a weaker baseline.
Not run (budget): qwen on the A mechanism arms (pos5/pos0_title) and on B control / mechanism arms.
