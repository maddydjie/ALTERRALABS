"""Make every figure from results/*.csv. Skips a figure if its input csv does not exist yet."""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

GRAY, ACCENT, INK = "#8a8f98", "#d1495b", "#222222"   # neutral conditions, the finding, text
os.makedirs("figures", exist_ok=True)
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})


def fig_a():
    """Omission rate per condition with Wilson 95% CI (results/failure_a_summary.csv)."""
    if not os.path.exists("results/failure_a_summary.csv"):
        return
    s = pd.read_csv("results/failure_a_summary.csv")
    order = ["base", "ctrl_header_case", "abbrev", "hpi_sentence", "pos100", "pos50", "pos0"]
    s = s.set_index("condition").loc[order].reset_index()
    fig, ax = plt.subplots(figsize=(6.5, 3.4))
    y = range(len(s))[::-1]
    for yi, r in zip(y, s.itertuples()):
        c = ACCENT if r.condition == "pos0" else GRAY
        ax.plot([100 * r.ci_lo, 100 * r.ci_hi], [yi, yi], color=c, lw=2)
        ax.plot(100 * r.rate, yi, "o", color=c, ms=8, mec="white", mew=1.5)
        ax.text(100 * r.ci_hi + 1, yi, "%d/%d" % (r.omitted, r.n), va="center", color=INK, fontsize=9)
    ax.set_yticks(list(y))
    labels = {"base": "base (unchanged)", "ctrl_header_case": "control: header capitalisation", "abbrev": "abbreviation or brand",
              "hpi_sentence": "free-text sentence", "pos100": "section at the end", "pos50": "section in the middle",
              "pos0": "section on first line (pos0)"}
    ax.set_yticklabels([labels[c] for c in s.condition])
    ax.set_xlabel("Allergy omitted (% of notes, Wilson 95% CI)")
    ax.set_xlim(0, 40)
    ax.set_title("Only the first-line position raises omission", loc="left", fontsize=11)
    ax.grid(axis="x", color="#e5e5e5", lw=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig("figures/fig_a_omission.png", dpi=200)


def fig_a_mech():
    """Position sweep + title test (results/failure_a_mechanism.csv)."""
    if not os.path.exists("results/failure_a_mechanism.csv"):
        return
    m = pd.read_csv("results/failure_a_mechanism.csv").set_index("condition")
    pos = {"pos0": 0, "pos5": 5, "pos10": 10, "pos25": 25}
    fig, ax = plt.subplots(figsize=(6.5, 3.4))
    xs = list(pos.values())
    ax.errorbar(xs, [100 * m.rate[c] for c in pos],
                yerr=[[100 * (m.rate[c] - m.ci_lo[c]) for c in pos], [100 * (m.ci_hi[c] - m.rate[c]) for c in pos]],
                color=ACCENT, marker="o", ms=7, lw=2, capsize=3)
    ax.axhline(100 * m.rate["base"], color=GRAY, lw=1.5, ls="--")
    ax.text(12, 100 * m.rate["base"] + 0.8, "base (section in place)", color=INK, fontsize=9)
    ax.errorbar([1.2], [100 * m.rate["pos0_title"]], color=INK, marker="s", ms=7,
                yerr=[[100 * (m.rate["pos0_title"] - m.ci_lo["pos0_title"])], [100 * (m.ci_hi["pos0_title"] - m.rate["pos0_title"])]], capsize=3)
    ax.text(2, 100 * m.rate["pos0_title"] + 1, "pos0 + neutral title line", color=INK, fontsize=9)
    ax.set_xlabel("Allergy section moved to this % of the way through the note")
    ax.set_ylabel("Omitted (% of notes)")
    ax.set_title("Omission is a cliff at the very start of the note", loc="left", fontsize=11)
    ax.grid(axis="y", color="#e5e5e5", lw=0.8)
    fig.tight_layout()
    fig.savefig("figures/fig_a_mechanism.png", dpi=200)


def fig_b():
    """Resolved-allergy arms: % of charts where the test drug is put on the allergy list."""
    if not os.path.exists("results/failure_b_temporal_summary.csv"):
        return
    s = pd.read_csv("results/failure_b_temporal_summary.csv")
    s = s[s.subset == "all"].set_index("arm")
    order = [("base", "no sentence"), ("control_tolerates", "takes X without problems"),
             ("resolved_no_reaction", "negative challenge, no reaction words"),
             ("resolved_first", "resolution stated first, then rash"),
             ("resolved", "rash as child; negative challenge 2019"),
             ("active_history", "rash as child (guard)")]
    fig, ax = plt.subplots(figsize=(6.5, 3.4))
    y = range(len(order))[::-1]
    for yi, (arm, label) in zip(y, order):
        r = s.loc[arm]
        c = ACCENT if arm == "resolved" else (INK if arm == "active_history" else GRAY)
        ax.plot([100 * r.ci_lo, 100 * r.ci_hi], [yi, yi], color=c, lw=2)
        ax.plot(100 * r.rate, yi, "o", color=c, ms=8, mec="white", mew=1.5)
        ax.text(100 * r.ci_hi + 1.5, yi, "%d/%d" % (r.listed, r.n), va="center", color=INK, fontsize=9)
    ax.set_yticks(list(y))
    ax.set_yticklabels([l for _, l in order])
    ax.set_xlabel("Drug put on allergy list (% of charts, Wilson 95% CI)")
    ax.set_xlim(0, 80)
    r = s.loc["resolved"]  # title number comes from the csv, not typed in
    ax.set_title("Disproven allergy re-listed in %d of %d charts" % (r.listed, r.n), loc="left", fontsize=11)
    ax.grid(axis="x", color="#e5e5e5", lw=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig("figures/fig_b_resolved.png", dpi=200)


if __name__ == "__main__":
    fig_a()
    fig_a_mech()
    fig_b()
    print("figures:", sorted(os.listdir("figures")))
