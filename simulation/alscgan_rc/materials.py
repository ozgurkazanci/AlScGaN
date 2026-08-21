"""Composition -> property maps for wurtzite Al(1-x-y)Ga(x)Sc(y)N.

A phenomenological, explicitly calibrated material model. Every map is a
smooth analytic function of the cation fractions (x = Ga, y = Sc) so that a
lateral composition spread can be evaluated segment by segment, and every
constant is traceable to a stated anchor or declared as a fitted effective
parameter.

The model is deliberately packaged as a class rather than module globals so
that sensitivity analyses (bandgap bowing, shifted anchors, temperature) are
performed by instantiating an alternative model, not by editing constants.

Calibration anchors
-------------------
Coercive field (Sc-dominated, weak Ga softening):
  A1  Al(0.73)Sc(0.27)N, sputtered      Ec = 4.7  MV/cm
      [Fichtner et al., J. Appl. Phys. 125, 114103 (2019); the reported
       range is ~4.5-5 MV/cm and is loop-frequency dependent.]
  A2  Sc(0.40)Ga(0.60)N, sputtered      Ec = 1.5  MV/cm
      [Uehara et al., APL Mater. 12, 121102 (2024) - AIST Kyushu, Tosu;
       lowest coercive field reported for a wurtzite ferroelectric.]

Retention / fading-memory time constant (bandgap -> leakage -> depolarization):
  A3  x = 0.10, y = 0.35 (Al-rich)      tau_ret = 1e3  s
  A4  x = 0.60, y = 0.35 (Ga-rich)      tau_ret = 1e-3 s
  A3/A4 are ASSUMED design targets, not measurements: they encode the
  qualitative, well-established ordering that wide-gap AlScN is effectively
  non-volatile on laboratory timescales while Ga-rich nitride ferroelectrics
  are leakage-limited and volatile. They fix the span of the accessible time
  constants; the paper's design principle depends on that span being large
  and monotone in x, not on the two endpoint values being exact.

Model form for retention
------------------------
  tau_ret(x, y, T) = TAU0 * exp( phi(x, y) / kT ),  phi = PHI0 + GAMMA * Eg

TAU0 is PINNED to 1e-13 s (an inverse phonon attempt time) so that the
temperature dependence is physically parameterized rather than an artifact of
an unconstrained prefactor fit. GAMMA (dimensionless, Poole-Frenkel-like
barrier-to-gap proportionality) and the offset PHI0 then follow from A3/A4.
PHI0 comes out negative (~ -0.2 eV); it is a phenomenological offset with no
microscopic claim attached. Temperature predictions are illustrative: they
assume the barrier itself is temperature independent.

Units: fields MV/cm, times s, energies eV, polarization uC/cm^2.
"""

import numpy as np

KB = 8.617333e-5          # eV/K
T_ROOM = 300.0            # K
KT_ROOM = KB * T_ROOM     # eV

# Binary end-member gaps (wurtzite; ScN value is an effective wurtzite-phase
# figure used only to interpolate the alloy trend).
EG_ALN, EG_GAN, EG_SCN = 6.2, 3.43, 2.0

# Static relative permittivity of the end members (c-axis, low frequency).
EPS_ALN, EPS_GAN, EPS_SCN = 9.0, 9.5, 20.0

ATTEMPT_TIME = 1.0e-13    # s, pinned prefactor TAU0


