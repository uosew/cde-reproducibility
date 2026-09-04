#!/usr/bin/env python3
"""Regenerate paper/fig_*.pdf exclusively from artifacts/ (KS field regenerated from the frozen generator, seed 7)."""
import runpy
from _common import SRC
runpy.run_path(str(SRC / "build_note_figures_v0.py"), run_name="__main__")
