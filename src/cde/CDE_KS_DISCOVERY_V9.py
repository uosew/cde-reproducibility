#!/usr/bin/env python3
"""CDE_KS_DISCOVERY_V9 — Kuramoto-Sivashinsky come test aggiuntivo (fase 2).

KS: u_t = -u u_x - u_xx - u_xxxx su [0, 32*pi) periodico (regime caotico).
E' il test piu' duro finora: il termine u_xx ha coefficiente NEGATIVO
(anti-diffusione, inietta energia) e u_xxxx stabilizza — la libreria deve
distinguere i due su un attrattore caotico.

Struttura (stessa disciplina V7->V8):
  Track D4 — l'identita'  int u_xxxx psi = int u psi_xxxx  viene validata su
    funzioni analitiche note (trig mix e gaussiana, derivate quarte esatte)
    PRIMA di toccare KS; la derivata quarta del bump e' derivata
    analiticamente (Faa' di Bruno) e verificata contro differenze finite.
    Gate come il track S della V7: err rel < 1e-6 o ordine di convergenza.

  Discovery KS — protocollo **v1.1 CONGELATO**: stlsq_support, bic_of,
    null_field, gate e costanti sono IMPORTATI da CDE_PDE_DISCOVERY_V8.
    Unica estensione dichiarata upfront: libreria a 8 termini
    (i 7 di V8 + u_xxxx). Le funzioni che dipendono dalla lista termini
    (stability/refit/residuo/valutazione) sono le stesse di V8
    parametrizzate sulla lista: logica identica riga per riga.
    Preflight r_GT < 1e-3 obbligatorio; scala rumore e nulli come V8.

Claim boundary: come V8 (PDE 1D periodiche, solver spettrale, rumore
gaussiano di misura); KS aggiunge il caso caotico con termine instabile.
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
from scipy.integrate import quad

BASE = Path(__file__).resolve().parent
ART = BASE.parent.parent / "artifacts"      # public layout (cde-reproducibility)
PAPER = BASE.parent.parent / "paper"
ROOT = BASE.parent
OUT = ART / "cde_ks_discovery_v9_out"

_spec7 = importlib.util.spec_from_file_location(
    "v7", BASE / "CDE_WEAK_OPERATOR_COMPONENTWISE_IDENTITY_V7.py")
V7 = importlib.util.module_from_spec(_spec7)
_spec7.loader.exec_module(V7)

_spec8 = importlib.util.spec_from_file_location(
    "v8", BASE / "CDE_PDE_DISCOVERY_V8.py")
V8 = importlib.util.module_from_spec(_spec8)
_spec8.loader.exec_module(V8)

_specg = importlib.util.spec_from_file_location(
    "runtime_guard_bootstrap", BASE / "runtime_guard_bootstrap.py")
RGB = importlib.util.module_from_spec(_specg)
_specg.loader.exec_module(RGB)

TERMS9 = V8.TERMS + ("u_xxxx",)          # estensione dichiarata upfront
KS_TRUE = {"uu_x": -1.0, "u_xx": -1.0, "u_xxxx": -1.0}
KS_L = 32.0 * np.pi


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


# ----------------------------------------------------------------------------
# Derivata quarta del bump: b = exp(g), g = -1/(1-s^2)  (Faa' di Bruno)
# b'''' = b * (g4 + 4 g1 g3 + 3 g2^2 + 6 g1^2 g2 + g1^4)
# con g4 = -24 (1 + 10 s^2 + 5 s^4) / (1-s^2)^5
# ----------------------------------------------------------------------------

def bump_d4phi(s):
    s = np.asarray(s, float)
    out = np.zeros_like(s)
    m = np.abs(s) < 1.0
    sm = s[m]
    g1 = V7.Bump._g1(sm)
    g2 = V7.Bump._g2(sm)
    g3 = V7.Bump._g3(sm)
    g4 = -24.0 * (1.0 + 10.0 * np.square(sm) + 5.0 * np.power(sm, 4)) \
        / np.power(1.0 - np.square(sm), 5)
    out[m] = V7.Bump.phi(sm) * (g4 + 4.0 * g1 * g3 + 3.0 * np.square(g2)
                                + 6.0 * np.square(g1) * g2 + np.power(g1, 4))
    return out


def track_D4(smoke: bool) -> dict:
    """Identita' D4 su funzioni analitiche, stile track S della V7."""
    out = {"configs": {}, "d4phi_check": None}

    # 0) verifica indipendente di bump_d4phi contro differenze finite di d3phi
    # riferimento FD di 2o ordine: con 20001 punti l'errore del RIFERIMENTO
    # scende a ~1e-6 (a 2001 punti dominava l'errore FD, non la formula)
    s = np.linspace(-0.95, 0.95, 20001)
    h = s[1] - s[0]
    fd4 = np.gradient(V7.Bump.d3phi(s), h)
    an4 = bump_d4phi(s)
    scale = np.abs(an4).max()
    err_d4 = float(np.abs(fd4 - an4)[500:-500].max() / scale)
    out["d4phi_check"] = {"max_rel_err_vs_fd": err_d4, "pass": err_d4 < 1e-4}

    # 1) identita' su funzioni analitiche con derivata quarta esatta
    a, b = 1.2, 5.0
    c, w = 0.5 * (a + b), 0.5 * (b - a)
    Ns = [65, 129, 257] if smoke else [65, 129, 257, 513, 1025]

    def u_trig(x):
        return np.sin(x) + 0.4 * np.cos(2.0 * x) + 0.2 * np.sin(3.0 * x + 0.5)

    def u4_trig(x):
        return np.sin(x) + 0.4 * 16.0 * np.cos(2.0 * x) \
            + 0.2 * 81.0 * np.sin(3.0 * x + 0.5)

    s2 = 0.5

    def u_gauss(x):
        return np.exp(-np.square(x - np.pi) / s2)

    def u4_gauss(x):
        aa = 1.0 / s2
        xx = x - np.pi
        return (12.0 * aa ** 2 - 48.0 * aa ** 3 * np.square(xx)
                + 16.0 * aa ** 4 * np.power(xx, 4)) * u_gauss(x)

    for name, u, u4 in (("trig_mix", u_trig, u4_trig),
                        ("gaussian", u_gauss, u4_gauss)):
        ref = quad(lambda t: u4(t) * V7.Bump.phi((t - c) / w), a, b,
                   epsabs=1e-13, epsrel=1e-13, limit=400)[0]
        for rule in ("trapezoid", "simpson"):
            errs, hs = [], []
            for N in Ns:
                x = np.linspace(a, b, N)
                sx = (x - c) / w
                rhs = V7.integ_grid(u(x) * bump_d4phi(sx) / w ** 4, x, rule)
                errs.append(abs(rhs - ref) / abs(ref))
                hs.append((b - a) / (N - 1))
            g = V7.gate_config(errs, hs, V7.Bump.theoretical_order[rule])
            g["rel_errs"] = errs
            g["Ns"] = Ns
            out["configs"][f"{name}/bump/D4_uxxxx/{rule}"] = g

    out["gate_pass"] = (out["d4phi_check"]["pass"]
                        and all(v["pass"] for v in out["configs"].values()))
    return out


