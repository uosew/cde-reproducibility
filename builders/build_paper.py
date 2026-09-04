#!/usr/bin/env python3
"""Regenerate paper/main.tex from artifacts/ (runs every claim assertion first)."""
import runpy
from _common import SRC
runpy.run_path(str(SRC / "build_research_note_v0.py"), run_name="__main__")
runpy.run_path(str(SRC / "build_research_note_latex_v0.py"), run_name="__main__")
