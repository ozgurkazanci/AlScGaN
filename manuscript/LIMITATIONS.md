# Declared limitations and modelling choices - INTERNAL CHECKLIST

**This file is not part of the manuscript and must not be assembled into it.**
An earlier version of this file was assembled into the manuscript verbatim,
which carried the L-numbers and this preamble into the built document. The seventeen items are now distributed through Methods, Results and
Discussion as prose; `check_limitations_coverage.py` verifies after every build
that each is still represented, and the map at the end records where each lives.

The list is the consolidated output of an independent adversarial review of the
simulation package. Nothing here is a defect to be hidden. Several are
load-bearing choices whose disclosure is what makes the rest of the claims
defensible.

**Numbers were re-verified against the archived results and several were stale.**
They are corrected in place and flagged CORRECTED. Do not re-import an
uncorrected figure from an older copy of this file.

## Geometry and the meaning of "graded"

**L1 — The model depends only on the time-constant spectrum, not on its spatial
arrangement.** The pad is a bank of parallel segments sharing one electrode
pair, so the field is common to all of them and the observable is a symmetric
area-weighted sum. The output is therefore exactly invariant to the ordering of
the segments and to the direction of the composition gradient (verified
numerically to 3e-14 over 3000 random field steps). "Graded" in this work means
"designed distribution of relaxation time constants" and nothing more. Readers
must not infer that gradient direction is a design variable in this model.

**L2 — Inter-segment electrostatic coupling is neglected.** Segments are treated
as independent. This is defensible for the lateral geometry adopted here: on a
combinatorial wafer the composition varies over millimetres while the film is
about 100 nm thick, so the boundary region between neighbouring compositions is
of order 1e-4 of the pad area. It would NOT be defensible for a growth-axis
graded stack, where polarization mismatch at internal interfaces and
conductivity-driven field redistribution are first-order effects. The choice of
lateral geometry is what buys the exact uniform-field statement, and the
manuscript should say so explicitly rather than presenting uniform field as a
generic approximation.

## Material model

**L3 — Bandgap uses the linear virtual-crystal approximation.** Pairwise bowing
is neglected in the main results. AlGaN bowing alone is of order 0.9 eV, and
Sc-containing wurtzites are more strongly nonlinear, so absolute compositions
carry errors of a few hundred meV of gap. The sensitivity run with pairwise
bowing (0.9, 4.2, 3.0 eV) is reported: the design rule survives - the iso-Ec
trajectory stays monotone and still spans more than seven decades - but the
composition values that realise a given time constant shift.

**L4 — The retention prefactor is pinned, and the offset is phenomenological.**
tau_ret = TAU0 exp[(PHI0 + GAMMA*Eg)/kT] with TAU0 fixed at 1e-13 s, an inverse
phonon attempt time, so that temperature dependence is physically parameterised
rather than an artefact of an unconstrained fit. GAMMA = 0.258 and
PHI0 = -0.196 eV then follow from the two retention anchors. The negative offset
carries no microscopic claim; only the combination is calibrated, and only at
300 K.

**L5 — The two retention anchors are design targets, not measurements.** They
encode the established qualitative ordering (wide-gap AlScN effectively non-
volatile on laboratory timescales, Ga-rich nitride ferroelectrics leakage-
limited and volatile). The coercive-field anchors, by contrast, are literature
values and are cited as such. The Al-rich retention anchor is conservative
against the measured behaviour of Al0.7Sc0.3N [24]. The conclusions depend on
the tau span being large and monotone in the Al:Ga ratio, not on the endpoint
values.

**L6 — The remanent-polarization map is an ad hoc linear fit** with no
independent calibration. It scales the observable but does not enter the
dynamics.

## Switching kinetics

