#!/usr/bin/env python3
"""CDE_WEAK_OPERATOR_COMPONENTWISE_IDENTITY_V7 — validazione componente per componente.

Campagna chirurgica successiva alla V6. La V6 ha stabilito che NON esiste un
unico bug nel weak operator: Allen-Cahn e' dominato dall'errore dell'operatore
TEMPORALE (integrazione diretta di u_t riduce il residuo GT di ~68x),
Fisher-KPP migliora ma conserva ~15% di residuo, Burgers non migliora
(problema nell'operatore SPAZIALE, in particolare nel termine convettivo uu_x).

Questa V7 separa completamente le componenti e le valida come un sistema
numerico, PRIMA di tornare alla scoperta simbolica:

  Track T — convergenza temporale di  ∫ u_t φ = -∫ u φ' + [uφ]
    su segnale sintetico analitico noto; test function: gaussian IBP senza
    boundary (diagnostica, fail atteso), gaussian CON boundary, bump C-inf,
    B-spline cubica; quadrature: trapezi, Simpson, Gauss-Legendre; piu'
    risoluzioni temporali.
    GATE: errore relativo < 1e-6 oppure ordine di convergenza chiaramente
    verificato (ordine empirico >= 0.8 * ordine teorico, errore decrescente).

  Track S — identita' spaziali testate SINGOLARMENTE su funzioni analitiche:
      ∫ u_x   φ = -∫ u φ_x   + boundary
      ∫ u_xx  φ =  ∫ u φ_xx  + boundary
      ∫ u_xxx φ = -∫ u φ_xxx + boundary
      ∫ u u_x φ = -(1/2) ∫ u^2 φ_x + boundary        (termine convettivo Burgers)
    Ogni identita' deve passare su funzioni analitiche note prima di essere
    applicata a una PDE. Stesso GATE del track T.

  Track PDE — SOLO dopo il pass di T e S: Allen-Cahn, Fisher-KPP, Burgers
    (solver spettrale ETDRK4, dealiasing 2/3). Si calcola il residuo ground
    truth r_GT con i coefficienti VERI, senza sparse selection:
        r_GT = ||A c_true - b||_2 / ||b||_2
    su K finestre spazio-temporali con test function bump separabili.
    GATE: r_GT < 1e-3 per aprire la discovery (la discovery NON viene
    eseguita in questa campagna).

Claim boundary: la validazione vale per segnali/soluzioni lisce su dominio
periodico e per le quattro identita' elencate; nessuna claim sulla discovery.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.integrate import quad, simpson

BASE = Path(__file__).resolve().parent
ART = BASE.parent.parent / "artifacts"      # public layout (cde-reproducibility)
PAPER = BASE.parent.parent / "paper"
ROOT = BASE.parent
OUT = ART / "cde_weak_operator_componentwise_identity_v7_out"

GATE_REL_ERR = 1e-6
GATE_ORDER_FRAC = 0.8      # ordine empirico >= 0.8 * ordine teorico
GATE_R_GT = 1e-3


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


# ----------------------------------------------------------------------------
# Test functions su finestra [a,b], parametrizzate in s = (2t-(a+b))/(b-a).
# Ogni classe espone phi, dphi, d2phi, d3phi (derivate in s) e compact_support.
# ----------------------------------------------------------------------------

class Bump:
    """C-infinito a supporto compatto: exp(-1/(1-s^2))."""
    name = "bump"
    compact_support = True
    # convergenza superalgebrica, ma l'ordine osservabile a N moderati e' ~4-6:
    # si dichiara 4 (conservativo, comunque > di Simpson su funzioni generiche)
    theoretical_order = {"trapezoid": 4.0, "simpson": 4.0}
    gl_order = 6.0

    @staticmethod
    def phi(s):
        s = np.asarray(s, float)
        out = np.zeros_like(s)
        m = np.abs(s) < 1.0
        out[m] = np.exp(-1.0 / (1.0 - s[m] ** 2))
        return out

    @staticmethod
    def _g1(s):   # g' con g = -1/(1-s^2)
        return -2.0 * s / (1.0 - s ** 2) ** 2

    @staticmethod
    def _g2(s):
        return -2.0 * (1.0 + 3.0 * s ** 2) / (1.0 - s ** 2) ** 3

    @staticmethod
    def _g3(s):
        return -24.0 * s * (1.0 + s ** 2) / (1.0 - s ** 2) ** 4

    @classmethod
    def dphi(cls, s):
        s = np.asarray(s, float)
        out = np.zeros_like(s)
        m = np.abs(s) < 1.0
        out[m] = cls.phi(s[m]) * cls._g1(s[m])
        return out

    @classmethod
    def d2phi(cls, s):
        s = np.asarray(s, float)
        out = np.zeros_like(s)
        m = np.abs(s) < 1.0
        sm = s[m]
        out[m] = cls.phi(sm) * (cls._g1(sm) ** 2 + cls._g2(sm))
        return out

    @classmethod
    def d3phi(cls, s):
        s = np.asarray(s, float)
        out = np.zeros_like(s)
        m = np.abs(s) < 1.0
        sm = s[m]
        g1, g2, g3 = cls._g1(sm), cls._g2(sm), cls._g3(sm)
        out[m] = cls.phi(sm) * (g1 ** 3 + 3.0 * g1 * g2 + g3)
        return out


class BSpline3:
    """B-spline cubica standard B3 riscalata al supporto [-1,1] (C^2)."""
    name = "bspline3"
    compact_support = True
    theoretical_order = {"trapezoid": 2.0, "simpson": 4.0}
    gl_order = 2.0   # C^2 con nodi interni: G-L non composita non e' spettrale

    @staticmethod
    def _b3(x):
        x = np.abs(np.asarray(x, float))
        out = np.zeros_like(x)
        m1 = x < 1.0
        m2 = (x >= 1.0) & (x < 2.0)
        out[m1] = 2.0 / 3.0 - x[m1] ** 2 + 0.5 * x[m1] ** 3
        out[m2] = (2.0 - x[m2]) ** 3 / 6.0
        return out

    @staticmethod
    def _db3(x):
        x = np.asarray(x, float)
        ax = np.abs(x)
        out = np.zeros_like(x)
        m1 = ax < 1.0
        m2 = (ax >= 1.0) & (ax < 2.0)
        out[m1] = -2.0 * ax[m1] + 1.5 * ax[m1] ** 2
        out[m2] = -0.5 * (2.0 - ax[m2]) ** 2
        return out * np.sign(x)

    @staticmethod
    def _d2b3(x):
        x = np.abs(np.asarray(x, float))
        out = np.zeros_like(x)
        m1 = x < 1.0
        m2 = (x >= 1.0) & (x < 2.0)
        out[m1] = -2.0 + 3.0 * x[m1]
        out[m2] = 2.0 - x[m2]
        return out

    @staticmethod
    def _d3b3(x):
        x = np.asarray(x, float)
        ax = np.abs(x)
        out = np.zeros_like(x)
        out[ax < 1.0] = 3.0
        out[(ax >= 1.0) & (ax < 2.0)] = -1.0
        return out * np.sign(x)

    @classmethod
    def phi(cls, s):
        return cls._b3(2.0 * np.asarray(s, float))

    @classmethod
    def dphi(cls, s):
        return 2.0 * cls._db3(2.0 * np.asarray(s, float))

    @classmethod
    def d2phi(cls, s):
        return 4.0 * cls._d2b3(2.0 * np.asarray(s, float))

    @classmethod
    def d3phi(cls, s):
        return 8.0 * cls._d3b3(2.0 * np.asarray(s, float))


class GaussTest:
    """Gaussiana troncata alla finestra: boundary NON trascurabile."""
    name = "gaussian"
    compact_support = False
    theoretical_order = {"trapezoid": 2.0, "simpson": 4.0}
    gl_order = 6.0
    SIG = 0.35

    @classmethod
    def phi(cls, s):
        return np.exp(-np.asarray(s, float) ** 2 / (2.0 * cls.SIG ** 2))

    @classmethod
    def dphi(cls, s):
        s = np.asarray(s, float)
        return -s / cls.SIG ** 2 * cls.phi(s)

    @classmethod
    def d2phi(cls, s):
        s = np.asarray(s, float)
        return (s ** 2 / cls.SIG ** 4 - 1.0 / cls.SIG ** 2) * cls.phi(s)

    @classmethod
    def d3phi(cls, s):
        s = np.asarray(s, float)
        return (3.0 * s / cls.SIG ** 4 - s ** 3 / cls.SIG ** 6) * cls.phi(s)


# ----------------------------------------------------------------------------
# Quadrature su [a,b] da campioni (trapezi/Simpson) o da valutazioni (G-L).
# ----------------------------------------------------------------------------

def integ_grid(y, x, rule: str) -> float:
    if rule == "trapezoid":
        return float(np.trapezoid(y, x))
    if rule == "simpson":
        return float(simpson(y, x=x))
    raise ValueError(rule)


def integ_gl(fn, a: float, b: float, n: int) -> float:
    z, w = leggauss(n)
    x = 0.5 * (b - a) * z + 0.5 * (a + b)
    return float(0.5 * (b - a) * np.sum(w * fn(x)))


def empirical_order(hs, errs):
    """Pendenza di log(err) vs log(h) sugli ultimi raffinamenti utili."""
    hs, errs = np.asarray(hs, float), np.asarray(errs, float)
    m = errs > 1e-15                      # sotto ~1e-15 domina il roundoff
    if m.sum() < 2:
        return float("inf")               # gia' a macchina: convergenza banale
    hs, errs = hs[m], errs[m]
    k = min(3, len(hs) - 1)
    return float(np.polyfit(np.log(hs[-k - 1:]), np.log(errs[-k - 1:]), 1)[0])


def gate_config(errs, hs, theo_order) -> dict:
    errs = np.asarray(errs, float)
    best = float(np.nanmin(errs))
    order = empirical_order(hs, errs)
    decreasing = bool(errs[-1] <= errs[0])
    ok = best < GATE_REL_ERR or (order >= GATE_ORDER_FRAC * theo_order and decreasing)
    return {"best_rel_err": best, "empirical_order": order,
            "theoretical_order": theo_order, "monotone_decreasing": decreasing,
            "pass": bool(ok)}


# ----------------------------------------------------------------------------
# Track T — convergenza temporale
# ----------------------------------------------------------------------------

def u_sig(t):
    return np.sin(3.0 * t) * np.exp(-((t - 1.0) ** 2) / 0.32)


def du_sig(t):
    return (3.0 * np.cos(3.0 * t) - np.sin(3.0 * t) * 2.0 * (t - 1.0) / 0.32) \
        * np.exp(-((t - 1.0) ** 2) / 0.32)


def track_T(smoke: bool) -> dict:
    a, b = 0.3, 1.7
    c, w = 0.5 * (a + b), 0.5 * (b - a)
    Ns = [33, 65, 129, 257] if smoke else [33, 65, 129, 257, 513, 1025]
    GLn = [8, 16, 32] if smoke else [8, 16, 32, 64]
    tests = [Bump, BSpline3, GaussTest]
    out = {"window": [a, b], "configs": {}}

    for T in tests:
        # riferimento: LHS = int u' phi (u' analitico, quad a 1e-13)
        ref = quad(lambda t: du_sig(t) * T.phi((t - c) / w), a, b,
                   epsabs=1e-13, epsrel=1e-13, limit=400)[0]
        variants = ["with_boundary"] if T.compact_support else \
                   ["ibp_no_boundary", "with_boundary"]
        for variant in variants:
            for rule in ("trapezoid", "simpson"):
                errs, hs = [], []
                for N in Ns:
                    t = np.linspace(a, b, N)
                    s = (t - c) / w
                    rhs = -integ_grid(u_sig(t) * T.dphi(s) / w, t, rule)
                    if variant == "with_boundary":
                        rhs += u_sig(b) * T.phi(np.array([1.0]))[0] \
                             - u_sig(a) * T.phi(np.array([-1.0]))[0]
                    errs.append(abs(rhs - ref) / abs(ref))
                    hs.append((b - a) / (N - 1))
                key = f"{T.name}/{variant}/{rule}"
                g = gate_config(errs, hs, T.theoretical_order[rule])
                g["rel_errs"] = errs
                g["Ns"] = Ns
                g["expected_fail"] = (variant == "ibp_no_boundary")
                out["configs"][key] = g
            # Gauss-Legendre: valutazione diretta ai nodi
            errs, hs = [], []
            for n in GLn:
                rhs = -integ_gl(lambda x: u_sig(x) * T.dphi((x - c) / w) / w,
                                a, b, n)
                if variant == "with_boundary":
                    rhs += u_sig(b) * T.phi(np.array([1.0]))[0] \
                         - u_sig(a) * T.phi(np.array([-1.0]))[0]
                errs.append(abs(rhs - ref) / abs(ref))
                hs.append((b - a) / n)
            key = f"{T.name}/{variant}/gauss_legendre"
            g = gate_config(errs, hs, T.gl_order)
            g["rel_errs"] = errs
            g["Ns"] = GLn
            g["expected_fail"] = (variant == "ibp_no_boundary")
            out["configs"][key] = g

    gated = {k: v for k, v in out["configs"].items() if not v["expected_fail"]}
    out["gate_pass"] = all(v["pass"] for v in gated.values())
    out["n_configs_gated"] = len(gated)
    out["diagnostics_expected_fail"] = {
        k: v["best_rel_err"] for k, v in out["configs"].items() if v["expected_fail"]}
    return out


# ----------------------------------------------------------------------------
# Track S — identita' spaziali singole su funzioni analitiche
# ----------------------------------------------------------------------------

def make_u_trig():
    """u(x) liscia con derivate analitiche fino alla terza."""
    def u(x):
        return np.sin(x) + 0.4 * np.cos(2.0 * x) + 0.2 * np.sin(3.0 * x + 0.5)

    def u1(x):
        return np.cos(x) - 0.8 * np.sin(2.0 * x) + 0.6 * np.cos(3.0 * x + 0.5)

    def u2(x):
        return -np.sin(x) - 1.6 * np.cos(2.0 * x) - 1.8 * np.sin(3.0 * x + 0.5)

    def u3(x):
        return -np.cos(x) + 3.2 * np.sin(2.0 * x) - 5.4 * np.cos(3.0 * x + 0.5)

    return {"name": "trig_mix", "u": u, "u1": u1, "u2": u2, "u3": u3}


def make_u_gaussian():
    s2 = 0.5

    def u(x):
        return np.exp(-((x - np.pi) ** 2) / s2)

    def u1(x):
        return -2.0 * (x - np.pi) / s2 * u(x)

    def u2(x):
        return (4.0 * (x - np.pi) ** 2 / s2 ** 2 - 2.0 / s2) * u(x)

    def u3(x):
        return (12.0 * (x - np.pi) / s2 ** 2
                - 8.0 * (x - np.pi) ** 3 / s2 ** 3) * u(x)

    return {"name": "gaussian", "u": u, "u1": u1, "u2": u2, "u3": u3}


def track_S(smoke: bool) -> dict:
    a, b = 1.2, 5.0
    c, w = 0.5 * (a + b), 0.5 * (b - a)
    Ns = [65, 129, 257] if smoke else [65, 129, 257, 513, 1025]
    out = {"window": [a, b], "configs": {}}

    identities = {
        # nome: LHS analitico, RHS dai soli campioni di u, boundary analitico
        "D1_ux": {
            "lhs": lambda U, T, t: U["u1"](t) * T.phi((t - c) / w),
            "rhs_grid": lambda U, T, x, s, rule:
                -integ_grid(U["u"](x) * T.dphi(s) / w, x, rule),
            "bnd": lambda U, T:
                U["u"](b) * T.phi(np.array([1.0]))[0]
                - U["u"](a) * T.phi(np.array([-1.0]))[0],
        },
        "D2_uxx": {
            "lhs": lambda U, T, t: U["u2"](t) * T.phi((t - c) / w),
            "rhs_grid": lambda U, T, x, s, rule:
                integ_grid(U["u"](x) * T.d2phi(s) / w ** 2, x, rule),
            "bnd": lambda U, T:
                (U["u1"](b) * T.phi(np.array([1.0]))[0]
                 - U["u"](b) * T.dphi(np.array([1.0]))[0] / w)
                - (U["u1"](a) * T.phi(np.array([-1.0]))[0]
                   - U["u"](a) * T.dphi(np.array([-1.0]))[0] / w),
        },
        "D3_uxxx": {
            "lhs": lambda U, T, t: U["u3"](t) * T.phi((t - c) / w),
            "rhs_grid": lambda U, T, x, s, rule:
                -integ_grid(U["u"](x) * T.d3phi(s) / w ** 3, x, rule),
            "bnd": lambda U, T:
                (U["u2"](b) * T.phi(np.array([1.0]))[0]
                 - U["u1"](b) * T.dphi(np.array([1.0]))[0] / w
                 + U["u"](b) * T.d2phi(np.array([1.0]))[0] / w ** 2)
                - (U["u2"](a) * T.phi(np.array([-1.0]))[0]
                   - U["u1"](a) * T.dphi(np.array([-1.0]))[0] / w
                   + U["u"](a) * T.d2phi(np.array([-1.0]))[0] / w ** 2),
        },
        "NL_uux": {
            "lhs": lambda U, T, t: U["u"](t) * U["u1"](t) * T.phi((t - c) / w),
            "rhs_grid": lambda U, T, x, s, rule:
                -0.5 * integ_grid(U["u"](x) ** 2 * T.dphi(s) / w, x, rule),
            "bnd": lambda U, T:
                0.5 * (U["u"](b) ** 2 * T.phi(np.array([1.0]))[0]
                       - U["u"](a) ** 2 * T.phi(np.array([-1.0]))[0]),
        },
    }

    for U in (make_u_trig(), make_u_gaussian()):
        for T in (Bump, BSpline3, GaussTest):
            for iname, ident in identities.items():
                ref = quad(lambda t: ident["lhs"](U, T, t), a, b,
                           epsabs=1e-13, epsrel=1e-13, limit=400)[0]
                if abs(ref) < 1e-12:      # riferimento degenere: salta
                    continue
                for rule in ("trapezoid", "simpson"):
                    errs, hs = [], []
                    for N in Ns:
                        x = np.linspace(a, b, N)
                        s = (x - c) / w
                        rhs = ident["rhs_grid"](U, T, x, s, rule)
                        if not T.compact_support:
                            rhs += ident["bnd"](U, T)
                        errs.append(abs(rhs - ref) / abs(ref))
                        hs.append((b - a) / (N - 1))
                    theo = T.theoretical_order[rule]
                    if T is BSpline3 and iname == "D3_uxxx":
                        theo = 1.0        # phi''' della B-spline e' discontinua
                    g = gate_config(errs, hs, theo)
                    g["rel_errs"] = errs
                    g["Ns"] = Ns
                    key = f"{U['name']}/{T.name}/{iname}/{rule}"
                    out["configs"][key] = g

    out["gate_pass"] = all(v["pass"] for v in out["configs"].values())
    out["n_configs"] = len(out["configs"])
    return out


# ----------------------------------------------------------------------------
# Track PDE — solver spettrale ETDRK4 + residuo ground truth r_GT
# ----------------------------------------------------------------------------

def _etdrk4_coeffs(z):
    """Coefficienti ETDRK4 per z REALE, in forma chiusa + Taylor per |z| piccolo.

    Sostituisce la media su contorno complesso di Kassam-Trefethen: su questa
    macchina la ufunc exp complessa vettorizzata dentro funzioni ha prodotto
    corruzioni NON deterministiche (debug V7 del 2026-07-28: stessi input,
    exp(LR) con re(LR)<=1 che 'overflowa' e f3 inf su indici casuali).
    Con z reale il contorno non serve: bastano le serie vicino a z=0.
    """
    z = np.asarray(z, float)
    small = np.abs(z) < 0.5
    zs = np.where(small, 0.0, z)          # evita 0/0 nel ramo diretto
    with np.errstate(divide="ignore", invalid="ignore"):
        q_d = (np.exp(zs / 2.0) - 1.0) / zs
        g1_d = (-4.0 - zs + np.exp(zs) * (4.0 - 3.0 * zs + zs ** 2)) / zs ** 3
        g2_d = (2.0 + zs + np.exp(zs) * (-2.0 + zs)) / zs ** 3
        g3_d = (-4.0 - 3.0 * zs - zs ** 2 + np.exp(zs) * (4.0 - zs)) / zs ** 3
    # serie di Taylor (coefficienti esatti dai fattoriali), |z|<0.5: err<1e-16
    import math
    K = 22
    fact = [math.factorial(i) for i in range(K + 3)]
    q_s = np.zeros_like(z)
    g1_s = np.zeros_like(z)
    g2_s = np.zeros_like(z)
    g3_s = np.zeros_like(z)
    zp = np.ones_like(z)
    for k_ in range(K):
        q_s += zp / (2.0 ** (k_ + 1) * fact[k_ + 1])
        kk = k_ + 3
        g1_s += zp * (4.0 / fact[kk] - 3.0 / fact[kk - 1] + 1.0 / fact[kk - 2])
        g2_s += zp * (-2.0 / fact[kk] + 1.0 / fact[kk - 1])
        g3_s += zp * (4.0 / fact[kk] - 1.0 / fact[kk - 1])
        zp = zp * z
    q = np.where(small, q_s, q_d)
    g1 = np.where(small, g1_s, g1_d)
    g2 = np.where(small, g2_s, g2_d)
    g3 = np.where(small, g3_s, g3_d)
    return q, g1, g2, g3


def etdrk4(u0, L_hat, nonlin, dt, nsteps, save_every, dealias):
    """ETDRK4 in spazio di Fourier per L reale (diffusione). u_t = L u + N(u)."""
    Lr = np.real(L_hat)
    v = np.fft.fft(u0)
    E = np.exp(dt * Lr)
    E2 = np.exp(dt * Lr / 2.0)
    z = dt * Lr
    q, g1, g2, g3 = _etdrk4_coeffs(z)
    Q, f1, f2, f3 = dt * q, dt * g1, dt * g2, dt * g3
    for nm, arr in (("Q", Q), ("f1", f1), ("f2", f2), ("f3", f3)):
        if not np.isfinite(arr).all():
            raise FloatingPointError(f"coefficiente ETDRK4 {nm} non finito")

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
    return np.array(frames)


def simulate_pde(name: str, seed: int, smoke: bool):
    # NB: la risoluzione spaziale determina i punti per finestra debole; il
    # debug V7 ha mostrato che ~23 punti/finestra producono errori O(1) su
    # int u psi_xx (stesso sintomo della V6 su Burgers). Servono >~80 punti.
    Nx = 256 if smoke else 512
    x = np.linspace(0.0, 2.0 * np.pi, Nx, endpoint=False)
    k = np.fft.fftfreq(Nx, d=1.0 / Nx) * 1.0j
    k2 = np.real(k ** 2)
    dealias = (np.abs(np.fft.fftfreq(Nx, d=1.0 / Nx)) < Nx / 3.0).astype(float)
    rng = np.random.default_rng(seed)

    def smooth_ic(lo, hi):
        c = rng.normal(0.0, 1.0, 4) / np.arange(1, 5)
        s = rng.normal(0.0, 1.0, 4) / np.arange(1, 5)
        f = sum(c[m] * np.cos((m + 1) * x) + s[m] * np.sin((m + 1) * x)
                for m in range(4))
        f = (f - f.min()) / (f.max() - f.min())
        return lo + (hi - lo) * f

    if name == "allen_cahn":
        eps = 0.05
        L_hat = eps * k2 + 0.0j
        u0 = smooth_ic(-0.9, 0.9)

        def nonlin(v):
            u = np.real(np.fft.ifft(v))
            return np.fft.fft(u - u ** 3)

        Tf, dt = 4.0, 1e-3
        coeffs = {"u_xx": eps, "u": 1.0, "u^3": -1.0}
    elif name == "fisher_kpp":
        D, r_ = 0.05, 1.0
        L_hat = D * k2 + 0.0j
        u0 = smooth_ic(0.05, 0.6)

        def nonlin(v):
            u = np.real(np.fft.ifft(v))
            return np.fft.fft(r_ * u * (1.0 - u))

        Tf, dt = 3.0, 1e-3
        coeffs = {"u_xx": D, "u": r_, "u^2": -r_}
    elif name == "burgers":
        nu = 0.08
        L_hat = nu * k2 + 0.0j
        u0 = smooth_ic(-1.0, 1.0)

        def nonlin(v):
            u = np.real(np.fft.ifft(v))
            return -0.5 * k * np.fft.fft(u ** 2)   # -(u^2/2)_x

        Tf, dt = 2.0, 5e-4
        coeffs = {"uu_x": -1.0, "u_xx": nu}
    else:
        raise ValueError(name)

    save_every = 5
    nsteps = int(round(Tf / dt))
    U = etdrk4(u0, L_hat, nonlin, dt, nsteps, save_every, dealias)
    t = np.arange(U.shape[0]) * dt * save_every
    return x, t, U, coeffs


def weak_features(x, t, U, wx, wt, centers, rule="simpson"):
    """Feature deboli su finestre con test bump separabile psi=phix(x)phit(t).

    Usa SOLO i campioni di U (mai derivate di u). Una colonna per feature.
    """
    cols = {"b_time": [], "u": [], "u^2": [], "u^3": [], "u_xx": [], "uu_x": []}
    for (xc, tc) in centers:
        mx = (x >= xc - wx) & (x <= xc + wx)
        mt = (t >= tc - wt) & (t <= tc + wt)
        xs, ts = x[mx], t[mt]
        sx = (xs - xc) / wx
        st = (ts - tc) / wt
        Uw = U[np.ix_(mt, mx)]
        px, dpx, d2px = Bump.phi(sx), Bump.dphi(sx) / wx, Bump.d2phi(sx) / wx ** 2
        pt, dpt = Bump.phi(st), Bump.dphi(st) / wt

        def II(F, gx, gt):
            inner = np.array([integ_grid(F[i] * gx, xs, rule)
                              for i in range(F.shape[0])])
            return integ_grid(inner * gt, ts, rule)

        # ATTENZIONE: mai operatori infissi (** * + -) su array grandi (>=256KB)
        # riusati come locali: su numpy 2.2.6 + CPython 3.14.0 l'elisione dei
        # temporanei MUTA l'operando in place (bug riprodotto il 2026-07-28:
        # 'Uw ** 2' trasformava Uw in Uw^2 e le feature successive ricevevano
        # Uw^4, Uw^6 — origine del residuo Burgers 0.80 e del sintomo V6).
        # Le ufunc esplicite (np.square/np.power) non passano dal percorso
        # di elisione e sono sicure.
        Uw2 = np.square(Uw)
        Uw3 = np.power(Uw, 3)
        cols["b_time"].append(-II(Uw, px, dpt))           # int u_t psi
        cols["u"].append(II(Uw, px, pt))
        cols["u^2"].append(II(Uw2, px, pt))
        cols["u^3"].append(II(Uw3, px, pt))
        cols["u_xx"].append(II(Uw, d2px, pt))             # int u psi_xx
        cols["uu_x"].append(-0.5 * II(Uw2, dpx, pt))      # -(1/2) int u^2 psi_x
    return {k: np.array(v) for k, v in cols.items()}


def track_PDE(seed: int, smoke: bool) -> dict:
    out = {}
    K = 60 if smoke else 200
    rng = np.random.default_rng(seed + 1)
    for name in ("allen_cahn", "fisher_kpp", "burgers"):
        x, t, U, coeffs = simulate_pde(name, seed, smoke)
        wx, wt = 1.0, 0.30
        xc = rng.uniform(x[0] + wx, x[-1] - wx, K)
        tc = rng.uniform(t[0] + wt + 0.05, t[-1] - wt, K)
        F = weak_features(x, t, U, wx, wt, list(zip(xc, tc)))
        b = F["b_time"]
        A = np.column_stack([F[term] for term in coeffs])
        c = np.array(list(coeffs.values()))
        r_gt = float(np.linalg.norm(A @ c - b) / np.linalg.norm(b))
        out[name] = {
            "coeffs_true": coeffs,
            "K_windows": K,
            "grid": {"Nx": len(x), "Nt": len(t)},
            "r_GT": r_gt,
            "discovery_gate_open": bool(r_gt < GATE_R_GT),
        }
    out["gate_pass"] = all(v["discovery_gate_open"]
                           for k, v in out.items() if isinstance(v, dict))
    return out


# ----------------------------------------------------------------------------

def numpy_elision_bug_canary() -> bool:
    """True se l'elisione dei temporanei numpy muta i locali (bug ambiente).

    Su numpy 2.2.6 + CPython 3.14.0 (macOS arm64), 'a ** 2' DENTRO una
    funzione muta 'a' quando nbytes >= 256KB. La V7 e' scritta per essere
    corretta comunque (ufunc esplicite sul percorso PDE), ma il flag viene
    registrato nell'envelope perche' invalida potenzialmente ogni altro
    script numpy del laboratorio eseguito su questo interprete.
    """
    a = np.full(32768, 2.0)   # 256 KB
    _ = a ** 2
    return bool(a[0] != 2.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    t0 = time.time()
    OUT.mkdir(exist_ok=True)

    # runtime guard obbligatorio PRIMA di qualsiasi calcolo (quarantena
    # 2026-07-28): blocca ambienti non verificati; LB_GUARD_ALLOW_FORENSIC=1
    # solo per riprodurre il bug con evidenza marcata non attendibile.
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location("runtime_guard_bootstrap",
                                         BASE / "runtime_guard_bootstrap.py")
    _rgb = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_rgb)
    runtime_guard = _rgb.enforce_runtime_guard(strict=True)

    elision_bug = numpy_elision_bug_canary()
    if elision_bug:
        print("!! ambiente: elisione temporanei numpy muta i locali "
              "(numpy 2.2.6 + py3.14) — percorso PDE gia' schermato con ufunc")

    print("== Track T: convergenza temporale ==")
    resT = track_T(args.smoke)
    print(f"   gate_pass={resT['gate_pass']}  ({resT['n_configs_gated']} config)")
    for k, v in resT["diagnostics_expected_fail"].items():
        print(f"   [diagnostica, fail atteso] {k}: err={v:.2e}")

    print("== Track S: identita' spaziali ==")
    resS = track_S(args.smoke)
    print(f"   gate_pass={resS['gate_pass']}  ({resS['n_configs']} config)")

    if resT["gate_pass"] and resS["gate_pass"]:
        print("== Track PDE: r_GT senza sparse selection ==")
        resP = track_PDE(args.seed, args.smoke)
        for k, v in resP.items():
            if isinstance(v, dict):
                print(f"   {k}: r_GT={v['r_GT']:.3e}  gate_open={v['discovery_gate_open']}")
    else:
        resP = {"skipped": "track T o S non passati", "gate_pass": False}
        print("== Track PDE SALTATO: track T/S non passati ==")

    results = {
        "run": "CDE_WEAK_OPERATOR_COMPONENTWISE_IDENTITY_V7",
        "seed": args.seed,
        "smoke": args.smoke,
        "gates": {"rel_err": GATE_REL_ERR, "order_frac": GATE_ORDER_FRAC,
                  "r_GT": GATE_R_GT},
        "track_T": resT,
        "track_S": resS,
        "track_PDE": resP,
        "elapsed_s": round(time.time() - t0, 2),
    }
    # le run smoke non devono sovrascrivere gli artifact canonici (regola di
    # quarantena: mai sovrascrivere run storiche)
    suffix = "_smoke" if args.smoke else ""
    res_path = OUT / f"results{suffix}.json"
    res_path.write_text(json.dumps(results, indent=2))

    envelope = {
        "run": "CDE_WEAK_OPERATOR_COMPONENTWISE_IDENTITY_V7",
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "results_sha256": hashlib.sha256(res_path.read_bytes()).hexdigest(),
        "seed": args.seed,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "platform": platform.platform(),
        "git_commit": _git_commit(),
        "numpy_temp_elision_bug_detected": elision_bug,
        "runtime_guard": runtime_guard,
        "human_review_required": True,
    }
    (OUT / f"evidence_envelope{suffix}.json").write_text(
        json.dumps(envelope, indent=2))

    verdict = ("TUTTI I GATE APERTI: discovery autorizzata"
               if resT["gate_pass"] and resS["gate_pass"]
               and resP.get("gate_pass") else
               "GATE NON APERTI: discovery NON autorizzata")
    card = [
        "# Claim card — CDE_WEAK_OPERATOR_COMPONENTWISE_IDENTITY_V7",
        "",
        f"- Track T (temporale): gate_pass={resT['gate_pass']} "
        f"su {resT['n_configs_gated']} configurazioni corrette; la variante "
        "gaussiana IBP senza boundary e' diagnostica (fail atteso).",
        f"- Track S (identita' spaziali D1/D2/D3/NL): gate_pass={resS['gate_pass']} "
        f"su {resS.get('n_configs', 0)} configurazioni.",
    ]
    if isinstance(resP, dict) and "allen_cahn" in resP:
        for k in ("allen_cahn", "fisher_kpp", "burgers"):
            v = resP[k]
            card.append(f"- {k}: r_GT={v['r_GT']:.3e} "
                        f"(gate<{GATE_R_GT}) -> open={v['discovery_gate_open']}")
    card += ["", f"**Verdetto: {verdict}**", "",
             "Claim boundary: validazione su segnali/soluzioni lisce, dominio "
             "periodico, test bump/B-spline/gaussiana; nessuna claim di discovery."]
    (OUT / f"claim_card{suffix}.md").write_text("\n".join(card))

    print(f"\n{verdict}")
    print(f"Output in {OUT}  ({results['elapsed_s']}s)")


if __name__ == "__main__":
    main()
