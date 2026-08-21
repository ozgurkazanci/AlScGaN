"""Verify every declared limitation is still present in the assembled manuscript.

LIMITATIONS.md used to be appended to the manuscript verbatim, which
guaranteed coverage but carried the L-number labels into the built document. The items are now distributed as prose
through Methods, Results and Discussion, so coverage is no longer automatic.

This script restores the guarantee. Each declared item is represented by
fingerprints - the specific numbers and phrases that carry its substance - and
every fingerprint must appear in MANUSCRIPT.md. A fingerprint that stops
matching means an edit dropped the disclosure, not that the fingerprint needs
loosening.

Run after assemble.py:  python check_limitations_coverage.py
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent

# item -> (where it now lives, [fingerprints that must all appear])
ITEMS = {
    "L1  ordering invariance / meaning of graded": ("Methods 2", [
        "invariant to segment ordering",
        "3000 field steps",
        "designed distribution of time constants",
        "provably are not",
    ]),
    "L2  inter-segment coupling neglected": ("Methods 2", [
        "inter-segment electrostatic coupling is neglected",
        "of the pad area",
        "growth-axis graded stack",
    ]),
    "L3  linear virtual-crystal bandgap": ("Methods 1, Results 1", [
        "linear virtual-crystal approximation",
        "few hundred meV",
        "7.56 decades",
        "illustrative rather than as fabrication targets",
    ]),
    "L4  retention prefactor pinned": ("Methods 1", [
        "is **pinned**",
        "inverse phonon attempt time",
        "carries no microscopic claim",
    ]),
    "L5  retention anchors are design targets": ("Methods 1, Discussion", [
        "design targets rather than\nmeasurements",
        "monotone in the Al:Ga",
    ]),
    "L6  remanent-polarization map ad hoc": ("Methods 1", [
        "neither is tied to a calibration\nanchor",
        "Neither map appears in a segment's equation of motion",
        "loop gain quoted here is really the product",
    ]),
    "L7  single-exponential switching (KAI n=1)": ("Methods 2, Discussion", [
        "nucleation-limited switching",
        "wrong limit for the operating regime",
        "conservative with respect to our claim",
    ]),
    "L8  Merz convention fixes what Ec means": ("Methods 2", [
        "13.8",
        "126 MV cm",
        "steeper field dependence",
        "re-selected by search",
    ]),
    "L9  main results at 300 K": ("Methods 1 and 5, Results 6", [
        "at an ambient\nof 300 K",
        "one decade per 25 K",
        "compresses",
    ]),
    "L10 readout ill-conditioning": ("Methods 5, Results 4", [
        "participation ratio",
        "condition\nnumber of order 10",
        "effective degrees\nof freedom",
        "usable features",
    ]),
    "L11 NARMA-10 not a valid primary metric": ("Methods 4, Results 2", [
        "0.3875",
        "rewards storage",
        "switches the device nonlinearity off",
    ]),
    "L12 open-loop Hammerstein, loop mandatory": ("Methods 3, Results 2, Discussion", [
        "Hammerstein",
        "dwell slot",
        "closed-loop configuration",
        "no choice of composition spread repairs it",
    ]),
    "L13 usable feedback window is narrow": ("Results 2, Discussion", [
        "0.001 to 0.006",
        "three quarters of a decade",
        "trimmable loop gain",
        "constraint on the amplifier",
    ]),
    "L14 does not approach a software reservoir": ("Results 3, Discussion, Conclusion", [
        "echo state network",
        "three to four times",
        "right-censored",
        "energy and area",
    ]),
    "L15 ~90 dB readout SNR requirement": ("Results 5, Discussion", [
        "90 dB",
        "100 dB",
        "fifteen\neffective bits",
        "no amount of\nreadout precision buys the loss back",
    ]),
    "L16 interleaved design tested and rejected": ("Results 3", [
        "interleaved design",
        "not an arbitrary choice among\nequivalent tilings",
    ]),
    "L17 channel-efficiency advantage reverses": ("Results 3, Conclusion", [
        "+11.7%",
        "reversed to",
        "must not be carried to large arrays",
    ]),
    "S1  selection on disjoint seeds": ("Methods 4 and 5", [
        "SELECTION seeds",
        "EVALUATION seeds, which are disjoint",
        "selected out of sample too",
    ]),
    "S2  paired realizations, Wilcoxon": ("Methods 5", [
        "10 mask realizations crossed with 10 input",
        "Wilcoxon signed-rank test",
    ]),
    "S3  ESN baseline is not a strawman": ("Methods 4", [
        "is not a strawman",
        "matched readout dimension",
    ]),
    "S4  memory capacity against a noise floor": ("Methods 4", [
        "surrogate-input noise floor",
        "positively biased",
    ]),
    "S5  uniform baseline is best-versus-best": ("Methods 3 and 5", [
        "not an arbitrary\npick",
        "best-versus-best",
    ]),
}


def main():
    path = HERE / "MANUSCRIPT.md"
    if not path.exists():
        sys.exit("MANUSCRIPT.md not found - run assemble.py first")
    raw = path.read_text(encoding="utf-8")
    # match on whitespace-normalised text: the manuscript is hard-wrapped, so a
    # fingerprint that spans a line break must still count as present
    text = re.sub(r"\s+", " ", raw)

    # the labels themselves must be gone from the manuscript
    labels = sorted(set(re.findall(r"\*\*L\d+ ", raw)))
    stray = re.findall(r"^#+ .*[Ll]imitations.*$", raw, flags=re.M)

    missing = {}
    for item, (home, prints) in ITEMS.items():
        gone = [f for f in prints if re.sub(r"\s+", " ", f) not in text]
        if gone:
            missing[item] = (home, gone)

    for item, (home, prints) in ITEMS.items():
        mark = "MISSING" if item in missing else "ok"
        print(f"  [{mark:>7}] {item:<48} {home}")

    print()
    problems = []
    if labels:
        problems.append(f"L-labels still in the manuscript: {labels}")
    if stray:
        problems.append(f"a Limitations heading is still assembled: {stray}")
    for item, (home, gone) in missing.items():
        problems.append(f"{item}: no longer covered - missing {gone}")

    if problems:
        print("PROBLEMS:")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)
    print(f"all {len(ITEMS)} declared items are represented; no L-labels remain")


if __name__ == "__main__":
    main()
