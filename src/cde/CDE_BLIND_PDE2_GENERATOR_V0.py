#!/usr/bin/env python3
"""Blind PDE campagna 2 — GENERATORE (conosce le leggi; i risolutori no).

Il generatore della campagna 1 e' congelato e non viene toccato: questo e' un
file nuovo, con tre aggiunte che lo stage 1 ha reso obbligatorie.

1. **Casi degeneri CON rumore.** Nel blind 1 tutti e tre i casi non
   identificabili erano a rumore zero, dove la collinearita' resta esatta e il
   cancello di condizionamento ha vita facile. Qui due dei quattro hanno
   rumore: se il cancello vive solo sul pulito, deve emergere.
2. **Decoy quasi-degeneri ma GENUINAMENTE identificabili.** Lo stage 1 ha
   misurato che un secondo modo con peso 0.01 da' max|corr| = 0.999871 contro
   1.000000 dei degeneri veri: un margine di 1.3e-04. I decoy esistono per far
   fallire il cancello nella direzione opposta — falsi negativi — e sono la
   ragione per cui l'endpoint primario non e' «zero falsi positivi» ma «zero
   falsi positivi SENZA regressione del recupero».
3. **Terza traiettoria ad ampiezza doppia.** E' il discriminante contro il
   surrogato di Taylor: `0.5 sin(u)` e la sua troncatura coincidono a piccola
   ampiezza e divergono a grande.

Ogni traiettoria viene verificata in risoluzione: se la coda spettrale supera
`TAIL_MAX` la generazione si ferma, invece di produrre un campo sotto-risolto
che il risolutore leggerebbe come «la legge non trasferisce» — un falso
negativo prodotto dal generatore, non dal motore.

Uso: python CDE_BLIND_PDE2_GENERATOR_V0.py [--pilota]
"""
from __future__ import annotations

import argparse
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
OUT = ART / "cde_blind_pde2_out"
CASES = OUT / "cases"
SEALED = OUT / "sealed"

_g = importlib.util.spec_from_file_location(
    "runtime_guard_bootstrap", BASE / "runtime_guard_bootstrap.py")
RGB = importlib.util.module_from_spec(_g)
_g.loader.exec_module(RGB)

import numpy as np                                        # noqa: E402

LIBRERIA = ("u", "u^2", "u^3", "u_x", "u_xx", "u_xxx", "uu_x")
FUORI_LIBRERIA = ("u_xxxx", "sin(u)", "tanh(u)")
AMMESSI = LIBRERIA + FUORI_LIBRERIA

NX = 768
T_FIN = 2.0
DT = 2e-4
SAVE_EVERY = 25
MOLT_AMPIEZZA = 2.0      # traiettoria di estrapolazione
TAIL_MAX = 1e-8          # energia frazionaria ammessa nel terzo centrale di k


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def _etdrk4(u0, L_hat, nonlin, dt, nsteps, save_every, dealias):
    v = np.fft.fft(u0)
    E = np.exp(dt * L_hat)
    E2 = np.exp(dt * L_hat / 2.0)
    M = 64
    r = np.exp(1j * np.pi * (np.arange(1, M + 1) - 0.5) / M)
    LR = dt * L_hat[:, None] + r[None, :]
    Q = dt * np.mean((np.exp(LR / 2.0) - 1.0) / LR, axis=1)
    f1 = dt * np.mean(
        (-4.0 - LR + np.exp(LR) * (4.0 - 3.0 * LR + np.square(LR)))
        / np.power(LR, 3), axis=1)
    f2 = dt * np.mean(
        (2.0 + LR + np.exp(LR) * (-2.0 + LR)) / np.power(LR, 3), axis=1)
    f3 = dt * np.mean(
        (-4.0 - 3.0 * LR - np.square(LR) + np.exp(LR) * (4.0 - LR))
        / np.power(LR, 3), axis=1)
    for nome, arr in (("Q", Q), ("f1", f1), ("f2", f2), ("f3", f3)):
        if not np.isfinite(arr).all():
            raise FloatingPointError(f"coefficiente ETDRK4 {nome} non finito")
    frames = [u0.copy()]
    for n in range(1, nsteps + 1):
        Nv = nonlin(v) * dealias
        a_ = E2 * v + Q * Nv
        Na = nonlin(a_) * dealias
        b_ = E2 * v + Q * Na
        Nb = nonlin(b_) * dealias
        c_ = E2 * a_ + Q * (2.0 * Nb - Nv)
        Nc = nonlin(c_) * dealias
        v = E * v + Nv * f1 + 2.0 * (Na + Nb) * f2 + Nc * f3
        if n % save_every == 0:
            frames.append(np.real(np.fft.ifft(v)))
    U = np.array(frames)
    if not np.isfinite(U).all():
        raise FloatingPointError("traiettoria non finita")
    return U


