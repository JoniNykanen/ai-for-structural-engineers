# Changelog

Notable changes to this repo. Keep entries short; newest on top.

## [Unreleased]
### Added
- **PTC Mathcad worksheet checker** (`docs/19`, `examples/mathcad/`):
  `check_mcdx.py` reads a Mathcad Prime `.mcdx` file without Mathcad
  (`worksheet.xml` + `result.xml`), re-evaluates every formula with its own
  unit handling and flags stale results, unit slips and Mathcad errors. Works
  with the free Mathcad Express. Tests in `tests/test_check_mcdx.py` build
  `.mcdx` fixtures in code. Field-tested on Mathcad Prime 12. Prime automation
  (COM API / MCP) is documented but not yet field-tested: Express can't assign
  inputs/outputs, and the 30-day trial stayed in Express mode.
- **Tekla Structures + EC3 steel** (`docs/18`, `examples/eurocode/steel/`):
  `export_tekla_beam.py` reads a beam from an open Tekla model (Open API via
  pythonnet); `steel_beam_ec3.py` checks it to EN 1993-1-1 (class, bending,
  shear, LTB, deflection) with cross-checks vs Tekla's catalog, numerical
  integration and Rayleigh–Ritz M_cr. Values from `params/na_steel.yaml`
  (template `params/na_steel.example.yaml`). Uses the community
  teknovizier/tekla_mcp_server (GPLv3), installed outside the repo.
- **PyNite FE example** `examples/frame/continuous_beam_pynite.py`: two-span
  continuous beam (reactions, M, V, deflection, diagrams) with a self-check
  against the closed form; tests in `tests/test_continuous_beam_pynite.py`.
  `PyNiteFEA` (MIT) added to `requirements.txt`. First frame-analysis path
  that needs neither MATLAB nor Robot.
### Changed
- **Renamed the repo to `ai-for-structural-engineers`** (was
  `matlab-claude-for-engineers`; GitHub redirects old links). README rewritten
  around what structural engineers and students search for (Eurocode in
  Python, PyNite, Revit MCP, Robot MCP, plasticity, verifying AI results);
  search-friendly doc titles; GitHub description and topics.
- `setup.ps1` step 7/8 detects the Revit MCP add-on and registers any edition
  other than Write-Tools at local scope (overrides `.mcp.json`).
### Added
- **PyNite FE example** `examples/frame/continuous_beam_pynite.py`: two-span
  continuous beam (reactions, M, V, deflection, diagrams) with a self-check
  against the closed form; tests in `tests/test_continuous_beam_pynite.py`.
  `PyNiteFEA` (MIT) added to `requirements.txt`. First frame-analysis path
  that needs neither MATLAB nor Robot.
- **Revit MCP** (`docs/17`): `.mcp.json` registers Autodesk's official Revit
  Public MCP Server (Write-Tools, Technical Preview) as `revit`. Read path
  field-tested on Revit 2027.3 with the Snowdon Towers structural sample; write
  tools not tested. New `examples/revit/check_revit_beam.py` checks a beam's
  Revit section data against its plate geometry and runs it in PyNite — it
  caught the sample's "W18x55" type carrying W12X26 stiffness (Ix 4.3× low).
  Finnish quickstart `examples/revit/revit-mcp-kayttoonotto.md`; tests in
  `tests/test_check_revit_beam.py`.
### Changed
- **License:** code is now Apache-2.0 (was MIT) and docs are CC BY 4.0
  (`LICENSE-docs`); a `NOTICE` file adds attribution, the trademark carve-out
  and the "no Eurocode values" statement.
- **mahapalkki example reads code values from `params/na_timber.yaml`** via the
  new `examples/structural/lue_na_parametrit.m`, which uses MATLAB's Python
  interface and pyyaml from the repo `.venv`. No normative values remain in
  the script. Results are unchanged (215 × 1710 mm, 76.8 %). The template gains
  `actions.psi0_wind`, `actions.psi2_wind` and `curved_beam.k_dis`.
- **Robot MCP field-tested** on Robot 2027 (Education): docs/14 status updated,
  new *Field-tested notes* (what works, missing tools + workarounds for
  buckling / releases / load deletion, gotchas); same rules added to the
  `robot-structural` skill, README and the Finnish quickstart.
### Removed
- `docs/13` LinkedIn MCP guide — a personal tool, unrelated to engineering.
  (Number 13 is left unused so other doc links stay stable.)
### Fixed
- **Ramberg–Osgood example** mixed two forms (α=0.002 with the σy/E factor),
  giving a plastic strain at σy of 2.5e-6 instead of 0.002. Now uses the 0.2 %
  offset form; regression-tested. Also: plastic-hinge note (collapse > first
  yield for *all* beams via shape factor), hydrostatic divide-by-zero in von Mises.
- **glulam_beam_ec5.py**: separate EN 1990 6.10a/6.10b combinations
  (`gamma_G_610a`/`gamma_G_610b`), snow duration class read from params
  (`actions.snow_duration`), truly independent numeric cross-check (exit 2 on
  mismatch), calc note flags DUMMY/TEST params. **Breaking:** filled
  `params/na_timber.yaml` files need these three new fields.
- **Auto-push hook** committed anything already staged; now commits only the
  captured paths, rebases before push, logs errors to `.claude/hooks/hook_errors.log`.
- **Hooks** now find Python on macOS/Linux/Windows (venv → python3 → python → py).
- **Setup scripts** check every external command and report failures honestly;
  closing prompt suggests a Python first win when MATLAB is absent.
### Changed
- **Utilisation policy** (designer's rule, stricter than the code): largest
  utilisation must be < 90 % (else HYLÄTTY, `glulam_beam_ec5.py` exits 3),
  target 70–80 %; sections are chosen at ≤ 80 %. Encoded in the eurocode-fi
  skill and both timber examples — mahapalkki is now 215 × 1710 mm (76.8 %).
- README: prerequisites checklist, 4-step quickstart, everything else under
  "Optional extras" (Robot marked experimental); skills tables moved to docs/08.
- CLAUDE.md: use the repo venv Python; every calculation answer includes a check.
### Added
- **Tests + CI**: `tests/` (pytest, 30 tests: example self-checks, EC5 golden
  values on TEST-ONLY params, hooks) and `.github/workflows/tests.yml`.
- `self_check()` physics checks in every Python plasticity/SymPy example.
- Session capture: secret/email redaction, 200 KB cap, opt-out via
  `.claude/capture.disabled`; disclosed in README.
- `docs/15-verify-ai-results.md` and `docs/16-academic-integrity.md`.
- Pinned MATLAB MCP server v0.14.0 (SHA-256 checked) and `skills@1.7.0`.
- **Robot MCP** (`docs/14`): project `.mcp.json` registers server `robot` —
  third-party MIT [`rsap-mcp`](https://github.com/nhantruong96/rsap-mcp), 35 tools
  (model → loads → calculate → results), pinned to reviewed commit `08ab805`.
  `setup.ps1` installs it to gitignored `tools/rsap-mcp/` when Robot is detected
  (or `-WithRobot`). Untested end-to-end here (no Robot on authoring machine).
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
