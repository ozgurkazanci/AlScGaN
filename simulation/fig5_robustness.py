"""Figure 5: robustness of the design rule, and the numerical checks.

(a) temperature - the whole spectrum slides about one decade per 21 K, and
    this is where a wide spectrum earns its keep
(b) spectral span - how many decades are actually needed
(c) discrete time-constant ladders against the continuum
(d) convergence in segments resolved per pad
(e) convergence in virtual nodes per pad
(f) sensitivity to bandgap bowing in the alloy model

(d) and (e) were one panel in an earlier version, sharing an axis labelled
"count". Segments per pad and virtual nodes per pad are different quantities
that happen to be counted, so they now get one panel each.
"""

import json
import os
import sys

import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C
import figstyle as F

F.use_style()

with open(os.path.join(C.OUT_DIR, "robustness.json"), encoding="utf-8") as fh:
    S = json.load(fh)

DESIGNS = ("graded", "homogeneous", "uniform")

fig = plt.figure(figsize=F.SIZE_3x2)
gs = fig.add_gridspec(3, 2, hspace=0.78, wspace=0.34,
                      left=0.105, right=0.965, top=0.925, bottom=0.055)


def converged(xs, ys, tol=0.05):
    """Smallest x whose capacity is within tol of the largest run."""
    ref = ys[-1]
    for x, y in zip(xs, ys):
        if abs(y - ref) <= tol * abs(ref):
            return x
    return xs[-1]


# --- (a) temperature ---------------------------------------------------------
ax = fig.add_subplot(gs[0, 0])
temps = sorted({float(k.split("|")[1]) for k in S["temperature"]})
for design in DESIGNS:
    cfg = F.DESIGN[design]
    ys = [S["temperature"][f"{design}|{t}"]["nlmc_mean"] for t in temps]
    es = [S["temperature"][f"{design}|{t}"]["nlmc_std"] for t in temps]
    ax.errorbar(temps, ys, yerr=es, color=cfg["color"], marker=cfg["marker"],
                ms=5, lw=1.8, elinewidth=1.0, capsize=2.5, label=cfg["label"])
ax.axvline(300, color=F.AXIS, lw=1.2, ls=":", zorder=0)
lo, hi = ax.get_ylim()
ax.set_ylim(lo, hi + 0.12 * (hi - lo))
ax.text(300, 0.97, " 300 K", transform=ax.get_xaxis_transform(),
        fontsize=8.8, color=F.MUTED, va="top")
ax.set_xlabel("temperature  (K)")
ax.set_ylabel("nonlinear memory capacity")
F.legend(ax, loc="lower right", fontsize=8.3)
drift = S.get("temperature_drift", {})
dg = drift.get("graded", {}).get("rel_drift_pct", float("nan"))
du = drift.get("uniform", {}).get("rel_drift_pct", float("nan"))
F.heading(ax, "Capacity against ambient temperature",
          f"over 275-325 K the spread drifts {dg:.0f}%, one $\\tau$ {du:.0f}%")
F.despine(ax)
F.panel_tag(ax, "a")

# --- (b) spectral span -------------------------------------------------------
ax = fig.add_subplot(gs[0, 1])
spans = sorted(float(k) for k in S["span"])
ys = [S["span"][str(s)]["nlmc_mean"] for s in spans]
es = [S["span"][str(s)]["nlmc_std"] for s in spans]
ax.errorbar(spans, ys, yerr=es, color=F.BLUE, marker="o", ms=5, lw=1.8,
            elinewidth=1.0, capsize=2.5)
best = spans[int(np.argmax(ys))]
ax.axvline(best, color=F.ORANGE, lw=1.6, ls="--", zorder=1)
ax.annotate(f"best: {best:g} decades", xy=(best, min(ys)), xytext=(7, 0),
            textcoords="offset points", color=F.ORANGE, fontsize=9,
            fontweight="bold", ha="left", va="bottom")
ax.set_xlabel(r"designed span of $\tau$  (decades)")
ax.set_ylabel("nonlinear memory capacity")
F.heading(ax, "How wide a spectrum pays",
          f"capacity rises to {best:g} decades, then stops improving")
F.despine(ax)
F.panel_tag(ax, "b")

# --- (c) discrete ladders ----------------------------------------------------
ax = fig.add_subplot(gs[1, 0])
levels = sorted(int(k) for k in S["ladder"])
ys = [S["ladder"][str(n)]["nlmc_mean"] for n in levels]
es = [S["ladder"][str(n)]["nlmc_std"] for n in levels]
cont = S["ladder_vs_continuum"]["continuum_nlmc"]
ax.axhline(cont, color=F.ORANGE, lw=1.8, ls="--", zorder=2)
ax.errorbar(levels, ys, yerr=es, color=F.BLUE, marker="o", ms=5, lw=1.8,
            elinewidth=1.0, capsize=2.5, zorder=3)
ax.text(levels[0], cont, "continuous spread ", color=F.ORANGE, fontsize=9,
        fontweight="bold", va="bottom", ha="left")
n_enough = converged(levels, ys)
ax.set_xscale("log", base=2)
ax.set_xticks(levels)
ax.set_xticklabels([str(n) for n in levels])
ax.set_xlabel("distinct time constants in the array")
ax.set_ylabel("nonlinear memory capacity")
F.heading(ax, "How much of the spectrum is needed",
          f"{n_enough} distinct time constants already match it")
F.despine(ax)
F.panel_tag(ax, "c")

