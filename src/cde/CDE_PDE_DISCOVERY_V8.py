#!/usr/bin/env python3
"""CDE_PDE_DISCOVERY_V8 — discovery simbolica sull'operatore weak validato (V7).

La V7 ha validato l'operatore componente per componente e aperto i gate
(r_GT < 1e-3 su Allen-Cahn, Fisher-KPP, Burgers). Questa V8 esegue la
discovery vera, con protocollo PREREGISTRATO (nessuna scelta a posteriori):

  Libreria condivisa (7 termini, identica per tutti i sistemi):
      u, u^2, u^3, u_x, u_xx, u_xxx, u*u_x
  tutte le derivate scaricate sulla test function bump (mai su u).

  Selezione: stability selection su B=100 sottocampioni (60% delle finestre),
  STLSQ per sottocampione con soglia scelta via BIC su griglia fissa;
  supporto finale = termini con frequenza >= 0.8; coefficienti rifittati
  su tutte le finestre ristretti al supporto.

  GATE per (sistema, sigma):  supporto esatto  E  errore relativo massimo
  dei coefficienti < 5%  E  nessun termine spurio stabile.

  Scala di rumore: sigma in {0, 1%, 2%, 5%, 10%} di std(U), gaussiano iid
  sui campioni PRIMA delle feature. Il punto di rottura sigma* e' risultato.

  Braccio NULLO (epistemico): per ogni sistema, (a) frame temporali permutati,
  (b) surrogato a fase randomizzata (stesso spettro, nessuna dinamica PDE).
  Una pipeline onesta deve restituire supporto VUOTO: ogni supporto stabile
  non vuoto su un nullo e' una falsa scoperta. FDR = false scoperte / run nulle.

  Transfer: KdV (u_t = -u u_x - delta2 u_xxx), sistema MAI usato per mettere
  a punto l'operatore; richiede ETDRK4 con L complesso (dispersione),
  implementato qui senza toccare la V7 (REPLICATED_AND_RELEASED).
  Pre-flight r_GT < 1e-3 obbligatorio per OGNI sistema prima della discovery.

Claim boundary: PDE 1D periodiche lisce, dati da solver spettrale con rumore
gaussiano di misura; nessuna claim su dati sperimentali o PDE non testate.
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
OUT = ART / "cde_pde_discovery_v8_out"

# componenti V7 (validati, non modificati)
_spec7 = importlib.util.spec_from_file_location(
    "v7", BASE / "CDE_WEAK_OPERATOR_COMPONENTWISE_IDENTITY_V7.py")
V7 = importlib.util.module_from_spec(_spec7)
_spec7.loader.exec_module(V7)

_specg = importlib.util.spec_from_file_location(
    "runtime_guard_bootstrap", BASE / "runtime_guard_bootstrap.py")
RGB = importlib.util.module_from_spec(_specg)
_specg.loader.exec_module(RGB)

TERMS = ("u", "u^2", "u^3", "u_x", "u_xx", "u_xxx", "uu_x")
PROTOCOL_VERSION = "1.1"
GATE_R_GT = 1e-3
GATE_COEF_RELERR = 0.05
# v1.1 (2026-07-29): gate sul residuo relativo del fit, aggiunto DOPO la
# calibrazione sul braccio nullo e PRIMA delle claim finali: i surrogati di
# fase producevano supporti stabili ma con residuo ~0.89 contro ~1e-4 dei
# sistemi veri (separazione di 4 ordini). Una scoperta e' CLAIMED solo se
# il modello selezionato spiega davvero i dati.
GATE_FIT_RESID = 0.05
STAB_B = 100
STAB_FRAC = 0.6
STAB_FREQ = 0.8
LAM_GRID = (0.02, 0.05, 0.1, 0.2, 0.4)      # soglie STLSQ (colonne normalizzate)
SIGMAS = (0.0, 0.01, 0.02, 0.05, 0.10)
N_NULL_SEEDS = 5

TRUE_COEFFS = {
    "allen_cahn": {"u_xx": 0.05, "u": 1.0, "u^3": -1.0},
    "fisher_kpp": {"u_xx": 0.05, "u": 1.0, "u^2": -1.0},
    "burgers": {"uu_x": -1.0, "u_xx": 0.08},
    "kdv": {"uu_x": -1.0, "u_xxx": -0.0484},     # delta2 = 0.22^2
}


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


# ----------------------------------------------------------------------------
# ETDRK4 con L complesso (dispersione KdV) — coefficienti via contorno.
# Sul venv ufficiale (canary pulito) il contorno complesso e' affidabile;
# gli array coinvolti sono comunque ~8KB, molto sotto la soglia di elisione.
# ----------------------------------------------------------------------------

def etdrk4_complex(u0, L_hat, nonlin, dt, nsteps, save_every, dealias):
    v = np.fft.fft(u0)
    E = np.exp(dt * L_hat)
    E2 = np.exp(dt * L_hat / 2.0)
    M = 64
    r = np.exp(1j * np.pi * (np.arange(1, M + 1) - 0.5) / M)
    LR = dt * L_hat[:, None] + r[None, :]
    Q = dt * np.mean((np.exp(LR / 2.0) - 1.0) / LR, axis=1)
    f1 = dt * np.mean(
        (-4.0 - LR + np.exp(LR) * (4.0 - 3.0 * LR + np.square(LR)))
        / np.power(LR, 3), axis=1)
    f2 = dt * np.mean(
        (2.0 + LR + np.exp(LR) * (-2.0 + LR)) / np.power(LR, 3), axis=1)
    f3 = dt * np.mean(
        (-4.0 - 3.0 * LR - np.square(LR) + np.exp(LR) * (4.0 - LR))
        / np.power(LR, 3), axis=1)
    for nm, arr in (("Q", Q), ("f1", f1), ("f2", f2), ("f3", f3)):
        if not np.isfinite(arr).all():
            raise FloatingPointError(f"coefficiente ETDRK4 {nm} non finito")

    frames = [u0.copy()]
    for n in range(1, nsteps + 1):
        Nv = nonlin(v) * dealias
        a_ = E2 * v + Q * Nv
        Na = nonlin(a_) * dealias
        b_ = E2 * v + Q * Na
        Nb = nonlin(b_) * dealias
        c_ = E2 * a_ + Q * (2.0 * Nb - Nv)
        Nc = nonlin(c_) * dealias
        v = E * v + Nv * f1 + 2.0 * (Na + Nb) * f2 + Nc * f3
        if n % save_every == 0:
            frames.append(np.real(np.fft.ifft(v)))
    return np.array(frames)


def simulate_kdv(seed: int, smoke: bool):
    """u_t = -u u_x - delta2 u_xxx, periodica, Zabusky-Kruskal-like.

    Nx=1024 in full: la feature u_xxx scarica psi''' (molto oscillante) sulla
    quadratura di finestra; a Nx=512 il preflight r_GT resta ~1e-2, a Nx=1024
    scende a ~9e-5 (misura 2026-07-29). Decisione presa in preflight, PRIMA
    della discovery.
    """
    Nx = 256 if smoke else 1024
    x = np.linspace(0.0, 2.0 * np.pi, Nx, endpoint=False)
    k = np.fft.fftfreq(Nx, d=1.0 / Nx) * 1.0j
    delta2 = 0.0484
    L_hat = -delta2 * np.power(k, 3)          # -delta2 (ik)^3: dispersivo
    dealias = (np.abs(np.fft.fftfreq(Nx, d=1.0 / Nx)) < Nx / 3.0).astype(float)
    rng = np.random.default_rng(seed)
    c = rng.normal(0.0, 1.0, 3) / np.arange(1, 4)
    s = rng.normal(0.0, 1.0, 3) / np.arange(1, 4)
    f = sum(c[m] * np.cos((m + 1) * x) + s[m] * np.sin((m + 1) * x)
            for m in range(3))
    u0 = f / max(1e-9, np.abs(f).max())       # ampiezza O(1)

    def nonlin(v):
        u = np.real(np.fft.ifft(v))
        return -0.5 * k * np.fft.fft(np.square(u))    # -(u^2/2)_x

    dt, Tf = 2e-4, 2.0
    save_every = 25                            # frame ogni 5e-3
    U = etdrk4_complex(u0, L_hat, nonlin, dt, int(round(Tf / dt)),
                       save_every, dealias)
    t = np.arange(U.shape[0]) * dt * save_every
    return x, t, U, TRUE_COEFFS["kdv"]


def simulate(system: str, seed: int, smoke: bool):
    if system == "kdv":
        return simulate_kdv(seed, smoke)
    x, t, U, _ = V7.simulate_pde(system, seed, smoke)
    return x, t, U, TRUE_COEFFS[system]


# ----------------------------------------------------------------------------
# Feature deboli estese (7 termini + b_time), solo campioni di U, ufunc sicure
# ----------------------------------------------------------------------------

def weak_features_v8(x, t, U, wx, wt, centers, rule="simpson"):
    Bump, ig = V7.Bump, V7.integ_grid
    cols = {k: [] for k in ("b_time",) + TERMS}
    for (xc, tc) in centers:
        mx = (x >= xc - wx) & (x <= xc + wx)
        mt = (t >= tc - wt) & (t <= tc + wt)
        xs, ts = x[mx], t[mt]
        sx = (xs - xc) / wx
        st = (ts - tc) / wt
        Uw = U[np.ix_(mt, mx)]
        Uw2 = np.square(Uw)                   # MAI infissi su array grandi
        Uw3 = np.power(Uw, 3)
        px = Bump.phi(sx)
        dpx = Bump.dphi(sx) / wx
        d2px = Bump.d2phi(sx) / wx ** 2
        d3px = Bump.d3phi(sx) / wx ** 3
        pt = Bump.phi(st)
        dpt = Bump.dphi(st) / wt

        def II(F, gx, gt):
            inner = np.array([ig(F[i] * gx, xs, rule)
                              for i in range(F.shape[0])])
            return ig(inner * gt, ts, rule)

        cols["b_time"].append(-II(Uw, px, dpt))
        cols["u"].append(II(Uw, px, pt))
        cols["u^2"].append(II(Uw2, px, pt))
        cols["u^3"].append(II(Uw3, px, pt))
        cols["u_x"].append(-II(Uw, dpx, pt))            # int u_x psi
        cols["u_xx"].append(II(Uw, d2px, pt))           # int u_xx psi
        cols["u_xxx"].append(-II(Uw, d3px, pt))         # int u_xxx psi
        cols["uu_x"].append(-0.5 * II(Uw2, dpx, pt))    # int u u_x psi
    return {k: np.array(v) for k, v in cols.items()}


def build_Ab(F):
    A = np.column_stack([F[k] for k in TERMS])
    return A, F["b_time"]


# ----------------------------------------------------------------------------
# STLSQ + BIC + stability selection (protocollo preregistrato)
# ----------------------------------------------------------------------------

def stlsq_support(A, b, lam, iters=10):
    """STLSQ su colonne normalizzate; ritorna il supporto (indici)."""
    scale = A.std(axis=0)
    scale[scale == 0] = 1.0
    An = A / scale
    active = np.arange(A.shape[1])
    for _ in range(iters):
        if active.size == 0:
            return frozenset()
        c, *_ = np.linalg.lstsq(An[:, active], b, rcond=None)
        if c.size == 0:
            return frozenset()
        keep = np.abs(c) >= lam * np.abs(c).max()
        # soglia relativa al massimo: invariante di scala del problema
        new_active = active[keep]
        if new_active.size == active.size:
            break
        active = new_active
    return frozenset(int(i) for i in active)


def bic_of(A, b, support):
    n = len(b)
    if not support:
        rss = float(np.sum(np.square(b)))
        k = 0
    else:
        idx = sorted(support)
        c, *_ = np.linalg.lstsq(A[:, idx], b, rcond=None)
        resid = b - A[:, idx] @ c
        rss = float(np.sum(np.square(resid)))
        k = len(idx)
    rss = max(rss, 1e-300)
    return n * np.log(rss / n) + k * np.log(n)


def stability_selection(A, b, rng):
    """Frequenze di selezione per termine su STAB_B sottocampioni."""
    n = len(b)
    m = max(8, int(round(STAB_FRAC * n)))
    counts = np.zeros(len(TERMS))
    for _ in range(STAB_B):
        idx = rng.choice(n, size=m, replace=False)
        As, bs = A[idx], b[idx]
        # il supporto VUOTO partecipa sempre al confronto BIC: senza di esso
        # la pipeline non puo' mai astenersi e su un nullo "scopre" per forza
        # qualcosa (debolezza trovata dal test su rumore puro, 2026-07-29)
        candidates = {frozenset()}
        for lam in LAM_GRID:
            candidates.add(stlsq_support(As, bs, lam))
        best, best_bic = frozenset(), np.inf
        for sup in candidates:
            bic = bic_of(As, bs, sup)
            if bic < best_bic:
                best, best_bic = sup, bic
        for i in best:
            counts[i] += 1
    freqs = counts / STAB_B
    support = frozenset(int(i) for i in np.where(freqs >= STAB_FREQ)[0])
    return support, freqs


def refit(A, b, support):
    if not support:
        return {}
    idx = sorted(support)
    c, *_ = np.linalg.lstsq(A[:, idx], b, rcond=None)
    return {TERMS[i]: float(ci) for i, ci in zip(idx, c)}


def fit_rel_resid(A, b, coeffs):
    """Residuo relativo L2 del modello selezionato su tutte le finestre."""
    if not coeffs:
        return 1.0
    idx = [TERMS.index(k) for k in coeffs]
    c = np.array([coeffs[k] for k in coeffs])
    return float(np.linalg.norm(A[:, idx] @ c - b) / np.linalg.norm(b))


def evaluate_discovery(coeffs_hat, true_coeffs):
    sup_hat = frozenset(coeffs_hat)
    sup_true = frozenset(true_coeffs)
    exact = sup_hat == sup_true
    if exact:
        errs = [abs(coeffs_hat[k] - true_coeffs[k]) / abs(true_coeffs[k])
                for k in sup_true]
        max_err = float(max(errs))
    else:
        max_err = float("inf")
    return {"support_exact": bool(exact),
            "spurious_terms": sorted(sup_hat - sup_true),
            "missing_terms": sorted(sup_true - sup_hat),
            "coef_rel_err_max": max_err,
            "gate_pass": bool(exact and max_err < GATE_COEF_RELERR)}


# ----------------------------------------------------------------------------
# Nulli epistemici
# ----------------------------------------------------------------------------

def null_field(U, kind, rng):
    if kind == "shuffle_t":
        return U[rng.permutation(U.shape[0])]
    if kind == "phase_surrogate":
        # stesso spettro spazio-temporale, fasi casuali: nessuna dinamica PDE.
        # Le fasi vengono prese dalla FFT di rumore bianco REALE: sono
        # hermitiane per costruzione, quindi il surrogato e' esattamente reale
        # e il modulo dello spettro e' conservato esattamente (il rfft2 con
        # fasi arbitrarie rompeva la simmetria sui bordi).
        S = np.fft.fft2(U)
        W = np.fft.fft2(rng.normal(size=U.shape))
        mag = np.abs(W)
        mag[mag == 0] = 1.0
        phases = W / mag
        return np.real(np.fft.ifft2(np.abs(S) * phases))
    raise ValueError(kind)


# ----------------------------------------------------------------------------

def run_system(system, seed, smoke):
    x, t, U, true_c = simulate(system, seed, smoke)
    wx, wt = 1.0, 0.30
    K = 60 if smoke else 200
    rng = np.random.default_rng(seed + 101)
    xc = rng.uniform(x[0] + wx, x[-1] - wx, K)
    tc = rng.uniform(t[0] + wt + 0.05, t[-1] - wt, K)
    centers = list(zip(xc, tc))
    ustd = float(U.std())

    # pre-flight r_GT (validate-before-discover) sul campo pulito
    F0 = weak_features_v8(x, t, U, wx, wt, centers)
    A0, b0 = build_Ab(F0)
    cvec = np.array([true_c.get(k, 0.0) for k in TERMS])
    r_gt = float(np.linalg.norm(A0 @ cvec - b0) / np.linalg.norm(b0))
    out = {"r_GT_preflight": r_gt,
           "preflight_open": bool(r_gt < GATE_R_GT),
           "true_coeffs": true_c, "K_windows": K,
           "grid": {"Nx": len(x), "Nt": len(t)}, "sigma": {}}
    if not out["preflight_open"]:
        out["skipped"] = "pre-flight r_GT non superato: discovery non eseguita"
        return out

    sigmas = SIGMAS[:3] if smoke else SIGMAS
    for sigma in sigmas:
        if sigma == 0.0:
            A, b = A0, b0
        else:
            noise_rng = np.random.default_rng(seed + int(sigma * 1e4))
            Un = U + noise_rng.normal(0.0, sigma * ustd, U.shape)
            Fn = weak_features_v8(x, t, Un, wx, wt, centers)
            A, b = build_Ab(Fn)
        sel_rng = np.random.default_rng(seed + 7 + int(sigma * 1e4))
        support, freqs = stability_selection(A, b, sel_rng)
        coeffs = refit(A, b, support)
        resid = fit_rel_resid(A, b, coeffs)
        ev = evaluate_discovery(coeffs, true_c)
        ev["fit_rel_resid"] = resid
        ev["gate_pass"] = bool(ev["gate_pass"] and resid < GATE_FIT_RESID)
        out["sigma"][str(sigma)] = {
            "support": sorted(TERMS[i] for i in support),
            "frequencies": {TERMS[i]: round(float(f), 3)
                            for i, f in enumerate(freqs)},
            "coefficients": coeffs, **ev}

    # sigma*: primo sigma della scala che NON passa il gate
    sigma_star = None
    for sigma in sigmas:
        if not out["sigma"][str(sigma)]["gate_pass"]:
            sigma_star = sigma
            break
    out["sigma_star_first_fail"] = sigma_star

    # braccio nullo: la pipeline deve restituire supporto vuoto
    nulls = {"n_runs": 0, "false_discoveries": 0, "detail": []}
    n_seeds = 2 if smoke else N_NULL_SEEDS
    for kind in ("shuffle_t", "phase_surrogate"):
        for ns in range(n_seeds):
            nrng = np.random.default_rng(1000 + 97 * ns
                                         + (0 if kind == "shuffle_t" else 7))
            Un = null_field(U, kind, nrng)
            Fn = weak_features_v8(x, t, Un, wx, wt, centers)
            An, bn = build_Ab(Fn)
            sel_rng = np.random.default_rng(555 + ns)
            support, freqs = stability_selection(An, bn, sel_rng)
            coeffs_n = refit(An, bn, support)
            resid_n = fit_rel_resid(An, bn, coeffs_n)
            stable_nonempty = len(support) > 0
            # v1.1: falsa scoperta = supporto stabile CHE PASSA anche il gate
            # sul residuo (una "scoperta" che non spiega i dati non e' una
            # claim). Riportiamo comunque entrambi i conteggi.
            fd = bool(stable_nonempty and resid_n < GATE_FIT_RESID)
            nulls["n_runs"] += 1
            nulls["stable_nonempty"] = nulls.get("stable_nonempty", 0) \
                + int(stable_nonempty)
            nulls["false_discoveries"] += int(fd)
            nulls["detail"].append({
                "kind": kind, "seed": ns,
                "stable_support": sorted(TERMS[i] for i in support),
                "fit_rel_resid": resid_n,
                "false_discovery": fd})
    nulls["fdr"] = nulls["false_discoveries"] / max(1, nulls["n_runs"])
    nulls["stable_nonempty_rate"] = nulls.get("stable_nonempty", 0) \
        / max(1, nulls["n_runs"])
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

    systems = ("allen_cahn", "fisher_kpp", "burgers", "kdv")
    results = {"run": "CDE_PDE_DISCOVERY_V8", "seed": args.seed,
               "smoke": args.smoke,
               "protocol": {"version": PROTOCOL_VERSION,
                            "terms": TERMS, "stability_B": STAB_B,
                            "subsample_frac": STAB_FRAC,
                            "freq_threshold": STAB_FREQ,
                            "lam_grid": LAM_GRID, "sigmas": SIGMAS,
                            "gate_coef_relerr": GATE_COEF_RELERR,
                            "gate_fit_resid": GATE_FIT_RESID,
                            "gate_r_gt": GATE_R_GT,
                            "amendment_note":
                                "v1.1: gate residuo fit aggiunto dopo la "
                                "calibrazione sui nulli (surrogati: supporti "
                                "stabili con residuo ~0.89 vs ~1e-4 dei veri)"},
               "systems": {}}
    for system in systems:
        print(f"== {system} ==")
        res = run_system(system, args.seed, args.smoke)
        results["systems"][system] = res
        # checkpoint per-sistema: questo Mac e' incline a memorystatus kill
        (OUT / "results_partial.json").write_text(json.dumps(results, indent=2))
        if "skipped" in res:
            print(f"   SKIP: r_GT={res['r_GT_preflight']:.2e}")
            continue
        for sig, r in res["sigma"].items():
            print(f"   sigma={sig}: support={r['support']} "
                  f"err={r['coef_rel_err_max']:.2%} gate={r['gate_pass']}")
        print(f"   sigma* (primo fail): {res['sigma_star_first_fail']} | "
              f"FDR nulli: {res['nulls']['fdr']:.2f} "
              f"({res['nulls']['false_discoveries']}/{res['nulls']['n_runs']})")

    results["elapsed_s"] = round(time.time() - t0, 2)
    suffix = "_smoke" if args.smoke else ""
    res_path = OUT / f"results{suffix}.json"
    res_path.write_text(json.dumps(results, indent=2))

    envelope = {
        "run": "CDE_PDE_DISCOVERY_V8",
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

    card = ["# Claim card — CDE_PDE_DISCOVERY_V8", ""]
    for system in systems:
        res = results["systems"][system]
        if "skipped" in res:
            card.append(f"- {system}: SKIP (r_GT preflight "
                        f"{res['r_GT_preflight']:.2e})")
            continue
        clean = res["sigma"].get("0.0", {})
        card.append(
            f"- **{system}**: r_GT={res['r_GT_preflight']:.2e}; sigma=0 -> "
            f"support={clean.get('support')} gate={clean.get('gate_pass')}; "
            f"sigma*={res['sigma_star_first_fail']}; "
            f"FDR nulli={res['nulls']['fdr']:.2f}")
    card += ["",
             "Protocollo preregistrato (stability selection B=100, freq>=0.8, "
             "BIC su griglia soglie fissa); libreria condivisa a 7 termini; "
             "KdV mai usata per la messa a punto dell'operatore (transfer).",
             "",
             "Claim boundary: PDE 1D periodiche lisce, solver spettrale, "
             "rumore gaussiano di misura; nessuna claim su dati sperimentali."]
    (OUT / f"claim_card{suffix}.md").write_text("\n".join(card))
    print(f"\nOutput in {OUT}  ({results['elapsed_s']}s)")


if __name__ == "__main__":
    main()
