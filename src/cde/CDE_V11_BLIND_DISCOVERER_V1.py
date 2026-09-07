#!/usr/bin/env python3
"""CDE V11 Blind Challenge — DISCOVERER V1 (ladder v2.1, cieco).

PREREGISTRATION_V11_BLIND_V1_2026_07_31.md @ de395f79.
Split del preflight: data_adequacy (P1 quadratura + P2' disaccordo
RELATIVO tra famiglie) separata da library_adequacy (holdout full
library). Dati sani + libreria inadeguata -> MISSPECIFIED (primo
livello). Calibrazione tau1/tau2 = 3x max sui 10 dataset NON-blind del
rehearsal V2 GO, rigenerati deterministicamente prima della run blind.
Legge SOLO cases/*.npz + public_meta.json; nessun accesso a sealed/.

Uso: python CDE_V11_BLIND_DISCOVERER_V1.py
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
JUL = BASE.parent.parent / "baselines" / "julia"
ROOT = BASE.parent
OUT = ART / "cde_v11_blind_out"
PREREG = "PREREGISTRATION_V11_BLIND_V1_2026_07_31.md @ de395f79"

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


R = _load("reh", "CDE_THERMAL_DRESS_REHEARSAL_V0.py")
GATE = R.GATE

LEVELS21 = ("operator_valid", "data_adequacy", "library_adequacy",
            "support_stable", "fit_gate", "transfer_gate",
            "identifiability_gate", "replication")
FAIL21 = {"operator_valid": "REJECTED_OPERATOR",
          "data_adequacy": "REJECTED_PREFLIGHT",
          "library_adequacy": "MISSPECIFIED",
          "support_stable": "ABSTAIN_EMPTY",
          "fit_gate": "ABSTAIN_GATE",
          "transfer_gate": "REJECTED_TRANSFER",
          "identifiability_gate": "NOT_IDENTIFIABLE",
          "replication": "PROVISIONAL_NO_REPLICATION"}


def ladder21(state):
    for lvl in LEVELS21:
        if not state[lvl]:
            return {"verdict": FAIL21[lvl], "blocked_at": lvl}
    return {"verdict": "CLAIM", "blocked_at": None}


def _git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def ls_resid_full(F):
    A = np.column_stack([F[k] for k in R.TERMS])
    b = F["b_time"]
    c, *_ = np.linalg.lstsq(A, b, rcond=None)
    return float(np.linalg.norm(A @ c - b) / np.linalg.norm(b))


def metrics_v21(x, t, V, centers):
    """P1 quadratura, P2' disaccordo relativo tra famiglie, P3 holdout."""
    F_s = R.weak_features_thermal(x, t, V, centers, "simpson")
    F_t = R.weak_features_thermal(x, t, V, centers, "trapezoid")
    F_b2 = R.weak_features_thermal(x, t, V, centers, "simpson",
                                   R.NOP.Bump2)
    p1 = R.NOP.rel_col_diff(F_s, F_t, R.TERMS)
    rA, rB = ls_resid_full(F_s), ls_resid_full(F_b2)
    p2p = abs(rA - rB) / max(rA, rB, 1e-300)
    A = np.column_stack([F_s[k] for k in R.TERMS])
    b = F_s["b_time"]
    rng = np.random.default_rng(2026)
    perm = rng.permutation(len(b))
    nh = int(round(0.3 * len(b)))
    hold, train = perm[:nh], perm[nh:]
    ct, *_ = np.linalg.lstsq(A[train], b[train], rcond=None)
    p3 = float(np.linalg.norm(A[hold] @ ct - b[hold])
               / np.linalg.norm(b[hold]))
    return p1, p2p, p3, F_s


def calibrate_taus():
    """tau = 3x max su 10 dataset non-blind del rehearsal V2 GO."""
    R.ICS, R.WX = R.V1_ICS, 0.08
    R.T_CROP, R.DRIFT_REF, R.BIN = (10.0, 70.0), True, 1
    R.WT = 4.0
    p1s, p2s = [], []
    for gamma in (0.0, R.GAMMA_VARDIFF):
        for i, ic in enumerate(R.ICS):
            x, t, V = R.simulate_bar(ic, gamma)
            xs, Vd, td = R.degrade(x, t, V, seed=300 + i)
            centers = R.centers_for(xs, td, seed=7 + i)
            p1, p2p, _, _ = metrics_v21(xs, td, Vd, centers)
            p1s.append(p1)
            p2s.append(p2p)
    return 3.0 * max(p1s), 3.0 * max(p2s), p1s, p2s


