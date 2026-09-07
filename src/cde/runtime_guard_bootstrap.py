#!/usr/bin/env python3
"""runtime_guard_bootstrap — enforcement obbligatorio del guard numpy.

Posizione: radice del repo LB (importabile da tutti gli entry point).
Fonte unica delle primitive: CDE_Scientific_Discovery/numpy_guard.py
(caricata per percorso: nessuna dipendenza dall'ordine di sys.path).

Contratto (protocollo quarantena 2026-07-28):
  - `enforce_runtime_guard(strict=True)` DEVE essere chiamato da ogni entry
    point scientifico PRIMA di caricare dataset o generare feature.
  - strict=True (default): su canary positivo o ambiente fuori matrice il
    processo termina con RuntimeError. Nessun fallback silenzioso.
  - Uso forense di un ambiente vulnerabile (es. riprodurre il bug su py3.14):
    SOLO con la variabile d'ambiente LB_GUARD_ALLOW_FORENSIC=1; il report
    esce comunque con status FAIL e forensic=True, e qualunque envelope che
    lo contenga viene valutato RUN_INVALID_ENVIRONMENT (mai promuovibile).
  - Negli ambienti ufficiali (requirements-lock.txt) il canary gira automaticamente a
    ogni avvio interprete via lb_guard_autoload (.pth installato da
    scripts/install_runtime_guard_pth.py): l'enforcement non dipende dalla
    disciplina del singolo autore.

Validazione envelope:
  - envelope senza sezione runtime_guard  -> EVIDENCE_INCOMPLETE
  - runtime_guard.status == FAIL          -> RUN_INVALID_ENVIRONMENT
  - runtime_guard.input_mutation_detected -> RUN_INVALID_ENVIRONMENT
  - altrimenti                            -> RUN_VALID
"""
from __future__ import annotations

import hashlib
import importlib.util
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent
_GUARD_PATH = _REPO_ROOT / "numpy_guard.py"

RUN_VALID = "RUN_VALID"
EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"
RUN_INVALID_ENVIRONMENT = "RUN_INVALID_ENVIRONMENT"


def _load_numpy_guard():
    spec = importlib.util.spec_from_file_location("numpy_guard", _GUARD_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _guard_sha256() -> str:
    return hashlib.sha256(_GUARD_PATH.read_bytes()).hexdigest()


def build_runtime_guard_report() -> dict:
    """Esegue il canary e produce il report strutturato serializzabile."""
    ng = _load_numpy_guard()
    import numpy as np
    try:
        import scipy
        scipy_version = scipy.__version__
    except ImportError:
        scipy_version = None

    canary = ng.elision_mutation_canary()
    ops = {k: bool(v) for k, v in canary.items() if k != "any"}
    mutation = bool(canary["any"])
    env_rep = ng.environment_report()
    in_matrix = bool(env_rep["in_support_matrix"])
    status = "PASS" if (not mutation and in_matrix) else "FAIL"

    return {
        "status": status,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "scipy_version": scipy_version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "virtual_env": os.environ.get("VIRTUAL_ENV")
                       or (sys.prefix if sys.prefix != sys.base_prefix else None),
        "in_support_matrix": in_matrix,
        "operations_tested": sorted(ops.keys()),
        "operations_result": ops,
        "input_mutation_detected": mutation,
        "checked_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "canary_sha256": _guard_sha256(),
        "guard_protocol_version": ng.GUARD_PROTOCOL_VERSION,
        "forensic": os.environ.get("LB_GUARD_ALLOW_FORENSIC") == "1",
    }


def enforce_runtime_guard(strict: bool = True) -> dict:
    """Canary sempre; blocca l'esecuzione se l'ambiente non e' verificato.

    Ritorna il report da inserire nell'evidence envelope sotto la chiave
    'runtime_guard'. Con LB_GUARD_ALLOW_FORENSIC=1 non solleva, ma il report
    resta FAIL+forensic e la run non sara' mai promuovibile.
    """
    rep = build_runtime_guard_report()
    if rep["status"] == "FAIL" and strict and not rep["forensic"]:
        why = ("mutazione da elisione rilevata"
               if rep["input_mutation_detected"] else
               "ambiente fuori matrice di supporto (vedi requirements-lock.txt)")
        raise RuntimeError(
            f"RUNTIME GUARD FAIL: {why} — python {rep['python_version']}, "
            f"numpy {rep['numpy_version']}, exe {rep['executable']}. "
            "Esecuzione scientifica bloccata PRIMA del caricamento dati. "
            "Per evidenza forense esplicita: LB_GUARD_ALLOW_FORENSIC=1.")
    if rep["status"] == "FAIL":
        print("!! runtime_guard: FAIL (modalita' forense: risultati NON "
              "attendibili, envelope sara' RUN_INVALID_ENVIRONMENT)",
              file=sys.stderr)
    return rep


def evaluate_run_validity(envelope: dict) -> str:
    """Applica le regole di validita' a un evidence envelope."""
    rg = envelope.get("runtime_guard")
    if not isinstance(rg, dict) or "status" not in rg:
        return EVIDENCE_INCOMPLETE
    if rg.get("status") != "PASS" or rg.get("input_mutation_detected"):
        return RUN_INVALID_ENVIRONMENT
    return RUN_VALID


def is_promotable(envelope: dict) -> bool:
    """Una run puo' entrare in ranking/vault/claim solo se RUN_VALID."""
    return evaluate_run_validity(envelope) == RUN_VALID


if __name__ == "__main__":
    import json
    rep = build_runtime_guard_report()
    print(json.dumps(rep, indent=2))
    sys.exit(0 if rep["status"] == "PASS" else 1)