class MaterialModel:
    """Composition -> (Eg, Ec, tau_ret, Pr, eps_r) maps with explicit anchors.

    Parameters
    ----------
    bowing : tuple or None
        Pairwise bandgap bowing (b_AlGa, b_AlSc, b_GaSc) in eV. None (default)
        selects the linear virtual-crystal approximation used for the main
        results. The SI sensitivity analysis uses (0.9, 4.2, 3.0).
    ec_anchor_hi, ec_anchor_lo : (x, y, Ec)
        The two coercive-field anchors A1, A2.
    tau_anchor_hi, tau_anchor_lo : (x, y, tau)
        The two retention anchors A3, A4.
    ga_softening : float
        Fractional reduction of Ec at x = 1 (weak Ga cross-term).
    """

    def __init__(self,
                 bowing=None,
                 ec_anchor_hi=(0.00, 0.27, 4.7),
                 ec_anchor_lo=(0.60, 0.40, 1.5),
                 tau_anchor_hi=(0.10, 0.35, 1.0e3),
                 tau_anchor_lo=(0.60, 0.35, 1.0e-3),
                 ga_softening=0.12,
                 pr_base=115.0, pr_ga=25.0, pr_sc=60.0,
                 attempt_time=ATTEMPT_TIME):
        self.bowing = bowing
        self.ga_soft = float(ga_softening)
        self.pr_base, self.pr_ga, self.pr_sc = pr_base, pr_ga, pr_sc
        self.tau0 = float(attempt_time)
        self._calibrate_ec(ec_anchor_hi, ec_anchor_lo)
        self._calibrate_tau(tau_anchor_hi, tau_anchor_lo)

    # -- bandgap --------------------------------------------------------------
    def bandgap(self, x_ga, y_sc):
        """Alloy bandgap Eg(x, y) in eV."""
        x = np.asarray(x_ga, dtype=float)
        y = np.asarray(y_sc, dtype=float)
        a = 1.0 - x - y
        eg = a * EG_ALN + x * EG_GAN + y * EG_SCN
        if self.bowing is not None:
            b_alga, b_alsc, b_gasc = self.bowing
            eg = eg - b_alga * a * x - b_alsc * a * y - b_gasc * x * y
        return eg

    def permittivity(self, x_ga, y_sc):
        """Static relative permittivity (linear VCA)."""
        x = np.asarray(x_ga, dtype=float)
        y = np.asarray(y_sc, dtype=float)
        return (1.0 - x - y) * EPS_ALN + x * EPS_GAN + y * EPS_SCN

    # -- coercive field -------------------------------------------------------
    def _calibrate_ec(self, hi, lo):
        """Fit Ec(x, y) = (E0 + S*(y - y0)) * (1 - g*x) to the two anchors."""
        x1, y1, e1 = hi
        x2, y2, e2 = lo
        self.ec_y0 = y1
        # anchor A1 defines E0 at its own x through the softening factor
        self.ec_e0 = e1 / (1.0 - self.ga_soft * x1)
        base2 = e2 / (1.0 - self.ga_soft * x2)
        self.ec_slope = (base2 - self.ec_e0) / (y2 - y1)

    def coercive_field(self, x_ga, y_sc):
        """Ec(x, y) in MV/cm. Sc-dominated with a weak Ga softening term."""
        x = np.asarray(x_ga, dtype=float)
        y = np.asarray(y_sc, dtype=float)
        ec = (self.ec_e0 + self.ec_slope * (y - self.ec_y0)) * (1.0 - self.ga_soft * x)
        return ec

    def _iso_ec_raw(self, x_ga, ec_target):
        x = np.asarray(x_ga, dtype=float)
        base = ec_target / (1.0 - self.ga_soft * x)
        return self.ec_y0 + (base - self.ec_e0) / self.ec_slope

    def x_window(self, ec_target, x_max_search=0.90, n_grid=9001,
                 al_min=0.02, margin=1e-3):
        """Widest Ga interval on the iso-Ec trajectory that stays physical.

        Returns (x_lo, x_hi) such that 0.05 <= y <= 0.45 and the Al cation
        fraction stays above al_min throughout.
        """
        xs = np.linspace(0.0, x_max_search, n_grid)
        ys = self._iso_ec_raw(xs, ec_target)
        ok = (ys >= 0.05) & (ys <= 0.45) & (1.0 - xs - ys >= al_min)
        if not np.any(ok):
            raise ValueError(f"no physical iso-Ec trajectory at Ec = {ec_target}")
        valid = xs[ok]
        return float(valid.min() + margin), float(valid.max() - margin)

    def iso_ec_sc_fraction(self, x_ga, ec_target):
        """Sc fraction y(x) holding Ec = ec_target along a Ga sweep.

        Exact algebraic inverse of coercive_field, validated against the
        physical composition simplex.
        """
        x = np.asarray(x_ga, dtype=float)
        y = self._iso_ec_raw(x, ec_target)
        if np.any(y < 0.05) or np.any(y > 0.45):
            raise ValueError(
                f"iso-Ec trajectory leaves the calibrated Sc range 0.05-0.45 "
                f"(got {np.min(y):.3f}..{np.max(y):.3f}); choose another "
                f"ec_target or a narrower x window.")
        al = 1.0 - x - y
        if np.any(al < 0.02):
            raise ValueError(
                f"iso-Ec trajectory needs Al fraction {np.min(al):.3f} < 0.02; "
                f"reduce the upper Ga limit.")
        return y

    # -- retention ------------------------------------------------------------
    def _calibrate_tau(self, hi, lo):
        """Fit phi = PHI0 + GAMMA*Eg at pinned prefactor TAU0."""
        x1, y1, t1 = hi
        x2, y2, t2 = lo
        eg1, eg2 = float(self.bandgap(x1, y1)), float(self.bandgap(x2, y2))
        if abs(eg1 - eg2) < 1e-9:
            raise ValueError("retention anchors have equal bandgap")
        self.gamma = KT_ROOM * np.log(t1 / t2) / (eg1 - eg2)
        self.phi0 = KT_ROOM * np.log(t1 / self.tau0) - self.gamma * eg1

    def barrier(self, x_ga, y_sc):
        """Effective retention barrier phi(x, y) in eV."""
        return self.phi0 + self.gamma * self.bandgap(x_ga, y_sc)

    def tau_retention(self, x_ga, y_sc, temperature_k=T_ROOM):
        """Leakage-mediated depolarization time constant in s."""
        return self.tau0 * np.exp(self.barrier(x_ga, y_sc) / (KB * temperature_k))

    def x_for_tau(self, tau, ec_target, x_bounds=None,
                  temperature_k=T_ROOM, n_grid=20001):
        """Ga fraction giving tau_ret = tau on the iso-Ec trajectory.

        Solved on a dense monotone grid (log-tau is monotone decreasing in x
        for every calibration used here), then refined by linear interpolation
        in log-tau. Raises if the requested tau is outside the reachable range.
        """
        if x_bounds is None:
            x_bounds = self.x_window(ec_target)
        xs = np.linspace(x_bounds[0], x_bounds[1], n_grid)
        ys = self.iso_ec_sc_fraction(xs, ec_target)
        taus = self.tau_retention(xs, ys, temperature_k)
        lt = np.log10(taus)
        if not np.all(np.diff(lt) < 0):
            raise ValueError("log-tau is not monotone in x for this model")
        target = np.log10(tau)
        if target > lt[0] or target < lt[-1]:
            raise ValueError(
                f"tau = {tau:.3g} s outside reachable range "
                f"{10**lt[-1]:.3g}..{10**lt[0]:.3g} s at Ec = {ec_target}")
        return float(np.interp(target, lt[::-1], xs[::-1]))

    def tau_span_decades(self, x_lo, x_hi, ec_target, temperature_k=T_ROOM):
        """Decades of tau spanned by a Ga window on the iso-Ec trajectory."""
        xs = np.array([x_lo, x_hi], dtype=float)
        ys = self.iso_ec_sc_fraction(xs, ec_target)
        t = self.tau_retention(xs, ys, temperature_k)
        return float(abs(np.log10(t[1] / t[0])))

    # -- remanent polarization ------------------------------------------------
    def remanent_polarization(self, x_ga, y_sc):
        """Pr in uC/cm^2. Ad hoc linear map; see limitations."""
        x = np.asarray(x_ga, dtype=float)
        y = np.asarray(y_sc, dtype=float)
        return self.pr_base - self.pr_ga * x - self.pr_sc * (y - 0.25)

    def summary(self):
        return (f"MaterialModel(bowing={self.bowing}, "
                f"Ec: E0={self.ec_e0:.3f} MV/cm, S={self.ec_slope:.2f}/Sc, "
                f"g={self.ga_soft}; "
                f"tau: TAU0={self.tau0:.1e} s, GAMMA={self.gamma:.4f}, "
                f"PHI0={self.phi0:+.4f} eV)")


# Default model used for all main-text results.
DEFAULT = MaterialModel()

# Sensitivity model with pairwise bandgap bowing (SI).
BOWED = MaterialModel(bowing=(0.9, 4.2, 3.0))
