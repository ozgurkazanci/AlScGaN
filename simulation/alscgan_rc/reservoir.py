"""Time-multiplexed physical reservoir on a composition-spread pad.

Delay-based (single physical node) reservoir computing. Each input sample u(k)
is expanded by a fixed binary mask into M virtual-node slots of duration theta.
The field applied in slot j of sample k is bipolar,

    E(k, j) = Ec_ref * m_j * (bias + gain * u(k)),   m_j in {-1, +1}

so the pad is driven around, and normally below, its switching threshold in
both directions. The Merz exponential supplies the nonlinearity; the competition
between partial switching and leakage-mediated relaxation supplies fading
memory, with a per-segment time constant set by composition.

Readout. The default observable is the per-slot switched charge dP, i.e. the
current integrated over a slot, which is what a charge amplifier on an MFM pad
actually delivers. Absolute polarization is available for comparison.

Operating regime. The drive must be chosen so that forgetting is performed by
leakage relaxation, not by field overwrite. If |E| approaches Ec in every slot,
the switching rate dominates every segment's relaxation rate, all segments are
driven to the same saturated state within one slot, and the engineered time
constants become dynamically invisible. The experiment scripts select the drive
by search and report the resulting switching rate so this regime check is
explicit rather than assumed.
"""

import numpy as np


class MultiplexedReservoir:
    """Delay-based reservoir driving one composition-spread pad.

    Mask schemes (`scheme`)
    -----------------------
    "polarity"  E = Ec_ref * m_j * (bias + gain*u),  m_j in {-1,+1}
        The mask only flips drive polarity, so every virtual node has the same
        transfer function and the state matrix collapses toward rank one.
        Retained as the naive reference.
    "bias"      E = Ec_ref * s_j * (bias*(1 + spread*m_j) + gain*u)
        Polarity alternates regularly (s_j = (-1)^j, keeping the pad charge
        balanced), while the mask offsets each slot's operating point along
        the Merz exponential. Every virtual node then sits at a different
        distance from threshold and responds to u with a different gain and
        curvature - the physical analogue of per-neuron biases.
    "input"     E = Ec_ref * s_j * (bias + gain*m_j*u)
        Regular polarity with the mask applied to the input coupling only.

    m_j is drawn once (fixed hardware) from a uniform distribution on [-1, 1],
    optionally quantized to `mask_levels` values to reflect a realistic
    arbitrary-waveform generator.
    """

    def __init__(self, film, n_virtual=50, theta=5e-3,
                 bias=0.55, gain=0.15, mask_seed=12345, readout="charge",
                 rest_slots=0, scheme="bias", mask_spread=0.25,
                 mask_levels=0, feedback=0.0, feedback_delay=1):
        self.film = film
        self.m = int(n_virtual)
        self.theta = float(theta)
        self.bias = float(bias)
        self.gain = float(gain)
        self.readout = readout           # "charge" (per-slot dP) | "polarization"
        self.rest_slots = int(rest_slots)  # zero-field slots between samples
        self.scheme = scheme
        self.mask_spread = float(mask_spread)
        # Delayed feedback closes the loop around the pad: the charge measured
        # one frame earlier is summed into the drive, which is what turns a
        # feed-forward filter bank into a recurrent system.
        self.feedback = float(feedback)
        self.feedback_delay = int(feedback_delay)
        rng = np.random.default_rng(mask_seed)   # the mask is fixed hardware
        if scheme == "polarity":
            self.mask = rng.choice([-1.0, 1.0], size=self.m)
        else:
            self.mask = rng.uniform(-1.0, 1.0, self.m)
            if mask_levels and mask_levels > 1:
                edges = np.linspace(-1.0, 1.0, mask_levels)
                self.mask = edges[np.argmin(
                    np.abs(self.mask[:, None] - edges[None, :]), axis=1)]
        self.polarity = np.where(np.arange(self.m) % 2 == 0, 1.0, -1.0)
        self.ec_ref = float(np.median(film.ec))

    def field_slots(self, uk, fb=0.0):
        if self.feedback and fb:
            uk = uk + self.feedback * fb
        if self.scheme == "polarity":
            return self.ec_ref * self.mask * (self.bias + self.gain * uk)
        if self.scheme == "input":
            return self.ec_ref * self.polarity * (self.bias
                                                  + self.gain * self.mask * uk)
        # "bias": heterogeneous operating points
        return self.ec_ref * self.polarity * (
            self.bias * (1.0 + self.mask_spread * self.mask) + self.gain * uk)

    def states(self, u):
        """State matrix X (len(u) x M) for the input sequence u."""
        self.film.reset(0.0)
        x = np.empty((len(u), self.m))
        p_prev = self.film.polarization()
        charge = self.readout == "charge"
        for k, uk in enumerate(u):
            for j, e in enumerate(self.field_slots(uk)):
                p_now = self.film.step(e, self.theta)
                x[k, j] = (p_now - p_prev) if charge else p_now
                p_prev = p_now
            for _ in range(self.rest_slots):
                p_prev = self.film.step(0.0, self.theta)
        return x

    # -- regime diagnostics ----------------------------------------------------
    def switching_rate(self, u_mean=0.25):
        """Per-segment Merz switching rate at the mean drive level (1/s)."""
        from .device import TAU_SW0, W_MERZ
        e = float(np.mean(np.abs(self.field_slots(u_mean))))
        return np.exp(-W_MERZ * self.film.ec / e) / TAU_SW0

    def regime_report(self, u_mean=0.25):
        """Compare switching and relaxation rates: which one does the forgetting."""
        r_sw = self.switching_rate(u_mean)
        r_rt = 1.0 / self.film.tau_ret
        return {
            "r_sw_median": float(np.median(r_sw)),
            "r_rt_min": float(r_rt.min()),
            "r_rt_max": float(r_rt.max()),
            "switch_per_sample": float(np.median(r_sw) * self.m * self.theta),
            "leakage_dominated_fraction": float(np.mean(r_rt > r_sw)),
        }


