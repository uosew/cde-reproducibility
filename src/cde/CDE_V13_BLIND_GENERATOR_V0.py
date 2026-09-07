"""CDE V13 — generatore della campagna cieca su larga scala.

Preregistrazione: PREREGISTRAZIONE_CDE_V13_REPLICA_LARGA_SCALA_2026_08_02.md

Il generatore V11 e' cablato su 90 casi (9 classi x 10) e semi `5000 + k`.
Questo lo parametrizza su numero di casi e base dei semi, **riusando le sue
funzioni invece di reimplementarle**: `draw_model`, `simulate`, `sample_camera`
e la degradazione `degrade_twin` sono importate, non ricopiate. Una
reimplementazione, per quanto fedele, introdurrebbe fra le due campagne una
differenza che poi non sarebbe piu' possibile escludere come causa.

I semi stanno su basi diverse da quelle della V11, cosi' che i casi siano
genuinamente nuovi e non gli stessi modelli rietichettati.

Cecita': la verita' finisce in `sealed/truth.json` e non va letta finche'
entrambi i nodi non hanno prodotto tutti i verdetti.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
ART = BASE.parent.parent / "artifacts"      # public layout (cde-reproducibility)
PAPER = BASE.parent.parent / "paper"
JUL = BASE.parent.parent / "baselines" / "julia"
ROOT = BASE.parent
OUT = ART / "cde_v13_blind_out"
CASES = OUT / "cases"
SEALED = OUT / "sealed"
PREREG = "PREREGISTRAZIONE_CDE_V13_REPLICA_LARGA_SCALA_2026_08_02.md"

RGB_spec = importlib.util.spec_from_file_location(
    "runtime_guard_bootstrap", BASE / "runtime_guard_bootstrap.py")
RGB = importlib.util.module_from_spec(RGB_spec)
RGB_spec.loader.exec_module(RGB)

import numpy as np                                    # noqa: E402


def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, BASE / fname)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


G11 = _load("gen11", "CDE_V11_BLIND_GENERATOR_V0.py")
Q = G11.Q

# Basi dei semi, dichiarate nel ledger PRIMA della generazione. Diverse da
# quelle della V11 (5000+k, 300+i, 9000+k*10+i) perche' i casi devono essere
# nuovi, non gli stessi modelli con un altro nome.
SEME_MODELLO = 700_000
SEME_DEGRADO = 710_000
SEME_NULLO = 900_000


def _git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True,
                              timeout=20).stdout.strip()[:12]
    except Exception:
        return "sconosciuto"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-classe", type=int, default=67,
                    help="casi per classe; 67 x 9 classi = 603 casi")
    args = ap.parse_args()

    t0 = time.time()
    for d in (OUT, CASES, SEALED):
        d.mkdir(exist_ok=True)
    guard = RGB.enforce_runtime_guard(strict=True)
    print(f"runtime guard: {guard.get('status')}  "
          f"({guard.get('python_version')}, numpy {guard.get('numpy_version')})")

    n_per = args.per_classe
    truth, public = {}, {}
    k = 0
    for cls in G11.CLASSES:
        for _ in range(n_per):
            case_id = f"case_{k:03d}"
            rng = np.random.default_rng(SEME_MODELLO + k)
            m, sup = G11.draw_model(cls, rng)
            cam = G11.sample_camera(rng)
            arrays = {}
            for i, ic in enumerate(G11.ICS_BASE):
                x, t, V = G11.simulate(m, ic)
                xp, tp, Vd = Q.degrade_twin(x, t, V, cam,
                                            seed=SEME_DEGRADO + k * 10 + i)
                if cls == "H":
                    nrng = np.random.default_rng(SEME_NULLO + k * 10 + i)
                    kind = "shuffle_t" if k % 2 == 0 else "phase_surrogate"
                    Vd = Q.R.V8.null_field(Vd, kind, nrng)
                arrays[f"V{i}"] = Vd.astype(np.float16)
            arrays["x"] = xp.astype(np.float32)
            arrays["t"] = tp.astype(np.float32)
            np.savez_compressed(CASES / f"{case_id}.npz", **arrays)
            public[case_id] = {"px": cam["px"], "hz": cam["hz"], "camera": cam}
            truth[case_id] = {"cls": cls,
                              "representable": sup not in (None, "NULL"),
                              "is_null": sup == "NULL",
                              "true_support": (sup if isinstance(sup, list)
                                               else None),
                              "model": m}
            k += 1
        print(f"   classe {cls}: {n_per} casi  ({time.time() - t0:.0f}s, "
              f"totale {k})", flush=True)

    (OUT / "public_meta.json").write_text(json.dumps(public, indent=1))
    (SEALED / "truth.json").write_text(json.dumps(truth, indent=1))

    manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(CASES.glob("*.npz"))}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1))

    # Composizione: e' informazione pubblica sulla popolazione, non la verita'
    # dei singoli casi, quindi si puo' guardare senza rompere la cecita'.
    rap = sum(1 for v in truth.values() if v["representable"] and not v["is_null"])
    nul = sum(1 for v in truth.values() if v["is_null"])
    env = {"run": "CDE_V13_BLIND_GENERATOR_V0", "prereg": PREREG,
           "generato": datetime.now(timezone.utc).isoformat(),
           "commit": _git_commit(), "runtime_guard": guard,
           "casi": k, "per_classe": n_per, "classi": list(G11.CLASSES),
           "semi": {"modello": SEME_MODELLO, "degrado": SEME_DEGRADO,
                    "nullo": SEME_NULLO},
           "composizione": {"rappresentabili": rap, "nulli": nul,
                            "non_rappresentabili": k - rap - nul},
           "avvertenza": ("La verita' e' sigillata in sealed/truth.json e non "
                          "va letta finche' entrambi i nodi non hanno prodotto "
                          "tutti i verdetti.")}
    (OUT / "generation_envelope.json").write_text(
        json.dumps(env, indent=1, default=str))

    print(f"\n{k} casi generati in {time.time() - t0:.0f}s")
    print(f"composizione: {rap} rappresentabili, {nul} nulli, "
          f"{k - rap - nul} non rappresentabili")
    print(f"artefatti in {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
