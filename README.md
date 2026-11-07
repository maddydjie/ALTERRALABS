# Alterra Labs Applied Research Take-Home

Madhavi Boddepalli. **Read first: [`writeup/writeup.pdf`](writeup/writeup.pdf)**, 4 pages plus appendix.

I tested **MedGemma 4B-it** on one clinical job: extract the drug allergy list from a note. I found two reproducible failures that differ in kind.

| Failure | One-sentence statement | Result |
|---|---|---|
| **A: omission** | When the allergy section is moved to the first line of a note, MedGemma-4B drops at least one documented allergy. | 26/119 (21.8%, CI 15.4-30.1) vs base 5/119; 24 notes worse, 3 better; Holm p < 0.001 |
| **B: reasoning** | When a note says a childhood drug rash was disproven by a negative challenge, MedGemma-4B still lists that drug as an allergy. | 29/116 (25.0%, CI 18.0-33.6) vs base 0/116; Holm p = 1.5e-8; fresh charts 18/81 |

**Real versus altered data:** all notes are real, public MTSamples reports with names and dates changed or removed, no PHI. Altered notes are real notes with one edit I made, labelled `source: perturbed_real` with a `parent_id`. No synthetic notes were used.

## Check the numbers

Needs Python 3.9+. No notes, model or GPU needed. It takes under a minute.

```
make setup     # create .venv and install pinned packages
make analyze   # recompute the numbers and figures from the saved model outputs in results/
make test      # unit tests for the statistics and graders
```

`make analyze` rewrites the summary files in `results/`. `git diff` should then show no number changes.

## Rerun end to end

Model answers are not in this repo because they contain the full note text (see Data below). A rerun therefore queries the model again: about 3,000 local calls, so expect hours on a laptop.

```
ollama serve &
ollama pull medgemma:4b
ollama pull qwen3.5:9b
make setup
make data        # download the notes and check their md5
make smoke       # one model call, end to end
make reproduce   # build cases, run both models, regenerate every number and figure
```

Each answer is cached in `data/cache/`, keyed by a hash of model, prompt and settings, so a second run makes no model calls. A model whose digest differs from the pinned one in `config.yaml` is refused. Later Ollama versions may not return byte-identical answers.

To rebuild the PDF: `make pdf` (needs Google Chrome).

## Data

- **Source:** MTSamples ([mtsamples.com](https://mtsamples.com)), downloaded from a [public mirror](https://github.com/socd06/medical-nlp); md5 `d8547837775283c95b8a70119da806f8`.
- **Why it is not committed:** the site allows sharing for education with credit, and the mirror's licence is unclear. So `data/raw/`, `data/cases/` and `data/cache/` are gitignored.
- **Small excerpts:** `results/` holds model outputs and short excerpts for hand-checking, with credit to MTSamples.

## Layout

- `writeup/` write-up (`writeup.pdf`, source `writeup.md`, builder `build_pdf.py`)
- `config.yaml` pinned models and settings (temperature 0, seed 42)
- `src/models.py` cached `generate()`
- `src/stats.py` Wilson CI, exact McNemar, bootstrap, kappa
- `src/parse.py`, `lexicon.py`, `perturb.py`, `grade.py` allergy-section parser, drug lexicon, perturbations, deterministic graders (no LLM judge)
- `experiments/` numbered scripts: 00 probes, 01 data download, 05-06 build A cases, 10-11 analyse A, 12 and 32 hand-check sheets, 13 hand-check agreement, 20-21 false-premise pilot, 30-31 Failure B, 40-41 qwen comparison, 50 secondary numbers, 99 figures
- `results/` output CSVs, `probe_log.csv` (every probe, clean ones included), `derived_checks.csv` (secondary and post hoc numbers), `handcheck_*.csv` (my hand labels), `preregistration*.md` (predictions and dated amendments)
- `figures/` the three figures
- `reports/` background literature notes made with AI assistance; not part of the results

## AI use

I used AI coding and writing assistants. [`AI_USAGE.md`](AI_USAGE.md) lists the date, files and work for each use. `CLAUDE.md` holds the working rules I gave the assistant.

## Limitations

- Both failures use my edits to real notes, so neither rate shows how often this happens in a hospital.
- I tested a Q4 quantised Ollama build, not the full-precision checkpoint.
- Expected answers come from a 40-drug lexicon; drugs outside it are not scored.
- The grader over-counts some Failure A omissions. Hand-check: 30/38 after review (first pass 27/38); correcting the errors changes the effect from +17.6 pp to +17.4 pp (`results/derived_checks.csv`). Failure B hand-check: 33/33.
- Preregistration dates are in my own files, with no external timestamp.
