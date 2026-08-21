"""Assemble the section files into one manuscript in IOP (NCE) order.

Neuromorphic Computing and Engineering asks for the IMRaD structure -
Introduction, Method, Results, Discussion, Conclusion, Acknowledgements,
References - a 300-word abstract cap, and either numbered or author-year
references. This script imposes that order and checks the abstract length
rather than trusting it.

LIMITATIONS.md is deliberately NOT assembled into the manuscript. It is an
internal coverage checklist: its seventeen items are distributed through
Methods, Results and Discussion as prose, and check_limitations_coverage.py
verifies that each one is still represented in the assembled text. Appending it
verbatim, as an earlier version of this script did, carried the L1-L17 labels
and the checklist preamble into the built document.
"""

import pathlib
import re

HERE = pathlib.Path(__file__).parent
FIGDIR = HERE.parent / "simulation" / "figures"
ABSTRACT_CAP = 300

# (file, demote_by, replacement H1 title or None to keep)
ORDER = [
    ("abstract.md", 0, None),
    ("introduction.md", 0, None),
    ("methods.md", 0, "Methods"),
    ("results.md", 0, None),
    ("discussion.md", 0, None),
    ("conclusion.md", 0, None),
]

FIGURES = [
    ("fig1_design_space",
     "Composition design space and the decoupling it enables. "
     "(a) Coercive field over the cation plane. (b) Relaxation time over the "
     "same plane, with the iso-coercive-field trajectory overlaid. "
     "(c) Relaxation time along iso-coercive-field trajectories. "
     "(d) Decades of relaxation time reachable inside a coercive-field "
     "tolerance band, quaternary against both ternary parents."),
    ("fig2_device",
     "Device signatures, drive regime and feedback loop. "
     "(a) P-E loops. (b) Retention after poling. (c) The designed "
     "time-constant spectra. (d) Switching rate against drive bias, with the "
     "span of relaxation rates shaded. (e) Nonlinear memory capacity against "
     "feedback loop gain; the open-loop value is dotted. (f) Linear memory "
     "capacity against delay."),
    ("fig3_headline",
     "Capability against readout channel count. "
     "(a) Nonlinear memory capacity on a logarithmic axis, so the "
     "software reference and the zero-scoring delay-line control are "
     "both visible. "
     "(b) Delayed-parity accuracy against delay at eight channels. "
     "(c) Paired difference between the composition spread and each "
     "competitor. (d) NARMA-10 error beside its delay-line control."),
    ("fig4_reproducibility",
     "Reproducibility and the two prices the readout charges. "
     "(a) Accuracy against transferability as a function of ridge "
     "regularization. (b) Readout transfer penalty against deposition "
     "tolerance, with the fabrication budget marked. (c) Design advantage "
     "against readout signal-to-noise ratio. (d) Capacity against readout "
     "precision for several levels of switching jitter."),
    ("fig5_robustness",
     "Robustness of the design rule, and the numerical checks. "
     "(a) Capacity against ambient temperature. (b) Capacity against the "
     "designed spectral span. (c) Discrete time-constant ladders against "
     "the continuum. (d) Convergence in composition segments resolved per "
     "pad. (e) Convergence in virtual nodes per pad. (f) Sensitivity to "
     "bandgap bowing in the alloy model."),
    ("fig6_ternary",
     "The ternary control. (a) Decades of relaxation time each alloy can "
     "build against the window requested. (b) Capability against drive, each "
     "design at its own optimum. (c) Temperature, where the substitution "
     "fails."),
]

BACK_MATTER = """# Acknowledgements

[To be completed.]

# Data availability statement

All data in this work are simulated. The complete simulation package - the
material and device models, every experiment script, and the scripts that
produced each figure - is available at [repository], together with the
consolidated numerical results from which every value quoted in the text was
transcribed. No experimental data were generated or analysed.

# Conflict of interest

The authors declare no conflict of interest."""


def demote(text, by):
    if not by:
        return text
    return re.sub(r"^(#{1,5}) ", lambda m: "#" * (len(m.group(1)) + by) + " ",
                  text, flags=re.M)


def check_abstract():
    txt = (HERE / "abstract.md").read_text(encoding="utf-8")
    if "## Abstract" not in txt:
        return None
    body = txt.split("## Abstract", 1)[1].split("**Keywords", 1)[0]
    n = len(body.split())
    status = "ok" if n <= ABSTRACT_CAP else f"OVER the {ABSTRACT_CAP}-word cap"
    print(f"abstract: {n} words ({status})")
    return n


def main():
    check_abstract()
    parts = []
    for name, dem, retitle in ORDER:
        text = (HERE / name).read_text(encoding="utf-8").strip()
        if retitle:
            text = re.sub(r"^# .*$", f"# {retitle}", text, count=1, flags=re.M)
        parts.append(demote(text, dem))

    parts.append(BACK_MATTER)
    # references.md keeps editorial notes (provenance, citation status) behind
    # an INTERNAL marker; they are for the authors, not for the paper
    refs = (HERE / "references.md").read_text(encoding="utf-8")
    parts.append(refs.split("<!-- INTERNAL")[0].strip())

    figs = ["# Figures", ""]
    for i, (stem, caption) in enumerate(FIGURES, 1):
        figs += [f"**Figure {i}.** {caption}", "",
                 f"![Figure {i}](../simulation/figures/{stem}.png)", ""]
    parts.append("\n".join(figs))

    out = HERE / "MANUSCRIPT.md"
    out.write_text("\n\n---\n\n".join(parts) + "\n", encoding="utf-8")

    text = out.read_text(encoding="utf-8")
    print(f"wrote {out.name}: {len(text.split())} words, "
          f"{len(FIGURES)} figures")
    print("section order:", " -> ".join(
        m.group(1) for m in re.finditer(r"^# (.+)$", text, flags=re.M)))
    missing = [s for s, _ in FIGURES if not (FIGDIR / f"{s}.png").exists()]
    print("missing figures:", missing or "none")


if __name__ == "__main__":
    main()
