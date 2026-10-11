# 17 — Revit MCP (read a BIM model, check it in Python)

*Lets Claude **query a live Revit model** — find structural members, read their
lengths and section properties — and hand them to the repo's own calculation
tools. Windows + Revit 2027 required.*

> **Status: experimental, field-tested read path.** Tested on **Revit 2027.3
> (Education)** with Autodesk's *Snowdon Towers Sample Structural* model:
> connection, model queries and element/type data all worked. The write tools
> (`modify_element_parameters`, `move_elements`, `rotate_elements`) were **not**
> exercised. Autodesk ships this server as a *Technical Preview*.

> 🇫🇮 Suomeksi, lyhyesti: [examples/revit/revit-mcp-kayttoonotto.md](../examples/revit/revit-mcp-kayttoonotto.md)

```
Claude Code → MCP server "revit" (Autodesk, stdio .exe) → add-in inside Revit → open model
```

---

## What it is

The **Revit Public MCP Server** — Autodesk's own MCP server for Revit 2027
(Technical Preview). It runs locally; the model is not uploaded to Autodesk,
but whatever the tools return is sent to Claude. Three editions exist; install
**one**:

| Edition | Can do | Use when |
|---|---|---|
| **Read-Tools** | query, element data, views, export, select | You only read the model (the workflow below) |
| **Write-Tools** | Read + change parameters, move, rotate, review changes | You also want Claude to edit (this repo's `.mcp.json` points here) |
| **Experimental-Tools** | Write + newer creation tools, at your own risk | Exploring |

Write and Experimental need Revit **2027.2 or later**.

## Setup

1. **Install the add-on:** Autodesk Account → *Products and Services* →
   *Product Updates* → filter *Revit 2027* → *Add-ons* → e.g.
   *"Revit 2027 MCP Server Write-Tools Technical Preview"*.
2. **Restart Revit.** The add-in loads only at Revit start-up — a Revit that
   was already open when you installed the add-on is invisible to the server
   (`get_running_revit_instances` returns `[]`). If Revit asks about the
   add-in, choose *Always Load*.
3. **Register it in Claude Code.** This repo's `.mcp.json` already has a
   `revit` entry pointing at the Write-Tools path:
   `C:\Program Files\Autodesk\Revit 2027 MCP Server Write-Tools Technical Preview\Autodesk.RevitMcpServer.Stdio.exe`.
   For Read-Tools, change `Write-Tools` to `Read-Tools` in that path. (Elsewhere:
   `claude mcp add revit -- "<path to Autodesk.RevitMcpServer.Stdio.exe>"`.)
   Autodesk's setup instructions cover Claude Desktop and Cursor, not Claude Code.
4. **Restart Claude Code** in this folder and approve the `revit` server.
5. In Revit: **open a model, close all dialogs, stay in *Modify***. The server
   does not answer while a command or dialog is active.

## Tools (12, Write-Tools edition)

| Area | Tools |
|---|---|
| Session | `get_running_revit_instances` (gives the process id every other tool needs), `get_active_context` |
| Read | `query_model` (filters by category / level / name / family / parameter / bounding box; returns ids + counts), `get_element_data` (basic info, bounding box, key / specific / all parameters) |
| View | `open_view`, `show_elements`, `select_elements`, `export_views` (PNG/JPG/PDF/CSV…) |
| Write | `modify_element_parameters` (incl. type change), `move_elements`, `rotate_elements`, `review_changes` |

Until the add-in inside Revit answers, Claude Code shows only
`get_running_revit_instances`; the other tools appear once Revit is found.

## Workflow: Revit beam → section check → PyNite

Prompt:

> *"Using the revit MCP: find the structural framing in the open model, pick a
> steel W-beam, read its System Length and its type's section properties, write
> them to a JSON like `examples/revit/snowdon_W18x55_608386.json`, then run
> `examples/revit/check_revit_beam.py` with q = 10 kN/m and report."*

What happens:

1. `query_model` with category `OST_StructuralFraming` → element ids and counts
   (the sample has 959 beams: AISC W, C and L shapes, joists, concrete beams;
   no timber).
2. `get_element_data` on one instance → `System Length`, `Cut Length`, type id.
3. `get_element_data` on the **type id** → section area, moments of inertia,
   height, width, flange and web thickness, *Section Name Key*.
4. `check_revit_beam.py` converts feet → m, checks the section data against
   the plate geometry, runs PyNite (simply supported, UDL) and compares to
   qL²/8 and 5qL⁴/384EI. See [examples/revit/README.md](../examples/revit/README.md).

**The model has no loads.** Loads and support conditions are *your* inputs;
say so when you report. Design checks (EC3) are a separate step.

## ⚠️ Units — read this

`get_element_data` returns each parameter twice: `value` in **Revit internal
units (feet, ft², ft⁴, …)** and `displayValue` as formatted text in the
project's units (here inches). Use `value` and convert (1 ft = 0.3048 m). Filters
in `query_model` also take feet. Never mix the two.

## Field-tested notes

**Worked:** instance discovery, active context (also lists linked models),
`query_model` by category incl. `TypesOnly`, by name, with counts per level,
`get_element_data` with `AllParameters` and `SpecificParameters`, type data via
the instance's `typeId`.

**Gotchas:**

- **BIM data can be wrong — check it.** In the sample model the type
  *W18x55* has the depth, width, plate thicknesses and area of a W18x55, but its
  *Section Name Key* is `W12X26` and its Ix (204 in⁴), Sx and Zx are W12X26's.
  The real W18x55 has Ix ≈ 890 in⁴. A deflection from the Revit value would be
  4.3× too large; a stress from its Sx ~3× too large — and in another model the
  error could go the unconservative way. Its *Nominal Weight* reads 550 lbf/ft
  (should be 55). `check_revit_beam.py` catches the Ix and name mismatch.
- **Section properties live on the type**, not the instance. Ask for the type
  id's parameters.
- **`SpecificParameters` silently skips names that don't exist** on that
  element (e.g. instance-level `Structural Material` on a steel beam) — no
  error, just missing from the output.
- **No analytical members** in the sample model and no loads (only load-case
  names). Spans come from `System Length`; supports are assumed.
- **Linked models and worksets are not supported** (Autodesk known limitation).
  The structural sample links the architectural/MEP models; their elements are
  not queried.
- The window title shows **EDUCATION (NON COMMERCIAL)** with an Education
  licence — no commercial use of the results.

## Honest caveats

- **Technical Preview**: tool names and behaviour may change before GA.
- **Write tools edit the live model.** Work on a copy; use `review_changes`
  after every write. Not tested here.
- **Verify independently** ([docs/15](15-verify-ai-results.md)): the MCP removes
  API hallucination, not modelling or data errors — as the W18x55 case shows.

Sources: [Autodesk — Revit Public MCP Server](https://help.autodesk.com/view/RVT/2027/ENU/?guid=GUID-80B05F4F-1642-46BD-ACED-699D3125AEB9) ·
[Autodesk Developer Blog — Revit MCP Server update](https://blog.autodesk.io/revit-mcp-server-update/)
