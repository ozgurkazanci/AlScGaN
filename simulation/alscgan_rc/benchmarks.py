"""Temporal benchmark tasks: NARMA-N, memory capacity, parity, Mackey-Glass.

Standard definitions from the physical-reservoir-computing literature so that
numbers are comparable across platforms.
"""

import numpy as np

from .reservoir import (LAM_GRID, _nrmse, _split, apply_model, fit_eval,
                        ridge_fit, ridge_predict, select_lambda, standardizer)


# --- input generators ---------------------------------------------------------
def uniform_input(n, rng, lo=0.0, hi=0.5):
    return rng.uniform(lo, hi, n)


def narma_target(u, order=10):
    """NARMA-N driven by u in [0, 0.5] (Atiya-Parlos form)."""
    n = len(u)
    y = np.zeros(n)
    for k in range(order - 1, n - 1):
        y[k + 1] = (0.3 * y[k]
                    + 0.05 * y[k] * np.sum(y[k - order + 1:k + 1])
                    + 1.5 * u[k - order + 1] * u[k]
                    + 0.1)
        if not np.isfinite(y[k + 1]) or abs(y[k + 1]) > 1e3:
            raise FloatingPointError("NARMA diverged")
    return y


def mackey_glass(n, rng=None, tau=17, beta=0.2, gamma=0.1, n_exp=10,
                 dt=1.0, discard=1000):
    """Mackey-Glass series, normalized to [0, 0.5] to match the drive range."""
    total = n + discard
    hist = 1.2
    x = np.full(tau + 1, hist, dtype=float)
    out = np.empty(total)
    buf = list(x)
    for k in range(total):
        x_tau = buf[-tau - 1]
        x_now = buf[-1]
        x_new = x_now + dt * (beta * x_tau / (1 + x_tau ** n_exp) - gamma * x_now)
        buf.append(x_new)
        out[k] = x_new
    s = out[discard:]
    s = (s - s.min()) / (s.max() - s.min()) * 0.5
    return s


# --- tasks --------------------------------------------------------------------
def narma_nrmse(x_states, u, order, n_washout, n_train, return_model=False):
    y = narma_target(u, order)
    return fit_eval(x_states, y, n_washout, n_train, return_model=return_model)


def mackey_glass_nrmse(x_states, s, horizon, n_washout, n_train):
    """One-shot prediction of s(k + horizon) from the reservoir state at k."""
    y = np.roll(s, -horizon)
    y[-horizon:] = s[-1]
    return fit_eval(x_states, y, n_washout, n_train)


def memory_capacity(x_states, u, n_washout, n_train, d_max=40,
                    lam_grid=LAM_GRID):
    """Linear short-term memory capacity, MC = sum_{d>=1} r^2(u(k-d), y_hat).

    Lambda is selected per delay on a validation tail of the training window.
    Delays must satisfy d <= n_washout so that np.roll wraparound samples are
    excluded by the washout.
    """
    if d_max > n_washout:
        raise ValueError("d_max must not exceed n_washout (roll wraparound)")
    mc_d = np.zeros(d_max + 1)
    for d in range(d_max + 1):
        y = np.roll(u, d)
        xt, yt, xs, ys = _split(x_states, y, n_washout, n_train)
        lam = select_lambda(xt, yt, lam_grid)
        z = standardizer(xt)
        w = ridge_fit(z(xt), yt, lam)
        y_hat = ridge_predict(z(xs), w)
        with np.errstate(invalid="ignore", divide="ignore"):
            c = np.corrcoef(ys, y_hat)[0, 1]
        mc_d[d] = max(c, 0.0) ** 2 if np.isfinite(c) else 0.0
    return mc_d, float(np.sum(mc_d[1:]))


def memory_capacity_noise_floor(x_states, n_washout, n_train, d_max, rng,
                                n_surrogate=5, lam_grid=LAM_GRID,
                                percentile=95.0):
    """Memory capacity measured against surrogate inputs.

    Returns (total_mean, total_std, per_delay_threshold). The per-delay
    threshold is the requested percentile of the surrogate r^2 values pooled
    over delays and surrogates: a delay whose r^2 lies below it is
    indistinguishable from a reservoir that never saw the input. Thresholding
    against the TOTAL floor divided by d_max instead - the obvious shortcut -
    sets the bar far too low and reports spurious memory out to the largest
    delay measured.
    """
    totals, profiles = [], []
    for _ in range(n_surrogate):
        surrogate = rng.uniform(0, 0.5, len(x_states))
        prof, mc = memory_capacity(x_states, surrogate, n_washout, n_train,
                                   d_max, lam_grid)
        totals.append(mc)
        profiles.append(prof[1:])
    thresh = float(np.percentile(np.concatenate(profiles), percentile))
    return float(np.mean(totals)), float(np.std(totals)), thresh


