#!/usr/bin/env python3
"""Limite di risoluzione dichiarato per un CLAIM (prereg 2026-09-03 §1).
Annotazione a valle: NON cambia verdetti. Pipeline-agnostica su (A, b, S, c)."""
import importlib.util
from pathlib import Path
import numpy as np
BASE = Path(__file__).resolve().parent
ART = BASE.parent.parent / "artifacts"      # public layout (cde-reproducibility)
PAPER = BASE.parent.parent / "paper"
def _L(n, f):
    s = importlib.util.spec_from_file_location(n, BASE / f); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
R = _L("reh", "CDE_THERMAL_DRESS_REHEARSAL_V0.py"); TERMS = R.TERMS
K_CANDIDATI = (1.0, 2.0)

def annota(A, b, supporto, coeffs, k):
    """X, c_min per termine fuori supporto, rho. Solo dati, nessuna verita'."""
    idx = [TERMS.index(t) for t in supporto]
    c = np.array([coeffs[t] for t in supporto], dtype=float)
    rho = float(np.linalg.norm(A[:, idx] @ c - b)) if idx else float(np.linalg.norm(b))
    nb = float(np.linalg.norm(b))
    out = {"k": k, "rho": rho, "norma_b": nb, "X": k * rho / nb, "c_min": {}}
    for t in TERMS:
        if t in supporto: continue
        na = float(np.linalg.norm(A[:, TERMS.index(t)]))
        out["c_min"][t] = (k * rho / na) if na > 0 else float("inf")
    return out

def contributo(A, b, t, c_vero):
    """f_t = |c_t| * ||A_t|| / ||b||"""
    return abs(c_vero) * float(np.linalg.norm(A[:, TERMS.index(t)])) / float(np.linalg.norm(b))

def coefficienti_veri(model):
    """Mappa parametri -> coefficienti (prereg §2). Solo per lo scorer."""
    a, be, ga = model["alpha"], model.get("beta", 0.0) or 0.0, model.get("gamma", 0.0) or 0.0
    return {"v_xx": a, "v": -be, "div_vv_x": a * ga}

def ricostruisci_Ab(case_path, hz):
    """Stesse feature pooled (repliche 0-3, Simpson) del discoverer V11/V13."""
    d = np.load(case_path); x = d["x"].astype(np.float64); t = d["t"].astype(np.float64)
    R.WX = 0.08; R.WT = float(min(max(4.0, 22.0 / hz), 25.0))
    feats = []
    for i in range(4):
        V = d[f"V{i}"].astype(np.float64); centers = R.centers_for(x, t, seed=7 + i)
        if not centers: return None, None
        feats.append(R.weak_features_thermal(x, t, V, centers, "simpson"))
    Fp = {k: np.concatenate([f[k] for f in feats]) for k in feats[0]}
    return R.to_Ab(Fp)


def annota_v2(A, b, supporto, coeffs):
    """Limite proiettato (nota 2026-09-07 §3): c_min(t) = ||(I-P_S) y|| / ||(I-P_S) a_t||, k = 1."""
    idx = [TERMS.index(t) for t in supporto]
    AS = A[:, idx]; c, *_ = np.linalg.lstsq(AS, b, rcond=None); r = b - AS @ c
    rho = float(np.linalg.norm(r)); P = AS @ np.linalg.pinv(AS)
    out = {"k": 1.0, "rho": rho, "X": rho / float(np.linalg.norm(b)), "c_min": {}, "c_min_v1_k2": {}, "chat": {}, "se": {}}
    n = len(b); sig = rho / np.sqrt(max(n - len(idx), 1))
    for t in TERMS:
        if t in supporto: continue
        a = A[:, TERMS.index(t)]; at = a - P @ a; nat = float(np.linalg.norm(at)); na = float(np.linalg.norm(a))
        out["c_min"][t] = rho / nat if nat > 0 else float("inf")
        out["c_min_v1_k2"][t] = 2 * rho / na if na > 0 else float("inf")
        out["chat"][t] = float(abs(at @ r) / (at @ at)) if nat > 0 else 0.0
        out["se"][t] = sig / nat if nat > 0 else float("inf")
    return out
