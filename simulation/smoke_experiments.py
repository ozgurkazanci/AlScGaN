"""Single-job smoke test of every production experiment.

Runs one job from each stage against the operating-point file currently on
disk, so that key errors, shape bugs and bad assumptions surface in seconds
instead of after a multi-hour sweep. It checks that every code path executes
and, where a result has a known sign, that the sign is right.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import threadcap  # noqa: F401

import json
import traceback

import numpy as np

import config as C
from alscgan_rc import benchmarks

FAILED = []


def run(name, fn):
    try:
        print(f"  [ok  ] {name}: {fn()}")
    except Exception as exc:  # noqa: BLE001 - a smoke test reports everything
        FAILED.append(name)
        print(f"  [FAIL] {name}: {type(exc).__name__}: {exc}")
        traceback.print_exc(limit=4)


with open(os.path.join(C.OUT_DIR, "operating_points.json"),
          encoding="utf-8") as fh:
    OPS = json.load(fh)
stub = OPS.get("_meta", {}).get("stub")
print(f"operating points: {'STUB' if stub else 'real'}")
print(f"  graded: {OPS['graded']}")

print("\nmetric sanity: a delay line must be at chance on delayed parity")


def _delay_line_parity():
    ub = C.binary_inputs(C.EVAL_INPUT_SEEDS[0])
    x = np.column_stack([np.roll(ub, d) for d in range(31)])
    acc, cap = benchmarks.nonlinear_memory_profile(x, ub, C.N_WASHOUT,
                                                   C.N_TRAIN, d_max=6)
    assert cap < 0.2, f"delay line scored {cap:.3f}, expected ~0"
    return f"capacity {cap:.3f} (chance), accuracies {np.round(acc, 2)}"


def _oracle_parity():
    ub = C.binary_inputs(C.EVAL_INPUT_SEEDS[0])
    s = 2 * ub - 1
    x = np.column_stack([np.roll(s, d) * np.roll(s, d + 1) for d in range(7)])
    _, cap = benchmarks.nonlinear_memory_profile(x, ub, C.N_WASHOUT,
                                                 C.N_TRAIN, d_max=6)
    assert cap > 6.5, f"oracle scored {cap:.3f}, expected ~7"
    return f"capacity {cap:.3f} (near perfect)"


run("delay line at chance", _delay_line_parity)
run("oracle solves it", _oracle_parity)

print("\nexp3 - device characterization")
import exp3_device as e3


def _e3_pe():
    film = e3.SegmentedFilm.graded_iso_ec(8, 0.20, 0.45, C.EC_TARGET)
    _, _, ecp, ecn, pr = e3.pe_loop(film, 1.6 * C.EC_TARGET, n_slots=400,
                                    n_cycles=2)
    return f"Ec+={ecp:.3f} Ec-={ecn:.3f} Pr={pr:.1f}"


def _e3_pe_sub():
    film = e3.SegmentedFilm.graded_iso_ec(8, 0.20, 0.45, C.EC_TARGET)
    _, _, ecp, _, _ = e3.pe_loop(film, 0.5 * C.EC_TARGET, n_slots=400,
                                 n_cycles=2)
    return f"sub-coercive returns {ecp} without raising"


def _e3_ret():
    film = e3.SegmentedFilm.graded_iso_ec(8, 0.20, 0.45, C.EC_TARGET)
    p0, pt = e3.retention(film, C.EC_TARGET, np.logspace(-3, 2, 8))
    return f"P0={p0:.1f} -> {pt[-1]:.2f}"


run("pe_loop", _e3_pe)
run("pe_loop sub-coercive", _e3_pe_sub)
run("retention", _e3_ret)

print("\nexp4 - headline benchmark")
import exp4_headline as e4

e4.OPS = OPS
KEYS = ("nlmc", "nl_depth", "nrmse", "mc", "eff_dof")
run("job_device graded P=2",
    lambda: {k: (round(v, 3) if isinstance(v, float) else v)
             for k, v in e4.job_device(("graded", 2, C.EVAL_MASK_SEEDS[0],
                                        C.EVAL_INPUT_SEEDS[0])).items()
             if k in KEYS})
run("job_device homogeneous P=2",
    lambda: {k: (round(v, 3) if isinstance(v, float) else v)
             for k, v in e4.job_device(("homogeneous", 2, C.EVAL_MASK_SEEDS[0],
                                        C.EVAL_INPUT_SEEDS[0])).items()
             if k in KEYS})
run("job_esn P=2",
    lambda: {k: (round(v, 3) if isinstance(v, float) else v)
             for k, v in e4.job_esn((2, 11, C.EVAL_INPUT_SEEDS[0])).items()
             if k in KEYS})
run("job_delay_line P=2",
    lambda: {k: (round(v, 3) if isinstance(v, float) else v)
             for k, v in e4.job_delay_line((2, 0, C.EVAL_INPUT_SEEDS[0])).items()
             if k in KEYS})

print("\nexp5 - reproducibility")
import exp5_reproducibility as e5

e5.OPS = OPS
run("signal_rms", lambda: round(e5.signal_rms(OPS["graded"]), 4))


def _e5_group():
    seed = C.EVAL_INPUT_SEEDS[0]
    states = [e5.job_states(("graded", 0.01, 0.0, np.inf, i, seed))["states"]
              for i in range(3)]
    y = benchmarks.narma_target(C.inputs(seed), C.NARMA_ORDER)
    out = []
    for lam in (1e-6, 1e0, 1e3):
        own, cal, strict = e5.group_metrics(states, y, lam)
        out.append(f"lam={lam:g}: own={own:.3f} transfer={cal:.3f}")
    return " | ".join(out) + f" | corr={e5.state_correlation(states):.4f}"


run("group_metrics across lambda", _e5_group)
run("read noise and Ec jitter",
    lambda: round(e5.job_states(("graded", 0.01, 0.03, 30.0, 0,
                                 C.EVAL_INPUT_SEEDS[0]))["nrmse"], 4))
run("stochastic arm",
    lambda: round(e5.job_states(("stochastic", 0.02, 0.0, np.inf, 0,
                                 C.EVAL_INPUT_SEEDS[0]))["nrmse"], 4))

print("\nexp6 - robustness")
import exp6_robustness as e6

e6.OPS = OPS
fmt = lambda r: {k: round(v, 3) for k, v in r.items()
                 if k in ("nlmc", "mc", "nrmse")}
run("job_temperature 325 K",
    lambda: fmt(e6.job_temperature(("graded", 325.0, C.EVAL_INPUT_SEEDS[0],
                                    C.EVAL_MASK_SEEDS[0]))))
run("job_bowing bowed",
    lambda: fmt(e6.job_bowing(("graded", "bowed", C.EVAL_INPUT_SEEDS[0],
                               C.EVAL_MASK_SEEDS[0]))))
run("job_span 2 decades",
    lambda: fmt(e6.job_span((2.0, C.EVAL_INPUT_SEEDS[0],
                             C.EVAL_MASK_SEEDS[0]))))
run("job_span 0 decades",
    lambda: fmt(e6.job_span((0.0, C.EVAL_INPUT_SEEDS[0],
                             C.EVAL_MASK_SEEDS[0]))))
for n in (1, 2, 4, 16):
    run(f"job_ladder {n} levels",
        lambda n=n: e6.job_ladder((n, C.EVAL_INPUT_SEEDS[0],
                                   C.EVAL_MASK_SEEDS[0]))["distinct"])
run("job_converge n_seg=4, M=100",
    lambda: fmt(e6.job_converge((4, 100, C.EVAL_INPUT_SEEDS[0],
                                 C.EVAL_MASK_SEEDS[0]))))

print()
if FAILED:
    print(f"SMOKE TEST FAILURES: {len(FAILED)}")
    for f in FAILED:
        print("  -", f)
    sys.exit(1)
print("ALL EXPERIMENT CODE PATHS EXECUTE")
