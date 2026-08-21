# Methods

All results in this work are simulated. No film was grown and no device was
measured. The material model is phenomenological and calibrated to published
coercive-field measurements; the two retention anchors are stated design
targets rather than measurements, and are identified as such below. Unless a
temperature sweep is stated explicitly, every reported result is at an ambient
of 300 K. The complete simulation package, including every script that produced
a figure, is available at [repository].

## 1. Composition–property model

We model wurtzite Al(1−x−y)Ga(x)Sc(y)N through four maps of the cation
fractions x (Ga) and y (Sc), with the Al fraction 1 − x − y constrained to
stay above 0.02.

**Bandgap.** The main results use the linear virtual-crystal approximation,

  Eg(x, y) = (1 − x − y)·E_AlN + x·E_GaN + y·E_ScN,

with E_AlN = 6.2 eV, E_GaN = 3.43 eV and an effective E_ScN = 2.0 eV. Bowing
is neglected here and its effect is reported as a sensitivity analysis using
pairwise bowing parameters (b_AlGa, b_AlSc, b_GaSc) = (0.9, 4.2, 3.0) eV. The
AlGa value sits within the range reported for wurtzite AlGaN in the standard
compilation [21] and in dedicated measurements on the alloy [32]; the two
Sc-pair values are estimates, since no comparable compilation exists for them.
The neglect is not free. AlGaN bowing alone is of order 0.9 eV, so absolute
compositions carry errors of a few hundred meV of gap; the Sc-containing pairs
are more strongly nonlinear still, which is why the two Sc bowing parameters
used in the sensitivity run are larger than the AlGa value and are estimates
rather than recommended constants. What survives the approximation is the
design rule — a monotone iso-Ec trajectory spanning more than seven decades of
relaxation time — and not the particular composition that realises a given time
constant. Composition values quoted anywhere in this work should be read in
that light.

**Coercive field.** Switching in Sc-containing wurtzites nucleates in
Sc-bearing unit cells, so Ec is taken to be governed by the Sc fraction with a
weak Ga softening term,

  Ec(x, y) = [E0 + S·(y − y0)]·(1 − g·x),  g = 0.12.

E0 and S are fixed by two literature anchors: Ec = 4.7 MV cm⁻¹ for sputtered
Al(0.73)Sc(0.27)N [9] and Ec = 1.5 MV cm⁻¹ for sputtered
Sc(0.40)Ga(0.60)N [11, 12], the lowest coercive field reported for any
wurtzite ferroelectric. This gives E0 = 4.70 MV cm⁻¹ and S = −23.7 MV cm⁻¹ per
unit Sc fraction. Unlike the retention anchors below, both are measured values
and are cited as such.

Because Ec depends on both cation fractions, the locus Ec(x, y) = Ec* can be
inverted analytically for y(x); we call this the iso-Ec trajectory and every
device in this work lies on one.

**Retention time constant.** Depolarization is leakage-mediated, and the
leakage barrier is taken proportional to the alloy bandgap in the manner of a
Poole–Frenkel process, which is the dominant leakage mechanism identified in
Al0.7Sc0.3N itself, attributed there to positively charged nitrogen vacancies
[29], and in Al-rich AlGaN [23],

  τ_ret(x, y, T) = τ0 · exp{[φ0 + Γ·Eg(x, y)] / kT}.

The prefactor τ0 is **pinned** at 10⁻¹³ s, an inverse phonon attempt time, so
that the temperature dependence is physically parameterised rather than an
artefact of an unconstrained fit. Γ = 0.258 (dimensionless) and φ0 = −0.196 eV
then follow from two anchors: τ_ret = 10³ s at (x, y) = (0.10, 0.35) and 10⁻³
s at (0.60, 0.35). These two anchors are **design targets rather than
measurements**: they encode the established qualitative ordering that wide-gap
AlScN is effectively non-volatile on laboratory timescales while Ga-rich
nitride ferroelectrics are leakage-limited and volatile. The Al-rich anchor is
conservative against what has been measured - Al0.7Sc0.3N shows negligible
polarization loss over 1000 s even at 400 °C [24], and AlScN memory devices
have held their state for 10⁵ s [30], so 10³ s at 300 K understates the true
retention of that end of the range. The anchor fixes where the spectrum sits in
absolute time; a longer true retention shifts the whole spectrum together,
which is compensated by moving the composition window rather than by changing
the design rule. The offset φ0 is phenomenological and carries no microscopic
claim; only the combination is calibrated, and only at 300 K. Everything the
paper concludes depends on the τ span being large and monotone in the Al:Ga
ratio, not on either endpoint value being exact.

