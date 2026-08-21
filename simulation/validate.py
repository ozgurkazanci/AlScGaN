"""Validation suite: calibration anchors, model invariants, numerical checks.

Run before any production experiment. Every check that can be stated as an
assertion is one; the rest print numbers for inspection.
"""

import sys

import numpy as np

sys.path.insert(0, ".")
from alscgan_rc import benchmarks
from alscgan_rc.device import (SegmentedFilm, TAU_SW0, W_MERZ,
                               switching_energy_pj)
from alscgan_rc.materials import BOWED, DEFAULT, MaterialModel
from alscgan_rc.reservoir import (EchoStateNetwork, MultiplexedReservoir,
                                  ridge_fit, ridge_predict)

np.seterr(over="raise", divide="raise", invalid="raise", under="ignore")
rng = np.random.default_rng(0)
EC = 2.7
FAILURES = []


def check(name, condition, detail=""):
    status = "ok  " if condition else "FAIL"
    if not condition:
        FAILURES.append(name)
    print(f"  [{status}] {name}" + (f"  {detail}" if detail else ""))


print("=" * 72)
print("1. MATERIAL MODEL CALIBRATION")
print("=" * 72)
print(" ", DEFAULT.summary())
ec1 = float(DEFAULT.coercive_field(0.00, 0.27))
ec2 = float(DEFAULT.coercive_field(0.60, 0.40))
t1 = float(DEFAULT.tau_retention(0.10, 0.35))
t2 = float(DEFAULT.tau_retention(0.60, 0.35))
check("Ec anchor A1 (Al0.73Sc0.27N = 4.7 MV/cm)", abs(ec1 - 4.7) < 1e-9,
      f"got {ec1:.4f}")
check("Ec anchor A2 (Sc0.40Ga0.60N = 1.5 MV/cm)", abs(ec2 - 1.5) < 1e-9,
      f"got {ec2:.4f}")
check("tau anchor A3 (1e3 s)", abs(np.log10(t1) - 3) < 1e-9, f"got {t1:.4g}")
check("tau anchor A4 (1e-3 s)", abs(np.log10(t2) + 3) < 1e-9, f"got {t2:.4g}")
check("retention prefactor pinned at 1e-13 s", DEFAULT.tau0 == 1e-13)
print(f"  GAMMA = {DEFAULT.gamma:.4f}, PHI0 = {DEFAULT.phi0:+.4f} eV, "
      f"barrier at A3 = {float(DEFAULT.barrier(0.10, 0.35)):.4f} eV")

x_probe = np.linspace(0.15, 0.60, 7)
y_probe = DEFAULT.iso_ec_sc_fraction(x_probe, EC)
ec_probe = DEFAULT.coercive_field(x_probe, y_probe)
check("iso-Ec inversion exact", np.allclose(ec_probe, EC, atol=1e-12),
      f"spread {np.ptp(ec_probe):.2e} MV/cm")
check("iso-Ec keeps Al fraction physical",
      np.all(1 - x_probe - y_probe > 0.02),
      f"min Al = {np.min(1 - x_probe - y_probe):.4f}")
try:
    DEFAULT.iso_ec_sc_fraction(np.array([0.85]), EC)
    check("iso-Ec rejects out-of-simplex request", False)
except ValueError:
    check("iso-Ec rejects out-of-simplex request", True)

span = DEFAULT.tau_span_decades(0.15, 0.60, EC)
print(f"  tau span over x = 0.15-0.60 at Ec = {EC}: {span:.2f} decades")
x_rt = DEFAULT.x_for_tau(1.0, EC)
check("x_for_tau inverts tau_retention",
      abs(float(DEFAULT.tau_retention(x_rt, DEFAULT.iso_ec_sc_fraction(x_rt, EC))) - 1.0) < 1e-6,
      f"x(tau=1 s) = {x_rt:.4f}")
print(f"  bowed model: {BOWED.summary()}")
print(f"  bowed tau span over the same window: "
      f"{BOWED.tau_span_decades(0.15, 0.60, EC):.2f} decades")

print()
print("=" * 72)
print("2. DEVICE MODEL INVARIANTS")
print("=" * 72)
graded = SegmentedFilm.graded_iso_ec(24, 0.15, 0.60, EC)
print("  ", graded.describe())
check("all segments iso-Ec", np.ptp(graded.ec) < 1e-12)

