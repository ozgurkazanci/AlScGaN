# Consolidated results

Every number the manuscript quotes, generated from the result files. All values are simulated.

## 1. Composition design space  (Figure 1)

- Quaternary on an iso-Ec trajectory at Ec = 2.7 MV/cm: **7.43 decades** of tau at **zero** Ec tolerance.
- Ternary controls, decades of tau reachable inside an Ec tolerance band:

  | tolerance | AlScN | ScGaN | quaternary |
  |---|---|---|---|
  | ±1% | 0.030 | 0.010 | 7.43 |
  | ±2% | 0.075 | 0.026 | 7.43 |
  | ±5% | 0.196 | 0.072 | 7.43 |
  | ±10% | 0.406 | 0.154 | 7.43 |

- Advantage over the better ternary at ±5%: **38x**.
- Ec cost of moving tau in a ternary: 1.30 (AlScN) and 3.44 (ScGaN) MV/cm per decade.
- With pairwise bandgap bowing the trajectory stays monotone (True) and spans 7.56 decades.
- Temperature sensitivity: one decade of tau per 25.0 K, evaluated mid-window at (x_Ga, y_Sc) = (0.35, 0.35) over 300->325 K. It is NOT constant along the trajectory: the barrier falls from 1.02 eV at the Al-rich end to 0.59 eV at the Ga-rich end, so the sensitivity runs 19 K/decade (slow end) to 33 K/decade (fast end) and the spectrum COMPRESSES with warming rather than sliding rigidly.

## 2. Controls: does the device compute at all?

- Best delay line (ridge on the raw input history): NARMA-10 NRMSE **0.3875**.
- Pad at its NARMA-selected drive: **0.5585** - it does **not** beat the delay line. NARMA-10 is therefore reported only with this control.
- Delayed parity, delay line: **0.501** (chance is 0.5). No linear filter can exceed chance here.
- Delayed parity, pad: up to **1.000** - the device computes something a delay line provably cannot.
- Tuned ESN on NARMA-10: 0.2142.

## 3. Selected operating points

Objective: nonlinear memory capacity (delayed parity). Selection seeds [101, 102] are disjoint from the evaluation seeds.

  | design | bias | gain | theta (s) | span (dec) | tau window (s) | feedback | NL-MC (select) | grid edges |
  |---|---|---|---|---|---|---|---|---|
  | graded | 0.65 | 0.1 | 0.002 | 5.0 | 0.000949–94.9 | 0.003 | 3.528 | none |
  | homogeneous | 0.65 | 0.1 | 0.002 | 4.0 | 0.001–10 | 0.003 | 3.269 | center_mult |
  | stochastic | 0.55 | 0.1 | 0.002 | 5.0 | 0.000949–94.9 | 0.003 | 3.181 | none |
  | uniform | 0.65 | 0.1 | 0.001 | 0.25 | 0.112–0.2 | 0.003 | 2.277 | span_decades |

- ESN baseline, tuned on the same objective: rho=0.6, leak=1.0, input scale=0.25, bias scale=0.5, NL-MC 9.000.

## 4. Device signatures and the feedback loop  (Figure 2)

- Retention half-life is nearly identical for the two pads (0.203 s spread versus 0.21 s single-composition - this is the `uniform` arm, not `homogeneous`): a single-number retention metric does not see the spectrum. The decay SHAPE does - the log-slope varies over 3.02 for the spread pad against 4.57 for the single-composition one, the smaller spread being the more power-law-like, multi-exponential decay.
- **Open loop the pad has almost no nonlinear memory** (capacity 1.33). Closing the loop raises it to **3.10** at gain 0.003; the usable window is [0.001, 0.006] - a factor of 6, i.e. 0.78 decades, NOT "under half a decade". Its lower edge is grid-censored: the smallest nonzero gain tested is 0.001.
- Linear memory capacity at the selected drive:
  - graded: **4.07** (surrogate floor 0.02), significant to delay 4
  - homogeneous: **2.98** (surrogate floor 0.04), significant to delay 4
  - uniform: **2.00** (surrogate floor 0.02), significant to delay 3

## 5. Headline benchmark  (Figure 3)

100 paired realizations per cell (10 mask x 10 input seeds).

  | design | P=1 | P=2 | P=4 | P=8 |
  |---|---|---|---|---|
  | graded | 2.29 ± 0.28 | 2.90 ± 0.22 | 3.10 ± 0.38 | 2.92 ± 0.61 |
  | homogeneous | 2.20 ± 0.32 | 2.59 ± 0.37 | 3.03 ± 0.19 | 2.97 ± 0.63 |
  | stochastic | 2.21 ± 0.13 | 2.56 ± 0.22 | 2.95 ± 0.24 | 3.16 ± 0.27 |
  | uniform | 2.07 ± 0.38 | 2.24 ± 0.27 | 2.33 ± 0.26 | 1.93 ± 0.39 |
  | esn | 6.34 ± 0.26 | 8.72 ± 0.19 | 10.80 ± 0.23 | 12.52 ± 0.19 |
  | delay_line | 0.00 ± 0.01 | 0.00 ± 0.01 | 0.00 ± 0.01 | 0.00 ± 0.01 |

