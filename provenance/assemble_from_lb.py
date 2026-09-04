"""Assembla ~/Desktop/cde-reproducibility dal monorepo LB: sottoinsieme congelato."""
import re, json, shutil, hashlib, subprocess
from pathlib import Path
LB = Path.home() / "Desktop/LB"; CDE = LB / "CDE_Scientific_Discovery"; R = Path.home() / "Desktop/cde-reproducibility"
SRC = R / "src/cde"; ART = R / "artifacts"; PROT = R / "blind/protocols"; PAPER = R / "paper"
for d in (SRC, ART, PROT, PAPER, R / "builders", R / "tests", R / "provenance"): d.mkdir(parents=True, exist_ok=True)
radici = ["build_research_note_v0.py","build_research_note_latex_v0.py","build_note_figures_v0.py",
  "CDE_V13_BLIND_UNBLINDING_V0.py","CDE_V11_BLIND_UNBLINDING_V1.py","CDE_BLIND4_SCORER_V0.py","CDE_BLIND_PDE2_SCORER_V0.py",
  "CDE_RISOLUZIONE_ANALYZER_V0.py","CDE_RISOLUZIONE_CLAIM_V0.py","CDE_RISOLUZIONE_STAGE1_V0.py",
  "CDE_PDE_PIPELINE_GATED_V1_1.py","CDE_PIPELINE_REPLAY_BLIND2_V1_1.py","CDE_PIPELINE_REPLAY_BLIND2_V0.py",
  "CDE_V11_BLIND_GENERATOR_V0.py","CDE_V13_BLIND_GENERATOR_V0.py","CDE_BLIND4_GENERATOR_V0.py","CDE_BLIND_PDE2_GENERATOR_V0.py",
  "CDE_BLIND4_RUNNER_V0.py","CDE_BLIND_PDE2_RUNNER_V0.py","CDE_BLIND_PDE_RUNNER_V0.py","CDE_V13_BLIND_DISCOVERER_V0.py",
  "CDE_V8_AVVERSARIALE_V0.py","CDE_V10_CAPABILITY_MATRIX_V0.py"]
pat_code = re.compile(r'(?:BASE|ROOT|_REPO_ROOT)\s*/\s*(?:"CDE_Scientific_Discovery"\s*/\s*)?"([A-Za-z0-9_./]+\.py)"|_load\w*\(\s*"[^"]+"\s*,\s*"([A-Za-z0-9_./]+\.py)"\)|_L\(\s*"[^"]+"\s*,\s*"([A-Za-z0-9_./]+\.py)"\)|_load_module\(\s*"[^"]+"\s*,\s*(?:BASE|ROOT)\s*/\s*"([A-Za-z0-9_./]+\.py)"')
pat_art = re.compile(r'"((?:cde_|arxiv_note|NUMPY_ELISION|RESEARCH_NOTE)[A-Za-z0-9_./\-]*)"')
codice, art, visti, coda = {}, set(), set(), list(radici)
while coda:
    f = coda.pop()
    if f in visti: continue
    visti.add(f); p = CDE / f if (CDE / f).exists() else LB / f
    if not p.exists(): print("  ?? non trovato:", f); continue
    s = p.read_text(errors="ignore"); codice[f] = p
    for m in pat_code.finditer(s): coda.append([x for x in m.groups() if x][0])
    for m in pat_art.finditer(s): art.add(m.group(1).split("/")[0])
