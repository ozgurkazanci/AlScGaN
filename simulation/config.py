"""Shared experimental configuration. Imported by every exp*.py script.

Fixed once, before the production runs, so that no result depends on a
parameter chosen after seeing it. Seeds are split into two disjoint pools:
SELECT_SEEDS are used only to choose operating points and hyperparameters,
EVAL_SEEDS only to produce reported numbers.
"""

import numpy as np

# --- material / device design -------------------------------------------------
EC_TARGET = 2.7          # MV/cm, shared coercive field for the whole wafer
N_SEG = 16               # composition segments resolved per pad
TAU_LO = 1.0e-2          # s, fast end of the designed spectrum
TAU_HI = 1.0e2           # s, slow end   -> 4 designed decades

# --- drive --------------------------------------------------------------------
M_VIRTUAL = 50           # virtual nodes per pad
THETA = 5.0e-3           # s per slot -> 0.25 s per input sample
SCHEME = "bias"          # heterogeneous operating points across virtual nodes
READOUT = "charge"       # per-slot switched charge, what a charge amp measures
FEEDBACK = 0.01          # delayed-feedback loop gain; without it the pad is a
                         # Hammerstein system (instantaneous nonlinearity plus
                         # linear filters) with no nonlinear memory at all
FEEDBACK_DELAY = 1       # in frames

# --- task / evaluation --------------------------------------------------------
N_TOTAL = 1600
N_WASHOUT = 200
N_TRAIN = 900            # leaves 500 test samples
D_MAX = 30               # linear memory-capacity delay range (<= N_WASHOUT)
D_MAX_NL = 12            # delayed-parity range for nonlinear memory capacity
PARITY_ORDER = 2
NARMA_ORDER = 10

# --- statistics ---------------------------------------------------------------
SELECT_SEEDS = [101, 102, 103]                       # operating-point search
EVAL_MASK_SEEDS = [201, 202, 203, 204, 205,
                   206, 207, 208, 209, 210]          # 10 mask realizations
EVAL_INPUT_SEEDS = [301, 302, 303, 304, 305,
                    306, 307, 308, 309, 310]         # 10 input realizations

# --- hardware assumptions for energy accounting -------------------------------
PAD_AREA_UM2 = 100.0     # 10 x 10 um pad
THICKNESS_NM = 100.0

OUT_DIR = "results"
FIG_DIR = "figures"


def inputs(seed, n=N_TOTAL):
    return np.random.default_rng(seed).uniform(0.0, 0.5, n)


def binary_inputs(seed, n=N_TOTAL):
    return np.random.default_rng(seed).integers(0, 2, n).astype(float)
