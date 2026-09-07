#!/usr/bin/env python3
"""Analizzatore Stage 1 (prereg §3): k* = il piu' piccolo k con 0 violazioni. Mutation test prima."""
import json, sys
from pathlib import Path
import numpy as np
BASE = Path(__file__).resolve().parent
ART = BASE.parent.parent / "artifacts"      # public layout (cde-reproducibility)
PAPER = BASE.parent.parent / "paper"
JUL = BASE.parent.parent / "baselines" / "julia"; OUT = ART / "cde_risoluzione_claim_out"; KS = ("1.0", "2.0")
def esito(righe):
    out = {"n": len(righe), "n_false": sum(r["falsa"] for r in righe), "per_k": {}}
    for k in KS:
        viol = [(r["case"], r["k"][k]["violazioni"]) for r in righe if r["k"][k]["violazioni"]]
        X = [r["k"][k]["X"] for r in righe]
        cop = [r for r in righe if r["falsa"]]; coperte = sum(1 for r in cop if not r["k"][k]["violazioni"])
        out["per_k"][k] = {"violazioni": viol, "n_violazioni": len(viol), "X_mediana": float(np.median(X)), "X_max": float(max(X)), "copertura_false": f"{coperte}/{len(cop)}"}
    sound = [k for k in KS if out["per_k"][k]["n_violazioni"] == 0]
    out["k_star"] = sound[0] if sound else None
    out["esito"] = "PROMISING" if sound and out["per_k"][sound[0]]["X_mediana"] <= 0.05 * float(sound[0]) else "NOT_PROMISING"
    return out
def mutation_test():
    def r(falsa, viol1, viol2, X1=0.01, X2=0.02): return {"case": "c", "falsa": falsa, "k": {"1.0": {"X": X1, "violazioni": viol1}, "2.0": {"X": X2, "violazioni": viol2}}}
    ok = {}
    base = [r(True, [], []), r(False, [], [])]; e = esito(base); ok["0 violazioni -> k*=1, PROMISING"] = e["k_star"] == "1.0" and e["esito"] == "PROMISING"
    e = esito([r(True, ["div_vv_x"], []), r(False, [], [])]); ok["k=1 viola, k=2 no -> k*=2"] = e["k_star"] == "2.0" and e["esito"] == "PROMISING"
    e = esito([r(True, ["div_vv_x"], ["div_vv_x"])]); ok["entrambi violano -> NOT_PROMISING"] = e["k_star"] is None and e["esito"] == "NOT_PROMISING"
    e = esito([r(False, [], [], X1=0.2, X2=0.4)]); ok["X vacuo (mediana > gate) -> NOT_PROMISING"] = e["esito"] == "NOT_PROMISING"
    e = esito([r(True, ["v"], []), r(True, [], [])]); ok["copertura false contata per k"] = e["per_k"]["1.0"]["copertura_false"] == "1/2" and e["per_k"]["2.0"]["copertura_false"] == "2/2"
    return ok
def main():
    ok = mutation_test(); print("== mutation test ==")
    for k, v in ok.items(): print(f"  {'MORDE' if v else '*** NON MORDE ***'}  {k}")
    if not all(ok.values()): return 1
    p = OUT / "stage1.json"
    if not p.exists(): print("\nnessuno stage1.json: solo mutation test"); return 0
    d = json.loads(p.read_text()); e = esito(d["righe"])
    print(f"\n== Stage 1 diagnostico, {e['n']} claim ({e['n_false']} false), prereg {d['prereg_sha256'][:12]}… ==")
    for k in KS:
        x = e["per_k"][k]; print(f"  k={k}: violazioni {x['n_violazioni']}  X mediana {x['X_mediana']:.4f} max {x['X_max']:.4f}  copertura delle false {x['copertura_false']}")
        for c, v in x["violazioni"][:10]: print(f"      viola: {c} {v}")
    print(f"\n  k* = {e['k_star']}   ESITO: {e['esito']}")
    (OUT / "esito_stage1.json").write_text(json.dumps({"esito": e, "mutation_test": ok, "prereg_sha256": d["prereg_sha256"]}, indent=1)); return 0
if __name__ == "__main__":
    sys.exit(main())