**L7 — Switching within a segment is a single exponential**, the n = 1 KAI
limit. There is no nucleation-limited-switching time dispersion inside a
segment; all dispersion comes from the composition spread. This is not the
measured limit for our operating regime. Al0.72Sc0.28N is nucleation-limited
at low field and only KAI-like at high field [28], and our sub-coercive drive
sits on the low-field side. The dispersion the nucleation-limited picture
would add [19] is not exploited by the design, so the choice stays
conservative with respect to the paper's claim - but it is the wrong limit for
the regime, and a quantitative comparison with experiment would need the
nucleation-limited distribution.

**L8 — The Merz convention fixes what Ec means.** W = ln(1e-3/1e-9) = 13.8
defines Ec as the field that reverses a segment in 1 ms, i.e. a kHz-loop
coercive field, consistent with the loop-measured anchors. Merz-law coercive
fields are frequency dependent, so every Ec quoted in this work must be quoted
with that timescale convention. The same convention fixes the activation field
at W·Ec ≈ 37 MV cm⁻¹, about three times shallower than the ≈126 MV cm⁻¹
measured for Al0.72Sc0.28N [28]. A steeper field dependence would move the
usable drive bias closer to Ec and raise the switching energy, but it does not
change the structure of the competition between switching and leakage on which
the design rests, because the drive is chosen by search in every case. Note
also that the depolarization channel stays active while the field is applied,
so leaky segments pole incompletely - this is the mechanism by which the tau
spectrum enters the response, and it is a modelling choice, not a derived
result.

## Operating conditions

**L9 — Main results are at 300 K.** The effective barrier of about 0.95 eV
shifts tau by one decade per roughly 21 K, so the entire designed spectrum
slides with ambient temperature. The temperature sweep (275-325 K) is reported
rather than assumed away.

## Statistical practice adopted (not limitations, but must be stated)

- Operating points, the designed tau window, and all ESN hyperparameters are
  selected on seeds disjoint from the seeds used for reported results.
- Every reported comparison uses 10 mask realizations crossed with 10 input
  realizations, with identical (mask, input) pairs across designs, and the
  differences are tested with a paired Wilcoxon signed-rank test.
- The ESN baseline is tuned over spectral radius, leak rate, input scale, and
  bias scale, and averaged over multiple weight realizations, so it is not a
  strawman. Readout dimension is matched between device and baseline.
- Memory capacity is reported against a surrogate-input noise floor, because the
  sum of squared correlations is positively biased.
- The uniform baseline is not a single arbitrary composition: the comparison is
  best-versus-best, each design at its own selected operating point, and the
  homogeneous array tiles the same tau span the spread array covers.

## Readout conditioning (discovered while building stage 5; must be reported)

**L10 — The state matrix has far fewer independent directions than columns.**
A four-pad array with fifty virtual nodes each produces 200 state columns, but
the participation ratio of the z-scored state correlation matrix is close to
unity and the training Gram matrix has a condition number of order 1e33, with
only 60 of its 201 columns numerically independent (CORRECTED from 1e35, which
no script computed; exp8_declared.py now does). The
readout is therefore severely ill-conditioned, and two consequences follow that
the manuscript must state rather than let a reader assume away.

First, selecting the ridge regularization for single-device accuracy alone
returns an essentially unregularized solution. That solution is legitimate as a
single-device result - it is validated on a held-out tail and evaluated on a
disjoint test window - but its large mutually cancelling weights are exact only
on the device they were fitted to. Cross-device transfer must therefore be
reported as a function of regularization; at one arbitrary value the metric
describes conditioning rather than reproducibility.

Second, because the readout leans on very-low-variance directions, the reported
accuracy presumes a readout that can resolve them. The measurement-noise sweep
is reported for that reason, and the signal-to-noise ratio at which the
composition-spread advantage is no longer resolvable is quoted explicitly. It
is a requirement placed on the charge amplifier, not a property of the film,
and it is the single most important number for anyone attempting the
experiment.

