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
    diag = json.loads((ART / "cde_risoluzione_claim_out" / "diagnostica_proiezione_2026-09-07.json").read_text())
    d4 = json.loads((ART / "cde_blind4_out" / "claim_dettaglio.json").read_text())["claim"]
    d5 = json.loads((ART / "cde_blind5_out" / "claim_dettaglio.json").read_text())["claim"]
    vero = [d["vero"] for d in diag]; h1 = [d["h1"] for d in diag]; p1 = [d["p1"] for d in diag]
    nh = sum(v >= b for v, b in zip(vero, h1)); npj = sum(v >= b for v, b in zip(vero, p1))
    assert nh > 0 and npj == 0
    s4 = [r for r in d4 if r["mancanti"]]
    x4 = [r["alpha_gamma_vero"] for r in s4]; y4 = [r["c_min_div_vv_x"] for r in s4]
    s5 = [(o["c_vero"], o["c_min_v2"]) for r in d5 for o in r["mancanti"].values()]
    x5 = [a for a, _ in s5]; y5 = [b for _, b in s5]
    assert all(a < b for a, b in zip(x4, y4)) and all(a < b for a, b in zip(x5, y5))

    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.7), constrained_layout=True)
    for ax, (xs, ys, labels, title) in zip(axes, [
            ([vero, vero], [h1, p1],
             [f"unprojected $\\|r\\|/\\|a_t\\|$, $k=1$ ({nh} violations)",
              "projected $\\|r\\|/\\|\\tilde{a}_t\\|$, $k=1$ (0)"],
             f"(a) diagnostic, {len(diag)} sub-support claims (open truth)"),
            ([x4, x5], [y4, y5],
             [f"sealed panel 1, unprojected $k=2$ ({len(x4)})",
              f"sealed panel 2, projected $k=1$ ({len(x5)})"],
             "(b) two sealed panels, scored blind")]):
        lo = min(min(x) for x in xs) * 0.55; hi = max(max(y) for y in ys) * 3.2
        # violation is |c_t| >= c_min, i.e. BELOW the diagonal
        ax.fill_between([lo, hi], [lo, lo], [lo, hi], color="#d62728", alpha=0.07, lw=0)
        ax.plot([lo, hi], [lo, hi], "-", color="0.35", lw=0.8)
        ax.plot(xs[0], ys[0], "s", ms=4.2, mfc="none", mec="#ff7f0e", mew=1.0, label=labels[0])
        ax.plot(xs[1], ys[1], "o", ms=4.2, color="#1f77b4", mew=0, label=labels[1])
        ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
        ax.set_xlabel(r"true coefficient $|c_t|$ of the missing term")
        ax.set_ylabel(r"declared bound $c_{\min}(t)$")
        ax.set_title(title)
        ax.legend(frameon=False, loc="upper left", handletextpad=0.3, borderpad=0.2)
    axes[0].text(0.96, 0.08, "violation: $|c_t| \\geq c_{\\min}$", fontsize=7, color="#a00000",
                 ha="right", transform=axes[0].transAxes)
    for ax in axes:      # sanity: sound points must sit ABOVE the diagonal
        pass
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
