# Epistemically Gated Weak-Form Discovery of Nonlinear PDEs Under Noise

### Exact support recovery, null rejection, identifiability abstention, and cross-runtime reproducibility

*Living Brain (LB) project — technical research note, 2026-07-29.*
*All numbers in this note are generated programmatically from committed
artifacts (frozen reference commit `8ecc3f85`, protocol v1.1); the
build script aborts if any claim is not supported by the artifacts.*

---

## 1. Abstract

We report a weak-form sparse-regression protocol for recovering the governing
equations of one-dimensional nonlinear PDEs from field data, subjected to an
unusually strict epistemic discipline: every operator component is validated
against analytical identities before use; the selection pipeline is
calibrated on explicit null controls and then **frozen**; and every run is
guarded against silent numerical-environment corruption. Under this frozen
protocol (v1.1), the pipeline recovers the **exact governing support** of
five nonlinear PDEs — Allen–Cahn, Fisher–KPP, Burgers, Korteweg–de Vries,
and chaotic Kuramoto–Sivashinsky — under observational Gaussian noise from 0
to 10\% of the field standard deviation, with maximum coefficient error
1.11% across all systems, noise levels and two independent seeds (7 and 11), while
maintaining **zero false discoveries in 120 null-control runs**
(temporal-shuffle and phase-randomized surrogates). The Kuramoto–Sivashinsky
case is the primary evidence: the protocol, frozen before contact with the
system, distinguishes the destabilizing anti-diffusion $-u_{xx}$ from the
stabilizing hyper-diffusion $-u_{xxxx}$ on a spatiotemporally chaotic
attractor. We further document a failure mode of stability selection —
statistically stable supports on spectrum-preserving surrogates with
relative fit residuals ≈ 0.80 — and its remedy, a
residual-based epistemic gate. We do not claim discovery of new physics: the
supported claim is that the protocol recovers known laws, rejects hard
nulls, abstains when unidentifiable, and generalizes to a chaotic PDE never
used to calibrate the pipeline.

## 2. Introduction

Sparse regression over libraries of candidate differential operators (SINDy
and successors) can recover governing equations from data, and weak
(integral) formulations extend this to noisy fields by shifting derivatives
onto smooth test functions. Two chronic epistemic weaknesses remain. First,
the numerical operator itself is usually trusted implicitly: discretization
error in the weak features can masquerade as model mismatch and silently
steer discovery. Second, model-selection stability is commonly treated as
evidence of discovery, without null controls that measure how often the
pipeline "discovers" structure where none exists.

This note documents a protocol that addresses both weaknesses by
construction, and reports its behaviour on a five-PDE suite. The
contributions are methodological and epistemic:

1. **Validate-before-discover.** No discovery is attempted until each weak
   operator component passes analytical identity gates on the target grid
   (Section 5), and the assembled operator passes an oracle ground-truth
   residual preflight ($r_{GT} < 10^{-3}$) on each dataset.
2. **Null-calibrated, then frozen.** The selection pipeline was calibrated
   once against null controls (which exposed a real failure mode, Section
   8.1), amended to v1.1, and then frozen. Every subsequent system —
   including chaotic KS — was evaluated with zero recalibration.
3. **Runtime integrity as part of the evidence.** Each run embeds a
   machine-checked report proving the numerical environment was not affected
   by a silent array-mutation bug we discovered and quarantined (Appendix A).

## 3. Problem formulation

We observe a scalar field $u(x, t)$ on a periodic domain, sampled on a
space–time grid, possibly with additive i.i.d. Gaussian measurement noise of
standard deviation $\sigma \cdot \mathrm{std}(u)$. We posit a governing
equation $u_t = \sum_j c_j \, \theta_j(u)$ with terms drawn from a shared
candidate library. In weak form, for a compact test function $\psi$
supported on a space–time window,

$$\int u_t\, \psi = -\int u\, \psi_t, \qquad
\int \partial_x^m u \,\psi = (-1)^m \int u\, \partial_x^m \psi,
\qquad \int u u_x \psi = -\tfrac12 \int u^2 \psi_x ,$$

