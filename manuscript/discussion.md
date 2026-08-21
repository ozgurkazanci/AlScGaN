# Discussion

## What the device is, as a computational object

The pad array is not a general-purpose reservoir and it is worth naming what
it is instead. Driven open-loop it is a Hammerstein system: a static
nonlinearity applied to the instantaneous drive, followed by a bank of linear
filters whose time constants are the designed composition spread. Such a
system has linear memory of whatever depth its slowest filter provides, and it
has an instantaneous nonlinearity, but it has almost no *nonlinear* memory — it
cannot cleanly form products of inputs separated in time. Our measurements bear
this out: open-loop the pad solves zero-delay parity perfectly, retains a weak
and fast-decaying ability at delays one to three (accuracy 0.71, 0.62, 0.55),
and is at chance from delay four onward. Of its open-loop capacity of 1.33, the
zero-delay term — which requires no memory at all — accounts for 1.00.

The reason is visible in the update equation. Each slot maps the state as
p ← p·f(E) + g(E). Products of inputs at different times do appear in the
resulting state, but every such product is multiplied by the intervening f(E)
factors and is therefore entangled with the intervening inputs, whereas the
additive g(E) terms survive cleanly and accumulate. A linear readout recovers
only the small unentangled residue, which is why the open-loop parity signal
decays within three delays. Linear memory is long; nonlinear memory is not. The
deficit belongs to the architecture rather than to any one design: no choice of
composition spread repairs it. Interleaving field-free dwell slots, which we
tried on the reasoning that it would decouple strong input coupling from fast
decay, does not change it either — the entanglement is structural, not a matter
of duty cycle.

Closing a delayed-feedback loop does change it, because the state then re-
enters the drive and the nonlinearity acts on stored information rather than
only on the present input. This is the ingredient the original
delay-based scheme [2] has and a bare masked drive lacks, and in a nitride pad it
costs one charge amplifier and one summing node. It is, in our view, the
single most consequential design statement in this paper: **a composition
spread supplies the timescales, but only a feedback loop turns them into
computation.**

## Which tasks this family fits

Read as a Hammerstein-plus-feedback system with long linear memory, shallow
nonlinear memory, and a designed spectrum, the natural targets are tasks whose
structure matches: a nonlinearity acting on the recent past combined with a
long linear history. Nonlinear channel equalisation is the canonical example.
Sensor linearisation and drift compensation are others, and both are
plausible at the point of measurement, which is where a device like this
belongs. Tasks requiring products across long delays — the ones an echo state
network handles comfortably — are not a good fit and we would not propose them.

## What the experiment would have to deliver

Three numbers, in decreasing order of how much they constrain the experiment.

**Readout precision.** Because the state matrix carries far fewer independent
directions than columns, the trained readout leans on small signals. The
composition-spread advantage stops being resolvable below about 90 dB of
readout signal-to-noise ratio, and reaching 95% of the noiseless capacity needs
100 dB — roughly fifteen effective bits on a per-slot switched-charge
measurement. That is a specification for the charge amplifier, not a property
of the film, and it should be checked before a
device is fabricated rather than after. It also conditions everything else we
report: the capacities in Table 2 presume a readout able to resolve those
directions.

**Loop gain.** The usable feedback window spans about three quarters of a
decade — 0.001 to 0.006, and the lower edge is set by our sweep grid rather
than by the physics, so it may be wider. Below it the system is feed-forward
and has almost no nonlinear memory; above it the loop saturates the pad and
both linear and nonlinear memory collapse, with capacity already down to 1.27
at a gain of 0.010 and to zero by 0.030. An experiment therefore needs a
trimmable loop gain, and the trim range matters more than its absolute
accuracy. Like the readout requirement, this is a constraint on the amplifier
and not on the film.

