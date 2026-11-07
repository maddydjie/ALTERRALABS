.PHONY: setup data smoke probes failure_a failure_b qwen derived figures analyze reproduce pdf test clean

PY = PYTHONPATH=. .venv/bin/python

setup:
	python3 -m venv .venv
	.venv/bin/pip install --index-url https://pypi.org/simple -r requirements.txt

# public MTSamples notes: checked against a known md5, not stored in this repo (licence is ambiguous)
data:
	sh experiments/01_download_data.sh

smoke:
	$(PY) -m tests.smoke

# every step reads/writes the disk cache (data/cache), so reruns are instant once the model has answered
probes:
	$(PY) experiments/00_probes.py

failure_a:
	$(PY) experiments/05_build_cases_a.py
	$(PY) experiments/06_build_mech_a.py
	$(PY) -m src.run data/cases/failure_a.jsonl results/run_a_primary.csv primary
	$(PY) -m src.run data/cases/failure_a_mech.jsonl results/run_a_mech_primary.csv primary
	$(PY) experiments/10_failure_a.py
	$(PY) experiments/11_failure_a_mechanism.py

failure_b: probes  # 30 reads results/probes_cases.jsonl
	# headline Failure B: resolved allergy re-listed (preregistration_b.md, Amendment 2)
	$(PY) experiments/30_build_cases_b_temporal.py
	$(PY) -m src.run data/cases/failure_b_temporal.jsonl results/run_b_temporal_primary.csv primary
	$(PY) experiments/31_failure_b_temporal.py
	# false-premise pilot (reported under "what did not fail")
	N_PER_STRATUM=20 $(PY) experiments/20_build_cases_b.py
	$(PY) -m src.run_b data/cases/failure_b.jsonl results/pilot_b_primary.csv primary
	$(PY) experiments/21_failure_b.py results/pilot_b_primary.csv

qwen: failure_a failure_b  # 40 reads their case files
	# comparison model on the headline conditions (results/preregistration_qwen.md)
	$(PY) experiments/40_build_qwen_subset.py
	$(PY) -m src.run data/cases/qwen_a.jsonl results/run_a_qwen.csv comparison
	$(PY) -m src.run data/cases/qwen_b.jsonl results/run_b_qwen.csv comparison
	$(PY) experiments/41_qwen_compare.py

derived:
	# secondary numbers quoted in the write-up (sensitivity, sulfa, nested, Holm p) -> results/derived_checks.csv
	$(PY) experiments/50_derived_checks.py
	# grader vs hand labels -> results/handcheck_agreement.csv
	$(PY) experiments/13_handcheck_agreement.py

figures:
	$(PY) experiments/99_figures.py

# recompute the reported numbers and figures from the saved outputs in results/ (no notes or model needed)
analyze:
	$(PY) experiments/10_failure_a.py
	$(PY) experiments/11_failure_a_mechanism.py
	$(PY) experiments/31_failure_b_temporal.py
	$(PY) experiments/21_failure_b.py results/pilot_b_primary.csv
	$(PY) experiments/41_qwen_compare.py
	$(MAKE) derived figures

reproduce: probes failure_a failure_b qwen derived figures

pdf:
	$(PY) writeup/build_pdf.py

test:
	$(PY) -m tests.test_stats && $(PY) -m tests.test_grade

clean:
	rm -f figures/*.png
