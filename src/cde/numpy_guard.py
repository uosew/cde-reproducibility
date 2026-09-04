#!/usr/bin/env python3
"""numpy_guard — schermatura anti-mutazione da elisione dei temporanei numpy.

Origine: 2026-07-28, debug CDE_WEAK_OPERATOR_COMPONENTWISE_IDENTITY_V7.
Su numpy 2.2.6 + CPython 3.14.0 (arm64) gli operatori infissi (** * + - /)
su array >= ~256 KB usati come variabili locali DENTRO funzioni mutano
l'operando in place: l'elisione dei temporanei di numpy controlla il refcount
e gli stack-ref di CPython 3.14 fanno apparire refcount 1 anche per locali
vivi. Vedi QUARANTENA_NUMPY_ELISION_2026_07_28.md per il protocollo completo.

Regole d'uso nelle campagne:
  1. All'avvio:      from numpy_guard import assert_supported_environment
                     env = assert_supported_environment()      # o strict=False
     e registrare `env` nell'evidence envelope.
  2. Trasformazioni: x2 = safe_square(x); xy = safe_multiply(x, y)
     (ufunc esplicite con `out` fresco + dtype esplicito + verifica opzionale
     di non-mutazione dell'input).
  3. Input critici:  freeze(x) prima di passare array a feature transformation:
     una scrittura in place fara' FALLIRE il processo invece di corrompere.
  4. Blocchi critici: with assert_no_mutation(x): ...  (copia prima, confronto
     dopo, RuntimeError se l'input e' cambiato).

Il canary va eseguito SEMPRE, anche su ambienti "supportati": non si assume
mai che il problema sia sparito.
"""
from __future__ import annotations

import platform
import sys
from contextlib import contextmanager

import numpy as np

# versione del protocollo guard: incrementare a ogni modifica delle regole.
GUARD_PROTOCOL_VERSION = "1.1.0"

# soglia empirica misurata il 2026-07-28 su questo Mac: la mutazione appare
# a partire da array da 256 KB (32768 float64); sotto, mai osservata.
ELIDE_THRESHOLD_BYTES = 256 * 1024

#: matrice di supporto adottata dal laboratorio (ambiente primario e replica).
SUPPORTED = (
    ((3, 12), "2.5"),
    ((3, 13), "2.5"),
)


def elision_mutation_canary(verbose: bool = False) -> dict:
    """Esegue il canary su ** , * , + dentro una funzione, array da 256 KB.

    Ritorna {"**": bool, "*": bool, "+": bool, "any": bool}: True = MUTATO.
    """
    n = ELIDE_THRESHOLD_BYTES // 8

    def _pow():
        a = np.full(n, 2.0)
        _ = a ** 2
        return bool(a[0] != 2.0)

    def _mul():
        a = np.full(n, 2.0)
        b = np.full(n, 3.0)
        _ = a * b
        return bool(a[0] != 2.0)

    def _add():
        a = np.full(n, 2.0)
        b = np.full(n, 3.0)
        _ = a + b
        return bool(a[0] != 2.0)

    def _sub():
        a = np.full(n, 2.0)
        b = np.full(n, 3.0)
        _ = a - b
        return bool(a[0] != 2.0)

    def _div():
        a = np.full(n, 2.0)
        b = np.full(n, 4.0)
        _ = a / b
        return bool(a[0] != 2.0)

    def _exp():
        a = np.full(n, 2.0)
        _ = np.exp(a)
        return bool(a[0] != 2.0)

    res = {"**": _pow(), "*": _mul(), "+": _add(),
           "-": _sub(), "/": _div(), "exp": _exp()}
    res["any"] = any(res.values())
    if verbose:
        for op, bad in res.items():
            if op != "any":
                print(f"  canary '{op}': {'MUTAZIONE' if bad else 'ok'}")
    return res


