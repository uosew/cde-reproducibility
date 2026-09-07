#!/usr/bin/env python3
"""Punteggio del confronto appaiato (prereg 2026-09-07 §2). Mutation test prima dell'esito."""
import json, sys
from pathlib import Path
BASE = Path(__file__).resolve().parent
ART = BASE.parent.parent / "artifacts"      # public layout (cde-reproducibility)
PAPER = BASE.parent.parent / "paper"
JUL = BASE.parent.parent / "baselines" / "julia"
EXPORT = ART / "cde_feature_export_out"; JL = JUL
GATE = 0.05


def esito(celle, dde):
    """Due politiche sui nulli, entrambe riportate (emendamento §1-a del 2026-09-07):

    - `fissa`: la soglia selezionata sulla cella a rumore zero dello stesso sistema, che e'
      esattamente la politica con cui furono contati i nulli di PySINDy. **Il verdetto usa
      questa**: e' l'unico confronto appaiato.
    - `oracolo`: la soglia piu' favorevole al concorrente, cioe' quella che si astiene se
      esiste. Riportata perche' una rivendicazione anche sotto questa politica e' la forma
      forte del risultato.
    """
    r = {"nulli": 0, "nulli_rivendicati": 0, "nulli_rivendicati_oracolo": 0,
         "nulli_rivendicati_gated": 0, "vere": 0, "supporto_esatto": 0, "errori": 0,
         "soglia_fissa_per_sistema": {}, "dettaglio": []}
    # politica fissa: soglia scelta sulla cella sigma=0 di ciascun sistema (supporto esatto,
    # altrimenti residuo minimo), come per PySINDy
    for cid, meta in celle.items():
        if meta["tipo"] != "vera" or meta.get("sigma") != 0.0:
            continue
        cell = dde.get(cid) or {}
        ok_l = {lam: v for lam, v in cell.items() if not v.get("errore")}
        if not ok_l:
            continue
        vero = set(meta["supporto_vero"])
        esatte = [lam for lam, v in ok_l.items()
                  if {EXPORT_TERMS[i] for i in v["supporto"]} == vero]
        r["soglia_fissa_per_sistema"][meta["sistema"]] = (
            esatte[0] if esatte else min(ok_l, key=lambda l: ok_l[l]["resid_rel"]))
    for cid, meta in celle.items():
        cell = dde.get(cid)
        if cell is None or all(v.get("errore") for v in cell.values()):
            r["errori"] += 1
            continue
        vero = set(meta["supporto_vero"])
        ok = {lam: v for lam, v in cell.items() if not v.get("errore")}
        if meta["tipo"] == "nullo":
            r["nulli"] += 1
            # oracolo pro-baseline: la soglia piu' favorevole, cioe' quella che astiene se puo'
            vuoti = [lam for lam, v in ok.items() if not v["supporto"]]
            scelto_o = ok[vuoti[0]] if vuoti else ok[min(ok, key=lambda l: len(ok[l]["supporto"]))]
            lam_f = r["soglia_fissa_per_sistema"].get(meta.get("sistema"))
            scelto = ok.get(lam_f) or scelto_o
            rivendica = bool(scelto["supporto"])
            r["nulli_rivendicati"] += rivendica
            r["nulli_rivendicati_oracolo"] += bool(scelto_o["supporto"])
            r["nulli_rivendicati_gated"] += bool(rivendica and scelto["resid_rel"] < GATE)
            r["dettaglio"].append({"cella": cid, "tipo": "nullo", "rivendica": rivendica,
                                   "rivendica_oracolo": bool(scelto_o["supporto"]),
                                   "soglia_fissa": lam_f, "resid": scelto["resid_rel"]})
        else:
            r["vere"] += 1
            # oracolo: la soglia che dà il supporto esatto, se esiste
            esatte = [lam for lam, v in ok.items()
                      if {list(EXPORT_TERMS)[i] for i in v["supporto"]} == vero]
            scelto = ok[esatte[0]] if esatte else ok[min(ok, key=lambda l: ok[l]["resid_rel"])]
            exact = bool(esatte)
            r["supporto_esatto"] += exact
            r["dettaglio"].append({"cella": cid, "tipo": "vera", "esatto": exact,
                                   "resid": scelto["resid_rel"]})
    n = r["nulli"]; c = r["nulli_rivendicati"]
    if r["errori"] >= 5:
        r["verdetto"] = "NON_CONFRONTABILE"
    elif c >= 30:
        r["verdetto"] = "CLASSE"
    elif c <= 10:
        r["verdetto"] = "IMPLEMENTAZIONE"
    else:
        r["verdetto"] = "INTERMEDIO"
    return r


