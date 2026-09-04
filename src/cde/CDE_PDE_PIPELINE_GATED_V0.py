#!/usr/bin/env python3
"""Pipeline di produzione del CDE con i due cancelli dei blind test.

`CDE_PDE_DISCOVERY_V8.py` NON viene modificato: e' un artefatto congelato,
importato da tutte le campagne V10, e cambiarlo altererebbe retroattivamente il
codice di risultati gia' committati. Qui V8 fornisce le primitive
(stability selection, refit, residuo) e questo modulo aggiunge la logica di
decisione.

I due cancelli vengono dai fallimenti misurati nel blind 1
(`REPORT_BLIND_PDE_2026-08-24.md`) e validati appaiati nel blind 2
(`REPORT_BLIND_PDE2_2026-08-24.md`, PASS: 4 falsi positivi -> 0, senza perdere
recuperi ne' decoy).

**(a) Condizionamento.** Se due colonne della matrice di disegno sono
numericamente indistinguibili da collineari, i dati non separano le leggi: la
risposta e' NOT_IDENTIFIABLE, non una scelta fra equivalenti. Agisce prima
della selezione — la degenerazione e' una proprieta' dei dati.

**(b) Estrapolazione in ampiezza.** I coefficienti congelati su una traiettoria
devono reggere su una a ampiezza diversa. Una legge vera ha coefficienti
indipendenti dall'ampiezza; il troncamento di Taylor di un termine fuori
libreria coincide a piccola ampiezza e diverge a grande.

## La decisione che l'integrazione ha forzato

Il gate (b) richiede una traiettoria a un secondo regime di ampiezza. In
produzione spesso non esiste. Saltarlo e affermare comunque riaprirebbe
esattamente il buco che chiude, quindi in sua assenza questa pipeline **non
dichiara CLAIM**: dichiara `CLAIM_EFFETTIVO`, con l'ambito di validita' scritto
nel risultato.

E' la risposta alla domanda che il blind 1 ha sollevato — quando un modello che
spiega e trasferisce puo' essere chiamato legge? Non prima di aver visto un
secondo regime. `CLAIM_EFFETTIVO` non e' un CLAIM indebolito per comodita': e'
il verdetto corretto quando manca l'evidenza che distingue la legge dal
surrogato.

Uso: importato. `python CDE_PDE_PIPELINE_GATED_V0.py` esegue gli autotest.
"""
from __future__ import annotations

import importlib.util
import itertools
from pathlib import Path

BASE = Path(__file__).resolve().parent
ART = BASE.parent.parent / "artifacts"      # public layout (cde-reproducibility)
PAPER = BASE.parent.parent / "paper"
ROOT = BASE.parent

_g = importlib.util.spec_from_file_location(
    "runtime_guard_bootstrap", BASE / "runtime_guard_bootstrap.py")
RGB = importlib.util.module_from_spec(_g)
_g.loader.exec_module(RGB)

import numpy as np                                        # noqa: E402


def _load(nome, fname):
    spec = importlib.util.spec_from_file_location(nome, BASE / fname)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


V8 = _load("v8", "CDE_PDE_DISCOVERY_V8.py")

TERMS = V8.TERMS
GATE_FIT = V8.GATE_FIT_RESID          # 0.05
GATE_TRANSFER = 0.05
GATE_AMPIEZZA = GATE_TRANSFER         # stesso gate, dati di un altro regime
FATTORE_IDENT = 2.0
SOGLIA_CORR = 0.9999                  # validata nel blind 2, con margine 2.2e-05


# --- regola anti-riciclaggio (SEMANTICA_VERDETTI_CDE_2026-08-24.md §3) -----
# CLAIM_EFFETTIVO e' un verdetto ASSERTIVO quanto CLAIM: afferma qualcosa sui
# dati. La differenza sta nell'ambito, non nella forza dell'atto.
#
# Serve perche' questa infrastruttura si e' quasi ingannata da sola: la
# funzione di scoring della regressione sul blind 1 contava come falso
# positivo la sola stringa "CLAIM", e case_17 — un fallimento noto — e' passato
# per «risolto» solo perche' il suo verdetto aveva cambiato nome. Un test
# superato perche' il fallimento si e' rinominato non e' un test superato.
VERDETTI_ASSERTIVI = ("CLAIM", "CLAIM_EFFETTIVO")


