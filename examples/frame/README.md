# Beam and frame analysis in Python (PyNite FEM examples)

Structural analysis of beams and frames with **PyNite** — a free, MIT-licensed
3D frame finite element library. **No MATLAB or Robot license needed.**

| File | What it does |
|---|---|
| `continuous_beam_pynite.py` | Two-span continuous beam, UDL on both spans: reactions, support moment, span moment, deflection, M and V diagrams. Self-checks every value against the closed-form solution. |

## Setup

```bash
pip install -r requirements.txt     # includes PyNiteFEA
```

## Run

```bash
python continuous_beam_pynite.py
```

Edit `INPUTS` at the top of the script (L, q, E, I …). Units are **kN and m**
throughout; PyNite has no units of its own, it only needs them consistent.

Default case (L = 6 m, q = 10 kN/m, I ≈ IPE 300):

| Quantity | PyNite | Closed form |
|---|---|---|
| R_A = R_C | 22.500 kN | 3qL/8 = 22.500 kN |
| R_B | 75.000 kN | 10qL/8 = 75.000 kN |
| M_B (support) | −45.000 kN·m | −qL²/8 = −45.000 kN·m |
| M_span (max) | 25.312 kN·m | 9qL²/128 = 25.312 kN·m |
| δ_max | 4.000 mm | 0.005416 qL⁴/EI = 4.000 mm |

The script exits with a non-zero code if any value is more than 0.5 % off the
closed form. Tests: `tests/test_continuous_beam_pynite.py` (also in CI).

> **Analysis, not design.** This gives internal forces only. Resistance checks
> (EC3 steel, EC5 timber) are a separate step and need Finnish NA values from
> `params/` — see [docs/11](../../docs/11-eurocode-fi.md).

## Cross-check in Robot (optional)

The closed form only exists for simple cases. For a real frame, the
independent second method ([docs/15](../../docs/15-verify-ai-results.md)) is to
run the **same model in a second program** and compare. With the `robot` MCP
connected ([docs/14](../../docs/14-robot-mcp.md)), ask Claude:

> Build the model from `examples/frame/continuous_beam_pynite.py` in Robot:
> nodes at x = 0, 6, 12 m, two bars, pin at A, rollers at B and C, uniform load
> 10 kN/m on both bars. Calculate and compare the reactions and the moment
> over B to the PyNite output.

Remember that Robot's MCP uses **N and m**, so 10 kN/m becomes 10 000 N/m.
Agreement to within rounding means both models are set up the same way;
disagreement usually points at a support or a load direction.
