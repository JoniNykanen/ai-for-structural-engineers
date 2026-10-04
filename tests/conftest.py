"""Shared pytest setup: make the repo root and example folders importable."""
import os
import sys
from pathlib import Path

# Headless plotting (no window, works in CI).
os.environ.setdefault("MPLBACKEND", "Agg")

REPO_ROOT = Path(__file__).resolve().parents[1]

for path in (REPO_ROOT,
             REPO_ROOT / "examples" / "plasticity",
             REPO_ROOT / "examples" / "sympy"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