def eval_case(case_path, hz):
    data = np.load(case_path)
    x = data["x"].astype(np.float64)
    t = data["t"].astype(np.float64)
    R.WX = 0.08
    R.WT = float(min(max(4.0, 22.0 / hz), 25.0))
    feats, p1s, p2s, p3s = [], [], [], []
    for i in range(5):
        V = data[f"V{i}"].astype(np.float64)
        centers = R.centers_for(x, t, seed=7 + i)
        if not centers:
            return {"verdict": "REJECTED_PREFLIGHT", "note": "no windows"}
        p1, p2p, p3, F = metrics_v21(x, t, V, centers)
        p1s.append(p1)
        p2s.append(p2p)
        p3s.append(p3)
        feats.append(F)
    return feats, p1s, p2s, p3s


def main():
    t0 = time.time()
    guard = RGB.enforce_runtime_guard(strict=True)

    print("== calibrazione tau1/tau2 (rehearsal V2 GO, non-blind) ==",
          flush=True)
    tau1, tau2, p1c, p2c = calibrate_taus()
    print(f"   tau1={tau1:.4f} (max cal {max(p1c):.4f}) "
          f"tau2={tau2:.4f} (max cal {max(p2c):.4f}) "
          f"({time.time() - t0:.0f}s)", flush=True)

    public = json.loads((OUT / "public_meta.json").read_text())
    cases = sorted((OUT / "cases").glob("case_*.npz"))
    verdicts = {}
    for p in cases:
        cid = p.stem
        out = eval_case(p, public[cid]["hz"])
        if isinstance(out, dict):
            verdicts[cid] = out
            continue
        feats, p1s, p2s, p3s = out
        data_ok = bool(max(p1s) <= tau1 and max(p2s) <= tau2)
        lib_ok = bool(max(p3s) < GATE)
        Fp = {k: np.concatenate([feats[i][k] for i in range(4)])
              for k in feats[0]}
        selp = R.select_thermal(Fp, sel_seed=7)
        r_hold = R.transfer_resid(selp["coefficients"], feats[4])
        swp = R.swap_rel(Fp, set(selp["support"]), selp["fit_rel_resid"])
        st = {"operator_valid": True,
              "data_adequacy": data_ok,
              "library_adequacy": lib_ok,
              "support_stable": bool(selp["support"]),
              "fit_gate": bool(selp["fit_rel_resid"] < GATE),
              "transfer_gate": bool(r_hold < GATE),
              "identifiability_gate": not swp["not_identifiable"],
              "replication": True}
        v = ladder21(st)
        verdicts[cid] = {
            "verdict": v["verdict"], "blocked_at": v["blocked_at"],
            "data_adequacy": data_ok, "library_adequacy": lib_ok,
            "P1": [round(z, 4) for z in p1s],
            "P2p": [round(z, 4) for z in p2s],
            "P3": [round(z, 4) for z in p3s],
            "support": selp["support"],
            "coefficients": selp["coefficients"],
            "fit_resid": selp["fit_rel_resid"],
            "r_holdout": r_hold}
        print(f"   {cid}: {v['verdict']}", flush=True)

    vp = OUT / "verdicts_v1.json"
    vp.write_text(json.dumps(verdicts, indent=1))
    env = {"run": "CDE_V11_BLIND_DISCOVERER_V1", "prereg": PREREG,
           "n_cases": len(verdicts),
           "tau1": tau1, "tau2": tau2,
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
    (OUT / "discoverer_v1_envelope.json").write_text(
        json.dumps(env, indent=2))
    from collections import Counter
    print("== verdetti V1 ==",
          dict(Counter(v["verdict"] for v in verdicts.values())))
    print(f"Output in {vp}  ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