The effective barrier φ0 + Γ·Eg is not a single number across the design
window: it falls from ≈1.02 eV at the Al-rich end of the iso-Ec trajectory to
≈0.59 eV at the Ga-rich end, and is ≈0.95 eV at the Al-rich retention anchor.
The temperature sensitivity therefore varies with it, from one decade of τ per
19 K at the slow end of the spectrum to one decade per 33 K at the fast end,
and one decade per 25 K at mid-window. A warming film does not slide its
spectrum rigidly — the spectrum also compresses, the fast end moving about 1.7
times fewer decades per kelvin than the slow end.

**Remanent polarization and permittivity** are ad hoc linear maps (Pr ≈ 115 −
25x − 60(y − 0.25) µC cm⁻², ε_r by linear virtual-crystal interpolation
between 9.0, 9.5 and 20). Unlike Ec and τ_ret, neither is tied to a calibration
anchor. The permittivity map in particular gives ε_r = 10.9–11.8 over
Sc = 0.17–0.25 and so *undershoots* by roughly a factor of two the 17–21
measured for Sc(x)Al(1−x)N in that range [22], precisely because the linear
form omits the strong bowing of the measured ScAlN dielectric constant [31].
Neither map appears in a segment's equation of motion, but neither is inert
either: Pr scales the measured charge, and because the delayed-feedback loop
returns that charge to the drive, the loop gain quoted here is really the
product of the electronic gain and Pr. A systematic error in Pr would rescale
the loop gain rather than change any conclusion, since the gain is selected by
search. ε_r is used only for a bounding screening estimate that no reported
result depends on.

## 2. Device model

**Geometry.** Combinatorial co-sputtering produces a *lateral* composition
gradient [16, 17, 26]. This is a different device from a film graded along the
growth axis, which has been pursued separately to manage defects and breakdown
in ultrathin AlScN [25]; the distinction matters here because it is what makes
the uniform-field treatment below exact rather than approximate. One
metal–ferroelectric–metal pad on such a wafer therefore covers a strip of
compositions side by side, not stacked along the growth axis. We model the pad
as N parallel segments sharing one electrode pair. Three consequences follow,
and the choice is made for the first of them:

1. every segment sees exactly the same field E = V/d, so the uniform-field
   assumption is exact rather than approximate;
2. inter-segment electrostatic coupling is neglected and the segments are
   treated as independent, up to in-plane fringing at their mutual boundaries.
   On a combinatorial wafer the composition varies over millimetres while the
   film is ~100 nm thick, so that boundary region is ~10⁻⁴ of the pad area and
   the neglect is defensible for this geometry;
3. the measured charge is the area-weighted sum of segment polarizations, and
   that sum is symmetric in the segments.

Neither the uniform field of (1) nor the independence of (2) would be
defensible for a growth-axis graded stack, where polarization mismatch at
internal interfaces and conductivity-driven field redistribution are
first-order effects. The lateral geometry is what buys both, and we adopt it
for that reason rather than presenting a uniform field as a generic
approximation.

A direct and important consequence of the symmetry in (3), stated here rather
than left implicit: **the model depends only on the multiset of segment
properties, so it is exactly invariant to segment ordering and to gradient
direction.** "Graded" in this work means "designed distribution of time
constants", nothing more. We verified the invariance numerically (outputs
agree to 3 × 10⁻¹⁴ under random permutation of the segments over 3000 field
steps). Readers should not infer from the word that gradient direction or
spatial ordering is a design variable here: in this model they provably are
not, and no result in this paper depends on either.

**Dynamics.** Each segment carries a normalized polarization p ∈ [−1, 1].
Under a field E two processes compete: Merz-law [14] field-activated switching
toward sign(E) at rate r_sw = exp(−W·Ec/|E|)/τ_sw0, and leakage-mediated
depolarization toward zero at rate r_rt = 1/τ_ret, so that

  dp/dt = [sign(E) − p]·r_sw − p·r_rt.

Within a constant-field slot this is linear in p and we use the exact
solution, which is unconditionally stable and step-size exact:

  p_eq = sign(E)·r_sw/(r_sw + r_rt),
  p ← p_eq + (p − p_eq)·exp[−(r_sw + r_rt)·Δt].

