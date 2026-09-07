#!/usr/bin/env python3
"""CDE V11 Blind Challenge — UNBLINDING V1 (scoring a denominatori separati).

PREREGISTRATION_V11_BLIND_V1_2026_07_31.md @ de395f79. Verifica sigillo
(hash + ordine commit: truth V0 precede verdicts_v1), poi gate:
G1 zero false claim; G4 zero CLAIM sui nulli; G5 err mediano < 5%;
G6 holdout >= 90%; G2' recovery su rappresentabili con dati sani >= 90%;
G3' misspec detection >= 90%; G8 preflight false rejection <= 10%;
G9 MISSPECIFIED precision >= 80% (recall riportato); potenza per classe.

Uso: python CDE_V11_BLIND_UNBLINDING_V1.py
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
OUT = ART / "cde_v11_blind_out"
PREREG = "PREREGISTRATION_V11_BLIND_V1_2026_07_31.md @ de395f79"

RGB_spec = importlib.util.spec_from_file_location(
    "runtime_guard_bootstrap", BASE / "runtime_guard_bootstrap.py")
RGB = importlib.util.module_from_spec(RGB_spec)
RGB_spec.loader.exec_module(RGB)

import numpy as np                                    # noqa: E402

DETECT_OK = {"MISSPECIFIED", "NOT_IDENTIFIABLE", "ABSTAIN_GATE",
             "ABSTAIN_EMPTY", "REJECTED_TRANSFER"}


def _git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT,
                                   text=True).strip()


def first_commit_time(path):
    out = _git("log", "--follow", "--format=%ct", "--", path)
    times = [int(x) for x in out.splitlines() if x.strip()]
    return min(times) if times else None


def main():
    t0 = time.time()
    guard = RGB.enforce_runtime_guard(strict=True)

    truth = json.loads((OUT / "sealed/truth.json").read_text())
    verd = json.loads((OUT / "verdicts_v1.json").read_text())
    gen_env = json.loads((OUT / "generator_envelope.json").read_text())
    sha_now = hashlib.sha256(
        (OUT / "sealed/truth.json").read_bytes()).hexdigest()
    assert sha_now == gen_env["truth_sha256"], "SIGILLO VIOLATO: hash"
    t_truth = first_commit_time(
        "CDE_Scientific_Discovery/cde_v11_blind_out/sealed/truth.json")
    t_verd = first_commit_time(
        "CDE_Scientific_Discovery/cde_v11_blind_out/verdicts_v1.json")
    assert t_truth and t_verd and t_truth <= t_verd, \
        "SIGILLO VIOLATO: ordine commit"
    print(f"== sigillo verificato ({t_truth} <= {t_verd}) ==")

    per_class, false_claims, coef_errs, hold_pass = {}, [], [], []
    rep_data_ok = rep_recovered = rep_total = rep_pf_rej = 0
    mis_total = mis_det = 0
    null_total = null_claim = 0
    missp_verdicts = missp_correct = missp_on_nonrep = 0
    for cid, tr in truth.items():
        v = verd[cid]
        cls = tr["cls"]
        d = per_class.setdefault(cls, {"n": 0, "verdicts": {},
                                       "support_ok": 0})
        d["n"] += 1
        d["verdicts"][v["verdict"]] = d["verdicts"].get(v["verdict"], 0) + 1
        claimed = v["verdict"] == "CLAIM"
        if v["verdict"] == "MISSPECIFIED":
            missp_verdicts += 1
            if tr["is_null"] or not tr["representable"]:
                missp_correct += 1
            if not tr["representable"] and not tr["is_null"]:
                missp_on_nonrep += 1
        if tr["is_null"]:
            null_total += 1
            if claimed:
                null_claim += 1
                false_claims.append({"case": cid, "cls": cls,
                                     "reason": "claim su nullo"})
        elif tr["representable"]:
            rep_total += 1
            if v["verdict"] == "REJECTED_PREFLIGHT":
                rep_pf_rej += 1
            if v.get("data_adequacy", False):
                rep_data_ok += 1
            sup_ok = claimed and sorted(v["support"]) == \
                sorted(tr["true_support"])
            if sup_ok:
                rep_recovered += 1
                d["support_ok"] += 1
                a_hat = v["coefficients"].get("v_xx")
                if a_hat is not None:
                    coef_errs.append(
                        abs(a_hat - tr["model"]["alpha"])
                        / tr["model"]["alpha"])
                hold_pass.append(v["r_holdout"] < 0.05)
            elif claimed:
                false_claims.append({"case": cid, "cls": cls,
                                     "reason": "supporto errato",
                                     "support": v["support"],
                                     "true": tr["true_support"]})
        else:
            mis_total += 1
            if v["verdict"] in DETECT_OK:
                mis_det += 1
            elif claimed:
                false_claims.append({"case": cid, "cls": cls,
                                     "reason": "claim su non "
                                               "rappresentabile",
                                     "support": v["support"]})

    med_err = float(np.median(coef_errs)) if coef_errs else None
    g2p = rep_recovered / rep_data_ok if rep_data_ok else None
    g3p = mis_det / mis_total if mis_total else None
    g8 = rep_pf_rej / rep_total if rep_total else None
    g9p = missp_correct / missp_verdicts if missp_verdicts else None
    g9r = missp_on_nonrep / mis_total if mis_total else None
    gates = {
        "G1_zero_false_claims": len(false_claims) == 0,
        "G4_null_claims": (null_claim, null_total, null_claim == 0),
        "G5_median_coef_err": (med_err, bool(med_err is not None
                                             and med_err < 0.05)),
        "G6_holdout": (sum(hold_pass), len(hold_pass),
                       bool(hold_pass and sum(hold_pass)
                            / len(hold_pass) >= 0.90)),
        "G2p_recovery_data_ok": (g2p, rep_recovered, rep_data_ok,
                                 bool(g2p is not None and g2p >= 0.90)),
        "G3p_misspec_detection": (g3p, mis_det, mis_total,
                                  bool(g3p is not None and g3p >= 0.90)),
        "G8_preflight_false_rejection": (g8, rep_pf_rej, rep_total,
                                         bool(g8 is not None
                                              and g8 <= 0.10)),
        "G9_missp_precision": (g9p, missp_correct, missp_verdicts,
                               bool(g9p is not None and g9p >= 0.80)),
        "G9_missp_recall_nonrep": (g9r, missp_on_nonrep, mis_total),
    }
    report = {"run": "CDE_V11_BLIND_UNBLINDING_V1", "prereg": PREREG,
              "seal_verified": True, "n_cases": len(truth),
              "per_class": per_class, "false_claims": false_claims,
              "P_claim_errata": len(false_claims) / len(truth),
              "coef_err_median": med_err,
              "gates": gates,
              "elapsed_s": round(time.time() - t0, 2)}

    print(f"== UNBLINDING V1 su {len(truth)} casi ==")
    for cls in sorted(per_class):
        d = per_class[cls]
        print(f"   {cls}: n={d['n']} supporto_ok={d['support_ok']} "
              f"verdetti={d['verdicts']}")
    print(f"   FALSE CLAIM: {len(false_claims)} | "
          f"G2'={g2p} ({rep_recovered}/{rep_data_ok}) | "
          f"G3'={g3p} ({mis_det}/{mis_total}) | G8={g8} | "
          f"G9 prec={g9p} recall={g9r} | med_err={med_err}")

    rp = OUT / "unblinding_report_v1.json"
    rp.write_text(json.dumps(report, indent=2))
    env = {"run": "CDE_V11_BLIND_UNBLINDING_V1",
           "timestamp_utc": datetime.now(timezone.utc)
                                    .strftime("%Y-%m-%dT%H:%M:%SZ"),
           "results_sha256": hashlib.sha256(rp.read_bytes()).hexdigest(),
           "python_version": platform.python_version(),
           "numpy_version": np.__version__,
           "platform": platform.platform(),
           "git_commit": _git("rev-parse", "--short", "HEAD"),
           "runtime_guard": guard,
           "human_review_required": True}
    (OUT / "unblinding_v1_envelope.json").write_text(
        json.dumps(env, indent=2))
    print(f"Output in {rp}  ({report['elapsed_s']}s)")


if __name__ == "__main__":
    main()
