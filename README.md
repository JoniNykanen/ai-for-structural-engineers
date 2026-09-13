# MATLAB + Claude for Engineers

**A beginner-friendly kit for engineering students who want an AI that can actually *do* the math.**

Claude Code is an AI assistant that runs in your terminal. It can read files, write code, and — crucially for us — **run real calculations**. This repo teaches you how to point that power at hard engineering problems (plasticity, stress analysis, dynamics, control systems) by connecting it to **MATLAB**, to **Python (SymPy/NumPy)**, or to both.

You do **not** need to be a programmer. If you can copy-paste a command and read English, you can follow this.

---

## What you'll be able to do

Ask, in plain English:

> *"A steel part has stresses σx = 180, σy = 60, τxy = 40 MPa. The yield strength is 250 MPa. Is it yielding by the von Mises criterion? Show the working and plot the yield surface."*

…and Claude will derive the formula, compute the number, tell you yes/no, and draw the plot — using MATLAB or Python underneath. No hand algebra, no silent black box: **you see every step.**

---

## The three ways to connect (pick what fits you)

| Method | Needs a MATLAB license? | Best for | Guide |
|---|---|---|---|
| **1. Python + SymPy/NumPy** | ❌ No | Everyone. Start here — it works out of the box with Claude Code. | [docs/05](docs/05-python-sympy-fallback.md) |
| **2. MATLAB Engine API for Python** | ✅ Yes | Students who already have MATLAB and want Claude to drive it. | [docs/03](docs/03-connect-matlab-engine-api.md) |
| **3. MATLAB MCP server** | ✅ Yes | Advanced: Claude calls MATLAB directly as a native tool. | [docs/04](docs/04-connect-matlab-mcp.md) |

**Not sure? Do Method 1 first.** It requires no license and proves the whole workflow. Add MATLAB later.

---

## Quickstart (15 minutes)

> **Fastest path:** install Claude Code ([docs/01](docs/01-install-claude-code.md))
> and Python ([docs/02](docs/02-python-setup.md)), then from the repo root run
> **`./setup.ps1`** (Windows) or **`bash setup.sh`** (macOS/Linux). It does the
> Python env, MATLAB Engine API, MATLAB MCP Server registration, skills, and
> plugins automatically. Add `-EnableAutoPush` / `--autopush` to also push
> captured sessions (see [docs/09](docs/09-how-this-repo-learns.md)). Then restart
> Claude Code. The manual steps below explain what the script does.

1. **New to all of this?** Read [docs/00 — What is this?](docs/00-what-is-this.md) first (5 min).
2. **Install Claude Code** → [docs/01](docs/01-install-claude-code.md)
3. **Set up Python** (the calculation engine) → [docs/02](docs/02-python-setup.md)
4. **Run your first calculation** with the no-license Python path → [docs/05](docs/05-python-sympy-fallback.md)
5. **Add MATLAB** when you're ready → [docs/03](docs/03-connect-matlab-engine-api.md) or [docs/04](docs/04-connect-matlab-mcp.md)
6. **Learn to prompt well** → [docs/07 — How to ask Claude for engineering calcs](docs/07-how-to-prompt-claude.md)
7. **Supercharge it** → [docs/08 — Recommended add-ons (vetted skills & tools)](docs/08-recommended-add-ons.md)
8. **Let it improve with use** → [docs/09 — How this repo learns from usage](docs/09-how-this-repo-learns.md)
9. **Structural engineering?** → [docs/10 — Autodesk Robot Structural Analysis + the Autodesk Product Help MCP](docs/10-connect-robot-structural.md)
10. **Code-compliant design (Eurocode + Finnish NA)?** → [docs/11 — eurocode-fi: cited, checkable calcs](docs/11-eurocode-fi.md)
11. **Cross-check against free Finnish tools** → [docs/12 — Puuinfo & co. reference/validation tools](docs/12-suomalaiset-referenssityokalut.md)
12. **(Optional) Read your own LinkedIn posts into Claude** → [docs/13 — LinkedIn MCP](docs/13-linkedin-mcp.md)

---

## Worked examples (theory of plasticity)

Ready-to-run code in [`examples/`](examples/):

