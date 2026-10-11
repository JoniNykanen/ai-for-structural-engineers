# 05 — Method 1: Free Python / SymPy path for engineering calculations (start here)

*Goal: do real symbolic and numeric engineering calculations with **zero MATLAB
license** — just Python. This is the fastest way to prove the whole workflow.*

If you did [docs/02](02-python-setup.md), you already have everything installed.
This page shows what you can now do.

## The two halves of Python math

| Library | What it's for | Plasticity example |
|---|---|---|
| **SymPy** | *Symbolic* — exact algebra, calculus, solving equations with letters | Derive the von Mises function; differentiate a yield surface for the flow rule |
| **NumPy / SciPy** | *Numeric* — fast numbers, matrices, solvers | Compute principal stresses (eigenvalues); solve a nonlinear return-mapping step |
| **Matplotlib** | Plots | Draw a stress–strain curve or a yield surface |

MATLAB does symbolic + numeric + plotting; **SymPy + NumPy + Matplotlib is the
free equivalent** for coursework-scale problems.

## Example A — Numeric yield check (NumPy)

Run:
```bash
python examples/plasticity/von_mises_yield_check.py
```
This builds the stress tensor, finds principal stresses via eigenvalues,
computes the von Mises equivalent stress, and reports the factor of safety.

## Example B — Symbolic derivation (SymPy)

Run:
```bash
python examples/sympy/symbolic_yield_derivation.py
```
This derives the von Mises equivalent stress *as a formula* from the deviatoric
stress tensor — the algebra done exactly, no rounding.

## Example C — A stress–strain curve (Matplotlib)

Run:
```bash
python examples/plasticity/stress_strain_ramberg_osgood.py
```
Generates and saves a Ramberg–Osgood elastic-plastic curve you can drop into a
lab report.

## Letting Claude do it for you

You rarely need to write this yourself. Start Claude in the repo and ask in
English:

```
For sigma = [[180, 40, 0],[40, 60, 0],[0, 0, 0]] MPa and yield 250 MPa:
compute principal stresses, the von Mises and Tresca equivalent stresses, and
both factors of safety. Show the working and plot the stress state on the
von Mises vs Tresca yield loci in principal-stress space.
```

Claude will write and run the Python, show each step, and produce the plot —
because [`CLAUDE.md`](../CLAUDE.md) tells it to always show working and run the
numbers.

## When you *do* need MATLAB

- Your course requires MATLAB-format code or `.m` submissions.
- You're using a Simulink/toolbox feature with no free equivalent.
- You want to check that a MATLAB answer and a Python answer agree.

Then add MATLAB with [docs/03](03-connect-matlab-engine-api.md). The
`matlab-symbolic-math` skill can also generate correct MATLAB Symbolic Math
Toolbox code for you to paste in, even before the engine is connected.

## Next step

→ [docs/07 — How to prompt Claude for engineering calcs](07-how-to-prompt-claude.md)