def significant_depth(profile, threshold):
    """Largest delay reached before the profile first drops below threshold.

    Deliberately the FIRST crossing, not the last excursion above it: memory
    that has already decayed into the noise does not come back, so a later
    spike is a fluctuation rather than recovered memory.
    """
    prof = np.asarray(profile)
    for d in range(1, len(prof)):
        if prof[d] < threshold:
            return d - 1
    return len(prof) - 1


def parity_accuracy(x_states, u_binary, n_washout, n_train, orders=(2, 3, 4),
                    lam_grid=LAM_GRID):
    """PC-n: sign of the product of the last n binary inputs."""
    s = 2 * np.asarray(u_binary, dtype=float) - 1
    acc = {}
    for n_ord in orders:
        y = np.ones_like(s)
        for d in range(n_ord):
            y = y * np.roll(s, d)
        xt, yt, xs, ys = _split(x_states, y, n_washout, n_train)
        lam = select_lambda(xt, yt, lam_grid)
        z = standardizer(xt)
        w = ridge_fit(z(xt), yt, lam)
        acc[n_ord] = float(np.mean(np.sign(ridge_predict(z(xs), w)) == ys))
    return acc


# --- state-space diagnostics ---------------------------------------------------
def effective_rank(x_states, n_washout):
    """Participation ratio of the CORRELATION-matrix eigenvalues.

    Columns are z-scored first, which is what the ridge readout sees, so this
    counts effectively independent features rather than raw variance
    concentration. A drive that collapses all virtual nodes onto one mode
    gives ~1; fully decorrelated features give the feature count.
    """
    x = x_states[n_washout:]
    sd = x.std(axis=0)
    keep = sd > 1e-12
    if not np.any(keep):
        return 0.0
    x = (x[:, keep] - x[:, keep].mean(axis=0)) / sd[keep]
    ev = np.linalg.svd(x, compute_uv=False) ** 2
    if ev.sum() <= 0:
        return 0.0
    return float(ev.sum() ** 2 / np.sum(ev ** 2))

def effective_dof(x_states, n_washout, n_train, lam):
    """Effective degrees of freedom of the ridge readout, tr[X(X'X+lam I)^-1 X'].

    The participation ratio says how many independent directions the state
    matrix contains; this says how many of them the readout actually spends
    parameters on at a given regularization. Reporting both is what stops a
    reader assuming that P*M features means P*M usable features.
    """
    x = x_states[n_washout:n_washout + n_train]
    sd = x.std(axis=0)
    keep = sd > 1e-12
    if not np.any(keep):
        return 0.0
    z = (x[:, keep] - x[:, keep].mean(axis=0)) / sd[keep]
    sv = np.linalg.svd(z, compute_uv=False) ** 2
    return float(np.sum(sv / (sv + lam)))


def variance_components(x_states, n_washout, frac=0.95):
    """Number of principal components needed to reach `frac` of the variance."""
    x = x_states[n_washout:]
    sd = x.std(axis=0)
    keep = sd > 1e-12
    if not np.any(keep):
        return 0
    z = (x[:, keep] - x[:, keep].mean(axis=0)) / sd[keep]
    ev = np.linalg.svd(z, compute_uv=False) ** 2
    c = np.cumsum(ev) / ev.sum()
    return int(np.searchsorted(c, frac) + 1)


# --- nonlinear memory: the task a delay line provably cannot do ----------------
def delayed_parity(u_binary, delay, order=2):
    """Target: parity of `order` consecutive inputs ending `delay` steps back.

    y(k) = prod_{i=0}^{order-1} s(k - delay - i),  s = 2u - 1

    This needs memory of depth delay+order AND a nonlinearity. A linear
    readout on any linear filter of the input - a delay line included - is at
    chance for every delay, because parity is not a linear function of the
    input history. Accuracy above chance is therefore direct evidence that the
    device itself is computing, not merely storing.
    """
    s = 2 * np.asarray(u_binary, dtype=float) - 1
    y = np.ones_like(s)
    for i in range(order):
        y = y * np.roll(s, delay + i)
    return y


def nonlinear_memory_profile(x_states, u_binary, n_washout, n_train,
                             d_max=20, order=2, lam_grid=LAM_GRID):
    """Delayed-parity accuracy against delay; returns (accuracies, capacity).

    The capacity is sum_d (2*acc_d - 1)^2, the parity analogue of linear
    memory capacity: it is zero at chance and one per perfectly solved delay.
    """
    if d_max + order > n_washout:
        raise ValueError("d_max + order must not exceed n_washout")
    acc = np.zeros(d_max + 1)
    for d in range(d_max + 1):
        y = delayed_parity(u_binary, d, order)
        xt, yt, xs, ys = _split(x_states, y, n_washout, n_train)
        lam = select_lambda(xt, yt, lam_grid)
        z = standardizer(xt)
        w = ridge_fit(z(xt), yt, lam)
        acc[d] = float(np.mean(np.sign(ridge_predict(z(xs), w)) == ys))
    cap = float(np.sum(np.clip(2 * acc - 1, 0.0, None) ** 2))
    return acc, cap
