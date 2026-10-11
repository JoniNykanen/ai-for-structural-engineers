# Revit + Python: check Revit beam data and analyse it (Revit MCP examples)

Reading a Revit model with Autodesk's **Revit MCP** and checking it with the
repo's Python tools. Setup and tool list: [docs/17](../../docs/17-revit-mcp.md).
Suomeksi: [revit-mcp-kayttoonotto.md](revit-mcp-kayttoonotto.md).

| File | What it does | Needs Revit? |
|---|---|---|
| `check_revit_beam.py` | Section-data check (Ix, A, name key vs plate geometry) + PyNite simply supported beam + closed-form check | ❌ (reads the JSON) |
| `snowdon_W18x55_608386.json` | Values read from the Revit 2027 sample model, element 608386, raw Revit units (ft) | — |

## Run

```bash
python check_revit_beam.py                                  # sample, q = 10 kN/m
python check_revit_beam.py my_beam.json 15                  # your beam, q = 15 kN/m
```

Sample output (Revit 2027.3, Snowdon Towers Sample Structural):

```
Section data check (Revit type vs independent plate model)
  A   Revit       105 cm² | plates       104 cm² |   +0.9 %  OK
  Ix  Revit      8491 cm⁴ | plates     36605 cm⁴ |  -76.8 %  MISMATCH
  type name 'W18x55' vs Section Name Key 'W12X26': MISMATCH

PyNite analysis vs closed form
  Revit Ix: M_mid = 34.89 kN·m (qL²/8 = 34.89), δ = 5.69 mm, L/δ = 929   PASS
  plate Ix: M_mid = 34.89 kN·m (qL²/8 = 34.89), δ = 1.32 mm, L/δ = 4004  PASS

SECTION DATA INCONSISTENT — ...
```

Exit code 2 = the Revit type's data contradicts its own geometry. Here the
type is named W18x55 but carries W12X26's stiffness. The moment doesn't depend
on I (statically determinate beam), but deflection and stresses do.

**Assumptions you must state when reporting:** q is chosen by you (the model
has no loads), supports are simple, span = Revit *System Length*. This is
analysis only; EC3 resistance checks are a separate step.

## JSON fields

Fill from `get_element_data` → use the **`value`** field (Revit internal units,
feet), not `displayValue`:

| JSON key | Revit parameter | From |
|---|---|---|
| `system_length_ft` | System Length | instance |
| `height_ft`, `width_ft` | Height, Width | type |
| `flange_thickness_ft`, `web_thickness_ft` | Flange Thickness, Web Thickness | type |
| `section_area_ft2` | Section Area | type |
| `Ix_strong_ft4`, `Iy_weak_ft4` | Moment of Inertia strong / weak axis | type |
| `J_ft4` | Torsional Moment of Inertia | type |
| `section_name_key` | Section Name Key | type |

Tests: `tests/test_check_revit_beam.py` (also in CI; no Revit needed).
