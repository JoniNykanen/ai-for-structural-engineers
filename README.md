# AI for Structural Engineers — Claude Code for Eurocode, Revit, Robot and Python calculations

**Verified structural engineering calculations with an AI that actually runs the numbers — for structural engineers and engineering students.**

Claude Code is an AI assistant that runs in your terminal. It can read files, write code and **run real calculations**. This repo points it at structural engineering work: **Eurocode design in Python** (with the Finnish National Annex), **free frame analysis with PyNite**, **reading Revit models** and **driving Robot Structural Analysis** through MCP servers, and **plasticity / mechanics of materials** for students. MATLAB is supported but optional.

Every example shows its working and **checks its own result** — against a closed-form solution, a second method or the model's own geometry. AI can be confidently wrong; this kit is built so you can see when it is.

You do **not** need to be a programmer. If you can copy-paste a command, you can follow this.

---

## What you can do with it

| Task | How | Licence needed? | Guide |
|---|---|---|---|
| **Eurocode calculations in Python** (EN 1995 timber, Finnish NA) | `eurocode-fi` skill + worked examples | ❌ No | [docs/11](docs/11-eurocode-fi.md) |
| **Free structural analysis in Python** (beams, frames, FEM) | PyNite | ❌ No | [examples/frame](examples/frame/README.md) |
| **Read and check a Revit model with AI** | Autodesk Revit MCP + Python | Revit 2027 | [docs/17](docs/17-revit-mcp.md) |
| **Drive Robot Structural Analysis with AI** | Robot MCP | Robot | [docs/14](docs/14-robot-mcp.md) |
| **Plasticity and mechanics of materials** (von Mises, Tresca, plastic hinges) | Python / SymPy | ❌ No | [docs/05](docs/05-python-sympy-fallback.md) |
| **Verify an AI structural calculation** | Checks built into every example | ❌ No | [docs/15](docs/15-verify-ai-results.md) |
| **Use MATLAB with Claude** (optional) | Engine API or MATLAB MCP | MATLAB | [docs/03](docs/03-connect-matlab-engine-api.md), [docs/04](docs/04-connect-matlab-mcp.md) |

Ask in plain language, for example:

> *"Two-span continuous steel beam, 6 m spans, 10 kN/m. Give the support moment and deflection in Python and check them against the textbook formulas."*

> *"Read the steel beams from the open Revit model and check that their section properties match their geometry."*

> *"σx = 180, σy = 60, τxy = 40 MPa, fy = 250 MPa. Is it yielding by von Mises? Show the working."*

---

## Who it is for

### Structural engineers

- **Automate routine checks** with Python instead of spreadsheets: Eurocode timber design, beam and frame analysis.
- **Connect AI to your BIM and analysis software**: Revit (official Autodesk MCP) and Robot Structural Analysis.
- **Catch bad model data** before it reaches a calculation — see the [Revit section-data check](examples/revit/README.md), which found a Revit sample type with the wrong stiffness.
- **National parameters stay yours**: no Eurocode or SFS values ship with the repo; you fill them in `params/`.

### Engineering students

- **Check homework and coursework calculations** step by step — governing equation, substitution, result, check.
- **Learn plasticity and mechanics of materials** with runnable Python and MATLAB examples.
- **A free alternative to MATLAB** for most course calculations (Python, SymPy, NumPy, PyNite).
- **Use AI honestly in coursework** → [docs/16](docs/16-academic-integrity.md).

---

## Before you start (checklist)

