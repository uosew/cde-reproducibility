#!/usr/bin/env python3
"""Pipeline di produzione del CDE, V1: correzioni strutturali, soglie invariate.

Nasce dall'audit del 2026-09-02 (`AUDIT_PROCESSO_SCOPERTA_2026-09-02.md`).
`CDE_PDE_DISCOVERY_V8.py` resta congelato e fornisce le primitive; la V0
resta come record. Nessuna soglia cambia: cambiare una soglia richiede una
campagna preregistrata, e questa V1 non ne contiene.

Cosa corregge, rispetto alla V0:

  F1  ordine dei cancelli allineato al codice VALIDATO del blind 2
      (`CDE_BLIND_PDE2_RUNNER_V0.py`, braccio `corretto`, PASS): ampiezza
      PRIMA del test di scambio. La V0 li aveva invertiti, quindi la
      pipeline «integrata senza toccare V8» non era il codice che il blind 2
      aveva validato.
  F2  colonna nulla nella matrice di disegno: la V0 produceva max_corr = NaN
      e il cancello di condizionamento passava in silenzio. Qui le colonne
      nulle vengono escluse dal calcolo e dichiarate.
  F3  il seme del sottocampionamento e' obbligatorio e per-caso: la V0 usava
      `seme=7` per ogni caso, cioe' lo stesso disegno di sottocampioni
      ovunque; il blind 2 usava `seme + 7` per caso.
  F4  `b` di norma nulla -> astensione dichiarata, non un residuo 1e300.
  F5  braccio nullo con semi DERIVATI dal seme di campagna: in V8 i semi del
      nullo sono costanti (1000+97*ns, 555+ns), quindi gli «800 nulli» della
      campagna avversariale condividono 10 flussi casuali. Il tasso e'
      chiamato col suo nome, `fpr_nulli`: e' un tasso di falsi positivi sui
      nulli, non un FDR.
  F6  diagnostica di sovrapposizione delle finestre: con K=200, wx=1, wt=0.3
      il 50.8% delle coppie di finestre si sovrappone, quindi i sottocampioni
      della stability selection non sono indipendenti. Qui si misura e si
      riporta; l'effetto sulle frequenze e' oggetto di campagna, non di V1.

Uso: importato. `python CDE_PDE_PIPELINE_GATED_V1.py` esegue gli autotest.
"""
from __future__ import annotations

import importlib.util
import itertools
from pathlib import Path

BASE = Path(__file__).resolve().parent
ART = BASE.parent.parent / "artifacts"      # public layout (cde-reproducibility)
PAPER = BASE.parent.parent / "paper"
JUL = BASE.parent.parent / "baselines" / "julia"
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
V0 = _load("gated_v0", "CDE_PDE_PIPELINE_GATED_V0.py")

TERMS = V8.TERMS
# soglie: IDENTICHE alla V0 e al blind 2, importate, non riscritte
GATE_FIT = V0.GATE_FIT
GATE_TRANSFER = V0.GATE_TRANSFER
GATE_AMPIEZZA = V0.GATE_AMPIEZZA
FATTORE_IDENT = V0.FATTORE_IDENT
SOGLIA_CORR = V0.SOGLIA_CORR
assert (GATE_FIT, GATE_TRANSFER, GATE_AMPIEZZA, FATTORE_IDENT, SOGLIA_CORR) \
    == (0.05, 0.05, 0.05, 2.0, 0.9999), "soglie diverse da quelle congelate"

# Margine della soglia di collinearita', come DICHIARATO dalle due fonti:
#   V0 (pipeline):        2.2e-05
#   blind 2 (runner):     1.3e-04  (decoy identificabile a 0.999871)
# Sono due numeri diversi per la stessa soglia, misurati su UN pannello.
# La soglia non e' osservabilmente calibrata: e' un fatto dichiarato qui,
# non corretto qui.
MARGINE_SOGLIA_CORR_DICHIARATO = {"V0": 2.2e-05, "blind2": 1.3e-04}

