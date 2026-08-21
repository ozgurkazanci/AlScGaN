"""Figure 2: what the device does, and the two conditions it must satisfy."""

import json
import os
import sys

import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C
import figstyle as F

F.use_style()

d = np.load(os.path.join(C.OUT_DIR, "device_char.npz"), allow_pickle=True)
with open(os.path.join(C.OUT_DIR, "device_summary.json"),
          encoding="utf-8") as fh:
    S = json.load(fh)

SPREAD = F.DESIGN["graded"]
REF = F.DESIGN["homogeneous"]
UNIF = F.DESIGN["uniform"]

fig = plt.figure(figsize=F.SIZE_3x2)
gs = fig.add_gridspec(3, 2, hspace=0.78, wspace=0.34,
                      left=0.10, right=0.965, top=0.925, bottom=0.055)

# --- (a) P-E loops -----------------------------------------------------------
ax = fig.add_subplot(gs[0, 0])
amps = list(d["pe_amps"])
for a, alpha in zip([x for x in amps if x in (1.0, 1.4, 2.0)],
                    (0.35, 0.62, 1.0)):
    ax.plot(d[f"pe_graded_{a}_e"], d[f"pe_graded_{a}_p"],
            color=SPREAD["color"], lw=1.5, alpha=alpha)
    ax.plot(d[f"pe_uniform_{a}_e"], d[f"pe_uniform_{a}_p"],
            color=REF["color"], lw=1.5, alpha=alpha)
ax.axhline(0, color=F.AXIS, lw=0.8, zorder=0)
ax.axvline(0, color=F.AXIS, lw=0.8, zorder=0)
ax.set_ylim(-152, 122)
ax.plot([], [], color=SPREAD["color"], lw=2, label="composition spread")
ax.plot([], [], color=REF["color"], lw=2, label="single composition")
F.legend(ax, loc="upper left")
ax.set_xlabel(r"applied field  (MV cm$^{-1}$)")
ax.set_ylabel(r"$P$  ($\mu$C cm$^{-2}$)")
ax.text(0.97, 0.06, "three amplitudes:\n1.0, 1.4, 2.0 $E_\\mathrm{c}$",
        transform=ax.transAxes, fontsize=8.3, color=F.MUTED, ha="right",
        va="center", linespacing=1.35)
F.heading(ax, "Polarization-field loops at 100 Hz",
          "both pads switch fully; the loops look alike")
F.panel_tag(ax, "a")

# --- (b) retention -----------------------------------------------------------
ax = fig.add_subplot(gs[0, 1])
t = d["ret_t"]
ax.semilogx(t, d["ret_graded"], color=SPREAD["color"], lw=2.2)
ax.semilogx(t, d["ret_uniform"], color=REF["color"], lw=2.2)
i = len(t) // 3
F.direct_label(ax, t[i], d["ret_graded"][i], "spread", SPREAD["color"],
               dx=4, dy=12)
F.direct_label(ax, t[i], d["ret_uniform"][i], "single", REF["color"],
               dx=-4, dy=-12, ha="right")
ax.axhline(0.5, color=F.AXIS, lw=0.8, ls=":", zorder=0)
ax.set_xlabel("time after poling  (s)")
ax.set_ylabel(r"$P(t)\,/\,P(0)$")
ax.set_ylim(-0.03, 1.05)
th = S["retention"]["graded"]["t_half"]
tu = S["retention"]["uniform"]["t_half"]
F.note(ax, f"half-lives almost equal:\n{th:.2f} s and {tu:.2f} s",
       "upper right")
F.heading(ax, "Polarization decay after poling",
          "the spread decays gradually, the single one abruptly")
F.panel_tag(ax, "b")

# --- (c) the designed spectra ------------------------------------------------
ax = fig.add_subplot(gs[1, 0])
rows = [("tau_graded", SPREAD, 2, "composition spread"),
        ("tau_homogeneous", REF, 1, "one $\\tau$ per pad"),
        ("tau_uniform", UNIF, 0, "single $\\tau$")]
for key, cfg, ypos, lab in rows:
    if key not in d:
        continue
    taus = np.asarray(d[key])
    ax.plot(taus, np.full_like(taus, ypos), marker="|", ms=15, lw=0,
            color=cfg["color"], markeredgewidth=1.6)
    ax.text(taus.min() * 0.6, ypos + 0.30, lab, color=cfg["color"],
            fontsize=9, fontweight="bold", va="bottom")
ax.set_xscale("log")
ax.set_yticks([])
ax.set_ylim(-0.55, 3.0)
ax.set_xlabel(r"$\tau$ carried by each design  (s)")
F.despine(ax, keep=("bottom",))
F.heading(ax, "Time constants each design contains",
          "every tick is one composition segment")
F.panel_tag(ax, "c")

# --- (d) drive regime --------------------------------------------------------
reg = d["regime"]
bias, r_sw, sw_per, leak_frac, nlmc, mc, nrmse, rank = \
    [reg[:, i] for i in range(8)]