- [ ] **A paid Claude plan** (Pro or Max) or API credits. See [docs/01](docs/01-install-claude-code.md#step-3--sign-in).
- [ ] **Git**, to download the repo. No Git? Use the green **Code → Download ZIP** button on GitHub and unzip it.
- [ ] **Python 3.x** ([docs/02](docs/02-python-setup.md)).
- [ ] **Node.js**, used by the setup script to install one optional skill. The setup still works without it; that step is just skipped.
- [ ] **Windows only:** if PowerShell refuses to run `setup.ps1` ("running scripts is disabled"), allow it for this window only:
  `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then run `./setup.ps1` again.
- [ ] **MATLAB, Revit and Robot are optional.** Everything in the quickstart works without them.

> **Privacy note:** a hook saves every session's questions and answers **locally** to `solved/`. They are only pushed to GitHub if you opt in to auto-push. To turn capture off completely, create an empty file `.claude/capture.disabled`. Details: [docs/09](docs/09-how-this-repo-learns.md).

---

## Quickstart (about 15 minutes, no licence)

1. **Install Claude Code and sign in** → [docs/01](docs/01-install-claude-code.md)
2. **Get this repo** (`git clone https://github.com/JoniNykanen/ai-for-structural-engineers.git` or Download ZIP), open a terminal in the folder, and run
   **`./setup.ps1`** (Windows) or **`bash setup.sh`** (macOS/Linux). It creates the Python
   environment and quietly skips anything you don't have, such as MATLAB, Revit or Robot.
   *(Prefer to do it by hand? → [docs/02](docs/02-python-setup.md).)*
3. **Start Claude in the repo folder:** type `claude`.
4. **Ask your first question:**
   > *"σx = 180, σy = 60, τxy = 40 MPa, yield strength 250 MPa. Is it yielding by von Mises? Run it in Python, show the working, and check the result with a limit case."*

That's your first win. Next, read [docs/07 — how to prompt](docs/07-how-to-prompt-claude.md) and [docs/15 — how to check an AI calculation](docs/15-verify-ai-results.md).
New to all of this? [docs/00 — What is this?](docs/00-what-is-this.md) explains the big picture in 5 minutes.

---

## Eurocode calculations in Python (Finnish National Annex)

The `eurocode-fi` module designs to EN 1990 / EN 1995 with Finnish NA values that **you** supply in `params/na_timber.yaml` — the code never invents a factor. Each calculation cites its clause, runs an independent cross-check and writes a Finnish calculation note.

- Glulam beam, ULS bending and shear + SLS deflection → [`examples/eurocode/timber`](examples/eurocode/timber/README.md)
- Curved glulam beam (mahapalkki) in MATLAB → [`examples/structural`](examples/structural/README.md)
- Free Finnish reference tools for cross-checking (Puuinfo) → [docs/12](docs/12-suomalaiset-referenssityokalut.md)

Full guide: [docs/11 — Eurocode + Finnish NA](docs/11-eurocode-fi.md).

## Free structural analysis in Python (PyNite)

[PyNite](https://github.com/JWock82/Pynite) is a free, MIT-licensed 3D frame FEM library. No MATLAB or Robot licence needed.

- Two-span continuous beam: reactions, bending moment and shear diagrams, deflection, self-checked against the closed-form solution → [`examples/frame`](examples/frame/README.md)

## Revit MCP setup (Revit 2027)

Autodesk's official **Revit Public MCP Server** lets Claude query an open Revit model — find structural framing, read lengths and section properties — and hand them to Python.

1. Autodesk Account → *Products and Services* → *Product Updates* → *Revit 2027* → *Add-ons* → install **Revit 2027 MCP Server Write-Tools** (or Read-Tools).
2. **Restart Revit** — the add-in loads only at start-up.
3. Run `./setup.ps1` (registers the edition you installed) and restart Claude Code in this folder; approve the `revit` server.
4. Open a model, close dialogs, stay in *Modify*, and ask: *"List the structural framing in the open Revit model."*

Field-tested on Revit 2027.3. Tools, units (Revit returns feet) and gotchas → [docs/17 — Revit MCP](docs/17-revit-mcp.md) · suomeksi: [Revit MCP – käyttöönotto](examples/revit/revit-mcp-kayttoonotto.md).

## Robot Structural Analysis with AI (Robot MCP)

A third-party MCP server lets Claude build a Robot model, run it and read results (35 tools). `./setup.ps1` installs it when Robot is detected. Field-tested on Robot 2027, with known gaps → [docs/14 — Robot MCP](docs/14-robot-mcp.md) · Python/COM route → [docs/10](docs/10-connect-robot-structural.md) · suomeksi: [Robot MCP – käyttöönotto](examples/robot/robot-mcp-kayttoonotto.md).

## Plasticity and mechanics of materials examples

Ready-to-run code for theory of plasticity and strength of materials courses:

- **von Mises and Tresca yield check** — [Python](examples/plasticity/von_mises_yield_check.py) · [MATLAB](examples/plasticity/von_mises_yield_check.m)
- **Ramberg–Osgood stress–strain curve** — [Python](examples/plasticity/stress_strain_ramberg_osgood.py)
- **Plastic hinge / collapse load of a beam** — [MATLAB](examples/plasticity/plastic_hinge_beam.m)
- **Symbolic derivation of the von Mises function** — [SymPy](examples/sympy/symbolic_yield_derivation.py)

## MATLAB with Claude Code (optional)

| Method | Needs a MATLAB licence? | Best for | Guide |
|---|---|---|---|
| **1. Python + SymPy/NumPy** | ❌ No | Everyone. Start here. | [docs/05](docs/05-python-sympy-fallback.md) |
| **2. MATLAB Engine API for Python** | ✅ Yes | You have MATLAB and want Claude to drive it. | [docs/03](docs/03-connect-matlab-engine-api.md) |
| **3. MATLAB MCP server** | ✅ Yes | Claude calls MATLAB directly as a tool. | [docs/04](docs/04-connect-matlab-mcp.md) |

Demo: [calling MATLAB from Python](examples/engine_api/call_matlab_from_python.py).

## How every AI calculation is verified

Each example runs at least one independent check and says whether it passed: a closed-form solution (e.g. qL²/8), a limit case (pure shear → σ_vm = √3·τ), a units check, or a second method. Tests run in CI on every push. How to check any AI answer yourself → [docs/15](docs/15-verify-ai-results.md).

---

## All docs

[00 What is this?](docs/00-what-is-this.md) ·
[01 Install Claude Code](docs/01-install-claude-code.md) ·
[02 Python setup](docs/02-python-setup.md) ·
[03 MATLAB Engine API](docs/03-connect-matlab-engine-api.md) ·
[04 MATLAB MCP](docs/04-connect-matlab-mcp.md) ·
[05 Python/SymPy path](docs/05-python-sympy-fallback.md) ·
[06 Troubleshooting](docs/06-troubleshooting.md) ·
[07 How to prompt](docs/07-how-to-prompt-claude.md) ·
[08 Add-ons, skills & plugins](docs/08-recommended-add-ons.md) ·
[09 How this repo learns](docs/09-how-this-repo-learns.md) ·
[10 Robot Structural Analysis](docs/10-connect-robot-structural.md) ·
[11 eurocode-fi](docs/11-eurocode-fi.md) ·
[12 Suomalaiset referenssityökalut](docs/12-suomalaiset-referenssityokalut.md) ·
[14 Robot MCP](docs/14-robot-mcp.md) ·
[15 Verify AI results](docs/15-verify-ai-results.md) ·
[16 Academic integrity](docs/16-academic-integrity.md) ·
[17 Revit MCP](docs/17-revit-mcp.md)

## Skills and plugins

The setup script installs a small set of skills and MATLAB plugins. What each one does, and when it fires, is listed in
[docs/08 — What each installed skill does](docs/08-recommended-add-ons.md#what-each-installed-skill-does).

## Repo map

```
ai-for-structural-engineers/
├── README.md              ← you are here
├── CLAUDE.md              ← makes Claude show its working and check every result
├── requirements.txt       ← Python packages (NumPy, SciPy, SymPy, PyNite …)
├── .mcp.json              ← MCP servers: Robot, Revit
├── params/                ← your national-annex values (not shipped)
├── docs/                  ← step-by-step guides, numbered in reading order
├── examples/              ← eurocode, frame (PyNite), revit, robot, plasticity, sympy, MATLAB
└── tests/                 ← self-checks, run in CI
```

---

## A note on honesty

AI can be confidently wrong. This repo is built around a rule: **Claude shows its working and runs the numbers so you can check them.** A computed answer you can reproduce beats a plausible answer you can't. The same goes for input data: a BIM model can be wrong too. Always sanity-check against your textbook, the code and your own judgement — the goal is to *work and learn faster*, not to outsource responsibility. See [docs/15 — How to check an AI calculation](docs/15-verify-ai-results.md) and [docs/16 — Using AI honestly in coursework](docs/16-academic-integrity.md).

## License

- **Code** (examples, scripts, hooks, setup scripts, Claude skills): [Apache License 2.0](LICENSE)
- **Documentation** (README, CHANGELOG, `docs/`): [CC BY 4.0](LICENSE-docs). Reuse and adapt it freely, including commercially, as long as you credit *Joni Nykänen — ai-for-structural-engineers*.

Keep the [NOTICE](NOTICE) file in forks. The project names are not licensed as trademarks. No Eurocode or SFS values ship with this repo: you supply them in `params/na_timber.yaml`. MATLAB, Revit, Robot Structural Analysis and Claude are trademarks of their owners; this project is not affiliated with them.

Use it, fork it, share the kit with your class or office. Your own `solved/` session data is a different matter: it stays private. If your fork is public, keep auto-push off and don't commit `solved/` (see [docs/09](docs/09-how-this-repo-learns.md)).
