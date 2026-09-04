#!/usr/bin/env python3
"""CDE V10 — WLC: wrong-library challenge (protocollo v2.0, preregistrato).

PREREGISTRATION_PROTOCOL_V2_2026_07_30.md (commit bb8f3427), sezione 2.
Pipeline di selezione v1.1 IDENTICA (stessi iperparametri, stessi rng,
stessi campi seed 7 della v1); cambia SOLO la libreria candidata:

  2a  leave-one-true-term-out: 13 configurazioni x sigma in {0, 5%}.
      Esiti: ABSTAIN_EMPTY / ABSTAIN_GATE (nessuna claim) oppure
      FALSE_SUBSTITUTE (supporto stabile + gate passato = claim errata).
      Metrica: structural FDR. Ipotesi H-WLC1: 0/26.
  2b  libreria sovradimensionata: v1.1 U {u^4, u_xxxx, u_xxxxx, u^2u_x}
      (KS: TERMS9 U {u^4, u_xxxxx, u^2u_x}), ladder sigma standard.
      Successo per cella: supporto esatto invariato + gate. H-WLC2: 0
      termini spurii su 25 celle. u_xxxxx richiede il gate D5 (validato
      qui sotto, stile track D4, PRIMA dell'uso).

Ancora di regressione: con la libreria standard su Burgers sigma=0 la
pipeline clonata deve riprodurre ESATTAMENTE la claim committata della v1.

Uso:  ../.venv313/bin/python CDE_V10_WRONG_LIBRARY_V0.py [--smoke]
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
ROOT = BASE.parent
OUT = ART / "cde_v10_wrong_library_v0_out"
PREREG = "PREREGISTRATION_PROTOCOL_V2_2026_07_30.md @ bb8f3427"


def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, BASE / fname)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RGB_spec = importlib.util.spec_from_file_location(
    "runtime_guard_bootstrap", BASE / "runtime_guard_bootstrap.py")
RGB = importlib.util.module_from_spec(RGB_spec)
RGB_spec.loader.exec_module(RGB)

import numpy as np                                    # noqa: E402

V7 = _load("v7", "CDE_WEAK_OPERATOR_COMPONENTWISE_IDENTITY_V7.py")
V8 = _load("v8", "CDE_PDE_DISCOVERY_V8.py")
V9 = _load("v9", "CDE_KS_DISCOVERY_V9.py")

EXTRA_V8 = ("u^4", "u_xxxx", "u_xxxxx", "u^2u_x")
EXTRA_KS = ("u^4", "u_xxxxx", "u^2u_x")

TRUE_ALL = dict(V8.TRUE_COEFFS)
TRUE_ALL["ks"] = V9.KS_TRUE


def _git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


# ----------------------------------------------------------------------------
# D5 del bump: phi5 = phi * B5(g1..g5) (Faa' di Bruno / Bell), con
# g = -1/(1-s^2), g5 = -240 s (3 + 10 s^2 + 3 s^4) / (1-s^2)^6.
# Gate: confronto con derivata FD (Richardson) della d4 GIA' validata (V9).
# ----------------------------------------------------------------------------

def _g4(s):
    return -24.0 * (1.0 + 10.0 * np.square(s) + 5.0 * np.power(s, 4)) \
        / np.power(1.0 - np.square(s), 5)


def _g5(s):
    return -240.0 * s * (3.0 + 10.0 * np.square(s) + 3.0 * np.power(s, 4)) \
        / np.power(1.0 - np.square(s), 6)


def bump_d5phi(s):
    s = np.asarray(s, float)
    out = np.zeros_like(s)
    m = np.abs(s) < 1.0
    sm = s[m]
    g1, g2, g3 = V7.Bump._g1(sm), V7.Bump._g2(sm), V7.Bump._g3(sm)
    g4, g5 = _g4(sm), _g5(sm)
    bell5 = (g5 + 5.0 * g4 * g1 + 10.0 * g3 * g2
             + 10.0 * g3 * np.square(g1) + 15.0 * np.square(g2) * g1
             + 10.0 * g2 * np.power(g1, 3) + np.power(g1, 5))
    out[m] = V7.Bump.phi(sm) * bell5
    return out


def validate_d5(tol=1e-4):
    """d5phi analitica vs derivata FD-Richardson della d4phi validata."""
    s = np.linspace(-0.75, 0.75, 301)
    h = 1e-3

    def fd(hh):
        return (V9.bump_d4phi(s + hh) - V9.bump_d4phi(s - hh)) / (2.0 * hh)

    fd_r = (4.0 * fd(h / 2.0) - fd(h)) / 3.0
    ana = bump_d5phi(s)
    err = float(np.max(np.abs(ana - fd_r)) / np.max(np.abs(ana)))
    assert err < tol, f"gate D5 fallito: err {err:.2e} >= {tol}"
    return {"d5_rel_err_vs_fd": err, "pass": True}


# ----------------------------------------------------------------------------
# Feature deboli parametrizzate sulla libreria (bump v1.1, Simpson)
# ----------------------------------------------------------------------------

def weak_features_wlc(x, t, U, wx, wt, centers, terms):
    ig = V7.integ_grid
    cols = {k: [] for k in ("b_time",) + tuple(terms)}
    for (xc, tc) in centers:
        mx = (x >= xc - wx) & (x <= xc + wx)
        mt = (t >= tc - wt) & (t <= tc + wt)
        xs, ts = x[mx], t[mt]
        sx = (xs - xc) / wx
        st = (ts - tc) / wt
        Uw = U[np.ix_(mt, mx)]
        Uw2 = np.square(Uw)
        Uw3 = np.power(Uw, 3)
        px = V7.Bump.phi(sx)
        dpx = V7.Bump.dphi(sx) / wx
        d2px = V7.Bump.d2phi(sx) / wx ** 2
        d3px = V7.Bump.d3phi(sx) / wx ** 3
        d4px = V9.bump_d4phi(sx) / wx ** 4
        d5px = bump_d5phi(sx) / wx ** 5
        pt = V7.Bump.phi(st)
        dpt = V7.Bump.dphi(st) / wt

        def II(F, gx, gt):
            inner = np.array([ig(F[i] * gx, xs, "simpson")
                              for i in range(F.shape[0])])
            return ig(inner * gt, ts, "simpson")

        val = {
            "b_time": -II(Uw, px, dpt),
            "u": II(Uw, px, pt),
            "u^2": II(Uw2, px, pt),
            "u^3": II(Uw3, px, pt),
            "u^4": II(np.power(Uw, 4), px, pt),
            "u_x": -II(Uw, dpx, pt),
            "u_xx": II(Uw, d2px, pt),
            "u_xxx": -II(Uw, d3px, pt),
            "u_xxxx": II(Uw, d4px, pt),
            "u_xxxxx": -II(Uw, d5px, pt),
            "uu_x": -0.5 * II(Uw2, dpx, pt),
            "u^2u_x": -(1.0 / 3.0) * II(Uw3, dpx, pt),
        }
        for k in cols:
            cols[k].append(val[k])
    return {k: np.array(v) for k, v in cols.items()}


# ----------------------------------------------------------------------------
# Pipeline v1.1 clonata, parametrizzata sui termini (stessi iperparametri)
# ----------------------------------------------------------------------------

def stability_selection_t(A, b, rng, n_terms):
    n = len(b)
    m = max(8, int(round(V8.STAB_FRAC * n)))
    counts = np.zeros(n_terms)
    for _ in range(V8.STAB_B):
        idx = rng.choice(n, size=m, replace=False)
        As, bs = A[idx], b[idx]
        candidates = {frozenset()}
        for lam in V8.LAM_GRID:
            candidates.add(V8.stlsq_support(As, bs, lam))
        best, best_bic = frozenset(), np.inf
        for sup in candidates:
            bic = V8.bic_of(As, bs, sup)
            if bic < best_bic:
                best, best_bic = sup, bic
        for i in best:
            counts[i] += 1
    freqs = counts / V8.STAB_B
    support = frozenset(int(i) for i in np.where(freqs >= V8.STAB_FREQ)[0])
    return support, freqs


def refit_t(A, b, support, terms):
    if not support:
        return {}
    idx = sorted(support)
    c, *_ = np.linalg.lstsq(A[:, idx], b, rcond=None)
    return {terms[i]: float(ci) for i, ci in zip(idx, c)}


def resid_t(A, b, coeffs, terms):
    if not coeffs:
        return 1.0
    idx = [terms.index(k) for k in coeffs]
    c = np.array([coeffs[k] for k in coeffs])
    return float(np.linalg.norm(A[:, idx] @ c - b) / np.linalg.norm(b))


def select_and_classify(F, terms, true_c, sel_rng):
    A = np.column_stack([F[k] for k in terms])
    b = F["b_time"]
    support, freqs = stability_selection_t(A, b, sel_rng, len(terms))
    coeffs = refit_t(A, b, support, terms)
    resid = resid_t(A, b, coeffs, terms)
    sup_names = sorted(terms[i] for i in support)
    if not support:
        outcome = "ABSTAIN_EMPTY"
    elif resid >= V8.GATE_FIT_RESID:
        outcome = "ABSTAIN_GATE"
    else:
        outcome = ("EXACT_CLAIM" if frozenset(coeffs) == frozenset(true_c)
                   else "FALSE_SUBSTITUTE")
    return {"support": sup_names, "coefficients": coeffs,
            "fit_rel_resid": resid, "outcome": outcome,
            "frequencies": {terms[i]: round(float(f), 3)
                            for i, f in enumerate(freqs) if f > 0}}


# ----------------------------------------------------------------------------
# Campi e finestre (identici alla v1: stessi seed, stessi centri)
# ----------------------------------------------------------------------------

def get_field(system, seed, smoke):
    if system == "ks":
        x, t, U = V9.simulate_ks(seed, smoke)
        return x, t, U, 12.0, 7.5, 0.5
    x, t, U, _ = V8.simulate(system, seed, smoke)
    return x, t, U, 1.0, 0.30, 0.05


def centers_for(x, t, wx, wt, K, seed, t_off):
    rng = np.random.default_rng(seed + 101)
    xc = rng.uniform(x[0] + wx, x[-1] - wx, K)
    tc = rng.uniform(t[0] + wt + t_off, t[-1] - wt, K)
    return list(zip(xc, tc))


def noisy(U, sigma, seed):
    if sigma == 0.0:
        return U
    noise_rng = np.random.default_rng(seed + int(sigma * 1e4))
    return U + noise_rng.normal(0.0, sigma * float(U.std()), U.shape)


def base_terms(system):
    return V9.TERMS9 if system == "ks" else V8.TERMS


def regression_anchor(smoke):
    """La pipeline clonata con libreria standard deve riprodurre la claim
    committata v1 (Burgers, sigma=0, seed 7)."""
    seed = 7
    x, t, U, wx, wt, t_off = get_field("burgers", seed, smoke)
    K = 60 if smoke else 200
    centers = centers_for(x, t, wx, wt, K, seed, t_off)
    F = weak_features_wlc(x, t, U, wx, wt, centers, V8.TERMS)
    sel_rng = np.random.default_rng(seed + 7 + 0)
    r = select_and_classify(F, V8.TERMS, V8.TRUE_COEFFS["burgers"], sel_rng)
    assert r["outcome"] == "EXACT_CLAIM", f"ancora v1 fallita: {r}"
    if not smoke:
        ref = json.loads((ART / "cde_pde_discovery_v8_out/"
                          "run_py313_canonical/results.json").read_text())
        ref_c = ref["systems"]["burgers"]["sigma"]["0.0"]["coefficients"]
        for k, v in ref_c.items():
            assert abs(r["coefficients"][k] - v) < 1e-9, \
                f"ancora v1: coeff {k} diverso ({r['coefficients'][k]} vs {v})"
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    t0 = time.time()
    OUT.mkdir(exist_ok=True)
    guard = RGB.enforce_runtime_guard(strict=True)
    seed = 7
    K = 60 if args.smoke else 200

    print("== gate D5 (u_xxxxx) ==")
    d5 = validate_d5()
    print(f"   d5 vs FD(d4 validata): {d5['d5_rel_err_vs_fd']:.2e}")
    print("== ancora di regressione v1 (Burgers sigma=0) ==")
    anchor = regression_anchor(args.smoke)
    print(f"   OK: {anchor['outcome']} support={anchor['support']}")

    res = {"run": "CDE_V10_WRONG_LIBRARY_V0", "smoke": args.smoke,
           "prereg": PREREG, "seed": seed, "d5_gate": d5,
           "anchor_v1": anchor, "leave_one_out": [], "overcomplete": {}}

    systems = ("allen_cahn", "fisher_kpp", "burgers", "kdv", "ks")
    loo_sigmas = (0.0,) if args.smoke else (0.0, 0.05)
    oc_sigmas = V8.SIGMAS[:2] if args.smoke else V8.SIGMAS

    for system in systems:
        x, t, U, wx, wt, t_off = get_field(system, seed, args.smoke)
        centers = centers_for(x, t, wx, wt, K, seed, t_off)
        terms0 = base_terms(system)
        true_c = TRUE_ALL[system]

        # --- 2a: leave-one-true-term-out --------------------------------
        for sigma in loo_sigmas:
            Un = noisy(U, sigma, seed)
            F = weak_features_wlc(x, t, Un, wx, wt, centers, terms0)
            for removed in sorted(true_c):
                terms = tuple(k for k in terms0 if k != removed)
                sel_rng = np.random.default_rng(seed + 7 + int(sigma * 1e4))
                r = select_and_classify(F, terms, true_c, sel_rng)
                r.update({"system": system, "removed": removed,
                          "sigma": sigma})
                res["leave_one_out"].append(r)
                print(f"   LOO {system} -{removed} sigma={sigma}: "
                      f"{r['outcome']} (resid={r['fit_rel_resid']:.2e}, "
                      f"support={r['support']})")

        # --- 2b: libreria sovradimensionata -----------------------------
        extra = EXTRA_KS if system == "ks" else EXTRA_V8
        terms_over = terms0 + extra
        res["overcomplete"][system] = {}
        for sigma in oc_sigmas:
            Un = noisy(U, sigma, seed)
            F = weak_features_wlc(x, t, Un, wx, wt, centers, terms_over)
            sel_rng = np.random.default_rng(seed + 7 + int(sigma * 1e4))
            r = select_and_classify(F, terms_over, true_c, sel_rng)
            r["support_exact"] = bool(frozenset(r["coefficients"])
                                      == frozenset(true_c))
            r["spurious_terms"] = sorted(frozenset(r["coefficients"])
                                         - frozenset(true_c))
            res["overcomplete"][system][str(sigma)] = r
            print(f"   OC  {system} sigma={sigma}: {r['outcome']} "
                  f"exact={r['support_exact']} spuri={r['spurious_terms']} "
                  f"(resid={r['fit_rel_resid']:.2e})")

    n_loo = len(res["leave_one_out"])
    n_false = sum(r["outcome"] == "FALSE_SUBSTITUTE"
                  for r in res["leave_one_out"])
    oc_cells = [r for s in res["overcomplete"].values() for r in s.values()]
    n_oc_spurious = sum(bool(r["spurious_terms"]) for r in oc_cells)
    n_oc_exact = sum(r["support_exact"] and r["outcome"] == "EXACT_CLAIM"
                     for r in oc_cells)
    res["summary"] = {
        "structural_fdr": n_false / max(1, n_loo),
        "loo_runs": n_loo, "loo_false_substitute": n_false,
        "loo_outcomes": {o: sum(r["outcome"] == o
                                for r in res["leave_one_out"])
                         for o in ("ABSTAIN_EMPTY", "ABSTAIN_GATE",
                                   "FALSE_SUBSTITUTE", "EXACT_CLAIM")},
        "oc_cells": len(oc_cells), "oc_cells_exact_claim": n_oc_exact,
        "oc_cells_with_spurious": n_oc_spurious,
    }
    res["elapsed_s"] = round(time.time() - t0, 2)
    print(f"== SINTESI == structural FDR {n_false}/{n_loo} | overcomplete: "
          f"{n_oc_exact}/{len(oc_cells)} claim esatte, "
          f"{n_oc_spurious} celle con spuri")

    suffix = "_smoke" if args.smoke else ""
    rp = OUT / f"results{suffix}.json"
    rp.write_text(json.dumps(res, indent=2))
    env = {"run": "CDE_V10_WRONG_LIBRARY_V0",
           "timestamp_utc": datetime.now(timezone.utc)
                                    .strftime("%Y-%m-%dT%H:%M:%SZ"),
           "results_sha256": hashlib.sha256(rp.read_bytes()).hexdigest(),
           "seed": seed,
           "python_version": platform.python_version(),
           "numpy_version": np.__version__,
           "platform": platform.platform(),
           "git_commit": _git_commit(),
           "runtime_guard": guard,
           "human_review_required": True}
    (OUT / f"evidence_envelope{suffix}.json").write_text(
        json.dumps(env, indent=2))
    print(f"Output in {OUT}  ({res['elapsed_s']}s)")


if __name__ == "__main__":
    main()
