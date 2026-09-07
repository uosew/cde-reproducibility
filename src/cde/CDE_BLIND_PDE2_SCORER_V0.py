#!/usr/bin/env python3
"""Blind PDE campagna 2 — SCORER appaiato (apre il sigillo e confronta).

Scritto e committato PRIMA della run.

La domanda non e' «il braccio corretto sbaglia meno?» ma **«sbaglia meno senza
costare recuperi?»**. Un cancello che azzera i falsi positivi rifiutando tutto
e' inutile, e i due decoy quasi-degeneri del pannello esistono apposta per
farlo vedere.

Criteri, congelati nella preregistrazione §5:

  RECUPERABILE / DECOY  corretto <=> CLAIM con supporto esatto ed errore
                        relativo massimo sui coefficienti < 0.05;
  NON_IDENTIFICABILE    corretto <=> NOT_IDENTIFIABLE o una qualunque
                        astensione; CLAIM = falso positivo;
  SURROGATO / CONTROLLO corretto <=> qualunque cosa diversa da CLAIM.

Cancelli del verdetto:

  H1 primario   il braccio corretto ha ZERO falsi positivi E non meno recuperi
                del baseline;
  H2 chiusura   nessun CLAIM del braccio corretto sui non identificabili e sui
                surrogati — i due fallimenti del blind 1;
  H3 costo      entrambi i decoy restano CLAIM nel braccio corretto.

  PASS = H1 & H2 & H3;  PARTIAL = H1 vero ma H3 falso (funziona ma costa);
  FAIL = H1 falso.

Uso: python CDE_BLIND_PDE2_SCORER_V0.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import platform
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
ART = BASE.parent.parent / "artifacts"      # public layout (cde-reproducibility)
PAPER = BASE.parent.parent / "paper"
JUL = BASE.parent.parent / "baselines" / "julia"
ROOT = BASE.parent
OUT = ART / "cde_blind_pde2_out"
SEALED = OUT / "sealed"
RUNNER = BASE / "CDE_BLIND_PDE2_RUNNER_V0.py"
GENERATORE = BASE / "CDE_BLIND_PDE2_GENERATOR_V0.py"

_g = importlib.util.spec_from_file_location(
    "runtime_guard_bootstrap", BASE / "runtime_guard_bootstrap.py")
RGB = importlib.util.module_from_spec(_g)
_g.loader.exec_module(RGB)

import numpy as np                                        # noqa: E402

GATE_COEF_RELERR = 0.05
TOLL_VINCOLO = 0.05
ATTESO_CLAIM = ("RECUPERABILE", "DECOY")


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def audit_cecita() -> dict:
    src = RUNNER.read_text()
    codice = re.sub(r'""".*?"""', "", src, flags=re.S)
    codice = "\n".join(r for r in codice.splitlines()
                       if not r.strip().startswith("#"))
    sospetti = [p for p in ("sealed", "truth", "PDE2_GENERATOR", "coeff_veri",
                            "esito_atteso", "famiglia")
                if p in codice]
    sha_att = hashlib.sha256((SEALED / "truth.json").read_bytes()).hexdigest()
    sha_reg = (SEALED / "truth.sha256").read_text().strip()
    return {"riferimenti_sospetti_nel_risolutore": sospetti,
            "risolutore_cieco": not sospetti,
            "sha256_verita_atteso": sha_reg,
            "sha256_verita_attuale": sha_att,
            "sigillo_intatto": sha_att == sha_reg,
            "sha256_risolutore": hashlib.sha256(RUNNER.read_bytes()).hexdigest(),
            "sha256_generatore":
                hashlib.sha256(GENERATORE.read_bytes()).hexdigest()}


def _err_coef(stimati: dict, veri: dict) -> float:
    if set(stimati) != set(veri):
        return float("inf")
    return max(abs(stimati[k] - veri[k]) / abs(veri[k]) for k in veri)


def _residuo_vincolo(stimati, vincolo):
    if not vincolo or not stimati:
        return None
    v = sum(p * stimati.get(k, 0.0)
            for k, p in zip(vincolo["termini"], vincolo["pesi"]))
    atteso = vincolo["valore"]
    return {"valore_stimato": round(float(v), 6), "valore_atteso": atteso,
            "sul_vincolo": bool(abs(v - atteso)
                                <= TOLL_VINCOLO * max(abs(atteso), 1e-12))}


def valuta(cv: dict, pred: dict) -> dict:
    fam, veri = cv["famiglia"], cv["coeff_veri"]
    dec = pred.get("decisione", "MANCANTE")
    stimati = pred.get("coefficienti", {})
    r = {"decisione": dec, "supporto_stimato": pred.get("supporto", []),
         "resid_fit": pred.get("resid_fit"),
         "resid_transfer": pred.get("resid_transfer"),
         "resid_ampiezza": pred.get("resid_ampiezza"),
         "max_corr": pred.get("collinearita", {}).get("max_corr")}

    if fam in ATTESO_CLAIM:
        err = _err_coef(stimati, veri)
        r["err_coef_rel_max"] = (None if err == float("inf")
                                 else round(float(err), 6))
        sup_ok = sorted(pred.get("supporto", [])) == sorted(veri)
        r["corretto"] = bool(dec == "CLAIM" and sup_ok
                             and err < GATE_COEF_RELERR)
        r["falso_positivo"] = bool(dec == "CLAIM" and not sup_ok)
        if dec != "CLAIM":
            r["modo_fallimento"] = f"recupero perso ({dec})"
        elif not sup_ok:
            r["modo_fallimento"] = "supporto sbagliato affermato"
        elif err >= GATE_COEF_RELERR:
            r["modo_fallimento"] = f"coefficienti a {err:.3f}"
    elif fam == "NON_IDENTIFICABILE":
        r["corretto"] = bool(dec != "CLAIM")
        r["falso_positivo"] = bool(dec == "CLAIM")
        r["flag_identificabilita"] = bool(dec == "NOT_IDENTIFIABLE")
        r["vincolo"] = _residuo_vincolo(stimati, cv.get("vincolo"))
        if dec == "CLAIM":
            v = r["vincolo"]
            r["modo_fallimento"] = (
                "ha affermato un membro della famiglia degenere"
                if v and v["sul_vincolo"]
                else "ha affermato una legge fuori dalla famiglia degenere")
    else:                                   # SURROGATO / CONTROLLO
        r["corretto"] = bool(dec != "CLAIM")
        r["falso_positivo"] = bool(dec == "CLAIM")
        if dec == "CLAIM":
            r["modo_fallimento"] = "ha affermato una legge dove non ce n'e'"
    return r


def riassumi(righe, vpi):
    def fam(c):
        return vpi[c["case_id"]]["famiglia"]
    rec = [c for c in righe if fam(c) in ATTESO_CLAIM]
    nid = [c for c in righe if fam(c) == "NON_IDENTIFICABILE"]
    ast = [c for c in righe if fam(c) in ("SURROGATO", "CONTROLLO")]
    dec = [c for c in righe if fam(c) == "DECOY"]
    return {"recuperi_corretti": sum(c["esito"]["corretto"] for c in rec),
            "recuperabili": len(rec),
            "falsi_positivi": sum(c["esito"]["falso_positivo"] for c in righe),
            "flag_identificabilita":
                sum(c["esito"].get("flag_identificabilita", False)
                    for c in nid),
            "non_identificabili": len(nid),
            "astensioni_corrette": sum(c["esito"]["corretto"] for c in ast),
            "astensioni_attese": len(ast),
            "decoy_mantenuti": sum(c["esito"]["corretto"] for c in dec),
            "decoy": len(dec)}


def main():
    audit = audit_cecita()
    if not audit["risolutore_cieco"]:
        raise SystemExit("CECITA' VIOLATA: "
                         f"{audit['riferimenti_sospetti_nel_risolutore']}")
    if not audit["sigillo_intatto"]:
        raise SystemExit("SIGILLO ROTTO: truth.json cambiato dopo il freeze")

    verita = json.loads((SEALED / "truth.json").read_text())
    pred = json.loads((OUT / "predictions.json").read_text())
    vpi = {c["case_id"]: c for c in verita["casi"]}
    ppi = {c["case_id"]: c for c in pred["casi"]}

    bracci = {}
    for arm in ("baseline", "corretto"):
        righe = []
        for cv in verita["casi"]:
            p = ppi.get(cv["case_id"], {}).get(arm, {})
            righe.append({"case_id": cv["case_id"], "famiglia": cv["famiglia"],
                          "sigma": cv["sigma"], "esito": valuta(cv, p)})
        bracci[arm] = {"righe": righe, "conteggi": riassumi(righe, vpi)}

    disc = []
    for cb, cc in zip(bracci["baseline"]["righe"], bracci["corretto"]["righe"]):
        if cb["esito"]["decisione"] != cc["esito"]["decisione"]:
            disc.append({"case_id": cb["case_id"], "famiglia": cb["famiglia"],
                         "baseline": cb["esito"]["decisione"],
                         "corretto": cc["esito"]["decisione"],
                         "baseline_corretto": cb["esito"]["corretto"],
                         "corretto_corretto": cc["esito"]["corretto"]})

    b, c = bracci["baseline"]["conteggi"], bracci["corretto"]["conteggi"]
    H1 = (c["falsi_positivi"] == 0
          and c["recuperi_corretti"] >= b["recuperi_corretti"])
    fp_mirati = sum(
        1 for r in bracci["corretto"]["righe"]
        if r["famiglia"] in ("NON_IDENTIFICABILE", "SURROGATO")
        and r["esito"]["decisione"] == "CLAIM")
    H2 = fp_mirati == 0
    H3 = c["decoy_mantenuti"] == c["decoy"]
    verdetto = ("PASS" if (H1 and H2 and H3)
                else "FAIL" if not H1 else "PARTIAL")

    res = {"run": "CDE_BLIND_PDE2_SCORER_V0",
           "data": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
           "commit": _git_commit(), "python": platform.python_version(),
           "numpy": np.__version__, "audit_cecita": audit,
           "per_braccio": {a: bracci[a]["conteggi"] for a in bracci},
           "discordanze": disc,
           "cancelli": {"H1_primario": bool(H1), "H2_chiusura": bool(H2),
                        "H3_costo_decoy": bool(H3)},
           "verdetto": verdetto,
           "dettaglio": {a: bracci[a]["righe"] for a in bracci}}
    (OUT / "scoring.json").write_text(json.dumps(res, indent=2,
                                                 ensure_ascii=False))

    print("== BLIND PDE 2 — SCORING APPAIATO ==")
    print(f"   cecita': cieco={audit['risolutore_cieco']}  "
          f"sigillo={audit['sigillo_intatto']}\n")
    for cb, cc in zip(bracci["baseline"]["righe"], bracci["corretto"]["righe"]):
        sb = "OK" if cb["esito"]["corretto"] else "NO"
        sc = "OK" if cc["esito"]["corretto"] else "NO"
        seg = (" " if cb["esito"]["decisione"] == cc["esito"]["decisione"]
               else "*")
        print(f"  {seg}{cb['case_id']} [{cb['famiglia'][:18]:<18}] "
              f"base {sb} {cb['esito']['decisione']:<22} -> "
              f"corr {sc} {cc['esito']['decisione']}")
    print(f"\n   {'metrica':<26}{'baseline':>10}{'corretto':>10}")
    for k in ("recuperi_corretti", "falsi_positivi", "flag_identificabilita",
              "astensioni_corrette", "decoy_mantenuti"):
        print(f"   {k:<26}{b[k]:>10}{c[k]:>10}")
    print(f"\n   discordanze: {len(disc)}")
    print(f"   H1={H1}  H2={H2}  H3={H3}  ->  VERDETTO {verdetto}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
