# Introduction

Physical reservoir computing exploits the dynamics a material already has. An
input drives a physical system, the system's own relaxation supplies fading
memory and its own nonlinearity supplies the expansion, and only a linear
readout is trained [1]. The appeal is that the expensive part of a recurrent
network — the recurrent dynamics — costs nothing to run, because the physics
runs it.

What makes a material good at this is not a single relaxation time but a broad
distribution of them. A reservoir with one time constant is a single low-pass
filter; a reservoir carrying many, spread over decades, can hold the recent
past and the distant past at once, and a linear readout can then select the
timescale each task needs. This is why disordered nanomaterial networks work
so well [6-8]. In Ag/Ag₂S nanoparticle assemblies the spread of junction sizes
produces a spread of ionic diffusion rates, and it is precisely that
heterogeneity that supplies the computational richness [6, 7].

The same mechanism is also the field's central obstacle. The distribution
arises from stochastic self-assembly, so no two networks are alike. Device-to
-device reproducibility is out of reach, a readout trained on one sample is
worthless on the next, and manufacturing is therefore not on the table. The
usual response has been to move to crystalline materials and tune the
relaxation time extrinsically — with bias, illumination, or ferroelectric
polarization state. That restores reproducibility but gives up the thing that
made the disordered networks work: those knobs deliver one time constant at a
time, not a simultaneous spectrum.

We ask whether a spectrum can be *designed* rather than *inherited*. The
requirement is sharper than it first appears. It is not enough to find a
material whose relaxation time varies with composition; almost any alloy does
that. The elements of an array must also switch at the same field, or they
cannot share a drive line, and an array whose elements each need their own
drive voltage is not a reservoir but a collection of separately addressed
devices. The real requirement is therefore a material in which the relaxation
time can be moved over decades *while the coercive field stays put*.

Wurtzite quaternary Al(1−x−y)Ga(x)Sc(y)N offers exactly the two independent
axes this needs. Scandium content sets the coercive field [9, 11], because
switching nucleates in Sc-bearing unit cells; the Al:Ga ratio sets the
bandgap, and through it the leakage that drives depolarization, and so the
relaxation time. A combinatorial co-sputtered wafer with a lateral composition
gradient can therefore carry a designed distribution of time constants at a
single coercive field; combinatorial gradient deposition is already
established for AlScN [16] and, in the quaternary AlScBN, across 850 samples
of a single phase space [17]. Ferroelectricity has been demonstrated in
sputtered ScGaN [10, 11] and, as a quaternary, in MBE-grown Sc-Al-Ga-N [13];
what has not been examined is what the second composition axis is worth as a
design variable. Neither ternary can: with one composition axis, moving the
relaxation time necessarily drags the coercive field with it.

This paper makes that argument quantitative and then tests it honestly. We
first map the composition design space and show what the decoupling is worth,
measured the way a device engineer would measure it — decades of relaxation
time available inside a given coercive-field tolerance. We then simulate the
resulting pad array as a delay-based reservoir and ask what it computes.

The second half of the paper is as much about controls as about results,
because the controls turned out to change the conclusions. Three of them
deserve stating up front.

First, NARMA-10, the field's most-used benchmark, cannot carry this argument.
Its target is dominated by a linear function of the input history, so a plain
delay line — ridge regression on the raw inputs, no device at all — beats the
device on it. Selecting an operating point by NARMA error also drives the
input modulation toward zero, switching the device's nonlinearity off. We
report NARMA-10 beside that control rather than omitting the task, and use
delayed parity as the primary metric instead: no linear filter of the input
can exceed chance on it at any delay, unlike NARMA-10 [5], so a score above
chance is direct evidence that the device is computing rather than storing.

Second, driven open-loop the pad is not a reservoir at all. It is a
Hammerstein system — an instantaneous nonlinearity followed by a bank of
linear filters — and although it solves zero-delay parity perfectly, what it
retains at longer delays is weak and gone by the fourth. We show why this follows from the structure of
the switching equation, and that a delayed-feedback loop, which is one charge
amplifier summed into the drive, is what makes the dynamics recurrent [2]. The
usable loop gain spans about three quarters of a decade.

Third, the readout is severely ill-conditioned: the array produces far more
state columns than independent dynamical directions. Choosing the
regularization for single-device accuracy alone yields weights that are exact
on the device they were fitted to and meaningless on any other, so
cross-device transfer must be studied as a function of regularization or the
metric reports conditioning rather than reproducibility.

None of these three is specific to nitride ferroelectrics, and we suspect the
first two apply to a good deal of the physical-reservoir literature.

What we claim, in the end, is bounded and we state the bounds plainly. The
materials result stands on its own: the quaternary buys orders of magnitude
more usable time-constant range at fixed coercive field than any ternary, and
that is a design rule for anyone building an array of nitride ferroelectric
elements. The computational result is real but modest: the designed spectrum
measurably raises nonlinear memory over one time constant per pad at matched
readout channels, and the deterministic spread matches a random one in
performance while beating it in device-to-device reproducibility, which was
the point. We do not claim to approach a tuned software reservoir; a matched
echo state network [3] reaches three to four times the nonlinear memory capacity,
and the case for the device is energy and area at the sensor, not accuracy
parity. Finally, everything here is simulated, from a phenomenological model
whose calibration anchors we state individually, and the experiment that would
test it is described in the discussion together with the measurement precision
it would require.
