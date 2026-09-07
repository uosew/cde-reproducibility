#!/usr/bin/env python3
"""Genera le figure della research note ESCLUSIVAMENTE dagli artifact
committati, con la stessa disciplina del builder testuale: importa
build_research_note_v0 (che a import-time rilegge tutti i results.json e
fallisce se un claim non e' supportato) e prende ogni numero da li'.

L'unica eccezione dichiarata e' il campo KS della fig. 1: i results.json non
contengono i campi grezzi, quindi viene RIGENERATO deterministicamente con il
generatore congelato (CDE_KS_DISCOVERY_V9.simulate_ks, seed 7) e verificato
contro i metadati committati (Nx, Nt, L, std(u)) prima dell'uso.

Output (in arxiv_note/): fig_ks_field.pdf, fig_coef_err.pdf, fig_gate_null.pdf
Uso:  python build_note_figures_v0.py
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

BASE = Path(__file__).resolve().parent
ART = BASE.parent.parent / "artifacts"      # public layout (cde-reproducibility)
PAPER = BASE.parent.parent / "paper"
ROOT = BASE.parent
OUTDIR = PAPER
OUTDIR.mkdir(exist_ok=True)


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RGB = _load_module("runtime_guard_bootstrap", BASE / "runtime_guard_bootstrap.py")
GUARD = RGB.enforce_runtime_guard(strict=True)

import numpy as np                     # noqa: E402  (dopo il guard)
import matplotlib                      # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt        # noqa: E402

M = _load_module("note_md", BASE / "build_research_note_v0.py")  # assert claims

plt.rcParams.update({
    "font.size": 8.5,
    "axes.titlesize": 9,
    "axes.labelsize": 8.5,
    "legend.fontsize": 7.5,
    "mathtext.fontset": "cm",
    "axes.linewidth": 0.6,
    "figure.dpi": 150,
})

SIG_PCT = [float(s) * 100 for s in M.SIGMAS]
COLORS = {"allen_cahn": "#1f77b4", "fisher_kpp": "#2ca02c",
          "burgers": "#d62728", "kdv": "#9467bd", "ks": "#111111"}
GATE = M.v8["protocol"]["gate_fit_resid"]        # 0.05, dal protocollo v1.1


# ----------------------------------------------------------------------------
# Fig. 1 -- campo KS (pulito e a sigma=10%), rigenerato e verificato
# ----------------------------------------------------------------------------

def fig_ks_field():
    V9 = _load_module("v9", BASE / "CDE_KS_DISCOVERY_V9.py")
    x, t, U = V9.simulate_ks(seed=int(M.ks["seed"]), smoke=False)
    grid = M.sys_res(M.ks, "ks")["grid"]
    assert U.shape == (int(grid["Nt"]), int(grid["Nx"])), \
        f"campo rigenerato {U.shape} != grid committata"
    assert abs(float(np.max(x)) + (x[1] - x[0]) - grid["L"]) < 1e-9
    u_std = float(np.std(U))
    assert abs(u_std - grid["u_std"]) / grid["u_std"] < 1e-9, \
        "std(u) rigenerata diversa da quella committata: campo non identico"

    sigma_show = 0.1
    rng = np.random.default_rng(int(M.ks["seed"]))
    U_noisy = U + sigma_show * u_std * rng.standard_normal(U.shape)

    vmax = float(np.max(np.abs(U_noisy)))
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.1), sharey=True,
                             constrained_layout=True)
    for ax, field, title in (
            (axes[0], U, r"clean field $u(x,t)$"),
            (axes[1], U_noisy, r"observed, $\sigma = 10\%$")):
        im = ax.pcolormesh(t, x, field.T, cmap="RdBu_r", vmin=-vmax,
                           vmax=vmax, rasterized=True, shading="auto")
        ax.set_title(title)
        ax.set_xlabel(r"$t$")
    axes[0].set_ylabel(r"$x$")
    fig.colorbar(im, ax=axes, shrink=0.85, pad=0.015)
    fig.savefig(OUTDIR / "fig_ks_field.pdf")
    plt.close(fig)


# ----------------------------------------------------------------------------
# Fig. 2 -- errore massimo sui coefficienti vs sigma, CDE e baseline PySINDy
# ----------------------------------------------------------------------------

def fig_coef_err():
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.5), sharey=True,
                             constrained_layout=True)

    ax = axes[0]
    for label, run, systems in M.all_runs:
        ls = "-" if label == "seed 7" else "--"
        for s in systems:
            errs = [M.sys_res(run, s)["sigma"][sig]["coef_rel_err_max"] * 100
                    for sig in M.SIGMAS]
            ax.plot(SIG_PCT, np.maximum(errs, 1e-6), ls, marker="o",
                    ms=2.5, lw=1.0, color=COLORS[s],
                    label=M.NAME[s] if label == "seed 7" else None)
    ax.set_title("CDE frozen protocol (v1.1)")
    ax.set_ylabel("max coefficient error [%]")

    ax = axes[1]
    for s, res in M.BL["systems"].items():
        errs, exact = [], []
        for sig in M.SIGMAS:
            r = res["sigma"][sig]
            errs.append(max(r["coef_rel_err_max"] * 100, 1e-6))
            exact.append(bool(r["support_exact"]))
        ax.plot(SIG_PCT, errs, "-", lw=1.0, color=COLORS[s], alpha=0.85)
        ok = [i for i, e in enumerate(exact) if e]
        ko = [i for i, e in enumerate(exact) if not e]
        ax.plot([SIG_PCT[i] for i in ok], [errs[i] for i in ok], "o",
                ms=2.5, color=COLORS[s])
        if ko:
            ax.plot([SIG_PCT[i] for i in ko], [errs[i] for i in ko], "x",
                    ms=5, mew=1.4, color=COLORS[s])
    ax.set_title("PySINDy weak (oracle threshold)")

    for ax in axes:
        ax.set_yscale("log")
        ax.axhline(5.0, color="0.4", lw=0.7, ls=":")
        ax.text(0.2, 5.0 * 1.25, "5% coefficient gate", color="0.35",
                fontsize=7)
        ax.set_xlabel(r"noise level $\sigma$ [% of std$(u)$]")
        ax.set_xticks(SIG_PCT)
    axes[0].legend(frameon=False, loc="lower right", ncol=2)
    fig.savefig(OUTDIR / "fig_coef_err.pdf")
    plt.close(fig)


# ----------------------------------------------------------------------------
# Fig. 3 -- (a) separazione dei residui vero/nullo; (b) decomposizione causale
# ----------------------------------------------------------------------------

def fig_gate_null():
    true_res, null_res = [], {}
    for label, run, systems in M.all_runs:
        for s in systems:
            r = M.sys_res(run, s)
            for sig in M.SIGMAS:
                true_res.append(r["sigma"][sig]["fit_rel_resid"])
            for n in r["nulls"]["detail"]:
                null_res.setdefault(n["kind"], []).append(n["fit_rel_resid"])
    assert max(true_res) < GATE and all(
        min(v) > GATE for v in null_res.values())

    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.5),
                             constrained_layout=True,
                             gridspec_kw={"width_ratios": [1.15, 1]})

    ax = axes[0]
    rng = np.random.default_rng(0)

    def strip(xc, vals, color, label):
        xs = xc + 0.09 * rng.standard_normal(len(vals))
        ax.plot(xs, vals, "o", ms=2.6, alpha=0.6, color=color, mew=0,
                label=f"{label}  (n={len(vals)})")

    strip(0, true_res, "#1f77b4", "claimed discoveries")
    strip(1, null_res.get("shuffle_t", []), "#d62728", "temporal shuffles")
    strip(2, null_res.get("phase_surrogate", []), "#ff7f0e",
          "phase surrogates")
    ax.axhline(GATE, color="0.2", lw=0.9, ls="--")
    ax.text(-0.42, GATE * 1.5, "5% residual gate", fontsize=7, color="0.2")
    ax.set_yscale("log")
    ax.set_xlim(-0.5, 2.5)
    ax.set_xticks([0, 1, 2], ["true\nsystems", "shuffled\nnulls",
                              "surrogate\nnulls"])
    ax.set_ylabel(r"relative fit residual $\|A_S c_S - b\|/\|b\|$")
    ax.set_title("(a) residual separation, all campaigns")
    ax.legend(frameon=False, loc="lower right", handletextpad=0.2)

    ax = axes[1]
    n_bl = M.bl_null_runs
    groups = [
        ("CDE frozen", 100.0 * M.cde_cells_total / M.bl_cells_total, 0.0),
        ("PySINDy\n(oracle thr.)", 100.0 * M.bl_cells_exact / M.bl_cells_total,
         100.0 * M.bl_null_fd / n_bl),
        ("PySINDy +\nepistemic gate", 100.0 * M.bl_gated_true / M.bl_cells_total,
         100.0 * M.bl_fd_gated / n_bl),
    ]
    xg = np.arange(len(groups))
    w = 0.36
    b1 = ax.bar(xg - w / 2, [g[1] for g in groups], w, color="#1f77b4",
                label="true cells claimed")
    b2 = ax.bar(xg + w / 2, [g[2] for g in groups], w, color="#d62728",
                label="null false-discovery rate")
    for bars in (b1, b2):
        for rect in bars:
            ax.annotate(f"{rect.get_height():.0f}%",
                        (rect.get_x() + rect.get_width() / 2,
                         rect.get_height()),
                        textcoords="offset points", xytext=(0, 1.5),
                        ha="center", fontsize=7)
    ax.set_xticks(xg, [g[0] for g in groups])
    ax.set_ylim(0, 150)
    ax.set_ylabel("[%]")
    ax.set_title("(b) causal decomposition (paired)")
    ax.legend(frameon=False, loc="upper right", handletextpad=0.4)
    fig.savefig(OUTDIR / "fig_gate_null.pdf")
    plt.close(fig)


def fig_resolution():
    import json
    st1 = json.loads((ART / "cde_risoluzione_claim_out" / "stage1.json").read_text())["righe"]
    d4 = json.loads((ART / "cde_blind4_out" / "claim_dettaglio.json").read_text())["claim"]
    false = [r for r in st1 if r["falsa"]]
    f1 = [list(r["contributi_mancanti"].values())[0] for r in false]
    x1 = [r["k"]["1.0"]["X"] for r in false]; x2 = [r["k"]["2.0"]["X"] for r in false]
    v1 = sum(f >= x for f, x in zip(f1, x1)); v2 = sum(f >= x for f, x in zip(f1, x2))
    assert v2 == 0 and v1 > 0
    ss = [r for r in d4 if r["mancanti"]]; ex = [r for r in d4 if r["esatta"]]
    f4 = [list(r["mancanti"].values())[0] for r in ss]; x4 = [r["X"] for r in ss]
    assert all(f < x for f, x in zip(f4, x4))
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.6), constrained_layout=True)
    ax = axes[0]
    lim = max(max(x2), max(f1)) * 1.15
    ax.fill_between([0, lim], [0, lim], [lim, lim], color="#d62728", alpha=0.07, lw=0)
    ax.plot([0, lim], [0, lim], "-", color="0.3", lw=0.8)
    ax.plot(f1, x1, "s", ms=4.5, color="#ff7f0e", mew=0, label=f"$k=1$ ({v1} violations)")
    ax.plot(f1, x2, "o", ms=4.5, color="#1f77b4", mew=0, label="$k=2$ (0 violations)")
    ax.text(lim * 0.55, lim * 0.93, "violation: $f \\geq X$", fontsize=7, color="#a00000")
    ax.set_xlim(0, lim); ax.set_ylim(0, lim)
    ax.set_xlabel("contribution $f$ of the missing term"); ax.set_ylabel("declared bound $X$")
    ax.set_title(f"(a) sealed replica, {len(false)} sub-support claims (diagnostic)")
    ax.legend(frameon=False, loc="lower right", handletextpad=0.3)
    ax = axes[1]
    lim = max(max(x4), max(r["X"] for r in ex)) * 1.08
    ax.fill_between([0, lim], [0, lim], [lim, lim], color="#d62728", alpha=0.07, lw=0)
    ax.plot([0, lim], [0, lim], "-", color="0.3", lw=0.8)
    ax.plot(f4, x4, "o", ms=5, color="#1f77b4", mew=0, label=f"{len(ss)} sub-support claims, $k=2$")
    rng = np.random.default_rng(0)
    ax.plot(-0.004 + 0.0015 * rng.standard_normal(len(ex)), [r["X"] for r in ex], "|", ms=5, color="0.55", mew=0.8, label=f"$X$ of the {len(ex)} exact claims")
    ax.set_xlim(-0.008, lim); ax.set_ylim(0, lim)
    ax.set_xlabel("contribution $f$ of the missing term"); ax.set_ylabel("declared bound $X$")
    ax.set_title("(b) second sealed panel, scored blind")
    ax.legend(frameon=False, loc="lower right", handletextpad=0.3)
    fig.savefig(OUTDIR / "fig_resolution.pdf")
    plt.close(fig)


if __name__ == "__main__":
    fig_coef_err()
    fig_gate_null()
    fig_ks_field()
    fig_resolution()
    for f in ("fig_ks_field.pdf", "fig_coef_err.pdf", "fig_gate_null.pdf", "fig_resolution.pdf"):
        p = OUTDIR / f
        assert p.exists() and p.stat().st_size > 5_000, f"{f} mancante/vuota"
        print(f"scritta {p} ({p.stat().st_size / 1024:.0f} KB)")
