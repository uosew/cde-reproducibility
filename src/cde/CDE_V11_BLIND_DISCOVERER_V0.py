#!/usr/bin/env python3
"""CDE V11 Blind Challenge — DISCOVERER (cieco).

PREREGISTRATION_V11_BLIND_CHALLENGE_2026_07_31.md @ 28e4c4bb.
Legge ESCLUSIVAMENTE cde_v11_blind_out/cases/*.npz e public_meta.json
(parametri camera ammessi). NON importa il generator, NON legge sealed/.
Per ogni caso: ingestion -> preflight non-oracle per IC -> selezione
v1.1 pooled IC0..3 -> holdout IC4 -> swap relativo 2x -> verdetto ladder
v2. Output: verdicts.json, emesso PRIMA dell'unblinding.

Uso: ../.venv313/bin/python CDE_V11_BLIND_DISCOVERER_V0.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import platform
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
ART = BASE.parent.parent / "artifacts"      # public layout (cde-reproducibility)
PAPER = BASE.parent.parent / "paper"
ROOT = BASE.parent
OUT = ART / "cde_v11_blind_out"
PREREG = "PREREGISTRATION_V11_BLIND_CHALLENGE_2026_07_31.md @ 28e4c4bb"

RGB_spec = importlib.util.spec_from_file_location(
    "runtime_guard_bootstrap", BASE / "runtime_guard_bootstrap.py")
RGB = importlib.util.module_from_spec(RGB_spec)
RGB_spec.loader.exec_module(RGB)

import numpy as np                                    # noqa: E402


def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, BASE / fname)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# SOLO la pipeline (rehearsal): nessun import del generator o del twin
R = _load("reh", "CDE_THERMAL_DRESS_REHEARSAL_V0.py")
LAD = R.LAD
GATE = R.GATE


def _git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def eval_case(case_path, hz):
    data = np.load(case_path)
    x = data["x"].astype(np.float64)
    t = data["t"].astype(np.float64)
    R.WX = 0.08
    R.WT = float(min(max(4.0, 22.0 / hz), 25.0))
    feats, pf_open, pf_p3 = [], [], []
    for i in range(5):
        V = data[f"V{i}"].astype(np.float64)
        centers = R.centers_for(x, t, seed=7 + i)
        if not centers:
            return {"verdict": "REJECTED_PREFLIGHT", "note": "no windows"}
        pf, F = R.preflight(x, t, V, centers)
        pf_open.append(pf["open"])
        pf_p3.append(pf["P3"])
        feats.append(F)
    Fp = {k: np.concatenate([feats[i][k] for i in range(4)])
          for k in feats[0]}
    selp = R.select_thermal(Fp, sel_seed=7)
    r_hold = R.transfer_resid(selp["coefficients"], feats[4])
    swp = R.swap_rel(Fp, set(selp["support"]), selp["fit_rel_resid"])
    st = {"operator_valid": True,
          "numerical_preflight": all(pf_open),
          "support_stable": bool(selp["support"]),
          "fit_gate": bool(selp["fit_rel_resid"] < GATE),
          "transfer_gate": bool(r_hold < GATE),
          "identifiability_gate": not swp["not_identifiable"],
          "replication": True}
    v = LAD.ladder_verdict(st)
    return {"verdict": v["verdict"], "blocked_at": v["blocked_at"],
            "support": selp["support"],
            "coefficients": selp["coefficients"],
            "fit_resid": selp["fit_rel_resid"],
            "r_holdout": r_hold,
            "preflight_open_all": all(pf_open),
            "preflight_p3": [round(p, 4) for p in pf_p3]}


def main():
    t0 = time.time()
    guard = RGB.enforce_runtime_guard(strict=True)
    public = json.loads((OUT / "public_meta.json").read_text())
    cases = sorted((OUT / "cases").glob("case_*.npz"))
    verdicts = {}
    for p in cases:
        cid = p.stem
        r = eval_case(p, public[cid]["hz"])
        verdicts[cid] = r
        print(f"   {cid}: {r['verdict']} support={r.get('support')}",
              flush=True)
    vp = OUT / "verdicts.json"
    vp.write_text(json.dumps(verdicts, indent=1))
    env = {"run": "CDE_V11_BLIND_DISCOVERER_V0", "prereg": PREREG,
           "n_cases": len(verdicts),
           "timestamp_utc": datetime.now(timezone.utc)
                                    .strftime("%Y-%m-%dT%H:%M:%SZ"),
           "verdicts_sha256": hashlib.sha256(vp.read_bytes()).hexdigest(),
           "inputs": ["cases/*.npz", "public_meta.json"],
           "python_version": platform.python_version(),
           "numpy_version": np.__version__,
           "platform": platform.platform(),
           "git_commit": _git_commit(),
           "runtime_guard": guard,
           "human_review_required": True}
    (OUT / "discoverer_envelope.json").write_text(json.dumps(env, indent=2))
    from collections import Counter
    print("== verdetti ==",
          dict(Counter(v["verdict"] for v in verdicts.values())))
    print(f"Output in {OUT}/verdicts.json  ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
