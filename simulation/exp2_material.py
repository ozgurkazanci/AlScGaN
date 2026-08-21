"""Stage 2: the composition-property maps and the decoupling claim.

Produces the data behind Figure 1: coercive field and retention time constant
over the (Ga, Sc) plane, the iso-Ec trajectories, and the time constant along
one such trajectory - the quantitative statement of the decoupling that the
quaternary makes possible and the ternaries do not.

Two ternary controls are included because they are the actual falsification
test: along Al(1-y)Sc(y)N and Sc(y)Ga(1-y)N there is only one composition
axis, so any change of tau necessarily drags Ec with it.

Output: results/material_maps.npz
"""

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C
from alscgan_rc.materials import BOWED, DEFAULT

np.seterr(over="raise", divide="raise", invalid="raise", under="ignore")


def plane(model, n=241):
    x = np.linspace(0.0, 0.75, n)
    y = np.linspace(0.10, 0.45, n)
    xx, yy = np.meshgrid(x, y)
    al = 1.0 - xx - yy
    mask = al >= 0.02
    ec = np.where(mask, model.coercive_field(xx, yy), np.nan)
    tau = np.where(mask, model.tau_retention(xx, yy), np.nan)
    eg = np.where(mask, model.bandgap(xx, yy), np.nan)
    return x, y, ec, tau, eg, mask


def iso_trajectory(model, ec_target, n=200):
    lo, hi = model.x_window(ec_target)
    x = np.linspace(lo, hi, n)
    y = model.iso_ec_sc_fraction(x, ec_target)
    return x, y, model.tau_retention(x, y), model.coercive_field(x, y)


def ternary_scan(model, kind, n=400, ec_bounds=(1.0, 6.0)):
    """Ec and tau along a single-axis ternary alloy.

    Restricted to the Sc range over which the calibrated Ec map stays inside
    ec_bounds, so the comparison is not driven by linear extrapolation into
    compositions no one would grow.
    """
    y = np.linspace(0.12, 0.45, n)
    if kind == "AlScN":
        x = np.zeros_like(y)
    elif kind == "ScGaN":
        x = 1.0 - y - 0.02          # Al pinned at the 2% floor
    else:
        raise ValueError(kind)
    ec = model.coercive_field(x, y)
    keep = (ec >= ec_bounds[0]) & (ec <= ec_bounds[1])
    x, y, ec = x[keep], y[keep], ec[keep]
    return x, y, ec, model.tau_retention(x, y)


def decades_within_tolerance(ec, tau, ec_center, rel_tol):
    """Decades of tau reachable while |Ec - ec_center| <= rel_tol * ec_center.

    This is the sharp form of the decoupling claim: a device array can only
    share one drive line if every element switches at the same field, so the
    usable design freedom is the tau range available inside an Ec tolerance
    band, not the tau range available in principle.
    """
    band = np.abs(ec - ec_center) <= rel_tol * ec_center
    if np.count_nonzero(band) < 2:
        return 0.0
    t = tau[band]
    return float(np.log10(t.max() / t.min()))


