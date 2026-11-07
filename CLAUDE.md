# CLAUDE.md — Alterra Labs Applied Research Take-Home

## Who I am and what this is
I'm Madhavi: MBBS (Andhra Medical College), clinical data scientist working on oncology real-world evidence from EHR data. This repo is my take-home for the **Applied Research** role at Alterra Labs.

**The assignment:** pick one SOTA or open-source model, apply it to a real clinical task, and find **two failures that are different in kind**. For each failure I need:
1. **What fails**: one crisp sentence.
2. **Evidence**: concrete examples plus a measured rate, with confidence intervals.
3. **Why**: a mechanism hypothesis and at least one experiment that tests it.

A failure is a *specific, reproducible condition* under which the output is clinically wrong. "Accuracy is 71%" does not count as a failure.

**Deliverables (due Day 7, 11:59 pm ET):**
- Write-up: max 4 pages plus appendix. One page per failure, plus a section on what I tried that did *not* turn up a failure.
- Code: this repo, runnable end to end, with a README.
- Slides: 5-minute talk covering the system and task, each failure, and next steps. In the presentation they deep-dive one failure for 10 min.

**Rubric (optimise in this order):**
| Criterion | Weight | What it means for this repo |
|---|---|---|
| Rigor | 30% | Controls, baselines, enough n to rule out noise, `make reproduce` regenerates every number |
| Mechanism | 25% | Each failure has a hypothesis and a targeted ablation/intervention that tests it |
| Clinical relevance | 20% | Each failure maps to a real workflow and a concrete harm, sized honestly |
| Communication | 15% | One-sentence failure statements, clean figures |
| Judgment & honesty | 10% | Limitations stated, real vs synthetic clearly labelled, dead ends reported |

## Non-negotiable rules for Claude Code
1. **Never invent numbers, examples, or citations.** Every number in the write-up must be produced by code in this repo and traceable to a file in `results/`. If a result doesn't exist yet, write `TODO`.
2. **I must be able to explain every line.** Simple, readable code. No clever abstractions or unneeded frameworks. Short comment where logic isn't obvious. Explain any non-trivial technique (stat test, perturbation method) to me in chat before using it.
3. **Log AI assistance.** Append to `AI_USAGE.md` whenever code or text is written or substantially changed: date, files, what was done.
4. **Determinism.** Temperature 0 / greedy, fixed seed. Pin exact model name and revision. Cache every raw response to `data/cache/` keyed by hash of model+prompt+params so reruns never re-query.
5. **Ask before burning time or money.** Confirm before any run with more than 500 model calls, any paid API usage, or any large download.
6. **Label data provenance everywhere.** Every test case carries `source: real | perturbed_real | synthetic` and the parent record ID if perturbed.
7. **No PHI.** Public datasets only. If MIMIC is used, follow the PhysioNet DUA: never commit MIMIC text, never send it to third-party APIs. `data/raw/` is gitignored.
8. **Prefer deterministic grading** (normalised string match, regex, structured JSON comparison) over LLM-as-judge. If a judge is unavoidable, validate on >=50 hand-labelled items and report Cohen's kappa.
9. **Report failures to find failures.** Every probe goes in `results/probe_log.csv`, including clean ones. These feed the "what didn't fail" section.

## System under test
- **Primary model:** MedGemma 4B-it (open weights, medically tuned). Pin exact checkpoint in `config.yaml`.
- **Backend:** `src/models.py::generate(prompt, **params) -> str` (Ollama local, with disk cache).
- **Comparison model:** `qwen3.5:9b` (general-purpose, already local) to test whether medical tuning helps or hurts.
- Hardware: Apple M2, 16 GB RAM.

## Data
- Without credentials: MTSamples, Synthea, hand-built and perturbed cases.
- If PhysioNet access comes through: MIMIC-IV-Note (local model only, rule 7).
- **Perturbed real notes are the main instrument:** change exactly one thing, keep everything else byte-identical, giving paired comparisons.

## Candidate failures (two that differ in kind)
**Failure A: extraction / omission.** Extract allergies and active medications as JSON. Items dropped when abbreviated (PCN, brand names), in a non-standard section, or mid-note in a long document. Mechanism tests: position sweep 0-100%, abbreviation vs expanded term, section placement. Harm: dropped allergy gets re-prescribed.

**Failure B: reasoning / premise.** B1 false premise / sycophancy (question asserts an allergy the chart doesn't document; neutral vs false premise vs premise + "verify against chart"). Fallback B2: unit confusion (mmol/L vs mg/dL, umol/L vs mg/dL).

**Broad probes (Days 1-2, log all):** negation, temporality, demographic counterfactuals, dose-unit errors, copy-forward duplication, long-context truncation.

## Experimental standards
- n >= 100 paired items per condition for headline numbers; justify smaller n.
- Rates with Wilson 95% CIs. Paired comparisons: McNemar's test, report discordant counts.
- Every failure gets: **baseline** (unperturbed), **control** (perturbation that shouldn't change the answer), and >=1 **mechanism test** with prediction written in `results/preregistration.md` BEFORE running.
- Say how many probes were run; no cherry-picking. Effect size over p-values.
- Hand-check >= 30 raw outputs per failure to confirm grader.

## Repo structure
See README.md. Phases: Setup -> Probe -> Pick -> Prove -> Write.

## Write-up format (per failure, one page)
Failure statement (one sentence) · Clinical workflow & harm (sized honestly) · Evidence (1-2 verbatim examples, rate+CI, baseline, control) · Mechanism (hypothesis, preregistered prediction, test, held or not) · Limitations.

## Style
Informal and fast. Be direct, recommend rather than menu. Explain stats/ML choices briefly in plain language. After each phase give a short summary: found, means, next.
