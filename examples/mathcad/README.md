# Mathcad + Python: re-check a Mathcad worksheet without Mathcad

Reads a PTC Mathcad Prime worksheet (`.mcdx`) straight from the file and
re-evaluates every formula in Python. Works with the **free Mathcad Express**,
or with no Mathcad installed at all. Background and Express vs Prime:
[docs/19](../../docs/19-mathcad.md).

| File | What it does | Needs Mathcad? |
|---|---|---|
| `check_mcdx.py` | Lists every definition, re-computes each formula with its own unit handling, compares with the result Mathcad saved, reports Mathcad's own errors | ❌ (reads the file) |

## Run

```bash
python check_mcdx.py my_calc.mcdx          # only rows that need attention
python check_mcdx.py my_calc.mcdx --all    # every row
```

Save the worksheet in Mathcad first: the checker compares against the results
of the **last calculation stored in the file**.

Sample output: a glulam beam sheet where the span was edited but the moment
result is stale (built by `tests/test_check_mcdx.py`):

```
12 math regions — INPUT: 6, MISMATCH: 1, OK: 5

status         name                                      Mathcad                 Python  note
MISMATCH       M_d                                     40.5 kN·m                45 kN·m

CHECK FAILED — 1 row(s) need attention.
```

With `--all` on the corrected sheet:

```
OK             M_d                                       45 kN·m                45 kN·m
OK             W_y                                  0.002484 m^3           0.002484 m^3
OK             σ_m.d                                 18.1159 MPa            18.1159 MPa
OK             = σ_m.d≤f_m.d                                   1                      1
OK             w_inst                                  29.032 mm              29.032 mm
```

Field test: on a real 454-region Mathcad Prime 12 timber design worksheet
(course work, not included) all 327 displayed results matched, and the one
Mathcad error in the sheet (an undefined variable in a function) was reported.

## Statuses

| Status | Meaning |
|---|---|
| `OK` | Python and Mathcad agree (relative tolerance 1e-6, same units) |
| `MISMATCH` | They disagree, or the formula mixes incompatible units. Usually a stale result: recalculate and save in Mathcad, then re-run |
| `MATHCAD ERROR` | Mathcad itself flagged the region (shown in red in Mathcad) |
| `UNIT WARNING` | The result's units don't reduce to the unit it is displayed in, e.g. a line load "shown in kN" |
| `INPUT` / `DEFINED` | A value is assigned but no result is displayed (`x := 5 m`) |
| `NOT CHECKED` | Uses something the checker doesn't evaluate (user functions, programs, integrals, …). Never guessed: later rows carry on with Mathcad's saved value |

## Use the values in other Python code

```python
from check_mcdx import values
v = values("my_calc.mcdx")      # name → quantity in SI
M_Ed = v["M_d"].v                # 45000.0 (N·m)
```

Names follow Mathcad's labels: `g` with subscript `k.katto` becomes `g_k.katto`.

**What a pass means:** the arithmetic and units in the worksheet are
consistent with what Mathcad shows. It does **not** mean the formulas, factors
or national-annex values are right for the design — check those against the
standard as usual ([docs/15](../../docs/15-verify-ai-results.md)).
