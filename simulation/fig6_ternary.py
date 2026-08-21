"""Figure 6: the control that joins the materials result to the device result.

A ternary-like array is built along a single composition axis, so spreading
the relaxation times necessarily spreads the coercive field, and is driven
from the same shared line with its own best drive.

(a) what each design can actually build: the requested time-constant window
    against the window the alloy reaches before leaving the physical
    composition range, and the coercive-field spread paid for it
(b) capability against drive. The ternary is not hopeless - a coercive-field
    spread becomes an enormous switching-rate spread under one drive, and that
    uncontrolled diversity substitutes for the designed kind
(c) but only at one temperature. The substitution collapses under ambient
    drift, because temperature robustness needs a wide spread of relaxation
    times and the ternary has barely one decade of them.

Three panels across, so the headings use the compact budget and the drive
axis carries explicit decimal ticks - the default log formatter emitted
overlapping minor labels like "2 x 10^-1" here.
"""

import json
import os
import sys

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C
import figstyle as F

F.use_style()
NL = chr(10)

with open(os.path.join(C.OUT_DIR, "ternary_control.json"),
          encoding="utf-8") as fh:
    S = json.load(fh)

QUAT, TERN = F.BLUE, F.ORANGE
KINDS = ["quaternary", "ternary"]
STYLE = {"quaternary": dict(color=QUAT, marker="o", label="quaternary"),
         "ternary": dict(color=TERN, marker="s", label="ternary")}

fig = plt.figure(figsize=(F.W, 4.3))
gs = fig.add_gridspec(1, 3, wspace=0.46, left=0.085, right=0.985, top=0.80,
                      bottom=0.17)

# --- (a) what each alloy can build -------------------------------------------
ax = fig.add_subplot(gs[0, 0])
req = S["requested_decades"]
got = [S["designs"][k]["tau_decades"] for k in KINDS]
xs = np.arange(len(KINDS))
ax.bar(xs, got, 0.54, color=[QUAT, TERN], zorder=3)
ax.axhline(req, color=F.INK, lw=1.4, ls="--", zorder=4)
ax.text(len(KINDS) - 0.42, req * 1.02, f"requested {req:.0f}", fontsize=8.3,
        color=F.INK, va="bottom", ha="right", fontweight="bold")
labels = []
for x, v, k in zip(xs, got, KINDS):
    spread = S["designs"][k]["ec_spread"]
    lab = "0" if spread < 1e-6 else f"{spread:.1f}"
    ax.text(x, v + 0.10, f"{v:.1f}", ha="center", fontsize=9,
            fontweight="bold", color=STYLE[k]["color"])
    labels.append(k + NL + "ΔE$_\\mathrm{c}$ = " + lab)
ax.set_xticks(xs)
ax.set_xticklabels(labels, fontsize=8.3)
ax.set_xlim(-0.62, len(KINDS) - 0.38)
ax.set_ylim(0, req * 1.30)
ax.set_ylabel(r"decades of $\tau$ built")
F.note(ax, r"$\Delta E_\mathrm{c}$ in MV cm$^{-1}$", "upper left")
F.heading(ax, "What the alloy can build",
          f"the ternary reaches {got[1]:.1f} of {req:.0f}", compact=True)
F.despine(ax)
F.panel_tag(ax, "a", dx=-0.30, dy=1.34)

# --- (b) capability against drive --------------------------------------------
ax = fig.add_subplot(gs[0, 1])
for k in KINDS:
    tbl = S["sweep"][k]
    b = sorted(float(x) for x in tbl)
    y = [tbl[f"{x:g}"]["nlmc_mean"] for x in b]
    e = [tbl[f"{x:g}"]["nlmc_std"] for x in b]
    ax.errorbar(b, y, yerr=e, color=STYLE[k]["color"], marker=STYLE[k]["marker"],
                ms=4.5, lw=1.8, elinewidth=1.0, capsize=2.5)