def coda_spettrale(U):
    """Frazione di energia nel terzo centrale dei numeri d'onda (sopra il
    taglio di dealiasing non c'e' nulla per costruzione)."""
    S = np.square(np.abs(np.fft.fft(U, axis=1)))
    n = S.shape[1]
    return float(S[:, n // 6: n // 3].sum() / max(S.sum(), 1e-300))


def _ic(x, seed, modi, ampiezza, offset, k_singolo, modi_pesati):
    if k_singolo is not None:
        fase = np.random.default_rng(seed).uniform(0.0, 2.0 * np.pi)
        return ampiezza * np.sin(k_singolo * x + fase) + offset
    if modi_pesati is not None:
        # somma esplicita di modi con pesi dati: serve ai decoy, dove il
        # secondo modo debole rompe la collinearita' ma di pochissimo
        f = sum(p * np.sin(k * x) for k, p in modi_pesati)
        return ampiezza * f + offset
    rng = np.random.default_rng(seed)
    f = np.zeros_like(x)
    for m in range(1, modi + 1):
        f = f + (rng.normal() * np.cos(m * x) + rng.normal() * np.sin(m * x)) / m
    return ampiezza * f / max(1e-9, np.abs(f).max()) + offset


def simula(coeffs, seed, Nx=NX, T=T_FIN, dt=DT, save_every=SAVE_EVERY,
           modi=3, ampiezza=1.0, offset=0.0, k_singolo=None,
           modi_pesati=None):
    ignoti = set(coeffs) - set(AMMESSI)
    if ignoti:
        raise ValueError(f"coefficienti non riconosciuti: {sorted(ignoti)}")
    x = np.linspace(0.0, 2.0 * np.pi, Nx, endpoint=False)
    kk = np.fft.fftfreq(Nx, d=1.0 / Nx)
    ik = 1j * kk
    L_hat = (coeffs.get("u", 0.0)
             + coeffs.get("u_x", 0.0) * ik
             + coeffs.get("u_xx", 0.0) * np.power(ik, 2)
             + coeffs.get("u_xxx", 0.0) * np.power(ik, 3)
             + coeffs.get("u_xxxx", 0.0) * np.power(ik, 4))
    dealias = (np.abs(kk) < Nx / 3.0).astype(float)
    a2, a3 = coeffs.get("u^2", 0.0), coeffs.get("u^3", 0.0)
    auux = coeffs.get("uu_x", 0.0)
    asin, atanh = coeffs.get("sin(u)", 0.0), coeffs.get("tanh(u)", 0.0)

    def nonlin(v):
        u = np.real(np.fft.ifft(v))
        out = np.zeros(Nx, dtype=complex)
        if a2:
            out = out + a2 * np.fft.fft(np.square(u))
        if a3:
            out = out + a3 * np.fft.fft(np.power(u, 3))
        if auux:
            out = out + auux * 0.5 * ik * np.fft.fft(np.square(u))
        if asin:
            out = out + asin * np.fft.fft(np.sin(u))
        if atanh:
            out = out + atanh * np.fft.fft(np.tanh(u))
        return out

    u0 = _ic(x, seed, modi, ampiezza, offset, k_singolo, modi_pesati)
    U = _etdrk4(u0, L_hat, nonlin, dt, int(round(T / dt)), save_every, dealias)
    t = np.arange(U.shape[0]) * dt * save_every
    return x, t, U


# ---------------------------------------------------------------------------
# Pannello 2. Disgiunto dal pannello 1 E dalle sonde dello stage 1.
# ---------------------------------------------------------------------------

def pannello():
    P = []

    def c(cid, famiglia, coeffs, esito, motivo, sigma=0.0, vincolo=None, **kw):
        P.append(dict(case_id=cid, famiglia=famiglia, coeff_veri=coeffs,
                      esito_atteso=esito, motivo=motivo, sigma=sigma,
                      vincolo=vincolo, opts=kw))

    # --- 10 RECUPERABILI, coefficienti tutti nuovi ------------------------
    c("case_01", "RECUPERABILE", {"u_xx": 0.150, "u": -0.60}, "CLAIM",
      "diffusione con decadimento")
    c("case_02", "RECUPERABILE", {"uu_x": -1.0, "u_xx": 0.045}, "CLAIM",
      "Burgers, viscosita' nuova", sigma=0.01)
    c("case_03", "RECUPERABILE", {"u_x": -0.90, "u_xx": 0.025, "u": 0.40},
      "CLAIM", "avvezione-diffusione-crescita")
    c("case_04", "RECUPERABILE", {"u_xx": 0.060, "u": 0.70, "u^2": -0.35},
      "CLAIM", "logistica su campo positivo", sigma=0.02,
      ampiezza=0.30, offset=0.50)
    c("case_05", "RECUPERABILE",
      {"uu_x": -1.0, "u_xx": 0.035, "u_xxx": -0.020}, "CLAIM",
      "Burgers-KdV, bilancio nuovo", sigma=0.01)
    c("case_06", "RECUPERABILE", {"u_xx": 0.080, "u^3": -0.50}, "CLAIM",
      "diffusione con saturazione cubica")
    c("case_07", "RECUPERABILE", {"u_x": -0.60, "u_xxx": -0.045}, "CLAIM",
      "avvezione dispersiva, IC multimodo")
    c("case_08", "RECUPERABILE", {"u_xx": 0.040, "u^2": 0.50, "u^3": -0.60},
      "CLAIM", "reazione quadratica e cubica", sigma=0.01, ampiezza=0.8)
    c("case_09", "RECUPERABILE",
      {"u_x": -0.30, "u_xx": 0.050, "uu_x": -1.0}, "CLAIM",
      "avvezione lineare e nonlineare insieme")
    c("case_10", "RECUPERABILE", {"u_xx": 0.120, "u": 0.80, "u^3": -0.80},
      "CLAIM", "Newell-Whitehead, coefficienti nuovi", sigma=0.02, ampiezza=0.9)

    # --- 4 NON IDENTIFICABILI, DUE CON RUMORE ------------------------------
    c("case_11", "NON_IDENTIFICABILE", {"u_x": -0.60, "u_xxx": -0.020},
      "ABSTAIN_OR_FLAG", "modo singolo k=2: u_xxx = -4u_x, famiglia a-4b=-0.52",
      sigma=0.0, k_singolo=2,
      vincolo={"termini": ["u_x", "u_xxx"], "pesi": [1.0, -4.0],
               "valore": -0.52})
    c("case_12", "NON_IDENTIFICABILE", {"u_xx": 0.080, "u": 0.50},
      "ABSTAIN_OR_FLAG",
      "modo singolo k=1 CON RUMORE: u_xx = -u, famiglia b-a=0.42",
      sigma=0.01, k_singolo=1,
      vincolo={"termini": ["u", "u_xx"], "pesi": [1.0, -1.0], "valore": 0.42})
    c("case_13", "NON_IDENTIFICABILE", {"u_xx": 0.030, "u": -0.20},
      "ABSTAIN_OR_FLAG",
      "modo singolo k=3 CON RUMORE: u_xx = -9u, famiglia -9a+b=-0.47",
      sigma=0.02, k_singolo=3,
      vincolo={"termini": ["u_xx", "u"], "pesi": [-9.0, 1.0], "valore": -0.47})
    c("case_14", "NON_IDENTIFICABILE", {"u_xx": 0.050, "u": 0.40},
      "ABSTAIN_OR_FLAG", "modo singolo k=2: u_xx = -4u, famiglia b-4a=0.20",
      sigma=0.0, k_singolo=2,
      vincolo={"termini": ["u", "u_xx"], "pesi": [1.0, -4.0], "valore": 0.20})

    # --- 2 DECOY: quasi degeneri ma IDENTIFICABILI -------------------------
    # Esistono per far fallire il cancello di condizionamento nella direzione
    # opposta. Lo stage 1 ha misurato max|corr| = 0.998777 a eps=0.03 e
    # 0.999871 a eps=0.01: il primo sta comodamente sotto la soglia 0.9999, il
    # secondo la sfiora. La risposta corretta per entrambi resta CLAIM.
    c("case_15", "DECOY", {"u_xx": 0.050, "u": 0.30}, "CLAIM",
      "due modi, secondo con peso 0.03: quasi degenere ma identificabile",
      modi_pesati=((1, 1.0), (2, 0.03)))
    c("case_16", "DECOY", {"u_xx": 0.050, "u": 0.30}, "CLAIM",
      "due modi, secondo con peso 0.01: al limite della soglia",
      modi_pesati=((1, 1.0), (2, 0.01)))

    # --- 4 SURROGATI: legge fuori libreria, Taylor la imita ----------------
    c("case_17", "SURROGATO", {"u_xx": 0.040, "sin(u)": 0.50}, "ABSTAIN",
      "sin(u) fuori libreria, ampiezza moderata", ampiezza=1.0)
    c("case_18", "SURROGATO", {"u_xx": 0.060, "sin(u)": 0.40}, "ABSTAIN",
      "sin(u) fuori libreria, ampiezza maggiore", ampiezza=1.4)
    # tanh al posto di exp: `u_t = 0.05u_xx + 0.3(exp(u)-1)` esplode in tempo
    # finito a doppia ampiezza — e' una proprieta' dell'equazione, non un
    # errore numerico, e un caso che non si puo' estrapolare non serve a
    # testare l'estrapolazione. tanh e' limitata e ha la stessa proprieta'
    # utile: il suo sviluppo u - u^3/3 sta tutto in libreria.
    c("case_19", "SURROGATO", {"u_xx": 0.050, "tanh(u)": 0.40}, "ABSTAIN",
      "tanh(u) fuori libreria: Taylor u - u^3/3 e' tutto in libreria",
      ampiezza=0.9)
    c("case_20", "SURROGATO", {"u_xx": 0.030, "u_xxxx": -0.0060}, "ABSTAIN",
      "u_xxxx fuori libreria: nessun polinomio in u lo imita")

    # --- 2 CONTROLLI di astensione ----------------------------------------
    c("case_21", "CONTROLLO", {}, "ABSTAIN", "rumore filtrato",
      generatore="rumore")
    c("case_22", "CONTROLLO", {}, "ABSTAIN", "surrogato di fase",
      generatore="surrogato", base={"uu_x": -1.0, "u_xx": 0.045})
    return P


def _campo(spec, seed, molt_ampiezza=1.0):
    opts = dict(spec["opts"])
    gen = opts.pop("generatore", None)
    base = opts.pop("base", None)
    Nx = opts.pop("Nx", NX)
    if molt_ampiezza != 1.0:
        opts["ampiezza"] = opts.get("ampiezza", 1.0) * molt_ampiezza

    if gen == "rumore":
        rng = np.random.default_rng(seed)
        x = np.linspace(0.0, 2.0 * np.pi, Nx, endpoint=False)
        t = np.arange(81) * (DT * SAVE_EVERY * 10)
        kk = np.fft.fftfreq(Nx, d=1.0 / Nx)
        filtro = 1.0 / (1.0 + np.square(kk / 4.0))
        W = rng.normal(size=(len(t), Nx))
        return x, t, np.real(np.fft.ifft(np.fft.fft(W, axis=1) * filtro, axis=1))
    if gen == "surrogato":
        x, t, U = simula(base, seed, Nx=Nx, **opts)
        rng = np.random.default_rng(seed + 991)
        S = np.fft.fft2(U)
        W = np.fft.fft2(rng.normal(size=U.shape))
        mag = np.abs(W)
        mag[mag == 0] = 1.0
        return x, t, np.real(np.fft.ifft2(np.abs(S) * (W / mag)))
    return simula(spec["coeff_veri"], seed, Nx=Nx, **opts)


def genera(pilota: bool):
    P = pannello()
    if pilota:
        P = P[:1]
    CASES.mkdir(parents=True, exist_ok=True)
    SEALED.mkdir(parents=True, exist_ok=True)

    pubblico, verita = [], []
    for i, spec in enumerate(P):
        cid = spec["case_id"]
        sa = 77000 + 23 * i
        x, t, U = _campo(spec, sa)                       # scoperta
        _, _, U2 = _campo(spec, sa + 7)                  # transfer, IC diversa
        _, _, U3 = _campo(spec, sa + 11, MOLT_AMPIEZZA)  # estrapolazione

        # Il controllo di risoluzione vale solo per i campi integrati: un
        # controllo di rumore non ha una PDE da risolvere, e la sua coda
        # spettrale alta e' cio' che lo rende un controllo.
        integrato = "generatore" not in spec["opts"]
        for nome, campo in (("U", U), ("U2", U2), ("U3", U3)) if integrato else ():
            coda = coda_spettrale(campo)
            if coda > TAIL_MAX:
                raise SystemExit(
                    f"{cid}/{nome}: coda spettrale {coda:.2e} > {TAIL_MAX:.0e} "
                    "— campo sotto-risolto, generazione fermata")

        sigma = spec["sigma"]
        if sigma > 0.0:
            nr = np.random.default_rng(sa + int(sigma * 1e4))
            U = U + nr.normal(0.0, sigma * float(U.std()), U.shape)
            U2 = U2 + nr.normal(0.0, sigma * float(U2.std()), U2.shape)
            U3 = U3 + nr.normal(0.0, sigma * float(U3.std()), U3.shape)

        np.savez_compressed(CASES / f"{cid}.npz", x=x, t=t, U=U, U2=U2, U3=U3)
        pubblico.append({"case_id": cid, "Nx": int(len(x)), "Nt": int(len(t)),
                         "u_std": round(float(U.std()), 6),
                         "u3_std": round(float(U3.std()), 6),
                         "file": f"cases/{cid}.npz"})
        verita.append({k: spec[k] for k in
                       ("case_id", "famiglia", "coeff_veri", "esito_atteso",
                        "motivo", "sigma", "vincolo")})

    (CASES / "public_manifest.json").write_text(json.dumps(
        {"generato": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
         "n_casi": len(pubblico), "molt_ampiezza": MOLT_AMPIEZZA,
         "casi": pubblico}, indent=2, ensure_ascii=False))
    tp = SEALED / "truth.json"
    tp.write_text(json.dumps(
        {"generato": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
         "commit": _git_commit(), "molt_ampiezza": MOLT_AMPIEZZA,
         "casi": verita}, indent=2, ensure_ascii=False))
    sha = hashlib.sha256(tp.read_bytes()).hexdigest()
    (SEALED / "truth.sha256").write_text(sha + "\n")
    return len(pubblico), sha


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilota", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    n, sha = genera(a.pilota)
    print(f"casi generati: {n}")
    print(f"sha256 sealed/truth.json: {sha}")
    print(f"python {platform.python_version()}  numpy {np.__version__}")
    print(f"wall-clock: {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
