# Results

All values are simulated. Every number here is generated into
`results/SUMMARY.md` by the analysis scripts and transcribed from there. Unless
a temperature sweep is stated, all values are at an ambient of 300 K.

## 1. Coercive field and relaxation time come apart in the quaternary

Figures 1a and 1b show the two property maps over the cation plane. The
coercive-field contours run almost horizontally: Ec follows the Sc fraction and
is nearly indifferent to the Al:Ga ratio. The time-constant contours run
diagonally, following the bandgap. The two families are not parallel, and that
non-parallelism is the whole content of the decoupling claim — the iso-Ec
trajectory drawn on Figure 1b crosses seven decades of relaxation time without
leaving its own coercive-field contour.

At Ec = 2.7 MV cm⁻¹ the accessible Ga range spans **7.43 decades** of
relaxation time while the coercive field varies by less than 10⁻¹⁴ MV cm⁻¹,
exactly constant because the trajectory is an analytic inverse (Figure 1c).

The comparison that matters for a device is not the range available in
principle but the range available *at one switching threshold*, since an array
whose elements switch at different fields cannot share a drive line. On that
basis (Figure 1d, Table 1), moving the relaxation time along AlScN costs
1.30 MV cm⁻¹ of coercive field per decade, and along ScGaN 3.44. Holding Ec to
±5%, AlScN delivers 0.196 decades and ScGaN 0.072, against the quaternary's
7.43 at zero tolerance — a factor of **38** at ±5%, and unbounded as the
tolerance closes.

**Table 1.** Decades of relaxation time reachable inside a coercive-field
tolerance band.

| tolerance on Ec | AlScN | ScGaN | quaternary |
|---|---|---|---|
| ±1% | 0.030 | 0.010 | 7.43 |
| ±2% | 0.075 | 0.026 | 7.43 |
| ±5% | 0.196 | 0.072 | 7.43 |
| ±10% | 0.406 | 0.154 | 7.43 |

Including pairwise bandgap bowing shifts the compositions that realise a given
time constant but leaves the trajectory monotone and the span at 7.56 decades,
so the design rule does not rest on the bandgap approximation — though, as
Methods Section 1 sets out, the composition values themselves do.

## 2. The device computes, but only with the loop closed

Two controls decide whether any benchmark number that follows means anything.

**A delay line is the benchmark to beat, and on NARMA-10 it wins.** Ridge
regression on the raw input history, with no device at all, reaches NRMSE
**0.3875** with 30 taps; the pad array reaches 0.56 at its NARMA-selected drive
and 0.84 at the drive selected for the primary metric. NARMA-10's target is
dominated by a linear function of the input history and a delay line has
perfect linear memory, so the task rewards storage. Worse, selecting an
operating point by NARMA error pushes the input modulation toward zero and
switches the device nonlinearity off. NARMA-10 is therefore reported only
beside this control (Figure 3d).

**On delayed parity the same delay line is exactly at chance**: capacity 0.004,
accuracy 0.501, against 7.00 for an oracle carrying the required products. The
pad array reaches capacity 2.3–3.2 and solves zero-delay parity perfectly, so
it computes something no linear filter of the input can.

**Open-loop, however, the pad has little nonlinear memory, and what it has is
shallow.** Figure 2e sweeps the feedback loop gain. With the loop open the
capacity is **1.33** on that sweep, but the number needs reading carefully: the
zero-delay parity term, which requires no memory at all, contributes 1.00 of
it. Resolved by delay on the 25-realization paired protocol used for the
dwell-slot control below — where the same open-loop configuration scores 1.30 —
parity accuracy is 1.000 at delay zero, 0.710 at delay one, 0.622 at delay two,
0.551 at delay three and 0.505 at delay four, contributing 1.000, 0.201, 0.071,
0.012 and 0.002 to the capacity. Only about 0.29 of it reflects memory of any
depth. That residual is what
the Hammerstein structure predicts: products of inputs at different times are
present in the state but entangled with the intervening inputs, so a linear
readout recovers only a rapidly decaying fraction of them. Closing the loop
raises the capacity to **3.10** at a gain of 0.003 and parity is solved out to
delay two. The usable window is **0.001 to 0.006**, a factor of six or about
three quarters of a decade; its lower edge is censored by the sweep grid, on
which 0.001 is the smallest non-zero gain tested, so the window may extend
further down. Above it the loop saturates the pad and memory collapses fast:
capacity is already 1.27 at a gain of 0.010, 0.17 at 0.020 and 0.01 at 0.030.
Interleaving field-free dwell slots, tested on the reasoning that it would
separate strong input coupling from fast decay, leaves the open-loop capacity
genuinely unchanged — 1.30 ± 0.12 with no dwell slot and 1.30 with one, two or
four, over the same 25 paired realizations. The limitation is structural, not a matter of duty
cycle.

