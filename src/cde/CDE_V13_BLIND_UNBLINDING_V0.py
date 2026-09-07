#!/usr/bin/env python3
"""CDE V13 replica su larga scala — UNBLINDING (scoring), 2026-09-03.

Preregistrazione: PREREGISTRAZIONE_CDE_V13_REPLICA_LARGA_SCALA_2026_08_02.md.
I 703 verdetti (mac 351 + win 352, 100 condivisi) esistono dal 2026-08-04 e non
sono mai stati valutati. Questo scorer:

  Domanda A (§2, §3, §6) — claim false. Regole identiche a
  CDE_V11_BLIND_UNBLINDING_V1.py: una claim e' falsa se CLAIM su un nullo, CLAIM
  su un non rappresentabile, o CLAIM su un rappresentabile con supporto diverso
  da quello vero (insiemi). Opportunita' di mentire = nulli + non rappresentabili
  + rappresentabili su cui il sistema ha prodotto un supporto errato (§3).
  Domanda B (§5) — accordo pieno sui 100 casi condivisi: verdetto, supporto come
  insieme, blocked_at. Si confrontano i verdetti, non i float.
  Esiti (§6): LIMITE_STRETTO / CLAIM_FALSA_OSSERVATA / DIVERGENZA_PIATTAFORMA /
  POTENZA_INSUFFICIENTE. Ordine di precedenza dichiarato qui, non nella prereg:
  prima la claim falsa (e' lo scopo della campagna), poi la divergenza, poi la
  potenza, infine il limite stretto.

Sigillo — dichiarato onestamente: a differenza di V11, l'envelope di generazione
V13 NON registra lo sha256 della verita', e truth.json e i verdetti stanno nello
stesso commit (23c254ba). Il sigillo e' quindi PROCEDURALE: (a) il discoverer non
contiene letture di sealed/ (verificato qui con grep sul sorgente), (b) truth.json
e' identico a HEAD, (c) generazione 2026-08-02T17:03Z precede l'esecuzione
22:19Z negli envelope. Non e' dimostrabile per hash che la verita' non sia stata
letta: si dichiara, non si finge.

Per Domanda A sui 100 condivisi si usa il verdetto Mac (dichiarato); Windows e'
riportato accanto. Mutation test obbligatori prima di leggere l'esito.
"""
import hashlib, json, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
BASE = Path(__file__).resolve().parent
ART = BASE.parent.parent / "artifacts"      # public layout (cde-reproducibility)
PAPER = BASE.parent.parent / "paper"
JUL = BASE.parent.parent / "baselines" / "julia"; ROOT = BASE.parent; OUT = ART / "cde_v13_blind_out"
PREREG = "PREREGISTRAZIONE_CDE_V13_REPLICA_LARGA_SCALA_2026_08_02.md"
SOGLIA_OPPORTUNITA = 350

def falsa(v, tr):
    """(e' claim falsa?, ragione)"""
    if v["verdict"] != "CLAIM": return False, None
    if tr["is_null"]: return True, "claim su nullo"
    if not tr["representable"]: return True, "claim su non rappresentabile"
    if sorted(v["support"]) != sorted(tr["true_support"]): return True, "supporto errato"
    return False, None

def domanda_A(truth, verd):
    r = {"n": len(truth), "nulli": 0, "non_rappresentabili": 0, "rappresentabili": 0,
         "rapp_supporto_errato": 0, "claim_corrette": 0, "claim_false": [], "coef_err": [], "per_classe": {}}
    for cid, tr in truth.items():
        v = verd[cid]; c = r["per_classe"].setdefault(tr["cls"], {"n": 0, "verdetti": {}, "claim_corrette": 0, "claim_false": 0})
        c["n"] += 1; c["verdetti"][v["verdict"]] = c["verdetti"].get(v["verdict"], 0) + 1
        if tr["is_null"]: r["nulli"] += 1
        elif not tr["representable"]: r["non_rappresentabili"] += 1
        else:
            r["rappresentabili"] += 1
            if v.get("support") is not None and sorted(v["support"]) != sorted(tr["true_support"]): r["rapp_supporto_errato"] += 1
        f, why = falsa(v, tr)
        if f:
            r["claim_false"].append({"case": cid, "cls": tr["cls"], "reason": why, "support": v.get("support"), "true": tr.get("true_support")}); c["claim_false"] += 1
        elif v["verdict"] == "CLAIM":
            r["claim_corrette"] += 1; c["claim_corrette"] += 1
            a = v["coefficients"].get("v_xx"); al = tr["model"].get("alpha")
            if a is not None and al: r["coef_err"].append(abs(a - al) / al)
    r["opportunita"] = r["nulli"] + r["non_rappresentabili"] + r["rapp_supporto_errato"]
    r["n_claim_false"] = len(r["claim_false"])
    r["limite_regola_del_tre"] = 3.0 / r["opportunita"] if r["opportunita"] else None
    r["coef_err_mediano"] = float(np.median(r["coef_err"])) if r["coef_err"] else None
    r["recall_rappresentabili"] = r["claim_corrette"] / r["rappresentabili"] if r["rappresentabili"] else None
    return r

