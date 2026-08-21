"""Stage 5b: the readout-precision specification.

The measurement-noise sweep in stage 5 left two gaps that matter for anyone
attempting the experiment.

First, it stopped at 60 dB, where the pad is still well short of its noiseless
performance - so the sweep bounded the problem without locating it. The grid
here reaches 90 dB, which is enough to find where readout noise stops
mattering.

Second, it measured NARMA-10 error, whereas every claim in this work rests on
nonlinear memory capacity. A specification derived from the wrong metric is
not a specification, so both are measured here, for the composition spread and
for the single-time-constant-per-pad reference, so the question "does the
design advantage survive a real charge amplifier" gets a direct answer.

Merges into results/reproducibility.json under "noise_spec".
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
from alscgan_rc import benchmarks
from exp5_reproducibility import drive, make_device

np.seterr(over="raise", divide="raise", invalid="raise", under="ignore")

SNR_DB_GRID = [np.inf, 100.0, 90.0, 80.0, 70.0, 60.0, 50.0, 40.0, 30.0, 20.0]
EC_JITTER_GRID = [0.0, 0.01, 0.03]
ARMS = ["graded", "homogeneous"]
SEEDS = C.EVAL_INPUT_SEEDS[:5]
SIGMA = 0.0          # isolate readout noise from deposition noise
N_PADS = 4
OPS = None
_RMS = {}


def _init(ops):
    global OPS
    OPS = ops
    np.seterr(over="raise", divide="raise", invalid="raise", under="ignore")


def signal_rms(op):
    key = "rms"
    if key not in _RMS:
        from alscgan_rc import arrays
        u = C.inputs(C.SELECT_SEEDS[0], n=400)
        arr = arrays.graded_array(N_PADS, op["tau_lo"], op["tau_hi"],
                                  C.EC_TARGET, n_seg=C.N_SEG)
        x = drive(arr, u, op)
        _RMS[key] = float(np.sqrt(np.mean(x[C.N_WASHOUT:] ** 2)))
    return _RMS[key]


def job(args):
    arm, jitter, snr, seed = args
    op = OPS["graded"]
    rng = np.random.default_rng(70000 + seed * 17 + int(jitter * 1000))
    noise = 0.0 if not np.isfinite(snr) else (
        signal_rms(op) * 10 ** (-snr / 20.0))
    try:
        ub = C.binary_inputs(seed)
        arr = make_device(arm, SIGMA, jitter, noise, rng, op)
        x = drive(arr, ub, op)
        if not np.all(np.isfinite(x)):
            return None
        _, nlmc = benchmarks.nonlinear_memory_profile(
            x, ub, C.N_WASHOUT, C.N_TRAIN, d_max=C.D_MAX_NL,
            order=C.PARITY_ORDER)
        u = C.inputs(seed)
        rng2 = np.random.default_rng(70000 + seed * 17 + int(jitter * 1000))
        arr2 = make_device(arm, SIGMA, jitter, noise, rng2, op)
        nrmse, _, _ = benchmarks.narma_nrmse(drive(arr2, u, op), u,
                                             C.NARMA_ORDER, C.N_WASHOUT,
                                             C.N_TRAIN)
    except (ValueError, FloatingPointError, np.linalg.LinAlgError):
        return None
    return dict(arm=arm, jitter=jitter, snr=float(snr), seed=seed,
                nlmc=float(nlmc), nrmse=float(nrmse))


def key_of(snr):
    return "inf" if not np.isfinite(snr) else f"{snr:g}"


def main():
    global OPS
    path = os.path.join(C.OUT_DIR, "reproducibility.json")
    with open(path, encoding="utf-8") as fh:
        rep = json.load(fh)
    OPS = rep["operating_points"] if "operating_points" in rep else None
    if OPS is None:
        with open(os.path.join(C.OUT_DIR, "operating_points.json"),
                  encoding="utf-8") as fh:
            OPS = json.load(fh)
    t0 = time.time()

    jobs = [(a, j, s, sd) for a in ARMS for j in EC_JITTER_GRID
            for s in SNR_DB_GRID for sd in SEEDS]
    print(f"{len(jobs)} runs")
    with Pool(initializer=_init, initargs=(OPS,)) as pool:
        recs = [r for r in pool.imap_unordered(job, jobs, chunksize=2) if r]

    spec = {}
    print(f"\n{'arm':>12} {'Ec jitter':>10} {'SNR (dB)':>9} "
          f"{'NL-MC':>15} {'NARMA':>15}")
    for arm in ARMS:
        for j in EC_JITTER_GRID:
            for s in SNR_DB_GRID:
                sub = [r for r in recs if r["arm"] == arm
                       and r["jitter"] == j and r["snr"] == float(s)]
                if not sub:
                    continue
                nl = np.array([r["nlmc"] for r in sub])
                nr = np.array([r["nrmse"] for r in sub])
                spec[f"{arm}_{j}_{key_of(s)}"] = dict(
                    nlmc_mean=float(nl.mean()), nlmc_std=float(nl.std(ddof=1)),
                    nrmse_mean=float(nr.mean()),
                    nrmse_std=float(nr.std(ddof=1)))
                print(f"{arm:>12} {j:10.3f} {key_of(s):>9} "
                      f"{nl.mean():8.3f} +- {nl.std(ddof=1):.3f} "
                      f"{nr.mean():8.4f} +- {nr.std(ddof=1):.4f}")

    # the specification: the SNR at which capacity reaches 95% of noiseless
    print("\nReadout-precision specification (no switching jitter):")
    req = {}
    for arm in ARMS:
        ref = spec[f"{arm}_0.0_inf"]["nlmc_mean"]
        need = None
        for s in sorted((x for x in SNR_DB_GRID if np.isfinite(x))):
            v = spec.get(f"{arm}_0.0_{key_of(s)}")
            if v and v["nlmc_mean"] >= 0.95 * ref:
                need = s
                break
        req[arm] = dict(noiseless_nlmc=ref, snr_for_95pct=need)
        print(f"  {arm:>12}: noiseless capacity {ref:.3f}, reaches 95% of it "
              f"at {need} dB" if need else
              f"  {arm:>12}: noiseless capacity {ref:.3f}, never reaches 95% "
              f"within the swept range")

    # does the design advantage survive a real amplifier?
    print("\nDesign advantage against readout SNR (spread minus single-tau):")
    gap = {}
    for s in SNR_DB_GRID:
        g = spec.get(f"graded_0.0_{key_of(s)}")
        h = spec.get(f"homogeneous_0.0_{key_of(s)}")
        if g and h:
            gap[key_of(s)] = float(g["nlmc_mean"] - h["nlmc_mean"])
            print(f"  {key_of(s):>5} dB: {gap[key_of(s)]:+.3f}")

    rep["noise_spec"] = dict(table=spec, requirement=req, advantage_vs_snr=gap,
                             sigma=SIGMA, seeds=SEEDS)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=2)
    print(f"\nMerged into {path}  ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