EXPORT_TERMS = ()


def mutation_test():
    global EXPORT_TERMS
    EXPORT_TERMS = ("u", "u^2", "u^3", "u_x", "u_xx", "u_xxx", "uu_x")
    def cella(sup, resid=0.01, err=False):
        return {"0.1": ({"errore": True} if err else
                        {"supporto": sup, "resid_rel": resid, "coef": []})}
    ok = {}
    man = {f"n{i}": {"tipo": "nullo", "supporto_vero": [], "sistema": "s"} for i in range(40)}
    dde = {k: cella([0, 4]) for k in man}
    ok["40 nulli rivendicati -> CLASSE"] = esito(man, dde)["verdetto"] == "CLASSE"
    dde2 = {k: cella([]) for k in man}
    ok["0 nulli rivendicati -> IMPLEMENTAZIONE"] = esito(man, dde2)["verdetto"] == "IMPLEMENTAZIONE"
    dde3 = {k: (cella([0, 4]) if i < 20 else cella([])) for i, k in enumerate(man)}
    ok["20 su 40 -> INTERMEDIO"] = esito(man, dde3)["verdetto"] == "INTERMEDIO"
    dde4 = {k: cella([], err=True) for k in man}
    ok["errori diffusi -> NON_CONFRONTABILE"] = esito(man, dde4)["verdetto"] == "NON_CONFRONTABILE"
    e = esito(man, {k: cella([0, 4], resid=0.9) for k in man})
    ok["il gate non conta un nullo con residuo alto"] = e["nulli_rivendicati"] == 40 and e["nulli_rivendicati_gated"] == 0
    # le due politiche devono poter divergere: soglia fissa che rivendica, oracolo che astiene
    man5 = dict(man); man5["z"] = {"tipo": "vera", "sigma": 0.0, "sistema": "s",
                                   "supporto_vero": ["u", "u_xx"]}
    due = {k: {"0.1": {"supporto": [0, 4], "resid_rel": 0.01},
               "0.5": {"supporto": [], "resid_rel": 0.9}} for k in man}
    due["z"] = {"0.1": {"supporto": [0, 4], "resid_rel": 0.001},
                "0.5": {"supporto": [], "resid_rel": 0.9}}
    e5 = esito(man5, due)
    ok["politica fissa e oracolo divergono e sono riportate entrambe"] = (
        e5["nulli_rivendicati"] == 40 and e5["nulli_rivendicati_oracolo"] == 0
        and e5["soglia_fissa_per_sistema"] == {"s": "0.1"})
    manv = {"v1": {"tipo": "vera", "supporto_vero": ["u", "u_xx"], "sistema": "s"}}
    ok["supporto esatto riconosciuto"] = esito(manv, {"v1": cella([0, 4])})["supporto_esatto"] == 1
    ok["supporto sbagliato non conta"] = esito(manv, {"v1": cella([0, 1])})["supporto_esatto"] == 0
    return ok


def main():
    global EXPORT_TERMS
    ok = mutation_test()
    print("== mutation test ==")
    for k, v in ok.items():
        print(f"  {'MORDE' if v else '*** NON MORDE ***'}  {k}")
    if not all(ok.values()):
        return 1
    mp = EXPORT / "manifest.json"; rp = JL / "risultati_dde.json"
    if not (mp.exists() and rp.exists()):
        print("\nartefatti mancanti: solo mutation test"); return 0
    man = json.loads(mp.read_text()); EXPORT_TERMS = tuple(man["terms"])
    dde = json.loads(rp.read_text())["celle"]
    e = esito(man["celle"], dde)
    print(f"\n== confronto appaiato, stesse matrici di disegno ==")
    print(f"  nulli (politica fissa, appaiata con PySINDy): {e['nulli_rivendicati']}/{e['nulli']} rivendicati; "
          f"con il nostro cancello: {e['nulli_rivendicati_gated']}/{e['nulli']}")
    print(f"  nulli (politica oracolo, la piu' favorevole al concorrente): "
          f"{e['nulli_rivendicati_oracolo']}/{e['nulli']}")
    print(f"  soglia fissa per sistema: {e['soglia_fissa_per_sistema']}")
    print(f"  celle vere: supporto esatto {e['supporto_esatto']}/{e['vere']}   errori: {e['errori']}")
    print(f"  riferimento PySINDy sugli stessi 4 sistemi: 40/40 nulli, 14/20 esatti")
    print(f"\n  VERDETTO: {e['verdetto']}")
    (JL / "scoring.json").write_text(json.dumps({"esito": e, "mutation_test": ok}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
