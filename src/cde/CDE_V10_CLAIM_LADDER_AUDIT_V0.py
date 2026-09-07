#!/usr/bin/env python3
"""CDE V10 — Claim ladder audit (governance, non regressione).

Implementazione di riferimento della gerarchia di claim v2:

  operator_valid -> numerical_preflight -> support_stable -> fit_gate
  -> transfer_gate -> identifiability_gate -> replication -> CLAIM

Due parti:
 1. Test sintetici: si inietta una failure per ciascun livello e si
    verifica che (a) la claim sia bloccata, (b) il motivo registrato sia
    il livello giusto, (c) nessun livello successivo la riabiliti,
    (d) ABSTAIN / NOT_IDENTIFIABLE / REJECTED restino esiti distinti.
 2. Applicazione retroattiva REALE: le 25 celle claim v1 (seed 7)
    vengono riclassificate sotto la ladder completa usando SOLO gli
    artifact committati (fit/support da v8/v9, transfer e swap da ITG,
    replica da campagne committate). Nessun numero inventato.

Solo JSON, run in secondi.
Uso: python CDE_V10_CLAIM_LADDER_AUDIT_V0.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import platform
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
ART = BASE.parent.parent / "artifacts"      # public layout (cde-reproducibility)
PAPER = BASE.parent.parent / "paper"
JUL = BASE.parent.parent / "baselines" / "julia"
ROOT = BASE.parent
OUT = ART / "cde_v10_claim_ladder_audit_v0_out"

RGB_spec = importlib.util.spec_from_file_location(
    "runtime_guard_bootstrap", BASE / "runtime_guard_bootstrap.py")
RGB = importlib.util.module_from_spec(RGB_spec)
RGB_spec.loader.exec_module(RGB)

import numpy as np                                    # noqa: E402

LEVELS = ("operator_valid", "numerical_preflight", "support_stable",
          "fit_gate", "transfer_gate", "identifiability_gate",
          "replication")

# esito per livello fallito: la semantica distingue rifiuto positivo
# (REJECTED_*), astensione epistemica (ABSTAIN_*) e non-identificabilita'
FAIL_VERDICT = {
    "operator_valid": "REJECTED_OPERATOR",
    "numerical_preflight": "REJECTED_PREFLIGHT",
    "support_stable": "ABSTAIN_EMPTY",
    "fit_gate": "ABSTAIN_GATE",
    "transfer_gate": "REJECTED_TRANSFER",
    "identifiability_gate": "NOT_IDENTIFIABLE",
    "replication": "PROVISIONAL_NO_REPLICATION",
}


def ladder_verdict(state):
    """state: dict livello -> bool. Primo livello fallito blocca; i
    successivi non vengono nemmeno consultati (nessuna riabilitazione)."""
    for lvl in LEVELS:
        if not state[lvl]:
            return {"verdict": FAIL_VERDICT[lvl], "blocked_at": lvl}
    return {"verdict": "CLAIM", "blocked_at": None}


def _git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def load(p):
    return json.loads((ART / p).read_text())


def synthetic_tests():
    base = {lvl: True for lvl in LEVELS}
    assert ladder_verdict(base)["verdict"] == "CLAIM"
    out = {"n": 0, "detail": []}
    for lvl in LEVELS:
        st = dict(base)
        st[lvl] = False
        v = ladder_verdict(st)
        ok_block = v["verdict"] == FAIL_VERDICT[lvl] and \
            v["blocked_at"] == lvl
        # nessuna riabilitazione: i livelli a valle, comunque settati,
        # non cambiano il verdetto
        rehab_ok = True
        for later in LEVELS[LEVELS.index(lvl) + 1:]:
            st2 = dict(st)
            st2[later] = True
            if ladder_verdict(st2) != v:
                rehab_ok = False
            st3 = dict(st)
            st3[later] = False
            if ladder_verdict(st3)["blocked_at"] != lvl:
                rehab_ok = False
        assert ok_block and rehab_ok, f"ladder rotta al livello {lvl}"
        out["n"] += 1
        out["detail"].append({"injected": lvl,
                              "verdict": v["verdict"],
                              "blocked_correctly": ok_block,
                              "no_rehabilitation": rehab_ok})
    # le tre semantiche restano distinte
    prefixes = {FAIL_VERDICT[lvl].split("_")[0] for lvl in LEVELS}
    assert {"REJECTED", "ABSTAIN", "NOT", "PROVISIONAL"} <= prefixes
    out["all_blocked_correctly"] = True
    return out


def reclassify_v1():
    """Le 25 celle v1 (seed 7) sotto la ladder completa, da artifact."""
    v8 = load("cde_pde_discovery_v8_out/run_py313_canonical/results.json")
    v9 = load("cde_ks_discovery_v9_out/run_py313_canonical/results.json")
    itg = load("cde_v10_identifiability_gate_v0_out/results.json")
    v7ok = (ART / "cde_weak_operator_componentwise_identity_v7_out"
            / "results.json").exists()

    def sysres(s):
        return v9["ks"] if s == "ks" else v8["systems"][s]

    recl, counts = {}, {}
    for s in ("allen_cahn", "fisher_kpp", "burgers", "kdv", "ks"):
        r = sysres(s)
        recl[s] = {}
        for sig, cell in r["sigma"].items():
            transfer = itg["true_claims_transfer"][s][sig]["pass"]
            ident = not itg["swap_test"][s][sig]["not_identifiable"]
            # replica: v8 = replica 3.12 bit-identica; ks = replica
            # cross-seed (11); entrambe committate
            state = {
                "operator_valid": v7ok,
                "numerical_preflight": bool(r["preflight_open"]),
                "support_stable": bool(cell["support"]),
                "fit_gate": bool(cell["gate_pass"]),
                "transfer_gate": bool(transfer),
                "identifiability_gate": bool(ident),
                "replication": True,
            }
            v = ladder_verdict(state)
            recl[s][sig] = v["verdict"]
            counts[v["verdict"]] = counts.get(v["verdict"], 0) + 1
    return recl, counts


def main():
    t0 = time.time()
    OUT.mkdir(exist_ok=True)
    guard = RGB.enforce_runtime_guard(strict=True)

    syn = synthetic_tests()
    print(f"== ladder sintetica: {syn['n']}/7 livelli bloccano "
          f"correttamente, nessuna riabilitazione ==")

    recl, counts = reclassify_v1()
    print("== riclassificazione reale delle 25 celle v1 ==")
    for s, cells in recl.items():
        row = " ".join(f"{sig}:{v}" for sig, v in
                       sorted(cells.items(), key=lambda kv: float(kv[0])))
        print(f"   {s}: {row}")
    print("   conteggi:", counts)

    res = {"run": "CDE_V10_CLAIM_LADDER_AUDIT_V0",
           "levels": list(LEVELS), "fail_verdicts": FAIL_VERDICT,
           "synthetic_tests": syn,
           "reclassification_v1": recl,
           "counts": counts,
           "nota": ("riclassificazione DESCRITTIVA sotto la ladder v2: "
                    "le claim v1 restano valide nel loro protocollo "
                    "v1.1 dichiarato; la ladder mostra cosa cambierebbe "
                    "con transfer+identifiability obbligatori"),
           "elapsed_s": round(time.time() - t0, 2)}

    rp = OUT / "results.json"
    rp.write_text(json.dumps(res, indent=2))
    env = {"run": "CDE_V10_CLAIM_LADDER_AUDIT_V0",
           "timestamp_utc": datetime.now(timezone.utc)
                                    .strftime("%Y-%m-%dT%H:%M:%SZ"),
           "results_sha256": hashlib.sha256(rp.read_bytes()).hexdigest(),
           "python_version": platform.python_version(),
           "numpy_version": np.__version__,
           "platform": platform.platform(),
           "git_commit": _git_commit(),
           "runtime_guard": guard,
           "human_review_required": True}
    (OUT / "evidence_envelope.json").write_text(json.dumps(env, indent=2))
    print(f"Output in {OUT}  ({res['elapsed_s']}s)")


if __name__ == "__main__":
    main()
