#!/usr/bin/env python3
"""CDE — Dress rehearsal termico (design EXPERIMENTAL_DESIGN_THERMAL_V0).

Prova generale SINTETICA e DICHIARATA TALE dell'esperimento reale di
diffusione termica: valida il pipeline (ladder v2, core v1.1 invariato)
su barra NON periodica alle specifiche hardware della camera termica,
PRIMA di misurare. Se il preflight rifiuta a queste specifiche, va
cambiato il protocollo di misura, non il gate.

Generatore (fisica vera, ignota al pipeline):
  v_t = (D(v) v_x)_x - beta v,  D(v) = alpha (1 + gamma v)
  alpha = 9.7e-5 m^2/s (alluminio, tabulato), beta = 0.02 1/s,
  gamma = 0 (braccio "linear") oppure 0.004 1/K (braccio "vardiff"),
  barra L = 0.4 m, estremi isolati (Neumann), FD esplicito fine.

Degradazione a specifica camera (FLIR-like, dichiarata nel design):
  160 px, 5 Hz, rumore gaussiano sigma 0.3 C, deriva lenta 0.2 C,
  quantizzazione 0.1 C. 5 condizioni iniziali per braccio (hot-spot in
  posizioni/ampiezze diverse), 120 s di puro rilassamento.

Libreria (design emendato 2026-07-31, tutta sample-only):
  {const, v, v^2, v_x, v_xx, v v_x, (v v_x)_x}   con
  (v v_x)_x = (1/2)(v^2)_xx -> (1/2) int v^2 psi''.
Supporto vero: linear {v, v_xx}; vardiff {v, v_xx, (v v_x)_x}.

Ladder: preflight non-oracle (P1 quadratura, P2 bump vs bump^2,
P3 holdout; gate 5%) -> selezione v1.1 -> gate residuo -> nulli
(shuffle_t + phase surrogate) -> transfer tra IC (coefficienti congelati
da IC0 sulle altre) -> swap test relativo 2x -> verdetto ladder.

Verdetti del rehearsal (go/no-go per l'hardware):
  R1 preflight apre alle specifiche camera; R2 braccio linear: supporto
  {v, v_xx} con alpha entro il 5% del tabulato; R3 braccio vardiff:
  (v v_x)_x rilevato; R4 transfer tra IC; R5 nulli 0 FD.

Esito V0 (committato 167d2f78): NO-GO — preflight rifiuta tutti i
dataset alle specifiche base. Variante --v1 (protocollo di misura
corretto, stessa pipeline): spot iniziali larghi (5-8 cm), analisi su
[10, 70] s (scarto transiente sotto-risolto e coda rumorosa), finestre
spaziali WX=0.08 m (64 px), correzione deriva con riferimento freddo
(media dei 10 px piu' freddi per frame). Il confronto V0/V1 e' la
specifica quantitativa del protocollo di misura reale.

Uso: python CDE_THERMAL_DRESS_REHEARSAL_V0.py [--v1]
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
OUT = ART / "cde_thermal_dress_rehearsal_v0_out"

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


V7 = _load("v7", "CDE_WEAK_OPERATOR_COMPONENTWISE_IDENTITY_V7.py")
W = _load("wlc", "CDE_V10_WRONG_LIBRARY_V0.py")
NOP = _load("nop", "CDE_V10_NONORACLE_PREFLIGHT_V0.py")
LAD = _load("lad", "CDE_V10_CLAIM_LADDER_AUDIT_V0.py")
V8 = W.V8

GATE = V8.GATE_FIT_RESID
TERMS = ("const", "v", "v2", "v_x", "v_xx", "vv_x", "div_vv_x")
ALPHA, BETA = 9.7e-5, 0.02
GAMMA_VARDIFF = 0.004
L_BAR, T_END = 0.4, 120.0
CAM_PX, CAM_HZ = 160, 5.0
NOISE_C, DRIFT_C, QUANT_C = 0.3, 0.2, 0.1
ICS = ((0.10, 60.0, 0.02), (0.20, 80.0, 0.03), (0.30, 50.0, 0.02),
       (0.14, 70.0, 0.04), (0.26, 45.0, 0.025))   # (centro, dT, larghezza)
WX, WT, K = 0.05, 4.0, 200
# variante V1 (protocollo di misura corretto; mutati in main con --v1)
V1_ICS = ((0.10, 60.0, 0.05), (0.20, 80.0, 0.06), (0.30, 50.0, 0.05),
          (0.14, 70.0, 0.08), (0.26, 45.0, 0.06))
T_CROP = None                                     # (t_min, t_max) in V1
DRIFT_REF = False                                 # riferimento freddo V1
BIN = 1            # V2: binning temporale x5 (rumore /sqrt(5))
POOLED = False     # V2: fit congiunto IC0..3, transfer su IC4 holdout


def _git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


# ----------------------------------------------------------------------------
# Generatore FD non periodico (Neumann) + degradazione a specifica camera
# ----------------------------------------------------------------------------

def simulate_bar(ic, gamma):
    Nx = 800
    x = np.linspace(0.0, L_BAR, Nx)
    dx = x[1] - x[0]
    dt = 0.2 * dx * dx / (ALPHA * (1.0 + gamma * 100.0))
    xc, dT, wid = ic
    v = dT * np.exp(-0.5 * np.square((x - xc) / wid))
    nsteps = int(round(T_END / dt))
    save_every = max(1, int(round(1.0 / (CAM_HZ * dt))))
    frames, times = [], []
    for n in range(nsteps + 1):
        if n % save_every == 0:
            frames.append(v.copy())
            times.append(n * dt)
        D = ALPHA * (1.0 + gamma * v)
        vx = np.gradient(v, dx)
        flux = D * vx
        div = np.gradient(flux, dx)
        v = v + dt * (div - BETA * v)
        v[0], v[-1] = v[1], v[-2]          # Neumann (estremi isolati)
    return x, np.array(times), np.array(frames)


def degrade(x, t, V, seed):
    rng = np.random.default_rng(seed)
    xs = np.linspace(x[0], x[-1], CAM_PX)
    Vc = np.stack([np.interp(xs, x, fr) for fr in V])
    drift = DRIFT_C * np.sin(2 * np.pi * t / (t[-1] * 2.0))[:, None]
    Vn = Vc + drift + rng.normal(0.0, NOISE_C, Vc.shape)
    Vq = np.round(Vn / QUANT_C) * QUANT_C
    if DRIFT_REF:
        # correzione deriva con OGGETTO DI RIFERIMENTO non riscaldato nel
        # frame (protocollo reale): misura la deriva pura della camera,
        # non la barra. La variante "pixel piu' freddi della barra"
        # (provata in un'iterazione precedente) contamina la dinamica:
        # il riferimento contiene segnale di campo lontano IC-dipendente
        # e la sottrazione inietta un forcing d'(t) fuori libreria.
        ref = drift + rng.normal(0.0, NOISE_C / 4.0, (len(t), 1))
        Vq = Vq - np.round(ref / QUANT_C) * QUANT_C
    td = t
    if BIN > 1:
        n = (len(td) // BIN) * BIN
        Vq = Vq[:n].reshape(-1, BIN, Vq.shape[1]).mean(axis=1)
        td = td[:n].reshape(-1, BIN).mean(axis=1)
    if T_CROP is not None:
        keep = (td >= T_CROP[0]) & (td <= T_CROP[1])
        return xs, Vq[keep], td[keep]
    return xs, Vq, td


# ----------------------------------------------------------------------------
# Feature deboli sample-only per la libreria termica
# ----------------------------------------------------------------------------

def weak_features_thermal(x, t, V, centers, rule="simpson", fam=None):
    fam = fam or NOP.BumpA
    ig = V7.integ_grid
    cols = {k: [] for k in ("b_time",) + TERMS}
    for (xc, tc) in centers:
        mx = (x >= xc - WX) & (x <= xc + WX)
        mt = (t >= tc - WT) & (t <= tc + WT)
        xs, ts = x[mx], t[mt]
        sx = (xs - xc) / WX
        st = (ts - tc) / WT
        Vw = V[np.ix_(mt, mx)]
        Vw2 = np.square(Vw)
        px = fam.phi(sx)
        dpx = fam.dphi(sx) / WX
        d2px = fam.d2phi(sx) / WX ** 2
        pt = fam.phi(st)
        dpt = fam.dphi(st) / WT
        one = np.ones_like(Vw)

        def II(F, gx, gt):
            inner = np.array([ig(F[i] * gx, xs, rule)
                              for i in range(F.shape[0])])
            return ig(inner * gt, ts, rule)

        cols["b_time"].append(-II(Vw, px, dpt))
        cols["const"].append(II(one, px, pt))
        cols["v"].append(II(Vw, px, pt))
        cols["v2"].append(II(Vw2, px, pt))
        cols["v_x"].append(-II(Vw, dpx, pt))
        cols["v_xx"].append(II(Vw, d2px, pt))
        cols["vv_x"].append(-0.5 * II(Vw2, dpx, pt))
        cols["div_vv_x"].append(0.5 * II(Vw2, d2px, pt))
    return {k: np.array(v) for k, v in cols.items()}


def centers_for(x, t, seed):
    rng = np.random.default_rng(seed + 101)
    xc = rng.uniform(x[0] + WX, x[-1] - WX, K)
    tc = rng.uniform(t[0] + WT + 1.0, t[-1] - WT, K)
    return list(zip(xc, tc))


def to_Ab(F):
    return np.column_stack([F[k] for k in TERMS]), F["b_time"]


def ls_resid(A, b):
    c, *_ = np.linalg.lstsq(A, b, rcond=None)
    return float(np.linalg.norm(A @ c - b) / np.linalg.norm(b)), c


def preflight(x, t, V, centers):
    F_s = weak_features_thermal(x, t, V, centers, "simpson")
    F_t = weak_features_thermal(x, t, V, centers, "trapezoid")
    F_b2 = weak_features_thermal(x, t, V, centers, "simpson", NOP.Bump2)
    A, b = to_Ab(F_s)
    A2, b2 = to_Ab(F_b2)
    p1 = NOP.rel_col_diff(F_s, F_t, TERMS)
    r1, c_a = ls_resid(A, b)
    p2 = max(float(np.linalg.norm(A2 @ c_a - b2) / np.linalg.norm(b2)),
             r1)
    rng = np.random.default_rng(2026)
    perm = rng.permutation(len(b))
    nh = int(round(0.3 * len(b)))
    hold, train = perm[:nh], perm[nh:]
    ct, *_ = np.linalg.lstsq(A[train], b[train], rcond=None)
    p3 = float(np.linalg.norm(A[hold] @ ct - b[hold])
               / np.linalg.norm(b[hold]))
    return {"P1": p1, "P2": p2, "P3": p3,
            "open": bool(p3 < GATE)}, F_s


def select_thermal(F, sel_seed):
    A, b = to_Ab(F)
    rng = np.random.default_rng(sel_seed)
    support, freqs = W.stability_selection_t(A, b, rng, len(TERMS))
    coeffs = W.refit_t(A, b, support, TERMS)
    resid = W.resid_t(A, b, coeffs, TERMS)
    return {"support": sorted(TERMS[i] for i in support),
            "coefficients": coeffs, "fit_rel_resid": resid}


def transfer_resid(coeffs, F):
    if not coeffs:
        return 1.0
    terms = sorted(coeffs)
    A = np.column_stack([F[k] for k in terms])
    c = np.array([coeffs[k] for k in terms])
    return float(np.linalg.norm(A @ c - F["b_time"])
                 / np.linalg.norm(F["b_time"]))


def swap_rel(F, support, rel_base):
    A, b = to_Ab(F)
    hits = []
    S = sorted(support)
    for j in S:
        for k in TERMS:
            if k in support:
                continue
            alt = [z for z in S if z != j] + [k]
            idx = [TERMS.index(z) for z in alt]
            c, *_ = np.linalg.lstsq(A[:, idx], b, rcond=None)
            r = float(np.linalg.norm(A[:, idx] @ c - b)
                      / np.linalg.norm(b))
            if r < 2.0 * rel_base:
                hits.append({"drop": j, "add": k, "resid": round(r, 5)})
    return {"alternatives_within_2x": hits,
            "not_identifiable": bool(hits)}


def run_arm(name, gamma, true_support):
    print(f"== braccio {name} (gamma={gamma}) ==", flush=True)
    datasets = []
    for i, ic in enumerate(ICS):
        x, t, V = simulate_bar(ic, gamma)
        xs, Vd, td = degrade(x, t, V, seed=300 + i)
        centers = centers_for(xs, td, seed=7 + i)
        datasets.append((xs, td, Vd, centers))
    arm = {"ics": {}, "nulls": {"n": 0, "fd": 0}, "transfer": {}}

    feats = []
    for i, (xs, t, Vd, centers) in enumerate(datasets):
        pf, F = preflight(xs, t, Vd, centers)
        sel = select_thermal(F, sel_seed=7 + i)
        sel["preflight"] = pf
        sel["support_true"] = bool(set(sel["support"]) == true_support)
        arm["ics"][f"ic{i}"] = sel
        feats.append(F)
        print(f"   ic{i}: preflight open={pf['open']} (P3={pf['P3']:.4f})"
              f" support={sel['support']} resid={sel['fit_rel_resid']:.4f}"
              f" | alpha_hat={sel['coefficients'].get('v_xx')}",
              flush=True)

    # nulli su ic0
    xs, t, Vd, centers = datasets[0]
    for ns in range(5):
        for kind in ("shuffle_t", "phase_surrogate"):
            nrng = np.random.default_rng(1000 + 97 * ns
                                         + (0 if kind == "shuffle_t" else 7))
            Vn = V8.null_field(Vd, kind, nrng)
            Fn = weak_features_thermal(xs, t, Vn, centers)
            rn = select_thermal(Fn, sel_seed=555 + ns)
            fd = bool(rn["support"] and rn["fit_rel_resid"] < GATE)
            arm["nulls"]["n"] += 1
            arm["nulls"]["fd"] += int(fd)
    print(f"   nulli: FD {arm['nulls']['fd']}/{arm['nulls']['n']}")

    # transfer: coefficienti congelati da ic0 sulle altre IC
    c0 = arm["ics"]["ic0"]["coefficients"]
    trs = [transfer_resid(c0, feats[j]) for j in range(1, len(feats))]
    arm["transfer"] = {"r": [round(r, 5) for r in trs],
                       "all_pass": bool(all(r < GATE for r in trs))}
    print(f"   transfer ic0 -> ic1..4: "
          f"{['%.3f' % r for r in trs]} pass={arm['transfer']['all_pass']}")

    # swap relativo su ic0
    sw = swap_rel(feats[0], set(arm["ics"]["ic0"]["support"]),
                  arm["ics"]["ic0"]["fit_rel_resid"])
    arm["swap_ic0"] = sw
    print(f"   swap 2x su ic0: NI={sw['not_identifiable']}")

    # V2: fit congiunto su IC0..3 (popolazione di traiettorie),
    # transfer sull'IC4 mai vista
    Fp = {k: np.concatenate([feats[i][k] for i in range(4)])
          for k in feats[0]}
    selp = select_thermal(Fp, sel_seed=7)
    selp["support_true"] = bool(set(selp["support"]) == true_support)
    r_hold = transfer_resid(selp["coefficients"], feats[4])
    swp = swap_rel(Fp, set(selp["support"]), selp["fit_rel_resid"])
    arm["pooled"] = {**selp, "transfer_holdout_ic4": r_hold,
                     "transfer_pass": bool(r_hold < GATE),
                     "swap": swp}
    print(f"   POOLED ic0..3: support={selp['support']} "
          f"resid={selp['fit_rel_resid']:.4f} "
          f"alpha_hat={selp['coefficients'].get('v_xx')} | "
          f"holdout ic4 r={r_hold:.4f} | NI={swp['not_identifiable']}")

    if POOLED:
        st = {"operator_valid": True,
              "numerical_preflight": all(v["preflight"]["open"]
                                         for v in arm["ics"].values()),
              "support_stable": bool(selp["support"]),
              "fit_gate": bool(selp["fit_rel_resid"] < GATE),
              "transfer_gate": bool(r_hold < GATE),
              "identifiability_gate": not swp["not_identifiable"],
              "replication": True}
    else:
        st = {"operator_valid": True,
              "numerical_preflight": all(v["preflight"]["open"]
                                         for v in arm["ics"].values()),
              "support_stable": bool(arm["ics"]["ic0"]["support"]),
              "fit_gate": bool(arm["ics"]["ic0"]["fit_rel_resid"] < GATE),
              "transfer_gate": arm["transfer"]["all_pass"],
              "identifiability_gate": not sw["not_identifiable"],
              "replication": True}
    arm["ladder"] = {**LAD.ladder_verdict(st), "state": st}
    print(f"   LADDER: {arm['ladder']['verdict']}")
    return arm


def main():
    global ICS, WX, T_CROP, DRIFT_REF, BIN, POOLED
    ap = argparse.ArgumentParser()
    ap.add_argument("--v1", action="store_true",
                    help="protocollo di misura corretto (vedi docstring)")
    ap.add_argument("--v2", action="store_true",
                    help="v1 + fit congiunto multi-IC con holdout "
                         "(popolazione di traiettorie; senza binning: "
                         "il binning x5 riduceva i frame per finestra "
                         "sotto la soglia di quadratura temporale)")
    args = ap.parse_args()
    if args.v1 or args.v2:
        ICS, WX = V1_ICS, 0.08
        T_CROP, DRIFT_REF = (10.0, 70.0), True
    if args.v2:
        POOLED = True
    t0 = time.time()
    OUT.mkdir(exist_ok=True)
    guard = RGB.enforce_runtime_guard(strict=True)

    res = {"run": "CDE_THERMAL_DRESS_REHEARSAL_V0",
           "variant": "v2" if args.v2 else "v1" if args.v1 else "v0",
           "design": "EXPERIMENTAL_DESIGN_THERMAL_V0_2026_07_31.md "
                     "(+ emendamento libreria)",
           "synthetic_and_declared": True,
           "camera_spec": {"px": CAM_PX, "hz": CAM_HZ,
                           "noise_C": NOISE_C, "drift_C": DRIFT_C,
                           "quant_C": QUANT_C},
           "physics": {"alpha": ALPHA, "beta": BETA,
                       "gamma_vardiff": GAMMA_VARDIFF},
           "terms": list(TERMS), "arms": {}}

    res["arms"]["linear"] = run_arm("linear", 0.0, {"v", "v_xx"})
    res["arms"]["vardiff"] = run_arm("vardiff", GAMMA_VARDIFF,
                                     {"v", "v_xx", "div_vv_x"})

    lin = res["arms"]["linear"]
    var = res["arms"]["vardiff"]
    src_l = lin["pooled"] if POOLED else lin["ics"]["ic0"]
    src_v = var["pooled"] if POOLED else var["ics"]["ic0"]
    a_hat = src_l["coefficients"].get("v_xx", float("nan"))
    tr_ok = (bool(lin["pooled"]["transfer_pass"]
                  and var["pooled"]["transfer_pass"]) if POOLED
             else bool(lin["transfer"]["all_pass"]
                       and var["transfer"]["all_pass"]))
    res["rehearsal_verdicts"] = {
        "R1_preflight_opens": bool(all(
            v["preflight"]["open"]
            for arm in res["arms"].values() for v in arm["ics"].values())),
        "R2_linear_support_and_alpha": bool(
            src_l["support_true"]
            and abs(a_hat - ALPHA) / ALPHA < 0.05),
        "R2_alpha_hat": a_hat, "R2_alpha_true": ALPHA,
        "R3_vardiff_detected": bool("div_vv_x" in src_v["support"]),
        "R4_transfer": tr_ok,
        "R5_nulls": bool(lin["nulls"]["fd"] == 0
                         and var["nulls"]["fd"] == 0),
    }
    res["elapsed_s"] = round(time.time() - t0, 2)
    print(f"== VERDETTI REHEARSAL == {res['rehearsal_verdicts']}")

    rp = OUT / ("results_v2.json" if args.v2
                else "results_v1.json" if args.v1 else "results.json")
    rp.write_text(json.dumps(res, indent=2))
    env = {"run": "CDE_THERMAL_DRESS_REHEARSAL_V0",
           "timestamp_utc": datetime.now(timezone.utc)
                                    .strftime("%Y-%m-%dT%H:%M:%SZ"),
           "results_sha256": hashlib.sha256(rp.read_bytes()).hexdigest(),
           "python_version": platform.python_version(),
           "numpy_version": np.__version__,
           "platform": platform.platform(),
           "git_commit": _git_commit(),
           "runtime_guard": guard,
           "human_review_required": True}
    (OUT / ("evidence_envelope_v2.json" if args.v2
            else "evidence_envelope_v1.json" if args.v1
            else "evidence_envelope.json")).write_text(
        json.dumps(env, indent=2))
    print(f"Output in {OUT}  ({res['elapsed_s']}s)")


if __name__ == "__main__":
    main()
