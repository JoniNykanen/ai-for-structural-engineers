# 08 — Recommended add-ons (vetted)

*A curated shortlist of skills, MCP servers, and toolboxes worth adding — and
what to skip. Every recommendation here was cross-checked against primary
(mostly first-party MathWorks) sources; citations are at the bottom.*

> **How to read this:** ✅ = set up in this guide already · ⭐ = recommended
> next · 🟡 = optional · ❌ = skip.

---

## ✅ Core stack (already covered by this repo)

| Item | Where |
|---|---|
| **Official MATLAB MCP Server** (MathWorks) | [docs/04](04-connect-matlab-mcp.md) — the reputable, first-party MCP path |
| **MATLAB Engine API for Python** | [docs/03](03-connect-matlab-engine-api.md) |
| **Python / SymPy / NumPy** (no-license) | [docs/05](05-python-sympy-fallback.md) |
| `matlab-symbolic-math` skill (MathWorks, experimental) | generates Symbolic Math Toolbox code |

> ⚠️ **License note:** the `matlab-symbolic-math` skill needs the **Symbolic Math
> Toolbox**, which is licensed *separately* from base MATLAB — it is not bundled.
> Check what you have: ask your agent *"list installed toolboxes"* (the MCP
> `detect_matlab_toolboxes` tool), or run `ver` in MATLAB.

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
| **`matlab-symbolic-math`** (MathWorks, *experimental*) | Generates correct **MATLAB Symbolic Math Toolbox** code: differentiation, integration, `solve`/`dsolve`, Laplace/Fourier transforms, and symbolic→numeric conversion. | Producing MATLAB code for a symbolic derivation (e.g. flow rule `∂f/∂σ`) you'll paste into MATLAB. **Needs the Symbolic Math Toolbox** (see the license note above). |
| **`matlab`** (K-Dense-AI) | Plans, builds, reviews, and migrates **MATLAB *or* GNU Octave** numerical workflows — arrays, tables, tests, graphics, MAT files, Python interop. Docs pinned to R2026a. | A second-opinion reviewer on MATLAB code, or a **free Octave** fallback if you're off your MATLAB license. |

### MATLAB Agentic Toolkit plugins (official MathWorks skill groups)

| Plugin | What it does | Best for (plasticity) |
|---|---|---|
| **`matlab-core`** | Teaches Claude to **create, debug, test, review, and manage** idiomatic MATLAB code without hallucinating functions. Required base group. | Everyday MATLAB: writing a clean stress-analysis script, debugging an error, adding tests. |
| **`math-and-optimization`** | Expertise for **Symbolic Math Toolbox**, Optimization Toolbox, and PDE Toolbox workflows. | Symbolic plasticity derivations done the MATLAB-idiomatic way; optimization/PDE work *if* you license those toolboxes later. |

> **Why only these?** Agents trigger skills more reliably when fewer are loaded,
> so this kit stays lean and plasticity-focused. Add more groups (e.g.
> `matlab-programming`, `control-systems`) anytime — see the next section.

> **Two things to remember:** (1) skills load at **session start** — restart
> Claude Code after installing. (2) Force any skill by name, e.g.
> `/matlab-write-tests`.

---

## ⭐ MATLAB Agentic Toolkit — skill groups (recommended)

The **official MathWorks** [MATLAB Agentic Toolkit](https://github.com/matlab/matlab-agentic-toolkit)
gives your agent curated MATLAB expertise so it hallucinates fewer functions and
skips dead ends. Its skills ship as **Claude Code plugins** via a marketplace, so
you can add them *without* MATLAB-side installation, and they don't disturb an
MCP server you already set up.

```bash
# 1. Add the marketplace (once)
claude plugin marketplace add "https://github.com/matlab/matlab-agentic-toolkit"

# 2. Install the required core group + the math group (Symbolic Math Toolbox)
claude plugin install matlab-core@matlab-agentic-toolkit
claude plugin install math-and-optimization@matlab-agentic-toolkit
```

**Why these two:** `matlab-core` (create/debug/test/**review** code) is required;
`math-and-optimization` covers **Symbolic Math Toolbox** — your plasticity
workhorse — plus Optimization and PDE toolboxes if you ever license them.

> **Keep it lean.** Install *only* the groups you use — agents trigger skills
> more reliably when fewer are loaded. Add others later (e.g.
> `matlab-programming` for validated-input functions) the same way. Force a
> specific skill with its slash name, e.g. `/matlab-write-tests`.

Full group list: `aerospace`, `ai-and-statistics`, `control-systems`,
`signal-processing`, `image-processing-and-computer-vision`, … (26 total — see
the marketplace).

---

## 🟡 K-Dense-AI scientific-agent-skills — the `matlab` skill (optional)

A large community skill library (165 skills). Install **only the one MATLAB
skill**, not the whole set:

```bash
npx skills add "K-Dense-AI/scientific-agent-skills@matlab"
```

It plans/reviews MATLAB **or GNU Octave** numerical workflows and its docs are
pinned to **R2026a** + Octave 11.3. Useful as a supplementary reviewer,
especially if you want an **Octave** (free) fallback. *Caveat: rests on a single,
promotional source — treat as supplementary, not core.*

---

## ❌ Skip these (for a student setup)

| Item | Why skip |
|---|---|
| Community MCP servers (`Tsuchijo/matlab-mcp`, `jigarbhoye04/MatlabMCP`) | Low-install hobby projects; the official MathWorks server is the reputable choice. *(One is interesting only because it explicitly returns figures — see open question below.)* |
| **MCP Framework for MATLAB Production Server** | Server-grade; needs MATLAB Compiler SDK + Production Server. Overkill unless you're *hosting* algorithms for others. |
| Installing **all 165** K-Dense skills | Hurts skill-triggering reliability and burns context. Install the single `matlab` skill only. |

---

## Open questions worth testing yourself

1. **Do plots come back?** The official MCP server's figure-return behavior
   wasn't confirmed in research (a community server explicitly returns figures).
   Test it: *"plot the von Mises vs Tresca yield loci and show me the figure."*
   If figures don't render in-agent, save them to a file and open them
   (Python examples in this repo already do this).
2. **Toolbox-aware code:** the `detect_matlab_toolboxes` tool lets the agent
   tailor code to what you've actually licensed — ask it to check before it
   writes toolbox-specific code.

---

## Sources

- MATLAB MCP Server (official): <https://github.com/matlab/matlab-mcp-server> ·
  <https://www.mathworks.com/products/matlab-mcp-server.html>
- MATLAB Agentic Toolkit (official): <https://github.com/matlab/matlab-agentic-toolkit>
- `matlab-symbolic-math` skill (official, experimental):
  <https://github.com/matlab/agent-skills-playground/tree/main/skills/matlab-symbolic-math>
- MathWorks MCP Core Server announcement (Nov 2025):
  <https://blogs.mathworks.com/deep-learning/2025/11/03/releasing-the-matlab-mcp-core-server-on-github/>
- K-Dense-AI scientific-agent-skills:
  <https://github.com/K-Dense-AI/scientific-agent-skills>
- MCP Framework for MATLAB Production Server:
  <https://www.mathworks.com/products/mcp-framework-matlab-production-server.html>

*Ecosystem note: this is a fast-moving 2025–2026 space (repos have already been
renamed, e.g. `matlab-mcp-core-server` → `matlab-mcp-server`). Re-verify exact
commands against the current repos before relying on them.*
