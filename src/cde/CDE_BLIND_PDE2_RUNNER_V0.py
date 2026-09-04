#!/usr/bin/env python3
"""Blind PDE campagna 2 — RISOLUTORE appaiato (vede solo i dati).

NON importa il generatore della campagna 2 e NON legge sealed/. Lo scorer lo
verifica sul sorgente prima di calcolare qualunque cosa.

Esegue DUE pipeline sullo stesso caso e sulle STESSE feature:

  baseline  la pipeline congelata della campagna 1, invariata: le funzioni
            vengono importate dal runner congelato, non riscritte, cosi' il
            braccio di controllo e' identico per costruzione;
  corretto  la stessa piu' i due cancelli suggeriti dai fallimenti del blind 1:

            (a) CONDIZIONAMENTO — se due colonne della matrice di disegno sono
                numericamente indistinguibili da collineari
                (max|corr| >= SOGLIA_CORR), i dati non separano le leggi e la
                risposta e' NOT_IDENTIFIABLE, non una scelta fra equivalenti.
                Agisce PRIMA della selezione: e' una proprieta' dei dati, non
                del modello scelto.

            (b) ESTRAPOLAZIONE IN AMPIEZZA — i coefficienti congelati sulla
                traiettoria base devono reggere anche su una traiettoria ad
                ampiezza doppia. Un surrogato di Taylor coincide con la legge
                vera a piccola ampiezza e diverge a grande; una legge vera ha
                coefficienti che non dipendono dall'ampiezza.

Le feature sono calcolate UNA volta per caso e condivise dai due bracci:
l'appaiamento e' esatto, senza rumore di semi fra i bracci.

Uso: ../.venv313/bin/python CDE_BLIND_PDE2_RUNNER_V0.py [--caso case_01]
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
OUT = ART / "cde_blind_pde2_out"
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


# Il braccio di controllo NON viene riscritto: e' il codice congelato.
RUN1 = _load("run1", "CDE_BLIND_PDE_RUNNER_V0.py")
V8, NOP = RUN1.V8, RUN1.NOP
TERMS = RUN1.TERMS

# --- soglie: nessuna nuova, tranne una, dichiarata ------------------------
GATE_P1, GATE_P2, GATE_P3 = RUN1.GATE_P1, RUN1.GATE_P2, RUN1.GATE_P3
GATE_FIT, GATE_TRANSFER = RUN1.GATE_FIT, RUN1.GATE_TRANSFER
FATTORE_IDENT = RUN1.FATTORE_IDENT
WX, WT, K = RUN1.WX, RUN1.WT, RUN1.K
SEME_CENTRI = 8484                       # diverso dalla campagna 1

# L'unica soglia nuova. Non e' tarata sui dati di questo pannello: significa
# «numericamente indistinguibile da perfettamente collineare». Lo stage 1 ha
# misurato 0.999871 su un decoy identificabile, cioe' 1.3e-04 sotto: il
# margine e' sottile, e i decoy del pannello esistono per farlo fallire.
SOGLIA_CORR = 0.9999

# Il gate di ampiezza NON introduce un numero nuovo: e' lo stesso gate di
# transfer applicato a dati nuovi.
GATE_AMPIEZZA = GATE_TRANSFER

assert (GATE_FIT, GATE_TRANSFER, FATTORE_IDENT) == (0.05, 0.05, 2.0), \
    "le soglie ereditate non corrispondono a quelle congelate nella campagna 1"


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def _collinearita(A):
    An = A / np.linalg.norm(A, axis=0)
    C = np.abs(An.T @ An)
    np.fill_diagonal(C, 0.0)
    i, j = np.unravel_index(C.argmax(), C.shape)
    return {"max_corr": float(C.max()), "cond_A": float(np.linalg.cond(A)),
            "coppia": f"{TERMS[i]} ~ {TERMS[j]}"}


def _decidi(A, b, A2, b2, A3, b3, seme, con_correzioni: bool) -> dict:
    """Una decisione. `con_correzioni` sceglie il braccio."""
    out = {}
    col = _collinearita(A)
    out["collinearita"] = {k: (round(v, 8) if isinstance(v, float) else v)
                           for k, v in col.items()}

    if con_correzioni and col["max_corr"] >= SOGLIA_CORR:
        out["decisione"] = "NOT_IDENTIFIABLE"
        out["motivo"] = (f"colonne {col['coppia']} collineari a "
                         f"{col['max_corr']:.6f}: i dati non separano le leggi")
        return out

    supporto, freqs = V8.stability_selection(A, b,
                                             np.random.default_rng(seme + 7))
    out["supporto"] = sorted(TERMS[i] for i in supporto)
    out["frequenze"] = {TERMS[i]: round(float(f), 3)
                        for i, f in enumerate(freqs)}
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

    cvec = np.array([coeffs.get(k, 0.0) for k in TERMS])
    r_tr = RUN1._rr(A2, b2, cvec)
    out["resid_transfer"] = round(float(r_tr), 8)
    if not (r_tr < GATE_TRANSFER):
        out["decisione"] = "ABSTAIN_TRANSFER"
        return out

    r_amp = RUN1._rr(A3, b3, cvec)
    out["resid_ampiezza"] = round(float(r_amp), 8)
    if con_correzioni and not (r_amp < GATE_AMPIEZZA):
        out["decisione"] = "ABSTAIN_AMPIEZZA"
        out["motivo"] = (f"i coefficienti non reggono ad ampiezza doppia "
                         f"({r_amp:.4f}): modello efficace, non legge")
        return out

    ident, alt = RUN1.swap_test(A, b, supporto, resid)
    out["identificabile"] = bool(ident)
    out["alternative_entro_fattore"] = alt
    out["decisione"] = "CLAIM" if ident else "NOT_IDENTIFIABLE"
    return out


def risolvi(cid: str) -> dict:
    d = np.load(CASES / f"{cid}.npz")
    x, t = d["x"], d["t"]
    seme = SEME_CENTRI + int(cid.split("_")[1])
    out = {"case_id": cid, "Nx": int(len(x)), "Nt": int(len(t))}

    centers = RUN1._centri(x, t, seme)
    if not centers:
        for arm in ("baseline", "corretto"):
            out[arm] = {"decisione": "ABSTAIN_GEOMETRIA"}
        return out

    A, b, pf = RUN1.preflight(x, t, d["U"], centers)
    out["preflight"] = {k: round(float(v), 8) for k, v in pf.items()}
    chiusure = [k for k, g in (("P1_quadratura", GATE_P1),
                               ("P2_famiglie", GATE_P2),
                               ("P3_holdout", GATE_P3)) if not (pf[k] < g)]
    if chiusure:
        for arm in ("baseline", "corretto"):
            out[arm] = {"decisione": "ABSTAIN_PREFLIGHT",
                        "cancelli_chiusi": chiusure}
        return out

    # feature delle altre due traiettorie, calcolate una volta sola e
    # condivise dai due bracci: l'appaiamento e' esatto
    def _feat(U, s):
        c = RUN1._centri(x, t, s)
        F = NOP.weak_features_nop(x, t, U, WX, WT, c, TERMS, "simpson",
                                  NOP.BumpA)
        return NOP.to_Ab(F, TERMS)

    A2, b2 = _feat(d["U2"], seme + 313)
    A3, b3 = _feat(d["U3"], seme + 517)

    out["baseline"] = _decidi(A, b, A2, b2, A3, b3, seme, con_correzioni=False)
    out["corretto"] = _decidi(A, b, A2, b2, A3, b3, seme, con_correzioni=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--caso", default=None)
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
        bl = r.get("baseline", {}).get("decisione", "?")
        co = r.get("corretto", {}).get("decisione", "?")
        segno = " " if bl == co else "*"
        print(f"  {segno}{cid}: baseline={bl:<24} corretto={co:<24} "
              f"({r['wall_s']}s)")

    res = {"run": "CDE_BLIND_PDE2_RUNNER_V0",
           "data": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
           "commit": _git_commit(), "python": platform.python_version(),
           "numpy": np.__version__,
           "parametri_congelati": {
               "TERMS": list(TERMS), "wx": WX, "wt": WT, "K": K,
               "GATE_P1": GATE_P1, "GATE_P2": GATE_P2, "GATE_P3": GATE_P3,
               "GATE_FIT": GATE_FIT, "GATE_TRANSFER": GATE_TRANSFER,
               "GATE_AMPIEZZA": GATE_AMPIEZZA, "SOGLIA_CORR": SOGLIA_CORR,
               "FATTORE_IDENT": FATTORE_IDENT, "SEME_CENTRI": SEME_CENTRI,
               "STAB_B": V8.STAB_B, "STAB_FREQ": V8.STAB_FREQ},
           "casi": risultati, "elapsed_s": round(time.time() - t0, 1)}
    p = OUT / "predictions.json"
    p.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(f"\npredictions.json sha256: "
          f"{hashlib.sha256(p.read_bytes()).hexdigest()}")
    print(f"wall-clock totale: {res['elapsed_s']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
