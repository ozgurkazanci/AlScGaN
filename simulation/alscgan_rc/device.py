"""Segment-ensemble dynamical model of a composition-spread Al-Sc-Ga-N pad.

Geometry (this choice is load-bearing; see the note below)
----------------------------------------------------------
A combinatorial co-sputtered wafer carries a LATERAL composition gradient.
One metal-ferroelectric-metal pad deposited on such a wafer therefore covers a
strip of compositions side by side, NOT stacked along the growth axis. The pad
is modelled as N parallel segments sharing the same top and bottom electrode:

  * every segment sees exactly the same field E = V/d (same electrode pair,
    same film thickness) - the uniform-field assumption is EXACT here, not an
    approximation, whereas in a growth-axis graded stack it would require a
    series field-division argument;
  * segments are electrostatically independent up to in-plane fringing at
    their mutual boundaries. On a combinatorial wafer the composition varies
    over millimetres while the film is ~100 nm thick, so the boundary region
    is ~1e-4 of the pad area;
  * the measured charge is exactly the area-weighted sum of the segment
    polarizations, which is what the observable below computes.

A direct consequence, which must be stated in the manuscript rather than left
implicit: the model depends only on the MULTISET of segment properties
{(w_i, Ec_i, tau_i, Pr_i)}, i.e. on the time-constant spectrum. It is exactly
invariant to the spatial ordering of the segments and to the direction of the
gradient. "Graded" here means "designed tau spectrum", nothing more.

Dynamics
--------
Each segment carries a normalized polarization p_i in [-1, 1]. Under a
piecewise-constant field E(t) two processes compete:

  switching   Merz-law field-activated reversal toward sign(E),
              r_sw = exp(-W * Ec_i / |E|) / TAU_SW0
  relaxation  leakage-mediated depolarization toward p = 0,
              r_rt = 1 / tau_ret,i

so that

  dp/dt = (sign(E) - p) * r_sw - p * r_rt

Within a constant-field slot this is linear in p, so the update is the exact
solution, unconditionally stable and step-size exact:

  p_eq = sign(E) * r_sw / (r_sw + r_rt)
  p   <- p_eq + (p - p_eq) * exp(-(r_sw + r_rt) * dt)

Three modelling choices this encodes, all deliberate:
  1. The depolarization channel stays active while the field is applied, so
     the sustained-field steady state is |p_eq| = r_sw/(r_sw + r_rt) < 1:
     leaky segments pole incompletely. This is leaky-ferroelectric
     phenomenology, and it is the mechanism by which the tau spectrum enters
     the response.
  2. Switching within one segment is a single exponential (the n = 1 KAI
     limit): no nucleation-limited-switching time dispersion inside a segment.
     Dispersion across the pad is supplied by the composition spread itself.
  3. W = ln(TAU_SW_AT_EC / TAU_SW0) = ln(1e-3/1e-9) = 13.8 DEFINES Ec as the
     field that switches a segment in 1 ms, i.e. a kHz-loop coercive field,
     consistent with the loop-measured calibration anchors. Merz-law Ec is
     frequency dependent, so this convention must be quoted with any Ec value.
  tau_sw carries no temperature dependence in this model while tau_ret does.
"""

import numpy as np

from .materials import DEFAULT as DEFAULT_MODEL
from .materials import T_ROOM

TAU_SW0 = 1.0e-9          # s, attempt-limited switching floor
TAU_SW_AT_EC = 1.0e-3     # s, switching time at |E| = Ec (defines Ec)
W_MERZ = float(np.log(TAU_SW_AT_EC / TAU_SW0))    # 13.8158
_EXP_CLAMP = 700.0        # keeps exp() inside double range

AL_MIN = 0.02             # minimum Al cation fraction kept physical


