# Design spec — eurocode-fi (Eurocode + Finnish NA norm-grounding)

Date: 2026-09-13 · Status: approved, implemented (first vertical)

## Goal
A capability for practising construction/structural engineers (also usable by
students) that makes Claude produce **code-compliant** structural calculations
that **cite clauses, show working, and are independently checkable** — in
Finnish — **without embedding copyrighted standard text or tables**.

## Decisions (from brainstorming)
1. **First vertical:** timber, EN 1995-1-1 + SFS-NA (builds on the existing,
   verified glulam example).
2. **Code values:** a local **parameter file** the engineer fills from their
   licensed NA. Committed template (blank + clause refs) + gitignored filled file.
3. **Verification:** Level 2 — self-documenting output **plus** an independent
   recomputation by a different route.
4. **Deliverable:** both a Finnish markdown calc note **and** a runnable script.

## Copyright constraint (shapes everything)
No Eurocode/SFS-NA/product-standard text or tables in the repo. Allowed: clause
numbers/titles (facts) and public engineering formulas. All standard values come
from the user's parameter file at runtime.

## Components
- `.claude/skills/eurocode-fi/SKILL.md` — rules: cite clause; never invent a
  value (stop if missing); show formula→substitution→result+units+utilisation;
  Level-2 re-check; SI units; Finnish; copyright guardrail. Generic framework,
  timber formulas listed.
- `params/na_timber.example.yaml` (tracked template) / `params/na_timber.yaml`
  (gitignored, user-filled).
- `examples/eurocode/timber/glulam_beam_ec5.py` — reads params, computes ULS
  bending (§6.1.6) + shear (§6.1.7) and SLS deflection (§2.2.3, §7.2), independent
  numeric cross-check, writes `laskumuistio_liimapuupalkki.md` (gitignored output).
- `docs/11-eurocode-fi.md` — usage, copyright stance, verification, disclaimer.

## Error handling
Missing/blank param → hard stop naming the field + clause. No guessed values.

## Out of scope (future specs)
Steel (EN 1993), concrete (EN 1992), loads (EN 1990/1991); PDF review report
(Level 3). Framework is generic so these add without rework.

## Verification of the implementation
Originally checked by hand only: the happy path was run once with dummy values
on Python 3.11 (utilisations sane, cross-check OK, note written), the guardrail
stopped on the blank template, and the filled params file is gitignored. There
were no automated tests at that point. Automated tests now exist in
`tests/test_glulam_ec5.py` (pytest, run in CI). No MATLAB needed.
