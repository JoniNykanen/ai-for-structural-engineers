# Changelog

Notable changes to this repo. Keep entries short; newest on top.

## [Unreleased]
### Added
- **LinkedIn MCP** (`docs/13`, optional): guide to connect Claude to your own
  LinkedIn posts via an open-source OAuth (official-API) MCP server — read-only,
  for voice/style matching. Notes the Community Management API approval gate.
  Machine-local (not committed); registration uses `-e` env creds.
- **Finnish reference tools** (`docs/12`): curated links to Puuinfo's free
  EC5/RIL 205 timber tools (glulam beam, mahapalkki, column…) for independent
  cross-checking, plus DOF with a legacy (RakMK B7) caveat. Link-only, no
  copyrighted content copied; wired into the eurocode-fi Level-2 verification.
- **eurocode-fi** (`docs/11`): code-grounded structural calcs to Eurocode +
  Finnish NA. New `eurocode-fi` skill (cite clause, never invent a value, Level-2
  independent re-check, Finnish output, copyright guardrail), a `params/`
  contract (committed blank template + gitignored filled file), and a timber
  worked example (`examples/eurocode/timber/glulam_beam_ec5.py`: ULS bending/shear
  + SLS deflection, cross-checked, writes a Finnish calc note). Adds `pyyaml`.
- **Autodesk support** (`docs/10`): registers the official **Autodesk Product
  Help MCP** (`https://developer.api.autodesk.com/knowledge/public/v1/mcp`,
  read-only, free) for trusted Autodesk docs; adds a **Robot Structural Analysis**
  Python/COM starter (`examples/robot/`) and a **`robot-structural` skill** that
  encodes RobotOM idioms. (No official MCP *drives* Robot; Product Help MCP + the
  skill counter API hallucination.)
- **Automatic learning loop**: `Stop` hook (`.claude/hooks/capture_session.py`)
  captures every session's Q&A into `solved/` and indexes it in `USAGE_LOG.md`.
- **Auto-push** (opt-in): `SessionEnd` hook (`.claude/hooks/push_session.py`)
  commits + pushes `solved/` per session when `.claude/autopush.enabled` exists.
- **One-command setup**: `setup.ps1` (Windows) and `setup.sh` (macOS/Linux) —
  Python env, MATLAB Engine API, MCP server registration, skills, and plugins.
- `docs/09-how-this-repo-learns.md` — the capture → review → codify routine.
- `CLAUDE.md` learning-loop section (weekly review + promotion of lessons).

## [0.1.0] — 2026-09-13
### Added
- Initial teaching kit: README, `CLAUDE.md` tutor rules, docs 00–08.
- Three MATLAB↔Claude connection methods (Python/SymPy, Engine API, official
  MATLAB MCP Server), all verified on MATLAB R2026a.
- Worked plasticity examples (Python + MATLAB) and a vetted add-ons guide.
- Skills: `matlab-symbolic-math`, `math`, `sympy-symbolic`, K-Dense `matlab`;
  plugins: `matlab-core`, `math-and-optimization`.
