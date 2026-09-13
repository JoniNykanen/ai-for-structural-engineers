# Autodesk Robot Structural Analysis examples

Driving **Robot Structural Analysis Professional** from Python via its COM API —
the Robot counterpart to the MATLAB Engine API. **Windows + licensed Robot only.**

| File | What it does | Needs Robot? |
|---|---|---|
| `robot_beam_example.py` | Connects to Robot via COM, creates a simply-supported beam (2 nodes + 1 bar), prints counts | ✅ |

## Setup

```bash
pip install pywin32
```
Plus Robot installed + licensed, and ideally the Robot **SDK** (installed from
Robot: "Install Tools & utilities" → SDK) for API docs and examples.

## Run

```bash
python robot_beam_example.py
```
Degrades gracefully if not on Windows, pywin32 is missing, or Robot isn't
installed — it won't crash.

> ⚠️ **This is a template to verify, not tested in this repo.** Robot's COM API
> is intricate and version-sensitive. Use the **`robot-structural` skill** and
> the **`autodesk-product-help` MCP** to confirm exact API names before relying
> on generated code. Full guidance: [docs/10](../../docs/10-connect-robot-structural.md).