VERDETTI_ASSERTIVI = V0.VERDETTI_ASSERTIVI
e_falso_positivo = V0.e_falso_positivo


# ---------------------------------------------------------------- F2 ------
def collinearita(A) -> dict:
    """Massima correlazione fra colonne distinte NON nulle."""
    norme = np.linalg.norm(A, axis=0)
    nulle = [TERMS[i] for i in np.where(norme == 0.0)[0]]
    vive = np.where(norme > 0.0)[0]
    out = {"colonne_nulle": nulle}
    if vive.size < 2:
        out.update({"max_corr": 0.0, "cond_A": float("inf"), "coppia": None})
        return out
    An = A[:, vive] / norme[vive]
    C = np.abs(An.T @ An)
    np.fill_diagonal(C, 0.0)
    i, j = np.unravel_index(C.argmax(), C.shape)
    out.update({"max_corr": float(C.max()),
                "cond_A": float(np.linalg.cond(A[:, vive])),
                "coppia": (TERMS[vive[i]], TERMS[vive[j]])})
    assert np.isfinite(out["max_corr"]), "max_corr non finito: bug"
    return out


def _rr(A, b, c) -> float:
    return float(np.linalg.norm(A @ c - b) / np.linalg.norm(b))


def _swap_test(A, b, supporto, resid_migliore):
    """Identico alla V0 / blind 2: alternative di pari cardinalita'."""
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


# ---------------------------------------------------------------- F6 ------
def sovrapposizione_finestre(centers, wx, wt) -> dict:
    """Frazione di coppie di finestre che si sovrappongono. Diagnostica."""
    c = np.asarray(centers, dtype=float)
    if len(c) < 2:
        return {"coppie": 0, "sovrapposte": 0, "frazione": 0.0}
    dx = np.abs(c[:, 0, None] - c[None, :, 0]) < 2 * wx
    dt = np.abs(c[:, 1, None] - c[None, :, 1]) < 2 * wt
    ov = np.triu(dx & dt, k=1).sum()
    n = len(c) * (len(c) - 1) // 2
    return {"coppie": int(n), "sovrapposte": int(ov),
            "frazione": round(float(ov / n), 4)}


# ------------------------------------------------------------ decisione ---
def decidi(A, b, A_transfer=None, b_transfer=None,
           A_ampiezza=None, b_ampiezza=None, *, seme: int,
           centers=None, wx=None, wt=None) -> dict:
    """Decisione completa. `seme` e' OBBLIGATORIO e per-caso (F3).

    Ordine dei cancelli (F1) = blind 2, braccio validato:
      condizionamento -> supporto -> fit -> transfer -> ampiezza -> scambio.
    """
    out = {"collinearita": collinearita(A)}
    if centers is not None:
        out["finestre"] = sovrapposizione_finestre(centers, wx, wt)

    if out["collinearita"]["max_corr"] >= SOGLIA_CORR:
        a, c = out["collinearita"]["coppia"]
        out["decisione"] = "NOT_IDENTIFIABLE"
        out["motivo"] = (f"colonne {a} e {c} collineari a "
                         f"{out['collinearita']['max_corr']:.7f}: i dati non "
                         "separano le leggi")
        return out

    if np.linalg.norm(b) == 0.0:                                      # F4
        out["decisione"] = "ABSTAIN_B_NULLO"
        out["motivo"] = "il termine temporale e' identicamente nullo"
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

    if A_ampiezza is not None:                                        # F1
        r_amp = _rr(A_ampiezza, b_ampiezza, cvec)
        out["resid_ampiezza"] = float(r_amp)
        if not (r_amp < GATE_AMPIEZZA):
            out["decisione"] = "ABSTAIN_AMPIEZZA"
            out["motivo"] = (f"i coefficienti non reggono al secondo regime "
                             f"({r_amp:.4f}): modello efficace, non legge")
            return out

    ident, alt = _swap_test(A, b, supporto, resid)
    out["identificabile"] = bool(ident)
    out["alternative_entro_fattore"] = alt
    if not ident:
        out["decisione"] = "NOT_IDENTIFIABLE"
        return out

    if A_ampiezza is None:
        out["decisione"] = "CLAIM_EFFETTIVO"
        out["ambito"] = ("valida nel regime di ampiezza osservato; nessuna "
                         "traiettoria a un secondo regime, quindi non e' "
                         "distinguibile da un troncamento di Taylor di un "
                         "termine fuori libreria")
        return out

    out["decisione"] = "CLAIM"
    out["ambito"] = "coefficienti stabili su due regimi di ampiezza"
    return out