Figure 2a–d shows the signatures an experiment would check first. The retention
half-life is almost the same for a spread pad and a single-composition pad
(0.203 s against 0.210 s), so a single-number retention measurement does not
see the spectrum at all; the decay *shape* does. Figure 2d locates the selected
drive at bias 0.65, where the switching rate sits in the middle of the
relaxation-rate spectrum and **59%** of segments forget by leakage rather than
field overwrite — the crossover, not either extreme. Linear memory capacity
there is **4.07** for the spread pad, 2.98 for one time constant per pad and
2.00 for a single time constant, significant against a surrogate-input
threshold out to delays 4, 4 and 3 respectively. The nonlinear-memory scan is
flat across this region — 3.11, 3.10 and 3.10 at biases 0.60, 0.65 and 0.70 —
so the selected drive sits on a plateau rather than a sharp optimum.

## 3. The designed spectrum pays when readout channels are scarce

Figure 3 compares the four designs at matched channel count and matched feature
count, each at its own selected operating point, over 100 paired realizations.

**Table 2.** Nonlinear memory capacity, mean ± s.d.

| design | P = 1 | P = 2 | P = 4 | P = 8 |
|---|---|---|---|---|
| composition spread | 2.29 ± 0.28 | 2.90 ± 0.22 | 3.10 ± 0.38 | 2.92 ± 0.61 |
| one τ per pad | 2.20 ± 0.32 | 2.59 ± 0.37 | 3.03 ± 0.19 | 2.97 ± 0.63 |
| random spread | 2.21 ± 0.13 | 2.56 ± 0.22 | 2.95 ± 0.24 | 3.16 ± 0.27 |
| single τ | 2.07 ± 0.38 | 2.24 ± 0.27 | 2.33 ± 0.26 | 1.93 ± 0.39 |
| tuned ESN | 6.34 ± 0.26 | 8.72 ± 0.19 | 10.80 ± 0.23 | 12.52 ± 0.19 |
| delay line | 0.00 ± 0.01 | — | — | — |

Paired against one time constant per pad on identical mask and input
realizations, the spread gains **+4.1%** at P = 1 (p = 9.5 × 10⁻³) and
**+11.7%** at P = 2 (p = 9.6 × 10⁻¹⁸). By four channels the advantage has
narrowed to +2.4%, and by eight it has reversed to −1.6%. Against a single time
constant for the whole array it instead grows monotonically, from +11.0% at
P = 1 to +51.2% at P = 8.

The useful form of this is a channel-efficiency statement: a continuum of time
constants inside each pad substitutes for extra readout channels, and stops
paying once there are enough channels to tile the spectrum discretely. Since
each channel is a charge amplifier and a converter, the scarce-channel regime
is the one a physical implementation occupies. The claim is explicitly a
scarce-channel claim and must not be carried to large arrays.

