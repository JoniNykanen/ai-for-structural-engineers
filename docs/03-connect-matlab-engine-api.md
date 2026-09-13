# 03 — Method 2: MATLAB Engine API for Python

*Goal: let Python (and therefore Claude Code) start MATLAB, run MATLAB code, and
read results back. This is the official MathWorks bridge and the most robust way
to connect the two. ~20 minutes. **Requires a MATLAB license.***

## The picture

```
Claude Code ──► Python script ──► import matlab.engine ──► MATLAB (running in background) ──► results back to Python ──► Claude explains
```

Claude Code already runs Python. Once the MATLAB Engine is installed, Claude can
write a tiny Python script that calls MATLAB functions and reads the answers.

## Prerequisites

- **MATLAB installed** (R2020b or newer recommended). Find your version: in
  MATLAB, run `version` or check *Help → About*.
- **Python** whose version is *supported by your MATLAB release*. Each MATLAB
  release supports specific Python versions — see MathWorks'
  "Versions of Python Compatible with MATLAB" page. As a rule, Python 3.9–3.12
  covers recent releases; if unsure, Python 3.11 is a safe bet.

## Step 1 — Install the engine (the easy way, R2023a+)

With your virtual environment active (from [docs/02](02-python-setup.md)):

```bash
python -m pip install matlabengine
```

**Important:** the package version must match your MATLAB release:

| MATLAB release | Install command |
|---|---|
| R2024b | `pip install matlabengine==24.2.*` |
| R2024a | `pip install matlabengine==24.1.*` |
| R2023b | `pip install matlabengine==23.2.*` |
| R2023a | `pip install matlabengine==23.1.*` |

If `pip install matlabengine` picks the wrong version, use the pinned command above.

## Step 1 (alternative) — Install from MATLAB itself (any release, incl. older)

Find your MATLAB root: in MATLAB run `matlabroot`. Then, in a terminal:

**Windows (PowerShell), example path:**
```powershell
cd "C:\Program Files\MATLAB\R2024b\extern\engines\python"
python setup.py install
```

**macOS / Linux:**
```bash
cd /usr/local/MATLAB/R2024b/extern/engines/python   # adjust to your matlabroot
python setup.py install
```

## Step 2 — Test the connection

Run the included demo:
```bash
python examples/engine_api/call_matlab_from_python.py
```
It starts MATLAB, computes `sqrt(2)` and a small matrix operation in MATLAB, and
prints the results. First launch is slow (MATLAB is booting) — that's normal.

Minimal version of what it does:
```python
import matlab.engine
eng = matlab.engine.start_matlab()      # boots MATLAB (takes a few seconds)
print(eng.sqrt(2.0))                      # -> 1.4142...
eng.eval("A = [1 2; 3 4]; d = det(A);", nargout=0)
print(eng.workspace['d'])                 # -> -2.0
eng.quit()
```

## Step 3 — Let Claude drive it

Start Claude in this repo and ask:
```
Using the MATLAB Engine, compute the principal stresses and von Mises stress for
sigma_x=180, sigma_y=60, tau_xy=40 MPa. Write the MATLAB, run it via matlab.engine,
and show me both the MATLAB code and the numeric result.
```
Claude will generate the `.m`/engine code, run it, and explain the output.

## Gotchas & fixes

- **`ModuleNotFoundError: No module named 'matlab'`** → the engine isn't
  installed in the *active* environment. Re-activate `.venv` and reinstall.
- **Version mismatch error** → the `matlabengine` pip version doesn't match your
  MATLAB release. Use the pinned version from the table.
- **Starts very slowly every call** → keep one engine alive
  (`eng = matlab.engine.start_matlab()`) and reuse it; don't start a new one per
  calculation. Or connect to an already-open MATLAB with
  `matlab.engine.connect_matlab()` after running `matlab.engine.shareEngine` in MATLAB.
- **No license / can't install?** Use the free path instead:
  [docs/05](05-python-sympy-fallback.md).

## Next step

→ [docs/04 — Method 3: MATLAB MCP server](04-connect-matlab-mcp.md) (more
AI-native, more setup), or jump to
[docs/07 — How to prompt Claude](07-how-to-prompt-claude.md).
