# Plasticity examples

Worked, runnable examples from the theory of plasticity. Each has a Python
version (no MATLAB license needed) and/or a MATLAB version.

| File | What it does | Needs MATLAB? |
|---|---|---|
| `von_mises_yield_check.py` | Principal stresses, von Mises + Tresca equivalent stress, factor of safety | ❌ |
| `von_mises_yield_check.m` | Same, in MATLAB | ✅ |
| `stress_strain_ramberg_osgood.py` | Plots an elastic-plastic stress–strain curve → `ramberg_osgood.png` | ❌ |
| `plastic_hinge_beam.m` | Collapse loads via plastic-hinge limit analysis (3 classic cases) | ✅ |

## Run the Python ones

```bash
python von_mises_yield_check.py
python stress_strain_ramberg_osgood.py
```

## Run the MATLAB ones

In MATLAB, open the `.m` file and press Run — or ask Claude to run it through the
MATLAB Engine API / MCP server (see `docs/03` and `docs/04`).

## Or just ask Claude

From the repo root, start `claude` and describe the problem in English
(see `docs/07`). Claude will adapt these examples to your specific numbers, run
them, and explain each step.
