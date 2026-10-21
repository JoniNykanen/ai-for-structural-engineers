# 14 — Robot Structural Analysis MCP for Claude Code (drive Robot with AI)

*Lets Claude **build, analyse and read results** from Autodesk Robot Structural
Analysis Professional through tools — the same way the MATLAB MCP (docs/04)
lets it run MATLAB. Windows + installed, licensed Robot required.*

> **Status: experimental, field-tested.** Used end-to-end against **Robot 2027
> (Education)** on a 2D steel frame: geometry, sections, loads,
> combinations, linear + nonlinear analysis and result reading all worked.
> Some things the tools cannot do — see [Field-tested notes](#field-tested-notes).
> Still check every result yourself.

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
- **Partially tested** — see [Field-tested notes](#field-tested-notes) for what
  was exercised against a real Robot 2027 install and what is missing.
- **Write access by default**: tools create/modify/save models. Work on copies
  of real projects.
- COM is Windows-only and single-threaded; `rsap_calculate` can take a while on
  big models.
- **Verify results independently** (hand calc, Python, or the eurocode-fi
  Level-2 check in docs/11). The MCP removes API hallucination, not modelling
  errors.

## Field-tested notes

From real use against Robot 2027 (Education) on a 2D frame.

**Worked:** `rsap_connect`, open / Save As / save, nodes, bars, sections from the
Robot database (`HEA …`, `IPE …`, rectangular hollow sections as `RRHS hxbxt`),
steel grades from the material database (e.g. `S355`), self-weight, uniform bar loads (incl. `projected=true`), nodal forces,
combinations, `rsap_calculate`, reactions, bar forces / envelopes, displacements.
A case created with `analysis="static_nonlinear"` gives geometrically nonlinear
(second-order) results — verified to differ from the identical linear case.

**The tools cannot:**

| Missing | Workaround |
|---|---|
| Buckling analysis (`analysis` accepts only `static_linear`, `static_nonlinear`, `modal`, `comb`) | Create one **simple case per combination containing the factored loads**, check it reproduces the combination's reactions, then the user sets *Analysis → Analysis Types → Change analysis type → Buckling* in the GUI. Robot runs buckling on simple cases, not combinations. |
| Set or read member releases, rigid links, supports | Do it in the GUI. Don't delete/recreate bars of an existing model (next row). |
| Delete or edit a load, or edit a combination | Add a **correction load** in the same case (loads superpose), or create a new case/combination. |
| Move a node | Delete + recreate (loses releases on attached bars). |

**Gotchas:**

- **Deleting and recreating bars silently drops their releases**, and the tools
  can't put them back. Changes the frame's behaviour without any error. Work on a
  copy and prefer not to rebuild bars of a model you were given.
- **Robot connects nodes that lie on a bar** at calculation time. A node that
  looks "unconnected" in `rsap_list_bars` (not a bar end) may be fine — check
  force continuity in the results before "fixing" geometry.
- **`rsap_node_reaction` returns numbers for nodes that are not supports.**
  Verify that the support reactions sum to the applied load.
- **Signs follow Robot:** bar `fx` > 0 is compression, < 0 tension. Graders or
  colleagues using Robot output expect these signs.
- **If the user closes the project in the GUI**, calls fail with COM error
  `-2147352567`. Run `rsap_status`; if `project: false`, reopen the file.
- **Nothing is on disk until `rsap_save_project`.** Cases and loads added after
  the last save are gone when the file is reopened. Save right after creating
  cases, not only after calculating.
- **Reading a case that doesn't exist returns zeros, not an error.** All-zero
  forces or reactions usually mean a wrong case number — check
  `rsap_list_load_cases` before trusting them.
- **After reopening a file, results are gone.** Reading them fails with the same
  COM error; run `rsap_calculate` first.
- **Buckling modes in the GUI:** the node-displacement table shows the *static*
  solution even when a mode is selected. Mode shapes appear only in the diagram
  (*Results → Diagrams for Bars → Deformation*, then **Normalize**). The global
  sway mode is the one where both column tops move the same way; local member
  modes can come first.
- **Results summary scans** default to 300 nodes/bars — raise the caps on big
  models.

## Related
- docs/10 — Autodesk Product Help MCP (docs) + raw COM scripting
- Skill: `robot-structural` — RobotOM idioms when you go beyond these 35 tools
- docs/04 — the MATLAB MCP this mirrors
