"""Stage 4: the headline benchmark - capability against readout channel count.

The question is not "does composition disorder help" but

    at a fixed number of readout channels, does a continuous time-constant
    spectrum inside each pad beat one time constant per pad?

so every design is compared at matched channel count P and matched feature
count P*M, on one shared drive line and one shared feedback loop, each design
at its own selected operating point (chosen in exp1 on disjoint seeds).

Primary metric: nonlinear memory capacity from delayed parity. No linear
filter of the input can score above chance on it, so it separates computing
from storing - which NARMA-10 does not. NARMA-10 and linear memory capacity
are reported too, each beside the delay-line control that bounds them.

Statistics: 10 mask realizations crossed with 10 input realizations, the same
(mask, input) pairs for every design, so design differences are paired and are
tested with a Wilcoxon signed-rank test.

Output: results/headline_summary.json, results/headline_records.json
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
from alscgan_rc.reservoir import EchoStateNetwork

np.seterr(over="raise", divide="raise", invalid="raise", under="ignore")

PAD_COUNTS = [1, 2, 4, 8]
DESIGNS = ["graded", "homogeneous", "uniform", "stochastic"]
DELAY_TAPS = 30
OPS = None


def _init(ops):
    global OPS
    OPS = ops
    np.seterr(over="raise", divide="raise", invalid="raise", under="ignore")


def build(design, n_pads, op, rng):
    lo, hi = op["tau_lo"], op["tau_hi"]
    kw = dict(n_seg=C.N_SEG)
    if design == "graded":
        return arrays.graded_array(n_pads, lo, hi, C.EC_TARGET, **kw)
    if design == "homogeneous":
        return arrays.homogeneous_array(n_pads, lo, hi, C.EC_TARGET, **kw)
    if design == "uniform":
        return arrays.uniform_array(n_pads, float(np.sqrt(lo * hi)),
                                    C.EC_TARGET, **kw)
    if design == "stochastic":
        return arrays.stochastic_array(n_pads, lo, hi, C.EC_TARGET, rng, **kw)
    raise ValueError(design)


def drive(arr, signal, op, mask_seed):
    return arr.states(signal, n_virtual=C.M_VIRTUAL, theta=op["theta"],
                      bias=op["bias"], gain=op["gain"], scheme=C.SCHEME,
                      mask_spread=op["mask_spread"], readout=C.READOUT,
                      mask_seed=mask_seed, feedback=op.get("feedback", 0.0),
                      feedback_delay=C.FEEDBACK_DELAY)


def measure(x_bin, ub, x_uni, u, charge=0.0):
    """The full metric set for one state matrix pair (binary and uniform drive)."""
    acc, nlmc = benchmarks.nonlinear_memory_profile(
        x_bin, ub, C.N_WASHOUT, C.N_TRAIN, d_max=C.D_MAX_NL,
        order=C.PARITY_ORDER)
    nrmse, _, _, model = benchmarks.narma_nrmse(x_uni, u, C.NARMA_ORDER,
                                                C.N_WASHOUT, C.N_TRAIN,
                                                return_model=True)
    mc_d, mc = benchmarks.memory_capacity(x_uni, u, C.N_WASHOUT, C.N_TRAIN,
                                          d_max=C.D_MAX)
    lam = float(model[2])
    depth = max([d for d in range(C.D_MAX_NL + 1) if acc[d] > 0.75] + [-1])
    return dict(nlmc=float(nlmc), nl_depth=int(depth), nrmse=float(nrmse),
                mc=float(mc), lam=lam,
                eff_rank=benchmarks.effective_rank(x_uni, C.N_WASHOUT),
                eff_dof=benchmarks.effective_dof(x_uni, C.N_WASHOUT,
                                                 C.N_TRAIN, lam),
                pcs95=benchmarks.variance_components(x_uni, C.N_WASHOUT),
                switched_charge=float(charge),
                nl_acc=acc.tolist(), mc_d=mc_d.tolist())


def job_device(args):
    design, n_pads, mask_seed, input_seed = args
    op = OPS[design]
    u, ub = C.inputs(input_seed), C.binary_inputs(input_seed)
    rng = np.random.default_rng(mask_seed * 7919 + input_seed)
    arr_b = build(design, n_pads, op, rng)
    x_bin = drive(arr_b, ub, op, mask_seed)
    arr_u = build(design, n_pads, op, np.random.default_rng(
        mask_seed * 7919 + input_seed))
    x_uni = drive(arr_u, u, op, mask_seed)
    rec = measure(x_bin, ub, x_uni, u, arr_u.last_switched_charge)
    rec.update(design=design, n_pads=n_pads, mask_seed=mask_seed,
               input_seed=input_seed)
    return rec


def job_esn(args):
    n_pads, weight_seed, input_seed = args
    op = OPS["esn"]
    u, ub = C.inputs(input_seed), C.binary_inputs(input_seed)
    kw = dict(n_nodes=C.M_VIRTUAL * n_pads,
              spectral_radius=op["spectral_radius"], leak=op["leak"],
              input_scale=op["input_scale"], bias_scale=op["bias_scale"],
              seed=weight_seed)
    rec = measure(EchoStateNetwork(**kw).states(ub), ub,
                  EchoStateNetwork(**kw).states(u), u)
    rec.update(design="esn", n_pads=n_pads, mask_seed=weight_seed,
               input_seed=input_seed)
    return rec


def job_delay_line(args):
    n_pads, _mask_seed, input_seed = args
    taps = min(DELAY_TAPS, C.M_VIRTUAL * n_pads)
    u, ub = C.inputs(input_seed), C.binary_inputs(input_seed)
    make = lambda sig: np.column_stack([np.roll(sig, d)
                                        for d in range(taps + 1)])
    rec = measure(make(ub), ub, make(u), u)
    rec.update(design="delay_line", n_pads=n_pads, mask_seed=0,
               input_seed=input_seed)
    return rec


def main():
    global OPS
    with open(os.path.join(C.OUT_DIR, "operating_points.json"),
              encoding="utf-8") as fh:
        OPS = json.load(fh)
    os.makedirs(C.OUT_DIR, exist_ok=True)
    t0 = time.time()

    pairs = list(itertools.product(C.EVAL_MASK_SEEDS, C.EVAL_INPUT_SEEDS))
    dev_jobs = [(d, p, ms, is_) for d in DESIGNS for p in PAD_COUNTS
                for ms, is_ in pairs]
    esn_jobs = [(p, ms, is_) for p in PAD_COUNTS for ms, is_ in pairs]
    dl_jobs = [(p, 0, is_) for p in PAD_COUNTS for is_ in C.EVAL_INPUT_SEEDS]
    print(f"{len(dev_jobs)} device + {len(esn_jobs)} ESN + {len(dl_jobs)} "
          f"delay-line runs ({len(pairs)} paired realizations)")

    records = []
    with Pool(initializer=_init, initargs=(OPS,)) as pool:
        for i, rec in enumerate(pool.imap_unordered(job_device, dev_jobs,
                                                    chunksize=4)):
            records.append(rec)
            if (i + 1) % 100 == 0:
                print(f"  device {i + 1}/{len(dev_jobs)}  "
                      f"({time.time() - t0:.0f} s)")
        records += list(pool.imap_unordered(job_esn, esn_jobs, chunksize=4))
        records += list(pool.imap_unordered(job_delay_line, dl_jobs,
                                            chunksize=2))

    def sel(design, n_pads, key):
        return np.array([r[key] for r in records
                         if r["design"] == design and r["n_pads"] == n_pads])

    summary = {"pad_counts": PAD_COUNTS, "n_realizations": len(pairs),
               "operating_points": OPS, "table": {}}
    order = DESIGNS + ["esn", "delay_line"]
    print("\n" + "=" * 92)
    print(f"{'design':>12} {'P':>2} {'chan':>5} {'NL-MC':>15} {'depth':>6} "
          f"{'NARMA':>15} {'lin MC':>13} {'dof':>6}")
    print("=" * 92)
    for design in order:
        summary["table"][design] = {}
        for p in PAD_COUNTS:
            nl = sel(design, p, "nlmc")
            if nl.size == 0:
                continue
            n = sel(design, p, "nrmse")
            m = sel(design, p, "mc")
            dep = sel(design, p, "nl_depth")
            summary["table"][design][str(p)] = dict(
                nlmc_mean=float(nl.mean()), nlmc_std=float(nl.std(ddof=1)),
                nl_depth_mean=float(dep.mean()),
                nrmse_mean=float(n.mean()), nrmse_std=float(n.std(ddof=1)),
                mc_mean=float(m.mean()), mc_std=float(m.std(ddof=1)),
                eff_rank_mean=float(sel(design, p, "eff_rank").mean()),
                eff_dof_mean=float(sel(design, p, "eff_dof").mean()),
                pcs95_mean=float(sel(design, p, "pcs95").mean()),
                lam_median=float(np.median(sel(design, p, "lam"))),
                switched_charge_mean=float(
                    sel(design, p, "switched_charge").mean()),
                nl_acc_mean=np.mean([r["nl_acc"] for r in records
                                     if r["design"] == design
                                     and r["n_pads"] == p], axis=0).tolist(),
                mc_d_mean=np.mean([r["mc_d"] for r in records
                                   if r["design"] == design
                                   and r["n_pads"] == p], axis=0).tolist())
            t = summary["table"][design][str(p)]
            print(f"{design:>12} {p:2d} {p * C.M_VIRTUAL:5d} "
                  f"{nl.mean():8.3f} +- {nl.std(ddof=1):.3f} {dep.mean():6.1f} "
                  f"{n.mean():8.4f} +- {n.std(ddof=1):.4f} "
                  f"{m.mean():7.2f} +- {m.std(ddof=1):.2f} "
                  f"{t['eff_dof_mean']:6.1f}")

    print("\nPaired comparisons on nonlinear memory capacity "
          "(same mask and input):")
    summary["paired"] = {}
    key = lambda r: (r["mask_seed"], r["input_seed"])
    for p in PAD_COUNTS:
        summary["paired"][str(p)] = {}
        base = {key(r): r["nlmc"] for r in records
                if r["design"] == "graded" and r["n_pads"] == p}
        for other in ["homogeneous", "uniform", "stochastic", "esn"]:
            comp = {key(r): r["nlmc"] for r in records
                    if r["design"] == other and r["n_pads"] == p}
            common = sorted(set(base) & set(comp))
            if len(common) < 5:
                continue
            a = np.array([base[k] for k in common])
            b = np.array([comp[k] for k in common])
            diff = a - b          # positive means the spread is better
            try:
                _, pval = stats.wilcoxon(diff)
            except ValueError:
                pval = np.nan
            summary["paired"][str(p)][other] = dict(
                mean_diff=float(diff.mean()),
                std_diff=float(diff.std(ddof=1)),
                rel_pct=float(diff.mean() / max(b.mean(), 1e-9) * 100),
                wilcoxon_p=float(pval), n=len(common))
            e = summary["paired"][str(p)][other]
            print(f"  P={p}: graded vs {other:>12}: "
                  f"dNL-MC = {e['mean_diff']:+.3f} +- {e['std_diff']:.3f} "
                  f"({e['rel_pct']:+.1f}%), Wilcoxon p = {pval:.2e}")

    print("\nChannel efficiency (single-time-constant pads needed to match "
          "one spread pad):")
    summary["channel_efficiency"] = {}
    hom = [(p, summary["table"]["homogeneous"][str(p)]["nlmc_mean"])
           for p in PAD_COUNTS if str(p) in summary["table"]["homogeneous"]]
    for p in PAD_COUNTS:
        if str(p) not in summary["table"]["graded"]:
            continue
        target = summary["table"]["graded"][str(p)]["nlmc_mean"]
        matched = [q for q, v in hom if v >= target]
        need = min(matched) if matched else None
        summary["channel_efficiency"][str(p)] = need
        txt = f"{need} pads" if need else f"more than {max(PAD_COUNTS)} pads"
        print(f"  graded P={p} (NL-MC {target:.3f}) matched by "
              f"homogeneous {txt}")

    with open(os.path.join(C.OUT_DIR, "headline_records.json"), "w",
              encoding="utf-8") as fh:
        json.dump(records, fh)
    with open(os.path.join(C.OUT_DIR, "headline_summary.json"), "w",
              encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    print(f"\nWrote {C.OUT_DIR}/headline_*.json  ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