# order invariance (a stated property of the parallel-segment model)
perm = rng.permutation(graded.n)
shuffled = SegmentedFilm(graded.x_ga[perm], graded.y_sc[perm])
fields = rng.uniform(-1.5 * EC, 1.5 * EC, 600)
a = graded.run(fields, 3e-3)
b = shuffled.run(fields, 3e-3)
check("output invariant to segment ordering", np.allclose(a, b, atol=1e-12),
      f"max |diff| = {np.max(np.abs(a - b)):.2e}")

# exactness of the slot update against a fine-grained reference
film = SegmentedFilm.graded_iso_ec(8, 0.15, 0.60, EC)
film.reset(-0.3)
film.step(1.1 * EC, 0.02)
exact = film.p.copy()
film2 = SegmentedFilm.graded_iso_ec(8, 0.15, 0.60, EC)
film2.reset(-0.3)
for _ in range(200):
    film2.step(1.1 * EC, 0.02 / 200)
check("slot update is step-size exact", np.allclose(exact, film2.p, atol=1e-12),
      f"max |diff| = {np.max(np.abs(exact - film2.p)):.2e}")

# numerical robustness at the extremes
film.reset(1.0)
film.step(1e-9, 1.0)
check("no overflow at vanishing field", np.all(np.isfinite(film.p)))
film.reset(1.0)
film.step(0.0, 1.0e6)
check("no error at huge zero-field dwell", np.all(np.isfinite(film.p)))
check("zero-field dwell relaxes to zero", np.allclose(film.p, 0.0, atol=1e-12))

# simplex enforcement in the noise path
noisy = graded.with_composition_noise(0.05, rng)
check("composition noise stays inside the simplex",
      np.all(1 - noisy.x_ga - noisy.y_sc >= 0.02 - 1e-12),
      f"min Al = {np.min(1 - noisy.x_ga - noisy.y_sc):.4f}")
try:
    SegmentedFilm(np.array([0.6]), np.array([0.5]))
    check("constructor rejects x+y>1", False)
except ValueError:
    check("constructor rejects x+y>1", True)

sym = SegmentedFilm(0.3, np.array([0.20, 0.30, 0.35]))
check("constructor broadcasts scalar x against array y", sym.n == 3)

ladder = SegmentedFilm.tau_ladder([1e-2, 1e0, 1e2], EC)
check("tau_ladder hits requested time constants",
      np.allclose(np.log10(ladder.tau_ret), [-2, 0, 2], atol=1e-4),
      f"got {np.round(np.log10(ladder.tau_ret), 4)}")

hot = graded.at_temperature(325.0)
dec_per_k = (np.log10(graded.tau_ret[0]) - np.log10(hot.tau_ret[0])) / 25.0
print(f"  temperature sensitivity: {1/dec_per_k:.1f} K per decade of tau")

print()
print("=" * 72)
print("3. READOUT AND BENCHMARK CORRECTNESS")
print("=" * 72)
n = 900
u = rng.uniform(0, 0.5, n)
y = benchmarks.narma_target(u, 10)
check("NARMA-10 stays bounded", np.all(np.abs(y) < 2), f"max {np.max(y):.3f}")
check("NARMA-10 has nonzero variance", np.var(y) > 1e-6)

# ridge intercept must be unpenalized: constant target -> exact fit
x_dummy = rng.normal(0, 1, (200, 5))
y_const = np.full(200, 7.0)
w = ridge_fit(x_dummy, y_const, lam=1e3)
check("intercept is not penalized",
      np.allclose(ridge_predict(x_dummy, w), 7.0, atol=1e-6),
      f"mean pred {np.mean(ridge_predict(x_dummy, w)):.4f}")

# constant states must not raise inside MC
const_states = np.ones((n, 4))
_, mc_const = benchmarks.memory_capacity(const_states, u, 200, 500, d_max=10)
check("MC handles degenerate constant states", mc_const < 0.05,
      f"MC = {mc_const:.4f}")
try:
    benchmarks.memory_capacity(const_states, u, 50, 500, d_max=100)
    check("MC rejects d_max > washout", False)
except ValueError:
    check("MC rejects d_max > washout", True)

esn = EchoStateNetwork(n_nodes=30)
xs = esn.states(u)
check("ESN state matrix finite and bounded", np.all(np.abs(xs) <= 1.0))
check("ESN has a bias input", np.any(esn.w_bias != 0))

