# 10 — Autodesk Robot Structural Analysis (advanced, optional)

*Two things: (A) an easy official MCP that gives Claude trusted Autodesk docs,
and (B) driving Robot itself from code. Windows + licensed Robot for (B).*

---

## A. Autodesk Product Help MCP — easy, official, free ✅

Autodesk publishes an official, **read-only remote MCP** that gives Claude
searchable access to Autodesk's official documentation across **110+ products,
10 languages** — including Robot. It does **not** drive Robot; it prevents Claude
from *hallucinating* Robot API/usage by grounding it in real docs.

**Register it with Claude Code (verified endpoint):**
```bash
claude mcp add autodesk-product-help --transport http \
  https://developer.api.autodesk.com/knowledge/public/v1/mcp
```
Streamable HTTP, public (no API key needed). Verify:
```bash
claude mcp list        # autodesk-product-help ... - Connected
```
Restart Claude Code, then ask e.g. *"Using autodesk-product-help, find the
RobotOM API for creating bars and load cases."*

> ✅ Verified connecting from this repo. Works in Claude Code / Desktop / VS Code
> / any MCP client.

---

> **New:** to drive Robot through MCP tools (like MATLAB), see
> [docs/14 — Robot MCP](14-robot-mcp.md). Part B below is the raw-COM route.

## B. Driving Robot itself — Python + COM

**Reality check:** Autodesk's automation MCPs cover **Revit** and **Fusion** —
**there is no official MCP that drives Robot Structural Analysis.** APS (Autodesk
Platform Services) is for cloud/data MCPs, not Robot's desktop automation. So to
*control* Robot you use its **COM API** (RobotOM), same architecture as the
MATLAB Engine API (docs/03).

```
Claude Code → Python (pywin32) → Robot COM API (RobotOM) → model/analysis/results
```

### Setup
- Robot Structural Analysis Professional installed + **licensed** (students:
  free Autodesk **education licence**).
- `pip install pywin32`
- Install the Robot **SDK** (from Robot: "Install Tools & utilities" → SDK) for
  API docs + examples.

### Use it
Start from [`examples/robot/robot_beam_example.py`](../examples/robot/robot_beam_example.py)
(connect → build a beam → run → read results). Then ask Claude — it will use the
**`robot-structural` skill** (in `.claude/skills/`) which encodes the correct
RobotOM idioms.

### Honest caveats
- **Claude knows this API far less than MATLAB** → more risk of wrong calls. The
  `robot-structural` skill + the Product Help MCP (part A) are the countermeasures.
- COM is **Windows-only, single-threaded, brittle**; Robot is heavyweight.
- **Experimental: untested against a real Robot install** (no Robot on the
  authoring machine). The example is a template to verify on your Robot
  machine. The Robot MCP in docs/14 has the same status: MCP handshake
  verified, nothing run against Robot itself.
- A more robust route for big jobs is the **.NET** API (`RobotOM.tlb`), but that
  adds a compile step; Python/COM is the pragmatic starting point.

### How this fits the kit
Robot ≠ redundant with MATLAB. MATLAB/SymPy = analytical hand-calc level; Robot =
full structural **FEA + Eurocode code-checking** of real models. Complementary.

---

## Related
- Skill: `robot-structural` (`.claude/skills/robot-structural/SKILL.md`)
- Example: [`examples/robot/`](../examples/robot/)
- If you ever use **Revit**, it now has an official automation MCP (see Autodesk).
