#!/usr/bin/env python3
"""CDE V11 — Virtual Instrument Qualification, fase 1 (mappa tolleranza).

PREREGISTRATION_V11_VIRTUAL_INSTRUMENT_2026_07_31.md @ 538b1611.
Gemello digitale della camera termica: dal campo ideale (cache unica,
Nx=800, campionamento denso 45 Hz) genera frame degradati lungo 12 assi
preregistrati + 5 scenari combinati; per ogni configurazione l'INTERA
ladder v2 (base = GO del rehearsal V2, pooled IC0..3 + holdout IC4)
emette il verdetto. Output: mappa di tolleranza + HARDWARE_SPEC_ENVELOPE
con la regola di derivazione preregistrata (ultimo CLAIM con
|err alpha|<5% e supporto esatto; margine 2x conservativo).

Ordine di degradazione (dichiarato): campionamento temporale con jitter
-> interpolazione spaziale a N px (con moto e errore scala) -> PSF ->
non-uniformita' emissivita' (pattern fisso della camera) -> rumore NETD
-> deriva differenziale residua (comune rimossa dal riferimento) ->
pixel morti + interpolazione ingestion -> saturazione -> quantizzazione.

Uso: python CDE_V11_VIRTUAL_INSTRUMENT_QUALIFICATION_V0.py [--smoke]
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
OUT = ART / "cde_v11_virtual_instrument_v0_out"
SPEC_MD = BASE / "HARDWARE_SPEC_ENVELOPE.md"
PREREG = "PREREGISTRATION_V11_VIRTUAL_INSTRUMENT_2026_07_31.md @ 538b1611"

RGB_spec = importlib.util.spec_from_file_location(
    "runtime_guard_bootstrap", BASE / "runtime_guard_bootstrap.py")
RGB = importlib.util.module_from_spec(RGB_spec)
RGB_spec.loader.exec_module(RGB)

import numpy as np                                    # noqa: E402
from scipy.ndimage import gaussian_filter1d           # noqa: E402


def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, BASE / fname)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


R = _load("reh", "CDE_THERMAL_DRESS_REHEARSAL_V0.py")
LAD = R.LAD
GATE = R.GATE
L_BAR = R.L_BAR

BASE_CFG = {"px": 160, "psf": 0.0, "netd": 0.3, "quant": 0.1, "hz": 5.0,
            "jitter_ms": 0.0, "drift": 0.2, "dead": 0.0, "nonunif": 0.0,
            "motion": 0.0, "scale_err": 0.0, "sat": None}

AXES = {
    "A1_px": ("px", [40, 80, 120, 160, 240, 320], "higher"),
    "A2_psf": ("psf", [0.0, 1.0, 2.0, 4.0, 8.0], "lower"),
    "A3_netd": ("netd", [0.05, 0.1, 0.3, 0.5, 1.0], "lower"),
    "A4_quant": ("quant", [0.01, 0.1, 0.5, 1.0], "lower"),
    "A5_hz": ("hz", [0.5, 1.0, 2.0, 5.0, 8.7], "higher"),
    "A6_jitter": ("jitter_ms", [0.0, 20.0, 50.0, 100.0, 200.0], "lower"),
    "A7_drift": ("drift", [0.0, 0.2, 0.5, 1.0, 2.0], "lower"),
    "A8_dead": ("dead", [0.0, 0.005, 0.02, 0.05], "lower"),
    "A9_nonunif": ("nonunif", [0.0, 0.01, 0.03, 0.05, 0.10], "lower"),
    "A10_motion": ("motion", [0.0, 0.5, 1.0, 2.0], "lower"),
    "A11_scale": ("scale_err", [0.0, 0.01, 0.03, 0.05], "lower"),
    "A12_sat": ("sat", [None, 60.0, 40.0], "lower"),
}

COMBINED = {
    "C1_noise_psf": {"netd": 0.5, "psf": 2.0},
    "C2_drift_nonunif": {"drift": 1.0, "nonunif": 0.03},
    "C3_lowhz_jitter": {"hz": 2.0, "jitter_ms": 100.0},
    "C4_motion_dead": {"motion": 1.0, "dead": 0.02},
    "C5_worst_plausible": {"psf": 2.0, "quant": 0.5, "netd": 0.5},
}


def _git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


# ----------------------------------------------------------------------------
# Cache dei campi ideali (densi nel tempo) — una sola volta
# ----------------------------------------------------------------------------

def build_cache():
    R.CAM_HZ = 45.0                       # campionamento denso per il twin
    cache = []
    for ic in R.V1_ICS:
        x, t, V = R.simulate_bar(ic, 0.0)
        cache.append((x, t, V))
    return cache


# ----------------------------------------------------------------------------
# Gemello digitale
# ----------------------------------------------------------------------------

def camera_pattern(px, seed, smooth):
    rng = np.random.default_rng(seed)
    p = gaussian_filter1d(rng.standard_normal(px), smooth)
    return p / max(1e-12, np.abs(p).max())


def degrade_twin(x, t, V, cfg, seed):
    rng = np.random.default_rng(seed)
    hz = cfg["hz"]
    t_nom = np.arange(0.0, R.T_END, 1.0 / hz)
    jit = rng.normal(0.0, cfg["jitter_ms"] / 1000.0, len(t_nom))
    t_true = np.clip(t_nom + jit, t[0], t[-1])
    idx = np.searchsorted(t, t_true)
    idx = np.clip(idx, 1, len(t) - 1)
    w = (t_true - t[idx - 1]) / (t[idx] - t[idx - 1])
    Vt = V[idx - 1] * (1 - w[:, None]) + V[idx] * w[:, None]

    px = cfg["px"]
    xs_true = np.linspace(x[0], x[-1], px)
    if cfg["motion"] > 0:
        px_size = L_BAR / px
        shift = cfg["motion"] * px_size * np.sin(2 * np.pi * t_nom / 60.0)
        Vc = np.stack([np.interp(xs_true + s, x, fr)
                       for s, fr in zip(shift, Vt)])
    else:
        Vc = np.stack([np.interp(xs_true, x, fr) for fr in Vt])
    x_pipe = xs_true * (1.0 + cfg["scale_err"])

    if cfg["psf"] > 0:
        Vc = gaussian_filter1d(Vc, cfg["psf"], axis=1)
    if cfg["nonunif"] > 0:
        Vc = Vc * (1.0 + cfg["nonunif"]
                   * camera_pattern(px, 42, px / 20.0)[None, :])
    Vc = Vc + rng.normal(0.0, cfg["netd"], Vc.shape)
    if cfg["drift"] > 0:
        # comune rimossa dal riferimento (resta il suo rumore);
        # 10% differenziale non correggibile
        diff = 0.1 * cfg["drift"] * np.sin(2 * np.pi * t_nom / 170.0 + 1.0)
        Vc = Vc + diff[:, None] + rng.normal(0.0, cfg["netd"] / 4.0,
                                             (len(t_nom), 1))
    if cfg["dead"] > 0:
        mask = np.random.default_rng(43).random(px) < cfg["dead"]
        good = ~mask
        if mask.any() and good.sum() > 2:
            Vc[:, mask] = np.stack(
                [np.interp(xs_true[mask], xs_true[good], fr[good])
                 for fr in Vc])
    if cfg["sat"] is not None:
        Vc = np.minimum(Vc, cfg["sat"])
    Vc = np.round(Vc / cfg["quant"]) * cfg["quant"]
    keep = (t_nom >= 10.0) & (t_nom <= 70.0)
    return x_pipe, t_nom[keep], Vc[keep]


# ----------------------------------------------------------------------------
# Valutazione di una configurazione (pooled, come rehearsal V2)
# ----------------------------------------------------------------------------

def eval_config(cache, cfg, n_nulls=2):
    R.WX = 0.08
    R.WT = float(min(max(4.0, 22.0 / cfg["hz"]), 25.0))
    feats, pf_open = [], []
    for i, (x, t, V) in enumerate(cache):
        xp, tp, Vd = degrade_twin(x, t, V, cfg, seed=300 + i)
        centers = R.centers_for(xp, tp, seed=7 + i)
        if not centers:
            return {"verdict": "REJECTED_PREFLIGHT", "note": "no windows"}
        pf, F = R.preflight(xp, tp, Vd, centers)
        pf_open.append(pf["open"])
        feats.append((F, xp, tp, Vd, centers))

    Fp = {k: np.concatenate([feats[i][0][k] for i in range(4)])
          for k in feats[0][0]}
    selp = R.select_thermal(Fp, sel_seed=7)
    r_hold = R.transfer_resid(selp["coefficients"], feats[4][0])
    swp = R.swap_rel(Fp, set(selp["support"]), selp["fit_rel_resid"])

    nf = 0
    F0, xp, tp, Vd, centers = feats[0]
    for ns in range(n_nulls):
        kind = "shuffle_t" if ns % 2 == 0 else "phase_surrogate"
        nrng = np.random.default_rng(1000 + ns)
        Vn = R.V8.null_field(Vd, kind, nrng)
        Fn = R.weak_features_thermal(xp, tp, Vn, centers)
        rn = R.select_thermal(Fn, sel_seed=555 + ns)
        nf += int(bool(rn["support"]) and rn["fit_rel_resid"] < GATE)

    st = {"operator_valid": True,
          "numerical_preflight": all(pf_open),
          "support_stable": bool(selp["support"]),
          "fit_gate": bool(selp["fit_rel_resid"] < GATE),
          "transfer_gate": bool(r_hold < GATE),
          "identifiability_gate": not swp["not_identifiable"],
          "replication": True}
    v = LAD.ladder_verdict(st)
    a_hat = selp["coefficients"].get("v_xx")
    return {"verdict": v["verdict"], "blocked_at": v["blocked_at"],
            "support": selp["support"],
            "support_exact": bool(set(selp["support"]) == {"v", "v_xx"}),
            "alpha_hat": a_hat,
            "alpha_err": (abs(a_hat - R.ALPHA) / R.ALPHA
                          if a_hat else None),
            "fit_resid": selp["fit_rel_resid"],
            "r_holdout": r_hold,
            "preflight_open_all": all(pf_open),
            "nulls_fd": nf}


def qualifies(res):
    return bool(res.get("verdict") == "CLAIM" and res.get("support_exact")
                and res.get("alpha_err") is not None
                and res["alpha_err"] < 0.05)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true",
                    help="solo asse A3 + C1 (verifica percorsi)")
    args = ap.parse_args()
    t0 = time.time()
    OUT.mkdir(exist_ok=True)
    guard = RGB.enforce_runtime_guard(strict=True)

    print("== cache campi ideali (45 Hz densi) ==", flush=True)
    cache = build_cache()
    print(f"   5 IC pronte ({time.time() - t0:.0f}s)", flush=True)

    axes = ({"A3_netd": AXES["A3_netd"]} if args.smoke else AXES)
    combined = ({"C1_noise_psf": COMBINED["C1_noise_psf"]}
                if args.smoke else COMBINED)

    res = {"run": "CDE_V11_VIRTUAL_INSTRUMENT_QUALIFICATION_V0",
           "smoke": args.smoke, "prereg": PREREG,
           "base_cfg": {k: v for k, v in BASE_CFG.items()},
           "axes": {}, "combined": {}, "spec_thresholds": {}}

    for aname, (param, values, direction) in axes.items():
        res["axes"][aname] = {}
        for val in values:
            cfg = dict(BASE_CFG)
            cfg[param] = val
            r_ = eval_config(cache, cfg)
            res["axes"][aname][str(val)] = r_
            ae = (f"{r_['alpha_err']:.3f}" if r_.get("alpha_err")
                  is not None else "n/d")
            print(f"   {aname}={val}: {r_['verdict']} "
                  f"(err_a={ae}, hold={r_.get('r_holdout', 1):.3f})",
                  flush=True)
        # soglia preregistrata: ultimo valore qualificante nello sweep
        ok_vals = [v for v in values
                   if qualifies(res["axes"][aname][str(v)])]
        if direction == "higher":
            thr = min(ok_vals) if ok_vals else None
        else:
            numeric = [v for v in ok_vals if v is not None]
            thr = (max(numeric) if numeric
                   else (None if not ok_vals else "none"))
        res["spec_thresholds"][aname] = {"param": param,
                                        "direction": direction,
                                        "threshold": thr,
                                        "qualifying_values": ok_vals}

    for cname, over in combined.items():
        cfg = dict(BASE_CFG)
        cfg.update(over)
        r_ = eval_config(cache, cfg)
        res["combined"][cname] = {"overrides": {k: v for k, v
                                                in over.items()}, **r_}
        print(f"   {cname}: {r_['verdict']}", flush=True)

    res["elapsed_s"] = round(time.time() - t0, 2)

    # HARDWARE_SPEC_ENVELOPE (margine 2x conservativo, regola preregistrata)
    if not args.smoke:
        sp = res["spec_thresholds"]

        def half(v):
            return None if v is None else v / 2.0

        lines = [
            "# Hardware Specification Envelope — camera termica",
            "",
            f"Generato da CDE_V11 il "
            f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%MZ')} "
            f"(commit `{_git_commit()}`), regola preregistrata: soglia = "
            "ultimo valore CLAIM con err(alpha)<5% e supporto esatto; "
            "specifica = soglia con margine 2x conservativo.",
            "",
            "| Parametro | Soglia misurata | Specifica (margine 2x) |",
            "|---|---|---|"]
        rows = [
            ("Pixel utili sul campione (barra 0.4 m)", "A1_px",
             lambda v: f">= {v}", lambda v: f">= {2 * v}"),
            ("PSF (sigma) [px]", "A2_psf",
             lambda v: f"<= {v}", lambda v: f"<= {half(v)}"),
            ("NETD/rumore [°C]", "A3_netd",
             lambda v: f"<= {v}", lambda v: f"<= {half(v)}"),
            ("Quantizzazione [°C]", "A4_quant",
             lambda v: f"<= {v}", lambda v: f"<= {half(v)}"),
            ("Frame rate [Hz]", "A5_hz",
             lambda v: f">= {v}", lambda v: f">= {2 * v}"),
            ("Jitter timestamp [ms]", "A6_jitter",
             lambda v: f"<= {v}", lambda v: f"<= {half(v)}"),
            ("Deriva (con riferimento nel frame) [°C]", "A7_drift",
             lambda v: f"<= {v}", lambda v: f"<= {half(v)}"),
            ("Pixel morti [%]", "A8_dead",
             lambda v: f"<= {100 * v}", lambda v: f"<= {50 * v}"),
            ("Non-uniformita' emissivita' [%]", "A9_nonunif",
             lambda v: f"<= {100 * v}", lambda v: f"<= {50 * v}"),
            ("Moto residuo [px]", "A10_motion",
             lambda v: f"<= {v}", lambda v: f"<= {half(v)}"),
            ("Errore scala px/m [%]", "A11_scale",
             lambda v: f"<= {100 * v}", lambda v: f"<= {50 * v}"),
        ]
        for label, key, fmt_t, fmt_s in rows:
            thr = sp[key]["threshold"]
            if thr is None:
                lines.append(f"| {label} | nessun valore qualificante | "
                             "fuori sweep: vincolo aperto |")
            else:
                lines.append(f"| {label} | {fmt_t(thr)} | {fmt_s(thr)} |")
        sat = sp["A12_sat"]["qualifying_values"]
        lines += [
            "",
            f"Saturazione: valori qualificanti {sat} (None = nessun clip; "
            "il campione arriva a ~80 °C: range radiometrico >= 120 °C "
            "consigliato).",
            "",
            "Requisiti non negoziabili emersi dal rehearsal: accesso a "
            "frame RADIOMETRICI numerici (no RGB ricostruito), oggetto di "
            "riferimento non riscaldato nel campo visivo, niente smoothing "
            "interno irreversibile.",
            "",
            "Scenari combinati: " + ", ".join(
                f"{k}={res['combined'][k]['verdict']}"
                for k in res["combined"]),
        ]
        SPEC_MD.write_text("\n".join(lines) + "\n")

    suffix = "_smoke" if args.smoke else ""
    rp = OUT / f"results{suffix}.json"
    rp.write_text(json.dumps(res, indent=2))
    env = {"run": "CDE_V11_VIRTUAL_INSTRUMENT_QUALIFICATION_V0",
           "timestamp_utc": datetime.now(timezone.utc)
                                    .strftime("%Y-%m-%dT%H:%M:%SZ"),
           "results_sha256": hashlib.sha256(rp.read_bytes()).hexdigest(),
           "python_version": platform.python_version(),
           "numpy_version": np.__version__,
           "platform": platform.platform(),
           "git_commit": _git_commit(),
           "runtime_guard": guard,
           "human_review_required": True}
    (OUT / f"evidence_envelope{suffix}.json").write_text(
        json.dumps(env, indent=2))
    print(f"Output in {OUT}"
          + ("" if args.smoke else f" + {SPEC_MD.name}")
          + f"  ({res['elapsed_s']}s)")


if __name__ == "__main__":
    main()
