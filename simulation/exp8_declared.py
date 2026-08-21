"""Stage 8: four quantities the earlier stages do not archive.

Each is measured here under the stage-4 protocol - evaluation seeds, paired
(mask, input) realizations - so that every number the manuscript quotes has a
reproducible source:

  1. the interleaved comb design against the partitioned (graded) design,
     paired over the same realizations at every channel count;
  2. field-free dwell slots between input samples, driven open-loop;
  3. the condition number and numerical rank of the training Gram matrix;
  4. the segment-permutation invariance check, at 600 and 3000 field steps.

Output: results/declared.json
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
from scipy import stats

import config as C
from alscgan_rc import arrays, benchmarks
from alscgan_rc.device import SegmentedFilm
from alscgan_rc.reservoir import standardizer, select_lambda

np.seterr(over="raise", divide="raise", invalid="raise", under="ignore")

PAD_COUNTS = [1, 2, 4, 8]
OPS = None


def _init(ops):
    global OPS
    OPS = ops
    np.seterr(over="raise", divide="raise", invalid="raise", under="ignore")


def drive(arr, signal, op, mask_seed, **over):
    kw = dict(n_virtual=C.M_VIRTUAL, theta=op["theta"], bias=op["bias"],
              gain=op["gain"], scheme=C.SCHEME,
              mask_spread=op["mask_spread"], readout=C.READOUT,
              mask_seed=mask_seed, feedback=op.get("feedback", 0.0),
              feedback_delay=C.FEEDBACK_DELAY)
    kw.update(over)
    return arr.states(signal, **kw)


def _profile(x, ub):
    acc, cap = benchmarks.nonlinear_memory_profile(
        x, ub, C.N_WASHOUT, C.N_TRAIN, d_max=C.D_MAX_NL, order=C.PARITY_ORDER)
    return np.asarray(acc, dtype=float), float(cap)


def _nlmc(x, ub):
    return _profile(x, ub)[1]


# --- 1. interleaved comb against the partitioned design ----------------------

def job_interleaved(args):
    n_pads, mask_seed, input_seed = args
    op = OPS["graded"]
    lo, hi = op["tau_lo"], op["tau_hi"]
    ub = C.binary_inputs(input_seed)
    g = arrays.graded_array(n_pads, lo, hi, C.EC_TARGET, n_seg=C.N_SEG)
    i = arrays.interleaved_array(n_pads, lo, hi, C.EC_TARGET, n_seg=C.N_SEG)
    return dict(n_pads=n_pads, mask_seed=mask_seed, input_seed=input_seed,
                graded=_nlmc(drive(g, ub, op, mask_seed), ub),
                interleaved=_nlmc(drive(i, ub, op, mask_seed), ub))


# --- 2. field-free dwell slots, open loop ------------------------------------

def job_dwell(args):
    rest, mask_seed, input_seed = args
    op = dict(OPS["graded"])
    op["feedback"] = 0.0                    # the claim is about the open loop
    lo, hi = op["tau_lo"], op["tau_hi"]
    ub = C.binary_inputs(input_seed)
    arr = arrays.graded_array(4, lo, hi, C.EC_TARGET, n_seg=C.N_SEG)
    acc, cap = _profile(drive(arr, ub, op, mask_seed, rest_slots=rest), ub)
    return dict(rest_slots=rest, mask_seed=mask_seed, input_seed=input_seed,
                nlmc=cap, acc=acc.tolist())


# --- 3. conditioning of the training Gram matrix -----------------------------

def gram_condition(x_states):
    """Condition number of the ridge design matrix's Gram, as actually formed.

    ridge_fit appends an unpenalized intercept to the z-scored states and
    solves (A'A + lam I) w = A'y, so A'A is the matrix whose conditioning
    decides whether the unregularized solution is meaningful.
    """
    xt = x_states[C.N_WASHOUT:C.N_WASHOUT + C.N_TRAIN]
    z = standardizer(xt)(xt)
    a = np.hstack([z, np.ones((len(z), 1))])
    sv = np.linalg.svd(a, compute_uv=False)
    lo = sv[-1]
    cond_a = float(sv[0] / lo) if lo > 0 else float("inf")
    return dict(cond_gram=cond_a ** 2, cond_design=cond_a,
                sv_max=float(sv[0]), sv_min=float(lo),
                n_columns=int(a.shape[1]),
                rank=int(np.linalg.matrix_rank(a)))


# --- 4. permutation invariance at the quoted step count ----------------------

def invariance(n_steps):
    """Permutation invariance on the same demo film validate.py uses.

    Same film, same dt and same tolerance as validate.py, so the two are
    directly comparable; only the step count varies.
    """
    rng = np.random.default_rng(0)
    film = SegmentedFilm.graded_iso_ec(24, 0.15, 0.60, C.EC_TARGET)
    perm = rng.permutation(film.n)
    shuffled = SegmentedFilm(film.x_ga[perm], film.y_sc[perm])
    fields = rng.uniform(-1.5 * C.EC_TARGET, 1.5 * C.EC_TARGET, n_steps)
    a = film.run(fields, 3e-3)
    b = shuffled.run(fields, 3e-3)
    return float(np.max(np.abs(a - b)))


def main():
    global OPS
    with open(os.path.join(C.OUT_DIR, "operating_points.json"),
              encoding="utf-8") as fh:
        OPS = json.load(fh)
    out = {}
    t0 = time.time()

    # ---- 1. interleaved -----------------------------------------------------
    jobs = [(p, m, i) for p in PAD_COUNTS
            for m in C.EVAL_MASK_SEEDS for i in C.EVAL_INPUT_SEEDS]
    print(f"interleaved vs graded: {len(jobs)} paired runs")
    with Pool(initializer=_init, initargs=(OPS,)) as pool:
        recs = pool.map(job_interleaved, jobs, chunksize=4)
    tbl = {}
    for p in PAD_COUNTS:
        g = np.array([r["graded"] for r in recs if r["n_pads"] == p])
        i = np.array([r["interleaved"] for r in recs if r["n_pads"] == p])
        rel = float((i.mean() - g.mean()) / g.mean() * 100.0)
        try:
            pv = float(stats.wilcoxon(i, g).pvalue)
        except ValueError:                  # identical arms (P = 1)
            pv = 1.0
        tbl[str(p)] = dict(graded_mean=float(g.mean()), graded_std=float(g.std()),
                           interleaved_mean=float(i.mean()),
                           interleaved_std=float(i.std()),
                           rel_pct=rel, wilcoxon_p=pv, n=int(g.size))
        print(f"  P={p}: graded {g.mean():.3f}  interleaved {i.mean():.3f}  "
              f"{rel:+.1f}%  p={pv:.3g}")
    out["interleaved"] = tbl
    worst = min(v["rel_pct"] for v in tbl.values() if v["n"] and v["wilcoxon_p"] < 0.05)
    best = max(v["rel_pct"] for v in tbl.values() if v["n"] and v["wilcoxon_p"] < 0.05)
    out["interleaved_span_pct"] = [worst, best]

    # ---- 2. dwell slots -----------------------------------------------------
    rest_grid = [0, 1, 2, 4]
    ms, is_ = C.EVAL_MASK_SEEDS[:5], C.EVAL_INPUT_SEEDS[:5]
    jobs = [(r, m, i) for r in rest_grid for m in ms for i in is_]
    print(f"\ndwell slots (open loop): {len(jobs)} runs")
    with Pool(initializer=_init, initargs=(OPS,)) as pool:
        recs = pool.map(job_dwell, jobs, chunksize=2)
    dwell = {}
    for r in rest_grid:
        v = np.array([q["nlmc"] for q in recs if q["rest_slots"] == r])
        acc = np.array([q["acc"] for q in recs if q["rest_slots"] == r])
        # capacity contribution per delay, averaged over realizations
        contrib = np.mean(np.maximum(2.0 * acc - 1.0, 0.0) ** 2, axis=0)
        dwell[str(r)] = dict(nlmc_mean=float(v.mean()), nlmc_std=float(v.std()),
                             n=int(v.size), acc_mean=acc.mean(axis=0).tolist(),
                             capacity_by_delay=contrib.tolist())
        print(f"  rest_slots={r}: {v.mean():.3f} +- {v.std():.3f}")
    out["dwell"] = dwell
    # rest_slots = 0 IS the open-loop configuration, so its profile is the
    # archived source for the delay-resolved open-loop parity the paper quotes
    base = dwell["0"]
    out["open_loop_parity"] = dict(
        nlmc_mean=base["nlmc_mean"], nlmc_std=base["nlmc_std"], n=base["n"],
        acc_mean=base["acc_mean"], capacity_by_delay=base["capacity_by_delay"])
    print("  open-loop parity accuracy by delay: "
          + ", ".join(f"{a:.3f}" for a in base["acc_mean"][:5]))
    print("  capacity by delay: "
          + ", ".join(f"{c:.3f}" for c in base["capacity_by_delay"][:5]))

    # ---- 3. conditioning ----------------------------------------------------
    print("\nconditioning of the training Gram matrix")
    _init(OPS)
    op = OPS["graded"]
    ub = C.binary_inputs(C.EVAL_INPUT_SEEDS[0])
    cond = {}
    for name, n_pads in (("graded_1", 1), ("graded_4", 4)):
        arr = arrays.graded_array(n_pads, op["tau_lo"], op["tau_hi"],
                                  C.EC_TARGET, n_seg=C.N_SEG)
        x = drive(arr, ub, op, C.EVAL_MASK_SEEDS[0])
        c = gram_condition(x)
        c["participation_ratio"] = benchmarks.effective_rank(x, C.N_WASHOUT)
        cond[name] = c
        print(f"  {name}: {c['n_columns']} columns, rank {c['rank']}, "
              f"cond(Gram) = {c['cond_gram']:.3e}, "
              f"participation ratio {c['participation_ratio']:.2f}")
    out["conditioning"] = cond

    # ---- 4. invariance ------------------------------------------------------
    print("\npermutation invariance")
    inv = {}
    for n in (600, 3000):
        inv[str(n)] = invariance(n)
        print(f"  {n} field steps: max |difference| = {inv[str(n)]:.3e}")
    out["invariance_max_abs_diff"] = inv

    path = os.path.join(C.OUT_DIR, "declared.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(f"\nwrote {path}  ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