ax = fig.add_subplot(gs[1, 1])
ax.semilogy(bias, r_sw, color=F.INK, lw=2.2, marker="o", ms=4.5)
tau_lo, tau_hi = S["window"]["tau_lo"], S["window"]["tau_hi"]
ax.axhspan(1 / tau_hi, 1 / tau_lo, color=F.BLUE, alpha=0.16, zorder=0)
ax.text(bias[0] + 0.005, np.sqrt((1 / tau_hi) * (1 / tau_lo)),
        "relaxation rates\nspanned by the array", color=F.BLUE, fontsize=8.8,
        fontweight="bold", va="center", linespacing=1.35)
# mark the drive the paper actually uses, not this scan's argmax: the
# scan is flat across 0.60-0.70 so its argmax is not meaningful
with open(os.path.join(C.OUT_DIR, "operating_points.json"),
          encoding="utf-8") as fh:
    best_bias = float(json.load(fh)["graded"]["bias"])
ax.axvline(best_bias, color=F.ORANGE, lw=1.8, ls="--", zorder=1)
ax.text(best_bias + 0.01, r_sw.max() * 0.2,
        f"selected drive\n{best_bias:.2f} $E_\\mathrm{{c}}$", color=F.ORANGE,
        fontsize=8.8, fontweight="bold", linespacing=1.35)
ax.set_xlabel(r"drive amplitude  ($|E|\,/\,E_\mathrm{c}$)")
ax.set_ylabel(r"switching rate  (s$^{-1}$)")
ax.set_ylim(top=r_sw.max() * 40)
# leak fraction AT the marked drive, not at the scan argmax
frac = float(leak_frac[int(np.argmin(np.abs(bias - best_bias)))])
F.heading(ax, "Switching rate against drive amplitude",
          f"at the chosen drive, {frac*100:.0f}% of segments still forget by leakage")
F.despine(ax)
F.panel_tag(ax, "d")

# --- (e) feedback loop gain --------------------------------------------------
ax = fig.add_subplot(gs[2, 0])
fb = d["feedback"]
g, cap = fb[:, 0], fb[:, 1]
pos = g > 0
ax.plot(g[pos], cap[pos], color=F.BLUE, marker="o", ms=5, lw=2.2)
open_loop = S["feedback"]["open_loop_nlmc"]
ax.axhline(open_loop, color=F.MUTED, lw=1.4, ls=":")
ax.text(g[pos].min(), open_loop + 0.08, "loop open", color=F.INK2,
        fontsize=9, va="bottom")
win = S["feedback"].get("stable_window")
if win:
    ax.axvspan(win[0], win[1], color=F.BLUE, alpha=0.13, zorder=0)
    ax.text(np.sqrt(win[0] * win[1]), open_loop * 0.50, "usable\nwindow",
            color=F.BLUE, fontsize=8.8, fontweight="bold", ha="center",
            va="center", linespacing=1.35)
ax.set_xscale("log")
ax.set_xlabel("feedback loop gain")
ax.set_ylabel("nonlinear memory capacity")
ax.set_ylim(-0.25, cap.max() * 1.22)
F.heading(ax, "Nonlinear memory vs feedback gain",
          f"capacity {open_loop:.1f} open, {S['feedback']['best_nlmc']:.1f} closed, then collapse")
F.despine(ax)
F.panel_tag(ax, "e")

# --- (f) linear memory against delay -----------------------------------------
ax = fig.add_subplot(gs[2, 1])
D_SHOW = 12
for label, cfg in (("graded", SPREAD), ("homogeneous", REF),
                   ("uniform", UNIF)):
    key = f"mcd_{label}"
    if key not in d:
        continue
    prof = np.asarray(d[key])
    ax.plot(np.arange(1, len(prof)), prof[1:], color=cfg["color"],
            marker=cfg["marker"], ms=4.5, lw=1.8, label=cfg["label"])
thresh = S["mc_profile"]["graded"].get("per_delay_threshold")
if thresh:
    ax.axhline(thresh, color=F.MUTED, lw=1.2, ls=":")
    ax.text(D_SHOW, thresh + 0.035, "noise floor", fontsize=8.8,
            color=F.MUTED, ha="right")
ax.set_xlim(0.4, D_SHOW)
ax.set_ylim(-0.04, 1.06)
ax.set_xlabel(r"delay  $d$  (input samples)")
ax.set_ylabel(r"$r^2$ of recalling $u(k\!-\!d)$")
F.legend(ax, loc="upper right")
mg = S["mc_profile"]["graded"]["mc"]
mu = S["mc_profile"]["uniform"]["mc"]
F.heading(ax, "How far back the array recalls the input",
          f"summed over delays: {mg:.1f} for the spread, {mu:.1f} for one $\\tau$")
F.despine(ax)
F.panel_tag(ax, "f")

os.makedirs(C.FIG_DIR, exist_ok=True)
for ext in ("pdf", "png"):
    fig.savefig(os.path.join(C.FIG_DIR, f"fig2_device.{ext}"))
print(f"wrote fig2  (bias {best_bias:.2f}, {frac*100:.0f}% leakage-dominated; "
      f"loop {open_loop:.2f} -> {S['feedback']['best_nlmc']:.2f}; "
      f"linear MC {mg:.2f} vs {mu:.2f})")
