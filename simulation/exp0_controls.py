"""Stage 0: the controls that decide whether the device computes anything.

Two questions have to be answered before any performance number in this work
means anything.

  1. Does the pad beat a plain delay line? A linear filter bank followed by a
     linear readout is exactly a finite-impulse-response filter on the input
     history. If the pad only matches a ridge regression on [u(k) ... u(k-D)],
     then it stores the input and computes nothing, and every comparison
     between pad designs is a comparison between storage schemes.

  2. Is the nonlinearity switched on at the selected drive? The selection
     search minimizes NARMA-10 error, and NARMA-10 has a large linear
     component, so the search can legitimately prefer memory over
     nonlinearity by driving the input modulation toward zero. Parity is the
     discriminating test: a linear filter bank with a linear readout cannot
     produce it at any delay, so parity accuracy above chance is proof that
     the Merz exponential is doing work.

Output: results/controls.json
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import threadcap  # noqa: F401  (must precede numpy)

import json
import time
from multiprocessing import Pool

import numpy as np

import config as C
from alscgan_rc import arrays, benchmarks
from alscgan_rc.reservoir import EchoStateNetwork

np.seterr(over="raise", divide="raise", invalid="raise", under="ignore")

N_PADS = 4
DELAY_ORDERS = [1, 2, 5, 10, 15, 20, 30]
GAIN_SWEEP = [0.02, 0.05, 0.10, 0.20, 0.35, 0.50]
PARITY_ORDERS = (2, 3)
OPS = None


def _init(ops):
    global OPS
    OPS = ops
    np.seterr(over="raise", divide="raise", invalid="raise", under="ignore")


def delay_line_states(u, order):
    """The trivial reservoir: the last `order` inputs, verbatim."""
    return np.column_stack([np.roll(u, d) for d in range(order + 1)])


def drive(arr, u, op, gain=None, mask_seed=None):
    return arr.states(u, n_virtual=C.M_VIRTUAL, theta=op["theta"],
                      bias=op["bias"], gain=op["gain"] if gain is None else gain,
                      scheme=C.SCHEME, mask_spread=op["mask_spread"],
                      readout=C.READOUT,
                      mask_seed=mask_seed or C.EVAL_MASK_SEEDS[0])


def build(design, op, rng=None):
    lo, hi = op["tau_lo"], op["tau_hi"]
    kw = dict(n_seg=C.N_SEG)
    if design == "graded":
        return arrays.graded_array(N_PADS, lo, hi, C.EC_TARGET, **kw)
    if design == "homogeneous":
        return arrays.homogeneous_array(N_PADS, lo, hi, C.EC_TARGET, **kw)
    if design == "uniform":
        return arrays.uniform_array(N_PADS, float(np.sqrt(lo * hi)),
                                    C.EC_TARGET, **kw)
    if design == "stochastic":
        return arrays.stochastic_array(N_PADS, lo, hi, C.EC_TARGET, rng, **kw)
    raise ValueError(design)


def job_gain(args):
    """Sweep the input modulation: memory against nonlinearity."""
    design, gain, seed = args
    op = OPS[design]
    u = C.inputs(seed)
    ub = C.binary_inputs(seed)
    arr = build(design, op, np.random.default_rng(seed))
    x = drive(arr, u, op, gain=gain)
    nrmse, _, _ = benchmarks.narma_nrmse(x, u, C.NARMA_ORDER, C.N_WASHOUT,
                                         C.N_TRAIN)
    _, mc = benchmarks.memory_capacity(x, u, C.N_WASHOUT, C.N_TRAIN,
                                       d_max=C.D_MAX)
    arr_b = build(design, op, np.random.default_rng(seed))
    xb = drive(arr_b, ub, op, gain=gain)
    par = benchmarks.parity_accuracy(xb, ub, C.N_WASHOUT, C.N_TRAIN,
                                     orders=PARITY_ORDERS)
    return dict(design=design, gain=gain, seed=seed, nrmse=float(nrmse),
                mc=float(mc), parity={str(k): v for k, v in par.items()})


def main():
    global OPS
    with open(os.path.join(C.OUT_DIR, "operating_points.json"),
              encoding="utf-8") as fh:
        OPS = json.load(fh)
    t0 = time.time()
    summary = {}
    seeds = C.EVAL_INPUT_SEEDS[:5]

    # --- 1. the delay-line control --------------------------------------------
    print("1. Delay line: ridge regression on the raw input history")
    print(f"   {'taps':>5} {'NARMA-10 NRMSE':>16} {'MC':>7} "
          f"{'PC-2':>7} {'PC-3':>7}")
    summary["delay_line"] = {}
    for order in DELAY_ORDERS:
        errs, mcs, p2, p3 = [], [], [], []
        for seed in seeds:
            u = C.inputs(seed)
            ub = C.binary_inputs(seed)
            x = delay_line_states(u, order)
            e, _, _ = benchmarks.narma_nrmse(x, u, C.NARMA_ORDER,
                                             C.N_WASHOUT, C.N_TRAIN)
            _, mc = benchmarks.memory_capacity(x, u, C.N_WASHOUT, C.N_TRAIN,
                                               d_max=C.D_MAX)
            par = benchmarks.parity_accuracy(delay_line_states(ub, order), ub,
                                             C.N_WASHOUT, C.N_TRAIN,
                                             orders=PARITY_ORDERS)
            errs.append(e)
            mcs.append(mc)
            p2.append(par[2])
            p3.append(par[3])
        summary["delay_line"][str(order)] = dict(
            nrmse_mean=float(np.mean(errs)), nrmse_std=float(np.std(errs, ddof=1)),
            mc_mean=float(np.mean(mcs)),
            parity2=float(np.mean(p2)), parity3=float(np.mean(p3)))
        print(f"   {order:5d} {np.mean(errs):10.4f} +- {np.std(errs, ddof=1):.4f} "
              f"{np.mean(mcs):7.2f} {np.mean(p2):7.3f} {np.mean(p3):7.3f}")
    best_dl = min(summary["delay_line"].values(),
                  key=lambda v: v["nrmse_mean"])
    summary["delay_line_best_nrmse"] = best_dl["nrmse_mean"]
    print(f"   best delay line: NRMSE = {best_dl['nrmse_mean']:.4f}, "
          f"PC-2 = {best_dl['parity2']:.3f}")

    # --- 2. tuned ESN reference ----------------------------------------------
    op = OPS["esn"]
    errs, p2 = [], []
    for seed in seeds:
        u, ub = C.inputs(seed), C.binary_inputs(seed)
        for ws in (11, 12, 13):
            esn = EchoStateNetwork(n_nodes=C.M_VIRTUAL * N_PADS,
                                   spectral_radius=op["spectral_radius"],
                                   leak=op["leak"], input_scale=op["input_scale"],
                                   bias_scale=op["bias_scale"], seed=ws)
            e, _, _ = benchmarks.narma_nrmse(esn.states(u), u, C.NARMA_ORDER,
                                             C.N_WASHOUT, C.N_TRAIN)
            errs.append(e)
            par = benchmarks.parity_accuracy(esn.states(ub), ub, C.N_WASHOUT,
                                             C.N_TRAIN, orders=PARITY_ORDERS)
            p2.append(par[2])
    summary["esn"] = dict(nrmse_mean=float(np.mean(errs)),
                          nrmse_std=float(np.std(errs, ddof=1)),
                          parity2=float(np.mean(p2)))
    print(f"\n2. Tuned ESN: NRMSE = {np.mean(errs):.4f}, "
          f"PC-2 = {np.mean(p2):.3f}")

    # --- 3. is the nonlinearity switched on? ---------------------------------
    print("\n3. Input modulation sweep: memory versus nonlinearity")
    jobs = [(d, g, s) for d in ("graded", "homogeneous")
            for g in GAIN_SWEEP for s in seeds]
    with Pool(initializer=_init, initargs=(OPS,)) as pool:
        recs = list(pool.imap_unordered(job_gain, jobs, chunksize=2))
    summary["gain_sweep"] = {}
    print(f"   {'design':>12} {'gain':>6} {'NRMSE':>16} {'MC':>7} "
          f"{'PC-2':>7} {'PC-3':>7}")
    for design in ("graded", "homogeneous"):
        summary["gain_sweep"][design] = {}
        for g in GAIN_SWEEP:
            sub = [r for r in recs if r["design"] == design and r["gain"] == g]
            if not sub:
                continue
            n = np.array([r["nrmse"] for r in sub])
            m = np.array([r["mc"] for r in sub])
            a2 = np.array([r["parity"]["2"] for r in sub])
            a3 = np.array([r["parity"]["3"] for r in sub])
            summary["gain_sweep"][design][f"{g:g}"] = dict(
                nrmse_mean=float(n.mean()), nrmse_std=float(n.std(ddof=1)),
                mc_mean=float(m.mean()), parity2=float(a2.mean()),
                parity3=float(a3.mean()))
            print(f"   {design:>12} {g:6.2f} {n.mean():10.4f} "
                  f"+- {n.std(ddof=1):.4f} {m.mean():7.2f} "
                  f"{a2.mean():7.3f} {a3.mean():7.3f}")

    # --- verdict --------------------------------------------------------------
    g_tab = summary["gain_sweep"]["graded"]
    sel_gain = f"{OPS['graded']['gain']:g}"
    sel = g_tab.get(sel_gain) or list(g_tab.values())[0]
    best_par = max(g_tab.values(), key=lambda v: v["parity2"])
    summary["verdict"] = dict(
        beats_delay_line=bool(sel["nrmse_mean"] <
                              summary["delay_line_best_nrmse"]),
        margin_vs_delay_line=float(summary["delay_line_best_nrmse"]
                                   - sel["nrmse_mean"]),
        parity_at_selected_gain=sel["parity2"],
        best_parity_over_gain=best_par["parity2"],
        delay_line_parity=best_dl["parity2"])
    print("\nVerdict")
    print(f"  best delay line NRMSE       {summary['delay_line_best_nrmse']:.4f}")
    print(f"  pad at selected drive       {sel['nrmse_mean']:.4f}  "
          f"({'beats' if summary['verdict']['beats_delay_line'] else 'DOES NOT BEAT'} "
          f"the delay line)")
    print(f"  parity PC-2, delay line     {best_dl['parity2']:.3f} (chance 0.5)")
    print(f"  parity PC-2, selected drive {sel['parity2']:.3f}")
    print(f"  parity PC-2, best over gain {best_par['parity2']:.3f}")

    with open(os.path.join(C.OUT_DIR, "controls.json"), "w",
              encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    print(f"\nWrote {C.OUT_DIR}/controls.json  ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
