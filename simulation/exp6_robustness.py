"""Stage 6: robustness of the design rule.

Four sweeps a referee will ask for, each of which could falsify the claim:

  A  temperature. The retention barrier puts one decade of tau per ~21 K, so
     the whole designed spectrum slides with ambient drift. If a designed
     spectrum is worth having, it should degrade more gracefully under that
     slide than a single time constant tuned to one temperature.
  B  bandgap bowing. The main results use a linear virtual-crystal bandgap.
     If the design rule only survives that approximation it is an artifact.
  C  spectral span. How many decades are actually needed, and does a discrete
     two- or three-value ladder capture most of the benefit?
  D  discretization and virtual-node count, i.e. numerical convergence.

Output: results/robustness.json
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import threadcap  # noqa: F401  (must precede numpy)

import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C
from alscgan_rc import arrays, benchmarks
from alscgan_rc.device import SegmentedFilm
from alscgan_rc.materials import BOWED, DEFAULT

np.seterr(over="raise", divide="raise", invalid="raise", under="ignore")

N_PADS = 4
TEMPERATURES = [275.0, 285.0, 300.0, 315.0, 325.0]
SPANS = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
LADDER_SIZES = [1, 2, 3, 4, 6, 8, 12, 16]
N_SEG_GRID = [4, 8, 16, 32, 64]
M_GRID = [10, 25, 50, 100]
OPS = None


def _init(ops):
    global OPS
    OPS = ops
    np.seterr(over="raise", divide="raise", invalid="raise", under="ignore")


def evaluate(arr, op, input_seed, mask_seed, m_virtual=None, theta=None,
             rebuild=None):
    """Return (nonlinear memory capacity, linear memory capacity, NARMA).

    The primary metric is nonlinear memory: NARMA-10 is reported but cannot
    carry a robustness argument on its own, since a delay line beats the pad
    on it (see LIMITATIONS L11).
    """
    kw = dict(n_virtual=m_virtual or C.M_VIRTUAL,
              theta=theta or op["theta"], bias=op["bias"], gain=op["gain"],
              scheme=C.SCHEME, mask_spread=op["mask_spread"],
              readout=C.READOUT, mask_seed=mask_seed,
              feedback=op.get("feedback", C.FEEDBACK),
              feedback_delay=C.FEEDBACK_DELAY)
    ub = C.binary_inputs(input_seed)
    _, nlmc = benchmarks.nonlinear_memory_profile(
        arr.states(ub, **kw), ub, C.N_WASHOUT, C.N_TRAIN,
        d_max=C.D_MAX_NL, order=C.PARITY_ORDER)
    u = C.inputs(input_seed)
    x = (rebuild() if rebuild else arr).states(u, **kw)
    nrmse, _, _ = benchmarks.narma_nrmse(x, u, C.NARMA_ORDER, C.N_WASHOUT,
                                         C.N_TRAIN)
    _, mc = benchmarks.memory_capacity(x, u, C.N_WASHOUT, C.N_TRAIN,
                                       d_max=C.D_MAX)
    return float(nlmc), float(mc), float(nrmse)


def job_temperature(args):
    design, temp, input_seed, mask_seed = args
    op = OPS[design]
    lo, hi = op["tau_lo"], op["tau_hi"]
    kw = dict(n_seg=C.N_SEG, temperature_k=temp)
    if design == "graded":
        arr = arrays.graded_array(N_PADS, lo, hi, C.EC_TARGET, **kw)
    elif design == "homogeneous":
        arr = arrays.homogeneous_array(N_PADS, lo, hi, C.EC_TARGET, **kw)
    else:
        arr = arrays.uniform_array(N_PADS, float(np.sqrt(lo * hi)),
                                   C.EC_TARGET, **kw)
    nl, m, n = evaluate(arr, op, input_seed, mask_seed)
    return dict(kind="temperature", nlmc=nl, design=design, temperature=temp,
                input_seed=input_seed, mask_seed=mask_seed, nrmse=n, mc=m,
                tau_lo=float(arr.tau_pool().min()),
                tau_hi=float(arr.tau_pool().max()))


def job_bowing(args):
    design, model_name, input_seed, mask_seed = args
    op = OPS[design]
    model = DEFAULT if model_name == "linear" else BOWED
    lo, hi = op["tau_lo"], op["tau_hi"]
    kw = dict(n_seg=C.N_SEG, model=model)
    if design == "graded":
        arr = arrays.graded_array(N_PADS, lo, hi, C.EC_TARGET, **kw)
    elif design == "homogeneous":
        arr = arrays.homogeneous_array(N_PADS, lo, hi, C.EC_TARGET, **kw)
    else:
        arr = arrays.uniform_array(N_PADS, float(np.sqrt(lo * hi)),
                                   C.EC_TARGET, **kw)
    nl, m, n = evaluate(arr, op, input_seed, mask_seed)
    return dict(kind="bowing", nlmc=nl, design=design, model=model_name,
                input_seed=input_seed, mask_seed=mask_seed, nrmse=n, mc=m)


def job_span(args):
    span, input_seed, mask_seed = args
    op = OPS["graded"]
    center = float(np.sqrt(op["tau_lo"] * op["tau_hi"]))
    lo = center / 10 ** (span / 2)
    hi = center * 10 ** (span / 2)
    if span == 0.0:
        arr = arrays.uniform_array(N_PADS, center, C.EC_TARGET, n_seg=C.N_SEG)
    else:
        arr = arrays.graded_array(N_PADS, lo, hi, C.EC_TARGET, n_seg=C.N_SEG)
    nl, m, n = evaluate(arr, op, input_seed, mask_seed)
    return dict(kind="span", nlmc=nl, span=span, input_seed=input_seed,
                mask_seed=mask_seed, nrmse=n, mc=m)


def job_ladder(args):
    n_levels, input_seed, mask_seed = args
    op = OPS["graded"]
    lo, hi = op["tau_lo"], op["tau_hi"]
    taus = np.logspace(np.log10(lo), np.log10(hi), max(n_levels, 1))
    if n_levels == 1:
        taus = np.array([float(np.sqrt(lo * hi))])
    per_pad = np.array_split(taus, N_PADS) if n_levels >= N_PADS else None
    films = []
    for p in range(N_PADS):
        sub = per_pad[p] if per_pad is not None else taus
        films.append(SegmentedFilm.tau_ladder(sub, C.EC_TARGET))
    arr = arrays.PadArray(films, f"ladder{n_levels}")
    nl, m, n = evaluate(arr, op, input_seed, mask_seed)
    return dict(kind="ladder", nlmc=nl, n_levels=int(n_levels), input_seed=input_seed,
                mask_seed=mask_seed, nrmse=n, mc=m,
                distinct=int(len(np.unique(np.round(np.log10(arr.tau_pool()), 6)))))


def job_converge(args):
    n_seg, m_virtual, input_seed, mask_seed = args
    op = OPS["graded"]
    theta = op["theta"] * (C.M_VIRTUAL / m_virtual)   # hold the frame duration
    arr = arrays.graded_array(N_PADS, op["tau_lo"], op["tau_hi"], C.EC_TARGET,
                              n_seg=n_seg)
    nl, m, n = evaluate(arr, op, input_seed, mask_seed,
                         m_virtual=m_virtual, theta=theta)
    return dict(kind="converge", nlmc=nl, n_seg=n_seg, m_virtual=m_virtual,
                input_seed=input_seed, mask_seed=mask_seed, nrmse=n, mc=m)


def agg(records, keys, group):
    """Mean and std of nrmse/mc grouped by the given key tuple."""
    out = {}
    for r in records:
        k = tuple(r[g] for g in group)
        out.setdefault(k, {"nrmse": [], "mc": [], "nlmc": []})
        out[k]["nrmse"].append(r["nrmse"])
        out[k]["mc"].append(r["mc"])
        out[k]["nlmc"].append(r["nlmc"])

    def stat(vals):
        return (float(np.mean(vals)),
                float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0)

    res = {}
    for k, v in sorted(out.items()):
        nm, ns = stat(v["nrmse"])
        mm, ms = stat(v["mc"])
        lm, ls = stat(v["nlmc"])
        res["|".join(map(str, k))] = dict(
            nrmse_mean=nm, nrmse_std=ns, mc_mean=mm, mc_std=ms,
            nlmc_mean=lm, nlmc_std=ls, n=len(v["nrmse"]))
    return res


def main():
    global OPS
    with open(os.path.join(C.OUT_DIR, "operating_points.json"),
              encoding="utf-8") as fh:
        OPS = json.load(fh)
    t0 = time.time()
    seeds = [(i, m) for i in C.EVAL_INPUT_SEEDS[:5]
             for m in C.EVAL_MASK_SEEDS[:2]]
    summary = {}

    with Pool(initializer=_init, initargs=(OPS,)) as pool:
        print("A. temperature sweep")
        jobs = [(d, t, i, m) for d in ("graded", "homogeneous", "uniform")
                for t in TEMPERATURES for i, m in seeds]
        recs = list(pool.imap_unordered(job_temperature, jobs, chunksize=4))
        summary["temperature"] = agg(recs, None, ["design", "temperature"])
        for design in ("graded", "homogeneous", "uniform"):
            row = [(t, summary["temperature"][f"{design}|{t}"]["nlmc_mean"])
                   for t in TEMPERATURES]
            base = dict(row)[300.0]
            worst = max(abs(v - base) for _, v in row)
            print(f"   {design:>12}: NL-MC at 300 K = {base:.3f}, "
                  f"largest drift over 275-325 K = {worst:.3f} "
                  f"({worst / max(base, 1e-9) * 100:.1f}%)")
            summary.setdefault("temperature_drift", {})[design] = dict(
                nlmc_300k=base, max_abs_drift=float(worst),
                rel_drift_pct=float(worst / max(base, 1e-9) * 100))

        print("B. bandgap-bowing sensitivity")
        jobs = [(d, mm, i, m) for d in ("graded", "homogeneous", "uniform")
                for mm in ("linear", "bowed") for i, m in seeds]
        recs = list(pool.imap_unordered(job_bowing, jobs, chunksize=4))
        summary["bowing"] = agg(recs, None, ["design", "model"])
        for d in ("graded", "homogeneous", "uniform"):
            a = summary["bowing"][f"{d}|linear"]["nlmc_mean"]
            b = summary["bowing"][f"{d}|bowed"]["nlmc_mean"]
            print(f"   {d:>12}: NL-MC linear {a:.3f} vs bowed {b:.3f} "
                  f"({(b - a) / max(a, 1e-9) * 100:+.1f}%)")

        print("C. spectral span and discrete ladders")
        jobs = [(s, i, m) for s in SPANS for i, m in seeds]
        recs = list(pool.imap_unordered(job_span, jobs, chunksize=4))
        summary["span"] = agg(recs, None, ["span"])
        for s in SPANS:
            v = summary["span"][str(s)]
            print(f"   span {s:.1f} dec: NL-MC {v['nlmc_mean']:.3f} "
                  f"+- {v['nlmc_std']:.3f}, linMC {v['mc_mean']:.2f}, "
                  f"NARMA {v['nrmse_mean']:.3f}")

        jobs = [(n, i, m) for n in LADDER_SIZES for i, m in seeds]
        recs = list(pool.imap_unordered(job_ladder, jobs, chunksize=4))
        summary["ladder"] = agg(recs, None, ["n_levels"])
        cont = summary["span"][str(max(SPANS))]["nlmc_mean"]
        for n in LADDER_SIZES:
            v = summary["ladder"][str(n)]
            print(f"   {n:2d} distinct tau: NL-MC {v['nlmc_mean']:.3f} "
                  f"+- {v['nlmc_std']:.3f}, linMC {v['mc_mean']:.2f}")
        summary["ladder_vs_continuum"] = dict(continuum_nlmc=cont)

        print("D. numerical convergence")
        jobs = [(ns, C.M_VIRTUAL, i, m) for ns in N_SEG_GRID
                for i, m in seeds[:4]]
        recs = list(pool.imap_unordered(job_converge, jobs, chunksize=2))
        # group by BOTH axes: the lookup below and figure 5 key on
        # "<n_seg>|<m_virtual>"
        summary["n_seg"] = agg(recs, None, ["n_seg", "m_virtual"])
        for ns in N_SEG_GRID:
            v = summary["n_seg"].get(f"{ns}|{C.M_VIRTUAL}")
            if v:
                print(f"   segments/pad {ns:3d}: NL-MC {v['nlmc_mean']:.3f} "
                      f"linMC {v['mc_mean']:.2f}")

        jobs = [(C.N_SEG, mv, i, m) for mv in M_GRID for i, m in seeds[:4]]
        recs = list(pool.imap_unordered(job_converge, jobs, chunksize=2))
        summary["m_virtual"] = agg(recs, None, ["n_seg", "m_virtual"])
        for mv in M_GRID:
            k = f"{C.N_SEG}|{mv}"
            if k in summary["m_virtual"]:
                v = summary["m_virtual"][k]
                print(f"   virtual nodes {mv:4d}: NL-MC {v['nlmc_mean']:.3f} "
                      f"linMC {v['mc_mean']:.2f}")

    with open(os.path.join(C.OUT_DIR, "robustness.json"), "w",
              encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    print(f"\nWrote {C.OUT_DIR}/robustness.json  ({time.time()-t0:.0f} s)")


if __name__ == "__main__":
    main()
