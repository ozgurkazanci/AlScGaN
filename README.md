# AlScGaN — a designed time-constant spectrum at fixed coercive field

Simulation package and manuscript for a study of wurtzite quaternary
Al(1−x−y)Ga(x)Sc(y)N as a physical-reservoir material.

**Everything in this repository is simulated.** No film was grown and no device
was measured. The material model is phenomenological: it is calibrated to
published coercive-field measurements, while its two retention anchors are
stated design targets rather than measurements. Both facts are declared in the
manuscript's Methods, and the limits of the claims are stated throughout rather
than collected into a separate section.

## The result, in one paragraph

An array of physical reservoir elements needs a spread of relaxation times
whose elements still switch at the same field, because otherwise they cannot
share a drive line. Sc sets the coercive field in this alloy and the Al:Ga
ratio sets the bandgap, hence the leakage that governs depolarization, so the
two properties can be moved independently. Along a trajectory of constant
coercive field the alloy spans 7.43 decades of relaxation time; inside a ±5%
coercive-field tolerance the ternary parents AlScN and ScGaN reach 0.196 and
0.072 decades. Simulating a composition-spread pad array as a delay-based
reservoir then places three bounds on what such a device can do — the advantage
is a scarce-channel one and reverses by eight readout channels, the array is
not a reservoir at all until a delayed-feedback loop is closed around it, and
the binding experimental requirement is about 90 dB of readout precision rather
than materials quality.

## Layout

```
manuscript/     the paper, as sections that assemble into one document
simulation/     the model, the experiments, and the figure scripts
  alscgan_rc/   material model, device model, arrays, reservoir, benchmarks
  exp*.py       the experiment stages, in order
  fig*.py       one script per figure
  results/      archived outputs; SUMMARY.md is the transcription source
  figures/      generated PDF and PNG figures
```

## Reproducing

Requires Python 3.11+ with `numpy`, `scipy`, `matplotlib`, and `python-docx`
for the Word build.

```bash
cd simulation
python validate.py          # model self-checks
bash run_all.sh             # every experiment stage, in order
python summarize.py         # regenerate results/SUMMARY.md
for f in fig*.py; do python "$f"; done
```

Then build the document:

```bash
cd manuscript
python assemble.py                      # sections -> MANUSCRIPT.md
python check_limitations_coverage.py    # every declared limitation still stated
python to_docx.py                       # MANUSCRIPT.md -> MANUSCRIPT.docx
```

`run_all.sh` takes a while; `simulation/threadcap.py` pins BLAS to one thread
per process before numpy is imported, which is what makes the parallel stages
worth running.

## How the numbers stay honest

- **`simulation/results/SUMMARY.md` is the single transcription source.** Every
  number quoted in the manuscript is generated into it by `summarize.py` and
  copied from there, so a re-run cannot silently leave the text behind.
- **Operating points are selected on seeds disjoint from the reported ones.**
  Selection uses `SELECT_SEEDS`, every reported comparison uses `EVAL_SEEDS`.
- **`manuscript/LIMITATIONS.md` is an internal checklist, not part of the
  paper.** Its seventeen declared items are distributed through Methods,
  Results and Discussion as prose;
  `manuscript/check_limitations_coverage.py` fails the build if any of them
  stops being stated.
- **Negative and adverse results are reported, not dropped.** The interleaved
  comb design was tested and rejected; NARMA-10 is quoted only beside a
  delay-line control that beats the device on it; the channel-efficiency
  advantage reverses at eight channels; and the composition spread becomes the
  *worse* design once cycle-to-cycle switching jitter dominates.

## Status

Manuscript in preparation. Author list, affiliations, acknowledgements and the
data-availability URL are still placeholders in the text.
