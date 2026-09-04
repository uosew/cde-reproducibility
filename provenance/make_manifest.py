#!/usr/bin/env python3
"""Write provenance/SHA256SUMS (every file under artifacts/, paper/main.tex, src/cde/*.py) and MANIFEST.json."""
import hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
files = sorted(list((ROOT / "artifacts").rglob("*")) + list((ROOT / "src/cde").glob("*.py")) + [ROOT / "paper/main.tex"] + list((ROOT / "blind/protocols").glob("*.md")))
lines = [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT)}" for p in files if p.is_file()]
(ROOT / "provenance/SHA256SUMS").write_text("\n".join(lines) + "\n")
ex = json.loads((ROOT / "provenance/EXTRACTION.json").read_text())
campaigns = {
 "cde_weak_operator_componentwise_identity_v7_out": ("V7 componentwise operator identities", "CDE_WEAK_OPERATOR_COMPONENTWISE_IDENTITY_V7.py", "protocol v1.1"),
 "cde_pde_discovery_v8_out": ("V8 discovery, four PDEs, seeds 7/11, py3.12 replica", "CDE_PDE_DISCOVERY_V8.py", "protocol v1.1 (frozen 8ecc3f85)"),
 "cde_pde_discovery_v8_multiseed": ("V8 twenty fresh seeds 101-120", "CDE_PDE_DISCOVERY_V8.py", "PREREGISTRAZIONE_V8_MULTISEED"),
 "cde_v8_avversariale_v0": ("V8 adversarial twenty seeds 201-220", "CDE_V8_AVVERSARIALE_V0.py", "PREREGISTRAZIONE_V8_AVVERSARIALE_2026_08_25.md"),
 "cde_ks_discovery_v9_out": ("V9 Kuramoto-Sivashinsky", "CDE_KS_DISCOVERY_V9.py", "protocol v1.1"),
 "cde_v8_external_solver_replication_v0_out": ("external solver replication (FD4 + RK45)", "CDE_V8_EXTERNAL_SOLVER_REPLICATION_V0.py", "protocol v1.1"),
 "cde_v8_pysindy_baseline_v0_out": ("paired PySINDy 2.1.0 baseline with oracle thresholds and gate transplant", "baseline runner", "paired baseline"),
 "cde_v11_blind_out": ("V11 sealed thermal blind challenge, 90 cases", "CDE_V11_BLIND_GENERATOR_V0.py / DISCOVERER / UNBLINDING_V1", "PREREGISTRATION_V11_BLIND_V1_2026_07_31.md"),
 "cde_v13_blind_out": ("V13 sealed replica, 603 cases, two nodes", "CDE_V13_BLIND_GENERATOR_V0.py / DISCOVERER / UNBLINDING_V0", "PREREGISTRAZIONE_CDE_V13_REPLICA_LARGA_SCALA_2026_08_02.md"),
 "cde_blind_pde_out": ("blind PDE panel 1", "CDE_BLIND_PDE_RUNNER_V0.py", "PREREGISTRAZIONE_BLIND_PDE_2026-08-24.md"),
 "cde_blind_pde2_out": ("blind PDE panel 2 (conditioning + amplitude gates)", "CDE_BLIND_PDE2_GENERATOR/RUNNER/SCORER_V0.py", "PREREGISTRAZIONE_BLIND_PDE2_2026-08-24.md"),
 "cde_risoluzione_claim_out": ("resolution bound, Stage 1 diagnostic on V13 claims", "CDE_RISOLUZIONE_STAGE1_V0.py / ANALYZER", "PREREGISTRAZIONE_LIMITE_RISOLUZIONE_CLAIM_2026-09-03.md"),
 "cde_blind4_out": ("blind-4, 120 sealed representable cases, resolution bound confirmed", "CDE_BLIND4_GENERATOR/RUNNER/SCORER_V0.py", "PREREGISTRAZIONE_LIMITE_RISOLUZIONE_CLAIM_2026-09-03.md"),
}
man = {"lb_commit": next(iter(ex["codice"].values()))["lb_commit"], "artifact_dirs": {}, "code": ex["codice"]}
for k, v in ex["artefatti"].items():
    d = k.split("/")[0]; c = campaigns.get(d, ("(supporting artifact)", "", ""))
    man["artifact_dirs"].setdefault(d, {"campaign": c[0], "produced_by": c[1], "protocol": c[2], "files": {}})["files"][k] = v
(ROOT / "provenance/MANIFEST.json").write_text(json.dumps(man, indent=1))
print(f"SHA256SUMS: {len(lines)} files; MANIFEST: {len(man['artifact_dirs'])} artifact dirs, {len(man['code'])} code files, LB commit {man['lb_commit']}")
