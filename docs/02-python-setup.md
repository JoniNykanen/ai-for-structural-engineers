# 02 — Set up Python (the calculation engine)

*Goal: have Python + the math libraries ready so Claude can run real
calculations. ~10 minutes. No MATLAB needed.*

Python is free and is the engine that makes all of this work even without a
MATLAB license. You install it once.

## Step 1 — Install Python

Check if you already have it:
```bash
python --version
```
If it prints `Python 3.10` or newer, skip to Step 2.

Otherwise:
- **Windows:** install from https://www.python.org/downloads/ — **tick
  "Add python.exe to PATH"** on the first screen of the installer.
- **macOS:** `brew install python` (or download from python.org).
- **Linux:** `sudo apt install python3 python3-pip python3-venv`.

## Step 2 — Create a virtual environment (keeps things tidy)

From inside the `matlab-claude-for-engineers` folder:

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

You'll see `(.venv)` at the start of your prompt when it's active.

> If PowerShell blocks the activate script, run once:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## Step 3 — Install the math libraries

```bash
pip install -r requirements.txt
```

This installs:
- **NumPy** — arrays and numeric linear algebra (stress tensors, eigenvalues)
- **SciPy** — solvers, optimization, integration
- **SymPy** — *symbolic* math (derive formulas, exact algebra, calculus)
- **Matplotlib** — plots (stress–strain curves, yield surfaces)

## Step 4 — Test it

```bash
python -c "import numpy, scipy, sympy, matplotlib; print('All good!')"
```

If it prints `All good!`, you're ready.

## Step 5 — Let Claude use it

Start Claude in this folder and ask:
```
Run the example examples/plasticity/von_mises_yield_check.py and explain the output.
```
Claude will execute it and walk you through the result.

> **Tip:** whenever you start a new terminal, re-activate the environment
> (Step 2's activate line) before running things, so Claude uses the libraries
> you installed.

## Next step

You can now do real work with **no MATLAB** →
[docs/05 — The no-license Python/SymPy path](05-python-sympy-fallback.md)

Or add MATLAB → [docs/03 — MATLAB Engine API](03-connect-matlab-engine-api.md)
