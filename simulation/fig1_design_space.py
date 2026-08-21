"""Figure 1: the composition design space and the decoupling it enables."""

import json
import os
import sys

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import LogFormatterMathtext

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C
import figstyle as F

F.use_style()

d = np.load(os.path.join(C.OUT_DIR, "material_maps.npz"))
with open(os.path.join(C.OUT_DIR, "material_summary.json"), encoding="utf-8") as fh:
    S = json.load(fh)

fig = plt.figure(figsize=F.SIZE_2x2)
gs = fig.add_gridspec(2, 2, hspace=0.62, wspace=0.42,
                      left=0.095, right=0.955, top=0.88, bottom=0.085)

x, y = d["plane_x"], d["plane_y"]
XX, YY = np.meshgrid(x, y)
targets = d["ec_targets"]
EC = C.EC_TARGET


def mark_forbidden(ax):
    xf = np.linspace(0, 0.75, 200)
    edge = np.clip(0.98 - xf, 0.10, 0.45)
    ax.fill_between(xf, edge, 0.45, color="#f0efec", zorder=2, lw=0)
    ax.plot(xf, edge, color=F.MUTED, lw=0.8, zorder=3)
    ax.text(0.735, 0.437, "Al < 2%", fontsize=8.3, color=F.MUTED, ha="right",
            va="top", zorder=4)


def cation_axes(ax):
    ax.set_xlabel("Ga cation fraction  $x$")
    ax.set_ylabel("Sc cation fraction  $y$")
    ax.set_xlim(0, 0.75)
    ax.set_ylim(0.10, 0.45)
    ax.grid(False)


# --- (a) coercive field ------------------------------------------------------
ax = fig.add_subplot(gs[0, 0])
im = ax.contourf(XX, YY, d["plane_ec"], levels=np.arange(0, 9.1, 0.75),
                 cmap=F.SEQ, extend="both")
cs = ax.contour(XX, YY, d["plane_ec"], levels=[2.0, 2.7, 3.4], colors=F.INK,
                linewidths=1.1)
ax.clabel(cs, fmt="%.1f", fontsize=8.3, inline=True,
          manual=[(0.20, 0.381), (0.20, 0.349), (0.20, 0.320)])
mark_forbidden(ax)
cb = fig.colorbar(im, ax=ax, pad=0.03, fraction=0.05,
                  ticks=[0, 3, 6, 9])
cb.set_label(r"$E_\mathrm{c}$ (MV cm$^{-1}$)", fontsize=9)
cb.ax.tick_params(labelsize=8.3)
cb.outline.set_visible(False)
cation_axes(ax)
F.heading(ax, r"Coercive field over the cation plane",
          "contours run horizontally: $E_\\mathrm{c}$ follows Sc only")
F.panel_tag(ax, "a")

# --- (b) time constant with the iso-Ec line ----------------------------------
ax = fig.add_subplot(gs[0, 1])
tau = np.log10(d["plane_tau"])
im = ax.contourf(XX, YY, tau, levels=np.arange(-4, 9.1, 1.0), cmap=F.SEQ,
                 extend="both")
LAB_ROW = int(np.argmin(np.abs(y - 0.155)))
prof = tau[LAB_ROW, :]
TAU_LEVELS, TAU_LABEL_POS = [], []
for lv in (-2, 0, 2, 4):
    if prof.min() + 0.15 <= lv <= prof.max() - 0.15:
        TAU_LEVELS.append(lv)
        TAU_LABEL_POS.append(
            (float(np.interp(lv, prof[::-1], x[::-1])), float(y[LAB_ROW])))
cs = ax.contour(XX, YY, tau, levels=TAU_LEVELS, colors=F.INK,
                linewidths=0.9, alpha=0.6, linestyles="solid")
ax.clabel(cs, fmt=r"$10^{%d}$", fontsize=8.3, inline=True,
          manual=TAU_LABEL_POS)
ax.plot(d[f"iso{EC}_x"], d[f"iso{EC}_y"], color=F.ORANGE, lw=2.4, zorder=5)
ax.text(0.30, 0.378, rf"iso-$E_\mathrm{{c}}$ = {EC} MV cm$^{{-1}}$",
        color=F.ORANGE, fontsize=8.8, fontweight="bold", zorder=6)