# ----------------------------------------------------------------------------
# Simulazione KS (ETDRK4 reale di V7: L = k^2 - k^4)
# ----------------------------------------------------------------------------

def simulate_ks(seed: int, smoke: bool):
    """Risoluzione full decisa in preflight (2026-07-29, PRIMA della
    discovery): la feature u_xxxx richiede Nx=2048 + frame ogni 0.1 +
    finestre 12x7.5 per r_GT ~ 8e-6 (a 1024/0.25/8x5 il preflight resta
    ~8e-2: quadratura di psi'''' su campo caotico)."""
    Nx = 512 if smoke else 2048
    x = np.linspace(0.0, KS_L, Nx, endpoint=False)
    kf = np.fft.fftfreq(Nx, d=1.0 / Nx) * (2.0 * np.pi / KS_L)
    k2 = np.square(kf)
    L_hat = (k2 - np.square(k2)) + 0.0j          # k^2 - k^4
    kc = 1.0j * kf
    dealias = (np.abs(np.fft.fftfreq(Nx, d=1.0 / Nx)) < Nx / 3.0).astype(float)
    rng = np.random.default_rng(seed)
    u0 = 0.1 * rng.standard_normal(Nx)
    u0 = np.real(np.fft.ifft(np.fft.fft(u0) * (np.abs(kf) < 1.5)))

    def nonlin(v):
        u = np.real(np.fft.ifft(v))
        return -0.5 * kc * np.fft.fft(np.square(u))

    dt = 0.05
    T_trans, T_keep = (30.0, 40.0) if smoke else (60.0, 100.0)
    save_every = 5 if smoke else 2                # full: frame ogni 0.1
    U_all = V7.etdrk4(u0, L_hat, nonlin, dt,
                      int(round((T_trans + T_keep) / dt)), save_every, dealias)
    t_all = np.arange(U_all.shape[0]) * dt * save_every
    keep = t_all >= T_trans                       # scarta il transiente
    U = U_all[keep]
    t = t_all[keep] - t_all[keep][0]
    return x, t, U


