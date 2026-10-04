---
name: eurocode-fi
description: >-
  Use when producing structural design calculations to the Eurocodes with the
  Finnish National Annex (SFS-NA) / RakMK — sizing or checking members, load
  combinations, ULS/SLS verification. Enforces clause citation, no invented code
  values, shown working, SI units, Finnish output, and an independent re-check.
  First implemented vertical: timber (EN 1995). Do NOT reproduce copyrighted
  standard text or tables.
metadata:
  type: reference
  author: matlab-claude-for-engineers
  version: "1.0"
---

# Eurocode + Finnish National Annex — code-grounded structural calcs

You are producing structural calculations a **practising engineer** can submit
and a checker can verify. Correctness and traceability outrank speed.

## Rule 0 — copyright guardrail (non-negotiable)

Do **not** reproduce Eurocode / SFS-NA / product-standard **text or tables**
(they are copyrighted). You MAY state **clause numbers and titles** (facts) and
use **publicly-derivable engineering formulas**. All code-specific *values*
(γM, kmod, kdef, kcr, ψ, material strengths, deflection limits) come from the
engineer's **parameter file**, never from you.

## Rule 1 — never invent a value

Read every code value from `params/na_timber.yaml` (see
`params/na_timber.example.yaml` for the contract). If a required field is missing
or blank, **STOP** and tell the engineer exactly which field + clause to fill
(e.g. "Täytä `k_mod.medium_term` — EN 1995-1-1 Table 3.1"). Do not proceed with a
guessed number.

## Rule 2 — show the working, cite the clause

For every check, output in Finnish:
**Lähtötiedot** (inputs + units) → **Kaava** → **Pykälä** (e.g. "EN 1995-1-1
§6.1.6") → **Sijoitus** (numbers) → **Tulos** (boxed, units) → **Käyttöaste**
(utilisation `= E_d / R_d`).

**Utilisation policy (the designer's own rule, stricter than the code):** the
largest utilisation of a design must be **below 90 %**; the target range is
**70–80 %**. Mark any check ≥ 90 % as **HYLÄTTY** (rejected), even though the code
allows up to 100 %. When choosing a section, pick the smallest one whose largest
utilisation is ≤ 80 %. Always end with "Suurin käyttöaste X % (check)" plus a
verdict: in the target range / above the target (80–90 %, consider a larger section) /
below the target (< 70 %, possibly oversized). This policy is not a code value,
so it can be stated in the repo.

## Rule 3 — Level-2 verification (independent re-check)

After the primary calculation, run an **independent recomputation** of the
governing results by a *different route* than the first (e.g. numeric vs
closed-form, or MATLAB vs Python, or hand-substitution), and compare within a
small tolerance. Report `Ristiintarkistus: OK` or the delta. Treat this as a
skeptical checker trying to find an error, not a rubber stamp.

For **timber**, an independent check can also mean running the same case through
a free Finnish reference tool (e.g. Puuinfo's glulam beam / mahapalkki tools) and
comparing utilisations — as a black box, never copying its content. See docs/12.

## Rule 4 — units & sanity

Work in consistent SI (kN, m, mm, N/mm²=MPa). Check dimensional consistency and
physical plausibility (no negative section, utilisation and deflection sane).

## Timber (EN 1995-1-1) — the formulas you may use

Public engineering relations (values from the params file):
- Design strength: `f_d = k_mod · f_k / γM`  (§2.4.1, §3.1.3)
- Bending: `σ_m,d = M_d / W`, `W = b h² / 6`; check `σ_m,d ≤ f_m,d` (§6.1.6)
- Shear: `τ_d = 1.5 V_d / (k_cr · b · h)`; check `τ_d ≤ f_v,d` (§6.1.7)
- Deflection: `w_inst = 5 q L⁴ / (384 E I)`, `I = b h³ / 12`; final with `k_def`
  (§2.2.3, §7.2); compare to the params deflection limits.
- Load duration selects `k_mod`; when combining, the shortest-duration action in
  the combination governs `k_mod` (§3.1.3).

Output = **both** a Finnish markdown calc note (`laskumuistio_*.md`) **and** the
runnable script that produced the numbers. End every deliverable with:
*"Apuväline; suunnittelija vastaa tuloksista. Arvot käyttäjän lisensoidusta
normista. Ei korvaa EN 1995-1-1 / SFS-NA:ta."*

## Reach for docs
Use the `autodesk-product-help` MCP or the engineer's licensed PDFs to confirm a
clause you are unsure of. See `docs/11-eurocode-fi.md`. Steel (EN 1993) / concrete
(EN 1992) are future verticals — the same rules apply.