Three modelling choices are encoded here and must be read as choices. (i) The
depolarization channel stays active while the field is applied, so the
sustained-field steady state is |p_eq| < 1 and leaky segments pole
incompletely — this is the mechanism by which the time-constant spectrum
enters the response, and it is a modelling choice rather than a derived
result. (ii) Switching within a segment is a single exponential,
the n = 1 limit of the Kolmogorov–Avrami–Ishibashi model [20], so all
switching-time dispersion comes from the composition spread and none from
within a segment. This is not the measured limit for the regime we operate in.
Al0.72Sc0.28N switches by nucleation-limited switching [19] at low field and
crosses over to KAI-like uniform switching only at high field [28], and our
drive is sub-coercive — the low-field side of that crossover. The dispersion
the nucleation-limited picture would add is not exploited by our design, so
the treatment stays conservative with respect to our claim; but it is the
wrong limit for the operating regime, and a quantitative match to experiment
would need the nucleation-limited distribution rather than a single
exponential. (iii) With τ_sw0 = 1 ns and a switching time of 1 ms at
|E| = Ec, W = ln(10⁶) = 13.8. This **defines** Ec as a kHz-loop coercive
field, consistent with the loop-measured anchors; Merz-law coercive fields are
frequency dependent [14], so every Ec in this work carries that convention.
The same convention fixes the activation field at W·Ec ≈ 37 MV cm⁻¹ at our
working point, about three times shallower than the ≈126 MV cm⁻¹ measured for
Al0.72Sc0.28N [28]. A steeper field dependence than ours would move the usable
drive bias closer to Ec and raise the switching energy. It would not change the
structure of the competition between switching and leakage on which the design
rests, because the drive bias is re-selected by search for every design rather
than fixed a priori.

## 3. Reservoir architecture

**Pad array.** P pads on the same wafer share one drive line — identical field
and identical mask — and are read out on P independent charge channels. Since
every design lies on one iso-Ec trajectory, all pads switch at the same field
and sharing a drive line is legitimate. *This is precisely what the quaternary
buys: in a ternary alloy, moving composition to change τ also moves Ec, and a
shared drive line becomes impossible.*

Four designs are compared at matched channel count P and matched feature count
P·M: **graded** (pad p spans the p-th sub-window of the wafer's composition
range, so each channel carries a continuum of time constants), **homogeneous**
(pad p sits at a single composition, the P compositions tiling that arm's own
selected window: one time constant per channel; because the window is itself a
searched variable, the two arms do not necessarily cover identical spans), **uniform** (all
pads at one composition), and **stochastic** (pad p spans an i.i.d. random
composition draw over the same window: matched spectrum statistics, no
reproducibility). The uniform arm's single composition is not an arbitrary
pick: its time-constant window was selected by the same coordinate search, on
the same disjoint seeds, as the spread designs, so the four-design comparison
of Figure 3 is best-versus-best. Two further comparisons are not, and are
flagged where they appear: the interleaved comb of Results Section 3 and the
readout-noise sweep of Section 5 both evaluate an arm at the composition
spread's operating point rather than at one searched for them.

**Time multiplexing.** Each input sample u(k) is expanded by a fixed mask into
M virtual-node slots of duration θ, following the delay-based scheme of
Appeltant et al. [2], with M = 50 throughout. Polarity alternates regularly,
keeping the pad charge-balanced, while the mask offsets each slot's operating
point along the Merz exponential:

  E(k, j) = Ec_ref · s_j · [b·(1 + σ_m·m_j) + G·ũ(k)],  s_j = (−1)^j,

with m_j drawn once from U(−1, 1) and held fixed as hardware. Every virtual
node therefore sits at a different distance from threshold and responds to the
input with a different gain and curvature — the physical analogue of
per-neuron biases. A mask that only flips polarity leaves every node with the
same transfer function and is reported as the naive reference.

**Delayed feedback.** ũ(k) = u(k) + F·q(k − 1), where q is the array-summed
charge of the previous frame. This is one charge amplifier and one summing
node. **The loop is not optional.** Open-loop the pad is a Hammerstein
system — an instantaneous nonlinearity followed by a bank of linear filters —
and has almost no nonlinear memory: it solves zero-delay parity perfectly, and
what little it retains beyond that decays within about three delays. The reason
is structural: the slot update has the form p ← p·f(E) + g(E), so products of
inputs at different times do appear in the state, but each such product is
multiplied by the intervening f(E) values and is therefore entangled with the
intervening inputs rather than cleanly readable by a linear readout, whereas
the additive g(E) terms survive intact. The deficit is not a property of one
design — no choice of composition spread repairs it. Field-free dwell slots do
not repair it either (tested; Section 2 of the Results). Closing the loop does.
All reported results below use the closed-loop configuration; open-loop numbers
appear only as the control that establishes why the loop is necessary.

**Readout.** The observable is the per-slot switched charge ΔP, which is what
a charge amplifier on an MFM pad delivers. Training is ridge regression with an
unpenalised intercept on z-scored states, the standardisation and the
regularisation both fitted on the training window only, with λ selected on a
held-out tail of that window. Because that selection optimises single-device
accuracy, it lands near the unregularised end: the median selected λ runs from
10⁻⁶ to 10⁻² depending on design and channel count. Every capacity reported
below is therefore a lightly regularised, single-device number, and the
cross-device transfer results of Section 4 of the Results are the ones that
show what a transferable λ costs.

