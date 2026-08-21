"""Stage 3: device-level electrical signatures and the drive regime.

Figure 2 data - what an experimentalist would measure first:
  * P-E loops at several amplitudes, with a robust coercive-field extraction
  * retention transients: a graded pad relaxes as a sum of exponentials over
    the designed span, a homogeneous pad as a single exponential
  * the drive-regime diagram: which of switching or leakage performs the
    forgetting, and where memory capacity peaks as a result

The regime diagram is the mechanism check the manuscript must pass. If the
best operating point sat where switching dominates, the engineered time
constants would be dynamically invisible and the whole premise would fail.

Output: results/device_char.npz
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import threadcap  # noqa: F401  (must precede numpy)

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C
from alscgan_rc import arrays, benchmarks
from alscgan_rc.device import SegmentedFilm
from alscgan_rc.reservoir import MultiplexedReservoir

np.seterr(over="raise", divide="raise", invalid="raise", under="ignore")

with open(os.path.join(C.OUT_DIR, "operating_points.json"), encoding="utf-8") as _fh:
    OP = json.load(_fh)["graded"]
TAU_LO, TAU_HI = OP["tau_lo"], OP["tau_hi"]
THETA, GAIN, SPREAD = OP["theta"], OP["gain"], OP["mask_spread"]
FEEDBACK = OP.get("feedback", C.FEEDBACK)


def pe_loop(film, e_amp, freq=100.0, n_slots=4000, n_cycles=3):
    """Triangular-wave P-E loop; returns the last cycle and extracted Ec, Pr."""
    period = 1.0 / freq
    dt = period / n_slots
    t = np.arange(n_slots * n_cycles) * dt
    e = e_amp * 2 / np.pi * np.arcsin(np.sin(2 * np.pi * freq * t))
    film.reset(-1.0)
    p = film.run(e, dt)
    e_l, p_l = e[-n_slots:], p[-n_slots:]
    rising = np.diff(e_l, prepend=e_l[0]) > 0

    ec_pos = _zero_crossing(e_l, p_l, rising & (e_l > -e_amp))
    ec_neg = _zero_crossing(e_l, p_l, (~rising) & (e_l < e_amp), descending=True)
    idx = np.where(rising)[0]
    pr = float(p_l[idx[np.argmin(np.abs(e_l[idx]))]]) if idx.size else np.nan
    return e_l, p_l, ec_pos, ec_neg, pr


def _zero_crossing(e_l, p_l, branch, descending=False):
    """Field at which P crosses zero on the given branch; NaN if it never does."""
    idx = np.where(branch)[0]
    if idx.size < 2:
        return np.nan
    p_b, e_b = p_l[idx], e_l[idx]
    s = np.sign(p_b)
    cross = np.where(np.diff(s) != 0)[0]
    if cross.size == 0:
        return np.nan
    want = cross[-1] if descending else cross[0]
    p0, p1 = p_b[want], p_b[want + 1]
    e0, e1 = e_b[want], e_b[want + 1]
    if p1 == p0:
        return float(e0)
    return float(e0 - p0 * (e1 - e0) / (p1 - p0))


def retention(film, ec_target, times):
    """Pole positively, then hold at zero field and sample P(t)."""
    film.reset(0.0)
    for _ in range(50):
        film.step(1.4 * ec_target, 5e-3)
    p0 = film.polarization()
    out, t_prev = [], 0.0
    for t in times:
        film.step(0.0, t - t_prev)
        t_prev = t
        out.append(film.polarization())
    return p0, np.array(out)


def main():
    os.makedirs(C.OUT_DIR, exist_ok=True)
    rng = np.random.default_rng(7)
    out, summary = {}, {}

    graded = SegmentedFilm.graded_iso_ec(
        C.N_SEG, DEF_LO := _x(TAU_HI), DEF_HI := _x(TAU_LO), C.EC_TARGET)
    uniform = SegmentedFilm.uniform(
        C.N_SEG, _x(np.sqrt(TAU_LO * TAU_HI)), C.EC_TARGET)
    print("graded :", graded.describe())
    print("uniform:", uniform.describe())

    # --- P-E loops ---------------------------------------------------------
    print("\nP-E loops (100 Hz triangular):")
    amps = [0.6, 1.0, 1.4, 1.7, 2.0]
    summary["pe"] = {}
    for name, film in (("graded", graded), ("uniform", uniform)):
        summary["pe"][name] = []
        for a in amps:
            e_l, p_l, ecp, ecn, pr = pe_loop(film, a * C.EC_TARGET)
            out[f"pe_{name}_{a}_e"] = e_l
            out[f"pe_{name}_{a}_p"] = p_l
            summary["pe"][name].append(dict(
                amplitude_rel=a, ec_pos=ecp, ec_neg=ecn, pr=pr,
                p_max=float(p_l.max()), p_min=float(p_l.min())))
            ecs = "n/a" if not np.isfinite(ecp) else f"{ecp:5.2f}"
            print(f"  {name:>8} at {a:4.1f} Ec: Ec+ = {ecs} MV/cm, "
                  f"Pr = {pr:7.1f}, P range {p_l.min():7.1f}..{p_l.max():6.1f}")
    out["pe_amps"] = np.array(amps)

    # --- retention ---------------------------------------------------------
    times = np.logspace(-4, 4, 60)
    out["ret_t"] = times
    print("\nRetention after positive poling (normalized P):")
    summary["retention"] = {}
    for name, film in (("graded", graded), ("uniform", uniform)):
        p0, pt = retention(film, C.EC_TARGET, times)
        out[f"ret_{name}"] = pt / p0
        # decay is single-exponential iff the local log-slope is constant
        norm = pt / p0
        ok = norm > 1e-3
        slope = np.gradient(np.log(np.clip(norm[ok], 1e-12, None)),
                            np.log(times[ok]))
        summary["retention"][name] = dict(
            p0=float(p0),
            t_half=float(np.interp(-0.5, -norm, times)),
            logslope_spread=float(np.ptp(slope)))
        print(f"  {name:>8}: P0 = {p0:6.1f} uC/cm2, t(1/2) = "
              f"{summary['retention'][name]['t_half']:.3g} s, "
              f"log-slope spread = {summary['retention'][name]['logslope_spread']:.2f}")

    # --- drive regime ------------------------------------------------------
    # Two things have to be shown here: that the selected drive sits where
    # leakage rather than field overwrite performs the forgetting, and that
    # the feedback loop gain sits inside its stable window.
    print("\nDrive-regime scan (4-pad graded array):")
    # evaluation seed, disjoint from the seeds the operating points were
    # selected on: these sweeps are reported in the paper, so they must not be
    # in-sample
    # evaluation seeds, disjoint from the seeds the operating points were
    # selected on. Three of them, averaged: on one realization the loop-gain
    # sweep is noisy enough to make the usable window non-contiguous.
    SEEDS = C.EVAL_INPUT_SEEDS[:3]
    SIGNALS = [(C.inputs(sd), C.binary_inputs(sd)) for sd in SEEDS]
    u, ub = SIGNALS[0]
    biases = np.arange(0.35, 0.92, 0.05)
    kw = dict(n_virtual=C.M_VIRTUAL, theta=THETA, gain=GAIN,
              scheme=C.SCHEME, mask_spread=SPREAD, readout=C.READOUT,
              feedback=FEEDBACK, feedback_delay=C.FEEDBACK_DELAY)
    rows = []
    for bias in biases:
        arr = arrays.graded_array(4, TAU_LO, TAU_HI, C.EC_TARGET, n_seg=C.N_SEG)
        # the regime diagnostic must see the WHOLE array: pad 0 alone covers
        # only one sub-window of the spectrum and would always look
        # leakage-dominated
        res = MultiplexedReservoir(pooled(arr), bias=bias, **kw)
        rep = res.regime_report()
        nl_v, mc_v, nr_v, er_v = [], [], [], []
        for uu, uub in SIGNALS:
            _, v = benchmarks.nonlinear_memory_profile(
                arr.states(uub, bias=bias, **kw), uub, C.N_WASHOUT,
                C.N_TRAIN, d_max=C.D_MAX_NL, order=C.PARITY_ORDER)
            nl_v.append(v)
            x = arr.states(uu, bias=bias, **kw)
            e, _, _ = benchmarks.narma_nrmse(x, uu, C.NARMA_ORDER,
                                             C.N_WASHOUT, C.N_TRAIN)
            _, m = benchmarks.memory_capacity(x, uu, C.N_WASHOUT, C.N_TRAIN,
                                              d_max=C.D_MAX)
            nr_v.append(e)
            mc_v.append(m)
            er_v.append(benchmarks.effective_rank(x, C.N_WASHOUT))
        nlmc = float(np.mean(nl_v))
        mc = float(np.mean(mc_v))
        nrmse = float(np.mean(nr_v))
        er = float(np.mean(er_v))
        rows.append([bias, rep["r_sw_median"], rep["switch_per_sample"],
                     rep["leakage_dominated_fraction"], nlmc, mc, nrmse, er])
        print(f"  bias {bias:.2f}: r_sw {rep['r_sw_median']:9.3g} 1/s, "
              f"switch/sample {rep['switch_per_sample']:8.3g}, "
              f"leak-dominated {rep['leakage_dominated_fraction']:.2f}, "
              f"NL-MC {nlmc:5.2f}, linMC {mc:5.2f}, NARMA {nrmse:.3f}, "
              f"rank {er:5.2f}")
    out["regime"] = np.array(rows)
    out["regime_cols"] = np.array(["bias", "r_sw", "switch_per_sample",
                                   "leak_fraction", "nlmc", "mc", "nrmse",
                                   "eff_rank"])
    best = out["regime"][np.argmax(out["regime"][:, 4])]
    summary["window"] = dict(tau_lo=TAU_LO, tau_hi=TAU_HI, theta=THETA,
                             gain=GAIN, spread=SPREAD, feedback=FEEDBACK)
    summary["regime_best"] = dict(bias=float(best[0]), nlmc=float(best[4]),
                                  mc=float(best[5]), nrmse=float(best[6]),
                                  leak_fraction=float(best[3]))
    print(f"  best nonlinear memory at bias = {best[0]:.2f}, where "
          f"{best[3] * 100:.0f}% of segments are leakage-dominated")

    # --- feedback loop: the stability window ---------------------------------
    print("\nFeedback loop-gain scan (the loop is what makes it recurrent):")
    fb_grid = [0.0, 0.001, 0.003, 0.006, 0.01, 0.02, 0.03, 0.05, 0.1, 0.3]
    fb_rows = []
    bias_opt = float(OP["bias"])
    for fb in fb_grid:
        kwf = dict(kw, bias=bias_opt, feedback=fb)
        nl_v, mc_v, nr_v = [], [], []
        diverged = False
        for uu, uub in SIGNALS:
            arr = arrays.graded_array(4, TAU_LO, TAU_HI, C.EC_TARGET,
                                      n_seg=C.N_SEG)
            xb = arr.states(uub, **kwf)
            if not np.all(np.isfinite(xb)):
                diverged = True
                break
            _, v = benchmarks.nonlinear_memory_profile(
                xb, uub, C.N_WASHOUT, C.N_TRAIN, d_max=C.D_MAX_NL,
                order=C.PARITY_ORDER)
            nl_v.append(v)
            x = arrays.graded_array(4, TAU_LO, TAU_HI, C.EC_TARGET,
                                    n_seg=C.N_SEG).states(uu, **kwf)
            _, m = benchmarks.memory_capacity(x, uu, C.N_WASHOUT, C.N_TRAIN,
                                              d_max=C.D_MAX)
            e, _, _ = benchmarks.narma_nrmse(x, uu, C.NARMA_ORDER,
                                             C.N_WASHOUT, C.N_TRAIN)
            mc_v.append(m)
            nr_v.append(e)
        if diverged:
            fb_rows.append([fb, np.nan, np.nan, np.nan])
            print(f"  fb {fb:6.3f}: diverged")
            continue
        nlmc = float(np.mean(nl_v))
        mc = float(np.mean(mc_v))
        nrmse = float(np.mean(nr_v))
        fb_rows.append([fb, nlmc, mc, nrmse])
        print(f"  fb {fb:6.3f}: NL-MC {nlmc:5.2f}, linMC {mc:5.2f}, "
              f"NARMA {nrmse:.3f}")
    out["feedback"] = np.array(fb_rows)
    out["feedback_cols"] = np.array(["feedback", "nlmc", "mc", "nrmse"])
    fin = out["feedback"][np.isfinite(out["feedback"][:, 1])]
    open_loop = float(fin[fin[:, 0] == 0.0][0, 1]) if np.any(fin[:, 0] == 0) \
        else float("nan")
    best_fb = fin[np.argmax(fin[:, 1])]
    stable = fin[fin[:, 1] > 0.5 * best_fb[1], 0]
    summary["feedback"] = dict(
        open_loop_nlmc=open_loop, best_gain=float(best_fb[0]),
        best_nlmc=float(best_fb[1]),
        stable_window=[float(stable.min()), float(stable.max())]
        if stable.size else None)
    print(f"  open loop NL-MC = {open_loop:.2f}; best {best_fb[1]:.2f} at "
          f"gain {best_fb[0]:g}; usable window "
          f"{summary['feedback']['stable_window']}")

    # --- the designed spectra themselves -------------------------------------
    for label, arr in (
            ("graded", arrays.graded_array(4, TAU_LO, TAU_HI, C.EC_TARGET,
                                           n_seg=C.N_SEG)),
            ("homogeneous", arrays.homogeneous_array(4, TAU_LO, TAU_HI,
                                                     C.EC_TARGET,
                                                     n_seg=C.N_SEG)),
            ("uniform", arrays.uniform_array(4, float(np.sqrt(TAU_LO * TAU_HI)),
                                             C.EC_TARGET, n_seg=C.N_SEG))):
        out[f"tau_{label}"] = arr.tau_pool()

    # --- memory-capacity profile: the mechanism signature -------------------
    print("\nMemory-capacity profile at the selected operating point:")
    bias_opt = float(OP["bias"])
    summary["mc_profile"] = {}
    for label, arr in (("graded", arrays.graded_array(4, TAU_LO, TAU_HI,
                                                      C.EC_TARGET, n_seg=C.N_SEG)),
                       ("homogeneous", arrays.homogeneous_array(
                           4, TAU_LO, TAU_HI, C.EC_TARGET, n_seg=C.N_SEG)),
                       ("uniform", arrays.uniform_array(
                           4, float(np.sqrt(TAU_LO * TAU_HI)), C.EC_TARGET,
                           n_seg=C.N_SEG))):
        drive_kw = dict(n_virtual=C.M_VIRTUAL, theta=THETA, bias=bias_opt,
                        gain=GAIN, scheme=C.SCHEME, mask_spread=SPREAD,
                        readout=C.READOUT, feedback=FEEDBACK,
                        feedback_delay=C.FEEDBACK_DELAY)
        prof = []
        for uu, _ in SIGNALS:
            xs = arr.states(uu, **drive_kw)
            d_i, _ = benchmarks.memory_capacity(xs, uu, C.N_WASHOUT,
                                                C.N_TRAIN, d_max=C.D_MAX)
            prof.append(d_i)
        mc_d = np.mean(prof, axis=0)
        mc = float(np.sum(mc_d))
        x = arr.states(u, **drive_kw)
        floor, floor_sd, thresh = benchmarks.memory_capacity_noise_floor(
            x, C.N_WASHOUT, C.N_TRAIN, C.D_MAX, rng, n_surrogate=5)
        out[f"mcd_{label}"] = mc_d
        out[f"mcthresh_{label}"] = np.array([thresh])
        summary["mc_profile"][label] = dict(
            mc=mc, noise_floor=floor, noise_floor_sd=floor_sd,
            per_delay_threshold=thresh, mc_above_floor=mc - floor,
            last_significant_delay=int(
                benchmarks.significant_depth(mc_d, thresh)))
        print(f"  {label:>12}: MC = {mc:5.2f} (surrogate total floor "
              f"{floor:.2f}+-{floor_sd:.2f}, per-delay threshold "
              f"{thresh:.4f}), memory significant to delay "
              f"{summary['mc_profile'][label]['last_significant_delay']}")

    np.savez_compressed(os.path.join(C.OUT_DIR, "device_char.npz"), **out)
    with open(os.path.join(C.OUT_DIR, "device_summary.json"), "w",
              encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    print(f"\nWrote {C.OUT_DIR}/device_char.npz and device_summary.json")


def pooled(arr):
    """One SegmentedFilm carrying every segment of every pad in the array.

    Used only for regime diagnostics, where the quantity of interest is the
    span of relaxation rates across the whole array rather than within one pad.
    """
    x = np.concatenate([f.x_ga for f in arr.films])
    y = np.concatenate([f.y_sc for f in arr.films])
    w = np.concatenate([f.w for f in arr.films]) / len(arr.films)
    return SegmentedFilm(x, y, w, model=arr.films[0].model,
                         temperature_k=arr.films[0].temperature_k)


def _x(tau):
    from alscgan_rc.materials import DEFAULT
    return DEFAULT.x_for_tau(tau, C.EC_TARGET)


if __name__ == "__main__":
    main()
