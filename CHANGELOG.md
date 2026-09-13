# Changelog

Notable changes to this repo. Keep entries short; newest on top.

## [Unreleased]
### Added
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
