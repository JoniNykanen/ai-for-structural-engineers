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

## Before you start (checklist)

- [ ] **A paid Claude plan** (Pro or Max) or API credits. See [docs/01](docs/01-install-claude-code.md#step-3--sign-in).
- [ ] **Git**, to download the repo. No Git? Use the green **Code → Download ZIP** button on GitHub and unzip it.
- [ ] **Python 3.x** ([docs/02](docs/02-python-setup.md)).
- [ ] **Node.js**, used by the setup script to install one optional skill. The setup still works without it; that step is just skipped.
- [ ] **Windows only:** if PowerShell refuses to run `setup.ps1` ("running scripts is disabled"), allow it for this window only:
  `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then run `./setup.ps1` again.
- [ ] **MATLAB is optional.** Everything in the quickstart works without it.

> **Privacy note:** a hook saves every session's questions and answers **locally** to `solved/`. They are only pushed to GitHub if you opt in to auto-push. To turn capture off completely, create an empty file `.claude/capture.disabled`. Details: [docs/09](docs/09-how-this-repo-learns.md).

---

## Quickstart (about 15 minutes, no MATLAB)

1. **Install Claude Code and sign in** → [docs/01](docs/01-install-claude-code.md)
2. **Get this repo** (`git clone …` or Download ZIP), open a terminal in the folder, and run
   **`./setup.ps1`** (Windows) or **`bash setup.sh`** (macOS/Linux). It creates the Python
   environment and quietly skips anything you don't have, such as MATLAB.
   *(Prefer to do it by hand? → [docs/02](docs/02-python-setup.md).)*
3. **Start Claude in the repo folder:** type `claude`.
4. **Ask your first question:**
   > *"σx = 180, σy = 60, τxy = 40 MPa, yield strength 250 MPa. Is it yielding by von Mises? Run it in Python, show the working, and check the result with a limit case."*

That's your first win. Next, read [docs/07 — how to prompt](docs/07-how-to-prompt-claude.md) and [docs/15 — how to check an AI calculation](docs/15-verify-ai-results.md).
New to all of this? [docs/00 — What is this?](docs/00-what-is-this.md) explains the big picture in 5 minutes.

### Optional extras (add when you need them)

- **MATLAB via the Engine API** — let Claude drive your own MATLAB from Python → [docs/03](docs/03-connect-matlab-engine-api.md)
- **MATLAB MCP server** — Claude calls MATLAB directly as a tool → [docs/04](docs/04-connect-matlab-mcp.md)
- **More Python/SymPy examples** without a license → [docs/05](docs/05-python-sympy-fallback.md)
- **Skills and plugins** — what each installed skill does, plus vetted add-ons → [docs/08](docs/08-recommended-add-ons.md)
- **Session capture and auto-push** — how the repo learns from use; `./setup.ps1 -EnableAutoPush` / `bash setup.sh --autopush` turns on pushing → [docs/09](docs/09-how-this-repo-learns.md)
- **Eurocode + Finnish NA calcs (eurocode-fi)** — cited, checkable timber design → [docs/11](docs/11-eurocode-fi.md)
- **Finnish reference tools (Puuinfo etc.)** — free tools for cross-checking → [docs/12](docs/12-suomalaiset-referenssityokalut.md)
- **Autodesk Robot Structural Analysis** — *experimental; the Robot MCP is field-tested on Robot 2027, with known gaps* → [docs/10](docs/10-connect-robot-structural.md) (Product Help MCP + COM) and [docs/14](docs/14-robot-mcp.md) (Robot MCP)

### All docs

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
[16 Academic integrity](docs/16-academic-integrity.md)

---

## Worked examples (theory of plasticity)

Ready-to-run code in [`examples/`](examples/):

- **von Mises yield check** — [Python](examples/plasticity/von_mises_yield_check.py) · [MATLAB](examples/plasticity/von_mises_yield_check.m)
- **Ramberg–Osgood stress–strain curve** — [Python](examples/plasticity/stress_strain_ramberg_osgood.py)
- **Plastic hinge / collapse load of a beam** — [MATLAB](examples/plasticity/plastic_hinge_beam.m)
- **Symbolic derivation of the von Mises function** — [SymPy](examples/sympy/symbolic_yield_derivation.py)
- **Calling MATLAB from Python** — [Engine API demo](examples/engine_api/call_matlab_from_python.py)

---

## Skills and plugins

The setup script installs a small set of skills and MATLAB plugins. What each one does, and when it fires, is listed in
[docs/08 — What each installed skill does](docs/08-recommended-add-ons.md#what-each-installed-skill-does).

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

AI can be confidently wrong. This repo is built around a rule: **Claude shows its working and runs the numbers so you can check them.** A computed answer you can reproduce beats a plausible answer you can't. Always sanity-check against your textbook — the goal is to *learn faster*, not to outsource your understanding. See [docs/15 — How to check an AI calculation](docs/15-verify-ai-results.md) and [docs/16 — Using AI honestly in coursework](docs/16-academic-integrity.md).

## License

MIT — see [LICENSE](LICENSE). Use it, fork it, share the kit with your class. Your own `solved/` session data is a different matter: it stays private. If your fork is public, keep auto-push off and don't commit `solved/` (see [docs/09](docs/09-how-this-repo-learns.md)).