class SegmentedFilm:
    """Parallel bank of ferroelectric segments with per-segment properties.

    Parameters
    ----------
    x_ga, y_sc : array_like
        Cation fractions per segment (broadcast against each other).
    weights : array_like or None
        Area fractions; defaults to equal areas.
    model : MaterialModel
    temperature_k : float
    read_noise : float
        Standard deviation of additive noise on the polarization observable,
        in uC/cm^2. Zero (default) reproduces the noiseless model exactly.
    ec_jitter : float
        Relative standard deviation of cycle-to-cycle coercive-field
        fluctuation, redrawn per call to step(). Zero (default) is noiseless.
    rng : numpy Generator or None
        Required if read_noise or ec_jitter is nonzero.
    """

    def __init__(self, x_ga, y_sc, weights=None, model=None,
                 temperature_k=T_ROOM, read_noise=0.0, ec_jitter=0.0,
                 rng=None):
        self.model = model if model is not None else DEFAULT_MODEL
        x, y = np.broadcast_arrays(np.asarray(x_ga, dtype=float),
                                   np.asarray(y_sc, dtype=float))
        x = np.atleast_1d(x).astype(float).copy()
        y = np.atleast_1d(y).astype(float).copy()
        _check_simplex(x, y)
        self.x_ga, self.y_sc = x, y
        self.n = x.size
        self.temperature_k = float(temperature_k)
        self.ec = np.asarray(self.model.coercive_field(x, y), dtype=float)
        self.tau_ret = np.asarray(
            self.model.tau_retention(x, y, self.temperature_k), dtype=float)
        self.pr = np.asarray(self.model.remanent_polarization(x, y), dtype=float)
        if weights is None:
            weights = np.full(self.n, 1.0 / self.n)
        w = np.asarray(weights, dtype=float)
        self.w = w / w.sum()
        self.read_noise = float(read_noise)
        self.ec_jitter = float(ec_jitter)
        if (self.read_noise > 0 or self.ec_jitter > 0) and rng is None:
            raise ValueError("rng is required when noise is enabled")
        self.rng = rng
        self.p = np.zeros(self.n)
        self.switched_charge = 0.0   # accumulated |dP| in uC/cm^2

    # -- construction helpers -------------------------------------------------
    @classmethod
    def graded_iso_ec(cls, n_seg, x_from, x_to, ec_target, model=None, **kw):
        """Linear Ga spread x_from -> x_to with Sc co-varied to hold Ec."""
        m = model if model is not None else DEFAULT_MODEL
        x = np.linspace(x_from, x_to, n_seg)
        return cls(x, m.iso_ec_sc_fraction(x, ec_target), model=m, **kw)

    @classmethod
    def uniform(cls, n_seg, x_ga, ec_target, model=None, **kw):
        """Homogeneous pad at one composition on the iso-Ec trajectory."""
        m = model if model is not None else DEFAULT_MODEL
        x = np.full(n_seg, float(x_ga))
        return cls(x, m.iso_ec_sc_fraction(x, ec_target), model=m, **kw)

    @classmethod
    def tau_ladder(cls, taus, ec_target, model=None, temperature_k=T_ROOM, **kw):
        """Pad built from an explicit list of target time constants.

        Used for the discrete 2-tau / 3-tau controls that quantify how much
        spectral coverage the continuous spread actually buys.
        """
        m = model if model is not None else DEFAULT_MODEL
        x = np.array([m.x_for_tau(t, ec_target, temperature_k=temperature_k)
                      for t in np.atleast_1d(taus)], dtype=float)
        return cls(x, m.iso_ec_sc_fraction(x, ec_target), model=m,
                   temperature_k=temperature_k, **kw)

    @classmethod
    def stochastic_iso_ec(cls, n_seg, x_from, x_to, ec_target, rng,
                          model=None, **kw):
        """Stochastic-disorder control: same window and iso-Ec constraint.

        x is drawn i.i.d. uniform instead of stratified, so this pad differs
        from graded_iso_ec ONLY in how the tau spectrum is sampled - the
        contrast the manuscript actually claims.
        """
        m = model if model is not None else DEFAULT_MODEL
        x = rng.uniform(x_from, x_to, n_seg)
        return cls(x, m.iso_ec_sc_fraction(x, ec_target), model=m, **kw)

    def with_composition_noise(self, sigma_ga, rng, sigma_sc=None):
        """Copy with independent composition noise on both cation fractions.

        Represents run-to-run and pad-to-pad deposition variation. The simplex
        constraint x + y <= 1 - AL_MIN is enforced after the draw, so no
        unphysical composition ever reaches the material maps.
        """
        s_sc = sigma_ga if sigma_sc is None else sigma_sc
        x = np.clip(self.x_ga + rng.normal(0.0, sigma_ga, self.n), 0.0, 0.90)
        y = np.clip(self.y_sc + rng.normal(0.0, s_sc, self.n), 0.05, 0.45)
        over = x + y > 1.0 - AL_MIN
        if np.any(over):
            scale = (1.0 - AL_MIN) / (x[over] + y[over])
            x[over] *= scale
            y[over] *= scale
        return SegmentedFilm(x, y, self.w, model=self.model,
                             temperature_k=self.temperature_k,
                             read_noise=self.read_noise,
                             ec_jitter=self.ec_jitter, rng=rng)

    def at_temperature(self, temperature_k):
        """Copy of this pad evaluated at another temperature."""
        return SegmentedFilm(self.x_ga, self.y_sc, self.w, model=self.model,
                             temperature_k=temperature_k,
                             read_noise=self.read_noise,
                             ec_jitter=self.ec_jitter, rng=self.rng)

    # -- dynamics --------------------------------------------------------------
    def reset(self, p0=0.0):
        self.p = np.full(self.n, float(p0))
        self.switched_charge = 0.0

    def step(self, e_field, dt):
        """Advance every segment by dt under constant field e_field (MV/cm)."""
        e = float(e_field)
        p_before = self.p
        r_rt = 1.0 / self.tau_ret
        with np.errstate(under="ignore"):
            if e != 0.0:
                ec = self.ec
                if self.ec_jitter > 0.0:
                    ec = ec * (1.0 + self.rng.normal(0.0, self.ec_jitter, self.n))
                    ec = np.maximum(ec, 1e-6)
                expo = np.minimum(W_MERZ * ec / abs(e), _EXP_CLAMP)
                r_sw = np.exp(-expo) / TAU_SW0
                r = r_sw + r_rt
                p_eq = np.sign(e) * r_sw / r
            else:
                r = r_rt
                p_eq = 0.0
            self.p = p_eq + (p_before - p_eq) * np.exp(-r * dt)
            self.switched_charge += float(
                np.sum(self.w * self.pr * np.abs(self.p - p_before)))
        return self.polarization()

    def polarization(self):
        """Area-averaged polarization in uC/cm^2 (the measured observable)."""
        p = float(np.sum(self.w * self.pr * self.p))
        if self.read_noise > 0.0:
            p += float(self.rng.normal(0.0, self.read_noise))
        return p

    def run(self, e_series, dt):
        """Apply a sequence of constant-field slots; return P after each."""
        out = np.empty(len(e_series))
        for k, e in enumerate(e_series):
            out[k] = self.step(e, dt)
        return out

    # -- reporting -------------------------------------------------------------
    def tau_decades(self):
        return float(np.log10(self.tau_ret.max() / self.tau_ret.min()))

    def describe(self):
        return (f"SegmentedFilm(n={self.n}, x={self.x_ga.min():.3f}"
                f"-{self.x_ga.max():.3f}, y={self.y_sc.min():.3f}"
                f"-{self.y_sc.max():.3f}, Ec={self.ec.min():.3f}"
                f"-{self.ec.max():.3f} MV/cm, tau={self.tau_ret.min():.3g}"
                f"-{self.tau_ret.max():.3g} s [{self.tau_decades():.2f} dec], "
                f"T={self.temperature_k:.0f} K)")


def _check_simplex(x, y):
    if np.any(x < 0) or np.any(y < 0):
        raise ValueError("negative cation fraction")
    al = 1.0 - x - y
    if np.any(al < AL_MIN - 1e-12):
        raise ValueError(
            f"Al cation fraction {np.min(al):.4f} below the {AL_MIN} floor; "
            f"composition is outside the physical simplex")


def switching_energy_pj(film, area_um2, thickness_nm, e_amplitude_mv_cm):
    """Switching work for the charge accumulated so far, in pJ.

    W = V * dQ = (E * d) * (dP * A). With E in MV/cm, d in nm, dP in uC/cm^2
    and A in um^2. Only ferroelectric switching work is counted: displacement
    charging of the linear permittivity, leakage, and all peripheral circuitry
    (drive amplifier, sense amplifier, ADC) are excluded, so this is a
    device-level lower bound and must be quoted as such.
    """
    voltage = (e_amplitude_mv_cm * 1.0e8) * (thickness_nm * 1.0e-9)   # V
    charge = (film.switched_charge * 1.0e-2) * (area_um2 * 1.0e-12)   # C
    return voltage * charge * 1.0e12                                  # pJ
