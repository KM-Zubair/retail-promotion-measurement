"""Create the machine-readable estimates, figure and decision memo."""
import csv
from dataclasses import asdict
from pathlib import Path

from .analysis import Arm, Contrast
from .data import CONTROL, MENS, WOMENS

LABELS = {CONTROL: "No email", MENS: "Men’s merchandise", WOMENS: "Women’s merchandise"}


def write_records(path, records):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(records[0])), lineterminator="\n")
        writer.writeheader()
        writer.writerows(asdict(record) for record in records)


def make_figure(effects, dest):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    with plt.rc_context({"font.size": 11, "axes.spines.top": False,
                         "axes.spines.left": False, "axes.spines.right": False}):
        fig, ax = plt.subplots(figsize=(9, 3.8))
        fig.subplots_adjust(top=0.79, bottom=0.27, left=0.30, right=0.96)
        fig.text(.035, .92, "Which email generated additional buyers?", fontsize=17, weight="bold")
        labels = ["Men’s vs no email", "Women’s vs no email", "Men’s vs women’s"]
        for i, e in enumerate(effects):
            color = "#1d5968" if i < 2 else "#9a4d27"
            ax.errorbar(e.extra_buyers_per_1000, i,
                        xerr=[[e.extra_buyers_per_1000-e.ci_low],[e.ci_high-e.extra_buyers_per_1000]],
                        color=color, marker="o", markersize=8, capsize=5, linewidth=2)
            ax.annotate(f"{e.extra_buyers_per_1000:+.2f}", (e.extra_buyers_per_1000, i),
                        xytext=(0, 10), textcoords="offset points", ha="center", color=color)
        ax.axvline(0, color="#555555", linestyle="--", linewidth=1)
        ax.set_yticks(range(len(effects)), labels)
        ax.set_ylim(len(effects)-0.45, -.55)
        ax.set_xlim(min(-.5, min(e.ci_low for e in effects)-.5), max(e.ci_high for e in effects)+.7)
        ax.grid(axis="x", alpha=.17)
        ax.tick_params(axis="y", length=0, pad=10)
        ax.set_xlabel("Additional buyers per 1,000 assigned customers", labelpad=8)
        fig.text(.035, .045, "Two-week purchase outcome  •  Bonferroni-adjusted intervals, 95% family confidence", fontsize=9)
        fig.savefig(dest, dpi=170, facecolor="white")
        plt.close(fig)


def decision(effects):
    men, women, head = effects
    if men.ci_low > 0 and head.ci_low > 0:
        return "Choose the men’s-merchandise email to maximize the number of buyers in a comparable audience."
    if women.ci_low > 0 and head.ci_high < 0:
        return "Choose the women’s-merchandise email to maximize the number of buyers in a comparable audience."
    if max(men.ci_low, women.ci_low) > 0:
        return "At least one email beats the holdout. The evidence does not establish a single best creative."
    return "Keep a holdout and gather more evidence before choosing a creative."


def memo(arms: list[Arm], effects: list[Contrast]) -> str:
    lines = ["# Campaign decision", "", "**" + decision(effects) + "**", "",
             "The outcome is a customer making at least one purchase within two weeks of assignment.",
             "", "| Assignment | Customers | Buyers | Purchase rate | Gross spend per assigned customer |",
             "|---|---:|---:|---:|---:|"]
    for a in arms:
        lines.append(f"| {LABELS[a.arm]} | {a.assigned:,} | {a.buyers:,} | {a.purchase_rate:.3%} | ${a.spend_per_assigned:.2f} |")
    lines += ["", "| Comparison | Additional buyers per 1,000 | 95% simultaneous confidence interval |", "|---|---:|---:|"]
    for e in effects:
        lines.append(f"| {LABELS[e.treatment]} vs {LABELS[e.comparison].lower()} | {e.extra_buyers_per_1000:+.2f} | [{e.ci_low:+.2f}, {e.ci_high:+.2f}] |")
    lines += ["", "![Estimated campaign effects with simultaneous intervals](campaign_lift.png)", "",
              "## Interpretation", "",
              "The intervals use the Newcombe score method with a Bonferroni adjustment for approximately 95% simultaneous confidence across the three comparisons. The head-to-head row directly estimates the difference between the creatives. The labels identify the merchandise featured in each email. Customers were randomly allocated across all three groups.",
              "", "The spend column includes zeros for non-buyers. It measures observed gross revenue per assignment. Choosing a campaign for profit would also require contribution margins, sending costs and the cost of any incentives.",
              "", "These estimates describe the historical challenge population and its two-week follow-up. A current rollout should use a comparable audience and retain a randomized holdout to measure whether the effect carries over.", ""]
    return "\n".join(lines)


def export(arms, effects, output: Path):
    output.mkdir(parents=True, exist_ok=True)
    write_records(output / "arm_summary.csv", arms)
    write_records(output / "campaign_effects.csv", effects)
    make_figure(effects, output / "campaign_lift.png")
    (output / "decision.md").write_text(memo(arms, effects), encoding="utf-8")