def domanda_B(vm, vw):
    comuni = sorted(set(vm) & set(vw)); disc = []
    for cid in comuni:
        a, b = vm[cid], vw[cid]
        diff = {}
        if a["verdict"] != b["verdict"]: diff["verdict"] = (a["verdict"], b["verdict"])
        if sorted(a.get("support") or []) != sorted(b.get("support") or []): diff["support"] = (a.get("support"), b.get("support"))
        if a.get("blocked_at") != b.get("blocked_at"): diff["blocked_at"] = (a.get("blocked_at"), b.get("blocked_at"))
        if diff: disc.append({"case": cid, **diff})
    return {"n_condivisi": len(comuni), "discrepanze": disc, "accordo_pieno": len(disc) == 0 and len(comuni) > 0}

def esito(A, B):
    if A["n_claim_false"] > 0: return "CLAIM_FALSA_OSSERVATA"
    if not B["accordo_pieno"]: return "DIVERGENZA_PIATTAFORMA"
    if A["opportunita"] < SOGLIA_OPPORTUNITA: return "POTENZA_INSUFFICIENTE"
    return "LIMITE_STRETTO"

def mutation_test():
    def T(cls, rep, null, sup=("v_xx",)): return {"cls": cls, "representable": rep, "is_null": null, "true_support": list(sup), "model": {"alpha": 1.0}}
    def V(verdict, sup=("v_xx",), blocked="none"): return {"verdict": verdict, "support": list(sup), "blocked_at": blocked, "coefficients": {"v_xx": 1.0}}
    ok = {}
    tr = {f"n{i}": T("H", False, True) for i in range(200)}; tr.update({f"m{i}": T("D", False, False) for i in range(200)}); tr.update({f"r{i}": T("A", True, False) for i in range(20)})
    vd = {k: V("MISSPECIFIED", ()) for k in tr}; 
    for i in range(20): vd[f"r{i}"] = V("CLAIM")
    vm = {k: vd[k] for k in list(tr)[:150]}; vw = {k: vd[k] for k in list(tr)[100:]}
    A = domanda_A(tr, vd); B = domanda_B(vm, vw)
    ok["400 opportunita', 0 false, accordo -> LIMITE_STRETTO"] = esito(A, B) == "LIMITE_STRETTO" and A["opportunita"] == 400
    vd2 = dict(vd); vd2["n0"] = V("CLAIM"); ok["claim su nullo -> CLAIM_FALSA_OSSERVATA"] = esito(domanda_A(tr, vd2), B) == "CLAIM_FALSA_OSSERVATA"
    vd3 = dict(vd); vd3["r0"] = V("CLAIM", ("v_xx", "v_x")); ok["supporto errato affermato -> CLAIM_FALSA_OSSERVATA"] = esito(domanda_A(tr, vd3), B) == "CLAIM_FALSA_OSSERVATA"
    vd4 = dict(vd); vd4["m0"] = V("CLAIM"); ok["claim su non rappresentabile -> CLAIM_FALSA_OSSERVATA"] = esito(domanda_A(tr, vd4), B) == "CLAIM_FALSA_OSSERVATA"
    vw2 = dict(vw); k = list(vw)[0]; vw2[k] = V("CLAIM") if vw[k]["verdict"] != "CLAIM" else V("NOT_IDENTIFIABLE"); ok["verdetto diverso su un condiviso -> DIVERGENZA_PIATTAFORMA"] = esito(A, domanda_B(vm, vw2)) == "DIVERGENZA_PIATTAFORMA"
    vw3 = dict(vw); vw3[k] = dict(vw[k], blocked_at="altro"); ok["blocked_at diverso -> DIVERGENZA"] = esito(A, domanda_B(vm, vw3)) == "DIVERGENZA_PIATTAFORMA"
    tr_p = {k: v for k, v in tr.items() if not k.startswith("m") or int(k[1:]) < 100}; vd_p = {k: vd[k] for k in tr_p}
    ok["300 opportunita' -> POTENZA_INSUFFICIENTE"] = esito(domanda_A(tr_p, vd_p), domanda_B({k: vd_p[k] for k in list(tr_p)[:10]}, {k: vd_p[k] for k in list(tr_p)[:10]})) == "POTENZA_INSUFFICIENTE"
    vd5 = dict(vd); vd5["r0"] = V("NOT_IDENTIFIABLE", ("v_xx", "v_x")); ok["supporto errato NON affermato = opportunita' in piu', non claim falsa"] = (domanda_A(tr, vd5)["opportunita"] == 401 and domanda_A(tr, vd5)["n_claim_false"] == 0)
    return ok