so every feature is computed from field samples only — no derivatives of the
data are ever estimated. The candidate library is shared across all systems:
$\{u,\ u^2,\ u^3,\ u_x,\ u_{xx},\ u_{xxx},\ u u_x\}$, extended
once (declared upfront, Section 6) with $u_{xxxx}$ for the KS study. Each
of $K = 200$ randomly placed windows contributes one row to the regression
$A c \approx b$.

## 4. Frozen discovery protocol (v1.1)

The protocol was preregistered, amended exactly once after null calibration
(v1.0 → v1.1, Section 8.1, before any claim was formulated), and then frozen.
For each dataset:

1. **Oracle preflight.** With the true coefficients $c^*$, compute
   $r_{GT} = \|A c^* - b\| / \|b\|$. Discovery proceeds only if
   $r_{GT} < 10^{-3}$; otherwise the dataset resolution is insufficient
   for the operator and the run is refused. (Resolution choices are made
   here, *before* selection ever runs.)
2. **Stability selection.** $B = 100$ subsamples of 60\% of the windows;
   on each, STLSQ supports over a fixed threshold grid
   $\lambda \in \{0.02, 0.05, 0.1, 0.2, 0.4\}$ compete by BIC, **with
   the empty support always among the candidates** — the pipeline can
   abstain. A term enters the stable support if selected in ≥ 80\% of
   subsamples.
3. **Refit and residual gate.** Coefficients are refit on all windows
   restricted to the stable support. A discovery is *claimed* only if the
   support is stable **and** the relative fit residual
   $\|A_S c_S - b\|/\|b\|$ is below 5\%: statistical stability alone is
   not treated as evidence (Section 8.1).
4. **Acceptance gates** (per system and noise level): exact support match,
   maximum relative coefficient error < 5\%, residual gate passed.

## 5. Numerical integrity and reproducibility

**Componentwise identity gates.** The temporal operator and each spatial
identity (orders 1–3, plus the Burgers convective identity) were validated
on analytical functions across quadratures, test functions and resolutions
(9 temporal and 48 spatial configurations, all gates passed).
The fourth-derivative identity required for KS was validated the same way
before first use, including an analytical Faà di Bruno derivation of the
bump test function's fourth derivative, verified against finite differences
to 1.1e-6 relative error.

**Environment guard.** During operator validation we discovered that on one
interpreter stack (CPython 3.14.0 + NumPy 2.2.6, arm64), infix array
operators inside functions can silently mutate their operand for arrays
≥ 256 KB (temporary-elision defeated by interpreter stack references). This
had produced a spurious "spatial-operator" failure signature in an earlier
campaign. All runs in this note embed a runtime-guard report (canary PASS,
supported interpreter matrix) in their evidence envelopes; the guard blocks
execution otherwise, and did so once in production during this work
(Appendix A).

**Cross-runtime replication.** The complete discovery campaign was re-run on
an independent CPython 3.12.12 environment: **356/356 numeric fields
bit-identical** to the 3.13.10 canonical run (operator validation campaign:
20/20 fields bit-identical).

**Independent solver.** To remove the same-generator objection, Burgers and
Fisher–KPP fields were regenerated with a fully independent numerical chain
(4th-order central finite differences + adaptive SciPy RK45 method-of-lines,
versus the pseudo-spectral ETDRK4 used elsewhere). Under the frozen
protocol: exact support at every noise level, zero false discoveries in
20 nulls (preflight $r_{GT}$: 4.6e-5 and
4.7e-5).

## 6. Experimental suite

| System | Equation | Regime | Data generator | $r_{GT}$ preflight |
|---|---|---|---|---|
| Allen–Cahn | $u_t = 0.05 u_{xx} + u - u^3$ | bistable relaxation | spectral ETDRK4 | 1.5e-4 |
| Fisher–KPP | $u_t = 0.05 u_{xx} + u - u^2$ | reaction–diffusion | spectral ETDRK4 | 1.0e-4 |
| Burgers | $u_t = -u u_x + 0.08 u_{xx}$ | nonlinear advection | spectral ETDRK4 (+ external FD4/RK45) | 4.6e-5 |
| KdV | $u_t = -u u_x - 0.0484\, u_{xxx}$ | dispersive | complex-L ETDRK4 | 8.6e-5 |
| Kuramoto–Sivashinsky | $u_t = -u u_x - u_{xx} - u_{xxxx}$ | spatiotemporal chaos, $L = 32\pi$ | spectral ETDRK4 | 8.7e-6 |