## 4. Benchmarks, and why these

**NARMA-10 is reported but is not the primary metric.** Its target has a large
linear component, so minimising its error rewards storage over computation.
Measured on the same footing, a plain 30-tap delay line — ridge regression on
the raw input history, no device at all — reaches NRMSE ≈0.39 where the pad
reaches ≈0.56, and selecting an operating point by NARMA error drives the
input modulation toward zero, switching the device nonlinearity off. Every
NARMA number here is quoted beside that control.

**The primary metric is nonlinear memory capacity from delayed parity**, the
nonlinear counterpart of the linear memory capacity of Jaeger [4]. The
target is the parity of two consecutive inputs ending d steps in the past,

  y(k) = s(k − d)·s(k − d − 1),  s = 2u − 1,  u ∈ {0, 1},

and the capacity is Σ_d max(2·acc_d − 1, 0)². No linear filter of the input can
score above chance on this at any delay, delay line included: we measure 0.004
for the same 30-tap delay line, against 7.00 for an oracle carrying the
products of the first seven delays. That oracle bounds only those seven terms
and is not a ceiling for the thirteen-delay capacities reported below. A capacity above zero is therefore direct evidence that the device is
computing rather than storing.

Linear memory capacity [4], measured against a surrogate-input noise floor
because the sum of squared correlations is positively biased, is reported
alongside.

**Baselines.** A leaky echo state network [3] with a bias input, tuned over
spectral radius, leak rate, input scale and bias scale and averaged over
several weight realizations, at matched readout dimension; and the delay line
above. The echo state network's hyperparameters were tuned on the same
selection seeds and against the same objective as the device operating points,
so the baseline is selected out of sample too and is not a strawman.

## 5. Selection and statistics

Operating points — drive bias, input modulation, mask spread, slot duration,
the designed time-constant window, and the feedback loop gain — were chosen
for each design separately by coordinate search maximising nonlinear memory
capacity on SELECTION seeds. The designed time-constant window is itself one of
the searched variables, for every arm including the uniform baseline. Every
reported design comparison uses EVALUATION seeds, which are disjoint. The single-device characterisation sweeps of
Figure 2 — the drive-regime scan, the loop-gain scan and the linear-memory
profile — are averaged over three evaluation seeds at the selected operating
point. One number is an exception and we state it rather than let a reader
assume otherwise: the regularization trade-off of Figure 4a is computed on a
selection seed, because it is a diagnostic of the readout rather than a claim
about one design beating another.

Every selected optimum was checked against its grid boundaries and the grids
widened until the optimum was interior. Two contacts remain and we report them
rather than suppress them: the homogeneous arm's window-centre multiplier sits
at the edge of the searched centre range, and the uniform arm's spectral span
sits at the narrow edge of the span grid, pinned at 0.25 decades. The second is
a boundary of that arm's own definition — a "uniform" array is one whose span
tends to zero — rather than evidence of an unexplored optimum, but it does mean
the uniform baseline is the narrowest the grid allows.

Reported comparisons use 10 mask realizations crossed with 10 input
realizations, with identical (mask, input) pairs across designs, so design
differences are paired and are tested with a Wilcoxon signed-rank test.
The deposition-tolerance sweep of Figure 4b uses 20 nominally identical
devices per arm at each noise level. The significance tests quoted beside it
are a separate, smaller run: 10 devices per arm, paired across 10 input
realizations, tested with the same Wilcoxon signed-rank test. No other test is
used anywhere in this work.

A note on the readout. The state matrix contains far fewer independent
directions than columns. A four-pad array with fifty virtual nodes each
produces 200 state columns, but the participation ratio of the z-scored state
correlation matrix is 1.05–1.12, only 60 of the 201 columns of the training
design matrix are numerically independent, and its Gram matrix has a condition
number of order 10³³. Selecting λ for single-device accuracy alone therefore
returns an essentially unregularised solution: legitimate on one device, since
it is validated and tested out of sample, but composed of large mutually
cancelling weights that are exact only there. Cross-device transfer is
consequently reported as a function of λ. We also report the effective degrees
of freedom the ridge readout actually spends — 11.1 of 50 columns at P = 1,
14.5 of 100 at P = 2, 16.2 of 200 at P = 4 and 18.2 of 400 at P = 8, against
139.2 of 200 for a tuned echo state network at P = 4 — so that P·M columns is
never read as P·M usable features. One further consequence has to be carried
forward by the reader: because the readout leans on very-low-variance
directions, every capacity we report presumes a readout able to resolve them,
which is why the measurement-noise sweep of Results Section 5 is reported and
why its answer is the binding experimental requirement.
