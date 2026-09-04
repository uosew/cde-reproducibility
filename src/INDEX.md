# src/cde — frozen subset of the discovery code, by role

The modules locate each other by file name in this directory, exactly as in the source repository; the only edit applied at extraction is the artifact path (`ART`, `PAPER`), recorded per file in `provenance/EXTRACTION.json` with the original sha256.

| role | files |
|---|---|
| operator v7 | `CDE_WEAK_OPERATOR_COMPONENTWISE_IDENTITY_V7.py` |
| engine v8 (frozen) and KS v9 | `CDE_PDE_DISCOVERY_V8.py`, `CDE_KS_DISCOVERY_V9.py`, `CDE_V8_EXTERNAL_SOLVER_REPLICATION_V0.py`, `CDE_V8_AVVERSARIALE_V0.py` |
| gated pipelines | `CDE_PDE_PIPELINE_GATED_V0.py`, `CDE_PDE_PIPELINE_GATED_V1.py`, `CDE_PDE_PIPELINE_GATED_V1_1.py` (V1 + declared resolution bound) |
| runtime guard | `runtime_guard_bootstrap.py`, `numpy_guard.py` |
| validation layer v10 | `CDE_V10_NONORACLE_PREFLIGHT_V0.py`, `CDE_V10_CLAIM_LADDER_AUDIT_V0.py`, `CDE_V10_WRONG_LIBRARY_V0.py`, `CDE_V10_CAPABILITY_MATRIX_V0.py` |
| thermal line | `CDE_THERMAL_DRESS_REHEARSAL_V0.py`, `CDE_V11_BLIND_GENERATOR_V0.py`, `CDE_V11_BLIND_DISCOVERER_V0.py`, `CDE_V11_BLIND_DISCOVERER_V1.py`, `CDE_V11_BLIND_UNBLINDING_V1.py`, `CDE_V13_BLIND_GENERATOR_V0.py`, `CDE_V13_BLIND_DISCOVERER_V0.py`, `CDE_V13_BLIND_UNBLINDING_V0.py` |
| blind PDE panels | `CDE_BLIND_PDE_RUNNER_V0.py`, `CDE_BLIND_PDE2_GENERATOR_V0.py`, `CDE_BLIND_PDE2_RUNNER_V0.py`, `CDE_BLIND_PDE2_SCORER_V0.py`, `CDE_PIPELINE_REPLAY_BLIND2_V0.py`, `CDE_PIPELINE_REPLAY_BLIND2_V1_1.py` |
| resolution bound and blind-4 | `CDE_RISOLUZIONE_CLAIM_V0.py`, `CDE_RISOLUZIONE_STAGE1_V0.py`, `CDE_RISOLUZIONE_ANALYZER_V0.py`, `CDE_BLIND4_GENERATOR_V0.py`, `CDE_BLIND4_RUNNER_V0.py`, `CDE_BLIND4_SCORER_V0.py` |
| paper builders | `build_research_note_v0.py` (numbers + asserts), `build_research_note_latex_v0.py`, `build_note_figures_v0.py` |