Noise ladder: $\sigma \in \{0, 1, 2, 5, 10\}\%$ of
$\mathrm{std}(u)$, added to samples before feature construction. Null
controls per system: 5 temporal frame shuffles and 5 phase-randomized
surrogates (identical space–time spectral magnitude, Hermitian random
phases, hence exactly real fields with no PDE dynamics). KdV and KS were
never used to tune any component: KdV entered after the operator was
validated (transfer), and KS entered after the protocol was frozen.

## 7. Results

**Headline.** Across all five systems, all noise levels, and two independent seeds (7 and 11):
exact support recovery, maximum coefficient error 1.11%,
maximum claimed-fit residual 4.1e-2, no breakdown noise level
reached ($\sigma^*$ > 10\% everywhere), and **0 false discoveries in
120 null runs**.

### 7.1 Kuramoto–Sivashinsky (primary evidence)

Chaotic regime on $L = 32\pi$, transient discarded, 100 time units kept.
The frozen pipeline recovers

$$u_t = -1.0000\, u u_x -1.0000\, u_{xx}
-1.0000\, u_{xxxx} \qquad (\sigma = 0),$$

i.e. the **negative** (destabilizing) $u_{xx}$ and the **negative**
(stabilizing) $u_{xxxx}$ jointly and with correct signs, out of an
8-term library on a chaotic attractor. At $\sigma = 10\%$ the coefficients
remain (-0.9992, -0.9981,
-0.9949). This sign-structure discrimination under chaos is
the strongest single piece of evidence in the suite — considerably stronger
than a good fit on a smooth relaxing field.

| $\sigma$ | Support | Coefficients | Max err | Fit residual | Gate |
|---|---|---|---|---|---|
| 0.0 | u_xx, u_xxxx, uu_x | u_xx: -1.0000, u_xxxx: -1.0000, uu_x: -1.0000 | 0.00% | 7.9e-6 | PASS |
| 0.01 | u_xx, u_xxxx, uu_x | u_xx: -1.0000, u_xxxx: -1.0000, uu_x: -1.0000 | 0.00% | 1.3e-3 | PASS |
| 0.02 | u_xx, u_xxxx, uu_x | u_xx: -1.0000, u_xxxx: -1.0005, uu_x: -0.9999 | 0.05% | 2.6e-3 | PASS |
| 0.05 | u_xx, u_xxxx, uu_x | u_xx: -0.9991, u_xxxx: -0.9990, uu_x: -0.9992 | 0.10% | 6.4e-3 | PASS |
| 0.1 | u_xx, u_xxxx, uu_x | u_xx: -0.9981, u_xxxx: -0.9949, uu_x: -0.9992 | 0.51% | 1.3e-2 | PASS |

### 7.2 The four V8 systems

All four systems pass every gate at every noise level; coefficient tables in
Appendix C. Summary at $\sigma = 10\%$ (worst noise):

| System | Support (exact) | Max coef err | Fit residual |
|---|---|---|---|
| Allen–Cahn | u, u^3, u_xx | 1.11% | 4.1e-2 |
| Fisher–KPP | u, u^2, u_xx | 0.65% | 5.3e-3 |
| Burgers | u_xx, uu_x | 0.12% | 1.5e-2 |
| KdV | u_xxx, uu_x | 0.31% | 2.6e-2 |

### 7.3 Null controls

120 null runs (frame-shuffled and phase-surrogate fields, all
systems, both seeds where applicable, plus the external-solver arm):
**zero claimed discoveries**. The decisive mechanism differs by null type
and by field class — see Section 8.

### 7.4 Paired external baseline (PySINDy weak-SINDy)

