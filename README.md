# cde-reproducibility

Reproducibility package for the research note **"Epistemically Gated Weak-Form Discovery of Nonlinear PDEs Under Noise"** (V. Berardi-Montesi, 2026; `paper/main.tex`). It is a frozen subset of a larger private research repository: exactly the code that produced the artifacts the paper is built from, the artifacts themselves, and the builders that regenerate every number and figure from them. It is deliberately small and boring: a reviewer should be able to see that *this code generates that result*, and nothing else.

## What is in here

| directory | content |
|---|---|
| `src/cde/` | 38 frozen Python modules (operator v7, engine v8, KS v9, gated pipelines V0/V1/V1.1, runtime guard, non-oracle preflight, blind generators/discoverers/scorers, resolution bound, paper builders). Flat on purpose: the modules locate each other by file name. `src/INDEX.md` groups them by role. |
| `artifacts/` | every committed output the paper reads (JSON/Markdown; raw `*.npz` fields are regenerable from recorded seeds and are not committed). `artifacts/INDEX.md` groups them by campaign. |
| `blind/protocols/` | the preregistrations, verdict semantics, claim cards, audit and decisions the campaigns were run under. |
| `builders/` | `build_numbers.py` (re-reads every artifact, runs every claim assertion, writes `provenance/CLAIM_PROVENANCE.md`), `build_figures.py`, `build_paper.py`. |
| `paper/` | `main.tex` and the figures, all generated. |
| `tests/` | the publication gate (below). |
| `provenance/` | `MANIFEST.json` (artifact → campaign, producing code, protocol, source commit), `SHA256SUMS`, `CLAIM_PROVENANCE.md` (each quantitative claim of the paper → artifact → code → campaign → builder → place in the paper), `EXTRACTION.json` (per-module original sha256 and the one path patch applied). |

## Prerequisites

- Python **3.12 or 3.13** (the artifacts were produced on 3.13.10; a 3.12 replica is in the manifest). Python 3.14 works only with NumPy ≥ 2.3: with an older NumPy the runtime guard refuses to run, on purpose (see *Environment*).
- A TeX distribution with `latexmk` and `pdflatex` **only if you want the PDF**; every number and figure is regenerated without it.
- No GPU, no network access after `pip install`; the full gate runs in well under a minute on a laptop.

## Reproduce

```bash
git clone https://github.com/uosew/cde-reproducibility
cd cde-reproducibility
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-lock.txt
pytest                                   # publication gate: 13 tests
python builders/build_numbers.py         # every claim re-asserted; CLAIM_PROVENANCE.md rewritten
python builders/build_figures.py         # paper/fig_*.pdf from artifacts only
python builders/build_paper.py           # paper/main.tex, byte-identical to the committed one
(cd paper && latexmk -pdf main.tex)      # 13 pages, 0 overfull boxes
```

Expected output, in order: `13 passed`; `8 claims verified -> provenance/numbers.json, CLAIM_PROVENANCE.md`; four `fig_*.pdf` written under `paper/` (plus the Markdown note); `paper/main.tex` rewritten and identical to the committed one (`git status` stays clean); `paper/main.pdf`, 13 pages, and `grep -c Overfull paper/main.log` printing `0`.

### Where to look

- Start from `provenance/CLAIM_PROVENANCE.md`: every quantitative claim of the paper, its value, the artifact it comes from, the code that produced the artifact, the campaign and protocol, the builder that asserts it, and where it appears in the paper.
- `blind/protocols/` holds the preregistrations (hashed before each run), the frozen verdict semantics, the claim cards and the process audit. Campaign names in the artifacts (`cde_*_out`) match the protocol file names.
- `src/INDEX.md` and `artifacts/INDEX.md` group modules and artifacts by role and campaign.

### Troubleshooting

- `RuntimeError: ... CANARY POSITIVO` or `runtime guard FAIL` at import: your interpreter/NumPy pair mutates array operands (CPython 3.14 with NumPy < 2.3). Use the pinned versions in `requirements-lock.txt`. This refusal is the guard working as designed, not a bug in the package.
- `test_paper_tex_regenerates_identically` fails: you edited `paper/main.tex` by hand. It is generated; edit the builder in `src/cde/build_research_note_latex_v0.py` instead and re-run `builders/build_paper.py`.
- `test_sha256sums_match` fails: an artifact was modified. Restore it from git; if you regenerated a campaign on purpose, re-run `provenance/make_manifest.py` and say so in your fork's history.
- Raw fields are not committed. To regenerate a sealed panel, run its generator from `src/cde/` (seeds are in the campaign envelope and preregistration); the manifests give the sha256 of every field file for verification.

The tests re-score the two sealed campaigns from the committed verdicts and truth and require the numbers to equal the reports; run every scorer's mutation tests (a gate that does not change the verdict when broken fails the suite); verify `SHA256SUMS`; check the cryptographic seals (truth sha256 in the generation envelope) of the panels that have one; regenerate `main.tex` and require it to be identical; and scan the code for any operational reference to the source monorepo.

## Environment

The artifacts were produced and the paper is rebuilt with CPython 3.13.10, NumPy 2.5.1, SciPy 1.18.0, Matplotlib 3.11.1 (`requirements-lock.txt`); a py3.12 replica is in the manifest. The paired baseline artifact was produced with PySINDy 2.1.0 and is committed, so PySINDy is not needed to rebuild the paper. `src/cde/numpy_guard.py` exists because on CPython 3.14 with NumPy < 2.3 infix operations on arrays ≥ 256 KB mutate their operand (NumPy issues #28681, #30435); every run records the guard's verdict in its evidence envelope, and an envelope without a passing guard is never promotable.

## What this package is not

It is not the research repository it was extracted from, and it does not try to be: no search engines, no evolution loops, no unrelated experiments. The extraction script is kept in the source repository; `provenance/EXTRACTION.json` records, for every module, the original sha256 and the single path patch applied.

## Contact and collaboration

Valentino Berardi-Montesi, independent researcher — **valentinoberardi@gmail.com** (ORCID [0009-0004-6209-7239](https://orcid.org/0009-0004-6209-7239)).

If this work is of interest to you, please get in touch: questions about the protocol, replication attempts on your own data, and disagreements with any claim are all welcome. I am open to **project-based collaborations** — applying the sealed-campaign discipline and the gated discovery pipeline to real field data, extending the residual gate into other sparse-regression tools, or joint replication studies. Issues and pull requests on this repository are welcome too; a failure story that one of these gates would have caught is the most useful contribution of all.

## License

MIT. Cite with `CITATION.cff`.
