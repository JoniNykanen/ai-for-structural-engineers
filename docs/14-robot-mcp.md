# 14 — Robot Structural Analysis MCP (drive Robot like MATLAB)

*Lets Claude **build, analyse and read results** from Autodesk Robot Structural
Analysis Professional through tools — the same way the MATLAB MCP (docs/04)
lets it run MATLAB. Windows + installed, licensed Robot required.*

> **Status: experimental.** The MCP handshake (and `rsap_status`) is verified;
> it is **untested against a real Robot install**. Treat every result as
> unverified until you have checked it yourself.

> 🇫🇮 Suomeksi, lyhyesti: [examples/robot/robot-mcp-kayttoonotto.md](../examples/robot/robot-mcp-kayttoonotto.md)

```
Claude Code → MCP server "robot" (Python, stdio) → Robot COM API (RobotOM) → Robot
```

This replaces hand-writing COM scripts (docs/10 part B) for everyday work: Claude
calls typed tools such as `rsap_add_bar` or `rsap_bar_forces` instead of
generating raw RobotOM code, so there is far less room for invented API calls.

---

## What it is

[`nhantruong96/rsap-mcp`](https://github.com/nhantruong96/rsap-mcp) — a
third-party, **MIT-licensed** MCP server (not by Autodesk). Written for Robot
**2027**; older versions may work but are untested.

- **Pinned** to commit `08ab805`. The source was read before pinning (only COM
  calls + stdio — no network, no subprocesses, no eval). That is a code read,
  not a test: the server has not been run against Robot. `setup.ps1` checks out
  exactly that commit.
- Installed to `tools/rsap-mcp/` (gitignored) with its own `.venv`.
- Registered for this repo in **`.mcp.json`** as server **`robot`** — every
  clone gets it; Claude Code asks you to approve it once.

## Setup

```powershell
./setup.ps1               # installs it automatically if Robot is detected
./setup.ps1 -WithRobot    # force install (e.g. Robot installed later)
```

Then **restart Claude Code** in this folder and approve the `robot` server
(or run `/mcp`). Check:

```bash
claude mcp list           # robot: ... - ✔ Connected
```

Before first use, **start Robot once from the Start menu** so it finishes its
first-run setup; the server can then start/attach to it via COM.

## Tools (35)

| Area | Tools |
|---|---|
| Project | `rsap_connect`, `rsap_status`, `rsap_new_project`, `rsap_open_project`, `rsap_save_project`, `rsap_close_project` |
| Geometry | `rsap_add_node(s)`, `rsap_add_bar(s)`, `rsap_list_nodes`, `rsap_list_bars`, `rsap_delete_objects` |
| Properties | `rsap_define_section`, `rsap_define_material`, `rsap_assign_section`, `rsap_assign_material`, `rsap_list_sections` |
| Supports | `rsap_define_support`, `rsap_assign_support` |
| Loads | `rsap_add_load_case`, `rsap_add_self_weight`, `rsap_add_nodal_force`, `rsap_add_bar_uniform_load`, `rsap_add_bar_point_load`, `rsap_add_combination`, `rsap_list_load_cases` |
| Analysis | `rsap_generate_mesh`, `rsap_calculate`, `rsap_calculation_status` |
| Results | `rsap_bar_forces`, `rsap_bar_force_envelope`, `rsap_node_displacement`, `rsap_node_reaction`, `rsap_results_summary` |

Selections use Robot text: `1to10`, `1 2 3`, `1to20by2`.

## Try it

> *"Using the robot MCP: new 2D frame, 6 m simply supported IPE 240 S355 beam,
> 10 kN/m uniform load + self-weight. Calculate and give max moment, support
> reactions and midspan deflection. Then check M_max against wL²/8 by hand."*

The last sentence matters — see below.

## ⚠️ Units — read this

The server works in **SI base units everywhere: m, N, N·m** (Pa for stress),
regardless of what Robot's GUI displays. 10 kN/m is 10 000 N/m. Reading a
result as kN·m when it is N·m is a silent ×1000 error — always state units and
sanity-check (repo CLAUDE.md rule 3).

## Honest caveats

- **Third-party, young project** (0 stars at time of review). Re-review the
  diff before bumping the pinned commit.
- **Untested against a real Robot install** — verified only up to the MCP
  handshake and `rsap_status` (no Robot on the authoring machine).
- **Write access by default**: tools create/modify/save models. Work on copies
  of real projects.
- COM is Windows-only and single-threaded; `rsap_calculate` can take a while on
  big models.
- **Verify results independently** (hand calc, Python, or the eurocode-fi
  Level-2 check in docs/11). The MCP removes API hallucination, not modelling
  errors.

## Related
- docs/10 — Autodesk Product Help MCP (docs) + raw COM scripting
- Skill: `robot-structural` — RobotOM idioms when you go beyond these 35 tools
- docs/04 — the MATLAB MCP this mirrors
