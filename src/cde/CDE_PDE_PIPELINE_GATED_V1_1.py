#!/usr/bin/env python3
"""Pipeline V1.1 = V1 (tag cde-v1-baseline-2026-09-02, importata, non copiata) + limite di
risoluzione dichiarato su ogni verdetto assertivo (SEMANTICA §7, emendamento 2026-09-03).

Nessun verdetto cambia: l'annotazione e' a valle dei cancelli. `decidi` restituisce lo
stesso dizionario della V1 piu' la chiave `risoluzione` = {k, rho, X, c_min} quando la
decisione e' CLAIM o CLAIM_EFFETTIVO. Soglie: quelle della V1, verificate con assert."""
import importlib.util
from pathlib import Path
import numpy as np
BASE = Path(__file__).resolve().parent
ART = BASE.parent.parent / "artifacts"      # public layout (cde-reproducibility)
PAPER = BASE.parent.parent / "paper"
JUL = BASE.parent.parent / "baselines" / "julia"
def _L(n, f):
    s = importlib.util.spec_from_file_location(n, BASE / f); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
V1 = _L("v1", "CDE_PDE_PIPELINE_GATED_V1.py"); TERMS = V1.TERMS; VERDETTI_ASSERTIVI = V1.VERDETTI_ASSERTIVI
K_RISOLUZIONE = V1.FATTORE_IDENT          # 2.0: k=1 falsificato allo Stage 1
assert K_RISOLUZIONE == 2.0
RGB = V1.RGB; braccio_nullo = V1.braccio_nullo; e_falso_positivo = V1.e_falso_positivo

def risoluzione(A, b, supporto, coeffs, k=K_RISOLUZIONE):
    idx = [TERMS.index(t) for t in supporto]; c = np.array([coeffs[t] for t in supporto], float)
    rho = float(np.linalg.norm(A[:, idx] @ c - b)); nb = float(np.linalg.norm(b))
    cmin = {t: (k * rho / float(np.linalg.norm(A[:, TERMS.index(t)])) if np.linalg.norm(A[:, TERMS.index(t)]) > 0 else float("inf")) for t in TERMS if t not in supporto}
    return {"k": k, "rho": rho, "X": k * rho / nb, "c_min": cmin,
            "lettura": f"legge {sorted(supporto)} a meno di termini della libreria con contributo relativo < {k * rho / nb:.4f}"}

def decidi(A, b, *args, **kw):
    d = V1.decidi(A, b, *args, **kw)
    if d["decisione"] in VERDETTI_ASSERTIVI:
        d["risoluzione"] = risoluzione(A, b, d["supporto"], d["coefficienti"])
    return d

def _autotest():
    rng = np.random.default_rng(0); n = 200; esiti = []
    A = rng.normal(size=(n, len(TERMS))); b = A[:, TERMS.index("u_xx")] * 0.1 + 0.002 * rng.normal(size=n)
    A2 = rng.normal(size=(n, len(TERMS))); b2 = A2[:, TERMS.index("u_xx")] * 0.1
    A3 = rng.normal(size=(n, len(TERMS))); b3 = A3[:, TERMS.index("u_xx")] * 0.1
    d0 = V1.decidi(A, b, A2, b2, A3, b3, seme=1); d1 = decidi(A, b, A2, b2, A3, b3, seme=1)
    esiti.append(("verdetto identico alla V1", d0["decisione"] == d1["decisione"] == "CLAIM"))
    esiti.append(("CLAIM porta X e c_min per ogni termine fuori supporto", "risoluzione" in d1 and set(d1["risoluzione"]["c_min"]) == set(TERMS) - {"u_xx"}))
    esiti.append(("X = 2 * resid_fit", abs(d1["risoluzione"]["X"] - 2 * d1["resid_fit"]) < 1e-12))
    e0 = V1.decidi(A, b, A2, b2, seme=1); e1 = decidi(A, b, A2, b2, seme=1)
    esiti.append(("CLAIM_EFFETTIVO annotato, verdetto identico", e1["decisione"] == e0["decisione"] == "CLAIM_EFFETTIVO" and "risoluzione" in e1))
    a0 = V1.decidi(A, b, seme=1); a1 = decidi(A, b, seme=1)
    esiti.append(("astensione NON annotata, identica", a0["decisione"] == a1["decisione"] and "risoluzione" not in a1))
    esiti.append(("soglie della V1 invariate", (V1.GATE_FIT, V1.GATE_TRANSFER, V1.SOGLIA_CORR, V1.FATTORE_IDENT) == (0.05, 0.05, 0.9999, 2.0)))
    print("== autotest V1.1 ==")
    for nome, ok in esiti: print(f"   {'OK ' if ok else 'NO '} {nome}")
    return 0 if all(o for _, o in esiti) else 1
if __name__ == "__main__":
    raise SystemExit(_autotest())