mark_forbidden(ax)
cb = fig.colorbar(im, ax=ax, pad=0.03, fraction=0.05, ticks=[-4, 0, 4, 8])
cb.set_label(r"$\log_{10}(\tau\,/\,\mathrm{s})$", fontsize=9)
cb.ax.tick_params(labelsize=8.3)
cb.outline.set_visible(False)
cation_axes(ax)
F.heading(ax, "Relaxation time over the same plane",
          "diagonal contours: they cross the iso-$E_\\mathrm{c}$ line")
F.panel_tag(ax, "b")

# --- (c) tau along iso-Ec ----------------------------------------------------
ax = fig.add_subplot(gs[1, 0])
shades = [F.SEQ(v) for v in np.linspace(0.32, 0.95, len(targets))]
label_at = np.linspace(0.26, 0.62, len(targets))
for t, col, xl in zip(targets, shades, label_at):
    xt, tt = d[f"iso{t}_x"], d[f"iso{t}_tau"]
    ax.semilogy(xt, tt, color=col, lw=2.0)
    yl = float(np.interp(xl, xt, np.log10(tt)))
    ax.annotate(f"{t:.1f}", xy=(xl, 10 ** yl), xytext=(0, 9),
                textcoords="offset points", color=col, fontsize=8.8,
                fontweight="bold", ha="center", va="bottom",
                bbox=dict(boxstyle="round,pad=0.15", fc=F.SURFACE, ec="none",
                          alpha=0.9))
q = S["quaternary_decades_at_zero_tolerance"]
ax.set_xlabel(r"Ga cation fraction  $x$  along an iso-$E_\mathrm{c}$ line")
ax.set_ylabel(r"$\tau$  (s)")
ax.set_xlim(-0.02, 0.72)
ax.yaxis.set_major_formatter(LogFormatterMathtext())
F.despine(ax)
F.note(ax, r"curve labels: $E_\mathrm{c}$ in MV cm$^{-1}$", "lower left")
F.heading(ax, "Time constant along a fixed coercive field",
          f"{q:.1f} decades of $\\tau$ while $E_\\mathrm{{c}}$ never moves")
F.panel_tag(ax, "c")

# --- (d) decades within a tolerance band -------------------------------------
ax = fig.add_subplot(gs[1, 1])
tols = [0.01, 0.02, 0.05, 0.10]
keys = [f"{t:.0%}" for t in tols]
alsc = [S["ternary"]["AlScN"]["decades_within_tolerance"][k] for k in keys]
scga = [S["ternary"]["ScGaN"]["decades_within_tolerance"][k] for k in keys]
xs = np.arange(len(tols))
w = 0.36
ax.bar(xs - w / 2 - 0.015, alsc, w, color=F.ORANGE, zorder=3,
       label="AlScN (ternary)")
ax.bar(xs + w / 2 + 0.015, scga, w, color=F.AQUA, zorder=3,
       label="ScGaN (ternary)")
ax.axhline(q, color=F.BLUE, lw=2.4, zorder=4)
ax.text(3.45, q * 0.58, f"quaternary: {q:.1f} decades\nat any tolerance",
        color=F.BLUE, fontsize=9, fontweight="bold", ha="right", va="top",
        linespacing=1.4)
for xi, v in zip(xs - w / 2 - 0.015, alsc):
    ax.text(xi, v * 1.32, f"{v:.2f}", ha="center", fontsize=8.3,
            color=F.ORANGE, fontweight="bold")
for xi, v in zip(xs + w / 2 + 0.015, scga):
    ax.text(xi, v * 1.32, f"{v:.2f}", ha="center", fontsize=8.3,
            color=F.AQUA, fontweight="bold")
ax.set_yscale("log")
ax.set_ylim(5e-3, 45)
ax.set_xlim(-0.55, 3.55)
ax.set_xticks(xs)
ax.set_xticklabels([f"±{int(t*100)}%" for t in tols])
ax.set_xlabel(r"tolerance allowed on $E_\mathrm{c}$ across the array")
ax.set_ylabel(r"decades of $\tau$ reachable")
F.legend(ax, loc="upper left")
F.despine(ax)
F.heading(ax, "What one shared drive line permits",
          f"the quaternary reaches {q/alsc[2]:.0f}x further at ±5%")
F.panel_tag(ax, "d")

os.makedirs(C.FIG_DIR, exist_ok=True)
for ext in ("pdf", "png"):
    fig.savefig(os.path.join(C.FIG_DIR, f"fig1_design_space.{ext}"))
print(f"wrote fig1  ({q:.2f} decades vs AlScN {alsc[2]:.3f} / ScGaN {scga[2]:.3f} at ±5%)")
