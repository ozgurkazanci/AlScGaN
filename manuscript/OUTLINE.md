# Manuscript outline and argument

Working title: **Decoupling coercive field from relaxation time in wurtzite
Al–Sc–Ga–N: a designed time-constant spectrum for in-materio computing, and
the limits of what it computes**

Target: *Neuromorphic Computing and Engineering* or *APL Machine Learning*.
Article type: modelling / design study. All data are simulated; the
manuscript says so in the title block, the abstract, and the methods.

## The argument in one paragraph

In-materio reservoirs draw their computational richness from a broad
distribution of relaxation times, which in nanomaterial networks comes from
stochastic self-assembly and is therefore irreproducible. A quaternary
wurtzite ferroelectric offers two independent composition axes: Sc sets the
coercive field, the Al:Ga ratio sets the bandgap and hence the leakage that
governs the depolarization time constant. A composition-spread wafer can
therefore present a *designed* spectrum of time constants at a *single*
coercive field, so an array of pads can share one drive line — something no
ternary alloy permits. We quantify that decoupling, simulate the resulting
device, and then measure what it can and cannot compute, including the
controls that most physical-reservoir studies omit.

## Claims, in descending order of strength

**C1 (materials, strong).** At exactly constant Ec the quaternary spans 7.43
decades of relaxation time. Holding Ec to ±5% — the loosest tolerance under
which an array can still share a drive line — a ternary AlScN reaches 0.196
decades and ScGaN 0.072. The quaternary advantage is a factor of ~38 at ±5%
and unbounded at 0%. *Figure 1.* This claim is independent of everything
downstream and is publishable on its own.

**C2 (device).** A composition-spread pad shows multi-exponential retention
where a homogeneous pad shows single-exponential decay, and the drive must be
biased where leakage rather than field overwrite performs the forgetting, or
the engineered spectrum is dynamically invisible. *Figure 2a–d.*

**C3 (architecture).** Open-loop the pad is a Hammerstein system — an
instantaneous nonlinearity followed by a bank of linear filters — with no
nonlinear memory whatsoever. A delayed-feedback loop makes it recurrent, and
the usable loop gain is a narrow window. *Figure 2e.* This is a necessary
condition, not a detail.

**C4 (computation).** At matched readout channels, the designed spectrum
raises nonlinear memory capacity over one time constant per pad. Numbers from
`results/headline_summary.json`. *Figure 3.*

**C5 (reproducibility).** Under matched deposition noise the designed and
random spectra perform alike but differ in device-to-device variance and in
how well one trained readout transfers. The deposition tolerance at which the
two become indistinguishable is a fabrication budget. *Figure 4.*

**C6 (robustness).** The design rule survives bandgap bowing and ambient
temperature drift; the required spectral span and the required measurement
SNR are quoted. *Figure 5.*

## What the paper explicitly does NOT claim

- It does not claim to beat a tuned software reservoir. A tuned ESN of matched
  readout dimension reaches roughly three times the nonlinear memory capacity.
- It does not claim to beat a delay line on NARMA-10. It does not, and we show
  the control rather than omitting the task.
- It does not claim that gradient direction or spatial ordering matters. In
  the lateral geometry adopted here they provably do not.

## Section plan

1. **Introduction.** The time-constant-spectrum argument for in-materio
   computing; the reproducibility problem with stochastic disorder; why a
   quaternary nitride is the natural place to look; what this paper adds.
2. **Composition design space.** The material model, its anchors, and the
   decoupling result (C1). Ternary controls.
3. **Device model.** Lateral composition spread, parallel-segment formulation,
   Merz switching against leakage relaxation, the exact slot update. State the
   ordering invariance here, not in a footnote.
4. **Reservoir architecture.** Time multiplexing, the mask scheme, the
   delayed-feedback loop, the readout. State the regularization/transfer
   trade-off.
5. **Benchmarks and controls.** Why NARMA-10 cannot be the primary metric;
   the delay-line control; delayed parity as the discriminating task; how the
   operating points were selected on disjoint seeds.
6. **Results.** C2–C6 in order.
7. **Discussion.** The computational class of this device family; which task
   families fit; the energy and area argument; what an experiment would need
   (SNR, loop gain, deposition tolerance).
8. **Limitations.** No standalone section. The seventeen declared items are
   distributed as prose: modelling choices into Methods, negative results and
   controls into Results, interpretive caveats into the Discussion's "Honest
   limits". `LIMITATIONS.md` stays on disk as the internal checklist and
   `check_limitations_coverage.py` guards the distribution.
9. **Methods.** Model equations, calibration, statistics, code availability.

## Numbers to pull in when the runs finish

- `results/material_summary.json` — C1
- `results/device_summary.json` — C2, C3
- `results/headline_summary.json` — C4
- `results/reproducibility.json` — C5
- `results/robustness.json` — C6
- `results/controls.json` — the delay-line and nonlinearity controls