def environment_report() -> dict:
    can = elision_mutation_canary()
    py = sys.version_info[:2]
    supported = any(py == v and np.__version__.startswith(nv)
                    for v, nv in SUPPORTED)
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "platform": platform.platform(),
        "in_support_matrix": supported,
        "elision_canary_mutation": can["any"],
        "canary_detail": {k: v for k, v in can.items() if k != "any"},
    }


def assert_supported_environment(strict: bool = True) -> dict:
    """Canary sempre; se strict, fallisce su canary positivo o matrice fuori.

    Ritorna il report ambiente da registrare nell'evidence envelope.
    """
    rep = environment_report()
    if rep["elision_canary_mutation"]:
        msg = (f"CANARY POSITIVO: elisione numpy muta i locali "
               f"(python {rep['python']}, numpy {rep['numpy']}). "
               "Risultati non affidabili su questo interprete.")
        if strict:
            raise RuntimeError(msg)
        print(f"!! {msg}", file=sys.stderr)
    if not rep["in_support_matrix"]:
        msg = (f"ambiente fuori matrice di supporto LB "
               f"(python {rep['python']}, numpy {rep['numpy']}); "
               f"use a supported interpreter (see requirements-lock.txt).")
        if strict:
            raise RuntimeError(msg)
        print(f"!! {msg}", file=sys.stderr)
    return rep


# ---------------------------------------------------------------------------
# Operazioni schermate: ufunc esplicita + out fresco + dtype esplicito
# + verifica di non-mutazione dell'input (attiva di default sopra soglia).
# ---------------------------------------------------------------------------

GUARD_VERIFY = True   # metti False solo per profiling, mai nelle campagne


def _verified(ufunc, *inputs, dtype=np.float64):
    arrs = [np.asarray(a) for a in inputs]
    check = GUARD_VERIFY and any(a.nbytes >= ELIDE_THRESHOLD_BYTES for a in arrs)
    before = [a.copy() for a in arrs] if check else None
    out = np.empty(np.broadcast(*arrs).shape, dtype=dtype)
    ufunc(*arrs, out=out)
    if check:
        for a, b in zip(arrs, before):
            if not np.array_equal(a, b, equal_nan=True):
                raise RuntimeError(
                    f"Unexpected input mutation in {ufunc.__name__}")
    return out


def safe_square(x, dtype=np.float64):
    return _verified(np.square, x, dtype=dtype)


def safe_power(x, p, dtype=np.float64):
    return _verified(np.power, x, p, dtype=dtype)


def safe_multiply(x, y, dtype=np.float64):
    return _verified(np.multiply, x, y, dtype=dtype)


def safe_add(x, y, dtype=np.float64):
    return _verified(np.add, x, y, dtype=dtype)


def safe_subtract(x, y, dtype=np.float64):
    return _verified(np.subtract, x, y, dtype=dtype)


def safe_exp(x, dtype=np.float64):
    return _verified(np.exp, x, dtype=dtype)


def freeze(x: np.ndarray) -> np.ndarray:
    """Rende l'array read-only: una scrittura in place ora ALZA ValueError."""
    x.setflags(write=False)
    return x


def thaw(x: np.ndarray) -> np.ndarray:
    x.setflags(write=True)
    return x


@contextmanager
def assert_no_mutation(*arrays):
    """Copia gli array all'ingresso e verifica all'uscita che siano intatti."""
    before = [np.asarray(a).copy() for a in arrays]
    yield
    for a, b in zip(arrays, before):
        if not np.array_equal(np.asarray(a), b, equal_nan=True):
            raise RuntimeError("Unexpected input mutation nel blocco protetto")


if __name__ == "__main__":
    rep = environment_report()
    print(f"python {rep['python']} | numpy {rep['numpy']}")
    print(f"in matrice di supporto: {rep['in_support_matrix']}")
    elision_mutation_canary(verbose=True)
    print("VERDETTO:", "AMBIENTE NON AFFIDABILE"
          if rep["elision_canary_mutation"] else "canary pulito")
    sys.exit(1 if rep["elision_canary_mutation"] else 0)