def sigillo():
    src = (BASE / "CDE_V13_BLIND_DISCOVERER_V0.py").read_text() + (BASE / "CDE_V11_BLIND_DISCOVERER_V0.py").read_text()
    letture = [l.strip() for l in src.splitlines() if re.search(r"sealed|truth\.json", l) and not l.strip().startswith("#") and "avvertenza" not in l and "NON legge" not in l and "non e' stato letto" not in l]
    def g(*a): return subprocess.check_output(["git", *a], cwd=ROOT, text=True).strip()
    truth_rel = "CDE_Scientific_Discovery/cde_v13_blind_out/sealed/truth.json"
    identico = g("diff", "--quiet", "HEAD", "--", truth_rel) == "" if subprocess.call(["git", "diff", "--quiet", "HEAD", "--", truth_rel], cwd=ROOT) == 0 else False
    commit_truth = g("log", "--format=%h %cI", "--", truth_rel).splitlines()
    commit_verd = g("log", "--format=%h %cI", "--", "CDE_Scientific_Discovery/cde_v13_blind_out/verdicts_mac.json").splitlines()
    gen = json.loads((OUT / "generation_envelope.json").read_text()); em = json.loads((OUT / "envelope_mac.json").read_text())
    return {"discoverer_legge_sealed": letture, "truth_identico_a_HEAD": identico, "commit_truth": commit_truth, "commit_verdicts": commit_verd,
            "stesso_commit": bool(commit_truth and commit_verd and commit_truth[-1].split()[0] == commit_verd[-1].split()[0]),
            "generazione_utc": gen.get("generato"), "esecuzione_mac_utc": em.get("eseguito_utc"),
            "sha256_truth_ora": hashlib.sha256((OUT / "sealed/truth.json").read_bytes()).hexdigest(),
            "sha256_truth_in_envelope": gen.get("truth_sha256"),
            "natura": "PROCEDURALE: nessuno sha della verita' negli envelope; verita' e verdetti nello stesso commit. Evidenza di cecita' = sorgente del discoverer + ordine temporale negli envelope."}

def main():
    ok = mutation_test(); print("== mutation test (prima del verdetto) ==")
    for k, v in ok.items(): print(f"  {'MORDE' if v else '*** NON MORDE ***'}  {k}")
    if not all(ok.values()): print("un cancello non morde: esito NON affidabile"); return 1
    s = sigillo(); print(f"\n== sigillo == natura: {s['natura']}\n  letture di sealed nel discoverer: {s['discoverer_legge_sealed'] or 'nessuna'}\n  truth identico a HEAD: {s['truth_identico_a_HEAD']}; stesso commit di verdetti: {s['stesso_commit']}\n  generazione {s['generazione_utc']}  esecuzione mac {s['esecuzione_mac_utc']}")
    vm = json.loads((OUT / "verdicts_mac.json").read_text()); vw = json.loads((OUT / "verdicts_win.json").read_text())
    truth = json.loads((OUT / "sealed/truth.json").read_text())
    verd = dict(vw); verd.update(vm)                       # sui condivisi vince il Mac (dichiarato)
    assert set(verd) == set(truth), "verdetti e verita' non coprono gli stessi casi"
    A = domanda_A(truth, verd); B = domanda_B(vm, vw); E = esito(A, B)
    print(f"\n== Domanda A: {A['n']} casi ==\n  nulli {A['nulli']} | non rappresentabili {A['non_rappresentabili']} | rappresentabili {A['rappresentabili']} (supporto errato prodotto: {A['rapp_supporto_errato']})")
    print(f"  OPPORTUNITA' DI MENTIRE: {A['opportunita']} (soglia {SOGLIA_OPPORTUNITA})   CLAIM FALSE: {A['n_claim_false']}   limite regola del tre: {A['limite_regola_del_tre']:.4f}")
    print(f"  claim corrette {A['claim_corrette']} / {A['rappresentabili']} rappresentabili (recall {A['recall_rappresentabili']:.3f}); errore coef. mediano {A['coef_err_mediano']}")
    for cls, c in sorted(A["per_classe"].items()): print(f"    classe {cls}: n={c['n']} corrette={c['claim_corrette']} false={c['claim_false']} verdetti={c['verdetti']}")
    for f in A["claim_false"]: print("    CLAIM FALSA:", f)
    print(f"\n== Domanda B: {B['n_condivisi']} condivisi == accordo pieno: {B['accordo_pieno']}; discrepanze: {len(B['discrepanze'])}")
    for d in B["discrepanze"][:20]: print("    ", d)
    print(f"\n  ESITO (§6): {E}")
    rep = {"run": "CDE_V13_BLIND_UNBLINDING_V0", "prereg": PREREG, "generato": datetime.now(timezone.utc).isoformat(), "sigillo": s, "domanda_A": A, "domanda_B": B, "esito": E, "mutation_test": ok,
           "nota_condivisi": "per la domanda A sui 100 condivisi conta il verdetto Mac"}
    (OUT / "unblinding_report.json").write_text(json.dumps(rep, indent=1, default=str)); print("\n  artefatto: cde_v13_blind_out/unblinding_report.json")
    return 0

if __name__ == "__main__":
    sys.exit(main())
