import importlib.util, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "cde"
def load(name):
    """Load a frozen module from src/cde by file name (the modules locate each other the same way)."""
    spec = importlib.util.spec_from_file_location(name.replace(".py", ""), SRC / name)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
