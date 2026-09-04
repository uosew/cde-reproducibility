"""CDE V13 — discoverer della campagna cieca su larga scala.

Preregistrazione: PREREGISTRAZIONE_CDE_V13_REPLICA_LARGA_SCALA_2026_08_02.md

Il discoverer V11 e' cablato su `cde_v11_blind_out` (riga 27) e su tutti i casi
(riga 153). Questo aggiunge due sole cose: la cartella della campagna e un
intervallo di casi, per poter ripartire il lavoro fra i nodi come previsto
in §4 della preregistrazione.

**La ladder resta quella della v2.1, importata e non ricopiata.** La §1 della
preregistrazione dice che nessun gate va toccato, e importare e' l'unico modo
di garantirlo: una copia, per quanto fedele, potrebbe divergere senza che
nessuno se ne accorga.

Cecita': si leggono `public_meta.json` e i casi, **mai** `sealed/truth.json`.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
ART = BASE.parent.parent / "artifacts"      # public layout (cde-reproducibility)
PAPER = BASE.parent.parent / "paper"
ROOT = BASE.parent
OUT = ART / "cde_v13_blind_out"
PREREG = "PREREGISTRAZIONE_CDE_V13_REPLICA_LARGA_SCALA_2026_08_02.md"

RGB_spec = importlib.util.spec_from_file_location(
    "runtime_guard_bootstrap", BASE / "runtime_guard_bootstrap.py")
RGB = importlib.util.module_from_spec(RGB_spec)
RGB_spec.loader.exec_module(RGB)

import numpy as np                                    # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "disc11", BASE / "CDE_V11_BLIND_DISCOVERER_V1.py")
D11 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(D11)

R, GATE = D11.R, D11.GATE


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--da", type=int, required=True, help="primo caso, incluso")
    ap.add_argument("--a", type=int, required=True, help="ultimo caso, incluso")
    ap.add_argument("--nodo", required=True, help="etichetta del nodo (mac/win)")
    args = ap.parse_args()

    t0 = time.time()
    guard = RGB.enforce_runtime_guard(strict=True)
    print(f"nodo {args.nodo} — {platform.platform()} — guard {guard.get('status')}",
          flush=True)

    print("== calibrazione tau1/tau2 (rehearsal V2 GO, non-blind) ==", flush=True)
    tau1, tau2, p1c, p2c = D11.calibrate_taus()
    print(f"   tau1={tau1:.4f} tau2={tau2:.4f}  ({time.time() - t0:.0f}s)",
          flush=True)

    public = json.loads((OUT / "public_meta.json").read_text())
    tutti = sorted((OUT / "cases").glob("case_*.npz"))
    casi = [p for p in tutti if args.da <= int(p.stem.split("_")[1]) <= args.a]
    print(f"   assegnati {len(casi)} casi ({args.da:03d}-{args.a:03d}) "
          f"su {len(tutti)} totali\n", flush=True)

    verdetti = {}
    for n, p in enumerate(casi, 1):
        cid = p.stem
        out = D11.eval_case(p, public[cid]["hz"])
        if isinstance(out, dict):
            verdetti[cid] = out
        else:
            feats, p1s, p2s, p3s = out
            data_ok = bool(max(p1s) <= tau1 and max(p2s) <= tau2)
            lib_ok = bool(max(p3s) < GATE)
            Fp = {k: np.concatenate([feats[i][k] for i in range(4)])
                  for k in feats[0]}
            selp = R.select_thermal(Fp, sel_seed=7)
            r_hold = R.transfer_resid(selp["coefficients"], feats[4])
            swp = R.swap_rel(Fp, set(selp["support"]), selp["fit_rel_resid"])
            st = {"operator_valid": True,
                  "data_adequacy": data_ok,
                  "library_adequacy": lib_ok,
                  "support_stable": bool(selp["support"]),
                  "fit_gate": bool(selp["fit_rel_resid"] < GATE),
                  "transfer_gate": bool(r_hold < GATE),
                  "identifiability_gate": not swp["not_identifiable"],
                  "replication": True}
            v = D11.ladder21(st)
            verdetti[cid] = {
                "verdict": v["verdict"], "blocked_at": v["blocked_at"],
                "data_adequacy": data_ok, "library_adequacy": lib_ok,
                "support": selp["support"],
                "coefficients": selp["coefficients"],
                "fit_rel_resid": float(selp["fit_rel_resid"]),
                "r_holdout": float(r_hold)}
        if n % 25 == 0 or n == len(casi):
            print(f"   {n}/{len(casi)}  ({time.time() - t0:.0f}s)", flush=True)

    dest = OUT / f"verdicts_{args.nodo}.json"
    dest.write_text(json.dumps(verdetti, indent=1, default=str))
    (OUT / f"envelope_{args.nodo}.json").write_text(json.dumps({
        "prereg": PREREG, "nodo": args.nodo,
        "intervallo": [args.da, args.a], "casi": len(verdetti),
        "eseguito_utc": datetime.now(timezone.utc).isoformat(),
        "durata_s": round(time.time() - t0, 1),
        "runtime_guard": guard, "platform": platform.platform(),
        "tau1": tau1, "tau2": tau2,
        "avvertenza": ("Verdetti ciechi: sealed/truth.json non e' stato letto "
                       "da questo processo.")}, indent=1, default=str))
    print(f"\n{len(verdetti)} verdetti in {time.time() - t0:.0f}s -> {dest.name}")


if __name__ == "__main__":
    main()
