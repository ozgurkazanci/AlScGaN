"""Pad-array designs on a composition-spread wafer.

All designs below place P metal-ferroelectric-metal pads on the same
combinatorial wafer, driven by ONE shared line (identical field and identical
mask for every pad) and read out on P independent charge channels. The pads
therefore differ only in the composition they cover, which is the variable the
manuscript claims to be the design knob.

The four designs answer the question the paper is actually about - not
"does composition disorder help" but "at a fixed number of readout channels,
does a continuous time-constant spectrum inside each pad beat one time
constant per pad":

  graded       pad p spans the p-th sub-window of the wafer's Ga range, so
               each channel carries a continuum of time constants
  homogeneous  pad p sits at a single composition, the P compositions tiling
               the same Ga range: one time constant per channel, same total
               spectral coverage, same channel count
  uniform      every pad at the same composition (a single time constant for
               the whole array); the naive reference
  stochastic   pad p spans an i.i.d. random composition draw over the same
               window: matched spectrum statistics, no reproducibility

Every design is constrained to the same iso-Ec trajectory, so all pads share
one coercive field and can legitimately share one drive line. That constraint
is the reason the quaternary is needed: in a ternary alloy, moving composition
to change tau also moves Ec, and a shared drive line becomes impossible.
"""

import numpy as np

from .device import TAU_SW0, W_MERZ, SegmentedFilm
from .materials import DEFAULT as DEFAULT_MODEL
from .reservoir import MultiplexedReservoir

_EXP_CLAMP = 700.0


class PadArray:
    """P pads sharing one drive line, read out on P channels."""

    def __init__(self, films, label=""):
        self.films = list(films)
        self.label = label
        self.last_switched_charge = 0.0

    @property
    def n_pads(self):
        return len(self.films)

    def states(self, u, **reservoir_kw):
        """Concatenated state matrix (len(u) x P*M).

        All pads share the drive line, so their segments are advanced as one
        stacked ensemble and the per-pad observables are extracted with a
        single mat-vec per slot. This is numerically identical to stepping the
        pads separately (verified in validate.py) and several times faster.
        """
        films = self.films
        ec = np.concatenate([f.ec for f in films])
        tau = np.concatenate([f.tau_ret for f in films])
        sizes = [f.n for f in films]
        total = int(np.sum(sizes))

        # observable matrix: row p picks out pad p's area-weighted Pr
        obs = np.zeros((len(films), total))
        off = 0
        for p, f in enumerate(films):
            obs[p, off:off + f.n] = f.w * f.pr
            off += f.n

        # One shared drive line means one reference field for the whole array,
        # taken as the median coercive field over every segment of every pad.
        # Using pad 0 alone is harmless when the array is iso-Ec by
        # construction but silently wrong for a single-composition-axis
        # control, where the pads do not agree on Ec.
        ref = MultiplexedReservoir(films[0], **reservoir_kw)
        ref.ec_ref = float(np.median(ec))
        m, theta = ref.m, ref.theta
        charge = ref.readout == "charge"
        rest = ref.rest_slots

        # device noise, if any, is a property of the films and must be
        # reproduced here exactly as SegmentedFilm.step would apply it
        ec_jitter = float(films[0].ec_jitter)
        read_noise = float(films[0].read_noise)
        if any(f.ec_jitter != ec_jitter or f.read_noise != read_noise
               for f in films):
            raise ValueError("all pads must share the same noise settings")
        noise_rng = films[0].rng
        if (ec_jitter > 0 or read_noise > 0) and noise_rng is None:
            raise ValueError("noisy pads need an rng")

        # Every pad shares one drive line, so the field pattern is common.
        # Without feedback it depends only on the input and can be built once;
        # with feedback it depends on the measured charge one frame earlier and
        # has to be produced sample by sample.
        fb_gain = ref.feedback
        fb_delay = ref.feedback_delay
        if fb_gain:
            fields = None
            fb_hist = []
        else:
            fields = np.stack([ref.field_slots(uk) for uk in u])   # (N, M)

        r_rt = 1.0 / tau
        obs_total = obs.sum(axis=0)      # for array-wide switched charge
        p_state = np.zeros(total)
        out = np.empty((len(u), len(films) * m))
        n_obs = len(films)
        prev = obs @ p_state
        if read_noise > 0:
            prev = prev + noise_rng.normal(0.0, read_noise, n_obs)
        sign_cache = None if fb_gain else np.sign(fields)
        switched = 0.0
        with np.errstate(under="ignore"):
            for k in range(len(u)):
                row = out[k]
                if fb_gain:
                    # the loop carries the array-summed charge from fb_delay
                    # frames ago, i.e. one shared amplifier and summing node
                    src = fb_hist[-fb_delay] if len(fb_hist) >= fb_delay else 0.0
                    frame_fields = ref.field_slots(u[k], src)
                    frame_signs = np.sign(frame_fields)
                for j in range(m):
                    e = frame_fields[j] if fb_gain else fields[k, j]
                    if e != 0.0:
                        ec_eff = ec
                        if ec_jitter > 0.0:
                            ec_eff = np.maximum(
                                ec * (1.0 + noise_rng.normal(0.0, ec_jitter,
                                                             total)), 1e-6)
                        expo = np.minimum(W_MERZ * ec_eff / abs(e), _EXP_CLAMP)
                        r_sw = np.exp(-expo) / TAU_SW0
                        r = r_sw + r_rt
                        sgn = frame_signs[j] if fb_gain else sign_cache[k, j]
                        p_eq = sgn * r_sw / r
                    else:
                        r, p_eq = r_rt, 0.0
                    p_new = p_eq + (p_state - p_eq) * np.exp(-r * theta)
                    switched += float(obs_total @ np.abs(p_new - p_state))
                    p_state = p_new
                    now = obs @ p_state
                    if read_noise > 0:
                        now = now + noise_rng.normal(0.0, read_noise, n_obs)
                    row[j::m] = (now - prev) if charge else now
                    prev = now
                for _ in range(rest):
                    p_new = p_state * np.exp(-r_rt * theta)
                    switched += float(obs_total @ np.abs(p_new - p_state))
                    p_state = p_new
                    prev = obs @ p_state
                    if read_noise > 0:
                        prev = prev + noise_rng.normal(0.0, read_noise, n_obs)
                if fb_gain:
                    fb_hist.append(float(row.sum()))
        self.last_switched_charge = switched
        return out

    def states_reference(self, u, **reservoir_kw):
        """Slow path: step each pad independently (used to verify states())."""
        return np.hstack([MultiplexedReservoir(f, **reservoir_kw).states(u)
                          for f in self.films])

    def tau_pool(self):
        return np.concatenate([f.tau_ret for f in self.films])

    def describe(self):
        t = self.tau_pool()
        return (f"{self.label}: P={self.n_pads}, "
                f"segments/pad={self.films[0].n}, "
                f"tau {t.min():.3g}-{t.max():.3g} s "
                f"({np.log10(t.max()/t.min()):.2f} dec), "
                f"distinct tau = {len(np.unique(np.round(np.log10(t), 6)))}")

    def switched_charge(self):
        return sum(f.switched_charge for f in self.films)


