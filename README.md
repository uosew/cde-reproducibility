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
| `provenance/` | `MANIFEST.json` (artifact → campaign, producing code, protocol, LB commit), `SHA256SUMS`, `CLAIM_PROVENANCE.md` (each quantitative claim of the paper → artifact → code → campaign → builder → place in the paper), `EXTRACTION.json` (per-module original sha256 and the one path patch applied). |

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

The tests re-score the two sealed campaigns from the committed verdicts and truth and require the numbers to equal the reports; run every scorer's mutation tests (a gate that does not change the verdict when broken fails the suite); verify `SHA256SUMS`; check the cryptographic seals (truth sha256 in the generation envelope) of the panels that have one; regenerate `main.tex` and require it to be identical; and scan the code for any operational reference to the source monorepo.

## Environment

The artifacts were produced and the paper is rebuilt with CPython 3.13.10, NumPy 2.5.1, SciPy 1.18.0, Matplotlib 3.11.1 (`requirements-lock.txt`); a py3.12 replica is in the manifest. The paired baseline artifact was produced with PySINDy 2.1.0 and is committed, so PySINDy is not needed to rebuild the paper. `src/cde/numpy_guard.py` exists because on CPython 3.14 with NumPy < 2.3 infix operations on arrays ≥ 256 KB mutate their operand (NumPy issues #28681, #30435); every run records the guard's verdict in its evidence envelope, and an envelope without a passing guard is never promotable.

## What this package is not

It is not the research repository it was extracted from, and it does not try to be: no search engines, no evolution loops, no unrelated experiments. `provenance/assemble_from_lb.py` is the extraction script; it runs only on the author's machine and is included so the extraction itself is inspectable.

## License

MIT. Cite with `CITATION.cff`.
