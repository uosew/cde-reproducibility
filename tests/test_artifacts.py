import hashlib, json
from pathlib import Path
from _common import ROOT
A = ROOT / "artifacts"
def test_sha256sums_match():
    bad = []
    for line in (ROOT / "provenance/SHA256SUMS").read_text().splitlines():
        h, rel = line.split("  ", 1); p = ROOT / rel
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != h: bad.append(rel)
    assert not bad, bad[:10]
def test_only_design_matrices_are_committed_not_raw_fields():
    """Raw simulation fields regenerate from the seeds and stay out; the exported design
    matrices of the paired comparison are in, because they are its interface."""
    npz = list(A.rglob("*.npz"))
    assert all(p.parent.name == "cde_feature_export_out" for p in npz), [
        str(p) for p in npz if p.parent.name != "cde_feature_export_out"]
    total_mb = sum(p.stat().st_size for p in npz) / 1e6
    assert total_mb < 5, total_mb
def test_blind4_truth_seal_matches_envelope():
    env = json.loads((A / "cde_blind4_out/generation_envelope.json").read_text())
    assert hashlib.sha256((A / "cde_blind4_out/sealed/truth.json").read_bytes()).hexdigest() == env["truth_sha256"]
    assert (A / "cde_blind4_out/sealed/truth.sha256").read_text().strip() == env["truth_sha256"]
def test_v11_truth_seal_matches_envelope():
    env = json.loads((A / "cde_v11_blind_out/generator_envelope.json").read_text())
    assert hashlib.sha256((A / "cde_v11_blind_out/sealed/truth.json").read_bytes()).hexdigest() == env["truth_sha256"]