# ---------------------------------------------------------------- F5 ------
def braccio_nullo(x, t, U, centers, wx, wt, seme: int, n_seeds: int = 5,
                  feature=None) -> dict:
    """Nulli epistemici con semi derivati dal seme di campagna.

    Replica V8.run_system (righe 400-431) con due differenze: i flussi
    casuali dipendono da `seme`, e il tasso si chiama `fpr_nulli`.
    `feature(x, t, U, wx, wt, centers) -> (A, b)`; default: V8.
    """
    if feature is None:
        def feature(x, t, U, wx, wt, centers):
            return V8.build_Ab(V8.weak_features_v8(x, t, U, wx, wt, centers))
    base = int(seme) * 10_007
    out = {"n_runs": 0, "false_positives": 0, "stable_nonempty": 0,
           "detail": []}
    for kind in ("shuffle_t", "phase_surrogate"):
        for ns in range(n_seeds):
            off = 0 if kind == "shuffle_t" else 7
            nrng = np.random.default_rng(base + 1000 + 97 * ns + off)
            Un = V8.null_field(U, kind, nrng)
            An, bn = feature(x, t, Un, wx, wt, centers)
            sel = np.random.default_rng(base + 555 + ns + 13 * off)
            sup, _ = V8.stability_selection(An, bn, sel)
            cn = V8.refit(An, bn, sup)
            rn = V8.fit_rel_resid(An, bn, cn)
            fp = bool(sup and rn < GATE_FIT)
            out["n_runs"] += 1
            out["stable_nonempty"] += int(bool(sup))
            out["false_positives"] += int(fp)
            out["detail"].append({"kind": kind, "seed": ns,
                                  "stable_support": sorted(TERMS[i] for i in sup),
                                  "fit_rel_resid": rn, "false_positive": fp})
    out["fpr_nulli"] = out["false_positives"] / max(1, out["n_runs"])
    out["nota"] = ("tasso di falsi positivi sui nulli, NON un FDR: il "
                   "denominatore sono le run nulle, non le scoperte")
    return out


