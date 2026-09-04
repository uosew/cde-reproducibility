#!/usr/bin/env python3
"""CDE_V8_EXTERNAL_SOLVER_REPLICATION_V0 — replica V8 con solver ESTERNO.

Obiettivo (fase 1 del consolidamento): verificare che la discovery V8 non
dipenda dal generatore dei dati. I campi vengono prodotti con il **metodo
delle linee**: differenze finite centrali di 4o ordine (periodiche, np.roll)
+ integratore adattivo esterno **scipy.solve_ivp RK45** — catena numerica
completamente indipendente dallo spettrale+ETDRK4 di V7/V8 (discretizzazione
diversa, integratore diverso, passo adattivo diverso).
(Nota: py-pde 0.58 era il candidato iniziale ma accoppia il backend numba,
incompatibile con numpy 2.5 della matrice di supporto; scartato.)

Protocollo: **v1.1 CONGELATO** — tutte le funzioni e costanti di selezione
(stability selection, BIC con supporto vuoto, gate su supporto/coefficienti/
residuo, scala di rumore, nulli) sono IMPORTATE da CDE_PDE_DISCOVERY_V8
senza alcuna ridefinizione. Questo file cambia solo la provenienza dei dati.

Sistemi: Burgers (u_t = -u u_x + 0.08 u_xx) e Fisher-KPP
(u_t = 0.05 u_xx + u - u^2), stesse IC per seed della V8.

Gate identici alla V8: preflight r_GT < 1e-3 per sistema, poi supporto
esatto + err coeff < 5% + residuo fit < 5% a ogni sigma; FDR nullo atteso 0.

Claim boundary: stessa della V8; questo run rimuove l'obiezione
"stesso generatore" per i due sistemi coperti.
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

import numpy as np

BASE = Path(__file__).resolve().parent
ART = BASE.parent.parent / "artifacts"      # public layout (cde-reproducibility)
PAPER = BASE.parent.parent / "paper"
ROOT = BASE.parent
OUT = ART / "cde_v8_external_solver_replication_v0_out"

_spec8 = importlib.util.spec_from_file_location(
    "v8", BASE / "CDE_PDE_DISCOVERY_V8.py")
V8 = importlib.util.module_from_spec(_spec8)
_spec8.loader.exec_module(V8)

_specg = importlib.util.spec_from_file_location(
    "runtime_guard_bootstrap", BASE / "runtime_guard_bootstrap.py")
RGB = importlib.util.module_from_spec(_specg)
_specg.loader.exec_module(RGB)

EXTERNAL_SYSTEMS = {
    "burgers": {"ic": (-1.0, 1.0), "t_range": 2.0,
                "true": V8.TRUE_COEFFS["burgers"]},
    "fisher_kpp": {"ic": (0.05, 0.6), "t_range": 3.0,
                   "true": V8.TRUE_COEFFS["fisher_kpp"]},
}

SOLVER_LABEL = "scipy solve_ivp RK45 + FD centrali 4o ordine (periodiche)"


def _dx1_4(u, dx):
    """Derivata prima, differenze centrali 4o ordine, bordo periodico."""
    return (-np.roll(u, -2) + 8.0 * np.roll(u, -1)
            - 8.0 * np.roll(u, 1) + np.roll(u, 2)) / (12.0 * dx)


def _dx2_4(u, dx):
    """Derivata seconda, differenze centrali 4o ordine, bordo periodico."""
    return (-np.roll(u, -2) + 16.0 * np.roll(u, -1) - 30.0 * u
            + 16.0 * np.roll(u, 1) - np.roll(u, 2)) / (12.0 * dx * dx)


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def simulate_external(system: str, seed: int, smoke: bool):
    """Campo da method-of-lines FD4 + scipy RK45; stesse IC per seed di V8."""
    from scipy.integrate import solve_ivp
    cfg = EXTERNAL_SYSTEMS[system]
    Nx = 256 if smoke else 512
    x = np.linspace(0.0, 2.0 * np.pi, Nx, endpoint=False)
    dx = x[1] - x[0]
    rng = np.random.default_rng(seed)
    c = rng.normal(0.0, 1.0, 4) / np.arange(1, 5)
    s = rng.normal(0.0, 1.0, 4) / np.arange(1, 5)
    f = sum(c[m] * np.cos((m + 1) * x) + s[m] * np.sin((m + 1) * x)
            for m in range(4))
    f = (f - f.min()) / (f.max() - f.min())
    lo, hi = cfg["ic"]
    u0 = lo + (hi - lo) * f

    if system == "burgers":
        def rhs(_t, u):
            return -u * _dx1_4(u, dx) + 0.08 * _dx2_4(u, dx)
    elif system == "fisher_kpp":
        def rhs(_t, u):
            return 0.05 * _dx2_4(u, dx) + u * (1.0 - u)
    else:
        raise ValueError(system)

    t_eval = np.arange(0.0, cfg["t_range"] + 1e-12, 2.5e-3)
    sol = solve_ivp(rhs, (0.0, cfg["t_range"]), u0, method="RK45",
                    t_eval=t_eval, rtol=1e-8, atol=1e-10)
    if not sol.success:
        raise RuntimeError(f"solve_ivp fallito per {system}: {sol.message}")
    U = sol.y.T.copy()
    return x, sol.t, U, cfg["true"]


def run_external_system(system, seed, smoke):
    """Stessa struttura di V8.run_system, con dati esterni; protocollo
    (funzioni e gate) interamente importato da V8."""
    x, t, U, true_c = simulate_external(system, seed, smoke)
    wx, wt = 1.0, 0.30
    K = 60 if smoke else 200
    rng = np.random.default_rng(seed + 101)
    xc = rng.uniform(x[0] + wx, x[-1] - wx, K)
    tc = rng.uniform(t[0] + wt + 0.05, t[-1] - wt, K)
    centers = list(zip(xc, tc))
    ustd = float(U.std())

    F0 = V8.weak_features_v8(x, t, U, wx, wt, centers)
    A0, b0 = V8.build_Ab(F0)
    cvec = np.array([true_c.get(k, 0.0) for k in V8.TERMS])
    r_gt = float(np.linalg.norm(A0 @ cvec - b0) / np.linalg.norm(b0))
    out = {"solver": SOLVER_LABEL,
           "r_GT_preflight": r_gt,
           "preflight_open": bool(r_gt < V8.GATE_R_GT),
           "true_coeffs": true_c, "K_windows": K,
           "grid": {"Nx": len(x), "Nt": len(t)}, "sigma": {}}
    if not out["preflight_open"]:
        out["skipped"] = "pre-flight r_GT non superato"
        return out

    sigmas = V8.SIGMAS[:3] if smoke else V8.SIGMAS
    for sigma in sigmas:
        if sigma == 0.0:
            A, b = A0, b0
        else:
            noise_rng = np.random.default_rng(seed + int(sigma * 1e4))
            Un = U + noise_rng.normal(0.0, sigma * ustd, U.shape)
            Fn = V8.weak_features_v8(x, t, Un, wx, wt, centers)
            A, b = V8.build_Ab(Fn)
        sel_rng = np.random.default_rng(seed + 7 + int(sigma * 1e4))
        support, freqs = V8.stability_selection(A, b, sel_rng)
        coeffs = V8.refit(A, b, support)
        resid = V8.fit_rel_resid(A, b, coeffs)
        ev = V8.evaluate_discovery(coeffs, true_c)
        ev["fit_rel_resid"] = resid
        ev["gate_pass"] = bool(ev["gate_pass"] and resid < V8.GATE_FIT_RESID)
        out["sigma"][str(sigma)] = {
            "support": sorted(V8.TERMS[i] for i in support),
            "coefficients": coeffs, **ev}

    sigma_star = None
    for sigma in sigmas:
        if not out["sigma"][str(sigma)]["gate_pass"]:
            sigma_star = sigma
            break
    out["sigma_star_first_fail"] = sigma_star

    nulls = {"n_runs": 0, "false_discoveries": 0, "stable_nonempty": 0,
             "detail": []}
    n_seeds = 2 if smoke else V8.N_NULL_SEEDS
    for kind in ("shuffle_t", "phase_surrogate"):
        for ns in range(n_seeds):
            nrng = np.random.default_rng(1000 + 97 * ns
                                         + (0 if kind == "shuffle_t" else 7))
            Un = V8.null_field(U, kind, nrng)
            Fn = V8.weak_features_v8(x, t, Un, wx, wt, centers)
            An, bn = V8.build_Ab(Fn)
            sel_rng = np.random.default_rng(555 + ns)
            support, _ = V8.stability_selection(An, bn, sel_rng)
            coeffs_n = V8.refit(An, bn, support)
            resid_n = V8.fit_rel_resid(An, bn, coeffs_n)
            stable_nonempty = len(support) > 0
            fd = bool(stable_nonempty and resid_n < V8.GATE_FIT_RESID)
            nulls["n_runs"] += 1
            nulls["stable_nonempty"] += int(stable_nonempty)
            nulls["false_discoveries"] += int(fd)
            nulls["detail"].append({
                "kind": kind, "seed": ns,
                "stable_support": sorted(V8.TERMS[i] for i in support),
                "fit_rel_resid": resid_n, "false_discovery": fd})
    nulls["fdr"] = nulls["false_discoveries"] / max(1, nulls["n_runs"])
    nulls["stable_nonempty_rate"] = nulls["stable_nonempty"] / max(1, nulls["n_runs"])
    out["nulls"] = nulls
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    t0 = time.time()
    OUT.mkdir(exist_ok=True)
    runtime_guard = RGB.enforce_runtime_guard(strict=True)

    results = {"run": "CDE_V8_EXTERNAL_SOLVER_REPLICATION_V0",
               "seed": args.seed, "smoke": args.smoke,
               "solver": SOLVER_LABEL,
               "protocol_frozen_from": "CDE_PDE_DISCOVERY_V8 v"
                                       + V8.PROTOCOL_VERSION,
               "systems": {}}
    for system in EXTERNAL_SYSTEMS:
        print(f"== {system} (solver esterno) ==")
        res = run_external_system(system, args.seed, args.smoke)
        results["systems"][system] = res
        (OUT / "results_partial.json").write_text(json.dumps(results, indent=2))
        if "skipped" in res:
            print(f"   SKIP: r_GT={res['r_GT_preflight']:.2e}")
            continue
        for sig, r in res["sigma"].items():
            print(f"   sigma={sig}: support={r['support']} "
                  f"err={r['coef_rel_err_max']:.2%} gate={r['gate_pass']}")
        print(f"   sigma*: {res['sigma_star_first_fail']} | FDR: "
              f"{res['nulls']['fdr']:.2f} | stabili-non-vuoti pre-gate: "
              f"{res['nulls']['stable_nonempty_rate']:.2f}")

    results["elapsed_s"] = round(time.time() - t0, 2)
    suffix = "_smoke" if args.smoke else ""
    res_path = OUT / f"results{suffix}.json"
    res_path.write_text(json.dumps(results, indent=2))
    envelope = {
        "run": "CDE_V8_EXTERNAL_SOLVER_REPLICATION_V0",
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "results_sha256": hashlib.sha256(res_path.read_bytes()).hexdigest(),
        "seed": args.seed,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "solver": SOLVER_LABEL,
        "platform": platform.platform(),
        "git_commit": _git_commit(),
        "runtime_guard": runtime_guard,
        "human_review_required": True,
    }
    (OUT / f"evidence_envelope{suffix}.json").write_text(
        json.dumps(envelope, indent=2))

    card = ["# Claim card — CDE_V8_EXTERNAL_SOLVER_REPLICATION_V0", ""]
    for system, res in results["systems"].items():
        if "skipped" in res:
            card.append(f"- {system}: SKIP (r_GT {res['r_GT_preflight']:.2e})")
            continue
        clean = res["sigma"].get("0.0", {})
        card.append(f"- **{system}** [FD4+RK45]: r_GT={res['r_GT_preflight']:.2e}; "
                    f"support={clean.get('support')} "
                    f"gate(sigma=0)={clean.get('gate_pass')}; "
                    f"sigma*={res['sigma_star_first_fail']}; "
                    f"FDR={res['nulls']['fdr']:.2f}")
    card += ["", "Dati generati con method-of-lines FD4 + scipy RK45: "
             "catena numerica indipendente dall'ETDRK4 spettrale di V8. "
             "Protocollo v1.1 congelato, importato da V8 senza ridefinizioni.",
             "", "Claim boundary: come V8; rimossa l'obiezione 'stesso "
             "generatore' per Burgers e Fisher-KPP."]
    (OUT / f"claim_card{suffix}.md").write_text("\n".join(card))
    print(f"\nOutput in {OUT}  ({results['elapsed_s']}s)")


if __name__ == "__main__":
    main()