Both effective degrees of freedom and the participation ratio are reported
alongside the feature count, so that P x M columns is never mistaken for
P x M usable features.

## Computational class of the device (stage 0 controls)

**L11 — NARMA-10 is not a valid primary metric for this device, and is
reported only with its control.** NARMA-10 has a large linear component, so
minimizing its error rewards storage rather than computation. Measured on the
same footing: a plain 30-tap delay line - ridge regression on the raw input
history, no device at all - reaches NRMSE 0.39, while the pad at its
NARMA-selected drive reaches 0.56. Selecting an operating point by NARMA error
also drives the input modulation toward zero, switching the device
nonlinearity off. Every NARMA number in this work is therefore quoted beside
the delay-line control, and the primary metric is delayed parity instead,
which no linear filter of the input can produce at any delay (measured
delay-line capacity 0.004, i.e. chance; CORRECTED from 0.006, which is the
standard deviation of that measurement rather than its mean).

**L12 — Without a feedback loop the pad is a Hammerstein system and has no
nonlinear memory.** Driven open-loop, the pad is an instantaneous nonlinearity
followed by a bank of linear filters: it solves zero-delay parity perfectly
and retains a weak, fast-decaying ability beyond that, giving a nonlinear
memory capacity of about 1.35 regardless of design. CORRECTED: earlier drafts
said "about 1.0" and "at chance for every delay of one or more". Measured
open-loop accuracy is 1.000 / 0.710 / 0.622 / 0.551 / 0.505 at delays 0-4, so
1.00 of the capacity is the zero-delay term and about 0.3 sits at delays one to
three. The structural argument below explains this correctly - the products are
present but entangled, hence only partly readable - but "no nonlinear memory at
all" overstates what was measured. The reason is structural. The
per-slot update is p <- p f(E) + g(E), so the state does contain products of
inputs at different times, but each such product is multiplied by the
intervening f(E) values and is therefore entangled with the intervening
inputs rather than linearly readable, whereas the purely additive g(E) terms
survive cleanly. Interleaving field-free dwell slots does not help (tested in
exp8_declared.py: open-loop capacity 1.30 with none, and 1.30 with one, two or
four, over 25 paired realizations. CORRECTED - the earlier figure of 1.27
matched no archived run). Closing a delayed-feedback loop - a charge
amplifier summed into the shared drive, one frame delayed - does: capacity
rises to 3.14 at gain 0.003 and parity is solved out to delay two (CORRECTED
from 3.25). All reported results
therefore use the closed-loop configuration, and the open-loop result is
reported as the control that establishes why the loop is necessary.

**L13 — The usable feedback window is narrow, and that is a real engineering
constraint.** CORRECTED, and this was the most consequential error in the file.
Earlier drafts said "loop gains of 0.01 to 0.03 give the capacities above; at
0.1 and beyond the loop saturates" - but those gains are where the device is
dead. The measured window is **0.001 to 0.006** (a factor of six, 0.78 decades,
not "half a decade"), and its lower edge is censored by the sweep grid, on
which 0.001 is the smallest non-zero gain tested. Collapse begins an order of
magnitude earlier than the old text claimed: capacity is 1.28 at gain 0.010,
0.43 at 0.020 and 0.01 at 0.030. The old figures traced to the stale
FEEDBACK = 0.01 default in config.py rather than to the sweep. The gain must be
held to about three quarters of a decade, which is a requirement on the
amplifier, not on the film.

**L14 — The device does not approach a tuned software reservoir on nonlinear
memory.** A tuned echo state network of matched readout dimension reaches
capacity 12.5 at eight channels and is still above chance at delay twelve, the
largest delay swept, so its depth is right-censored rather than measured; the
closed-loop pad reaches 3.1 and delay two, and the ratio runs 2.8x at one
channel to 4.3x at eight. CORRECTED: the earlier pair "11.0 and delay eight"
against "3.25 and delay two" mixed two different channel counts and used the
stale closed-loop figure. The case for the device is energy and area at the
sensor, not accuracy parity with software, and the manuscript must not imply
otherwise.

