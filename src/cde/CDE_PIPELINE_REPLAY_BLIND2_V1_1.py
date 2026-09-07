#!/usr/bin/env python3
"""Regressione: V0 e V1 rigiocate sul pannello SIGILLATO del blind 2.

Non e' evidenza cieca (la verita' del pannello e' aperta dal 2026-08-24):
e' un controllo che la pipeline di produzione riproduca, caso per caso, il
braccio `corretto` validato. Ogni divergenza deve essere spiegata da una
correzione dichiarata (F1..F6), altrimenti e' un bug.
"""
import importlib.util, json, sys, time
from pathlib import Path
import numpy as np
BASE = Path(__file__).resolve().parent
ART = BASE.parent.parent / "artifacts"      # public layout (cde-reproducibility)
PAPER = BASE.parent.parent / "paper"
JUL = BASE.parent.parent / "baselines" / "julia"
def L(n, f):
    s = importlib.util.spec_from_file_location(n, BASE / f)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
RUN2 = L("run2", "CDE_BLIND_PDE2_RUNNER_V0.py")
V11 = L("v11", "CDE_PDE_PIPELINE_GATED_V1_1.py"); V1 = V11.V1; V0 = V1.V0
RUN1, NOP, CASES = RUN2.RUN1, RUN2.NOP, RUN2.CASES
WX, WT = RUN2.WX, RUN2.WT
sigillate = {c["case_id"]: c for c in json.loads((RUN2.OUT / "predictions.json").read_text())["casi"]}
ids = [c["case_id"] for c in json.loads((CASES / "public_manifest.json").read_text())["casi"]]
righe, t0 = [], time.time()
for cid in ids:
    d = np.load(CASES / f"{cid}.npz"); x, t = d["x"], d["t"]
    seme = RUN2.SEME_CENTRI + int(cid.split("_")[1])
    atteso = sigillate[cid].get("corretto", {}).get("decisione")
    centers = RUN1._centri(x, t, seme)
    if not centers:
        righe.append((cid, atteso, "ABSTAIN_GEOMETRIA", "ABSTAIN_GEOMETRIA")); continue
    A, b, pf = RUN1.preflight(x, t, d["U"], centers)
    if any(not (pf[k] < g) for k, g in (("P1_quadratura", RUN2.GATE_P1), ("P2_famiglie", RUN2.GATE_P2), ("P3_holdout", RUN2.GATE_P3))):
        righe.append((cid, atteso, "ABSTAIN_PREFLIGHT", "ABSTAIN_PREFLIGHT")); continue
    def feat(U, s):
        F = NOP.weak_features_nop(x, t, U, WX, WT, RUN1._centri(x, t, s), RUN2.TERMS, "simpson", NOP.BumpA)
        return NOP.to_Ab(F, RUN2.TERMS)
    A2, b2 = feat(d["U2"], seme + 313); A3, b3 = feat(d["U3"], seme + 517)
    r0 = V0.decidi(A, b, A2, b2, A3, b3, seme=seme + 7)
    r1 = V11.decidi(A, b, A2, b2, A3, b3, seme=seme + 7, centers=centers, wx=WX, wt=WT)
    righe.append((cid, atteso, r0["decisione"], r1["decisione"], round(r1["risoluzione"]["X"], 4) if "risoluzione" in r1 else ""))
print(f"{'caso':8} {'blind2 corretto':24} {'V0 produzione':24} {'V1.1':24} X")
div0 = div1 = 0
for r in righe:
    cid, att, d0, d1 = r[:4]; fr = r[4] if len(r) > 4 else ""
    m0 = " " if d0 == att else "*"; m1 = " " if d1 == att else "*"
    div0 += d0 != att; div1 += d1 != att
    print(f"{cid:8} {att:24} {m0}{d0:23} {m1}{d1:23} {fr}")
print(f"\ndivergenze dal braccio validato: V0 = {div0}/{len(righe)}   V1 = {div1}/{len(righe)}   ({time.time()-t0:.0f}s)")
json.dump({"righe": righe, "div_V0": div0, "div_V1": div1}, open(ART / "cde_blind_pde2_out" / "replay_pipeline_V0_V11.json", "w"), indent=1)
