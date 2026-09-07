#!/usr/bin/env python3
"""Scorer blind-4 (prereg §4). Apre sealed/ solo dopo l'hash delle predizioni. Mutation test prima."""
import hashlib, importlib.util, json, re, sys
from pathlib import Path
BASE = Path(__file__).resolve().parent
ART = BASE.parent.parent / "artifacts"      # public layout (cde-reproducibility)
PAPER = BASE.parent.parent / "paper"
JUL = BASE.parent.parent / "baselines" / "julia"; OUT = ART / "cde_blind4_out"
def _L(n, f):
    s = importlib.util.spec_from_file_location(n, BASE / f); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def valuta(ann, truth, contributo):
    """ann: verdetti annotati; truth; contributo(cid, t, c_vero) -> f_t. Ritorna esito §4."""
    claims = [c for c in truth if ann[c]["verdict"] == "CLAIM"]
    viol, sotto, coperte, false_strette, corrette = [], 0, 0, 0, 0
    for c in claims:
        v = ann[c]; tr = truth[c]; X = v["risoluzione"]["X"]
        mancanti = [t for t in tr["true_support"] if t not in v["support"]]
        spurii = [t for t in v["support"] if t not in tr["true_support"]]
        if not mancanti and not spurii: corrette += 1
        else: false_strette += 1
        if mancanti and not spurii:
            sotto += 1
            f = {t: contributo(c, t) for t in mancanti}
            if all(fx < X for fx in f.values()): coperte += 1
            else: viol.append({"case": c, "cls": tr["cls"], "X": X, "contributi": f})
    verd_cambiati = sum(1 for c in truth if ann[c]["verdict"] != ann[c].get("verdict_originale", ann[c]["verdict"]))
    out = {"n_claim": len(claims), "corrette": corrette, "false_strette": false_strette, "sotto_supporto": sotto, "coperte": coperte,
           "violazioni": viol, "verdetti_cambiati": verd_cambiati, "X_mediana": (sorted(ann[c]["risoluzione"]["X"] for c in claims)[len(claims)//2] if claims else None)}
    if viol or verd_cambiati: out["verdetto"] = "REJECTED"
    elif len(claims) >= 30: out["verdetto"] = "CONFIRMED"
    else: out["verdetto"] = "INCONCLUSIVE"
    return out
def mutation_test():
    def T(sup): return {"cls": "C", "true_support": sup}
    def V(verdict, sup, X=0.01): return {"verdict": verdict, "support": sup, "risoluzione": {"X": X}}
    ok = {}
    tr = {f"c{i}": T(["v", "v_xx"]) for i in range(30)}; tr["s"] = T(["v", "v_xx", "div_vv_x"])
    an = {f"c{i}": V("CLAIM", ["v", "v_xx"]) for i in range(30)}; an["s"] = V("CLAIM", ["v", "v_xx"], X=0.01)
    ok["31 claim, sotto-supporto coperto -> CONFIRMED"] = valuta(an, tr, lambda c, t: 0.005)["verdetto"] == "CONFIRMED"
    ok["contributo mancante >= X -> REJECTED"] = valuta(an, tr, lambda c, t: 0.02)["verdetto"] == "REJECTED"
    an2 = {k: v for k, v in list(an.items())[:20]}; tr2 = {k: tr[k] for k in an2}; ok["< 30 claim -> INCONCLUSIVE"] = valuta(an2, tr2, lambda c, t: 0.005)["verdetto"] == "INCONCLUSIVE"
    an3 = dict(an); an3["c0"] = dict(an["c0"], verdict_originale="NOT_IDENTIFIABLE"); ok["verdetto cambiato dall'annotazione -> REJECTED"] = valuta(an3, tr, lambda c, t: 0.005)["verdetto"] == "REJECTED"
    an4 = dict(an); an4["c1"] = V("CLAIM", ["v", "v_xx", "v2"]); e = valuta(an4, tr, lambda c, t: 0.005); ok["termine spurio = falsa stretta, non sotto-supporto"] = e["false_strette"] == 2 and e["sotto_supporto"] == 1
    return ok
def main():
    ok = mutation_test(); print("== mutation test ==")
    for k, v in ok.items(): print(f"  {'MORDE' if v else '*** NON MORDE ***'}  {k}")
    if not all(ok.values()): return 1
    pa = OUT / "verdicts_annotati.json"
    if not pa.exists(): print("\nnessun verdicts_annotati.json: solo mutation test"); return 0
    sha_pred = hashlib.sha256(pa.read_bytes()).hexdigest()
    env = json.loads((OUT / "generation_envelope.json").read_text()); tp = OUT / "sealed/truth.json"
    sha_now = hashlib.sha256(tp.read_bytes()).hexdigest(); assert sha_now == env["truth_sha256"], "SIGILLO VIOLATO"
    runner = (BASE / "CDE_BLIND4_RUNNER_V0.py").read_text() + (BASE / "CDE_V13_BLIND_DISCOVERER_V0.py").read_text()
    sosp = [l.strip() for l in runner.splitlines() if re.search(r"sealed|truth\.json", l) and not l.strip().startswith("#") and "non e' stato letto" not in l and "mai" not in l and "Legge solo" not in l]
    d = json.loads(pa.read_text()); ann = d["verdetti"]; orig = json.loads((OUT / "verdicts_mac.json").read_text())
    for c in ann: ann[c]["verdict_originale"] = orig[c]["verdict"]
    truth = json.loads(tp.read_text()); RIS = _L("ris", "CDE_RISOLUZIONE_CLAIM_V0.py"); pub = json.loads((OUT / "public_meta.json").read_text())
    cache = {}
    def contributo(c, t):
        if c not in cache: cache[c] = RIS.ricostruisci_Ab(OUT / "cases" / f"{c}.npz", pub[c]["hz"])
        A, b = cache[c]; return RIS.contributo(A, b, t, RIS.coefficienti_veri(truth[c]["model"])[t])
    e = valuta(ann, truth, contributo)
    print(f"\n== BLIND-4: {len(truth)} casi, k*={d['k_star']}, sigillo intatto, runner cieco: {not sosp} ==")
    print(f"  CLAIM {e['n_claim']}: corrette {e['corrette']}, false strette {e['false_strette']} (di cui sotto-supporto {e['sotto_supporto']}, coperte dal limite {e['coperte']}); X mediana {e['X_mediana']}")
    print(f"  violazioni di H1: {len(e['violazioni'])}; verdetti cambiati: {e['verdetti_cambiati']}")
    for v in e["violazioni"]: print("    VIOLA:", v)
    print(f"\n  VERDETTO: {e['verdetto']}")
    (OUT / "scoring.json").write_text(json.dumps({"audit_cecita": {"sha256_predizioni": sha_pred, "sha256_verita": sha_now, "riferimenti_sospetti": sosp}, "esito": e, "mutation_test": ok}, indent=1)); return 0
if __name__ == "__main__":
    sys.exit(main())
