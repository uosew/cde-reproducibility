#!/usr/bin/env python3
"""CDE V11 Blind Challenge — GENERATOR (conosce i modelli; il discoverer
non deve MAI importare questo file ne' leggere sealed/).

PREREGISTRATION_V11_BLIND_CHALLENGE_2026_07_31.md @ 28e4c4bb.
9 classi x 10 seed x 5 IC; solver FD (Nx=400) con diffusivita' D(x,v),
perdita beta(x), sorgente S(x,t), avvezione w(t), BC Neumann o Robin;
degradazione camera via twin V11 con parametri campionati DENTRO
l'envelope di procurement. Output: cases/*.npz (float16),
public_meta.json (solo parametri camera), sealed/truth.json (sha256
nell'envelope; sigillo = hash + ordine dei commit).

Uso: python CDE_V11_BLIND_GENERATOR_V0.py [--smoke]
"""
from __future__ import annotations

import argparse
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
CASES = OUT / "cases"
SEALED = OUT / "sealed"
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


Q = _load("q", "CDE_V11_VIRTUAL_INSTRUMENT_QUALIFICATION_V0.py")

L_BAR, T_END, DENSE_HZ = 0.4, 120.0, 45.0
CLASSES = "ABCDEFGHI"
ICS_BASE = ((0.10, 60.0, 0.05), (0.20, 80.0, 0.06), (0.30, 50.0, 0.05),
            (0.14, 70.0, 0.08), (0.26, 45.0, 0.06))


def _git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def draw_model(cls, rng):
    a = float(rng.uniform(5e-5, 2e-4))
    m = {"alpha": a, "beta": 0.0, "gamma": 0.0, "alpha_x": None,
         "source": None, "robin": 0.0, "iface": None, "advect": None,
         "null_kind": None}
    if cls == "A":
        sup = ["v_xx"]
    elif cls == "B":
        m["beta"] = float(rng.uniform(0.005, 0.05))
        sup = ["v", "v_xx"]
    elif cls == "C":
        m["beta"] = float(rng.uniform(0.005, 0.05))
        m["gamma"] = float(rng.uniform(0.003, 0.008))
        sup = ["div_vv_x", "v", "v_xx"]
    elif cls == "D":
        m["alpha_x"] = float(rng.uniform(0.0, 2 * np.pi))   # fase
        sup = None
    elif cls == "E":
        m["beta"] = float(rng.uniform(0.005, 0.05))
        m["source"] = {"x0": float(rng.uniform(0.1, 0.3)),
                       "w": 0.03, "amp": float(rng.uniform(0.3, 1.0)),
                       "tau": 15.0}
        sup = None
    elif cls == "F":
        m["robin"] = float(rng.uniform(0.3, 0.8))
        sup = ["v_xx"]
    elif cls == "G":
        m["iface"] = {"xi": float(rng.uniform(0.15, 0.25)),
                      "ratio": float(rng.uniform(1.8, 2.5))}
        sup = None
    elif cls == "H":
        m["null_kind"] = "mixed"
        sup = "NULL"
    else:  # I
        m["beta"] = float(rng.uniform(0.005, 0.05))
        m["advect"] = {"w0": float(rng.uniform(0.002, 0.005)),
                       "period": 25.0}
        sup = None
    return m, sup


def simulate(m, ic):
    Nx = 400
    x = np.linspace(0.0, L_BAR, Nx)
    dx = x[1] - x[0]
    if m["iface"] is not None:
        prof = 1.0 + (m["iface"]["ratio"] - 1.0) * 0.5 * (
            1.0 + np.tanh((x - m["iface"]["xi"]) / 0.01))
        D_x = m["alpha"] * prof
    elif m["alpha_x"] is not None:
        D_x = m["alpha"] * (1.0 + 0.25 * np.sin(3 * np.pi * x / L_BAR
                                                + m["alpha_x"]))
    else:
        D_x = np.full(Nx, m["alpha"])
    Dmax = float(D_x.max()) * (1.0 + m["gamma"] * 100.0)
    dt = 0.2 * dx * dx / Dmax
    xc, dT, wid = ic
    v = dT * np.exp(-0.5 * np.square((x - xc) / wid))
    if m["source"] is not None:
        s = m["source"]
        Sx = s["amp"] * np.exp(-0.5 * np.square((x - s["x0"]) / s["w"]))
    nsteps = int(round(T_END / dt))
    save_every = max(1, int(round(1.0 / (DENSE_HZ * dt))))
    frames, times = [], []
    tcur = 0.0
    for n in range(nsteps + 1):
        if n % save_every == 0:
            frames.append(v.copy())
            times.append(tcur)
        D = D_x * (1.0 + m["gamma"] * v)
        vx = np.gradient(v, dx)
        rhs = np.gradient(D * vx, dx) - m["beta"] * v
        if m["source"] is not None:
            rhs = rhs + Sx * np.exp(-tcur / m["source"]["tau"])
        if m["advect"] is not None:
            w = m["advect"]["w0"] * np.sin(
                2 * np.pi * tcur / m["advect"]["period"])
            rhs = rhs + w * vx
        v = v + dt * rhs
        v[0], v[-1] = v[1], v[-2]
        if m["robin"] > 0:
            v[0] *= max(0.0, 1.0 - m["robin"] * dt / dx * m["alpha"] / dx)
            v[-1] *= max(0.0, 1.0 - m["robin"] * dt / dx * m["alpha"] / dx)
        tcur += dt
    return x, np.array(times), np.array(frames)