Nonlinear memory capacity, mean ± s.d. A delay line scores zero by construction whatever its length.

- P=1, spread versus homogeneous: +0.090 ± 0.263 (+4.1%), Wilcoxon p = 9.53e-03
- P=1, spread versus uniform: +0.227 ± 0.277 (+11.0%), Wilcoxon p = 2.34e-15
- P=1, spread versus stochastic: +0.085 ± 0.245 (+3.9%), Wilcoxon p = 2.93e-02
- P=1, spread versus esn: -4.045 ± 0.403 (-63.8%), Wilcoxon p = 3.90e-18
- P=2, spread versus homogeneous: +0.304 ± 0.215 (+11.7%), Wilcoxon p = 9.60e-18
- P=2, spread versus uniform: +0.655 ± 0.248 (+29.2%), Wilcoxon p = 3.90e-18
- P=2, spread versus stochastic: +0.336 ± 0.289 (+13.1%), Wilcoxon p = 1.95e-14
- P=2, spread versus esn: -5.830 ± 0.292 (-66.8%), Wilcoxon p = 3.90e-18
- P=4, spread versus homogeneous: +0.073 ± 0.278 (+2.4%), Wilcoxon p = 2.95e-07
- P=4, spread versus uniform: +0.776 ± 0.243 (+33.3%), Wilcoxon p = 3.90e-18
- P=4, spread versus stochastic: +0.151 ± 0.399 (+5.1%), Wilcoxon p = 8.48e-06
- P=4, spread versus esn: -7.701 ± 0.540 (-71.3%), Wilcoxon p = 3.90e-18
- P=8, spread versus homogeneous: -0.049 ± 0.171 (-1.6%), Wilcoxon p = 1.82e-02
- P=8, spread versus uniform: +0.989 ± 0.593 (+51.2%), Wilcoxon p = 4.67e-18
- P=8, spread versus stochastic: -0.235 ± 0.558 (-7.5%), Wilcoxon p = 2.29e-05
- P=8, spread versus esn: -9.599 ± 0.658 (-76.7%), Wilcoxon p = 3.90e-18

- Channel efficiency (single-time-constant pads needed to match one spread pad): {'1': 2, '2': 4, '4': None, '8': 4}

## 6. Reproducibility  (Figure 4)

- The readout is ill-conditioned, so accuracy and transferability trade off. At lambda=1e-06 the readout scores 0.730 on its own device and 1.32e+03 on another; at the selected lambda=100 it scores 0.820 and 0.900.
- Deposition tolerance at which the designed and random spectra become statistically indistinguishable in variance: **sigma* = 0.02**.

  | sigma | arm | NRMSE | inter-device s.d. | state corr | transfer penalty |
  |---|---|---|---|---|---|
  | 0.0 | graded | 0.8037 | 0.00000 | 1.0000 | -0.0000 |
  | 0.0 | stochastic | 0.8058 | 0.00243 | 0.9975 | +0.0820 |
  | 0.0 | homogeneous | 0.8089 | 0.00000 | 1.0000 | -0.0000 |
  | 0.005 | graded | 0.7734 | 0.03433 | 0.9774 | +0.0569 |
  | 0.005 | stochastic | 0.7657 | 0.03625 | 0.9773 | +0.1157 |
  | 0.005 | homogeneous | 0.7765 | 0.02120 | 0.9778 | +0.0277 |
  | 0.01 | graded | 0.6769 | 0.04910 | 0.9226 | +0.1048 |
  | 0.01 | stochastic | 0.6603 | 0.05161 | 0.9284 | +0.1753 |
  | 0.01 | homogeneous | 0.6839 | 0.05130 | 0.9244 | +0.2337 |
  | 0.02 | graded | 0.6532 | 0.03069 | 0.8449 | +0.1992 |
  | 0.02 | stochastic | 0.6253 | 0.03438 | 0.8566 | +0.2365 |
  | 0.02 | homogeneous | 0.6535 | 0.03031 | 0.8478 | +0.2292 |
  | 0.03 | graded | 0.6652 | 0.03305 | 0.8392 | +0.1888 |
  | 0.03 | stochastic | 0.6368 | 0.03264 | 0.8532 | +0.1809 |
  | 0.03 | homogeneous | 0.6724 | 0.04034 | 0.8412 | +0.1904 |
  | 0.05 | graded | 0.6679 | 0.03743 | 0.8673 | +0.1173 |
  | 0.05 | stochastic | 0.6479 | 0.02746 | 0.8839 | +0.1287 |
  | 0.05 | homogeneous | 0.6654 | 0.03545 | 0.8692 | +0.1175 |


### Readout precision - the binding experimental requirement

