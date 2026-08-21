"""Design study of the drive scheme: which masking makes the pad a reservoir.

Compares the three mask schemes over bias, gain, mask spread and slot duration,
reporting NARMA-10 NRMSE, memory capacity and the effective rank of the state
matrix. This is a design-space exploration, not a reported result; the chosen
scheme is then fixed for all experiments.
"""

import sys
import time

import numpy as np

sys.path.insert(0, ".")
from alscgan_rc import benchmarks
from alscgan_rc.device import SegmentedFilm
from alscgan_rc.reservoir import EchoStateNetwork, MultiplexedReservoir

np.seterr(over="raise", divide="raise", invalid="raise", under="ignore")
rng = np.random.default_rng(11)

EC = 2.7
X_LO, X_HI, NSEG = 0.15, 0.60, 24
N_TOT, N_WASH, N_TRAIN = 1400, 200, 800
M = 50
u = rng.uniform(0, 0.5, N_TOT)


def evaluate(res):
    x = res.states(u)
    nrmse, _, _ = benchmarks.narma_nrmse(x, u, 10, N_WASH, N_TRAIN)
    _, mc = benchmarks.memory_capacity(x, u, N_WASH, N_TRAIN, d_max=30)
    er = benchmarks.effective_rank(x, N_WASH)
    return nrmse, mc, er


t0 = time.time()
print(f"{'scheme':>9} {'bias':>5} {'gain':>5} {'spread':>6} {'theta':>7} "
      f"| {'NRMSE':>6} {'MC':>6} {'rank':>6}")
best = {}
for scheme in ("polarity", "input", "bias"):
    spreads = (0.0,) if scheme != "bias" else (0.15, 0.30, 0.45)
    for bias in (0.45, 0.55, 0.65):
        for gain in (0.10, 0.20):
            for spread in spreads:
                for theta in (2e-3, 5e-3, 1e-2):
                    film = SegmentedFilm.graded_iso_ec(NSEG, X_LO, X_HI, EC)
                    res = MultiplexedReservoir(
                        film, n_virtual=M, theta=theta, bias=bias, gain=gain,
                        scheme=scheme, mask_spread=spread)
                    nrmse, mc, er = evaluate(res)
                    key = scheme
                    if key not in best or nrmse < best[key][0]:
                        best[key] = (nrmse, mc, er, bias, gain, spread, theta)
                    if nrmse < 0.75 or er > 3:
                        print(f"{scheme:>9} {bias:5.2f} {gain:5.2f} "
                              f"{spread:6.2f} {theta:7.0e} | {nrmse:6.3f} "
                              f"{mc:6.2f} {er:6.2f}")

print("\nBest per scheme:")
for k, v in best.items():
    print(f"  {k:>9}: NRMSE={v[0]:.3f} MC={v[1]:.2f} rank={v[2]:.2f} "
          f"@ bias={v[3]} gain={v[4]} spread={v[5]} theta={v[6]:.0e}")

esn = EchoStateNetwork(n_nodes=M)
xs = esn.states(u)
n_e, _, _ = benchmarks.narma_nrmse(xs, u, 10, N_WASH, N_TRAIN)
_, mc_e = benchmarks.memory_capacity(xs, u, N_WASH, N_TRAIN, d_max=30)
print(f"  ESN-{M} (untuned): NRMSE={n_e:.3f} MC={mc_e:.2f} "
      f"rank={benchmarks.effective_rank(xs, N_WASH):.2f}")
print(f"\nElapsed {time.time()-t0:.0f} s")
