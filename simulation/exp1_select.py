"""Stage 1: choose operating points on the SELECTION seeds only.

The selection objective is nonlinear memory capacity - delayed-parity accuracy
summed over delays - and not NARMA-10 error. That choice is forced by the
stage-0 controls:

  * NARMA-10 has a large linear component, so minimizing its error rewards
    storage over computation. A plain 30-tap delay line reaches NRMSE 0.39
    where the pad reaches 0.56, and a search that minimizes NARMA error drives
    the input modulation toward zero, switching the device nonlinearity off.
  * Delayed parity cannot be produced by any linear filter of the input,
    delay line included (measured capacity 0.006, i.e. chance). Capacity above
    zero is therefore direct evidence that the device is computing rather than
    storing, and maximizing it keeps the nonlinearity engaged.

The search also includes the delayed-feedback loop gain. With the loop open
the pad is a Hammerstein system - an instantaneous nonlinearity followed by a
bank of linear filters - and has no nonlinear memory whatsoever; closing the
loop is what makes the dynamics recurrent, and the usable gain window is
narrow, so it has to be searched rather than assumed.

Four coordinate stages, each scored on SELECT_SEEDS:
  A  drive parameters at a nominal window and loop gain
  B  the designed time-constant window (centre and span)
  C  loop gain together with bias and input modulation
  D  the ESN baseline, tuned equally hard on the same objective

Output: results/operating_points.json
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import threadcap  # noqa: F401  (must precede numpy)

import itertools
import json
import time
from multiprocessing import Pool

import numpy as np

import config as C
from alscgan_rc import arrays, benchmarks
from alscgan_rc.reservoir import EchoStateNetwork

np.seterr(over="raise", divide="raise", invalid="raise", under="ignore")

N_PADS_SELECT = 4
DESIGNS = ["graded", "homogeneous", "uniform", "stochastic"]
SEL_SEEDS = C.SELECT_SEEDS[:2]
D_MAX_SEL = 8                     # cheaper than the reported D_MAX_NL

BIAS_GRID = [0.35, 0.45, 0.55, 0.65, 0.75, 0.85]
GAIN_GRID = [0.02, 0.05, 0.10, 0.20]
SPREAD_GRID = [0.15, 0.30, 0.45]
THETA_GRID = [1e-3, 2e-3, 5e-3]
CENTER_MULT_GRID = [0.1, 0.3, 1.0, 3.0, 10.0]
SPAN_GRID = [0.25, 0.5, 1.0, 2.0, 3.0, 4.0]
FEEDBACK_GRID = [0.0, 0.003, 0.006, 0.01, 0.02, 0.03, 0.05]

ESN_RHO = [0.6, 0.8, 0.9, 1.0, 1.1]
ESN_LEAK = [0.1, 0.3, 0.5, 0.8, 1.0]
ESN_IN = [0.25, 0.5, 1.0, 2.0]
ESN_BIAS = [0.0, 0.2, 0.5]
ESN_SEEDS = [11, 12]


def tau_window(center_mult, span, theta, m_virtual=C.M_VIRTUAL):
    center = center_mult * m_virtual * theta
    if span <= 0:
        return center, center
    return center / 10 ** (span / 2), center * 10 ** (span / 2)


def build(design, n_pads, tau_lo, tau_hi, rng=None):
    kw = dict(n_seg=C.N_SEG)
    if design == "graded":
        return arrays.graded_array(n_pads, tau_lo, tau_hi, C.EC_TARGET, **kw)
    if design == "homogeneous":
        return arrays.homogeneous_array(n_pads, tau_lo, tau_hi, C.EC_TARGET,
                                        **kw)
    if design == "uniform":
        return arrays.uniform_array(n_pads, float(np.sqrt(tau_lo * tau_hi)),
                                    C.EC_TARGET, **kw)
    if design == "stochastic":
        return arrays.stochastic_array(n_pads, tau_lo, tau_hi, C.EC_TARGET,
                                       rng, **kw)
    raise ValueError(design)


def score(job):
    """Mean nonlinear memory capacity over the selection seeds (higher wins)."""
    design, bias, gain, spread, theta, center_mult, span, fb = job
    try:
        tau_lo, tau_hi = tau_window(center_mult, span, theta)
        caps = []
        for seed in SEL_SEEDS:
            ub = C.binary_inputs(seed)
            arr = build(design, N_PADS_SELECT, tau_lo, tau_hi,
                        np.random.default_rng(seed))
            x = arr.states(ub, n_virtual=C.M_VIRTUAL, theta=theta, bias=bias,
                           gain=gain, scheme=C.SCHEME, mask_spread=spread,
                           readout=C.READOUT, mask_seed=1000 + seed,
                           feedback=fb, feedback_delay=C.FEEDBACK_DELAY)
            if not np.all(np.isfinite(x)):
                return job, -1.0
            _, cap = benchmarks.nonlinear_memory_profile(
                x, ub, C.N_WASHOUT, C.N_TRAIN, d_max=D_MAX_SEL,
                order=C.PARITY_ORDER)
            caps.append(cap)
        return job, float(np.mean(caps))
    except (ValueError, FloatingPointError, np.linalg.LinAlgError):
        return job, -1.0


def score_esn(job):
    rho, leak, scale, bscale = job
    caps = []
    for seed in SEL_SEEDS:
        ub = C.binary_inputs(seed)
        for ws in ESN_SEEDS:
            esn = EchoStateNetwork(n_nodes=C.M_VIRTUAL * N_PADS_SELECT,
                                   spectral_radius=rho, leak=leak,
                                   input_scale=scale, bias_scale=bscale,
                                   seed=ws)
            _, cap = benchmarks.nonlinear_memory_profile(
                esn.states(ub), ub, C.N_WASHOUT, C.N_TRAIN, d_max=D_MAX_SEL,
                order=C.PARITY_ORDER)
            caps.append(cap)
    return job, float(np.mean(caps))


def run_stage(name, jobs, pool, report_every=100):
    t0 = time.time()
    print(f"\n{name}: {len(jobs)} configurations")
    best = {}
    for i, (job, cap) in enumerate(pool.imap_unordered(score, jobs,
                                                       chunksize=2)):
        d = job[0]
        if d not in best or cap > best[d][1]:
            best[d] = (job, cap)
        if (i + 1) % report_every == 0:
            print(f"   {i + 1}/{len(jobs)}  ({time.time() - t0:.0f} s)")
    for d, (job, cap) in sorted(best.items()):
        print(f"   {d:>12}: NL-MC={cap:.3f}  bias={job[1]} gain={job[2]} "
              f"spread={job[3]} theta={job[4]:g} centre={job[5]}xframe "
              f"span={job[6]}dec fb={job[7]}")
    return best


def main():
    os.makedirs(C.OUT_DIR, exist_ok=True)
    t0 = time.time()
    nom_center, nom_span, nom_fb = 1.0, 2.0, 0.01

    with Pool() as pool:
        jobs_a = [(d, b, g, s, t, nom_center, nom_span, nom_fb)
                  for d in DESIGNS
                  for b, g, s, t in itertools.product(BIAS_GRID, GAIN_GRID,
                                                      SPREAD_GRID, THETA_GRID)]
        best_a = run_stage("Stage A - drive parameters", jobs_a, pool)

        jobs_b = []
        for d, (job, _) in best_a.items():
            _, b, g, s, t, _, _, fb = job
            for cm, sp in itertools.product(CENTER_MULT_GRID, SPAN_GRID):
                jobs_b.append((d, b, g, s, t, cm, sp, fb))
        best_b = run_stage("Stage B - designed time-constant window", jobs_b,
                           pool, report_every=30)

        jobs_c = []
        for d, (job, _) in best_b.items():
            _, _, _, s, t, cm, sp, _ = job
            for b, g, fb in itertools.product(BIAS_GRID, GAIN_GRID,
                                              FEEDBACK_GRID):
                jobs_c.append((d, b, g, s, t, cm, sp, fb))
        best_c = run_stage("Stage C - loop gain and drive", jobs_c, pool)

        final = {}
        for d in DESIGNS:
            cands = [c for c in (best_b.get(d), best_c.get(d)) if c]
            job, cap = max(cands, key=lambda c: c[1])
            _, bias, gain, spread, theta, cm, span, fb = job
            tau_lo, tau_hi = tau_window(cm, span, theta)
            final[d] = dict(bias=bias, gain=gain, mask_spread=spread,
                            theta=theta, center_mult=cm, span_decades=span,
                            feedback=fb, tau_lo=tau_lo, tau_hi=tau_hi,
                            select_nlmc=cap)

        esn_jobs = list(itertools.product(ESN_RHO, ESN_LEAK, ESN_IN, ESN_BIAS))
        print(f"\nStage D - ESN baseline: {len(esn_jobs)} configurations "
              f"x {len(ESN_SEEDS)} weight seeds")
        best_esn, best_cap = None, -np.inf
        for i, (job, cap) in enumerate(pool.imap_unordered(score_esn, esn_jobs,
                                                           chunksize=4)):
            if cap > best_cap:
                best_esn, best_cap = job, cap
            if (i + 1) % 60 == 0:
                print(f"   {i + 1}/{len(esn_jobs)}  ({time.time() - t0:.0f} s)")
        rho, leak, scale, bscale = best_esn
        final["esn"] = dict(spectral_radius=rho, leak=leak, input_scale=scale,
                            bias_scale=bscale, select_nlmc=best_cap)
        print(f"   selected: NL-MC={best_cap:.3f} rho={rho} leak={leak} "
              f"input_scale={scale} bias_scale={bscale}")

    edges = {"bias": BIAS_GRID, "gain": GAIN_GRID, "mask_spread": SPREAD_GRID,
             "theta": THETA_GRID, "center_mult": CENTER_MULT_GRID,
             "span_decades": SPAN_GRID, "feedback": FEEDBACK_GRID}
    print("\nBoundary check (a selected value at a grid edge means the search "
          "was truncated):")
    any_edge = False
    for d, v in final.items():
        if d == "esn":
            continue
        hits = [k for k, g in edges.items()
                if k in v and (v[k] == min(g) or v[k] == max(g))]
        final[d]["grid_edge_hits"] = hits
        if hits:
            any_edge = True
            print(f"  {d:>12}: at a grid edge for {', '.join(hits)}")
        else:
            print(f"  {d:>12}: interior optimum")
    final["_boundary_hits"] = any_edge

    print("\nFinal operating points:")
    for d, v in final.items():
        if d.startswith("_"):
            continue
        print(f"  {d:>12}: {v}")

    final["_meta"] = dict(objective="nonlinear memory capacity (delayed parity)",
                          n_pads_select=N_PADS_SELECT, select_seeds=SEL_SEEDS,
                          d_max_select=D_MAX_SEL, ec_target=C.EC_TARGET,
                          n_seg=C.N_SEG, m_virtual=C.M_VIRTUAL,
                          scheme=C.SCHEME, readout=C.READOUT)
    path = os.path.join(C.OUT_DIR, "operating_points.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(final, fh, indent=2)
    print(f"\nWrote {path}  ({time.time() - t0:.0f} s total)")


if __name__ == "__main__":
    main()