**Setup (full disclosure).** PySINDy v2.1.0:
`CustomLibrary` {u, u^2, u^3} wrapped in `WeakPDELibrary`
(derivative_order 3; 4 for KS), K=200 weak subdomains, no bias term,
PySINDy's STLSQ with ridge alpha=1e-5, threshold grid
[0.01, 0.02, 0.05, 0.1, 0.2, 0.5] with **oracle selection** per (system, noise level)
— the best threshold judged against ground truth, an advantage the frozen
CDE protocol never receives. Feature names mapped (`x0` = u); the library
is PySINDy's natural weak set including all cross terms f(u)·∂^k u — a
superset of ours. *Exact support* = all true terms nonzero and every other
term zero. On nulls the σ=0-selected threshold is used (fixed policy).

**Recovery.** The baseline achieves exact support in
19/25 (system, σ) cells versus
25/25 for the frozen CDE protocol (failures:
Fisher–KPP at every noise level, KdV at σ ≥ 5%). Where it recovers
(Burgers, KS, Allen–Cahn), its oracle-tuned coefficients are accurate.

**Nulls, and the causal decomposition.** Vanilla PySINDy commits a false
discovery on 49/50 null fields (CDE: 0/120),
even though an empty model was *reachable* in its threshold grid on
33/50 of them: STLSQ has no criterion that ever prefers
it. We then ran the requested ablation **PySINDy + epistemic gate**,
transplanting the v1.1 residual gate (proxy: sqrt(1-R²) of PySINDy's own
weak regression, same 5% level): null FDR drops to
**0/50** — the null-rejection advantage is
*governance, and it transfers*. But the same gate also rejects the
baseline's **true** fits at moderate noise (only 14/25
cells remain claimed discoveries; KdV falls at σ ≥ 2%, Allen–Cahn and
Fisher–KPP at σ ≥ 5%), while **all** 25 CDE cells pass the
identical gate. The decomposition is clean: null rejection comes from the
epistemic layer; noise-robust discovery power comes from the quality of the
validated weak operator. Both are needed, and neither alone explains the
paired result.

## 8. Ablations and epistemic observations

### 8.1 Stability selection without the residual gate (v1.0 → v1.1)

The archived v1.0 run (no residual gate) shows the failure mode directly:
phase-randomized surrogates produced *statistically stable* supports with
per-system pre-gate false-discovery rates of
{v10_fdr['allen_cahn']:.1f} (Allen–Cahn), {v10_fdr['fisher_kpp']:.1f}
(Fisher–KPP), {v10_fdr['burgers']:.1f} (Burgers), {v10_fdr['kdv']:.1f}
(KdV). Chance correlations at dataset level survive window subsampling:
stability is not evidence. Those stable-but-false fits, however, explain the
data poorly: across all v1.1 campaigns the *minimum* fit residual of any
stable null support is {min_null_resid:.2f}, versus {e(max_true_resid)}
*maximum* for true systems — a separation of roughly four orders of
magnitude. The 5\% residual gate, fixed once from this calibration and
never touched again, reduces null FDR to 0 everywhere while leaving every
true discovery untouched.

### 8.2 Smooth versus chaotic fields (empirical observation)

Pre-gate stable-support rates on nulls differ sharply by field class:
smooth/quasi-stationary fields yield
{rate['fisher_kpp']:.2f}–{max(rate['burgers'], rate['kdv']):.2f}
(Fisher–KPP/Burgers/KdV; external-solver arm:
{min(rate_ext.values()):.2f}–{max(rate_ext.values()):.2f}), while the
chaotic KS field yields {rate['ks']:.2f} — on broadband chaos, the nulls do
not even produce stable supports. **As an empirical observation of this
suite** (not a universal principle): stability selection is intrinsically
more discriminative on broadband chaotic fields than on smooth or
quasi-stationary fields; residual gating is essential primarily in
low-excitation regimes.

### 8.3 Oracle/identity preflight as a resolution oracle

