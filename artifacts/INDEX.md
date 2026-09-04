# artifacts — committed outputs the paper is built from

Raw fields (`*.npz`) are not committed: they regenerate deterministically from the seeds recorded in each campaign's envelope and preregistration, and their sha256 are listed in the campaign manifests (`manifest.json`, `cases_manifest.json`). Everything the builders read is here; `provenance/MANIFEST.json` maps each directory to the campaign, the code that produced it and its protocol.

| group | directories |
|---|---|
| null_controls / core PDE campaigns | `cde_weak_operator_componentwise_identity_v7_out`, `cde_pde_discovery_v8_out`, `cde_pde_discovery_v8_multiseed`, `cde_v8_avversariale_v0`, `cde_ks_discovery_v9_out`, `cde_v8_external_solver_replication_v0_out` |
| pysindy | `cde_v8_pysindy_baseline_v0_out` |
| blind PDE panels | `cde_blind_pde_out`, `cde_blind_pde2_out` |
| v13 | `cde_v11_blind_out`, `cde_v13_blind_out`, `cde_thermal_dress_rehearsal_v0_out`, `cde_v11_virtual_instrument_v0_out`, `cde_real_thermography_v0_out` |
| blind4 / resolution bound | `cde_risoluzione_claim_out`, `cde_blind4_out` |
| validation layer v10 | `cde_v10_*_out` |
| environment audit | `NUMPY_ELISION_REPOSITORY_AUDIT_2026_07_28.json` |
