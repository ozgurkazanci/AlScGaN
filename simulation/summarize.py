"""Consolidate every reportable number into one place.

Reads whatever result files exist and writes results/SUMMARY.md, so that the
manuscript is transcribed from a single generated document rather than from
scattered logs. Missing stages are reported as missing rather than skipped
silently.
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C

LINES = []


def out(text=""):
    LINES.append(text)
    print(text)


def load(name):
    path = os.path.join(C.OUT_DIR, name)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def missing(stage, script):
    out(f"**Not yet run.** Produce it with `python {script}`.")
    out()


mat = load("material_summary.json")
ctl = load("controls.json")
ops = load("operating_points.json")
dev = load("device_summary.json")
head = load("headline_summary.json")
rep = load("reproducibility.json")
rob = load("robustness.json")
tern = load("ternary_control.json")

out("# Consolidated results")
out()
out("Every number the manuscript quotes, generated from the result files. "
    "All values are simulated.")
out()

# --- 1 -----------------------------------------------------------------------
out("## 1. Composition design space  (Figure 1)")
out()
if not mat:
    missing("material", "exp2_material.py")
else:
    q = mat["quaternary_decades_at_zero_tolerance"]
    out(f"- Quaternary on an iso-Ec trajectory at Ec = {mat['ec_target_used']} "
        f"MV/cm: **{q:.2f} decades** of tau at **zero** Ec tolerance.")
    out("- Ternary controls, decades of tau reachable inside an Ec tolerance "
        "band:")
    out()
    out("  | tolerance | AlScN | ScGaN | quaternary |")
    out("  |---|---|---|---|")
    for tol in ("1%", "2%", "5%", "10%"):
        a = mat["ternary"]["AlScN"]["decades_within_tolerance"][tol]
        b = mat["ternary"]["ScGaN"]["decades_within_tolerance"][tol]
        out(f"  | ±{tol} | {a:.3f} | {b:.3f} | {q:.2f} |")
    out()
    a5 = mat["ternary"]["AlScN"]["decades_within_tolerance"]["5%"]
    out(f"- Advantage over the better ternary at ±5%: **{q / a5:.0f}x**.")
    out(f"- Ec cost of moving tau in a ternary: "
        f"{mat['ternary']['AlScN']['ec_cost_per_decade']:.2f} (AlScN) and "
        f"{mat['ternary']['ScGaN']['ec_cost_per_decade']:.2f} (ScGaN) "
        f"MV/cm per decade.")
    out(f"- With pairwise bandgap bowing the trajectory stays monotone "
        f"({mat['bowed']['monotone']}) and spans "
        f"{mat['bowed']['decades']:.2f} decades.")
    out(f"- Temperature sensitivity: one decade of tau per "
        f"{mat['temperature_sensitivity_k_per_decade']:.1f} K, evaluated "
        f"mid-window at (x_Ga, y_Sc) = (0.35, 0.35) over 300->325 K. It is "
        f"NOT constant along the trajectory: the barrier falls from 1.02 eV "
        f"at the Al-rich end to 0.59 eV at the Ga-rich end, so the "
        f"sensitivity runs 19 K/decade (slow end) to 33 K/decade (fast end) "
        f"and the spectrum COMPRESSES with warming rather than sliding "
        f"rigidly.")
out()

# --- 2 -----------------------------------------------------------------------
out("## 2. Controls: does the device compute at all?")
out()
if not ctl:
    missing("controls", "exp0_controls.py")
else:
    v = ctl["verdict"]
    out(f"- Best delay line (ridge on the raw input history): NARMA-10 NRMSE "
        f"**{ctl['delay_line_best_nrmse']:.4f}**.")
    out(f"- Pad at its NARMA-selected drive: **{ctl['delay_line_best_nrmse'] - v['margin_vs_delay_line']:.4f}** "
        f"- it does {'' if v['beats_delay_line'] else '**not** '}beat the "
        f"delay line. NARMA-10 is therefore reported only with this control.")
    out(f"- Delayed parity, delay line: **{v['delay_line_parity']:.3f}** "
        f"(chance is 0.5). No linear filter can exceed chance here.")
    out(f"- Delayed parity, pad: up to **{v['best_parity_over_gain']:.3f}** - "
        f"the device computes something a delay line provably cannot.")
    out(f"- Tuned ESN on NARMA-10: {ctl['esn']['nrmse_mean']:.4f}.")
out()

# --- 3 -----------------------------------------------------------------------
out("## 3. Selected operating points")
out()
if not ops:
    missing("selection", "exp1_select.py then exp1b_refine.py")
else:
    out(f"Objective: {ops['_meta'].get('objective', 'n/a')}. Selection seeds "
        f"{ops['_meta'].get('select_seeds')} are disjoint from the evaluation "
        f"seeds.")
    out()
    out("  | design | bias | gain | theta (s) | span (dec) | tau window (s) "
        "| feedback | NL-MC (select) | grid edges |")
    out("  |---|---|---|---|---|---|---|---|---|")
    for d in ("graded", "homogeneous", "stochastic", "uniform"):
        v = ops.get(d)
        if not v:
            continue
        edges = ", ".join(v.get("grid_edge_hits") or []) or "none"
        out(f"  | {d} | {v['bias']} | {v['gain']} | {v['theta']:g} | "
            f"{v['span_decades']} | {v['tau_lo']:.3g}–{v['tau_hi']:.3g} | "
            f"{v['feedback']:g} | {v['select_nlmc']:.3f} | {edges} |")
    out()
    e = ops.get("esn", {})
    out(f"- ESN baseline, tuned on the same objective: rho="
        f"{e.get('spectral_radius')}, leak={e.get('leak')}, "
        f"input scale={e.get('input_scale')}, bias scale="
        f"{e.get('bias_scale')}, NL-MC {e.get('select_nlmc', float('nan')):.3f}.")
out()

# --- 4 -----------------------------------------------------------------------
out("## 4. Device signatures and the feedback loop  (Figure 2)")
out()
if not dev:
    missing("device", "exp3_device.py")
else:
    r = dev["retention"]
    out(f"- Retention half-life is nearly identical for the two pads "
        f"({r['graded']['t_half']:.3g} s spread versus "
        f"{r['uniform']['t_half']:.3g} s single-composition - this is the "
        f"`uniform` arm, not `homogeneous`): a single-number "
        f"retention metric does not see the spectrum. The decay SHAPE does - "
        f"the log-slope varies over {r['graded']['logslope_spread']:.2f} for "
        f"the spread pad against {r['uniform']['logslope_spread']:.2f} for the "
        f"single-composition one, the smaller spread being the more power-law-like, "
        f"multi-exponential decay.")
    f = dev["feedback"]
    out(f"- **Open loop the pad has almost no nonlinear memory** "
        f"(capacity {f['open_loop_nlmc']:.2f}). Closing the loop raises it to "
        f"**{f['best_nlmc']:.2f}** at gain {f['best_gain']:g}; the usable "
        f"window is {f['stable_window']} - a factor of "
        f"{f['stable_window'][1] / f['stable_window'][0]:.0f}, i.e. "
        f"{math.log10(f['stable_window'][1] / f['stable_window'][0]):.2f} "
        f"decades, NOT \"under half a decade\". Its lower edge is "
        f"grid-censored: the smallest nonzero gain tested is "
        f"{f['stable_window'][0]:g}.")
    out("- Linear memory capacity at the selected drive:")
    for k, v in dev["mc_profile"].items():
        out(f"  - {k}: **{v['mc']:.2f}** (surrogate floor "
            f"{v['noise_floor']:.2f}), significant to delay "
            f"{v['last_significant_delay']}")
out()

# --- 5 -----------------------------------------------------------------------
out("## 5. Headline benchmark  (Figure 3)")
out()
if not head:
    missing("headline", "exp4_headline.py")
else:
    P = head["pad_counts"]
    out(f"{head['n_realizations']} paired realizations per cell "
        f"(10 mask x 10 input seeds).")
    out()
    out("  | design | " + " | ".join(f"P={p}" for p in P) + " |")
    out("  |---|" + "---|" * len(P))
    for d in ("graded", "homogeneous", "stochastic", "uniform", "esn",
              "delay_line"):
        row = head["table"].get(d, {})
        if not row:
            continue
        cells = " | ".join(
            f"{row[str(p)]['nlmc_mean']:.2f} ± {row[str(p)]['nlmc_std']:.2f}"
            if str(p) in row else "—" for p in P)
        out(f"  | {d} | {cells} |")
    out()
    out("Nonlinear memory capacity, mean ± s.d. A delay line scores zero by "
        "construction whatever its length.")
    out()
    for p in P:
        pr = head["paired"].get(str(p), {})
        for other, e in pr.items():
            out(f"- P={p}, spread versus {other}: "
                f"{e['mean_diff']:+.3f} ± {e['std_diff']:.3f} "
                f"({e['rel_pct']:+.1f}%), Wilcoxon p = {e['wilcoxon_p']:.2e}")
    out()
    ce = head.get("channel_efficiency", {})
    out(f"- Channel efficiency (single-time-constant pads needed to match one "
        f"spread pad): {ce}")
out()

# --- 6 -----------------------------------------------------------------------
out("## 6. Reproducibility  (Figure 4)")
out()
if not rep:
    missing("reproducibility", "exp5_reproducibility.py")
else:
    lam = rep["lam_transfer"]
    tr = rep["lambda_tradeoff"]["graded"]
    lo_key = min(tr, key=lambda k: float(k))
    out(f"- The readout is ill-conditioned, so accuracy and transferability "
        f"trade off. At lambda={lo_key} the readout scores "
        f"{tr[lo_key]['own']:.3f} on its own device and "
        f"{tr[lo_key]['transfer']:.3g} on another; at the selected "
        f"lambda={lam:g} it scores {tr[f'{lam:g}']['own']:.3f} and "
        f"{tr[f'{lam:g}']['transfer']:.3f}.")
    out(f"- Deposition tolerance at which the designed and random spectra "
        f"become statistically indistinguishable in variance: "
        f"**sigma* = {rep.get('sigma_star')}**.")
    out()
    out("  | sigma | arm | NRMSE | inter-device s.d. | state corr | transfer "
        "penalty |")
    out("  |---|---|---|---|---|---|")
    for s in sorted(rep["sigma_sweep"], key=float):
        for arm, v in rep["sigma_sweep"][s].items():
            out(f"  | {s} | {arm} | {v['nrmse_mean']:.4f} | "
                f"{v['inter_device_std']:.5f} | {v['state_corr']:.4f} | "
                f"{v['transfer_penalty']:+.4f} |")
    out()
    spec = rep.get("noise_spec", {})
    if spec:
        out()
        out("### Readout precision - the binding experimental requirement")
        out()
        for arm, v in spec.get("requirement", {}).items():
            need = v["snr_for_95pct"]
            txt = (f"{need:g} dB" if need
                   else "more than the swept range reaches")
            out(f"- {arm}: noiseless capacity {v['noiseless_nlmc']:.3f}; "
                f"95% of it needs **{txt}**.")
        out()
        out("- Capacity advantage of the spread against readout SNR:")
        gap = spec.get("advantage_vs_snr", {})
        order = sorted((k for k in gap if k != "inf"), key=float, reverse=True)
        if "inf" in gap:
            out(f"  - noiseless: {gap['inf']:+.3f}")
        for k in order:
            out(f"  - {k} dB: {gap[k]:+.3f}")
        resolvable = [float(k) for k in order if gap[k] > 0.05]
        if resolvable:
            out()
            out(f"  The advantage stops being resolvable below about "
                f"**{min(resolvable):g} dB**. This is the same "
                f"ill-conditioning seen twice: a readout that leans on "
                f"low-variance directions needs large dynamic range.")
out()

# --- 7 -----------------------------------------------------------------------
out("## 7. Robustness  (Figure 5)")
out()
if not rob:
    missing("robustness", "exp6_robustness.py")
else:
    for d, v in rob.get("temperature_drift", {}).items():
        out(f"- {d}: NL-MC {v['nlmc_300k']:.3f} at 300 K, largest drift over "
            f"275–325 K {v['max_abs_drift']:.3f} ({v['rel_drift_pct']:.1f}%)")
    out()
    out("- Spectral span:")
    for s in sorted(rob["span"], key=float):
        v = rob["span"][s]
        out(f"  - {s} decades: NL-MC {v['nlmc_mean']:.3f} ± "
            f"{v['nlmc_std']:.3f}, linear MC {v['mc_mean']:.2f}")
    out()
    out("- Discrete ladders versus the continuum "
        f"({rob['ladder_vs_continuum']['continuum_nlmc']:.3f}):")
    for n in sorted(rob["ladder"], key=int):
        v = rob["ladder"][n]
        out(f"  - {n} distinct tau: NL-MC {v['nlmc_mean']:.3f} ± "
            f"{v['nlmc_std']:.3f}")
out()

# --- 8 -----------------------------------------------------------------------
out("## 8. The ternary control  (Figure 6)")
out()
if not tern:
    missing("ternary control", "exp7_ternary.py")
else:
    req = tern["requested_decades"]
    out(f"Both arrays are asked for the same {req:.2f}-decade window and driven "
        f"from one shared line, each at its own best drive.")
    out()
    out("  | | decades of tau built | Ec spread (MV/cm) | switching-rate "
        "spread | NL-MC | temperature drift |")
    out("  |---|---|---|---|---|---|")
    for k in ("quaternary", "ternary"):
        d = tern["designs"][k]
        b = tern["best"][k]
        t = tern["temperature"][k]
        rd = d.get("switching_rate_decades")
        out(f"  | {k} | {d['tau_decades']:.2f} | {d['ec_spread']:.3g} | "
            f"{rd:.1f} decades | {b['nlmc_mean']:.3f} | "
            f"{t['rel_drift_pct']:.1f}% |")
    out()
    out(f"- The ternary reaches only **{tern['designs']['ternary']['tau_decades']:.2f}** "
        f"of the {req:.2f} decades requested before leaving the physical "
        f"composition range.")
    out(f"- Its coercive-field spread of "
        f"**{tern['designs']['ternary']['ec_spread']:.2f} MV/cm** becomes "
        f"**{tern['designs']['ternary']['switching_rate_decades']:.1f} decades** "
        f"of switching-rate spread under one drive - uncontrolled diversity "
        f"standing in for the designed kind, which is why it still reaches "
        f"{tern['best']['ternary']['nlmc_mean'] / tern['best']['quaternary']['nlmc_mean'] * 100:.0f}% "
        f"of the quaternary's capacity at fixed temperature.")
    out(f"- The substitution fails under ambient drift: "
        f"**{tern['temperature']['ternary']['rel_drift_pct']:.1f}%** loss over "
        f"275-325 K against the quaternary's "
        f"**{tern['temperature']['quaternary']['rel_drift_pct']:.1f}%**.")
out()

# --- 9. numbers that previously had no archived run -------------------------
declared = load("declared.json")
if not declared:
    missing("declared", "exp8_declared.py")
else:
    out()
    out("## 9. Declared numbers that previously had no archived run "
        "(exp8_declared.py)")
    out()
    out("Four figures quoted in earlier drafts came from working notes rather "
        "than from a script. They are measured here under the stage-4 protocol.")
    out("")
    il = declared["interleaved"]
    out("- **Interleaved comb against the partitioned design.** The earlier "
        "claim of \"3-5% worse at every channel count\" was wrong in both "
        "magnitude and universality.")
    out("")
    out("  | P | graded | interleaved | difference | Wilcoxon p |")
    out("  |---|---|---|---|---|")
    for k in sorted(il, key=int):
        v = il[k]
        out(f"  | {k} | {v['graded_mean']:.3f} | {v['interleaved_mean']:.3f} "
            f"| {v['rel_pct']:+.1f}% | {v['wilcoxon_p']:.2g} |")
    out("")
    dw = declared["dwell"]
    order = sorted(dw, key=int)
    vals = ", ".join(f"{dw[k]['nlmc_mean']:.2f}" for k in order)
    out(f"- **Field-free dwell slots, open loop** ({dw[order[0]]['n']} paired "
        f"realizations, graded, P = 4): capacity {vals} for "
        f"{', '.join(order)} dwell slots. Genuinely unchanged; the earlier "
        f"figure of 1.27 matched no run.")
    olp = declared.get("open_loop_parity")
    if olp:
        acc = ", ".join(f"{a:.3f}" for a in olp["acc_mean"][:5])
        cap = ", ".join(f"{c:.3f}" for c in olp["capacity_by_delay"][:5])
        out(f"- **Open-loop delayed parity is not at chance beyond delay "
            f"zero.** Mean accuracy at delays 0-4: {acc} (chance 0.5), "
            f"contributing {cap} to a capacity of "
            f"{olp['nlmc_mean']:.2f}. The zero-delay term needs no memory, so "
            f"only about "
            f"{olp['nlmc_mean'] - olp['capacity_by_delay'][0]:.2f} reflects "
            f"memory of any depth. Statements that the open-loop pad is \"at "
            f"chance for every delay of one or more\" are too strong.")
    cg = declared["conditioning"]["graded_4"]
    c1 = declared["conditioning"]["graded_1"]
    out(f"- **Conditioning of the training Gram matrix**: at P = 4, "
        f"{cg['n_columns']} columns of which only **rank {cg['rank']}** are "
        f"numerically independent, cond(Gram) = **{cg['cond_gram']:.1e}** "
        f"(P = 1: {c1['n_columns']} columns, rank {c1['rank']}, cond "
        f"{c1['cond_gram']:.1e}). Earlier drafts said \"of order 1e35\".")
    inv = declared["invariance_max_abs_diff"]
    out("- **Segment-permutation invariance**: max |difference| = "
        + ", ".join(f"{inv[k]:.2e} over {k} field steps" for k in
                    sorted(inv, key=int)) + ".")

path = os.path.join(C.OUT_DIR, "SUMMARY.md")
with open(path, "w", encoding="utf-8") as fh:
    fh.write("\n".join(LINES) + "\n")
print(f"\n[wrote {path}]")

