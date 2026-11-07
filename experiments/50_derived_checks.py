"""Secondary numbers quoted in the write-up/slides that the main summaries do not store.

Reads the raw run csvs, writes results/derived_checks.csv (one row per check: name, value, detail),
so every number in the write-up traces to a file in results/ (CLAUDE.md rule 1).
"""
import pandas as pd

from src.stats import mcnemar_exact, wilson_ci

rows = []


def add(name, value, detail=""):
    rows.append({"check": name, "value": value, "detail": detail})


def holm(pvals):
    """Holm step-down: sort p, multiply by (m - rank), keep monotone."""
    out, run = {}, 0.0
    for rank, (k, p) in enumerate(sorted(pvals.items(), key=lambda x: x[1])):
        run = max(run, min(1.0, p * (len(pvals) - rank)))
        out[k] = run
    return out


# ---- Failure A (MedGemma) ----
a = pd.read_csv("results/run_a_primary.csv")
p0 = a[a.condition == "pos0"]
add("A pos0 empty lists among omissions", "%d/%d" % (((p0.n_items == 0) & (p0.omitted == 1)).sum(), p0.omitted.sum()))
add("A pos0 parse failures", int((~p0.parse_ok).sum()), ";".join(map(str, p0[~p0.parse_ok].parent_id)))
wrong_json = int(((p0.omitted == 1) & p0.parse_ok).sum())  # a JSON answer that really dropped a drug
add("A pos0 omissions with valid JSON only", "%d/%d" % (wrong_json, len(p0)), "%.1f%%" % (100 * wrong_json / len(p0)))
# sensitivity: drop every note with a parse failure in base or pos0
w = a.pivot(index="parent_id", columns="condition", values="omitted")
ok = a.pivot(index="parent_id", columns="condition", values="parse_ok")
keep = w[ok.base & ok.pos0]
worse = int(((keep.base == 0) & (keep.pos0 == 1)).sum())
better = int(((keep.base == 1) & (keep.pos0 == 0)).sum())
add("A pos0 vs base excluding parse-failure notes",
    "%+.1f pp" % (100 * (keep.pos0.mean() - keep.base.mean())),
    "n=%d worse=%d better=%d p=%.2g" % (len(keep), worse, better, mcnemar_exact(worse, better)))
# post hoc sensitivity from the hand-check audit. The grader itself stays unchanged.
# Drop the 3 notes with non-JSON pos0 answers (1478, 3267, 3357) and note 1357 ("Demetrol" = misspelt Demerol).
# Note 1801 at base listed "Cefalexin", a cephalosporin the lexicon lacks, so count it as not omitted.
fix = w.drop([1478, 3267, 3357, 1357]).copy()
fix.loc[1801, "base"] = 0
worse = int(((fix.base == 0) & (fix.pos0 == 1)).sum())
better = int(((fix.base == 1) & (fix.pos0 == 0)).sum())
lo, hi = wilson_ci(int(fix.pos0.sum()), len(fix))
add("A pos0 vs base, hand-check corrected (post hoc)",
    "%+.1f pp" % (100 * (fix.pos0.mean() - fix.base.mean())),
    "n=%d base=%d pos0=%d (%.1f%%, CI %.1f-%.1f) worse=%d better=%d p=%.2g"
    % (len(fix), fix.base.sum(), fix.pos0.sum(), 100 * fix.pos0.mean(), 100 * lo, 100 * hi, worse, better,
       mcnemar_exact(worse, better)))

# post hoc: pos0 was seen looking worst in the sanity run, so also test only the notes that run did not include
seen = set(pd.read_csv("results/sanity_a_primary.csv").parent_id)
unseen = w[~w.index.isin(seen)]
worse = int(((unseen.base == 0) & (unseen.pos0 == 1)).sum())
better = int(((unseen.base == 1) & (unseen.pos0 == 0)).sum())
lo, hi = wilson_ci(int(unseen.pos0.sum()), len(unseen))
add("A pos0 vs base, notes not in sanity run (post hoc)",
    "%+.1f pp" % (100 * (unseen.pos0.mean() - unseen.base.mean())),
    "n=%d base=%d pos0=%d (%.1f%%, CI %.1f-%.1f) worse=%d better=%d p=%.2g"
    % (len(unseen), unseen.base.sum(), unseen.pos0.sum(), 100 * unseen.pos0.mean(), 100 * lo, 100 * hi, worse, better,
       mcnemar_exact(worse, better)))

