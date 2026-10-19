# 19 — PTC Mathcad with Claude Code: check a Mathcad worksheet in Python

*Lets Claude **read a Mathcad Prime worksheet and re-check every result** in
Python. Works with the free Mathcad Express. Driving Mathcad itself (change an
input, recalculate) needs a paid or trial Mathcad Prime licence.*

> **Status: Express path field-tested, Prime automation not yet.** Tested on
> **Mathcad Prime 12.0.0.1** (Windows 11). The file reader matched all 327
> displayed results of a real 454-region worksheet. Automation through
> Mathcad's API could not be field-tested: see [Field-tested notes](#field-tested-notes).

```
Express (free):  my_calc.mcdx ──► check_mcdx.py ──► every formula re-computed, compared, reported
Prime (paid):    Claude Code ──► Mathcad automation API (COM) ──► set input → recalculate → read output
```

---

## Express vs Prime: what works

| | Mathcad **Express** (free) | Mathcad **Prime** (paid / 30-day trial) |
|---|---|---|
| Read a worksheet and re-check it in Python (`check_mcdx.py`) | ✅ | ✅ |
| Works without Mathcad installed (e.g. in CI) | ✅ | ✅ |
| Connect to Mathcad through its automation API | ✅ responds | ✅ |
| Mark values as inputs/outputs (*Input/Output → Assign Inputs*) | ❌ greyed out | ✅ |
| Change an input → recalculate → read the new result | ❌ (needs marked inputs/outputs) | ✅ |
| MCP server (Claude drives Mathcad) | ❌ nothing to drive | ✅ (planned, see below) |

Express and Prime are the **same installed program**: after the 30-day trial
the premium features switch off and it runs as Express. The automation files
(`Ptc.MathcadPrime.Automation.dll`) are installed either way. Having them does
not mean Express lets you script it.

## Express path: `check_mcdx.py`

A `.mcdx` file is a zip. Inside:

| Part | Holds |
|---|---|
| `mathcad/worksheet.xml` | Every math region as an expression tree: names, formulas, units, display unit overrides |
| `mathcad/result.xml` | The results of the **last calculation**, linked to regions by `resultRef`, plus Mathcad's errors and warnings |

`examples/mathcad/check_mcdx.py` re-evaluates each formula in worksheet order
with its own unit handling and compares the value with the saved result. It
catches stale results, unit slips and Mathcad's own errors. It never guesses:
anything it can't evaluate is reported as `NOT CHECKED`.

How to run it and what each status means: [examples/mathcad](../examples/mathcad/README.md).

Ask Claude, for example:

> *"Check my Mathcad worksheet `C:\...\palkki.mcdx` with check_mcdx.py and explain any row that isn't OK."*

> *"Read the design moment and section modulus from `palkki.mcdx` and check the beam to EN 1995 with the eurocode-fi module."*

### Gotchas

- **Save in Mathcad first.** The checker compares against the results stored
  in the file, which come from the last calculation before saving.
- **Display units:** a result shown as `= 6.2 kN/m` is stored as the bare
  number `6.2` in the override unit. Results without an override are stored in
  SI base units. The checker handles both.
- **Inline math inside a text paragraph** is read at the paragraph's position.
- **Not evaluated:** user-defined functions `f(x) := …`, programs (if/for),
  integrals, sums and solve blocks. Later rows continue with Mathcad's saved value.
- **Same name defined twice:** Mathcad uses the newest definition from that
  point on, and so does the checker. Mathcad's "redefined" warning is shown with `--all`.

## Prime path: automation API (not yet field-tested)

Mathcad Prime installs a COM automation API (`MathcadPrime.Application`). With
a Prime licence, a worksheet with inputs and outputs marked can be driven from
Python (`pywin32`) or from an MCP server:

- **MCP server:** [hvkshetry/mathcad-mcp](https://cdn.jsdelivr.net/gh/hvkshetry/mathcad-mcp@main/README.md)
  is a community server, not by PTC, with about 28 tools (open, set inputs with
  units, read outputs, recalculate, export PDF). **Not yet audited, pinned or
  registered by `setup.ps1`.** That waits until it can be field-tested
  against a working Prime licence.
- **Python:** the planned `pywin32` script calls the API directly
  (`Open`, `SetRealValue`, `Synchronize`, `OutputGetRealValue`). We didn't use
  [MathcadPy](https://pypi.org/project/MathcadPy/) because it is GPLv3 and this
  repo's code is Apache-2.0.

## Field-tested notes

Mathcad Prime 12.0.0.1, Windows 11, 19 Oct 2026:

- **Express:** the API connects (`GetVersion` → `12.0.0.1`, worksheets listed).
  `SetRealValue` / `OutputGetRealValue` on a missing name return error code 1
  ("alias not found"), so Express doesn't refuse the API outright. But
  *Assign Inputs* is greyed out, so there's nothing to drive.
- **30-day Prime trial:** the licence was valid ("30-day, full-functionality",
  feature `MathcadPrime 12.0`), was saved in the licence settings, and Mathcad
  reported `LicenseType: Trial`. After several restarts the window title still
  read *PTC Mathcad Express* and *Assign Inputs* stayed greyed out. This
  matches PTC article [CS154971](https://www.ptc.com/en/support/article/CS154971)
  ("Prime running in express mode even after configuring with license file").
  Not solved. Try *Repair* in Windows Apps, then the reseller or PTC support.
- **Reader:** on a real 454-region worksheet all 327 displayed results matched
  the Python re-computation. The one Mathcad error in the sheet was reported.

## Getting a full Mathcad licence as a student

- Ask your university IT or course staff whether there is a campus licence,
  and whether it covers your own computer or only university machines.
- Some Finnish universities send students to the reseller **mathcad.fi** for a
  low-cost student licence ("Opiskelijalisenssi"), for example
  [Metropolia's instructions](https://tietohallinto.metropolia.fi/spaces/itservices/pages/137199841/Mathcad+for+Students+Home+Use).
- Everything in the Express path works without any of this.

Mathcad is a trademark of PTC Inc.; this project is not affiliated with PTC.