**Deposition tolerance.** The reproducibility argument is a variance
statement, and it has a threshold: above a certain composition scatter the
designed and random spectra become statistically indistinguishable, at which
point the designed array has no reproducibility advantage left to offer. That scatter is σ = 0.02 in cation fraction, i.e. 2 at%, and
the last value at which the designed spread still pays is 1 at%; two
published measurements bear on it - though they measure different things and
should not be conflated. Our sigma is independent random scatter between
nominally identical pads, so its direct analogue is run-to-run
reproducibility: Gregoire et al. co-sputtered the same composition-spread
library on two separate days and mapped both by x-ray fluorescence, finding a
mean absolute deviation of 0.1 at.% and a maximum of 0.7 at.% [27] - well
inside our budget, although for an oxide rather than a nitride. The other
quantity is systematic drift with position: Carmona-Cejas et al. measured the
Sc cation fraction across a 200 mm AlScN wafer by Rutherford backscattering as
28.4% at the centre and 30.6% at the edge [26], a full range of 0.022 in
cation fraction. That is a gradient rather than scatter, so it bounds how far
a pad's mean composition moves with wafer position rather than how much
identical pads differ; comparable radial variation is reported elsewhere [15],
and wafer-scale integration of a fixed AlScN composition has been demonstrated
across 200 mm [18]. Read correctly, the run-to-run requirement is met with
margin and the positional requirement is the one to design around.

## Relation to the ternary literature

The lowest coercive field yet reported for a wurtzite ferroelectric was
achieved in sputtered ScGaN [11, 12], and the AlScN family [9] is where most
of the device work sits. The quaternary itself has been grown by molecular
beam epitaxy [13], though not as a composition spread. Our result does not compete with either; it explains what
neither can do. Both are single-composition-axis systems, so both trade
coercive field against relaxation time at a fixed exchange rate, which we
quantify. The quaternary is not a better ferroelectric than either parent —
it is the smallest system in which the two properties come apart.

## Honest limits

We have not shown that this device is efficient, only that it is designable.
We quote no energy figure at all, and no reader should infer one from the case
we make for energy and area at the sensor: an estimate counting ferroelectric
switching work alone would exclude the drive amplifier, the sense amplifier and
the converter, which in comparable analog systems typically dominate. We have not shown that it beats
software: a tuned echo state network at matched readout dimension reaches three
to four times the nonlinear memory capacity, the ratio widening with channel
count from 2.8× at one channel to 4.3× at eight, and its depth exceeds the
largest delay we measured.

Nor have we grown anything, and three features of the model deserve to be
weighed before the numbers are. The material model is phenomenological, and two
of its four calibration anchors — the retention pair — are design targets rather
than measurements; what the conclusions rest on is that the relaxation-time span
is wide and monotone in the Al:Ga ratio, not that either endpoint is right. The
composition values that realise a given time constant shift when bandgap bowing
is included, even though the design rule itself survives, so those values should
be read as illustrative rather than as fabrication targets. And the switching
kinetics are treated in the single-exponential limit, which is the wrong limit
for the sub-coercive regime we operate in: Al0.72Sc0.28N is nucleation-limited
at these fields [19, 28]. That choice is conservative with respect to our claim,
because the extra dispersion nucleation-limited switching would supply is
dispersion our design does not exploit, but a quantitative comparison with a
real film would need it. In the same vein, our Merz convention defines the
coercive field at a kHz loop rate and yields an activation field about three
times shallower than the measured one; a steeper dependence would push the
usable drive closer to Ec and raise the switching energy without altering the
switching-versus-leakage competition the design rests on.

Finally, the operating point is 300 K. Because the effective barrier varies
along the trajectory, the spectrum does not merely slide with temperature but
compresses, and the temperature sweep we report is what discharges that
limitation rather than an incidental robustness check.

What we believe does transfer beyond this material system is the framing. A
time-constant spectrum is only useful if the elements carrying it can be
driven together, so the figure of merit for a designed reservoir material is
not the range of relaxation times it offers but the range it offers *at fixed
switching threshold*. By that measure the quaternary nitride is, as far as we
know, without a competitor among the wurtzite ferroelectrics.