We also tested an interleaved design in which every pad carries a comb spanning
the full window rather than a contiguous sub-window. At one channel the two are
statistically indistinguishable, as they must be, since a single pad spans the
whole window either way (−0.2%, p = 0.09). From two channels up the comb is
clearly worse: −7.4% at P = 2, −9.7% at P = 4 and −11.5% at P = 8, all with
p < 10⁻¹⁶. Channel decorrelation evidently matters more than per-channel
spectral coverage: partitioning specialises each channel, interleaving makes
the channels resemble one another. The comb was evaluated at the
partitioned design's selected operating point rather than at one searched for
it, so the deficit is an upper bound on how well a comb could do; we report the
negative result because even so it establishes that the partitioned design is
not an arbitrary choice among equivalent tilings of the same τ window.

Figure 3b shows where each design runs out. Every device variant solves parity
at zero delay and falls to chance by delay five or six. The tuned echo state
network does not fall to chance anywhere in the swept range: it is still at
0.873 accuracy at delay twelve, the largest delay measured, so its depth is
right-censored by our sweep rather than resolved. Its capacity there is 12.5 against the device's 2.9 at
the same eight channels, and 3.1 at the device's best channel count of four. We state that plainly: this device does not approach a
software reservoir on this metric — the ratio runs from 2.8× at one channel to
4.3× at eight — and the case for it is energy and area at the sensor.

## 4. Deterministic disorder reproduces; random disorder does not

The two spreads perform alike — that they do is the point of the comparison.
With perfect fabrication their NARMA-10 errors are 0.804 and 0.806 — both
well above the 0.3875 delay-line control of Section 2, beside which Section 2
requires every NARMA number to be read — and their time constant statistics are
matched by construction. They differ in reproducibility.

At zero deposition noise the designed array shows **exactly zero**
device-to-device variation, a state correlation of **1.0000** between nominally
identical devices, and a readout transfer penalty of **0.000** — a readout
trained on one device runs on another with no loss. The random array, with the
same statistics and the same performance, still incurs a penalty, because its
spectrum is redrawn per device: **0.082** over the twenty-device sweep and
**0.088** over the ten-device paired run that carries the significance tests
below.

As deposition noise rises the two converge (Figure 4b). The designed array
remains significantly more transferable at σ = 0.005 (penalty 0.053 against
0.126, a factor 2.39, p = 0.002) and at σ = 0.010 (0.114 against 0.181, factor
1.58, p = 0.006), and the difference vanishes at σ = 0.020 (factor 1.01, p =
0.77). The designed spread therefore stops being measurably more
transferable at **σ\* = 0.02 in cation fraction**, which is 2 at%; the last
scatter at which it still pays is σ = 0.01, so the fabrication budget is to
hold composition to about ±1 at% or better, and beyond 2 at% a designed
spectrum buys nothing a random one does not. For scale, the run-to-run reproducibility of a
co-sputtered composition spread has been measured at 0.1 at.% mean absolute
deviation and 0.7 at.% maximum [27], which is the quantity sigma represents
and sits well inside the budget; the systematic variation of Sc cation
fraction across a 200 mm AlScN wafer is larger, 28.4% at the centre against
30.6% at the edge [26], but that is a gradient with position rather than
scatter between nominally identical pads.

Reporting this required a detour we consider a result in its own right. The
array produces far more state columns than independent dynamical directions —
the participation ratio of the standardised state correlation matrix is 1.05 to
1.12 for 200 columns, only 60 of the 201 columns of the training design matrix
are numerically independent, and the Gram matrix condition number is of order
10³³. Choosing the readout regularization for single-device accuracy alone
returns an essentially unregularised solution whose large cancelling weights
are exact only where they were fitted: it scores 0.730 on its own device and
**1321** on another. On a selection seed and at σ = 0.01, where the two
arms can be told apart at all, regularising at λ = 10² costs 0.090 in
single-device error and brings the designed array's transfer penalty to 0.080
(Figure 4a); the 0.000 above is the same arm at zero deposition noise. Cross-device transfer has
to be reported against regularization, or the metric describes conditioning
rather than reproducibility.

## 5. Readout precision is the binding experimental requirement

The same ill-conditioning appears a second time, and this is the most
consequential number in the paper for anyone attempting the experiment. Because
the trained readout leans on low-variance directions, it needs large dynamic
range. Figure 4c sweeps readout signal-to-noise ratio at zero deposition noise
and zero switching jitter:

