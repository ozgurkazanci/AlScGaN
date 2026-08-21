"""Stage 7: the control that closes the loop between materials and computation.

Figure 1 shows that a ternary alloy cannot spread its relaxation times without
spreading its coercive field. This stage shows what that costs a device.

A ternary-like array is built along a single composition axis, so the pads no
longer agree on the field at which they switch, and is then driven from one
shared line exactly as the quaternary arrays are. Its drive is swept over the
full range, so the comparison is best-versus-best rather than the quaternary's
operating point imposed on it: even at its own optimum, a single drive cannot
sit near threshold for pads whose coercive fields differ by several MV/cm.

Two quantities are reported per drive: the fraction of segments that are
usefully driven (within a stated band of their own threshold), and the
resulting nonlinear memory capacity.

Output: results/ternary_control.json
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

np.seterr(over="raise", divide="raise", invalid="raise", under="ignore")

N_PADS = 4
TEMPERATURES = [275.0, 285.0, 300.0, 315.0, 325.0]
BIAS_GRID = [0.20, 0.30, 0.40, 0.50, 0.65, 0.80, 1.0, 1.3, 1.7, 2.2]
SEEDS = C.EVAL_INPUT_SEEDS[:5]
DEAD_BAND = (0.30, 1.60)   # |E|/Ec outside this does nothing useful
OPS = None


def _init(ops):
    global OPS
    OPS = ops
    np.seterr(over="raise", divide="raise", invalid="raise", under="ignore")


def build(kind, op, temperature_k=300.0):
    lo, hi = op["tau_lo"], op["tau_hi"]
    kw = dict(n_seg=C.N_SEG, temperature_k=temperature_k)
    if kind == "quaternary":
        return arrays.graded_array(N_PADS, lo, hi, C.EC_TARGET, **kw)
    if kind == "ternary":
        return arrays.ternary_array(N_PADS, lo, hi, **kw)
    raise ValueError(kind)


def switching_rate_decades(arr, bias):
    """Decades of spread in the Merz switching rate across the array.

    The rate is exponential in Ec/E, so a coercive-field spread that looks
    modest becomes an enormous spread in dynamics under one shared drive.
    This is the quantity that makes an Ec-disordered array behave like a
    disordered reservoir - uncontrolled diversity standing in for designed
    diversity.
    """
    from alscgan_rc.device import TAU_SW0, W_MERZ
    ec = np.concatenate([f.ec for f in arr.films])
    e = bias * np.median(ec)
    rates = np.exp(-np.minimum(W_MERZ * ec / e, 700.0)) / TAU_SW0
    return float(np.log10(rates.max() / max(rates.min(), 1e-300)))


def usefully_driven(arr, bias):
    """Fraction of segments whose drive lands inside the useful band.

    The shared drive is referenced to the array median coercive field, so a
    segment sees |E|/Ec_i = bias * median(Ec) / Ec_i.
    """
    ec = np.concatenate([f.ec for f in arr.films])
    rel = bias * np.median(ec) / ec
    return float(np.mean((rel > DEAD_BAND[0]) & (rel < DEAD_BAND[1])))


def job_temperature(args):
    kind, temp, bias, seed = args
    op = OPS["graded"]
    kw = dict(n_virtual=C.M_VIRTUAL, theta=op["theta"], bias=bias,
              gain=op["gain"], scheme=C.SCHEME,
              mask_spread=op["mask_spread"], readout=C.READOUT,
              mask_seed=C.EVAL_MASK_SEEDS[0], feedback=op["feedback"],
              feedback_delay=C.FEEDBACK_DELAY)
    try:
        ub = C.binary_inputs(seed)
        x = build(kind, op, temp).states(ub, **kw)
        if not np.all(np.isfinite(x)):
            return dict(kind=kind, temp=temp, seed=seed, nlmc=0.0)
        _, nlmc = benchmarks.nonlinear_memory_profile(
            x, ub, C.N_WASHOUT, C.N_TRAIN, d_max=C.D_MAX_NL,
            order=C.PARITY_ORDER)
    except (ValueError, FloatingPointError, np.linalg.LinAlgError):
        return dict(kind=kind, temp=temp, seed=seed, nlmc=0.0)
    return dict(kind=kind, temp=temp, seed=seed, nlmc=float(nlmc))


def job(args):
    kind, bias, seed = args
    op = OPS["graded"]
    kw = dict(n_virtual=C.M_VIRTUAL, theta=op["theta"], bias=bias,
              gain=op["gain"], scheme=C.SCHEME,
              mask_spread=op["mask_spread"], readout=C.READOUT,
              mask_seed=C.EVAL_MASK_SEEDS[0], feedback=op["feedback"],
              feedback_delay=C.FEEDBACK_DELAY)
    try:
        ub = C.binary_inputs(seed)
        arr = build(kind, op)
        frac = usefully_driven(arr, bias)
        x = arr.states(ub, **kw)
        if not np.all(np.isfinite(x)):
            return dict(kind=kind, bias=bias, seed=seed, nlmc=0.0,
                        mc=0.0, frac=frac, diverged=True)
        _, nlmc = benchmarks.nonlinear_memory_profile(
            x, ub, C.N_WASHOUT, C.N_TRAIN, d_max=C.D_MAX_NL,
            order=C.PARITY_ORDER)
        u = C.inputs(seed)
        x2 = build(kind, op).states(u, **kw)
        _, mc = benchmarks.memory_capacity(x2, u, C.N_WASHOUT, C.N_TRAIN,
                                           d_max=C.D_MAX)
    except (ValueError, FloatingPointError, np.linalg.LinAlgError):
        return dict(kind=kind, bias=bias, seed=seed, nlmc=0.0, mc=0.0,
                    frac=float("nan"), diverged=True)
    return dict(kind=kind, bias=bias, seed=seed, nlmc=float(nlmc),
                mc=float(mc), frac=frac, diverged=False)


def main():
    global OPS
    with open(os.path.join(C.OUT_DIR, "operating_points.json"),
              encoding="utf-8") as fh:
        OPS = json.load(fh)
    t0 = time.time()
    op = OPS["graded"]

    summary = {"n_pads": N_PADS, "bias_grid": BIAS_GRID,
               "dead_band": list(DEAD_BAND), "designs": {}}

    for kind in ("quaternary", "ternary"):
        arr = build(kind, op)
        ec = np.concatenate([f.ec for f in arr.films])
        tau = arr.tau_pool()
        summary["designs"][kind] = dict(
            ec_lo=float(ec.min()), ec_hi=float(ec.max()),
            ec_spread=float(np.ptp(ec)),
            tau_lo=float(tau.min()), tau_hi=float(tau.max()),
            tau_decades=float(np.log10(tau.max() / tau.min())))
        v = summary["designs"][kind]
        print(f"{kind:>12}: Ec {v['ec_lo']:.3f}-{v['ec_hi']:.3f} MV/cm "
              f"(spread {v['ec_spread']:.3g}), tau "
              f"{v['tau_lo']:.3g}-{v['tau_hi']:.3g} s "
              f"({v['tau_decades']:.2f} decades)")
    req = float(np.log10(op["tau_hi"] / op["tau_lo"]))
    summary["requested_decades"] = req
    print(f"\nrequested window: {req:.2f} decades - the ternary reaches "
          f"{summary['designs']['ternary']['tau_decades']:.2f} of them before "
          f"leaving the physical composition range")

    jobs = [(k, b, s) for k in ("quaternary", "ternary")
            for b in BIAS_GRID for s in SEEDS]
    print(f"\ndrive sweep: {len(jobs)} runs")
    with Pool(initializer=_init, initargs=(OPS,)) as pool:
        recs = list(pool.imap_unordered(job, jobs, chunksize=2))

    print(f"\n{'design':>12} {'bias':>6} {'driven':>8} {'NL-MC':>16} "
          f"{'lin MC':>8}")
    summary["sweep"] = {}
    for kind in ("quaternary", "ternary"):
        summary["sweep"][kind] = {}
        for b in BIAS_GRID:
            sub = [r for r in recs if r["kind"] == kind and r["bias"] == b]
            if not sub:
                continue
            nl = np.array([r["nlmc"] for r in sub])
            mc = np.array([r["mc"] for r in sub])
            frac = float(np.nanmean([r["frac"] for r in sub]))
            summary["sweep"][kind][f"{b:g}"] = dict(
                nlmc_mean=float(nl.mean()), nlmc_std=float(nl.std(ddof=1)),
                mc_mean=float(mc.mean()), fraction_driven=frac,
                diverged=int(sum(r["diverged"] for r in sub)))
            print(f"{kind:>12} {b:6.2f} {frac:8.2f} {nl.mean():9.3f} "
                  f"+- {nl.std(ddof=1):.3f} {mc.mean():8.2f}")

    best = {}
    for kind in ("quaternary", "ternary"):
        tbl = summary["sweep"][kind]
        k = max(tbl, key=lambda b: tbl[b]["nlmc_mean"])
        best[kind] = dict(bias=float(k), **tbl[k])
    summary["best"] = best
    q, t = best["quaternary"]["nlmc_mean"], best["ternary"]["nlmc_mean"]
    summary["quaternary_advantage"] = float(q - t)
    summary["quaternary_advantage_pct"] = float((q - t) / max(t, 1e-9) * 100)
    print(f"\nBest of each, each at its own drive:")
    for kind, v in best.items():
        print(f"  {kind:>12}: NL-MC {v['nlmc_mean']:.3f} at bias {v['bias']:g}, "
              f"{v['fraction_driven'] * 100:.0f}% of segments usefully driven")
    print(f"  quaternary advantage: {q - t:+.3f} "
          f"({summary['quaternary_advantage_pct']:+.0f}%)")

    # --- the decisive comparison: temperature ---------------------------------
    print("\nTemperature sweep, each design at its own best drive:")
    jobs_t = [(k, t, best[k]["bias"], s)
              for k in ("quaternary", "ternary")
              for t in TEMPERATURES for s in SEEDS]
    with Pool(initializer=_init, initargs=(OPS,)) as pool:
        recs_t = list(pool.imap_unordered(job_temperature, jobs_t, chunksize=2))
    summary["temperature"] = {}
    for kind in ("quaternary", "ternary"):
        vals = {}
        for t in TEMPERATURES:
            sub = [r["nlmc"] for r in recs_t
                   if r["kind"] == kind and r["temp"] == t]
            vals[str(t)] = float(np.mean(sub)) if sub else float("nan")
        base = vals[str(300.0)]
        drift = max(abs(v - base) for v in vals.values())
        summary["temperature"][kind] = dict(
            values=vals, nlmc_300k=base, max_abs_drift=float(drift),
            rel_drift_pct=float(drift / max(base, 1e-9) * 100))
        e = summary["temperature"][kind]
        print(f"  {kind:>12}: NL-MC {base:.3f} at 300 K, largest drift over "
              f"275-325 K {drift:.3f} ({e['rel_drift_pct']:.1f}%)")

    # how much of the ternary's capacity comes from coercive-field disorder
    for kind in ("quaternary", "ternary"):
        arr = build(kind, op)
        summary["designs"][kind]["switching_rate_decades"] = \
            switching_rate_decades(arr, best[kind]["bias"])
        print(f"  {kind:>12}: switching rate spread across the array at its "
              f"drive: {summary['designs'][kind]['switching_rate_decades']:.1f}"
              f" decades")

    with open(os.path.join(C.OUT_DIR, "ternary_control.json"), "w",
              encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    print(f"\nWrote {C.OUT_DIR}/ternary_control.json "
          f"({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
