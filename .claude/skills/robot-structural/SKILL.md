---
name: robot-structural
description: >-
  Use when driving Autodesk Robot Structural Analysis Professional from code —
  building models, running analysis, or reading results via its COM API (Python
  pywin32 or .NET). Encodes the correct RobotOM idioms so generated code does not
  hallucinate API names. Windows + licensed Robot only.
metadata:
  type: reference
  author: matlab-claude-for-engineers
  version: "1.0"
---

# Driving Autodesk Robot Structural Analysis (RobotOM COM API)

You are generating code to control **Robot Structural Analysis Professional**.
Its automation surface is the **RobotOM COM API**. This is niche and
version-sensitive — follow these rules to avoid inventing API members.

## Prefer the `robot` MCP when it is connected

If the `robot` MCP server is available (docs/14), use its `rsap_*` tools instead
of generating COM code. They work in **SI base units (m, N, N·m)** — convert and
label units explicitly when reporting. Fall back to the COM code below only for
things those tools don't cover.

## Rule 0 — verify, don't guess

Robot's API has hundreds of interfaces. Before asserting an object/method/enum
you are not sure of:
1. Prefer the **`autodesk-product-help` MCP** (search Robot help/API docs) or the
   **Robot SDK** docs+examples (installed with Robot under `...\SDK`).
2. If you cannot verify a member, say so and generate a clearly-marked TODO
   rather than a plausible-looking guess.

## Connection (Python)

Use `EnsureDispatch` so the type library is generated and **named enum constants
become available** — never hard-code enum integers:

```python
import win32com.client as win32
robot = win32.gencache.EnsureDispatch("Robot.Application")   # ProgID: Robot.Application
from win32com.client import constants as c                    # e.g. c.I_PT_FRAME_2D
robot.Visible = 1
robot.Interactive = 1
```

(.NET alternative: reference `RobotOM.tlb` / `Interop.RobotOM`; more robust and
better-documented than Python for large jobs.)

## Object model you can rely on

- `robot.Project` → `proj.New(c.I_PT_FRAME_2D | I_PT_FRAME_3D | I_PT_SHELL | …)`
- `proj.Structure` → the model. Key collections:
  - `.Nodes` — `nodes.Create(number, x, y, z)`
  - `.Bars` — `bars.Create(number, startNode, endNode)`
  - `.Labels` — section/material/support/release labels (create then assign by
    name to nodes/bars)
  - `.Cases` (load cases/combinations) via `proj.Structure.Cases`
- Run analysis: `proj.CalcEngine.Calculate()`
- Results: `proj.Structure.Results...` (bar forces, node reactions, displacements)

## Hard constraints (state these when relevant)

- **Single-threaded:** all Robot API calls must run on the main thread.
- **Windows-only**, COM; requires an installed + licensed Robot.
- COM is brittle — wrap calls in try/except, check `.Count` after creates, and
  release the app cleanly when done.

## Workflow to follow

1. Connect (above). 2. New project of the right `I_PT_*` type. 3. Build geometry
(nodes → bars). 4. Create + assign labels (section, material, supports, releases).
5. Define load cases/combinations. 6. `CalcEngine.Calculate()`. 7. Read results,
report with **units** and a sanity check (per this repo's CLAUDE.md).

## When unsure

There is **no official Autodesk MCP that *drives* Robot** — the `robot` MCP is
third-party (docs/14). Outside its tools you are generating raw COM code — accuracy
matters. Lean on `autodesk-product-help` for the docs, keep examples small, and
have the user run them in Robot to verify (this repo can't test Robot).