def sample_camera(rng):
    return {"px": int(rng.choice([160, 240, 320])),
            "psf": float(rng.uniform(0.0, 4.0)),
            "netd": float(rng.uniform(0.05, 0.25)),
            "quant": float(rng.choice([0.1, 0.5])),
            "hz": float(rng.choice([2.0, 5.0, 8.7])),
            "jitter_ms": float(rng.uniform(0.0, 100.0)),
            "drift": float(rng.uniform(0.0, 0.5)),
            "dead": float(rng.uniform(0.0, 0.02)),
            "nonunif": float(rng.uniform(0.0, 0.015)),
            "motion": float(rng.uniform(0.0, 0.25)),
            "scale_err": float(rng.uniform(0.0, 0.005)),
            "sat": None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true",
                    help="2 casi per classe invece di 10")
    args = ap.parse_args()
    t0 = time.time()
    for d in (OUT, CASES, SEALED):
        d.mkdir(exist_ok=True)
    guard = RGB.enforce_runtime_guard(strict=True)

    n_per = 2 if args.smoke else 10
    truth, public = {}, {}
    k = 0
    for ci, cls in enumerate(CLASSES):
        for s in range(n_per):
            case_id = f"case_{k:03d}"
            rng = np.random.default_rng(5000 + k)
            m, sup = draw_model(cls, rng)
            cam = sample_camera(rng)
            arrays = {}
            for i, ic in enumerate(ICS_BASE):
                x, t, V = simulate(m, ic)
                xp, tp, Vd = Q.degrade_twin(x, t, V, cam, seed=300 + i)
                if cls == "H":
                    nrng = np.random.default_rng(9000 + k * 10 + i)
                    kind = "shuffle_t" if k % 2 == 0 else "phase_surrogate"
                    Vd = Q.R.V8.null_field(Vd, kind, nrng)
                arrays[f"V{i}"] = Vd.astype(np.float16)
            arrays["x"] = xp.astype(np.float32)
            arrays["t"] = tp.astype(np.float32)
            np.savez_compressed(CASES / f"{case_id}.npz", **arrays)
            public[case_id] = {"px": cam["px"], "hz": cam["hz"],
                               "camera": cam}
            truth[case_id] = {"cls": cls,
                              "representable": sup not in (None, "NULL"),
                              "is_null": sup == "NULL",
                              "true_support": (sup if isinstance(sup, list)
                                               else None),
                              "model": m}
            k += 1
        print(f"   classe {cls}: {n_per} casi ({time.time() - t0:.0f}s)",
              flush=True)

    (OUT / "public_meta.json").write_text(json.dumps(public, indent=1))
    tp = SEALED / "truth.json"
    tp.write_text(json.dumps(truth, indent=1))
    manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(CASES.glob("*.npz"))}
    env = {"run": "CDE_V11_BLIND_GENERATOR_V0", "smoke": args.smoke,
           "prereg": PREREG, "n_cases": k,
           "timestamp_utc": datetime.now(timezone.utc)
                                    .strftime("%Y-%m-%dT%H:%M:%SZ"),
           "truth_sha256": hashlib.sha256(tp.read_bytes()).hexdigest(),
           "cases_manifest_sha256": hashlib.sha256(
               json.dumps(manifest, sort_keys=True).encode()).hexdigest(),
           "python_version": platform.python_version(),
           "numpy_version": np.__version__,
           "platform": platform.platform(),
           "git_commit": _git_commit(),
           "runtime_guard": guard,
           "human_review_required": True}
    (OUT / "generator_envelope.json").write_text(json.dumps(env, indent=2))
    (OUT / "cases_manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"{k} casi generati in {OUT}  ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