class EchoStateNetwork:
    """Leaky ESN baseline with a bias input, as in the canonical formulation."""

    def __init__(self, n_nodes=50, spectral_radius=0.9, leak=0.3,
                 input_scale=1.0, bias_scale=0.2, seed=7):
        rng = np.random.default_rng(seed)
        w = rng.normal(0, 1, (n_nodes, n_nodes))
        eig = np.max(np.abs(np.linalg.eigvals(w)))
        self.w = w * (spectral_radius / eig)
        self.w_in = rng.uniform(-input_scale, input_scale, n_nodes)
        self.w_bias = rng.uniform(-bias_scale, bias_scale, n_nodes)
        self.leak = float(leak)
        self.n = int(n_nodes)

    def states(self, u):
        x = np.zeros(self.n)
        out = np.empty((len(u), self.n))
        for k, uk in enumerate(u):
            pre = self.w @ x + self.w_in * uk + self.w_bias
            x = (1 - self.leak) * x + self.leak * np.tanh(pre)
            out[k] = x
        return out


# --- linear readout -----------------------------------------------------------
LAM_GRID = (1e-6, 1e-4, 1e-2, 1e0, 1e2)


def standardizer(x_train):
    """Column z-score transform fitted on training states only."""
    mu = x_train.mean(axis=0)
    sd = x_train.std(axis=0)
    # absolute AND relative floors: a column carrying essentially no variance
    # must not be amplified into a dominant feature
    floor = max(1e-12, 1e-9 * float(sd.max())) if sd.size else 1e-12
    sd = np.where(sd < floor, 1.0, sd)
    return lambda x: (x - mu) / sd


def ridge_fit(x_train, y_train, lam=1e-4):
    """Ridge regression with an UNPENALIZED intercept column."""
    a = np.hstack([x_train, np.ones((len(x_train), 1))])
    pen = lam * np.eye(a.shape[1])
    pen[-1, -1] = 0.0
    return np.linalg.solve(a.T @ a + pen, a.T @ y_train)


def ridge_predict(x, w):
    return np.hstack([x, np.ones((len(x), 1))]) @ w


def _split(x, y, n_washout, n_train):
    xw, yw = x[n_washout:], y[n_washout:]
    return xw[:n_train], yw[:n_train], xw[n_train:], yw[n_train:]


def select_lambda(xt, yt, lam_grid=LAM_GRID, val_frac=0.2):
    """Choose lambda on a held-out tail of the training window (no test data)."""
    n_val = max(1, int(val_frac * len(xt)))
    x_fit, y_fit = xt[:-n_val], yt[:-n_val]
    x_val, y_val = xt[-n_val:], yt[-n_val:]
    z = standardizer(x_fit)
    best_lam, best_err = lam_grid[0], np.inf
    for lam in lam_grid:
        w = ridge_fit(z(x_fit), y_fit, lam)
        err = _nrmse(y_val, ridge_predict(z(x_val), w))
        if err < best_err:
            best_lam, best_err = lam, err
    return best_lam


def fit_eval(x, y, n_washout, n_train, lam_grid=LAM_GRID, return_model=False):
    """Washout / train / test evaluation with leakage-free lambda selection."""
    xt, yt, xs, ys = _split(x, y, n_washout, n_train)
    lam = select_lambda(xt, yt, lam_grid)
    z = standardizer(xt)
    w = ridge_fit(z(xt), yt, lam)
    y_hat = ridge_predict(z(xs), w)
    err = _nrmse(ys, y_hat)
    if return_model:
        return err, y_hat, ys, (z, w, lam)
    return err, y_hat, ys


def apply_model(x, y, n_washout, n_train, model):
    """Strict cross-device transfer: ship the normalization AND the weights.

    Nothing about the target device is measured. This is the harshest test and
    is dominated by per-channel DC offsets, which composition changes move by
    many times a channel own input-driven variation.
    """
    _, _, xs, ys = _split(x, y, n_washout, n_train)
    z, w, _ = model
    return _nrmse(ys, ridge_predict(z(xs), w))


def apply_model_calibrated(x, y, n_washout, n_train, model):
    """Cross-device transfer after label-free per-channel calibration.

    The target device re-estimates its own per-column mean and scale by simply
    running the input and recording statistics - no labels, no retraining -
    and then applies the SHARED ridge weights. This isolates the question the
    manuscript actually asks: do two devices implement the same nonlinear
    filter bank, up to a per-channel affine normalization? It is also what any
    real system would do, since the calibration costs one unlabelled run.
    """
    xt, _, xs, ys = _split(x, y, n_washout, n_train)
    _, w, _ = model
    z_local = standardizer(xt)
    return _nrmse(ys, ridge_predict(z_local(xs), w))


def _nrmse(y, y_hat):
    var = np.var(y)
    if var <= 0:
        return np.nan
    return float(np.sqrt(np.mean((y - y_hat) ** 2) / var))
