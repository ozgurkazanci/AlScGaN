"""Stage 1b: push the grid edges out until the optimum is interior.

The stage-1 search returned optima sitting on grid boundaries for the slot
duration and, for the composition-spread design, for the spectral span. A
boundary optimum is not an optimum - it only says the search stopped there -
and the span is the paper's own claim variable, so it cannot be left truncated.

This stage widens exactly those axes around each design's selected point and
rewrites results/operating_points.json in place, keeping everything else
fixed. Scoring is on the same selection seeds, so nothing reported later has
seen this search.
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
from exp1_select import D_MAX_SEL, N_PADS_SELECT, SEL_SEEDS, build, tau_window
from alscgan_rc import benchmarks

np.seterr(over="raise", divide="raise", invalid="raise", under="ignore")

THETA_GRID = [2.5e-4, 5e-4, 1e-3, 2e-3, 5e-3]
SPAN_GRID = [0.25, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
CENTER_GRID = [1.0, 3.0, 10.0, 30.0]
# mask spread is held at each design's stage-1 value; the axes
# that hit a boundary were the slot duration and the span
SPREAD_GRID = None
OPS = None


def _init(ops):
    global OPS
    OPS = ops
    np.seterr(over="raise", divide="raise", invalid="raise", under="ignore")


def score(job):
    design, theta, center, span, spread = job
    op = OPS[design]
    try:
        lo, hi = tau_window(center, span, theta)
        caps = []
        for seed in SEL_SEEDS:
            ub = C.binary_inputs(seed)
            arr = build(design, N_PADS_SELECT, lo, hi,
                        np.random.default_rng(seed))
            x = arr.states(ub, n_virtual=C.M_VIRTUAL, theta=theta,
                           bias=op["bias"], gain=op["gain"], scheme=C.SCHEME,
                           mask_spread=spread, readout=C.READOUT,
                           mask_seed=1000 + seed, feedback=op["feedback"],
                           feedback_delay=C.FEEDBACK_DELAY)
            if not np.all(np.isfinite(x)):
                return job, -1.0
            _, cap = benchmarks.nonlinear_memory_profile(
                x, ub, C.N_WASHOUT, C.N_TRAIN, d_max=D_MAX_SEL,
                order=C.PARITY_ORDER)
            caps.append(cap)
        return job, float(np.mean(caps))
    except (ValueError, FloatingPointError, np.linalg.LinAlgError):
        return job, -1.0


def main():
    global OPS
    path = os.path.join(C.OUT_DIR, "operating_points.json")
    with open(path, encoding="utf-8") as fh:
        OPS = json.load(fh)
    designs = [d for d in OPS if not d.startswith("_") and d != "esn"]
    t0 = time.time()

    jobs = [(d, t, c, s, OPS[d]["mask_spread"]) for d in designs
            for t, c, s in itertools.product(THETA_GRID, CENTER_GRID,
                                             SPAN_GRID)]
    print(f"{len(jobs)} configurations across {len(designs)} designs")
    best = {}
    with Pool(initializer=_init, initargs=(OPS,)) as pool:
        for i, (job, cap) in enumerate(pool.imap_unordered(score, jobs,
                                                           chunksize=4)):
            d = job[0]
            if d not in best or cap > best[d][1]:
                best[d] = (job, cap)
            if (i + 1) % 200 == 0:
                print(f"  {i + 1}/{len(jobs)}  ({time.time() - t0:.0f} s)")

    edges = {"theta": THETA_GRID, "center_mult": CENTER_GRID,
             "span_decades": SPAN_GRID}
    print("\nRefined operating points:")
    any_edge = False
    for d, (job, cap) in sorted(best.items()):
        _, theta, center, span, spread = job
        old = OPS[d]["select_nlmc"]
        lo, hi = tau_window(center, span, theta)
        OPS[d].update(theta=theta, center_mult=center, span_decades=span,
                      mask_spread=spread, tau_lo=lo, tau_hi=hi,
                      select_nlmc=cap, refined=True)
        vals = dict(theta=theta, center_mult=center, span_decades=span)
        hits = [k for k, g in edges.items()
                if vals[k] == min(g) or vals[k] == max(g)]
        OPS[d]["grid_edge_hits"] = hits
        any_edge = any_edge or bool(hits)
        print(f"  {d:>12}: NL-MC {old:.3f} -> {cap:.3f}  theta={theta:g} "
              f"centre={center}xframe span={span}dec spread={spread} "
              f"tau {lo:.3g}-{hi:.3g} s")
        note = ("at grid edge for " + ", ".join(hits)) if hits             else "interior optimum"
        print(f"                {note}")
    OPS["_boundary_hits"] = any_edge
    OPS["_meta"]["refined_axes"] = ["theta", "center_mult",
                                    "span_decades"]

    with open(path, "w", encoding="utf-8") as fh:
        json.dump(OPS, fh, indent=2)
    print(f"\nRewrote {path}  ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
