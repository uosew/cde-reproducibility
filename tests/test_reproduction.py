"""Re-score the sealed campaigns from the committed verdicts and truth; the numbers must equal the reports."""
import json, subprocess, sys
from _common import ROOT, load
A = ROOT / "artifacts"
def test_v13_rescored_from_verdicts_and_truth():
    U = load("CDE_V13_BLIND_UNBLINDING_V0.py"); d = A / "cde_v13_blind_out"
    vm = json.loads((d / "verdicts_mac.json").read_text()); vw = json.loads((d / "verdicts_win.json").read_text()); truth = json.loads((d / "sealed/truth.json").read_text())
    verd = dict(vw); verd.update(vm); a = U.domanda_A(truth, verd); b = U.domanda_B(vm, vw)
    rep = json.loads((d / "unblinding_report.json").read_text())
    assert (a["n_claim_false"], a["opportunita"], a["claim_corrette"]) == (rep["domanda_A"]["n_claim_false"], rep["domanda_A"]["opportunita"], rep["domanda_A"]["claim_corrette"])
    assert b["accordo_pieno"] and U.esito(a, b) == rep["esito"] == "CLAIM_FALSA_OSSERVATA"
def test_blind4_rescored_from_annotated_verdicts_and_truth():
    S = load("CDE_BLIND4_SCORER_V0.py"); d = A / "cde_blind4_out"
    ann = json.loads((d / "verdicts_annotati.json").read_text())["verdetti"]; truth = json.loads((d / "sealed/truth.json").read_text())
    det = {r["case"]: r for r in json.loads((d / "claim_dettaglio.json").read_text())["claim"]}
    orig = json.loads((d / "verdicts_mac.json").read_text())
    for c in ann: ann[c]["verdict_originale"] = orig[c]["verdict"]
    e = S.valuta(ann, truth, lambda c, t: det[c]["mancanti"][t])
    rep = json.loads((d / "scoring.json").read_text())["esito"]
    assert (e["n_claim"], e["sotto_supporto"], len(e["violazioni"]), e["verdetto"]) == (rep["n_claim"], rep["sotto_supporto"], 0, "CONFIRMED")
def test_paper_tex_regenerates_identically(tmp_path):
    committed = (ROOT / "paper/main.tex").read_text()
    subprocess.run([sys.executable, str(ROOT / "builders/build_paper.py")], check=True, capture_output=True)
    assert (ROOT / "paper/main.tex").read_text() == committed
def test_no_monorepo_dependency():
    forbidden = ("Desktop" + "/LB", "living" + "_brain", "LB" + "_LAB", "/Users" + "/")   # split so this file does not match itself
    scanned = list((ROOT / "src").rglob("*.py")) + list((ROOT / "builders").glob("*.py")) + [ROOT / "provenance/make_manifest.py"]
    hits = [str(p) for p in scanned if any(s in p.read_text() for s in forbidden)]
    assert not hits, hits
