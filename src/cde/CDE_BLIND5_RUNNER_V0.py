#!/usr/bin/env python3
"""Blind-4 runner: il discoverer V13 INVARIATO (ladder v2.1), puntato sulla cartella
del blind-4. Legge solo cases/ e public_meta.json. Poi annota ogni CLAIM con il
limite di risoluzione per k* (letto da cde_risoluzione_claim_out/esito_stage1.json)."""
import hashlib, importlib.util, json, sys, time
from pathlib import Path
BASE = Path(__file__).resolve().parent
ART = BASE.parent.parent / "artifacts"      # public layout (cde-reproducibility)
PAPER = BASE.parent.parent / "paper"
JUL = BASE.parent.parent / "baselines" / "julia"; OUT = ART / "cde_blind5_out"
def _L(n, f):
    s = importlib.util.spec_from_file_location(n, BASE / f); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
D13 = _L("d13", "CDE_V13_BLIND_DISCOVERER_V0.py"); RIS = _L("ris", "CDE_RISOLUZIONE_CLAIM_V0.py")
def main():
    D13.OUT = OUT                                   # unica differenza dalla V13
    sys.argv = ["blind4", "--da", "0", "--a", "119", "--nodo", "mac"]
    t0 = time.time(); D13.main()
    k = 1.0; pub = json.loads((OUT / "public_meta.json").read_text())      # v2 proiettato, k = 1 (prereg blind-5)
    verd = json.loads((OUT / "verdicts_mac.json").read_text()); ann = {}
    for cid, v in verd.items():
        ann[cid] = dict(v)
        if v["verdict"] == "CLAIM":
            A, b = RIS.ricostruisci_Ab(OUT / "cases" / f"{cid}.npz", pub[cid]["hz"])
            ann[cid]["risoluzione"] = RIS.annota_v2(A, b, v["support"], v["coefficients"])
    (OUT / "verdicts_annotati.json").write_text(json.dumps({"k_star": k, "versione_limite": "v2 proiettato (nota 2026-09-07)", "verdetti": ann}, indent=1, default=str))
    print(f"annotati {sum('risoluzione' in a for a in ann.values())} CLAIM con k*={k}; sha256 verdicts_annotati: {hashlib.sha256((OUT / 'verdicts_annotati.json').read_bytes()).hexdigest()[:16]}  ({time.time()-t0:.0f}s)")
if __name__ == "__main__":
    main()
