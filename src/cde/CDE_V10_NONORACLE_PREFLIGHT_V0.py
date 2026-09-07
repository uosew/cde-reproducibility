#!/usr/bin/env python3
"""CDE V10 — NOP: preflight NON-ORACLE (protocollo v2.0, preregistrato).

Implementa il preflight di auto-consistenza della preregistrazione
PREREGISTRATION_PROTOCOL_V2_2026_07_30.md (commit bb8f3427), sezione 1:

  P1  accordo di quadratura (Simpson vs trapezio, stesse finestre);
  P2  accordo tra famiglie di test function (bump v1.1 vs bump^2, entrambe
      C-infinito a supporto compatto; cross-residuo simmetrico, max);
  P3  holdout predittivo sulle finestre (split 70/30, rng seed 2026);
  P4  (diagnostica, non decisionale) residuo LS a risoluzione /2.

Calibrazione soglie: tau_i = 3 * max(metrica_i) sui 4 dataset V8 sigma=0
seed 7 (decisione oracle nota: OPEN). Poi soglie CONGELATE e valutate sul
set di valutazione preregistrato (2 rifiuti storici + 3 open). L'oracle
r_GT viene calcolato SOLO per la matrice di accordo NOP/oracle.

Uso:  python CDE_V10_NONORACLE_PREFLIGHT_V0.py [--smoke]
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
OUT = ART / "cde_v10_nonoracle_preflight_v0_out"

PREREG = "PREREGISTRATION_PROTOCOL_V2_2026_07_30.md @ bb8f3427"
CAL_MARGIN = 3.0                      # M, preregistrato
HOLDOUT_SEED = 2026                   # preregistrato
HOLDOUT_FRAC = 0.30                   # preregistrato


def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, BASE / fname)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RGB_spec = importlib.util.spec_from_file_location(
    "runtime_guard_bootstrap", BASE / "runtime_guard_bootstrap.py")
RGB = importlib.util.module_from_spec(RGB_spec)
RGB_spec.loader.exec_module(RGB)

import numpy as np                                    # noqa: E402

V7 = _load("v7", "CDE_WEAK_OPERATOR_COMPONENTWISE_IDENTITY_V7.py")
V8 = _load("v8", "CDE_PDE_DISCOVERY_V8.py")
V9 = _load("v9", "CDE_KS_DISCOVERY_V9.py")
EXT = _load("ext", "CDE_V8_EXTERNAL_SOLVER_REPLICATION_V0.py")


def _git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


# ----------------------------------------------------------------------------
# Famiglia B: bump^2 = exp(-2/(1-s^2)). Compatta, C-infinito; derivate esatte
# in termini delle derivate del bump v1.1 (gia' validate) + d4 di V9.
# ----------------------------------------------------------------------------

class Bump2:
    name = "bump2"

    @staticmethod
    def phi(s):
        return np.square(V7.Bump.phi(s))

    @staticmethod
    def dphi(s):
        return 2.0 * V7.Bump.phi(s) * V7.Bump.dphi(s)

    @staticmethod
    def d2phi(s):
        p, d1, d2 = V7.Bump.phi(s), V7.Bump.dphi(s), V7.Bump.d2phi(s)
        return 2.0 * (np.square(d1) + p * d2)

    @staticmethod
    def d3phi(s):
        p = V7.Bump.phi(s)
        d1, d2, d3 = V7.Bump.dphi(s), V7.Bump.d2phi(s), V7.Bump.d3phi(s)
        return 2.0 * (3.0 * d1 * d2 + p * d3)

    @staticmethod
    def d4phi(s):
        p = V7.Bump.phi(s)
        d1, d2 = V7.Bump.dphi(s), V7.Bump.d2phi(s)
        d3, d4 = V7.Bump.d3phi(s), V9.bump_d4phi(s)
        return 2.0 * (3.0 * np.square(d2) + 4.0 * d1 * d3 + p * d4)


class BumpA:
    """Famiglia A = bump v1.1 con la d4 di V9 (gia' validata dal track D4)."""
    name = "bump"
    phi = staticmethod(V7.Bump.phi)
    dphi = staticmethod(V7.Bump.dphi)
    d2phi = staticmethod(V7.Bump.d2phi)
    d3phi = staticmethod(V7.Bump.d3phi)
    d4phi = staticmethod(V9.bump_d4phi)


def validate_bump2(tol=1e-4):
    """Gate componentwise (stile track D4): derivate 1..4 di bump^2 vs FD
    centrali sulla phi analitica di bump^2. Il gate cattura errori di
    codifica delle formule di Leibniz (discrepanze O(1)); si verifica su
    |s|<=0.75 dove il troncamento FD non e' dominato dall'esplosione delle
    derivate del bump al bordo del supporto ((1-s^2)^-k)."""
    s = np.linspace(-0.75, 0.75, 301)
    hs = {1: 1e-3, 2: 1e-3, 3: 2e-3, 4: 4e-3}
    ana = {1: Bump2.dphi(s), 2: Bump2.d2phi(s),
           3: Bump2.d3phi(s), 4: Bump2.d4phi(s)}

    def fd_k(k, h):
        ph = [Bump2.phi(s + j * h) for j in (-3, -2, -1, 0, 1, 2, 3)]
        if k == 1:
            return (ph[4] - ph[2]) / (2 * h)
        if k == 2:
            return (ph[4] - 2 * ph[3] + ph[2]) / h ** 2
        if k == 3:
            return (ph[5] - 2 * ph[4] + 2 * ph[2] - ph[1]) / (2 * h ** 3)
        return (ph[5] - 4 * ph[4] + 6 * ph[3] - 4 * ph[2] + ph[1]) / h ** 4

    errs = {}
    for k in (1, 2, 3, 4):
        h = hs[k]
        # Richardson (elimina il termine h^2): O(h^4)
        fd = (4.0 * fd_k(k, h / 2.0) - fd_k(k, h)) / 3.0
        scale = np.max(np.abs(ana[k]))
        errs[k] = float(np.max(np.abs(ana[k] - fd)) / scale)
        assert errs[k] < tol, f"bump2 d{k}phi: err FD {errs[k]:.2e} >= {tol}"
    return {f"d{k}_rel_err_vs_fd": errs[k] for k in errs}


# ----------------------------------------------------------------------------
# Feature deboli parametrizzate su (termini, regola, famiglia)
# ----------------------------------------------------------------------------

def weak_features_nop(x, t, U, wx, wt, centers, terms, rule, fam):
    ig = V7.integ_grid
    cols = {k: [] for k in ("b_time",) + tuple(terms)}
    need4 = "u_xxxx" in terms
    for (xc, tc) in centers:
        mx = (x >= xc - wx) & (x <= xc + wx)
        mt = (t >= tc - wt) & (t <= tc + wt)
        xs, ts = x[mx], t[mt]
        sx = (xs - xc) / wx
        st = (ts - tc) / wt
        Uw = U[np.ix_(mt, mx)]
        Uw2 = np.square(Uw)
        Uw3 = np.power(Uw, 3)
        px = fam.phi(sx)
        dpx = fam.dphi(sx) / wx
        d2px = fam.d2phi(sx) / wx ** 2
        d3px = fam.d3phi(sx) / wx ** 3
        d4px = fam.d4phi(sx) / wx ** 4 if need4 else None
        pt = fam.phi(st)
        dpt = fam.dphi(st) / wt

        def II(F, gx, gt):
            inner = np.array([ig(F[i] * gx, xs, rule)
                              for i in range(F.shape[0])])
            return ig(inner * gt, ts, rule)

        cols["b_time"].append(-II(Uw, px, dpt))
        cols["u"].append(II(Uw, px, pt))
        cols["u^2"].append(II(Uw2, px, pt))
        cols["u^3"].append(II(Uw3, px, pt))
        cols["u_x"].append(-II(Uw, dpx, pt))
        cols["u_xx"].append(II(Uw, d2px, pt))
        cols["u_xxx"].append(-II(Uw, d3px, pt))
        if need4:
            cols["u_xxxx"].append(II(Uw, d4px, pt))
        cols["uu_x"].append(-0.5 * II(Uw2, dpx, pt))
    return {k: np.array(v) for k, v in cols.items()}


def to_Ab(F, terms):
    return np.column_stack([F[k] for k in terms]), F["b_time"]


# ----------------------------------------------------------------------------
# Generatori parametrizzati (copie fedeli, con assert di fedelta' vs modulo)
# ----------------------------------------------------------------------------

def simulate_kdv_param(seed, Nx):
    x = np.linspace(0.0, 2.0 * np.pi, Nx, endpoint=False)
    k = np.fft.fftfreq(Nx, d=1.0 / Nx) * 1.0j
    delta2 = 0.0484
    L_hat = -delta2 * np.power(k, 3)
    dealias = (np.abs(np.fft.fftfreq(Nx, d=1.0 / Nx)) < Nx / 3.0).astype(float)
    rng = np.random.default_rng(seed)
    c = rng.normal(0.0, 1.0, 3) / np.arange(1, 4)
    s = rng.normal(0.0, 1.0, 3) / np.arange(1, 4)
    f = sum(c[m] * np.cos((m + 1) * x) + s[m] * np.sin((m + 1) * x)
            for m in range(3))
    u0 = f / max(1e-9, np.abs(f).max())

    def nonlin(v):
        u = np.real(np.fft.ifft(v))
        return -0.5 * k * np.fft.fft(np.square(u))

    dt, Tf = 2e-4, 2.0
    save_every = 25
    U = V8.etdrk4_complex(u0, L_hat, nonlin, dt, int(round(Tf / dt)),
                          save_every, dealias)
    t = np.arange(U.shape[0]) * dt * save_every
    return x, t, U


def simulate_ks_param(seed, Nx, save_every, T_trans, T_keep):
    x = np.linspace(0.0, V9.KS_L, Nx, endpoint=False)
    kf = np.fft.fftfreq(Nx, d=1.0 / Nx) * (2.0 * np.pi / V9.KS_L)
    k2 = np.square(kf)
    L_hat = (k2 - np.square(k2)) + 0.0j
    kc = 1.0j * kf
    dealias = (np.abs(np.fft.fftfreq(Nx, d=1.0 / Nx)) < Nx / 3.0).astype(float)
    rng = np.random.default_rng(seed)
    u0 = 0.1 * rng.standard_normal(Nx)
    u0 = np.real(np.fft.ifft(np.fft.fft(u0) * (np.abs(kf) < 1.5)))

    def nonlin(v):
        u = np.real(np.fft.ifft(v))
        return -0.5 * kc * np.fft.fft(np.square(u))

    dt = 0.05
    U_all = V7.etdrk4(u0, L_hat, nonlin, dt,
                      int(round((T_trans + T_keep) / dt)), save_every, dealias)
    t_all = np.arange(U_all.shape[0]) * dt * save_every
    keep = t_all >= T_trans
    U = U_all[keep]
    t = t_all[keep] - t_all[keep][0]
    return x, t, U


def fidelity_checks():
    """Le copie parametrizzate devono riprodurre bit-a-bit i generatori
    committati nelle configurazioni di riferimento (smoke: economiche)."""
    xk, tk, Uk = simulate_kdv_param(7, 256)
    xv, tv, Uv, _ = V8.simulate_kdv(7, True)
    assert np.array_equal(Uk, Uv) and np.array_equal(xk, xv), \
        "copia simulate_kdv non fedele"
    xs_, ts_, Us_ = simulate_ks_param(7, 512, 5, 30.0, 40.0)
    xw, tw, Uw = V9.simulate_ks(7, True)
    assert np.array_equal(Us_, Uw) and np.array_equal(xs_, xw), \
        "copia simulate_ks non fedele"
    return True


# ----------------------------------------------------------------------------
# Dataset del protocollo (calibrazione + valutazione preregistrate)
# ----------------------------------------------------------------------------

def make_centers(x, t, wx, wt, K, seed, t_off):
    rng = np.random.default_rng(seed + 101)
    xc = rng.uniform(x[0] + wx, x[-1] - wx, K)
    tc = rng.uniform(t[0] + wt + t_off, t[-1] - wt, K)
    return list(zip(xc, tc))


def datasets(smoke):
    K = 60 if smoke else 200
    seed = 7
    out = []

    def v8like(name, x, t, U, true_c, role, expect_open):
        out.append({"name": name, "x": x, "t": t, "U": U,
                    "terms": V8.TERMS, "true": true_c,
                    "wx": 1.0, "wt": 0.30, "t_off": 0.05, "K": K,
                    "role": role, "oracle_expect_open": expect_open})

    for s in ("allen_cahn", "fisher_kpp", "burgers"):
        x, t, U, tc = V8.simulate(s, seed, smoke)
        v8like(s, x, t, U, tc, "calibration", True)
    x, t, U, tc = V8.simulate_kdv(seed, smoke)
    v8like("kdv", x, t, U, tc, "calibration", True)

    # valutazione 1: KdV bassa risoluzione (rifiuto storico, Nx=512)
    x, t, U = simulate_kdv_param(seed, 256 if smoke else 512)
    v8like("kdv_lowres", x, t, U, V8.TRUE_COEFFS["kdv"], "evaluation", False)

    # valutazione 2-3: KS a campionamento V8-standard (rifiuto storico)
    # e KS full (open). In smoke si riduce tutto ma i ruoli restano.
    if smoke:
        xl, tl, Ul = simulate_ks_param(seed, 256, 10, 30.0, 40.0)
        xf, tf, Uf = V9.simulate_ks(seed, True)
    else:
        xl, tl, Ul = simulate_ks_param(seed, 1024, 5, 60.0, 100.0)
        xf, tf, Uf = V9.simulate_ks(seed, False)
    out.append({"name": "ks_lowres", "x": xl, "t": tl, "U": Ul,
                "terms": V9.TERMS9, "true": V9.KS_TRUE,
                "wx": 8.0, "wt": 5.0, "t_off": 0.5, "K": K,
                "role": "evaluation", "oracle_expect_open": False})
    out.append({"name": "ks_full", "x": xf, "t": tf, "U": Uf,
                "terms": V9.TERMS9, "true": V9.KS_TRUE,
                "wx": 12.0, "wt": 7.5, "t_off": 0.5, "K": K,
                "role": "evaluation", "oracle_expect_open": True})

    # valutazione 4-5: bracci solver esterno FD4/RK45 (open)
    for s in ("burgers", "fisher_kpp"):
        x, t, U, tc = EXT.simulate_external(s, seed, smoke)
        out.append({"name": f"{s}_ext", "x": x, "t": t, "U": U,
                    "terms": V8.TERMS, "true": tc,
                    "wx": 1.0, "wt": 0.30, "t_off": 0.05, "K": K,
                    "role": "evaluation", "oracle_expect_open": True})
    return out


# ----------------------------------------------------------------------------
# Metriche NOP
# ----------------------------------------------------------------------------

def rel_col_diff(FA, FB, terms):
    d = 0.0
    for k in ("b_time",) + tuple(terms):
        na = float(np.linalg.norm(FA[k]))
        if na < 1e-300:
            continue
        d = max(d, float(np.linalg.norm(FA[k] - FB[k]) / na))
    return d


def ls_fit(A, b):
    c, *_ = np.linalg.lstsq(A, b, rcond=None)
    return c


def rel_resid(A, b, c):
    return float(np.linalg.norm(A @ c - b) / np.linalg.norm(b))


def nop_metrics(ds):
    x, t, U = ds["x"], ds["t"], ds["U"]
    terms, wx, wt, K = ds["terms"], ds["wx"], ds["wt"], ds["K"]
    centers = make_centers(x, t, wx, wt, K, 7, ds["t_off"])

    F_as = weak_features_nop(x, t, U, wx, wt, centers, terms, "simpson", BumpA)
    F_at = weak_features_nop(x, t, U, wx, wt, centers, terms, "trapezoid",
                             BumpA)
    F_bs = weak_features_nop(x, t, U, wx, wt, centers, terms, "simpson", Bump2)

    A_a, b_a = to_Ab(F_as, terms)
    A_b, b_b = to_Ab(F_bs, terms)

    p1 = rel_col_diff(F_as, F_at, terms)

    c_a, c_b = ls_fit(A_a, b_a), ls_fit(A_b, b_b)
    p2 = max(rel_resid(A_b, b_b, c_a), rel_resid(A_a, b_a, c_b))

    rng = np.random.default_rng(HOLDOUT_SEED)
    perm = rng.permutation(len(b_a))
    n_hold = max(1, int(round(HOLDOUT_FRAC * len(b_a))))
    hold, train = perm[:n_hold], perm[n_hold:]
    c_tr = ls_fit(A_a[train], b_a[train])
    p3 = rel_resid(A_a[hold], b_a[hold], c_tr)

    # P4 diagnostica: stesso operatore su campo sottocampionato /2
    F_sub = weak_features_nop(x[::2], t[::2], U[::2, ::2], wx, wt, centers,
                              terms, "simpson", BumpA)
    A_s, b_s = to_Ab(F_sub, terms)
    p4 = rel_resid(A_s, b_s, ls_fit(A_s, b_s))
    r_ls_full = rel_resid(A_a, b_a, c_a)

    cvec = np.array([ds["true"].get(k, 0.0) for k in terms])
    r_gt = rel_resid(A_a, b_a, cvec)

    return {"P1_dquad": p1, "P2_cross": p2, "P3_holdout": p3,
            "P4_subsample_rls": p4, "r_ls_full": r_ls_full,
            "r_GT_oracle": r_gt,
            "oracle_open": bool(r_gt < V8.GATE_R_GT)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    t0 = time.time()
    OUT.mkdir(exist_ok=True)
    guard = RGB.enforce_runtime_guard(strict=True)

    print("== gate componentwise bump2 (derivate 1..4 vs FD) ==")
    b2 = validate_bump2()
    print("   " + " ".join(f"d{k[1]}={v:.1e}" for k, v in b2.items()))
    print("== fidelity check copie parametrizzate (bit-identiche) ==")
    fidelity_checks()
    print("   OK")

    res = {"run": "CDE_V10_NONORACLE_PREFLIGHT_V0", "smoke": args.smoke,
           "prereg": PREREG, "margin_M": CAL_MARGIN,
           "holdout": {"seed": HOLDOUT_SEED, "frac": HOLDOUT_FRAC},
           "bump2_gate": b2, "datasets": {}}

    for ds in datasets(args.smoke):
        m = nop_metrics(ds)
        m["role"] = ds["role"]
        m["oracle_expect_open"] = ds["oracle_expect_open"]
        res["datasets"][ds["name"]] = m
        print(f"== {ds['name']} ({ds['role']}) ==")
        print(f"   P1={m['P1_dquad']:.2e} P2={m['P2_cross']:.2e} "
              f"P3={m['P3_holdout']:.2e} | P4(diag)={m['P4_subsample_rls']:.2e}"
              f" r_LS={m['r_ls_full']:.2e} | r_GT={m['r_GT_oracle']:.2e} "
              f"oracle_open={m['oracle_open']}")

    cal = {k: v for k, v in res["datasets"].items()
           if v["role"] == "calibration"}
    taus = {p: CAL_MARGIN * max(v[p] for v in cal.values())
            for p in ("P1_dquad", "P2_cross", "P3_holdout")}
    res["taus"] = taus
    print(f"== soglie congelate (M={CAL_MARGIN}) == " +
          " ".join(f"{p}<={t:.2e}" for p, t in taus.items()))

    agree = {"n_eval": 0, "n_agree": 0, "detail": {}}
    for name, m in res["datasets"].items():
        nop_open = all(m[p] <= taus[p]
                       for p in ("P1_dquad", "P2_cross", "P3_holdout"))
        m["nop_open"] = bool(nop_open)
        if m["role"] == "evaluation":
            ok = nop_open == m["oracle_open"]
            agree["n_eval"] += 1
            agree["n_agree"] += int(ok)
            agree["detail"][name] = {"nop_open": nop_open,
                                     "oracle_open": m["oracle_open"],
                                     "agree": ok}
            print(f"   {name}: NOP={'OPEN' if nop_open else 'REFUSE'} "
                  f"oracle={'OPEN' if m['oracle_open'] else 'REFUSE'} "
                  f"{'OK' if ok else 'DISACCORDO'}")
    res["agreement"] = agree
    res["agreement_perfect"] = bool(agree["n_agree"] == agree["n_eval"])
    # coerenza interna: sui dataset di calibrazione il NOP deve essere OPEN
    # per costruzione (soglie = 3x il massimo osservato)
    assert all(res["datasets"][k]["nop_open"] for k in cal), \
        "incoerenza: dataset di calibrazione non-OPEN con soglie 3x"

    res["elapsed_s"] = round(time.time() - t0, 2)
    suffix = "_smoke" if args.smoke else ""
    rp = OUT / f"results{suffix}.json"
    rp.write_text(json.dumps(res, indent=2))
    env = {"run": "CDE_V10_NONORACLE_PREFLIGHT_V0",
           "timestamp_utc": datetime.now(timezone.utc)
                                    .strftime("%Y-%m-%dT%H:%M:%SZ"),
           "results_sha256": hashlib.sha256(rp.read_bytes()).hexdigest(),
           "python_version": platform.python_version(),
           "numpy_version": np.__version__,
           "platform": platform.platform(),
           "git_commit": _git_commit(),
           "runtime_guard": guard,
           "human_review_required": True}
    (OUT / f"evidence_envelope{suffix}.json").write_text(
        json.dumps(env, indent=2))
    print(f"accordo NOP/oracle: {agree['n_agree']}/{agree['n_eval']}"
          f" | output in {OUT}  ({res['elapsed_s']}s)")


if __name__ == "__main__":
    main()
