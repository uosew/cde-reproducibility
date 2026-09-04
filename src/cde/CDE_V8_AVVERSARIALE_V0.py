#!/usr/bin/env python3
"""Tenta di rompere la claim V8 su venti semi mai visti.

PERCHE'. La caratterizzazione ha dato 20/20 su tutti e quattro i sistemi, sia a
rumore zero sia al 10%, con FDR 0 su 800 nulli. Un punteggio perfetto non e' una
buona notizia: significa che la prova non era abbastanza dura per trovare il
punto di rottura. `sigma_star_first_fail` esce `None` ovunque — il perimetro non
e' stato misurato, e' stato superato. La nota e' a un passo dalla sottomissione,
e un difetto trovato adesso costa ore invece che la sottomissione.

IL MOTORE NON VIENE TOCCATO. `CDE_PDE_DISCOVERY_V8.py` gira come sottoprocesso,
impronta `4a2181b8dbeda428`, unica versione mai esistita nella storia del
repository. Questo script non importa il motore e non ne altera una costante:
lo esegue e ne raccoglie l'uscita.

GLI ARTEFATTI SIGILLATI SONO INTOCCABILI. Il motore scrive sempre negli stessi
tre file di `cde_pde_discovery_v8_out/`. Qui vengono salvati prima, spostati
nella cartella del seme dopo ogni run, e ripristinati alla fine — con verifica
per impronta prima e dopo, e arresto bloccante se qualcosa e' cambiato. E' lo
stesso schema dell'orchestratore multi-seme, ripreso perche' e' corretto.

A2 USA UNA COPIA DICHIARATA, NON UNA MONKEYPATCH. Guardare oltre il 10% richiede
di cambiare la costante `SIGMAS`. Alterarla a runtime lasciando l'impronta del
file invariata sarebbe una divergenza invisibile — esattamente il tipo di cosa
che questo progetto esiste per impedire. Si scrive una copia il cui unico
diverso e' quella riga, se ne registra l'impronta accanto a quella
dell'originale, e non la si usa mai per A1.

NON DECIDE NIENTE DI NUOVO. Le soglie sono quelle congelate il 4 agosto e
rilette dall'artefatto della campagna originale invece che ricopiate a mano: se
qualcuno le cambiasse la', questo script fallirebbe il confronto invece di
mentire.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

BASE = Path(__file__).resolve().parent
ART = BASE.parent.parent / "artifacts"      # public layout (cde-reproducibility)
PAPER = BASE.parent.parent / "paper"
MOTORE = BASE / "CDE_PDE_DISCOVERY_V8.py"
OUT_V8 = ART / "cde_pde_discovery_v8_out"
ORIGINALE = ART / "cde_pde_discovery_v8_multiseed"
DEST = ART / "cde_v8_avversariale_v0"
PREREG = BASE / "PREREGISTRAZIONE_V8_AVVERSARIALE_2026_08_25.md"

SEMI = tuple(range(201, 221))          # mai usati: 7, 11, 101-120 sono presi
SEMI_A2 = tuple(range(201, 206))       # i primi cinque, per la mappa del confine
SIGMAS_A2 = (0.15, 0.20, 0.30)
ARTEFATTI = ("results.json", "evidence_envelope.json", "claim_card.md")
SISTEMI = ("allen_cahn", "fisher_kpp", "burgers", "kdv")
IMPRONTA_MOTORE_ATTESA = "4a2181b8dbeda428"

T0 = time.monotonic()


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')} · {(time.monotonic()-T0)/60:6.1f}m] {m}",
          flush=True)


def sha(p: Path) -> str:
    import hashlib
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else "assente"


def soglie_congelate() -> dict:
    """Le soglie si rileggono dall'artefatto originale, non si ricopiano.

    Ricopiarle a mano significherebbe che una divergenza fra questa campagna e
    quella sigillata resterebbe invisibile. Cosi' invece si romperebbe qui.
    """
    d = json.loads((ORIGINALE / "caratterizzazione.json").read_text())
    s1 = d["S1_recupero_esatto_sigma_zero"]["soglia"]
    s2 = d["S2_recupero_sigma_dieci_per_cento"]["soglia"]
    s3 = d["S3_falsi_positivi_sui_nulli"]["soglia"]
    n1 = [int(x) for x in re.findall(r">= (\d+)/20", s1)]
    n2 = [int(x) for x in re.findall(r">= (\d+)/20", s2)]
    fdr = float(re.findall(r"([\d.]+)", s3)[0])
    if not (len(n1) == 2 and len(n2) == 1):
        raise SystemExit(f"soglie non riconosciute: {s1!r} {s2!r}")
    return {"S1_confermata": n1[0], "S1_probabilistica": n1[1],
            "S2_minimo": n2[0], "S3_fdr_max": fdr,
            "testo": {"S1": s1, "S2": s2, "S3": s3}}


def esegui(seme: int, motore: Path, dove: Path) -> dict | None:
    dove.mkdir(parents=True, exist_ok=True)
    if (dove / "results.json").exists():          # ripresa dopo interruzione
        return json.loads((dove / "results.json").read_text())
    r = subprocess.run([sys.executable, str(motore), "--seed", str(seme)],
                       cwd=BASE, capture_output=True, text=True)
    (dove / "stdout.txt").write_text(r.stdout + r.stderr, encoding="utf-8")
    if r.returncode != 0:
        log(f"    seme {seme}: uscita {r.returncode} — riportato, non ritentato")
        return None
    for a in ARTEFATTI:
        if (OUT_V8 / a).exists():
            shutil.move(str(OUT_V8 / a), str(dove / a))
    p = dove / "results.json"
    return json.loads(p.read_text()) if p.exists() else None


def conta(risultati: list[dict], sigma: str, sistema: str) -> int:
    n = 0
    for r in risultati:
        s = r.get("systems", {}).get(sistema, {}).get("sigma", {}).get(sigma)
        if s and s.get("support_exact"):
            n += 1
    return n


def main() -> None:
    DEST.mkdir(exist_ok=True)
    imp = sha(MOTORE)[:16]
    log(f"motore {imp} (atteso {IMPRONTA_MOTORE_ATTESA})")
    if imp != IMPRONTA_MOTORE_ATTESA:
        raise SystemExit("il motore non e' quello sigillato: mi fermo")
    sog = soglie_congelate()
    log(f"soglie rilette dall'artefatto originale: S1>={sog['S1_confermata']}/20 "
        f"· S2>={sog['S2_minimo']}/20 · FDR<={sog['S3_fdr_max']}")

    # Gli artefatti della campagna sigillata, salvati e verificati.
    salvati = DEST / "_artefatti_salvati"
    salvati.mkdir(exist_ok=True)
    prima = {a: sha(OUT_V8 / a) for a in ARTEFATTI}
    for a in ARTEFATTI:
        if (OUT_V8 / a).exists():
            shutil.copy2(OUT_V8 / a, salvati / a)
    log(f"artefatti sigillati salvati: "
        f"{ {a: h[:8] for a, h in prima.items()} }")

    stato = {"run": "CDE_V8_AVVERSARIALE_SEMI_NUOVI_V0",
             "prereg": PREREG.name, "prereg_sha256": sha(PREREG),
             "motore_sha256": sha(MOTORE), "semi": list(SEMI),
             "soglie_congelate": sog, "avvio_utc": time.strftime(
                 "%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    (DEST / "stato.json").write_text(json.dumps(stato, indent=1,
                                                ensure_ascii=False))

    # --- A1: la replica, motore intatto -----------------------------------
    log(f"A1 — replica su {len(SEMI)} semi mai visti, motore intatto")
    a1 = []
    for i, s in enumerate(SEMI, 1):
        t = time.monotonic()
        r = esegui(s, MOTORE, DEST / f"seed_{s:03d}")
        if r:
            a1.append(r)
            det = " ".join(
                f"{n[:3]}:{'ok' if r['systems'][n]['sigma']['0.0']['support_exact'] else 'NO'}"
                f"/{'ok' if r['systems'][n]['sigma']['0.1']['support_exact'] else 'NO'}"
                for n in SISTEMI)
            log(f"  {i:2}/{len(SEMI)} seme {s} · {time.monotonic()-t:5.0f}s · "
                f"sigma0/sigma10 → {det}")
        stato["a1_completati"] = len(a1)
        (DEST / "stato.json").write_text(json.dumps(stato, indent=1,
                                                    ensure_ascii=False))

    # --- A2: oltre il confine, copia dichiarata ---------------------------
    log(f"A2 — oltre il 10% su {len(SEMI_A2)} semi, copia dichiarata del motore")
    variante = DEST / "_motore_sigmas_estese.py"
    src = MOTORE.read_text(encoding="utf-8")
    vecchia = "SIGMAS = (0.0, 0.01, 0.02, 0.05, 0.10)"
    if vecchia not in src:
        raise SystemExit("riga SIGMAS non trovata: non invento una sostituzione")
    variante.write_text(src.replace(
        vecchia, f"SIGMAS = {tuple(SIGMAS_A2)}"), encoding="utf-8")
    stato["motore_a2_sha256"] = sha(variante)
    stato["a2_sigmas"] = list(SIGMAS_A2)
    stato["a2_unica_differenza"] = f"{vecchia}  ->  SIGMAS = {tuple(SIGMAS_A2)}"
    log(f"  copia {sha(variante)[:16]} · unica differenza la riga SIGMAS")
    a2 = []
    for i, s in enumerate(SEMI_A2, 1):
        t = time.monotonic()
        r = esegui(s, variante, DEST / f"a2_seed_{s:03d}")
        if r:
            a2.append(r)
            det = " ".join(
                f"{n[:3]}:" + "".join(
                    "1" if r["systems"][n]["sigma"][str(g)]["support_exact"]
                    else "0" for g in SIGMAS_A2) for n in SISTEMI)
            log(f"  {i}/{len(SEMI_A2)} seme {s} · {time.monotonic()-t:5.0f}s · "
                f"15/20/30% → {det}")
        stato["a2_completati"] = len(a2)
        (DEST / "stato.json").write_text(json.dumps(stato, indent=1,
                                                    ensure_ascii=False))

    # --- ripristino e verifica -------------------------------------------
    for a in ARTEFATTI:
        if (salvati / a).exists():
            shutil.copy2(salvati / a, OUT_V8 / a)
    dopo = {a: sha(OUT_V8 / a) for a in ARTEFATTI}
    intatti = prima == dopo
    log(f"artefatti sigillati intatti: {intatti}")
    if not intatti:
        raise SystemExit("gli artefatti sigillati sono cambiati: ERRORE GRAVE")

    # --- verdetto, con le regole congelate --------------------------------
    n = len(a1)
    s1 = {k: conta(a1, "0.0", k) for k in SISTEMI}
    s2 = {k: conta(a1, "0.1", k) for k in SISTEMI}
    nulli = sum(r["systems"][k]["nulls"]["n_runs"] for r in a1 for k in SISTEMI)
    falsi = sum(r["systems"][k]["nulls"]["false_discoveries"]
                for r in a1 for k in SISTEMI)
    fdr = falsi / nulli if nulli else 0.0

    # Le soglie sono su 20; se un seme fosse fallito tecnicamente, il
    # confronto va fatto sul numero effettivo e la cosa va detta.
    scala = n / 20
    rotto = (any(v < sog["S1_probabilistica"] * scala for v in s1.values())
             or any(v < sog["S2_minimo"] * scala for v in s2.values())
             or fdr > sog["S3_fdr_max"])
    piena = all(v >= sog["S1_confermata"] * scala for v in s1.values())
    verdetto = "ROTTA" if rotto else ("REPLICA" if piena else "INDEBOLITA")

    conf = {}
    for k in SISTEMI:
        st = [r["systems"][k].get("sigma_star_first_fail") for r in a2]
        conf[k] = {"primo_fallimento_per_seme": st,
                   "conteggi": {str(g): sum(
                       1 for r in a2
                       if r["systems"][k]["sigma"][str(g)]["support_exact"])
                       for g in SIGMAS_A2},
                   "su": len(a2)}

    art = {**stato, "n_semi_riusciti": n,
           "A1": {"S1_sigma_zero": s1, "S2_sigma_dieci": s2,
                  "S3_nulli": {"run": nulli, "false_discoveries": falsi,
                               "fdr": round(fdr, 6)}},
           "A2_oltre_il_confine": conf,
           "VERDETTO": verdetto,
           "artefatti_sigillati_intatti": intatti,
           "durata_s": round(time.monotonic() - T0, 1)}
    (DEST / "risultati.json").write_text(json.dumps(art, indent=1,
                                                    ensure_ascii=False))
    log(f"A1  S1 sigma0  {s1}")
    log(f"A1  S2 sigma10 {s2}")
    log(f"A1  S3 nulli   {falsi}/{nulli}  FDR {fdr:.4f}")
    for k, v in conf.items():
        log(f"A2  {k:<12} 15/20/30% → {v['conteggi']} su {v['su']}")
    log(f"VERDETTO: {verdetto}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        DEST.mkdir(exist_ok=True)
        (DEST / "ERRORE.txt").write_text(traceback.format_exc(),
                                         encoding="utf-8")
        log("ERRORE — traccia in cde_v8_avversariale_v0/ERRORE.txt")
        raise
