#!/usr/bin/env python3
"""CDE Blind PDE — RISOLUTORE (vede solo i dati).

NON importa CDE_BLIND_PDE_GENERATOR_V0.py e NON legge sealed/. Non e' una
raccomandazione: lo scorer ispeziona il sorgente di questo file e fallisce se
vi trova un riferimento alla verita' sigillata.

Per ogni caso applica la pipeline congelata, nell'ordine:

  1. finestre deboli (wx, wt, K fissi; centri da seme derivato dal case_id);
  2. preflight NON-oracle P1/P2/P3 — se chiude, ASTENSIONE senza guardare
     oltre: nessuna legge puo' essere affermata su dati che non reggono
     numericamente l'operatore;
  3. stability selection (STLSQ + BIC su 100 sottocampioni) -> supporto;
     supporto vuoto = ASTENSIONE;
  4. refit e residuo relativo -> se sopra il gate, ASTENSIONE;
  5. transfer sulla SECONDA traiettoria con i coefficienti congelati sulla
     prima -> se sopra il gate, ASTENSIONE;
  6. swap test di identificabilita': se esiste un supporto alternativo che
     spiega i dati entro un fattore dal migliore, NON_IDENTIFICABILE.

Solo se tutti i cancelli passano ed e' identificabile, la decisione e' CLAIM.

Uso: python CDE_BLIND_PDE_RUNNER_V0.py [--caso case_01]
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
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
OUT = ART / "cde_blind_pde_out"
CASES = OUT / "cases"

_g = importlib.util.spec_from_file_location(
    "runtime_guard_bootstrap", BASE / "runtime_guard_bootstrap.py")
RGB = importlib.util.module_from_spec(_g)
_g.loader.exec_module(RGB)

import numpy as np                                        # noqa: E402


def _load(nome, fname):
    spec = importlib.util.spec_from_file_location(nome, BASE / fname)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


V8 = _load("v8", "CDE_PDE_DISCOVERY_V8.py")
NOP = _load("nop", "CDE_V10_NONORACLE_PREFLIGHT_V0.py")

# --- parametri congelati (nessuno scelto dopo aver visto un risultato) -----
TERMS = V8.TERMS                       # 7 termini, invariati dal protocollo v1.1
WX, WT, K = 1.0, 0.30, 200
GATE_P1 = 0.05                         # coerenza di quadratura
GATE_P2 = 0.05                         # coerenza fra famiglie di test function
GATE_P3 = 0.05                         # holdout predittivo (come termografia)
GATE_FIT = V8.GATE_FIT_RESID           # 0.05, ereditato
GATE_TRANSFER = 0.05                   # stesso valore del gate di transfer V10
FATTORE_IDENT = 2.0                    # swap test: alternativa entro 2x
HOLDOUT_SEED = NOP.HOLDOUT_SEED        # 2026
HOLDOUT_FRAC = NOP.HOLDOUT_FRAC        # 0.30
SEME_CENTRI = 4242


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def _centri(x, t, seme):
    rng = np.random.default_rng(seme)
    lo_t = t[0] + WT + 0.05 * (t[-1] - t[0])
    hi_t = t[-1] - WT
    if hi_t <= lo_t or (x[-1] - WX) <= (x[0] + WX):
        return []
    return list(zip(rng.uniform(x[0] + WX, x[-1] - WX, K),
                    rng.uniform(lo_t, hi_t, K)))


def _rr(A, b, c):
    return float(np.linalg.norm(A @ c - b) / max(np.linalg.norm(b), 1e-300))


def _ls(A, b):
    c, *_ = np.linalg.lstsq(A, b, rcond=None)
    return c


def preflight(x, t, U, centers):
    """P1/P2/P3 — nessuno usa la legge vera. Misurano se le colonne deboli
    sono numericamente affidabili e se il modello lineare generalizza a
    finestre non viste."""
    F_as = NOP.weak_features_nop(x, t, U, WX, WT, centers, TERMS, "simpson",
                                 NOP.BumpA)
    F_at = NOP.weak_features_nop(x, t, U, WX, WT, centers, TERMS, "trapezoid",
                                 NOP.BumpA)
    F_bs = NOP.weak_features_nop(x, t, U, WX, WT, centers, TERMS, "simpson",
                                 NOP.Bump2)
    A_a, b_a = NOP.to_Ab(F_as, TERMS)
    A_b, b_b = NOP.to_Ab(F_bs, TERMS)

    p1 = NOP.rel_col_diff(F_as, F_at, TERMS)
    c_a, c_b = _ls(A_a, b_a), _ls(A_b, b_b)
    p2 = max(_rr(A_b, b_b, c_a), _rr(A_a, b_a, c_b))
    rng = np.random.default_rng(HOLDOUT_SEED)
    perm = rng.permutation(len(b_a))
    n_h = max(1, int(round(HOLDOUT_FRAC * len(b_a))))
    hold, train = perm[:n_h], perm[n_h:]
    p3 = _rr(A_a[hold], b_a[hold], _ls(A_a[train], b_a[train]))
    return A_a, b_a, {"P1_quadratura": p1, "P2_famiglie": p2, "P3_holdout": p3}


def swap_test(A, b, supporto, resid_migliore):
    """Esiste un supporto DIVERSO che spiega i dati quasi altrettanto bene?

    Si tolgono a turno i termini selezionati e si cerca il miglior supporto
    fra i rimanenti, di cardinalita' uguale a quella scelta. Se qualcuno
    arriva entro FATTORE_IDENT volte il residuo migliore, i dati non separano
    le due leggi: la risposta corretta e' dichiarare la degenerazione, non
    sceglierne una.
    """
    if not supporto:
        return True, []
    idx_sel = sorted(supporto)
    alternative = []
    for fuori in idx_sel:
        restanti = [i for i in range(len(TERMS)) if i != fuori]
        for combo in itertools.combinations(restanti, len(idx_sel)):
            if set(combo) == set(idx_sel):
                continue
            c = _ls(A[:, list(combo)], b)
            r = _rr(A[:, list(combo)], b, c)
            if r <= FATTORE_IDENT * max(resid_migliore, 1e-12):
                alternative.append({
                    "supporto": sorted(TERMS[i] for i in combo),
                    "resid": round(float(r), 6),
                    "coefficienti": {TERMS[i]: round(float(ci), 6)
                                     for i, ci in zip(combo, c)}})
    visti = {}
    for alt in alternative:
        chiave = tuple(alt["supporto"])
        if chiave not in visti or alt["resid"] < visti[chiave]["resid"]:
            visti[chiave] = alt
    migliori = sorted(visti.values(), key=lambda a: a["resid"])[:5]
    return (len(migliori) == 0), migliori


def risolvi(cid: str) -> dict:
    d = np.load(CASES / f"{cid}.npz")
    x, t, U, U2 = d["x"], d["t"], d["U"], d["U2"]
    seme = SEME_CENTRI + int(cid.split("_")[1])
    out = {"case_id": cid, "Nx": int(len(x)), "Nt": int(len(t))}

    centers = _centri(x, t, seme)
    if not centers:
        out.update(decisione="ABSTAIN_GEOMETRIA",
                   motivo="dominio troppo piccolo per le finestre congelate")
        return out

    A, b, pf = preflight(x, t, U, centers)
    out["preflight"] = {k: round(float(v), 8) for k, v in pf.items()}
    chiusure = [k for k, g in (("P1_quadratura", GATE_P1),
                               ("P2_famiglie", GATE_P2),
                               ("P3_holdout", GATE_P3))
                if not (pf[k] < g)]
    if chiusure:
        out.update(decisione="ABSTAIN_PREFLIGHT", cancelli_chiusi=chiusure)
        return out

    sel_rng = np.random.default_rng(seme + 7)
    supporto, freqs = V8.stability_selection(A, b, sel_rng)
    out["frequenze"] = {TERMS[i]: round(float(f), 3)
                        for i, f in enumerate(freqs)}
    out["supporto"] = sorted(TERMS[i] for i in supporto)
    if not supporto:
        out["decisione"] = "ABSTAIN_SUPPORTO_VUOTO"
        return out

    coeffs = V8.refit(A, b, supporto)
    resid = V8.fit_rel_resid(A, b, coeffs)
    out["coefficienti"] = {k: round(float(v), 8) for k, v in coeffs.items()}
    out["resid_fit"] = round(float(resid), 8)
    if not (resid < GATE_FIT):
        out["decisione"] = "ABSTAIN_GATE_FIT"
        return out

    # transfer: coefficienti CONGELATI sulla prima traiettoria, applicati alla
    # seconda. Nessun refit: sarebbe un'altra domanda.
    centers2 = _centri(x, t, seme + 313)
    F2 = NOP.weak_features_nop(x, t, U2, WX, WT, centers2, TERMS, "simpson",
                               NOP.BumpA)
    A2, b2 = NOP.to_Ab(F2, TERMS)
    cvec = np.array([coeffs.get(k, 0.0) for k in TERMS])
    r_tr = _rr(A2, b2, cvec)
    out["resid_transfer"] = round(float(r_tr), 8)
    if not (r_tr < GATE_TRANSFER):
        out["decisione"] = "ABSTAIN_TRANSFER"
        return out

    ident, alt = swap_test(A, b, supporto, resid)
    out["identificabile"] = bool(ident)
    out["alternative_entro_fattore"] = alt
    out["decisione"] = "CLAIM" if ident else "NOT_IDENTIFIABLE"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--caso", default=None, help="risolve un solo caso")
    a = ap.parse_args()

    manifest = json.loads((CASES / "public_manifest.json").read_text())
    ids = [c["case_id"] for c in manifest["casi"]]
    if a.caso:
        ids = [a.caso]

    t0 = time.time()
    risultati = []
    for cid in ids:
        t1 = time.time()
        r = risolvi(cid)
        r["wall_s"] = round(time.time() - t1, 2)
        risultati.append(r)
        print(f"   {cid}: {r['decisione']:<26} "
              f"supporto={r.get('supporto', [])} ({r['wall_s']}s)")

    res = {"run": "CDE_BLIND_PDE_RUNNER_V0",
           "data": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
           "commit": _git_commit(),
           "python": platform.python_version(), "numpy": np.__version__,
           "parametri_congelati": {
               "TERMS": list(TERMS), "wx": WX, "wt": WT, "K": K,
               "GATE_P1": GATE_P1, "GATE_P2": GATE_P2, "GATE_P3": GATE_P3,
               "GATE_FIT": GATE_FIT, "GATE_TRANSFER": GATE_TRANSFER,
               "FATTORE_IDENT": FATTORE_IDENT, "SEME_CENTRI": SEME_CENTRI,
               "STAB_B": V8.STAB_B, "STAB_FRAC": V8.STAB_FRAC,
               "STAB_FREQ": V8.STAB_FREQ, "LAM_GRID": list(V8.LAM_GRID)},
           "casi": risultati,
           "elapsed_s": round(time.time() - t0, 1)}
    p = OUT / "predictions.json"
    p.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(f"\npredictions.json sha256: "
          f"{hashlib.sha256(p.read_bytes()).hexdigest()}")
    print(f"wall-clock totale: {res['elapsed_s']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
