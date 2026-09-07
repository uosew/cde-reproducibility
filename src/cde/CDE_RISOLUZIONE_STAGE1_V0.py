#!/usr/bin/env python3
"""Stage 1 diagnostico (prereg §3) sulla V13, verita' APERTA: non e' conferma."""
import hashlib, importlib.util, json, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
BASE = Path(__file__).resolve().parent
ART = BASE.parent.parent / "artifacts"      # public layout (cde-reproducibility)
PAPER = BASE.parent.parent / "paper"
JUL = BASE.parent.parent / "baselines" / "julia"; V13 = ART / "cde_v13_blind_out"; OUT = ART / "cde_risoluzione_claim_out"
def _L(n, f):
    s = importlib.util.spec_from_file_location(n, BASE / f); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
RIS = _L("ris", "CDE_RISOLUZIONE_CLAIM_V0.py")
PREREG = "PREREGISTRAZIONE_LIMITE_RISOLUZIONE_CLAIM_2026-09-03.md"
def main():
    OUT.mkdir(exist_ok=True); t0 = time.time(); RIS.R.RGB.enforce_runtime_guard(strict=True) if hasattr(RIS.R, "RGB") else None
    truth = json.loads((V13 / "sealed/truth.json").read_text()); pub = json.loads((V13 / "public_meta.json").read_text())
    vm = json.loads((V13 / "verdicts_mac.json").read_text()); vw = json.loads((V13 / "verdicts_win.json").read_text()); verd = dict(vw); verd.update(vm)
    false = [c for c in sorted(truth) if verd[c]["verdict"] == "CLAIM" and truth[c]["representable"] and not truth[c]["is_null"] and sorted(verd[c]["support"]) != sorted(truth[c]["true_support"])]
    corr = [c for c in sorted(truth) if verd[c]["verdict"] == "CLAIM" and truth[c]["representable"] and sorted(verd[c]["support"]) == sorted(truth[c]["true_support"])]
    rng = np.random.default_rng(20260903); camp = false + sorted(rng.choice(corr, size=30, replace=False).tolist())
    print(f"campione: {len(false)} false + 30 corrette su {len(corr)} = {len(camp)} casi", flush=True)
    righe = []
    for n, cid in enumerate(camp, 1):
        A, b = RIS.ricostruisci_Ab(V13 / "cases" / f"{cid}.npz", pub[cid]["hz"])
        v = verd[cid]; tr = truth[cid]; cv = RIS.coefficienti_veri(tr["model"])
        r = {"case": cid, "cls": tr["cls"], "falsa": cid in false, "supporto": v["support"], "vero": tr["true_support"], "fit_rel_resid": v["fit_rel_resid"], "k": {}}
        mancanti = [t for t in tr["true_support"] if t not in v["support"]]
        r["contributi_mancanti"] = {t: RIS.contributo(A, b, t, cv[t]) for t in mancanti}
        for k in RIS.K_CANDIDATI:
            an = RIS.annota(A, b, v["support"], v["coefficients"], k)
            r["k"][str(k)] = {"X": an["X"], "c_min": an["c_min"], "violazioni": [t for t in mancanti if r["contributi_mancanti"][t] >= an["X"]]}
        righe.append(r)
        print(f"  {n:2}/{len(camp)} {cid} {'FALSA' if r['falsa'] else 'ok   '} fit={v['fit_rel_resid']:.4f} X1={r['k']['1.0']['X']:.4f} X2={r['k']['2.0']['X']:.4f} mancanti={ {t: round(f, 4) for t, f in r['contributi_mancanti'].items()} } viol k1={r['k']['1.0']['violazioni']} k2={r['k']['2.0']['violazioni']}  ({time.time()-t0:.0f}s)", flush=True)
        (OUT / "stage1.partial.json").write_text(json.dumps(righe, indent=1))
    art = {"run": "CDE_RISOLUZIONE_STAGE1_V0", "prereg": PREREG, "prereg_sha256": hashlib.sha256((BASE / PREREG).read_bytes()).hexdigest(), "generato": datetime.now(timezone.utc).isoformat(),
           "campione": {"false": false, "corrette": camp[len(false):], "seme": 20260903}, "righe": righe, "elapsed_s": round(time.time() - t0, 1), "avvertenza": "diagnostico a verita' aperta: non conferma nulla (prereg §0, §3)"}
    (OUT / "stage1.json").write_text(json.dumps(art, indent=1)); print(f"\nelapsed {art['elapsed_s']}s", flush=True)
if __name__ == "__main__":
    main()
