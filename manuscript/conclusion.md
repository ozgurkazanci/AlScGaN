# Conclusion

A wurtzite quaternary nitride can carry a designed distribution of relaxation
times at a single coercive field, and that combination — not either property
alone — is what an array of physical reservoir elements needs. Quantified as
decades of relaxation time reachable inside a coercive-field tolerance, the
figure of merit we propose for this class of material, Al–Sc–Ga–N delivers 7.43
decades at zero tolerance against 0.196 and 0.072 decades for its ternary
parents at ±5%. That result stands on the composition–property model alone and
is independent of everything we then do with it.

Simulating the resulting composition-spread pad array as a delay-based
reservoir places three bounds on what such a device can be expected to do, and
we regard the bounds as the more useful half of the paper.

The advantage of a designed spectrum is a scarce-channel advantage. It is 11.7%
in nonlinear memory capacity over one time constant per pad at two readout
channels, and it has reversed by eight. Since each channel is a charge
amplifier and a converter, the regime where the spectrum pays is the regime a
physical implementation occupies — but the claim must not be carried to large
arrays.

The device is not a reservoir until a loop is closed around it. Driven
open-loop it is a Hammerstein system: an instantaneous nonlinearity followed by
a bank of linear filters, whose nonlinear memory is shallow enough to be gone
by the fourth delay and whose open-loop capacity is dominated by the zero-delay
term. A delayed-feedback loop raises the capacity from 1.33 to 3.10, within a
usable gain window about three quarters of a decade wide. Any experimental attempt needs a
trimmable loop gain, and the trim range matters more than its absolute
accuracy.

The binding requirement is readout precision, not materials quality. Because
the array produces far more state columns than independent dynamical
directions, the trained readout leans on small signals: below roughly 90 dB of
readout signal-to-noise ratio the composition-spread advantage is not
resolvable at all. Together with a deposition tolerance of ±1 at% - against a
measured run-to-run reproducibility of 0.1 to 0.7 at.% for co-sputtered
composition spreads [27] - and the loop gain window, this is the specification
an experiment would have to meet, and it should be budgeted before fabrication
rather than discovered after.

Finally, the width of the spectrum earns its keep somewhere other than where we
expected. At fixed temperature one decade suffices; five add nothing. What the
extra decades buy is immunity to the fact that the whole spectrum moves with
ambient temperature — one decade per 25 K at mid-window, and compressing as it
moves, from one decade per 19 K at the slow end to one per 33 K at the fast —
so that over 275–325 K a
single-time-constant array loses 36.6% of its capacity where the spread array
loses 2.4%. A ternary alloy can partly substitute coercive-field disorder for
designed time-constant disorder and reach 86% of the quaternary's capacity at
one temperature, but it loses 22.9% across the same range. The quaternary is
not a better ferroelectric than either parent; it is the smallest system in
which the two properties come apart, and that is the claim we make for it.

We do not claim parity with software. A tuned echo state network at matched
readout dimension reaches three to four times the nonlinear memory capacity, and
the case for a device of this kind rests on energy and area at the point of
measurement. Nothing here has been grown or measured, and the experiment that
would test it is specified above.