def main():
    os.makedirs(C.OUT_DIR, exist_ok=True)
    out = {}

    x, y, ec, tau, eg, mask = plane(DEFAULT)
    out.update(plane_x=x, plane_y=y, plane_ec=ec, plane_tau=tau, plane_eg=eg)

    ec_targets = [2.0, 2.4, 2.7, 3.0, 3.4]
    for t in ec_targets:
        xi, yi, ti, eci = iso_trajectory(DEFAULT, t)
        out[f"iso{t}_x"] = xi
        out[f"iso{t}_y"] = yi
        out[f"iso{t}_tau"] = ti
        out[f"iso{t}_ec"] = eci
    out["ec_targets"] = np.array(ec_targets)

    summary = {"ec_target_windows": {}}
    print("Iso-Ec trajectories (quaternary, both axes free):")
    for t in ec_targets:
        xi, yi, ti, eci = iso_trajectory(DEFAULT, t)
        dec = float(np.log10(ti.max() / ti.min()))
        summary["ec_target_windows"][str(t)] = dict(
            x_lo=float(xi.min()), x_hi=float(xi.max()),
            y_lo=float(yi.min()), y_hi=float(yi.max()),
            tau_lo=float(ti.min()), tau_hi=float(ti.max()),
            decades=dec, ec_spread=float(np.ptp(eci)))
        print(f"  Ec = {t:.1f} MV/cm: x {xi.min():.3f}-{xi.max():.3f}, "
              f"y {yi.min():.3f}-{yi.max():.3f}, "
              f"tau {ti.min():.3g}-{ti.max():.3g} s ({dec:.2f} decades), "
              f"Ec spread {np.ptp(eci):.2e} MV/cm")

    print("\nTernary controls (one composition axis only):")
    summary["ternary"] = {}
    tolerances = [0.01, 0.02, 0.05, 0.10]
    for kind in ("AlScN", "ScGaN"):
        tx, ty, tec, ttau = ternary_scan(DEFAULT, kind)
        out[f"tern_{kind}_y"] = ty
        out[f"tern_{kind}_ec"] = tec
        out[f"tern_{kind}_tau"] = ttau
        dec = np.log10(ttau)
        slope = float(np.abs(np.polyfit(dec, tec, 1)[0]))
        tol_dec = {f"{t:.0%}": decades_within_tolerance(tec, ttau,
                                                        C.EC_TARGET, t)
                   for t in tolerances}
        summary["ternary"][kind] = dict(
            ec_lo=float(tec.min()), ec_hi=float(tec.max()),
            tau_lo=float(ttau.min()), tau_hi=float(ttau.max()),
            decades=float(np.ptp(dec)),
            ec_cost_per_decade=slope,
            decades_within_tolerance=tol_dec)
        print(f"  {kind}: over Ec = {tec.min():.2f}-{tec.max():.2f} MV/cm, "
              f"tau spans {np.ptp(dec):.2f} decades "
              f"({slope:.2f} MV/cm of Ec per decade of tau)")
        print(f"    decades of tau within an Ec tolerance band: "
              + ", ".join(f"{k} -> {v:.3f}" for k, v in tol_dec.items()))

    # the quaternary reaches its full span at exactly zero Ec tolerance
    xq, yq, tq, ecq = iso_trajectory(DEFAULT, C.EC_TARGET)
    summary["quaternary_decades_at_zero_tolerance"] = float(
        np.log10(tq.max() / tq.min()))
    print(f"  quaternary (iso-Ec): "
          f"{summary['quaternary_decades_at_zero_tolerance']:.2f} decades at "
          f"0% Ec tolerance (Ec spread {np.ptp(ecq):.1e} MV/cm)")

    # designed windows actually used by the experiments
    lo, hi = DEFAULT.x_window(C.EC_TARGET)
    summary["ec_target_used"] = C.EC_TARGET
    summary["x_window_used"] = [lo, hi]
    summary["max_decades_at_ec_target"] = DEFAULT.tau_span_decades(
        lo, hi, C.EC_TARGET)
    print(f"\nAt the working point Ec = {C.EC_TARGET} MV/cm the reachable "
          f"Ga window is {lo:.3f}-{hi:.3f}, giving "
          f"{summary['max_decades_at_ec_target']:.2f} decades of tau.")

    # bowing sensitivity: does the design rule survive a different bandgap map?
    xb, yb, tb, ecb = iso_trajectory(BOWED, C.EC_TARGET)
    out["bowed_x"], out["bowed_tau"] = xb, tb
    summary["bowed"] = dict(
        decades=float(np.log10(tb.max() / tb.min())),
        monotone=bool(np.all(np.diff(tb) < 0)),
        gamma=float(BOWED.gamma), phi0=float(BOWED.phi0))
    print(f"With pairwise bandgap bowing: {summary['bowed']['decades']:.2f} "
          f"decades, monotone in x = {summary['bowed']['monotone']}")

    summary["model_default"] = DEFAULT.summary()
    summary["model_bowed"] = BOWED.summary()
    summary["temperature_sensitivity_k_per_decade"] = float(
        1.0 / ((np.log10(float(DEFAULT.tau_retention(0.35, 0.35, 300.0)))
                - np.log10(float(DEFAULT.tau_retention(0.35, 0.35, 325.0)))) / 25.0))

    np.savez_compressed(os.path.join(C.OUT_DIR, "material_maps.npz"), **out)
    with open(os.path.join(C.OUT_DIR, "material_summary.json"), "w",
              encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    print(f"\nWrote {C.OUT_DIR}/material_maps.npz and material_summary.json")


if __name__ == "__main__":
    main()
