"""Figure 4: reproducibility, and the two prices the readout charges.

(a) accuracy against transferability. An unregularized readout is the most
    accurate on the device it was fitted to and worthless on any other,
    because the state matrix carries far fewer independent directions than
    columns. Regularization buys transfer at a stated cost in accuracy.
(b) readout transfer penalty against deposition tolerance, with the
    fabrication budget marked - the deposition scatter beyond which a
    designed spectrum is no more transferable than a random one.
(c) the design advantage against readout precision. This is the binding
    experimental requirement: the same ill-conditioning that makes the readout
    hard to transfer also makes it lean on small signals.
(d) capacity against readout precision at several levels of cycle-to-cycle
    switching jitter.
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

with open(os.path.join(C.OUT_DIR, "reproducibility.json"),
          encoding="utf-8") as fh:
    S = json.load(fh)

SIGMAS = sorted(float(k) for k in S["sigma_sweep"])
ARMS = ["graded", "stochastic", "homogeneous"]
LAM_STAR = S["lam_transfer"]
SPEC = S.get("noise_spec", {})

fig = plt.figure(figsize=F.SIZE_2x2)
gs = fig.add_gridspec(2, 2, hspace=0.66, wspace=0.36,
                      left=0.105, right=0.965, top=0.895, bottom=0.085)


def pull(arm, field):
    return np.array([S["sigma_sweep"][str(s)].get(arm, {}).get(field, np.nan)
                     for s in SIGMAS])


# --- (a) accuracy versus transferability -------------------------------------
ax = fig.add_subplot(gs[0, 0])
rows = S["lambda_tradeoff"]["graded"]
lams = sorted(float(k) for k in rows)
own = np.array([rows[f"{l:g}"]["own"] for l in lams])
tra = np.array([rows[f"{l:g}"]["transfer"] for l in lams])
ax.plot(lams, own, color=F.BLUE, marker="o", ms=4.5, lw=1.8)
ax.plot(lams, tra, color=F.ORANGE, marker="s", ms=4.5, lw=1.8)
F.direct_label(ax, lams[1], own[1], "on its own device", F.BLUE, dx=6, dy=13)
F.direct_label(ax, lams[1], tra[1], "on another device", F.ORANGE, dx=6, dy=11)
ax.axvline(LAM_STAR, color=F.INK2, lw=1.4, ls="--", zorder=1)
ax.text(LAM_STAR * 1.5, 0.40, f"selected\n$\\lambda$ = {LAM_STAR:g}",
        transform=ax.get_xaxis_transform(), fontsize=8.8, color=F.INK2,
        fontweight="bold", va="center", linespacing=1.35)
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel(r"ridge regularization  $\lambda$")
ax.set_ylabel("NARMA-10 error  (NRMSE)")
i_star = int(np.argmin(np.abs(np.array(lams) - LAM_STAR)))
F.heading(ax, "What a transferable readout costs",
          "the two curves meet only once the readout is damped")
F.despine(ax)
F.panel_tag(ax, "a")

# --- (b) transfer penalty and the fabrication budget -------------------------
ax = fig.add_subplot(gs[0, 1])
XB = list(range(len(SIGMAS)))
i_ss = SIGMAS.index(S["sigma_star"]) if S.get("sigma_star") else None
for arm in ARMS:
    cfg = F.DESIGN[arm]
    ax.plot(XB, pull(arm, "transfer_penalty"), color=cfg["color"],
            marker=cfg["marker"], ms=5, lw=1.8, label=cfg["label"])
ax.axhline(0, color=F.AXIS, lw=1.0, zorder=0)
ss = S.get("sigma_star")
if ss:
    ax.axvspan(i_ss, XB[-1] + 0.4, color=F.MUTED, alpha=0.13, zorder=0)
    ax.axvline(i_ss, color=F.INK2, lw=1.4, ls="--", zorder=1)
    ax.text(i_ss + 0.15, 0.62, f"no advantage\nbeyond {ss:g}",
            transform=ax.get_xaxis_transform(), fontsize=8.8, color=F.INK2,
            va="center", fontweight="bold", linespacing=1.35)
ax.set_xlabel(r"deposition tolerance  $\sigma$  (cation fraction)")
ax.set_xticks(XB)
ax.set_xlim(-0.4, XB[-1] + 0.4)
ax.set_xticklabels([f"{s:g}" for s in SIGMAS])
ax.set_ylabel("error added by transfer  (NRMSE)")
lo, hi = ax.get_ylim()
ax.set_ylim(lo, hi + 0.52 * (hi - lo))
F.legend(ax, loc="upper left", fontsize=8.3)
F.heading(ax, f"One readout, many devices",
          f"the designed spread stays transferable to $\\sigma$ = {ss:g}")
F.despine(ax)
F.panel_tag(ax, "b")

# --- (c) the binding requirement: readout precision --------------------------
ax = fig.add_subplot(gs[1, 0])
gap = SPEC.get("advantage_vs_snr", {})
snrs = sorted(float(k) for k in gap if k != "inf")
vals = np.array([gap[f"{s:g}"] for s in snrs])
resolvable = [s for s, v in zip(snrs, vals) if v > 0.05]
edge = min(resolvable) if resolvable else None
if edge is not None:
    ax.axvspan(min(snrs) - 4, edge, color=F.MUTED, alpha=0.13, zorder=0)
ax.plot(snrs, vals, color=F.BLUE, marker="o", ms=5, lw=1.8, zorder=3)
if "inf" in gap:
    ax.axhline(gap["inf"], color=F.INK2, lw=1.2, ls=":", zorder=1)
    ax.text(max(snrs), gap["inf"] * 1.06, "noiseless readout", color=F.INK2,
            fontsize=8.8, va="bottom", ha="right")
ax.axhline(0, color=F.AXIS, lw=1.0, zorder=2)
ax.set_xlabel("readout signal-to-noise ratio  (dB)")
ax.set_ylabel("capacity advantage of the spread")
if edge is not None:
    lo = min(snrs) - 4
    ax.text(0.5 * (lo + edge), max(vals) * 0.55, "advantage not\nresolvable",
            fontsize=8.8, color=F.INK2, fontweight="bold", ha="center",
            va="center", linespacing=1.35)
    ax.annotate(f"{edge:g} dB", xy=(edge, 0), xytext=(4, 14),
                textcoords="offset points", color=F.BLUE, fontsize=9,
                fontweight="bold")
F.heading(ax, "The binding experimental requirement",
          f"below {edge:g} dB the two designs cannot be told apart")
F.despine(ax)
F.panel_tag(ax, "c")

# --- (d) capacity against readout precision ----------------------------------
ax = fig.add_subplot(gs[1, 1])
tbl = SPEC.get("table", {})
jitters = sorted({float(k.split("_")[1]) for k in tbl}) if tbl else []
shades = [F.SEQ(v) for v in np.linspace(0.42, 0.95, max(len(jitters), 1))]
for j, col in zip(jitters, shades):
    xs, ys, es = [], [], []
    for s in snrs:
        e = tbl.get(f"graded_{j}_{s:g}")
        if e:
            xs.append(s)
            ys.append(e["nlmc_mean"])
            es.append(e["nlmc_std"])
    ax.errorbar(xs, ys, yerr=es, color=col, marker="o", ms=4.5, lw=1.8,
                elinewidth=1.0, capsize=2.5,
                label=f"{j:g}" if j else "none")
ref = tbl.get(f"graded_{jitters[0]}_inf") if jitters else None
if ref:
    ax.axhline(ref["nlmc_mean"], color=F.INK2, lw=1.2, ls=":", zorder=0)
    ax.text(max(snrs), ref["nlmc_mean"] * 1.03, "noiseless readout",
            fontsize=8.8, color=F.INK2, ha="right", va="bottom")
ax.set_xlabel("readout signal-to-noise ratio  (dB)")
ax.set_ylabel("nonlinear memory capacity")
if ref:
    ax.set_ylim(top=ref["nlmc_mean"] * 1.12)
leg = F.legend(ax, loc="upper left", fontsize=8.3,
               title="cycle-to-cycle\n$E_\\mathrm{c}$ jitter")
leg.get_title().set_fontsize(8.3)
leg.get_title().set_color(F.INK2)
F.heading(ax, "Precision and switching jitter",
          "readout precision costs far more than device jitter")
F.despine(ax)
F.panel_tag(ax, "d")

os.makedirs(C.FIG_DIR, exist_ok=True)
for ext in ("pdf", "png"):
    fig.savefig(os.path.join(C.FIG_DIR, f"fig4_reproducibility.{ext}"))
print("wrote fig4")
print(f"  transfer regularization lambda = {LAM_STAR:g}")
print(f"  fabrication budget sigma* = {S.get('sigma_star')} cation fraction")
for s in SIGMAS:
    t = S["tolerance"].get(str(s))
    if t:
        print(f"    sigma={s:<6g} transfer penalty "
              f"{t['transfer_penalty_graded']:.4f} vs "
              f"{t['transfer_penalty_stochastic']:.4f} "
              f"(ratio {t['penalty_ratio']:.2f}x, p={t['paired_p']:.3g})")
for arm, v in SPEC.get("requirement", {}).items():
    print(f"  {arm}: noiseless capacity {v['noiseless_nlmc']:.3f}, "
          f"95% of it needs {v['snr_for_95pct']} dB")
print("  design advantage vs SNR:", {k: round(v, 3) for k, v in gap.items()})