# --- (d) convergence in segments per pad -------------------------------------
ax = fig.add_subplot(gs[1, 1])
segs = sorted({int(k.split("|")[0]) for k in S["n_seg"]})
xs = [n for n in segs if f"{n}|{C.M_VIRTUAL}" in S["n_seg"]]
ys = [S["n_seg"][f"{n}|{C.M_VIRTUAL}"]["nlmc_mean"] for n in xs]
es = [S["n_seg"][f"{n}|{C.M_VIRTUAL}"]["nlmc_std"] for n in xs]
ax.errorbar(xs, ys, yerr=es, color=F.BLUE, marker="o", ms=5, lw=1.8,
            elinewidth=1.0, capsize=2.5)
n_seg_ok = converged(xs, ys)
ax.axvline(C.N_SEG, color=F.INK2, lw=1.4, ls="--", zorder=1)
ax.text(C.N_SEG * 1.12, 0.06, f"used: {C.N_SEG}",
        transform=ax.get_xaxis_transform(), fontsize=8.8, color=F.INK2,
        fontweight="bold", va="bottom")
ax.set_xscale("log", base=2)
ax.set_xticks(xs)
ax.set_xticklabels([str(t) for t in xs])
ax.set_xlabel("composition segments resolved per pad")
ax.set_ylabel("nonlinear memory capacity")
F.heading(ax, "Convergence: segments per pad",
          f"settled by {n_seg_ok} segments; the runs use {C.N_SEG}")
F.despine(ax)
F.panel_tag(ax, "d")

# --- (e) convergence in virtual nodes ----------------------------------------
ax = fig.add_subplot(gs[2, 0])
mvs = sorted({int(k.split("|")[1]) for k in S["m_virtual"]})
xs2 = [m for m in mvs if f"{C.N_SEG}|{m}" in S["m_virtual"]]
ys2 = [S["m_virtual"][f"{C.N_SEG}|{m}"]["nlmc_mean"] for m in xs2]
es2 = [S["m_virtual"][f"{C.N_SEG}|{m}"]["nlmc_std"] for m in xs2]
ax.errorbar(xs2, ys2, yerr=es2, color=F.BLUE, marker="o", ms=5, lw=1.8,
            elinewidth=1.0, capsize=2.5)
m_ok = converged(xs2, ys2)
ax.axvline(C.M_VIRTUAL, color=F.INK2, lw=1.4, ls="--", zorder=1)
ax.text(C.M_VIRTUAL * 1.08, 0.06, f"used: {C.M_VIRTUAL}",
        transform=ax.get_xaxis_transform(), fontsize=8.8, color=F.INK2,
        fontweight="bold", va="bottom")
ax.set_xscale("log", base=2)
ax.set_xticks(xs2)
ax.set_xticklabels([str(t) for t in xs2])
ax.set_xlabel("virtual nodes per pad")
ax.set_ylabel("nonlinear memory capacity")
F.heading(ax, "Convergence: virtual nodes per pad",
          f"settled by {m_ok} nodes; the runs use {C.M_VIRTUAL}")
F.despine(ax)
F.panel_tag(ax, "e")

# --- (f) bandgap bowing ------------------------------------------------------
ax = fig.add_subplot(gs[2, 1])
xs3 = np.arange(len(DESIGNS))
w = 0.36
lin = [S["bowing"][f"{d}|linear"]["nlmc_mean"] for d in DESIGNS]
bow = [S["bowing"][f"{d}|bowed"]["nlmc_mean"] for d in DESIGNS]
lin_e = [S["bowing"][f"{d}|linear"]["nlmc_std"] for d in DESIGNS]
bow_e = [S["bowing"][f"{d}|bowed"]["nlmc_std"] for d in DESIGNS]
ax.bar(xs3 - w / 2 - 0.012, lin, w, yerr=lin_e, color=F.BLUE, zorder=3,
       ecolor=F.INK2, error_kw=dict(lw=1.0), label="linear bandgap")
ax.bar(xs3 + w / 2 + 0.012, bow, w, yerr=bow_e, color=F.AQUA, zorder=3,
       ecolor=F.INK2, error_kw=dict(lw=1.0), label="with bowing")
worst = max(abs(b - a) / a * 100 for a, b in zip(lin, bow))
ax.set_xticks(xs3)
NL = chr(10)
ax.set_xticklabels(["composition" + NL + "spread",
                    "one τ" + NL + "per pad", "single τ"],
                   fontsize=8.8)
ax.set_ylabel("nonlinear memory capacity")
lo, hi = ax.get_ylim()
ax.set_ylim(lo, hi + 0.26 * (hi - lo))
F.legend(ax, loc="upper right", fontsize=8.3)
F.heading(ax, "Sensitivity to bandgap bowing",
          f"bowing moves capacity by at most {worst:.1f}%")
F.despine(ax)
F.panel_tag(ax, "f")

os.makedirs(C.FIG_DIR, exist_ok=True)
for ext in ("pdf", "png"):
    fig.savefig(os.path.join(C.FIG_DIR, f"fig5_robustness.{ext}"))
print("wrote fig5")
for d_, v in S.get("temperature_drift", {}).items():
    print(f"  {d_:>12}: NL-MC(300 K) = {v['nlmc_300k']:.3f}, "
          f"drift over 275-325 K = {v['rel_drift_pct']:.1f}%")
for d_ in DESIGNS:
    a = S["bowing"][f"{d_}|linear"]["nlmc_mean"]
    b = S["bowing"][f"{d_}|bowed"]["nlmc_mean"]
    print(f"  {d_:>12}: bowing shifts NL-MC {a:.3f} -> {b:.3f} "
          f"({(b - a) / a * 100:+.1f}%)")
print(f"  converged: {n_seg_ok} segments/pad, {m_ok} virtual nodes/pad, "
      f"{n_enough} distinct time constants")
