"""Stage 5: reproducibility under realistic imperfection.

A reproducibility claim made in a noiseless deterministic simulation is empty:
two copies of a designed pad are bit-identical, so the designed arm has zero
device-to-device variance by construction. The claim only means something as a
VARIANCE statement under matched imperfection, which is what this stage
measures. Every arm receives the same deposition noise, the same
cycle-to-cycle coercive-field jitter and the same readout noise; the arms
differ only in whether the composition profile was designed or drawn at random
per device.

A second issue surfaced while building this stage, and is reported rather than
hidden. The pad array produces many more state columns than independent
dynamical directions (participation ratio near unity for 200 columns), so the
ridge readout is severely ill-conditioned. Selecting the regularization for
single-device accuracy alone picks an essentially unregularized solution,
whose large cancelling weights are exact on the device they were fitted to and
meaningless on any other. Cross-device transfer therefore has to be studied as
a function of regularization rather than at one arbitrary value - otherwise
the metric reports conditioning rather than reproducibility. Section B does
that on the selection seeds; section A then uses the regularization it picks.

Metrics, in increasing order of operational relevance:
  1. inter-device standard deviation of the task error
  2. inter-device correlation of the state matrices under identical input
  3. readout transfer - fit on one device, run unchanged on the others, both
     with label-free per-channel recalibration (one unlabelled run) and
     strictly (ship the source normalization too)

Output: results/reproducibility.json
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
from alscgan_rc.reservoir import (_nrmse, _split, ridge_fit, ridge_predict,
                                  standardizer)

np.seterr(over="raise", divide="raise", invalid="raise", under="ignore")

N_DEVICES = 20
N_PADS = 4
SIGMA_GRID = [0.0, 0.005, 0.01, 0.02, 0.03, 0.05]
EC_JITTER_GRID = [0.0, 0.01, 0.03]
# extends well above 60 dB: at 60 dB the pad is still measurably short of its
# noiseless performance, so the grid has to reach the point where readout
# noise stops mattering or the experimental specification cannot be quoted
SNR_DB_GRID = [np.inf, 90.0, 80.0, 70.0, 60.0, 50.0, 45.0, 40.0, 35.0, 30.0,
               25.0, 20.0]
LAM_TRANSFER_GRID = [1e-6, 1e-4, 1e-2, 1e-1, 1e0, 1e1, 1e2, 1e3, 1e4, 1e5]
ARMS = ["graded", "stochastic", "homogeneous"]
OPS = None
_SIGNAL_RMS = {}


def _init(ops):
    global OPS
    OPS = ops
    np.seterr(over="raise", divide="raise", invalid="raise", under="ignore")


# --- device construction ------------------------------------------------------
def make_device(design, sigma, ec_jitter, read_noise, rng, op):
    kw = dict(n_seg=C.N_SEG)
    lo, hi = op["tau_lo"], op["tau_hi"]
    noise_kw = {}
    if ec_jitter > 0 or read_noise > 0:
        noise_kw = dict(ec_jitter=ec_jitter, read_noise=read_noise, rng=rng)
    if design == "graded":
        arr = arrays.graded_array(N_PADS, lo, hi, C.EC_TARGET, **kw, **noise_kw)
    elif design == "stochastic":
        arr = arrays.stochastic_array(N_PADS, lo, hi, C.EC_TARGET, rng,
                                      **kw, **noise_kw)
    elif design == "homogeneous":
        arr = arrays.homogeneous_array(N_PADS, lo, hi, C.EC_TARGET,
                                       **kw, **noise_kw)
    else:
        raise ValueError(design)
    if sigma > 0:
        arr = arrays.with_composition_noise(arr, sigma, rng)
    return arr


def drive(arr, u, op, mask_seed=None):
    return arr.states(u, n_virtual=C.M_VIRTUAL, theta=op["theta"],
                      bias=op["bias"], gain=op["gain"], scheme=C.SCHEME,
                      mask_spread=op["mask_spread"], readout=C.READOUT,
                      mask_seed=mask_seed or C.EVAL_MASK_SEEDS[0],
                      feedback=op.get("feedback", C.FEEDBACK),
                      feedback_delay=C.FEEDBACK_DELAY)


def signal_rms(op):
    """RMS of the noiseless per-slot charge signal; the SNR reference level."""
    key = (op["theta"], op["bias"], op["gain"], op["mask_spread"],
           op["tau_lo"], op["tau_hi"])
    if key not in _SIGNAL_RMS:
        u = C.inputs(C.SELECT_SEEDS[0], n=400)
        arr = arrays.graded_array(N_PADS, op["tau_lo"], op["tau_hi"],
                                  C.EC_TARGET, n_seg=C.N_SEG)
        x = drive(arr, u, op)
        _SIGNAL_RMS[key] = float(np.sqrt(np.mean(x[C.N_WASHOUT:] ** 2)))
    return _SIGNAL_RMS[key]


def job_states(args):
    """One device: its state matrix (float32) and its own-device task error."""
    design, sigma, ec_jitter, snr_db, device_id, input_seed = args
    op = OPS["graded"]        # one shared drive line for every arm
    u = C.inputs(input_seed)
    rng = np.random.default_rng(90000 + device_id * 131 + input_seed)
    read_noise = 0.0 if not np.isfinite(snr_db) else (
        signal_rms(op) * 10 ** (-snr_db / 20.0))
    arr = make_device(design, sigma, ec_jitter, read_noise, rng, op)
    x = drive(arr, u, op)
    nrmse, _, _ = benchmarks.narma_nrmse(x, u, C.NARMA_ORDER, C.N_WASHOUT,
                                         C.N_TRAIN)
    return dict(design=design, sigma=sigma, ec_jitter=ec_jitter,
                snr_db=float(snr_db), device_id=device_id,
                input_seed=input_seed, nrmse=float(nrmse),
                states=x.astype(np.float32))


# --- group-level metrics ------------------------------------------------------
def fit_on(x, y, lam):
    xt, yt, _, _ = _split(x, y, C.N_WASHOUT, C.N_TRAIN)
    z = standardizer(xt)
    return z, ridge_fit(z(xt), yt, lam)


def eval_with(x, y, model, calibrated):
    xt, _, xs, ys = _split(x, y, C.N_WASHOUT, C.N_TRAIN)
    z_src, w = model
    z = standardizer(xt) if calibrated else z_src
    return _nrmse(ys, ridge_predict(z(xs), w))


def group_metrics(states, y, lam):
    """Mean own error and mean transfer error, calibrated and strict."""
    models = [fit_on(x, y, lam) for x in states]
    own, cal, strict = [], [], []
    for i, mi in enumerate(models):
        own.append(eval_with(states[i], y, mi, calibrated=True))
        for j, xj in enumerate(states):
            if i == j:
                continue
            cal.append(eval_with(xj, y, mi, calibrated=True))
            strict.append(eval_with(xj, y, mi, calibrated=False))
    return float(np.mean(own)), float(np.mean(cal)), float(np.mean(strict))


def state_correlation(states):
    flat = [x.ravel() for x in states]
    cors = []
    for a, b in itertools.combinations(flat, 2):
        with np.errstate(invalid="ignore", divide="ignore"):
            c = np.corrcoef(a, b)[0, 1]
        if np.isfinite(c):
            cors.append(c)
    return float(np.mean(cors)) if cors else float("nan")


def run_group(pool, design, sigma, ec_jitter, snr_db, seed, n_devices):
    """States for one set of nominally identical devices, in device order.

    Groups are processed one at a time so that only one group of state
    matrices is resident at once.
    """
    jobs = [(design, sigma, ec_jitter, snr_db, i, seed)
            for i in range(n_devices)]
    recs = list(pool.imap(job_states, jobs, chunksize=1))
    recs.sort(key=lambda r: r["device_id"])
    return recs


def main():
    global OPS
    with open(os.path.join(C.OUT_DIR, "operating_points.json"),
              encoding="utf-8") as fh:
        OPS = json.load(fh)
    t0 = time.time()
    eval_seeds = C.EVAL_INPUT_SEEDS[:3]
    summary = {"n_devices": N_DEVICES, "n_pads": N_PADS,
               "eval_seeds": eval_seeds, "select_seeds": C.SELECT_SEEDS}

    with Pool(initializer=_init, initargs=(OPS,)) as pool:
        # --- B: accuracy versus transferability, on the SELECTION seeds -----
        print("B. regularization versus transferability (selection seeds)")
        summary["lambda_tradeoff"] = {}
        sel_seed = C.SELECT_SEEDS[0]
        y_sel = benchmarks.narma_target(C.inputs(sel_seed), C.NARMA_ORDER)
        best_lam = LAM_TRANSFER_GRID[0]
        for arm in ("graded", "stochastic"):
            recs = run_group(pool, arm, 0.01, 0.0, np.inf, sel_seed, 8)
            states = [r["states"] for r in recs]
            rows = {}
            for lam in LAM_TRANSFER_GRID:
                own, cal, strict = group_metrics(states, y_sel, lam)
                rows[f"{lam:g}"] = dict(own=own, transfer=cal,
                                        transfer_strict=strict,
                                        penalty=cal - own)
            summary["lambda_tradeoff"][arm] = rows
            if arm == "graded":
                best_lam = min(LAM_TRANSFER_GRID,
                               key=lambda L: rows[f"{L:g}"]["transfer"])
            print(f"   {arm}:")
            print(f"   {'lambda':>9} {'own':>8} {'transfer':>10} "
                  f"{'strict':>12} {'penalty':>9}")
            for lam in LAM_TRANSFER_GRID:
                r = rows[f"{lam:g}"]
                print(f"   {lam:9.0e} {r['own']:8.4f} {r['transfer']:10.4f} "
                      f"{r['transfer_strict']:12.4g} {r['penalty']:+9.4f}")
        summary["lam_transfer"] = best_lam
        print(f"   selected transfer regularization: lambda = {best_lam:g} "
              f"({time.time() - t0:.0f} s)")

        # --- A: deposition-noise sweep at that regularization ---------------
        n_groups = len(ARMS) * len(SIGMA_GRID) * len(eval_seeds)
        print(f"\nA. deposition-noise sweep ({n_groups} groups of "
              f"{N_DEVICES} devices)")
        summary["sigma_sweep"] = {str(s): {} for s in SIGMA_GRID}
        print(f"{'sigma':>7} {'design':>12} {'NRMSE':>9} {'inter-dev sd':>13} "
              f"{'state corr':>11} {'transfer':>10} {'strict':>12}")
        for sigma in SIGMA_GRID:
            for design in ARMS:
                errs, sds, cors, cals, raws = [], [], [], [], []
                for seed in eval_seeds:
                    recs = run_group(pool, design, sigma, 0.0, np.inf, seed,
                                     N_DEVICES)
                    states = [r["states"] for r in recs]
                    vals = np.array([r["nrmse"] for r in recs])
                    y = benchmarks.narma_target(C.inputs(seed), C.NARMA_ORDER)
                    own, cal, strict = group_metrics(states, y, best_lam)
                    errs.append(vals.mean())
                    sds.append(vals.std(ddof=1))
                    cors.append(state_correlation(states))
                    cals.append(cal - own)
                    raws.append(strict - own)
                entry = dict(nrmse_mean=float(np.mean(errs)),
                             inter_device_std=float(np.mean(sds)),
                             state_corr=float(np.nanmean(cors)),
                             transfer_penalty=float(np.mean(cals)),
                             transfer_penalty_strict=float(np.mean(raws)))
                summary["sigma_sweep"][str(sigma)][design] = entry
                print(f"{sigma:7.3f} {design:>12} {entry['nrmse_mean']:9.4f} "
                      f"{entry['inter_device_std']:13.5f} "
                      f"{entry['state_corr']:11.4f} "
                      f"{entry['transfer_penalty']:10.4f} "
                      f"{entry['transfer_penalty_strict']:12.4g}")

        # --- fabrication budget ---------------------------------------------
        # Defined on the readout transfer penalty rather than on the spread of
        # task error. Once deposition noise dominates, both arms carry the
        # same noise and their error spreads converge; the transfer penalty
        # keeps separating them because it asks whether two devices implement
        # the same function, which is the question production poses.
        print("\nFabrication budget (graded versus stochastic, "
              "paired across input realizations):")
        summary["tolerance"] = {}
        # ten pairs, not six: with six the Wilcoxon signed-rank floor
        # is p = 1/32 = 0.031, so every significant row sits at the
        # test's minimum and the p-value carries no information about
        # effect size
        tol_seeds = C.EVAL_INPUT_SEEDS[:10]
        n_dev = 10
        for sigma in SIGMA_GRID:
            pen_g, pen_s, sd_g, sd_s = [], [], [], []
            for seed in tol_seeds:
                y = benchmarks.narma_target(C.inputs(seed), C.NARMA_ORDER)
                for arm, pen, sd in (("graded", pen_g, sd_g),
                                     ("stochastic", pen_s, sd_s)):
                    recs = run_group(pool, arm, sigma, 0.0, np.inf, seed,
                                     n_dev)
                    st = [r["states"] for r in recs]
                    own, cal, _ = group_metrics(st, y, best_lam)
                    pen.append(cal - own)
                    sd.append(float(np.std([r["nrmse"] for r in recs],
                                           ddof=1)))
            dg = np.array(pen_g) - np.array(pen_s)
            try:
                pv = float(stats.wilcoxon(dg).pvalue) if np.any(dg) else 1.0
            except ValueError:
                pv = float("nan")
            summary["tolerance"][str(sigma)] = dict(
                transfer_penalty_graded=float(np.mean(pen_g)),
                transfer_penalty_stochastic=float(np.mean(pen_s)),
                penalty_ratio=float(np.mean(pen_s)
                                    / max(np.mean(pen_g), 1e-9)),
                device_sd_graded=float(np.mean(sd_g)),
                device_sd_stochastic=float(np.mean(sd_s)),
                paired_p=pv, n_pairs=len(tol_seeds))
            e = summary["tolerance"][str(sigma)]
            print(f"  sigma={sigma:5.3f}: transfer penalty graded="
                  f"{e['transfer_penalty_graded']:.4f} stochastic="
                  f"{e['transfer_penalty_stochastic']:.4f} "
                  f"(ratio {e['penalty_ratio']:5.2f}x), paired p={pv:.3g}")
        indist = [float(k) for k, v in sorted(summary["tolerance"].items(),
                                              key=lambda kv: float(kv[0]))
                  if float(k) > 0 and (not np.isfinite(v["paired_p"])
                                       or v["paired_p"] > 0.05)]
        summary["sigma_star"] = min(indist) if indist else None
        print(f"  fabrication budget: the designed spread stops being "
              f"measurably more transferable at sigma = "
              f"{summary['sigma_star']} in cation fraction")

        # --- C: measurement noise and switching jitter ----------------------
        # The state matrix carries far fewer independent directions than
        # columns, so the readout leans on very small signals. Whether the
        # design advantage survives a real charge amplifier is therefore a
        # question the paper has to answer, not assume - so both the spread
        # and the single-time-constant arm are swept here.
        n_groups = len(EC_JITTER_GRID) * len(SNR_DB_GRID) + len(SNR_DB_GRID)
        print(f"\nC. measurement noise and switching jitter "
              f"({n_groups} groups)")
        summary["noise_sweep"] = {}
        print(f"{'design':>12} {'Ec jitter':>10} {'SNR (dB)':>9} "
              f"{'NRMSE':>18}")
        for jit in EC_JITTER_GRID:
            for snr in SNR_DB_GRID:
                recs = run_group(pool, "graded", 0.01, jit, snr,
                                 eval_seeds[0], 8)
                vals = np.array([r["nrmse"] for r in recs])
                key = f"{jit}_{'inf' if not np.isfinite(snr) else snr}"
                summary["noise_sweep"][key] = dict(
                    nrmse_mean=float(vals.mean()),
                    nrmse_std=float(vals.std(ddof=1)))
                label = "inf" if not np.isfinite(snr) else f"{snr:.0f}"
                print(f"{'graded':>12} {jit:10.3f} {label:>9} "
                      f"{vals.mean():11.4f} +- {vals.std(ddof=1):.4f}")

        summary["noise_sweep_homogeneous"] = {}
        for snr in SNR_DB_GRID:
            recs = run_group(pool, "homogeneous", 0.01, 0.0, snr,
                             eval_seeds[0], 8)
            vals = np.array([r["nrmse"] for r in recs])
            key = f"0.0_{'inf' if not np.isfinite(snr) else snr}"
            summary["noise_sweep_homogeneous"][key] = dict(
                nrmse_mean=float(vals.mean()),
                nrmse_std=float(vals.std(ddof=1)))
            label = "inf" if not np.isfinite(snr) else f"{snr:.0f}"
            print(f"{'homogeneous':>12} {0.0:10.3f} {label:>9} "
                  f"{vals.mean():11.4f} +- {vals.std(ddof=1):.4f}")

        # the SNR at which the spread advantage is no longer resolvable
        gap = {}
        for snr in SNR_DB_GRID:
            key = f"0.0_{'inf' if not np.isfinite(snr) else snr}"
            g = summary["noise_sweep"].get(key, {}).get("nrmse_mean")
            h = summary["noise_sweep_homogeneous"].get(key, {}).get("nrmse_mean")
            if g is not None and h is not None:
                gap["inf" if not np.isfinite(snr) else f"{snr:g}"] = float(h - g)
        summary["snr_gap"] = gap
        print("  spread advantage (homogeneous minus graded NRMSE) versus SNR:")
        for k, v in gap.items():
            print(f"    {k:>5} dB: {v:+.4f}")

    with open(os.path.join(C.OUT_DIR, "reproducibility.json"), "w",
              encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    print(f"\nWrote {C.OUT_DIR}/reproducibility.json  "
          f"({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