for k, dy in zip(KINDS, (9, -17)):
    v = S["best"][k]
    ax.plot([v["bias"]], [v["nlmc_mean"]], marker="*", ms=13,
            color=STYLE[k]["color"], zorder=5)
    ax.annotate(k, xy=(v["bias"], v["nlmc_mean"]),
                xytext=(0 if dy > 0 else -5, dy),
                textcoords="offset points", color=STYLE[k]["color"],
                fontsize=9, fontweight="bold",
                ha="center" if dy > 0 else "right")
ax.set_xscale("log")
ticks = [0.2, 0.5, 1.0, 2.0]
ax.xaxis.set_major_locator(FixedLocator(ticks))
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
ax.xaxis.set_minor_locator(FixedLocator([]))
ax.xaxis.set_minor_formatter(NullFormatter())
ax.set_xlabel(r"drive  ($|E|\,/\,\tilde{E}_\mathrm{c}$)")
ax.set_ylabel("nonlinear memory capacity")
lo, hi = ax.get_ylim()
ax.set_ylim(lo, hi + 0.24 * (hi - lo))
rd = S["designs"]["ternary"].get("switching_rate_decades")
if rd:
    F.note(ax, f"stars mark the best drive{NL}ternary rate spread "
               f"{rd:.1f} dec", "upper left")
adv = S["quaternary_advantage_pct"]
F.heading(ax, "Each at its own best drive",
          f"the quaternary still leads by {adv:.0f}%", compact=True)
F.despine(ax)
F.panel_tag(ax, "b", dx=-0.30, dy=1.34)

# --- (c) temperature ----------------------------------------------------------
ax = fig.add_subplot(gs[0, 2])
drifts = {}
for k in KINDS:
    vals = S["temperature"][k]["values"]
    t = sorted(float(x) for x in vals)
    y = [vals[str(x)] for x in t]
    ax.plot(t, y, color=STYLE[k]["color"], marker=STYLE[k]["marker"], ms=4.5,
            lw=1.8)
    drifts[k] = S["temperature"][k]["rel_drift_pct"]
    i = 1
    up = k == "ternary"
    ax.annotate(k, xy=(t[i], y[i]), xytext=(0, 7 if up else -7),
                textcoords="offset points", color=STYLE[k]["color"],
                fontsize=9, fontweight="bold", ha="center",
                va="bottom" if up else "top")
ax.axvline(300, color=F.AXIS, lw=1.2, ls=":", zorder=0)
ax.text(300, 0.02, " 300 K", transform=ax.get_xaxis_transform(), fontsize=8.3,
        color=F.MUTED, va="bottom")
ax.set_xlabel("temperature  (K)")
ax.set_ylabel("nonlinear memory capacity")
ax.set_xlim(270, 334)
F.note(ax, f"drift over 275-325 K:{NL}"
           f"{drifts['quaternary']:.0f}% vs {drifts['ternary']:.0f}%",
       "lower left")
ratio = drifts["ternary"] / drifts["quaternary"]
F.heading(ax, "Where the substitution fails",
          f"the ternary drifts {ratio:.0f}x more", compact=True)
F.despine(ax)
F.panel_tag(ax, "c", dx=-0.30, dy=1.34)

os.makedirs(C.FIG_DIR, exist_ok=True)
for ext in ("pdf", "png"):
    fig.savefig(os.path.join(C.FIG_DIR, f"fig6_ternary.{ext}"))
print("wrote fig6")
for k in KINDS:
    d = S["designs"][k]
    t = S["temperature"][k]
    print(f"  {k:>12}: {d['tau_decades']:.2f} of {req:.2f} requested decades, "
          f"Ec spread {d['ec_spread']:.3g} MV/cm, "
          f"rate spread {d.get('switching_rate_decades', float('nan')):.1f} dec, "
          f"NL-MC {S['best'][k]['nlmc_mean']:.3f} at bias {S['best'][k]['bias']:g}, "
          f"temperature drift {t['rel_drift_pct']:.1f}%")
print(f"  quaternary advantage {adv:.1f}%, drift ratio {ratio:.1f}x")