def e_falso_positivo(decisione: str, esito_atteso: str) -> bool:
    """Vero se `decisione` afferma dove la risposta corretta era astenersi.

    Da usare in TUTTI gli scorer futuri al posto di `dec == "CLAIM"`. Ampliare
    il vocabolario dei verdetti non deve poter assolvere retroattivamente una
    campagna chiusa.
    """
    return decisione in VERDETTI_ASSERTIVI and esito_atteso != "CLAIM"


def collinearita(A) -> dict:
    """Massima correlazione fra colonne distinte della matrice di disegno."""
    An = A / np.linalg.norm(A, axis=0)
    C = np.abs(An.T @ An)
    np.fill_diagonal(C, 0.0)
    i, j = np.unravel_index(C.argmax(), C.shape)
    return {"max_corr": float(C.max()), "cond_A": float(np.linalg.cond(A)),
            "coppia": (TERMS[i], TERMS[j])}


def _rr(A, b, c) -> float:
    return float(np.linalg.norm(A @ c - b) / max(np.linalg.norm(b), 1e-300))


def _swap_test(A, b, supporto, resid_migliore):
    """Alternative di pari cardinalita' entro FATTORE_IDENT dal residuo
    migliore. Il blind 1 ha mostrato che questo test NON vede le degenerazioni
    fra cardinalita' diverse: quelle le intercetta il cancello di
    condizionamento, a monte."""
    if not supporto:
        return True, []
    idx = sorted(supporto)
    trovate = {}
    for fuori in idx:
        restanti = [i for i in range(len(TERMS)) if i != fuori]
        for combo in itertools.combinations(restanti, len(idx)):
            if set(combo) == set(idx):
                continue
            c, *_ = np.linalg.lstsq(A[:, list(combo)], b, rcond=None)
            r = _rr(A[:, list(combo)], b, c)
            if r <= FATTORE_IDENT * max(resid_migliore, 1e-12):
                chiave = tuple(sorted(TERMS[i] for i in combo))
                if chiave not in trovate or r < trovate[chiave]:
                    trovate[chiave] = r
    alt = [{"supporto": list(k), "resid": round(v, 8)}
           for k, v in sorted(trovate.items(), key=lambda kv: kv[1])[:5]]
    return (len(alt) == 0), alt


def decidi(A, b, A_transfer=None, b_transfer=None,
           A_ampiezza=None, b_ampiezza=None, seme: int = 7) -> dict:
    """Decisione completa sulle feature deboli gia' costruite.

    `A_transfer` (traiettoria indipendente) e `A_ampiezza` (secondo regime di
    ampiezza) sono opzionali, e la loro assenza cambia il verdetto invece di
    essere ignorata in silenzio.
    """
    out = {"collinearita": collinearita(A)}

    if out["collinearita"]["max_corr"] >= SOGLIA_CORR:
        a, c = out["collinearita"]["coppia"]
        out["decisione"] = "NOT_IDENTIFIABLE"
        out["motivo"] = (f"colonne {a} e {c} collineari a "
                         f"{out['collinearita']['max_corr']:.7f}: i dati non "
                         "separano le leggi")
        return out

    supporto, freqs = V8.stability_selection(A, b, np.random.default_rng(seme))
    out["supporto"] = sorted(TERMS[i] for i in supporto)
    out["frequenze"] = {TERMS[i]: round(float(f), 3)
                        for i, f in enumerate(freqs)}
    if not supporto:
        out["decisione"] = "ABSTAIN_SUPPORTO_VUOTO"
        return out

    coeffs = V8.refit(A, b, supporto)
    resid = V8.fit_rel_resid(A, b, coeffs)
    out["coefficienti"] = {k: float(v) for k, v in coeffs.items()}
    out["resid_fit"] = float(resid)
    if not (resid < GATE_FIT):
        out["decisione"] = "ABSTAIN_GATE_FIT"
        return out

    cvec = np.array([coeffs.get(k, 0.0) for k in TERMS])

    if A_transfer is None:
        out["decisione"] = "ABSTAIN_TRANSFER_ASSENTE"
        out["motivo"] = ("nessuna traiettoria indipendente: il fit da solo non "
                         "distingue un modello da un overfit")
        return out
    r_tr = _rr(A_transfer, b_transfer, cvec)
    out["resid_transfer"] = float(r_tr)
    if not (r_tr < GATE_TRANSFER):
        out["decisione"] = "ABSTAIN_TRANSFER"
        return out

    ident, alt = _swap_test(A, b, supporto, resid)
    out["identificabile"] = bool(ident)
    out["alternative_entro_fattore"] = alt
    if not ident:
        out["decisione"] = "NOT_IDENTIFIABLE"
        return out

    if A_ampiezza is None:
        # Senza un secondo regime non esiste evidenza che distingua la legge
        # dal suo surrogato efficace. Non si afferma piu' di quel che si sa.
        out["decisione"] = "CLAIM_EFFETTIVO"
        out["ambito"] = ("valida nel regime di ampiezza osservato; nessuna "
                         "traiettoria a un secondo regime, quindi non e' "
                         "distinguibile da un troncamento di Taylor di un "
                         "termine fuori libreria")
        return out

    r_amp = _rr(A_ampiezza, b_ampiezza, cvec)
    out["resid_ampiezza"] = float(r_amp)
    if not (r_amp < GATE_AMPIEZZA):
        out["decisione"] = "ABSTAIN_AMPIEZZA"
        out["motivo"] = (f"i coefficienti non reggono al secondo regime "
                         f"({r_amp:.4f}): modello efficace, non legge")
        return out

    out["decisione"] = "CLAIM"
    out["ambito"] = "coefficienti stabili su due regimi di ampiezza"
    return out