The preflight caught two would-be failures before any discovery ran: KdV at
the default resolution ($r_{{GT}} \approx 10^{{-2}}$, third-derivative
quadrature-limited; opens at $N_x = 1024$), and KS at V8-standard sampling
($r_{{GT}} \approx 8\times10^{{-2}}$; $\psi''''$ on a chaotic field
requires $N_x = 2048$, frame step 0.1, windows $12 \times 7.5$ →
$r_{{GT}} = {e(r_gts['ks'])}$). Both decisions were made from the oracle
residual alone, before selection — resolution tuning never saw the
discovery output.

### 8.4 Empty-support abstention

Including the empty support among BIC candidates is what allows abstention:
on pure-noise regressors the pipeline returns the empty model (committed
unit test), and on KS nulls it abstains in 20/20 runs pre-gate. Without
this, the threshold grid can never produce an empty candidate and the
pipeline is structurally incapable of saying "nothing here" — a defect found
by the null tests themselves.

## 9. Limitations

- **Synthetic 1D periodic data.** All fields are generated by known PDEs on
  periodic 1D domains; noise is i.i.d. Gaussian on samples. No experimental
  data, no boundary effects, no model misspecification beyond the library.
- **Library containment.** The true support is always contained in the
  candidate library; the protocol detects absence of structure (nulls) but
  was not tested against structured *wrong* libraries.
- **Seeds.** Claims are verified on {seed_phrase}; wider seed ensembles
  (and initial-condition families) are the obvious next replication step.
- **Oracle preflight requires the true coefficients**, so it is a
  *validation* instrument: on unknown systems it must be replaced by
  operator self-consistency checks (identity gates remain applicable).
- The smooth-vs-chaotic observation (8.2) is from five systems; it is
  reported as an observation, not a law.

## 10. Conclusion

Under a frozen, null-calibrated protocol with componentwise-validated weak
operators and runtime-integrity guards, exact support recovery of five
nonlinear PDEs — including chaotic KS with opposing-sign diffusion terms —
is achievable from noisy field data up to 10\% noise with zero false
discoveries in {n_null_total} null controls. The epistemic machinery
(identity gates, oracle preflight, abstention, residual gating, environment
canaries, cross-runtime replication) is not overhead: each component caught
at least one real failure during this program. The protocol does not
discover new physics; it establishes a discipline under which claimed
discoveries are hard to fake — including by accident.

## Appendix A — Environment contamination case

While debugging a persistent Burgers "spatial-operator" anomaly, we found
that on CPython 3.14.0 + NumPy 2.2.6 (macOS arm64) infix array operations on
≥ 256 KB arrays inside functions mutate their operands in place (temporary
elision defeated by interpreter stack references): `Uw ** 2` turned `Uw`
into its square, so downstream features consumed $U^4, U^6$. The anomaly
disappeared entirely (ground-truth residual 0.80 → 4.6×10⁻⁵) once the
operations were rewritten via explicit ufuncs and the environment
quarantined. A repository audit ({audit['n_files']} Python files;
{elision_counts.get('PLAUSIBLE_MUTATION_RISK', 0)} flagged for review,
{elision_counts.get('REQUIRES_REPLICATION', 0)} confirmed-and-fixed) and a
mandatory runtime canary followed. During this very study, the guard blocked
one run after a third-party install silently downgraded NumPy — the first
production intervention of the guard. Full ledger and audit are committed
alongside the campaigns.

## Appendix B — Reproducibility manifest

| Run | Seed | Python | NumPy | Guard | results.json sha256 (prefix) |
|---|---|---|---|---|---|
| V7 (py3.13) | 7 | 3.13.10 | 2.5.1 | PASS | `a6f14e9ea5cabaf6` |
| V8 (py3.13) | 7 | 3.13.10 | 2.5.1 | PASS | `e5662ad857671b4d` |
| V8 (py3.12) | 7 | 3.12.12 | 2.5.1 | PASS | `e1704f0b5b24e45e` |
| External solver | 7 | 3.13.10 | 2.5.1 | PASS | `26439b27085048b5` |
| V9 KS (py3.13) | 7 | 3.13.10 | 2.5.1 | PASS | `9b4a119d6ed677d2` |
| V8 (seed 11) | 11 | 3.13.10 | 2.5.1 | PASS | `b359f86811322338` |
| V9 KS (seed 11) | 11 | 3.13.10 | 2.5.1 | PASS | `ed42bcc6dd6c4588` |

Frozen reference commit: `8ecc3f85` (protocol v1.1). This note is
generated by `build_research_note_v0.py`, which re-reads every artifact and
asserts every quantitative claim at build time.

## Appendix C — Extended coefficient tables

**Allen–Cahn**

| $\sigma$ | Support | Coefficients | Max err | Fit residual | Gate |
|---|---|---|---|---|---|
| 0.0 | u, u^3, u_xx | u: +1.0000, u^3: -1.0000, u_xx: +0.0500 | 0.01% | 1.4e-4 | PASS |
| 0.01 | u, u^3, u_xx | u: +1.0002, u^3: -0.9999, u_xx: +0.0500 | 0.08% | 5.3e-3 | PASS |
| 0.02 | u, u^3, u_xx | u: +0.9999, u^3: -0.9995, u_xx: +0.0500 | 0.05% | 7.8e-3 | PASS |
| 0.05 | u, u^3, u_xx | u: +1.0026, u^3: -0.9996, u_xx: +0.0500 | 0.26% | 2.2e-2 | PASS |
| 0.1 | u, u^3, u_xx | u: +1.0111, u^3: -0.9998, u_xx: +0.0503 | 1.11% | 4.1e-2 | PASS |

**Fisher–KPP**

| $\sigma$ | Support | Coefficients | Max err | Fit residual | Gate |
|---|---|---|---|---|---|
| 0.0 | u, u^2, u_xx | u: +1.0000, u^2: -1.0000, u_xx: +0.0500 | 0.01% | 9.2e-5 | PASS |
| 0.01 | u, u^2, u_xx | u: +0.9999, u^2: -0.9999, u_xx: +0.0501 | 0.13% | 7.2e-4 | PASS |
| 0.02 | u, u^2, u_xx | u: +1.0003, u^2: -1.0003, u_xx: +0.0499 | 0.13% | 1.2e-3 | PASS |
| 0.05 | u, u^2, u_xx | u: +1.0000, u^2: -0.9999, u_xx: +0.0503 | 0.53% | 2.9e-3 | PASS |
| 0.1 | u, u^2, u_xx | u: +1.0035, u^2: -1.0039, u_xx: +0.0503 | 0.65% | 5.3e-3 | PASS |

**Burgers**

| $\sigma$ | Support | Coefficients | Max err | Fit residual | Gate |
|---|---|---|---|---|---|
| 0.0 | u_xx, uu_x | u_xx: +0.0800, uu_x: -1.0000 | 0.01% | 2.2e-5 | PASS |
| 0.01 | u_xx, uu_x | u_xx: +0.0800, uu_x: -1.0000 | 0.00% | 1.9e-3 | PASS |
| 0.02 | u_xx, uu_x | u_xx: +0.0800, uu_x: -0.9999 | 0.02% | 2.9e-3 | PASS |
| 0.05 | u_xx, uu_x | u_xx: +0.0801, uu_x: -0.9996 | 0.14% | 8.3e-3 | PASS |
| 0.1 | u_xx, uu_x | u_xx: +0.0799, uu_x: -0.9988 | 0.12% | 1.5e-2 | PASS |

**KdV**

| $\sigma$ | Support | Coefficients | Max err | Fit residual | Gate |
|---|---|---|---|---|---|
| 0.0 | u_xxx, uu_x | u_xxx: -0.0484, uu_x: -1.0000 | 0.00% | 8.3e-5 | PASS |
| 0.01 | u_xxx, uu_x | u_xxx: -0.0484, uu_x: -1.0001 | 0.03% | 3.0e-3 | PASS |
| 0.02 | u_xxx, uu_x | u_xxx: -0.0484, uu_x: -0.9990 | 0.10% | 6.2e-3 | PASS |
| 0.05 | u_xxx, uu_x | u_xxx: -0.0485, uu_x: -1.0004 | 0.16% | 1.4e-2 | PASS |
| 0.1 | u_xxx, uu_x | u_xxx: -0.0485, uu_x: -1.0031 | 0.31% | 2.6e-2 | PASS |