## Readout precision (the binding experimental requirement)

**L15 — The composition-spread advantage requires roughly 90 dB of readout
signal-to-noise ratio, and is not resolvable below it.** This is the same
ill-conditioning as L10 seen a second time: a readout that leans on
low-variance directions needs large dynamic range. Measured at zero deposition
noise and zero switching jitter, the capacity advantage of the spread over one
time constant per pad is +0.161 with a noiseless readout, +0.132 at 90 dB,
+0.036 at 80 dB, and indistinguishable from zero at 70 dB and below. Reaching
95% of the noiseless capacity needs 100 dB. Ninety decibels on a per-slot
switched-charge measurement is about fifteen effective bits; it is achievable
with a slow-integrating charge amplifier but it is a specification, and it
should be budgeted before fabrication rather than discovered afterwards.
Cycle-to-cycle coercive-field jitter compounds it: 1% jitter alone reduces the
capacity from 3.05 to about 1.0 irrespective of readout precision.

**L16 — The interleaved design was tested and rejected.** Giving every pad a
comb spanning the whole window, rather than a contiguous sub-window, is
statistically indistinguishable at one channel - as it must be, since a single
pad spans the whole window either way - and 7-12% worse from two channels up
(-7.4%, -9.7% and -11.5% at P = 2, 4 and 8; all p < 1e-16). CORRECTED from
"3-5% worse at every channel count", which was both understated and not
universal; exp8_declared.py now archives the comparison. Reported because it shows the partitioned design
is not an arbitrary choice among equivalent tilings: channel decorrelation
matters more than per-channel spectral coverage.

**L17 — The channel-efficiency advantage reverses at eight channels.** Paired
against one time constant per pad the spread gains 4.1% at one channel and
11.7% at two, narrows to 2.4% at four, and is 1.6% WORSE at eight. The claim is
therefore explicitly a scarce-channel claim and is stated as such; a reader
must not carry it to large arrays.

---

## Where each item now lives in the manuscript

Distributed as prose; `check_limitations_coverage.py` enforces this map after
every build.

| item | now stated in |
|---|---|
| L1 ordering invariance, meaning of "graded" | Methods 2 (Geometry) |
| L2 inter-segment coupling neglected | Methods 2 (Geometry), consequence 2 |
| L3 linear virtual-crystal bandgap | Methods 1 (Bandgap); Results 1; Discussion (Honest limits) |
| L4 retention prefactor pinned | Methods 1 (Retention) |
| L5 retention anchors are design targets | Methods 1 (Retention); Discussion (Honest limits) |
| L6 remanent-polarization map ad hoc | Methods 1 (Remanent polarization and permittivity) |
| L7 single-exponential switching | Methods 2 (Dynamics, choice ii); Discussion (Honest limits) |
| L8 Merz convention fixes what Ec means | Methods 2 (Dynamics, choice iii); Discussion (Honest limits) |
| L9 main results at 300 K | Methods preamble and 1; Results 6; Discussion (Honest limits) |
| L10 readout ill-conditioning | Methods 5; Results 4 |
| L11 NARMA-10 not a valid primary metric | Methods 4; Results 2 |
| L12 open-loop Hammerstein, loop mandatory | Methods 3 (Delayed feedback); Results 2; Discussion 1 |
| L13 usable feedback window is narrow | Results 2; Discussion (Loop gain) |
| L14 no parity with a software reservoir | Results 3; Discussion (Honest limits); Conclusion |
| L15 ~90 dB readout SNR requirement | Results 5; Discussion (Readout precision) |
| L16 interleaved design tested and rejected | Results 3 |
| L17 channel-efficiency advantage reverses | Results 3; Conclusion |
| statistical practice (5 bullets) | Methods 3, 4 and 5 |