# ---------------------------------------------------------------------------

def _autotest():
    """Il modulo si verifica su matrici costruite a mano: nessun dato, nessun
    seme di simulazione, esito deterministico."""
    rng = np.random.default_rng(0)
    n = 200
    esiti = []

    # 1. degenerazione esatta: due colonne proporzionali
    Ad = rng.normal(size=(n, len(TERMS)))
    Ad[:, TERMS.index("u_xxx")] = -4.0 * Ad[:, TERMS.index("u_x")]
    bd = Ad[:, TERMS.index("u_x")] * -0.5
    r = decidi(Ad, bd)
    esiti.append(("degenerazione -> NOT_IDENTIFIABLE",
                  r["decisione"] == "NOT_IDENTIFIABLE"))

    # 2. transfer assente -> non si afferma
    A = rng.normal(size=(n, len(TERMS)))
    b = A[:, TERMS.index("u_xx")] * 0.1
    r = decidi(A, b)
    esiti.append(("transfer assente -> ABSTAIN_TRANSFER_ASSENTE",
                  r["decisione"] == "ABSTAIN_TRANSFER_ASSENTE"))

    # 3. ampiezza assente -> CLAIM_EFFETTIVO, mai CLAIM
    A2 = rng.normal(size=(n, len(TERMS)))
    b2 = A2[:, TERMS.index("u_xx")] * 0.1
    r = decidi(A, b, A2, b2)
    esiti.append(("ampiezza assente -> CLAIM_EFFETTIVO",
                  r["decisione"] == "CLAIM_EFFETTIVO"))

    # 4. ampiezza presente e coerente -> CLAIM
    A3 = rng.normal(size=(n, len(TERMS)))
    b3 = A3[:, TERMS.index("u_xx")] * 0.1
    r = decidi(A, b, A2, b2, A3, b3)
    esiti.append(("ampiezza coerente -> CLAIM", r["decisione"] == "CLAIM"))

    # 5. ampiezza incoerente -> astensione, non CLAIM
    b3_rotto = A3[:, TERMS.index("u_xx")] * 0.4
    r = decidi(A, b, A2, b2, A3, b3_rotto)
    esiti.append(("ampiezza incoerente -> ABSTAIN_AMPIEZZA",
                  r["decisione"] == "ABSTAIN_AMPIEZZA"))

    # 6. la regola anti-riciclaggio: CLAIM_EFFETTIVO non assolve nulla
    esiti.append(("CLAIM_EFFETTIVO su caso da astenere -> falso positivo",
                  e_falso_positivo("CLAIM_EFFETTIVO", "ABSTAIN")))
    esiti.append(("CLAIM su caso da astenere -> falso positivo",
                  e_falso_positivo("CLAIM", "ABSTAIN")))
    esiti.append(("CLAIM_EFFETTIVO dove atteso CLAIM -> non falso positivo",
                  not e_falso_positivo("CLAIM_EFFETTIVO", "CLAIM")))
    esiti.append(("astensione -> mai falso positivo",
                  not e_falso_positivo("ABSTAIN_AMPIEZZA", "ABSTAIN")))

    print("== autotest pipeline con cancelli ==")
    for nome, ok in esiti:
        print(f"   {'OK ' if ok else 'NO '} {nome}")
    return 0 if all(ok for _, ok in esiti) else 1


if __name__ == "__main__":
    raise SystemExit(_autotest())