# ----------------------------------------------------------------------------
# Feature a 8 termini + selezione: logica v1.1 parametrizzata su TERMS9
# ----------------------------------------------------------------------------

def weak_features_v9(x, t, U, wx, wt, centers, rule="simpson"):
    ig = V7.integ_grid
    cols = {k: [] for k in ("b_time",) + TERMS9}
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
        d4px = bump_d4phi(sx) / wx ** 4
        pt = V7.Bump.phi(st)
        dpt = V7.Bump.dphi(st) / wt

        def II(F, gx, gt):
            inner = np.array([ig(F[i] * gx, xs, rule)
                              for i in range(F.shape[0])])
            return ig(inner * gt, ts, rule)

        cols["b_time"].append(-II(Uw, px, dpt))
        cols["u"].append(II(Uw, px, pt))
        cols["u^2"].append(II(Uw2, px, pt))
        cols["u^3"].append(II(Uw3, px, pt))
        cols["u_x"].append(-II(Uw, dpx, pt))
        cols["u_xx"].append(II(Uw, d2px, pt))
        cols["u_xxx"].append(-II(Uw, d3px, pt))
        cols["u_xxxx"].append(II(Uw, d4px, pt))       # identita' D4 (pari)
        cols["uu_x"].append(-0.5 * II(Uw2, dpx, pt))
    return {k: np.array(v) for k, v in cols.items()}


def build_Ab9(F):
    return np.column_stack([F[k] for k in TERMS9]), F["b_time"]


def stability_selection9(A, b, rng):
    """Identica a V8.stability_selection, con TERMS9 (8 colonne)."""
    n = len(b)
    m = max(8, int(round(V8.STAB_FRAC * n)))
    counts = np.zeros(len(TERMS9))
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


def refit9(A, b, support):
    if not support:
        return {}
    idx = sorted(support)
    c, *_ = np.linalg.lstsq(A[:, idx], b, rcond=None)
    return {TERMS9[i]: float(ci) for i, ci in zip(idx, c)}


def fit_rel_resid9(A, b, coeffs):
    if not coeffs:
        return 1.0
    idx = [TERMS9.index(k) for k in coeffs]
    c = np.array([coeffs[k] for k in coeffs])
    return float(np.linalg.norm(A[:, idx] @ c - b) / np.linalg.norm(b))