- **von Mises yield check** — [Python](examples/plasticity/von_mises_yield_check.py) · [MATLAB](examples/plasticity/von_mises_yield_check.m)
- **Ramberg–Osgood stress–strain curve** — [Python](examples/plasticity/stress_strain_ramberg_osgood.py)
- **Plastic hinge / collapse load of a beam** — [MATLAB](examples/plasticity/plastic_hinge_beam.m)
- **Symbolic derivation of the von Mises function** — [SymPy](examples/sympy/symbolic_yield_derivation.py)
- **Calling MATLAB from Python** — [Engine API demo](examples/engine_api/call_matlab_from_python.py)

---

## What each installed skill does

"Skills" are curated instruction packs that teach Claude *how* to do a specific
kind of work. Claude loads one automatically when your request matches it (or you
can force one by name). Here's the set this kit uses and when each fires.

### General math / symbolic skills

| Skill | What it does | Best for (plasticity) |
|---|---|---|
| **`math`** | Unified math helper — routes your request to computation, equation-solving, or step-by-step explanation. The generalist. | Any calculation where you want the working shown: yield checks, factors of safety, solving equilibrium equations. |
| **`sympy-symbolic`** | Derives and solves equations **symbolically** using Python's SymPy. *Note: written with a fluid-dynamics/pump slant, so for pure plasticity the `math` skill is often the better generalist.* | Exact algebra with letters — e.g. deriving a yield function before plugging in numbers. |

### MATLAB-specific skills

| Skill | What it does | Best for (plasticity) |
|---|---|---|
| **`matlab-symbolic-math`** (MathWorks, *experimental*) | Generates correct **MATLAB Symbolic Math Toolbox** code: differentiation, integration, `solve`/`dsolve`, Laplace/Fourier transforms, and symbolic→numeric conversion. | Producing MATLAB code for a symbolic derivation (e.g. flow rule `∂f/∂σ`) you'll paste into MATLAB. **Needs the Symbolic Math Toolbox** (you have it). |
| **`matlab`** (K-Dense-AI) | Plans, builds, reviews, and migrates **MATLAB *or* GNU Octave** numerical workflows — arrays, tables, tests, graphics, MAT files, Python interop. Docs pinned to R2026a. | A second-opinion reviewer on MATLAB code, or a **free Octave** fallback if you're off your MATLAB license. |

### MATLAB Agentic Toolkit plugins (official MathWorks skill groups)

| Plugin | What it does | Best for (plasticity) |
|---|---|---|
| **`matlab-core`** | Teaches Claude to **create, debug, test, review, and manage** idiomatic MATLAB code without hallucinating functions. Required base group. | Everyday MATLAB: writing a clean stress-analysis script, debugging an error, adding tests. |
| **`math-and-optimization`** | Expertise for **Symbolic Math Toolbox**, Optimization Toolbox, and PDE Toolbox workflows. | Symbolic plasticity derivations done the MATLAB-idiomatic way; optimization/PDE work *if* you license those toolboxes later. |

> **Why only these?** Agents trigger skills more reliably when fewer are loaded,
> so this kit stays lean and plasticity-focused. Add more groups (e.g.
> `matlab-programming`, `control-systems`) anytime — see
> [docs/08](docs/08-recommended-add-ons.md).

> **Two things to remember:** (1) skills load at **session start** — restart
> Claude Code after installing. (2) Force any skill by name, e.g.
> `/matlab-write-tests`.

## Repo map

```
matlab-claude-for-engineers/
├── README.md              ← you are here
├── CLAUDE.md              ← makes Claude behave like a patient tutor in this repo
├── requirements.txt       ← Python packages
├── docs/                  ← step-by-step guides, numbered in reading order
└── examples/              ← runnable plasticity + connection examples
```

---

## A note on honesty

AI can be confidently wrong. This repo is built around a rule: **Claude shows its working and runs the numbers so you can check them.** A computed answer you can reproduce beats a plausible answer you can't. Always sanity-check against your textbook — the goal is to *learn faster*, not to outsource your understanding.

## License

MIT — see [LICENSE](LICENSE). Use it, fork it, share it with your class.