# copia codice, con patch dei percorsi
prov = {"codice": {}, "artefatti": {}}
head = subprocess.check_output(["git","rev-parse","--short","HEAD"], cwd=LB, text=True).strip()
for f, p in sorted(codice.items()):
    s = p.read_text(); orig = hashlib.sha256(p.read_bytes()).hexdigest()
    s2 = s
    s2 = re.sub(r'(BASE|OUT|OUTDIR)\s*/\s*"(cde_[A-Za-z0-9_]*_out[A-Za-z0-9_/.\-]*)"', r'ART / "\2"', s2)
    s2 = re.sub(r'BASE\s*/\s*"(cde_pde_discovery_v8_multiseed|cde_v8_avversariale_v0|cde_ks_discovery_v9_multiseed)([A-Za-z0-9_/.\-]*)"', r'ART / "\1\2"', s2)
    s2 = s2.replace("return json.loads((BASE / p).read_text())", "return json.loads((ART / p).read_text())")
    s2 = s2.replace("    p = BASE / path\n", "    p = ART / path\n").replace("    p = BASE / rel\n", "    p = ART / rel\n")
    s2 = s2.replace('(BASE / "CDE_V10_CAPABILITY_MATRIX.md")', '(ART / "CDE_V10_CAPABILITY_MATRIX.md")')
    s2 = s2.replace('f"usare .venv313 o .venv312 in Desktop/LB.")', 'f"use a supported interpreter (see requirements-lock.txt).")')
    s2 = s2.replace('ROOT / "NUMPY_ELISION_REPOSITORY_AUDIT_2026_07_28.json"', 'ART / "NUMPY_ELISION_REPOSITORY_AUDIT_2026_07_28.json"')
    s2 = s2.replace('BASE / "RESEARCH_NOTE_WEAKFORM_DISCOVERY_2026_07_29.md"', 'PAPER / "RESEARCH_NOTE_WEAKFORM_DISCOVERY_2026_07_29.md"')
    s2 = re.sub(r'OUTDIR = BASE / "arxiv_note"', 'OUTDIR = PAPER', s2)
    s2 = s2.replace('ROOT / "runtime_guard_bootstrap.py"', 'BASE / "runtime_guard_bootstrap.py"')
    s2 = s2.replace('_REPO_ROOT / "CDE_Scientific_Discovery" / "numpy_guard.py"', '_REPO_ROOT / "numpy_guard.py"')
    s2 = re.sub(r'(BASE = Path\(__file__\)\.resolve\(\)\.parent\n)', r'\1ART = BASE.parent.parent / "artifacts"      # public layout (cde-reproducibility)\nPAPER = BASE.parent.parent / "paper"\n', s2, count=1)
    if "ART = " not in s2 and ("ART /" in s2 or "PAPER" in s2):
        s2 = s2.replace("BASE = Path(__file__).resolve().parent", 'BASE = Path(__file__).resolve().parent\nART = BASE.parent.parent / "artifacts"      # public layout (cde-reproducibility)\nPAPER = BASE.parent.parent / "paper"', 1)
    (SRC / f).write_text(s2)
    prov["codice"][f] = {"lb_path": str(p.relative_to(LB)), "sha256_originale": orig, "sha256_pubblico": hashlib.sha256(s2.encode()).hexdigest(), "patchato": s2 != s, "lb_commit": head}
# artefatti: solo json/md/txt/sha256/csv, mai npz
for d in sorted(art):
    src = CDE / d if (CDE / d).exists() else LB / d
    if not src.exists(): print("  ?? artefatto non trovato:", d); continue
    if src.is_file():
        shutil.copy2(src, ART / src.name); prov["artefatti"][src.name] = hashlib.sha256(src.read_bytes()).hexdigest(); continue
    if d == "arxiv_note": continue
    for f in src.rglob("*"):
        if f.is_file() and f.suffix in (".json", ".md", ".txt", ".sha256", ".csv", ".tex") and "__pycache__" not in f.parts and ".partial" not in f.name and "log" not in f.name:
            dest = ART / f.relative_to(CDE if src.is_relative_to(CDE) else LB); dest.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(f, dest)
            prov["artefatti"][str(dest.relative_to(ART))] = hashlib.sha256(f.read_bytes()).hexdigest()
# protocolli: preregistrazioni, semantica, claim card, audit, decisione
for f in list(CDE.glob("PREREGISTRA*.md")) + list(CDE.glob("PREREGISTRATION*.md")) + list(CDE.glob("CLAIM_CARD*.md")) + [CDE / "SEMANTICA_VERDETTI_CDE_2026-08-24.md", CDE / "AUDIT_PROCESSO_SCOPERTA_2026-09-02.md", CDE / "DECISIONE_CLAIM_BOUNDARY_RUMORE_10_2026-09-03.md", CDE / "REPORT_BLIND_PDE_2026-08-24.md", CDE / "REPORT_BLIND_PDE2_2026-08-24.md"]:
    if f.exists(): shutil.copy2(f, PROT / f.name)
# paper
for f in (CDE / "arxiv_note").glob("*"):
    if f.suffix in (".tex", ".pdf") and not f.name.startswith("main.") or f.name == "main.tex": shutil.copy2(f, PAPER / f.name)
shutil.copy2(CDE / "RESEARCH_NOTE_WEAKFORM_DISCOVERY_2026_07_29.md", PAPER / "RESEARCH_NOTE_WEAKFORM_DISCOVERY_2026_07_29.md") if (CDE / "RESEARCH_NOTE_WEAKFORM_DISCOVERY_2026_07_29.md").exists() else None
json.dump(prov, open(R / "provenance/EXTRACTION.json", "w"), indent=1)
print(f"codice: {len(codice)} file ({sum(v['patchato'] for v in prov['codice'].values())} patchati)  artefatti: {len(prov['artefatti'])} file  protocolli: {len(list(PROT.glob('*')))}")
print("dir artefatti:", sorted(set(k.split('/')[0] for k in prov['artefatti'])))