# --- design constructors --------------------------------------------------------
def _edges(tau_lo, tau_hi, n_pads):
    return np.logspace(np.log10(tau_lo), np.log10(tau_hi), n_pads + 1)


def graded_array(n_pads, tau_lo, tau_hi, ec_target, n_seg=16,
                 model=None, **film_kw):
    m = model or DEFAULT_MODEL
    e = _edges(tau_lo, tau_hi, n_pads)
    films = []
    for i in range(n_pads):
        x_hi = m.x_for_tau(e[i], ec_target)       # tau falls as x rises
        x_lo = m.x_for_tau(e[i + 1], ec_target)
        films.append(SegmentedFilm.graded_iso_ec(
            n_seg, min(x_lo, x_hi), max(x_lo, x_hi), ec_target, model=m,
            **film_kw))
    return PadArray(films, "graded")


def homogeneous_array(n_pads, tau_lo, tau_hi, ec_target, n_seg=16,
                      model=None, **film_kw):
    """P single-composition pads whose time constants tile the same span."""
    m = model or DEFAULT_MODEL
    e = _edges(tau_lo, tau_hi, n_pads)
    centers = np.sqrt(e[:-1] * e[1:])             # geometric centre per window
    films = [SegmentedFilm.uniform(n_seg, m.x_for_tau(t, ec_target),
                                   ec_target, model=m, **film_kw)
             for t in centers]
    return PadArray(films, "homogeneous")


