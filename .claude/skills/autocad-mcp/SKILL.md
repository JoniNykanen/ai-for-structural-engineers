---
name: autocad-mcp
description: >-
  Use when drawing in, reading from or plotting a live AutoCAD drawing through
  the `autocad` MCP server (autocad-mcp-pro 1.8.0, COM engine), or when tempted
  to drive AutoCAD with Python win32com / pywin32 instead. Covers finding the
  right tool among the 257 hidden ones, reading dimension values and table
  cells, starting from a .dwt template, layouts, page setup and PDF plotting,
  and what to do when the server says CONNECTION_CLOSED or CONNECT_TIMEOUT.
metadata:
  type: reference
  author: ai-for-structural-engineers
  version: "1.0"
---

# AutoCAD through the `autocad` MCP

**Core rule: the MCP is the path, plain COM is not.** Every drawing task in
this repo goes through the `autocad` MCP server. Python `win32com` against
AutoCAD is allowed only in the two cases under *When COM is allowed*.

Setup, settings and server gotchas: [docs/20](../../../docs/20-autocad-mcp.md).
Drawing rules (template, 0,0, ALL CAPS, sheet layout, plot): `CLAUDE.md` →
*CAD drawings*.

## 1. Check the connection first

Before anything else call `call_tool(name="system_status")` (it is one of the
hidden tools, see section 2). It must say `"backend":"com"` and
`"connected":true`.

| What you see | Cause | Tell the user |
|---|---|---|
| No `mcp__autocad__*` tools, or `CONNECTION_CLOSED` | The server never started. Usually `uvx` is missing or not on PATH | Check `uvx --version`. Missing: install uv (docs/20 step 2) and restart Claude Code. Present: open AutoCAD, then `/mcp` → *Reconnect* |
| `CONNECT_TIMEOUT` (30000 ms) | AutoCAD was not open (`CAD_LAUNCH=never`) or the first download was slow | Open AutoCAD and the drawing, then `/mcp` → *autocad* → *Reconnect* |
| `cad_not_running` on every call | Backend is `com` but AutoCAD is closed | Open AutoCAD, reconnect |
| `busy` after a long call | A call ran over 60 s | Press Esc in AutoCAD, retry |

**If the MCP is not connected: stop and report.** Name the row above and the
fix. Do not switch to `win32com` on your own: the user asked for the MCP, and a
COM workaround hides the broken setup they need to fix.

## 2. Finding a tool

The server runs in search mode. Only six tools are listed directly:
`search_tools`, `describe_tool`, `call_tool`, `cad_batch`, `drawing_info`,
`entity_list`. The other 251 exist but are hidden.

1. `search_tools` with an **English** phrase or an AutoCAD command name
   (`"linear dimension"`, `"PAGESETUP"`), not Finnish.
2. `describe_tool` with `names=[...]` to read the schemas of several at once.
3. `call_tool` with `name` and `arguments`.

**A tool you have not searched for is not a tool that does not exist.** Before
concluding "the MCP can't do this", search with at least two phrasings, then
check the table below.

## 3. Task → tool

| Task | Tool(s) | Note |
|---|---|---|
| New drawing from the user's template | `drawing_new(template="<path>.dwt")` | Path is used as given. Then `drawing_save_as` to name it. Check with `layer_list` and `dimstyle_list` that the template's layers and styles arrived |
| Open / switch / list drawings | `drawing_open`, `document_activate`, `document_list` | |
| Layers | `layer_create`, `layer_set_current`, `analysis_layer_stats` | Use the template's layers, name which one each part went on |
| Many entities at once | `cad_batch` or `entity_batch_create` | Never one call per entity |
| Lines, polylines, arcs, text | `entity_create_line` / `_polyline` / `_arc` / `_text` / `_mtext` | Text in ALL CAPS |
| Dimensions | `dimension_linear`, `dimension_aligned`, `dimension_auto`; style: `dimstyle_list`, `dimstyle_set_current` | Pick the style by scale |
| **Read a dimension's measured value** | **`entity_get(handle)`** → `dimension.measurement` | `analysis_list_properties` does not show it; `entity_get` does |
| Length / area of something drawn | `analysis_measure_entity(handle)`, `analysis_measure_distance` | Area includes arc edges |
| Table | `entity_create_table(..., layer=...)` | **Always pass `layer`**: default is `TEXT`, which the template may not have |
| Find texts (e.g. profile names) | `entity_list(type_filter="TEXT", fields=[...])`, filter the list yourself | No text-content filter exists. `text_find_replace(dry_run=True)` previews matches but is a replace tool |
| Select by layer / type / place | `entity_select_smart(predicate)`, `selection_filter` | Predicate keys: type, layer, near, length_range, color |
| System variables (LTSCALE, DIMSCALE) | `system_set_variable` | |
| Extents start at 0,0 | `analysis_bounding_box` | Lower-left must be 0,0, nothing negative |
| Layout + viewport at a scale | `layout_create`, `viewport_create(..., scale=...)`, `viewport_set_scale` | `scale` is paper:model as a number: 1:50 → `0.02`, 1:20 → `0.05` |
| Page setup | `page_setup_apply(layout, paper="A4", bleed="full_bleed", plot_style="monochrome.ctb")` | Full-bleed media avoids clipped frames. `plot_area` is `layout` or `extents` only (no Window), so check the frame in the PDF |
| Title block / frame | `titleblock_apply`, `sheet_frame` | ISO 7200 lower-right. Move it if the repo's sheet layout needs another place |
| Plot to PDF | `drawing_export_pdf(path, layout)`, `batch_plot` | Then look at the PDF |
| Look at the result | `view_zoom_and_screenshot` | |
| Save | `drawing_save`, `drawing_save_as` | Work on a copy, never the original |
| Anything else | `system_run_command` (an AutoCAD command string) | Still inside the MCP, before any COM |

## 4. When COM is allowed

Plain `win32com` is allowed only when **both** hold:

1. The MCP is connected and you searched for a tool (section 2) and found none,
   and
2. The COM code **only reads**, as an independent check of something the MCP
   wrote.

Known case: **table cell contents.** No MCP tool reads them back, so read them
with COM after `entity_create_table`, using the handle from its result. Say in
the answer that COM was used and why.

```python
import win32com.client  # read-only check, MCP connected, no read tool exists
doc = win32com.client.GetActiveObject("AutoCAD.Application").ActiveDocument
table = doc.HandleToObject(handle)  # handle returned by entity_create_table
cells = [[table.GetText(r, c) for c in range(table.Columns)] for r in range(table.Rows)]
```

COM that **writes** to the drawing needs the user's explicit OK first, every
time. When it is used, note: `Documents.Add` returns an object without
`SaveAs`; use `ActiveDocument`.

## Red flags: stop and go back to section 2

| Thought | Reality |
|---|---|
| "The MCP failed to connect, I'll just use win32com" | Stop and report the fix (section 1) |
| "analysis_list_properties doesn't show it, so COM" | Try `entity_get`, then search |
| "There's no tool for that" | You saw six of 257. Search |
| "COM is quicker for this one check" | Only for reads no MCP tool covers |
| "I'll draw the title block by hand" | `titleblock_apply` exists |

## Report

In the answer say which MCP tools did the work, and list every COM call
separately with its reason. If something was not checked (for example the PDF
was not opened), say so.