print()
print("=" * 72)
print("4. PAD-ARRAY FAST PATH")
print("=" * 72)
from alscgan_rc import arrays  # noqa: E402
u_short = rng.uniform(0, 0.5, 120)
kw = dict(n_virtual=20, theta=5e-3, bias=0.55, gain=0.15, scheme="bias",
          mask_spread=0.3, readout="charge")
arr = arrays.graded_array(3, 1e-2, 1e2, EC, n_seg=8)
fast = arr.states(u_short, **kw)
slow = arr.states_reference(u_short, **kw)
check("stacked fast path matches per-pad reference",
      np.allclose(fast, slow, atol=1e-12),
      f"max |diff| = {np.max(np.abs(fast - slow)):.2e}")
check("fast path column layout matches hstack order", fast.shape == slow.shape)

hom = arrays.homogeneous_array(3, 1e-2, 1e2, EC, n_seg=8)
uni = arrays.uniform_array(3, 1.0, EC, n_seg=8)
sto = arrays.stochastic_array(3, 1e-2, 1e2, EC, rng, n_seg=8)
for a in (arr, hom, uni, sto):
    print("  ", a.describe())
check("homogeneous array has one tau per pad",
      len(np.unique(np.round(np.log10(hom.tau_pool()), 9))) == 3)
check("uniform array has a single tau",
      len(np.unique(np.round(np.log10(uni.tau_pool()), 9))) == 1)
check("all designs share one coercive field",
      max(float(np.ptp(np.concatenate([f.ec for f in a.films])))
          for a in (arr, hom, uni, sto)) < 1e-9)

# device noise must reach the fast path
quiet = arrays.graded_array(2, 1e-2, 1e2, EC, n_seg=8)
loud = arrays.graded_array(2, 1e-2, 1e2, EC, n_seg=8, read_noise=1.0,
                           ec_jitter=0.02, rng=np.random.default_rng(3))
kw2 = dict(kw, n_virtual=10)
xq, xl = quiet.states(u_short, **kw2), loud.states(u_short, **kw2)
check("read noise and Ec jitter reach the stacked path",
      not np.allclose(xq, xl, atol=1e-9),
      f"rms difference = {np.sqrt(np.mean((xq-xl)**2)):.3g}")
loud2 = arrays.graded_array(2, 1e-2, 1e2, EC, n_seg=8, read_noise=1.0,
                            ec_jitter=0.02, rng=np.random.default_rng(3))
check("noisy runs are reproducible given the same rng seed",
      np.allclose(xl, loud2.states(u_short, **kw2), atol=1e-12))

print()
print("=" * 72)
print("5. DRIVE REGIME DIAGNOSTIC")
print("=" * 72)
print(f"  {'bias':>5} {'r_sw(med)':>11} {'sw/sample':>10} "
      f"{'leak-dom frac':>14} {'eff.rank':>9} {'MC':>6}")
u_s = rng.uniform(0, 0.5, 1200)
for bias in (0.45, 0.55, 0.65, 0.75, 0.85):
    f = SegmentedFilm.graded_iso_ec(24, 0.15, 0.60, EC)
    res = MultiplexedReservoir(f, n_virtual=50, theta=5e-3, bias=bias,
                               gain=0.15, readout="charge")
    rep = res.regime_report()
    st = res.states(u_s)
    er = benchmarks.effective_rank(st, 200)
    _, mc = benchmarks.memory_capacity(st, u_s, 200, 700, d_max=30)
    print(f"  {bias:5.2f} {rep['r_sw_median']:11.3g} "
          f"{rep['switch_per_sample']:10.3g} "
          f"{rep['leakage_dominated_fraction']:14.2f} {er:9.2f} {mc:6.2f}")

f = SegmentedFilm.graded_iso_ec(24, 0.15, 0.60, EC)
res = MultiplexedReservoir(f, n_virtual=50, theta=5e-3, bias=0.55, gain=0.15)
res.states(u_s[:200])
e_pj = switching_energy_pj(f, area_um2=100.0, thickness_nm=100.0,
                           e_amplitude_mv_cm=0.55 * EC)
print(f"\n  switching energy, 100x100 um pad, 100 nm, 200 samples: "
      f"{e_pj:.3g} pJ ({e_pj/200:.3g} pJ per input sample)")

print()
print("=" * 72)
if FAILURES:
    print(f"FAILED CHECKS: {len(FAILURES)}")
    for f_ in FAILURES:
        print("  -", f_)
    sys.exit(1)
print("ALL CHECKS PASSED")
