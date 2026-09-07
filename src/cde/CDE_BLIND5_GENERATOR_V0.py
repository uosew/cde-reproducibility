#!/usr/bin/env python3
"""Blind-4 (prereg limite di risoluzione §4): 120 casi rappresentabili A,B,C,F x 30,
semi nuovi, verita' sigillata con sha256 nell'envelope (correzione E8-bis).
Riusa per importazione la fisica V11 (draw_model, simulate, sample_camera) tramite il
generatore V13, esattamente come faceva la V13."""
import hashlib, importlib.util, json, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
BASE = Path(__file__).resolve().parent
ART = BASE.parent.parent / "artifacts"      # public layout (cde-reproducibility)
PAPER = BASE.parent.parent / "paper"; OUT = ART / "cde_blind5_out"; CASES = OUT / "cases"; SEALED = OUT / "sealed"
def _L(n, f):
    s = importlib.util.spec_from_file_location(n, BASE / f); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
G13 = _L("g13", "CDE_V13_BLIND_GENERATOR_V0.py"); G11 = G13.G11
PREREG = "PREREGISTRAZIONE_BLIND5_LIMITE_PROIETTATO_2026-09-07.md"
CLASSI = "ABCF"; N_PER = 30; SEME_MODELLO = 740_000; SEME_DEGRADO = 750_000
def main():
    CASES.mkdir(parents=True, exist_ok=True); SEALED.mkdir(exist_ok=True); t0 = time.time()
    guard = G13.RGB.enforce_runtime_guard(strict=True)
    truth, public, k = {}, {}, 0
    for cls in CLASSI:
        for _ in range(N_PER):
            rng = np.random.default_rng(SEME_MODELLO + k)
            m, sup = G11.draw_model(cls, rng)
            cam = G11.sample_camera(rng)
            arrays = {}
            for i, ic in enumerate(G11.ICS_BASE):
                x, t, V = G11.simulate(m, ic)
                xp, tp, Vd = G13.Q.degrade_twin(x, t, V, cam, seed=SEME_DEGRADO + k * 10 + i)
                arrays[f"V{i}"] = Vd.astype(np.float16)
            arrays["x"] = xp.astype(np.float32); arrays["t"] = tp.astype(np.float32)
            cid = f"case_{k:03d}"
            np.savez_compressed(CASES / f"{cid}.npz", **arrays)
            public[cid] = {"px": cam["px"], "hz": cam["hz"], "camera": cam}
            truth[cid] = {"cls": cls, "representable": sup not in (None, "NULL"), "is_null": sup == "NULL",
                          "true_support": (sup if isinstance(sup, list) else None), "model": m}
            k += 1
            if k % 20 == 0: print(f"  {k} casi ({time.time()-t0:.0f}s)", flush=True)
    (OUT / "public_meta.json").write_text(json.dumps(public, indent=1, default=str))
    tp = SEALED / "truth.json"; tp.write_text(json.dumps(truth, indent=1, default=str))
    sha = hashlib.sha256(tp.read_bytes()).hexdigest(); (SEALED / "truth.sha256").write_text(sha + "\n")
    manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(CASES.glob("*.npz"))}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1))
    env = {"run": "CDE_BLIND5_GENERATOR_V0", "prereg": PREREG, "prereg_sha256": hashlib.sha256((BASE / PREREG).read_bytes()).hexdigest(),
           "generato": datetime.now(timezone.utc).isoformat(), "casi": k, "classi": CLASSI, "per_classe": N_PER,
           "semi": {"modello": SEME_MODELLO, "degrado": SEME_DEGRADO}, "truth_sha256": sha, "runtime_guard": guard,
           "avvertenza": "verita' sigillata: sha registrato qui e in sealed/truth.sha256; da committare PRIMA del discoverer"}
    (OUT / "generation_envelope.json").write_text(json.dumps(env, indent=1, default=str))
    print(f"\n{k} casi in {time.time()-t0:.0f}s\nsha256 truth.json: {sha}")
if __name__ == "__main__":
    main()
