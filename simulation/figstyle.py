"""Shared figure style: legible first, compact second.

The first version of these figures was sized for a journal column at 7 pt and
crammed six panels into a 7 x 4.9 in canvas. It was unreadable. This version
trades area for legibility:

  * base type at 10 pt, ticks at 9 pt, nothing below 8 pt
  * panels no smaller than about 3 x 2.5 in
  * every panel gets a two-line heading - a bold line naming WHAT is plotted
    and a grey line stating WHAT TO CONCLUDE - so a reader who skips the
    caption still gets the point
  * one quantity per axis, always; two quantities of different scale get two
    panels, never a shared axis with mixed meaning

Colours come from the documented categorical palette and were checked with the
data-viz validator on the all-pairs list in light mode: worst CVD dE 9.2
(deutan), worst normal-vision dE 16.3. Aqua sits below 3:1 contrast on white,
so every series also carries a distinct marker and, where there is room, a
direct label.
"""

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# --- categorical slots (light mode) -----------------------------------------
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
VIOLET = "#4a3aa7"
RED = "#e34948"
YELLOW = "#eda100"

# --- ink --------------------------------------------------------------------
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SURFACE = "#fcfcfb"

# --- design roles -----------------------------------------------------------
DESIGN = {
    "graded":      dict(color=BLUE,   marker="o", label="composition spread"),
    "homogeneous": dict(color=ORANGE, marker="s", label="one $\\tau$ per pad"),
    "stochastic":  dict(color=AQUA,   marker="^", label="random spread"),
    "uniform":     dict(color=VIOLET, marker="D", label="single $\\tau$"),
    # references are not devices: neutral, dashed or dotted, unmarked
    "esn":         dict(color=INK2,   marker=None, label="tuned ESN (software)",
                        linestyle="--"),
    "delay_line":  dict(color=MUTED,  marker=None, label="delay line",
                        linestyle=":"),
}

# --- sequential ramp (single hue, light -> dark) -----------------------------
_BLUE_STEPS = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec",
               "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab",
               "#184f95", "#104281", "#0d366b"]
SEQ = LinearSegmentedColormap.from_list("seq_blue", _BLUE_STEPS)

_DIV = ["#0d366b", "#2a78d6", "#86b6ef", "#f0efec", "#f0a5a4", "#e34948",
        "#8f2322"]
DIV = LinearSegmentedColormap.from_list("div_blue_red", _DIV)

# --- canvas sizes (inches) ---------------------------------------------------
W = 7.2                 # full text width
SIZE_2x2 = (W, 6.4)     # four panels, ~3.2 x 2.7 each
SIZE_3x2 = (W, 9.0)     # six panels, ~3.2 x 2.6 each
SIZE_1x3 = (W, 3.2)     # three panels in a row
SIZE_1x2 = (W, 3.4)


def use_style():
    mpl.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 10,
        "axes.labelsize": 10,
        "axes.titlesize": 10.5,
        "axes.labelcolor": INK,
        "axes.edgecolor": AXIS,
        "axes.linewidth": 0.9,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": GRID,
        "grid.linewidth": 0.7,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelcolor": INK2,
        "ytick.labelcolor": INK2,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.width": 0.9,
        "ytick.major.width": 0.9,
        "xtick.major.size": 3.5,
        "ytick.major.size": 3.5,
        "legend.frameon": False,
        "legend.fontsize": 9,
        "legend.handlelength": 1.8,
        "legend.labelspacing": 0.35,
        "lines.linewidth": 1.8,
        "lines.markersize": 5,
        "lines.markeredgewidth": 0.0,
        "errorbar.capsize": 2.5,
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.05,
    })


# a left-aligned bold title longer than this reaches the next
# panel's tag; the italic line is smaller so it may run a little wider
MAX_TITLE = 42
MAX_TAKEAWAY = 62


def heading(ax, what, takeaway=None, compact=False):
    """Two-line panel heading: what is plotted, then what to conclude.

    The takeaway line is capped: anything longer overruns the panel and
    collides with the neighbouring panel's tag, which is how the first version
    of these figures became unreadable.
    """
    if len(what) > MAX_TITLE:
        raise ValueError(
            f"title is {len(what)} chars, max {MAX_TITLE}: {what!r}")
    if takeaway and len(takeaway) > MAX_TAKEAWAY:
        raise ValueError(
            f"takeaway is {len(takeaway)} chars, max {MAX_TAKEAWAY}: "
            f"{takeaway!r}")
    if takeaway:
        ax.set_title(f"{what}\n", fontsize=10.5, fontweight="bold",
                     loc="left", color=INK, pad=16)
        ax.text(0, 1.015, takeaway, transform=ax.transAxes, fontsize=8.8,
                color=INK2, ha="left", va="bottom", style="italic")
    else:
        ax.set_title(what, fontsize=10.5, fontweight="bold", loc="left",
                     color=INK, pad=7)


def panel_tag(ax, tag, dx=-0.155, dy=1.30):
    ax.text(dx, dy, tag, transform=ax.transAxes, fontsize=12,
            fontweight="bold", color=INK, ha="left", va="top")


def despine(ax, keep=("left", "bottom")):
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(side in keep)


def note(ax, text, loc="lower left", **kw):
    """A small grey note inside the axes, placed away from the data."""
    x, y, ha, va = {
        "lower left": (0.03, 0.04, "left", "bottom"),
        "lower right": (0.97, 0.04, "right", "bottom"),
        "upper left": (0.03, 0.96, "left", "top"),
        "upper right": (0.97, 0.96, "right", "top"),
    }[loc]
    ax.text(x, y, text, transform=ax.transAxes, fontsize=8.3, color=MUTED,
            ha=ha, va=va, linespacing=1.35, **kw)


def direct_label(ax, x, y, text, color, dx=6, dy=0, **kw):
    """Label a series at a point, in its own colour."""
    ax.annotate(text, xy=(x, y), xytext=(dx, dy), textcoords="offset points",
                color=color, fontsize=9, fontweight="bold", va="center", **kw)


def legend(ax, **kw):
    kw.setdefault("borderaxespad", 0.3)
    kw.setdefault("handletextpad", 0.6)
    return ax.legend(**kw)


# kept for backward compatibility with older scripts
COL1 = 3.5
COL2 = W