# ------------------------------------------------------------- autotest ---
def _autotest():
    rng = np.random.default_rng(0)
    n = 200
    esiti = []

    # F2: colonna nulla non produce NaN e non apre il cancello in silenzio
    Az = rng.normal(size=(n, len(TERMS)))
    Az[:, 5] = 0.0
    c = collinearita(Az)
    esiti.append(("F2 colonna nulla -> max_corr finito e dichiarata",
                  np.isfinite(c["max_corr"]) and c["colonne_nulle"] == ["u_xxx"]))
    c0 = V0.collinearita(Az)
    esiti.append(("F2 (controllo) la V0 dava NaN", np.isnan(c0["max_corr"])))

    # V0 degenerazione -> NOT_IDENTIFIABLE, invariato
    Ad = rng.normal(size=(n, len(TERMS)))
    Ad[:, TERMS.index("u_xxx")] = -4.0 * Ad[:, TERMS.index("u_x")]
    bd = Ad[:, TERMS.index("u_x")] * -0.5
    esiti.append(("degenerazione -> NOT_IDENTIFIABLE",
                  decidi(Ad, bd, seme=1)["decisione"] == "NOT_IDENTIFIABLE"))

    # F4
    esiti.append(("F4 b nullo -> ABSTAIN_B_NULLO",
                  decidi(Ad * 0 + rng.normal(size=Ad.shape), np.zeros(n),
                         seme=1)["decisione"] == "ABSTAIN_B_NULLO"))

    # F3: seme obbligatorio
    A = rng.normal(size=(n, len(TERMS)))
    b = A[:, TERMS.index("u_xx")] * 0.1
    try:
        decidi(A, b)
        esiti.append(("F3 seme obbligatorio", False))
    except TypeError:
        esiti.append(("F3 seme obbligatorio", True))

    # verdetti V0 conservati dove l'ordine non conta
    A2 = rng.normal(size=(n, len(TERMS))); b2 = A2[:, TERMS.index("u_xx")] * 0.1
    A3 = rng.normal(size=(n, len(TERMS))); b3 = A3[:, TERMS.index("u_xx")] * 0.1
    esiti.append(("transfer assente -> ABSTAIN_TRANSFER_ASSENTE",
                  decidi(A, b, seme=1)["decisione"] == "ABSTAIN_TRANSFER_ASSENTE"))
    esiti.append(("ampiezza assente -> CLAIM_EFFETTIVO",
                  decidi(A, b, A2, b2, seme=1)["decisione"] == "CLAIM_EFFETTIVO"))
    esiti.append(("ampiezza coerente -> CLAIM",
                  decidi(A, b, A2, b2, A3, b3, seme=1)["decisione"] == "CLAIM"))
    esiti.append(("ampiezza incoerente -> ABSTAIN_AMPIEZZA",
                  decidi(A, b, A2, b2, A3, b3 * 4, seme=1)["decisione"]
                  == "ABSTAIN_AMPIEZZA"))

    # F1: caso in cui scambio E ampiezza falliscono -> l'ordine decide.
    # Costruito: due colonne quasi uguali (sotto SOGLIA_CORR) cosi' che il
    # test di scambio trovi un'alternativa, e ampiezza incoerente.
    rs = np.random.default_rng(3)
    As = rs.normal(size=(n, len(TERMS)))
    As[:, 1] = As[:, 0] + 0.02 * rs.normal(size=n)   # corr 0.99983 < soglia
    bs = As[:, 0] * 0.3 + 0.01 * rs.normal(size=n)    # fit 0.036 < gate
    As2, bs2 = As, bs
    r1 = decidi(As, bs, As2, bs2, As2, bs2 * 5, seme=1)
    r0 = V0.decidi(As, bs, As2, bs2, As2, bs2 * 5, seme=1)
    esiti.append(("F1 stesso caso: V1 = blind2 (ABSTAIN_AMPIEZZA)",
                  r1["decisione"] == "ABSTAIN_AMPIEZZA"))
    esiti.append(("F1 (controllo) la V0 dava un verdetto diverso",
                  r0["decisione"] != r1["decisione"]))

    # F6
    cs = [(1.0, 0.5), (1.5, 0.6), (5.0, 1.5)]
    esiti.append(("F6 sovrapposizione: 1 coppia su 3",
                  sovrapposizione_finestre(cs, 1.0, 0.3)["sovrapposte"] == 1))

    # F5: semi diversi -> flussi diversi
    x = np.linspace(0, 2*np.pi, 64, endpoint=False); t = np.linspace(0, 1, 40)
    U = np.sin(x)[None, :] * np.cos(t)[:, None]
    def feat(x, t, U, wx, wt, cs):
        return rng.normal(size=(20, 7)), rng.normal(size=20)
    n1 = braccio_nullo(x, t, U, [(3, 0.5)], 1.0, 0.3, seme=1, n_seeds=1, feature=feat)
    esiti.append(("F5 fpr_nulli presente e 'fdr' assente",
                  "fpr_nulli" in n1 and "fdr" not in n1))

    print("== autotest pipeline V1 ==")
    for nome, ok in esiti:
        print(f"   {'OK ' if ok else 'NO '} {nome}")
    return 0 if all(ok for _, ok in esiti) else 1


if __name__ == "__main__":
    raise SystemExit(_autotest())