def run_ks(seed, smoke):
    x, t, U = simulate_ks(seed, smoke)
    wx, wt = 12.0, 7.5                            # deciso in preflight
    K = 60 if smoke else 200
    rng = np.random.default_rng(seed + 101)
    xc = rng.uniform(x[0] + wx, x[-1] - wx, K)
    tc = rng.uniform(t[0] + wt + 0.5, t[-1] - wt, K)
    centers = list(zip(xc, tc))
    ustd = float(U.std())

    F0 = weak_features_v9(x, t, U, wx, wt, centers)
    A0, b0 = build_Ab9(F0)
    cvec = np.array([KS_TRUE.get(k, 0.0) for k in TERMS9])
    r_gt = float(np.linalg.norm(A0 @ cvec - b0) / np.linalg.norm(b0))
    out = {"r_GT_preflight": r_gt,
           "preflight_open": bool(r_gt < V8.GATE_R_GT),
           "true_coeffs": KS_TRUE, "K_windows": K,
           "grid": {"Nx": len(x), "Nt": len(t), "L": KS_L,
                    "u_std": ustd}, "sigma": {}}
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
            Fn = weak_features_v9(x, t, Un, wx, wt, centers)
            A, b = build_Ab9(Fn)
        sel_rng = np.random.default_rng(seed + 7 + int(sigma * 1e4))
        support, freqs = stability_selection9(A, b, sel_rng)
        coeffs = refit9(A, b, support)
        resid = fit_rel_resid9(A, b, coeffs)
        ev = V8.evaluate_discovery(coeffs, KS_TRUE)
        ev["fit_rel_resid"] = resid
        ev["gate_pass"] = bool(ev["gate_pass"] and resid < V8.GATE_FIT_RESID)
        out["sigma"][str(sigma)] = {
            "support": sorted(TERMS9[i] for i in support),
            "frequencies": {TERMS9[i]: round(float(f), 3)
                            for i, f in enumerate(freqs)},
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
            Fn = weak_features_v9(x, t, Un, wx, wt, centers)
            An, bn = build_Ab9(Fn)
            sel_rng = np.random.default_rng(555 + ns)
            support, _ = stability_selection9(An, bn, sel_rng)
            coeffs_n = refit9(An, bn, support)
            resid_n = fit_rel_resid9(An, bn, coeffs_n)
            stable_nonempty = len(support) > 0
            fd = bool(stable_nonempty and resid_n < V8.GATE_FIT_RESID)
            nulls["n_runs"] += 1
            nulls["stable_nonempty"] += int(stable_nonempty)
            nulls["false_discoveries"] += int(fd)
            nulls["detail"].append({
                "kind": kind, "seed": ns,
                "stable_support": sorted(TERMS9[i] for i in support),
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

    print("== Track D4: identita' u_xxxx ==")
    resD4 = track_D4(args.smoke)
    print(f"   d4phi vs FD: err={resD4['d4phi_check']['max_rel_err_vs_fd']:.2e}"
          f" | gate_pass={resD4['gate_pass']}")

    results = {"run": "CDE_KS_DISCOVERY_V9", "seed": args.seed,
               "smoke": args.smoke,
               "protocol": {"frozen_from": "CDE_PDE_DISCOVERY_V8 v"
                                           + V8.PROTOCOL_VERSION,
                            "terms": TERMS9,
                            "library_extension": "u_xxxx (dichiarata upfront, "
                                                 "validata dal track D4)"},
               "track_D4": resD4, "ks": {}}

    if not resD4["gate_pass"]:
        results["ks"] = {"skipped": "track D4 non passato"}
        print("== KS SALTATO: D4 non validata ==")
    else:
        print("== KS: discovery (protocollo v1.1 congelato) ==")
        res = run_ks(args.seed, args.smoke)
        results["ks"] = res
        if "skipped" in res:
            print(f"   SKIP: r_GT={res['r_GT_preflight']:.2e}")
        else:
            print(f"   r_GT preflight: {res['r_GT_preflight']:.2e}")
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
        "run": "CDE_KS_DISCOVERY_V9",
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "results_sha256": hashlib.sha256(res_path.read_bytes()).hexdigest(),
        "seed": args.seed,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "platform": platform.platform(),
        "git_commit": _git_commit(),
        "runtime_guard": runtime_guard,
        "human_review_required": True,
    }
    (OUT / f"evidence_envelope{suffix}.json").write_text(
        json.dumps(envelope, indent=2))

    card = ["# Claim card — CDE_KS_DISCOVERY_V9", "",
            f"- Track D4: gate_pass={resD4['gate_pass']} "
            f"(d4phi verificata vs FD, identita' su 2 funzioni analitiche)"]
    res = results["ks"]
    if "skipped" in res:
        card.append(f"- KS: SKIP ({res['skipped']})")
    else:
        clean = res["sigma"].get("0.0", {})
        card.append(
            f"- **Kuramoto-Sivashinsky** (L=32pi, caotico): "
            f"r_GT={res['r_GT_preflight']:.2e}; sigma=0 -> "
            f"support={clean.get('support')} gate={clean.get('gate_pass')}; "
            f"sigma*={res['sigma_star_first_fail']}; "
            f"FDR nulli={res['nulls']['fdr']:.2f}")
    card += ["", "Protocollo v1.1 congelato (importato da V8); unica "
             "estensione dichiarata: termine u_xxxx, validato dal track D4 "
             "PRIMA della discovery. Il termine u_xx va recuperato con "
             "coefficiente NEGATIVO (anti-diffusione).",
             "", "Claim boundary: come V8; aggiunto il caso caotico con "
             "termine instabile."]
    (OUT / f"claim_card{suffix}.md").write_text("\n".join(card))
    print(f"\nOutput in {OUT}  ({results['elapsed_s']}s)")


if __name__ == "__main__":
    main()