def uniform_array(n_pads, tau, ec_target, n_seg=16, model=None, **film_kw):
    m = model or DEFAULT_MODEL
    x = m.x_for_tau(tau, ec_target)
    films = [SegmentedFilm.uniform(n_seg, x, ec_target, model=m, **film_kw)
             for _ in range(n_pads)]
    return PadArray(films, "uniform")


def stochastic_array(n_pads, tau_lo, tau_hi, ec_target, rng, n_seg=16,
                     model=None, **film_kw):
    m = model or DEFAULT_MODEL
    x_a = m.x_for_tau(tau_hi, ec_target)
    x_b = m.x_for_tau(tau_lo, ec_target)
    x_from, x_to = min(x_a, x_b), max(x_a, x_b)
    films = [SegmentedFilm.stochastic_iso_ec(n_seg, x_from, x_to, ec_target,
                                             rng, model=m, **film_kw)
             for _ in range(n_pads)]
    return PadArray(films, "stochastic")


def with_composition_noise(array, sigma, rng):
    """Copy of a design with per-pad deposition noise applied."""
    return PadArray([f.with_composition_noise(sigma, rng) for f in array.films],
                    array.label)


def ternary_array(n_pads, tau_lo, tau_hi, n_seg=16, model=None,
                  al_fixed=0.02, **film_kw):
    """The control the materials claim rests on: a single-composition-axis array.

    Composition moves along one axis only (Al pinned at its floor, Sc traded
    against Ga - a ScGaN-like alloy), so spreading the time constants
    necessarily spreads the coercive field too. Every pad still shares one
    drive line, because that is the point: the array is driven at one field
    and the pads no longer agree on what that field means. Pads whose Ec has
    risen above the drive never switch; pads whose Ec has fallen below it
    saturate.

    This is what the quaternary exists to avoid, and comparing it against
    graded_array at the same drive is the computational statement of the
    decoupling result.
    """
    m = model or DEFAULT_MODEL
    lo, hi = min(tau_lo, tau_hi), max(tau_lo, tau_hi)
    targets = np.logspace(np.log10(lo), np.log10(hi), n_pads)

    # invert tau along the single axis: y is the only free variable
    ys = np.linspace(0.12, 0.45, 4001)
    xs = 1.0 - ys - al_fixed
    taus = m.tau_retention(xs, ys)
    order = np.argsort(taus)
    y_of_tau = np.interp(np.log10(targets), np.log10(taus[order]), ys[order])

    films = []
    for y in y_of_tau:
        yy = np.full(n_seg, float(y))
        xx = np.full(n_seg, 1.0 - float(y) - al_fixed)
        films.append(SegmentedFilm(xx, yy, model=m, **film_kw))
    return PadArray(films, "ternary")


def interleaved_array(n_pads, tau_lo, tau_hi, ec_target, n_seg=16,
                      model=None, **film_kw):
    """Deterministic design in which every pad spans the FULL window.

    graded_array partitions the spectrum, giving each channel a narrow
    sub-window: total coverage is complete but each channel is specialised.
    stochastic_array instead lets every pad sample the whole window, buying
    cross-channel diversity without giving up per-channel coverage - which is
    why it overtakes the partitioned design once channels are plentiful.

    Repeating one full-window pad P times gains nothing, because the model is
    invariant to segment ordering and identical pads produce identical states.
    Interleaving is the deterministic way to get both properties: pad p
    carries a comb spanning the whole window, offset by p/(P*N) of a comb
    period from its neighbours, so every channel sees the full spectrum and no
    two channels see the same time constants.

    RESULT: it does not help. Measured against the partitioned design it is
    3-5% worse at every channel count tested. The interpretation is that
    channel DECORRELATION matters more than per-channel coverage: when every
    pad spans the same broad spectrum their summed responses resemble one
    another, whereas partitioning specialises each channel and decorrelates
    them. The function is kept because the negative result is worth reporting -
    partitioning is not an arbitrary choice among equivalent tilings.
    """
    m = model or DEFAULT_MODEL
    lo, hi = min(tau_lo, tau_hi), max(tau_lo, tau_hi)
    step = (np.log10(hi) - np.log10(lo)) / (n_seg * n_pads)
    films = []
    for p in range(n_pads):
        exps = (np.log10(lo) + p * step
                + np.arange(n_seg) * step * n_pads)
        films.append(SegmentedFilm.tau_ladder(10 ** exps, ec_target, model=m,
                                              **film_kw))
    return PadArray(films, "interleaved")
