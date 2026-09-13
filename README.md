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

1. **New to all of this?** Read [docs/00 — What is this?](docs/00-what-is-this.md) first (5 min).
2. **Install Claude Code** → [docs/01](docs/01-install-claude-code.md)
3. **Set up Python** (the calculation engine) → [docs/02](docs/02-python-setup.md)
4. **Run your first calculation** with the no-license Python path → [docs/05](docs/05-python-sympy-fallback.md)
5. **Add MATLAB** when you're ready → [docs/03](docs/03-connect-matlab-engine-api.md) or [docs/04](docs/04-connect-matlab-mcp.md)
6. **Learn to prompt well** → [docs/07 — How to ask Claude for engineering calcs](docs/07-how-to-prompt-claude.md)
7. **Supercharge it** → [docs/08 — Recommended add-ons (vetted skills & tools)](docs/08-recommended-add-ons.md)

---

## Worked examples (theory of plasticity)

Ready-to-run code in [`examples/`](examples/):

- **von Mises yield check** — [Python](examples/plasticity/von_mises_yield_check.py) · [MATLAB](examples/plasticity/von_mises_yield_check.m)
- **Ramberg–Osgood stress–strain curve** — [Python](examples/plasticity/stress_strain_ramberg_osgood.py)
- **Plastic hinge / collapse load of a beam** — [MATLAB](examples/plasticity/plastic_hinge_beam.m)
- **Symbolic derivation of the von Mises function** — [SymPy](examples/sympy/symbolic_yield_derivation.py)
- **Calling MATLAB from Python** — [Engine API demo](examples/engine_api/call_matlab_from_python.py)

---

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
