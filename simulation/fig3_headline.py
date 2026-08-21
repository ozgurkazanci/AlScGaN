"""Figure 3: the headline result - capability against readout channel count."""

import json
import os
import sys

import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C
import figstyle as F

F.use_style()

with open(os.path.join(C.OUT_DIR, "headline_summary.json"),
          encoding="utf-8") as fh:
    S = json.load(fh)

P = S["pad_counts"]
DEVICES = ["graded", "homogeneous", "stochastic", "uniform"]
ORDER = DEVICES + ["esn", "delay_line"]

fig = plt.figure(figsize=F.SIZE_2x2)
gs = fig.add_gridspec(2, 2, hspace=0.66, wspace=0.34,
                      left=0.10, right=0.965, top=0.895, bottom=0.145)


def series(design, key):
    tbl = S["table"].get(design, {})
    xs, ys, es = [], [], []
    for p in P:
        if str(p) in tbl:
            xs.append(p)
            ys.append(tbl[str(p)][f"{key}_mean"])
            es.append(tbl[str(p)].get(f"{key}_std", 0.0))
    return np.array(xs), np.array(ys), np.array(es)


def pad_axis(ax):
    ax.set_xscale("log", base=2)
    ax.set_xticks(P)
    ax.set_xticklabels([str(p) for p in P])
    ax.set_xlabel("pads  $P$   (readout channels)")


# --- (a) nonlinear memory capacity, log scale so everything is visible -------
ax = fig.add_subplot(gs[0, 0])
for design in ORDER:
    cfg = F.DESIGN[design]
    xs, ys, es = series(design, "nlmc")
    if xs.size == 0:
        continue
    ys = np.maximum(ys, 3e-3)          # keep the delay line on a log axis
    ax.errorbar(xs, ys, yerr=es, color=cfg["color"], marker=cfg["marker"],
                ms=5, linestyle=cfg.get("linestyle", "-"), lw=1.8,
                elinewidth=1.0, capsize=2.5, label=cfg["label"])
ax.set_yscale("log")
ax.set_ylim(2e-3, 40)
pad_axis(ax)
ax.set_ylabel("nonlinear memory capacity")
handles, labels = ax.get_legend_handles_labels()
ax.text(0.03, 0.15, "delay line: zero at any length",
        transform=ax.transAxes, fontsize=8.3, color=F.MUTED)
F.heading(ax, "Delayed-parity capacity against array size",
          "log scale, so zero and the ESN are both on view")
F.despine(ax)
F.panel_tag(ax, "a")

# --- (b) delayed-parity accuracy against delay -------------------------------
ax = fig.add_subplot(gs[0, 1])
p_show = max(P)
for design in ORDER:
    tbl = S["table"].get(design, {}).get(str(p_show))
    if not tbl or "nl_acc_mean" not in tbl:
        continue
    cfg = F.DESIGN[design]
    acc = np.array(tbl["nl_acc_mean"])
    ax.plot(np.arange(len(acc)), acc, color=cfg["color"], marker=cfg["marker"],
            ms=4, lw=1.8, linestyle=cfg.get("linestyle", "-"),
            label=cfg["label"])
ax.axhline(0.5, color=F.AXIS, lw=1.2, ls="--", zorder=0)
ax.text(len(acc) - 0.3, 0.517, "chance", fontsize=8.8, color=F.MUTED,
        ha="right")
ax.set_xlabel(r"delay  $d$  (input samples)")
ax.set_ylabel("fraction of parities predicted")
ax.set_ylim(0.44, 1.04)
F.heading(ax, f"Where each design runs out  ($P$ = {p_show})",
          "pads reach chance by delay 5–6, the ESN by 12")
F.despine(ax)
F.panel_tag(ax, "b")

# --- (c) paired differences ---------------------------------------------------
ax = fig.add_subplot(gs[1, 0])
comps = ["homogeneous", "stochastic", "uniform"]
width = 0.25
xs = np.arange(len(P))
for i, comp in enumerate(comps):
    cfg = F.DESIGN[comp]
    vals, errs, stars = [], [], []
    for p in P:
        e = S["paired"].get(str(p), {}).get(comp)
        vals.append(e["mean_diff"] if e else np.nan)
        errs.append(e["std_diff"] / np.sqrt(e["n"]) if e else np.nan)
        pv = e["wilcoxon_p"] if e else np.nan
        stars.append("***" if pv < 1e-3 else "**" if pv < 1e-2
                     else "*" if pv < 0.05 else "n.s.")
    off = (i - 1) * width
    ax.bar(xs + off, vals, width * 0.9, yerr=errs, color=cfg["color"],
           ecolor=F.INK2, error_kw=dict(lw=1.0), zorder=3,
           label=f"vs {cfg['label']}")
    span = np.nanmax(np.abs(vals))
    for xi, v, st in zip(xs + off, vals, stars):
        if np.isfinite(v):
            ax.text(xi, v + np.sign(v) * span * 0.08, st, ha="center",
                    fontsize=8.3, color=F.INK2,
                    va="bottom" if v >= 0 else "top")
ax.axhline(0, color=F.AXIS, lw=1.0, zorder=2)
lo, hi = ax.get_ylim()
ax.set_ylim(lo - 0.22 * (hi - lo), hi)
ax.set_xticks(xs)
ax.set_xticklabels([str(p) for p in P])
ax.set_xlabel("pads  $P$")
ax.set_ylabel("capacity gained by the spread")
F.legend(ax, loc="upper left", fontsize=8.3)
F.note(ax, "*** p < 0.001, Wilcoxon, 100 paired runs", "lower right")
e2 = S["paired"]["2"]["homogeneous"]
e8 = S["paired"]["8"]["homogeneous"]
F.heading(ax, "Paired advantage of the spread",
          f"{e2['rel_pct']:+.0f}% at two channels, {e8['rel_pct']:+.0f}% at eight")
F.despine(ax)
F.panel_tag(ax, "c")

# --- (d) NARMA-10 with its control -------------------------------------------
ax = fig.add_subplot(gs[1, 1])
for design in ORDER:
    cfg = F.DESIGN[design]
    xs_, ys, es = series(design, "nrmse")
    if xs_.size == 0:
        continue
    ax.errorbar(xs_, ys, yerr=es, color=cfg["color"], marker=cfg["marker"],
                ms=5, linestyle=cfg.get("linestyle", "-"), lw=1.8,
                elinewidth=1.0, capsize=2.5, label=cfg["label"])
pad_axis(ax)
ax.set_ylabel("NARMA-10 error  (NRMSE)")
F.note(ax, "the delay line uses no device", "lower left")
F.heading(ax, "The same designs on NARMA-10",
          "a plain delay line beats every pad, so NARMA cannot test this")
F.despine(ax)
F.panel_tag(ax, "d")

fig.legend(handles, labels, loc="lower center", ncol=3, frameon=False,
           fontsize=9, bbox_to_anchor=(0.53, 0.0), columnspacing=2.4,
           handletextpad=0.6)

os.makedirs(C.FIG_DIR, exist_ok=True)
for ext in ("pdf", "png"):
    fig.savefig(os.path.join(C.FIG_DIR, f"fig3_headline.{ext}"))
print("wrote fig3")
for design in ORDER:
    row = S["table"].get(design, {})
    cells = "  ".join(f"P={p}:{row[str(p)]['nlmc_mean']:5.2f}"
                      for p in P if str(p) in row)
    print(f"  {design:>12}  {cells}")