| readout SNR | capacity advantage of the spread over one τ per pad |
|---|---|
| noiseless | +0.161 |
| 100 dB | +0.212 |
| 90 dB | +0.132 |
| 80 dB | +0.036 |
| 70 dB and below | ≈ 0 |

The composition-spread advantage stops being resolvable below about **90 dB**,
and the spread design needs **100 dB** to reach 95% of its noiseless capacity.
Ninety decibels on a per-slot switched-charge measurement is roughly fifteen
effective bits — demanding but not exotic for a slow-integrating charge
amplifier. It is a specification on the charge amplifier rather than a property
of the film, it is nonetheless the single most binding requirement the design
imposes, and it should be budgeted before a device is fabricated rather than
after. Cycle-to-cycle coercive-field jitter compounds it, and no amount of
readout precision buys the loss back: 1% jitter alone drops the spread array's
capacity from 3.05 to 0.99 at every readout SNR from noiseless down to 50 dB
(Figure 4d). It also reverses the comparison, and we state that plainly. Under
1% jitter one time constant per pad scores 1.27 against the spread's 0.99, and
under 3% jitter 0.54 against 0.42 — a designed spectrum is the *worse* design
once switching jitter dominates, because the jitter destroys precisely the
deterministic structure the design contributes. The composition-spread claim is
therefore bounded twice over: it is a scarce-channel claim, and it is a
low-jitter claim.

## 6. The spectrum earns its width through temperature, not through capacity

The robustness sweeps (Figure 5) separate two questions that are easy to
conflate.

**How many decades does the task need?** At fixed temperature, remarkably few.
Capacity rises from 2.57 with a single time constant to 3.12 with one decade of
spread and is then flat out to five (3.12, 3.11, 3.10, 3.09). Linear memory
keeps improving to about three decades (1.06 → 3.38). A discrete ladder reaches
the continuum's value at roughly eight distinct time constants.

**Why then design seven decades?** Because the whole spectrum moves with
ambient temperature — one decade per 25 K at mid-window, and, since the barrier
falls along the trajectory, one decade per 19 K at the slow end against one per
33 K at the fast end, so the spectrum compresses as it moves rather than
sliding rigidly. A wide spectrum always retains some segments at the useful
timescale wherever it goes. Over 275–325 K the single-time-constant array loses
**36.6%** of its capacity while the spread arrays lose **2.4%** and **0.5%**.
The width buys temperature robustness, not peak capacity, and that is the
honest statement of what the material is for.

Bandgap bowing changes the capacity by 0.1% for the composition spread and
0.1% for one time constant per pad, and by 0.3% for the single-time-constant
array; the random-spread arm was not run under bowing. Results are converged in the number of
composition segments resolved per pad (3.075 at four segments to 3.060 at
sixty-four) and in the number of virtual nodes.

## 7. The ternary control, and the substitution it can and cannot make

Figure 6 joins the materials argument to the device argument. A ternary-like
array is built along a single composition axis, driven from the same shared
line, and given its own best drive.

It cannot build the designed window: asked for five decades of relaxation time
it reaches **1.09** before leaving the physical composition range, and pays
**3.65 MV cm⁻¹** of coercive-field spread for even that.

What happens next is more interesting than a simple failure. Because the Merz
rate is exponential in Ec/E, that coercive-field spread becomes **3.7 decades**
of switching-rate spread under one shared drive — uncontrolled dynamical
diversity standing in for the designed kind. At its own best drive the ternary
array reaches capacity **2.62** against the quaternary's **3.05**, or 86% of it.
Coercive-field disorder does substitute for designed time-constant disorder.

But only at one temperature. Over 275–325 K the ternary array loses **22.9%**
of its capacity against the quaternary's **2.2%**, because temperature
robustness requires a wide spread of *relaxation times* and the ternary has
barely one decade of them. The substitution is real and it is fragile, and
separating those two statements is what the quaternary is for.