# ---- Failure B (MedGemma) ----
b = pd.read_csv("results/run_b_temporal_primary.csv")
wb = b.pivot(index="parent_id", columns="condition", values="listed_drug")
drug = b.drop_duplicates("parent_id").set_index("parent_id").drug
sul = wb.control_tolerates[drug == "sulfa"]
add("B control listed, sulfa charts", "%d/%d" % (sul.sum(), len(sul)), "%.1f%%" % (100 * sul.mean()))
for d in ["penicillin", "sulfa", "codeine", "aspirin"]:
    add("B charts with test drug " + d, int((drug == d).sum()))
worse = int(((wb.control_tolerates == 0) & (wb.resolved == 1)).sum())
better = int(((wb.control_tolerates == 1) & (wb.resolved == 0)).sum())
add("B resolved vs control", "%d worse / %d better" % (worse, better), "p=%.2g" % mcnemar_exact(worse, better))
relisted = set(wb.index[wb.resolved == 1])
active = set(wb.index[wb.active_history == 1])
add("B re-listed charts inside active-listed", "%d/%d" % (len(relisted & active), len(relisted)),
    "conditional rate %d/%d = %.1f%% (post hoc)" % (len(relisted), len(active), 100 * len(relisted) / len(active)))
add("B parse failures", int((~b.parse_ok).sum()), ";".join("%s:%s" % t for t in zip(b[~b.parse_ok].parent_id, b[~b.parse_ok].condition)))
# post hoc: resolved rate per test drug
for d in ["sulfa", "codeine", "penicillin", "aspirin"]:
    k, n = int(wb.resolved[drug == d].sum()), int((drug == d).sum())
    lo, hi = wilson_ci(k, n)
    add("B resolved listed, %s charts (post hoc)" % d, "%d/%d" % (k, n), "%.1f%%, CI %.1f-%.1f" % (100 * k / n, 100 * lo, 100 * hi))
# post hoc: the test-drug grader cannot see other items, so count non-empty lists on these NKDA charts at base
base_b = b[b.condition == "base"]
add("B base outputs with a non-empty list (post hoc)", "%d/%d" % ((base_b.n_items > 0).sum(), len(base_b)),
    ";".join(map(str, base_b[base_b.n_items > 0].parent_id)))
# post hoc: do listings in the other arms also fall inside the charts that list the plain rash history?
for arm in ["resolved", "control_tolerates", "resolved_first", "resolved_no_reaction"]:
    inside = int(((wb[arm] == 1) & (wb.active_history == 1)).sum())
    add("B %s listings inside guard-listed charts (post hoc)" % arm, "%d/%d" % (inside, wb[arm].sum()))


def mc(x, y):
    """x -> y: count charts listed in y but not x, and the reverse"""
    return mcnemar_exact(int(((wb[x] == 0) & (wb[y] == 1)).sum()), int(((wb[x] == 1) & (wb[y] == 0)).sum()))


tests = {"C1 resolved vs base": mc("base", "resolved"), "C2 control vs base": mc("base", "control_tolerates"),
         "M1 no_reaction vs resolved": mc("resolved", "resolved_no_reaction"),
         "M2 first vs resolved": mc("resolved", "resolved_first")}
for k, v in holm(tests).items():
    add("B Holm p (m=4) " + k, "%.2g" % v)
# preregistration text said 5 tests; C3 is a threshold, so the code uses 4. Show m=5 for transparency.
for k, v in tests.items():
    add("B Holm p if m=5 (conservative) " + k, "%.2g" % min(1.0, v * 5), "upper bound")

# ---- False-premise pilot ----
# The gate requires a correct neutral answer, so the gated neutral rate is 0 by construction. Report all charts too.
pilot = pd.read_csv("results/pilot_b_primary.csv")
answers = pilot.pivot(index="parent_id", columns="arm", values="answer")
stratum = pilot.drop_duplicates("parent_id").set_index("parent_id").stratum
false_charts = answers[stratum != "penicillin"]
false_yes, neutral_yes = false_charts.P_false == "yes", false_charts.P_neutral == "yes"
add("Pilot all charts: false premise yes", "%d/%d" % (false_yes.sum(), len(false_charts)))
add("Pilot all charts: neutral yes", "%d/%d" % (neutral_yes.sum(), len(false_charts)), "both yes=%d" % (false_yes & neutral_yes).sum())
lo, hi = wilson_ci(2, 36)
add("Pilot gated false premise CI", "2/36", "CI %.1f-%.1f" % (100 * lo, 100 * hi))

# ---- qwen ----
q = pd.read_csv("results/run_a_qwen.csv")
q0 = q[q.condition == "pos0"]
add("qwen A pos0 empty lists among omissions", "%d/%d" % (((q0.n_items == 0) & (q0.omitted == 1)).sum(), q0.omitted.sum()))

out = pd.DataFrame(rows)
out.to_csv("results/derived_checks.csv", index=False)
print(out.to_string(index=False))