- graded: noiseless capacity 3.047; 95% of it needs **100 dB**.
- homogeneous: noiseless capacity 2.886; 95% of it needs **more than the swept range reaches**.

- Capacity advantage of the spread against readout SNR:
  - noiseless: +0.161
  - 100 dB: +0.212
  - 90 dB: +0.132
  - 80 dB: +0.036
  - 70 dB: -0.014
  - 60 dB: -0.008
  - 50 dB: -0.006
  - 40 dB: +0.007
  - 30 dB: +0.025
  - 20 dB: +0.019

  The advantage stops being resolvable below about **90 dB**. This is the same ill-conditioning seen twice: a readout that leans on low-variance directions needs large dynamic range.

## 7. Robustness  (Figure 5)

- graded: NL-MC 3.092 at 300 K, largest drift over 275–325 K 0.073 (2.4%)
- homogeneous: NL-MC 3.034 at 300 K, largest drift over 275–325 K 0.016 (0.5%)
- uniform: NL-MC 2.433 at 300 K, largest drift over 275–325 K 0.891 (36.6%)

- Spectral span:
  - 0.0 decades: NL-MC 2.567 ± 0.200, linear MC 1.06
  - 1.0 decades: NL-MC 3.119 ± 0.062, linear MC 2.71
  - 2.0 decades: NL-MC 3.120 ± 0.087, linear MC 3.14
  - 3.0 decades: NL-MC 3.108 ± 0.073, linear MC 3.38
  - 4.0 decades: NL-MC 3.095 ± 0.077, linear MC 3.38
  - 5.0 decades: NL-MC 3.092 ± 0.078, linear MC 3.29

- Discrete ladders versus the continuum (3.092):
  - 1 distinct tau: NL-MC 2.567 ± 0.200
  - 2 distinct tau: NL-MC 2.536 ± 0.417
  - 3 distinct tau: NL-MC 2.763 ± 0.282
  - 4 distinct tau: NL-MC 2.881 ± 0.178
  - 6 distinct tau: NL-MC 2.797 ± 0.278
  - 8 distinct tau: NL-MC 3.051 ± 0.032
  - 12 distinct tau: NL-MC 3.055 ± 0.038
  - 16 distinct tau: NL-MC 3.065 ± 0.048

## 8. The ternary control  (Figure 6)

Both arrays are asked for the same 5.00-decade window and driven from one shared line, each at its own best drive.

  | | decades of tau built | Ec spread (MV/cm) | switching-rate spread | NL-MC | temperature drift |
  |---|---|---|---|---|---|
  | quaternary | 5.00 | 1.78e-15 | 0.0 decades | 3.047 | 2.2% |
  | ternary | 1.09 | 3.65 | 3.7 decades | 2.623 | 22.9% |

- The ternary reaches only **1.09** of the 5.00 decades requested before leaving the physical composition range.
- Its coercive-field spread of **3.65 MV/cm** becomes **3.7 decades** of switching-rate spread under one drive - uncontrolled diversity standing in for the designed kind, which is why it still reaches 86% of the quaternary's capacity at fixed temperature.
- The substitution fails under ambient drift: **22.9%** loss over 275-325 K against the quaternary's **2.2%**.


## 9. Declared numbers that previously had no archived run (exp8_declared.py)

Four figures quoted in earlier drafts came from working notes rather than from a script. They are measured here under the stage-4 protocol.

- **Interleaved comb against the partitioned design.** The earlier claim of "3-5% worse at every channel count" was wrong in both magnitude and universality.

  | P | graded | interleaved | difference | Wilcoxon p |
  |---|---|---|---|---|
  | 1 | 2.295 | 2.289 | -0.2% | 0.088 |
  | 2 | 2.895 | 2.681 | -7.4% | 9.3e-17 |
  | 4 | 3.103 | 2.804 | -9.7% | 2.1e-17 |
  | 8 | 2.921 | 2.584 | -11.5% | 3.9e-18 |

- **Field-free dwell slots, open loop** (25 paired realizations, graded, P = 4): capacity 1.30, 1.30, 1.30, 1.30 for 0, 1, 2, 4 dwell slots. Genuinely unchanged; the earlier figure of 1.27 matched no run.
- **Open-loop delayed parity is not at chance beyond delay zero.** Mean accuracy at delays 0-4: 1.000, 0.710, 0.622, 0.551, 0.505 (chance 0.5), contributing 1.000, 0.201, 0.071, 0.012, 0.002 to a capacity of 1.30. The zero-delay term needs no memory, so only about 0.30 reflects memory of any depth. Statements that the open-loop pad is "at chance for every delay of one or more" are too strong.
- **Conditioning of the training Gram matrix**: at P = 4, 201 columns of which only **rank 60** are numerically independent, cond(Gram) = **4.1e+33** (P = 1: 51 columns, rank 32, cond 1.1e+31). Earlier drafts said "of order 1e35".
- **Segment-permutation invariance**: max |difference| = 2.84e-14 over 600 field steps, 2.84e-14 over 3000 field steps.
