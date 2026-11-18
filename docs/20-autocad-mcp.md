# 20 — AutoCAD MCP with Claude Code: draw and read structural drawings

*Lets Claude **draw in and read from a live AutoCAD drawing**: lines, texts,
dimensions, layers, blocks, tables and title blocks. It can also write DXF
files with no AutoCAD at all. Windows + full AutoCAD for the live mode.*

> **Status: experimental, not field-tested with AutoCAD.** The server starts
> from `.mcp.json` and the headless DXF mode was tested on Windows 11 (no
> AutoCAD installed): a new drawing, a 7200 mm beam line, an `IPE300` label and
> a save to `.dxf` all worked. **The live AutoCAD mode has not been tested in
> this repo yet.** The test protocol is in
> [examples/autocad/autocad-mcp-testaus.md](../examples/autocad/autocad-mcp-testaus.md).

```
Claude Code → MCP server "autocad" (community, Python) → AutoCAD COM API → open drawing
                                                      └→ ezdxf (no AutoCAD) → .dxf file
```

---

## What it is

[U-C4N/Autocad-MCP](https://github.com/U-C4N/Autocad-MCP), published on PyPI
as `autocad-mcp-pro`. It is a Python (FastMCP) server with two engines:

| Engine | Needs | Use |
|---|---|---|
| `com` | Windows + **full AutoCAD** (2026 tested by the author) | Draw in and read the drawing open in AutoCAD |
| `ezdxf` | Nothing but Python | Write and read `.dxf` files without AutoCAD |

**AutoCAD LT does not work with the `com` engine**: LT has no COM/ActiveX API.
For LT 2024+ the alternative is
[puran-water/autocad-mcp](https://github.com/puran-water/autocad-mcp) (AutoLISP
file queue), not set up in this repo.

It has 257 tools. Only six are listed to Claude by default (`search_tools`,
`describe_tool`, `call_tool`, `cad_batch`, `drawing_info`, `entity_list`).
Claude finds the rest with `search_tools`, which keeps the idle cost at about
1,000 tokens instead of about 59,000.

**It is not a structural-design tool.** Its built-in generators are for
mechanical parts, P&ID diagrams and floor plans. Structural content (beam
elevations, profile sections, member schedules from our Eurocode checks) is
built from its basic tools: lines, polylines, dimensions, texts, tables,
layers and blocks.

Autodesk's own *AutoCAD and Civil 3D MCP Server* (Tech Preview) is not used:
Autodesk Assistant is its only supported client, so Claude cannot connect to it.

**Licence:** MIT, so it is compatible with this repo. The repo does not vendor
the code. `.mcp.json` runs a pinned version (`==1.8.0`) from PyPI through `uvx`.

## Setup

1. **Install full AutoCAD** (2026 or newer recommended). Students: Autodesk
   Education licence, which is non-commercial use only.
2. **Install uv** (it runs the server; nothing else to install):
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
   Open a new terminal and check: `uvx --version`.
3. **Download the server once before starting Claude** (the first run downloads
   about 85 packages; doing it here keeps Claude's start-up from timing out):
   ```powershell
   uvx --from "autocad-mcp-pro[com,pdf]==1.8.0" python -c "import ezdxf, win32com; print('ok')"
   ```
4. **Open AutoCAD and a drawing first**, then start Claude Code in this repo
   folder and approve the `autocad` server. `CAD_LAUNCH=never` means the server
   never starts AutoCAD by itself; it only attaches to the one already running.
5. Check the connection: *"Call system_status on the autocad server."* The
   answer must say `"backend":"com"` and `"connected":true`.

If AutoCAD opened after Claude: `/mcp` → *autocad* → *Reconnect*.

### No AutoCAD: DXF-only mode

In `.mcp.json` set `"AUTOCAD_MCP_BACKEND": "ezdxf"`. Leaving it on `auto` does
**not** fall back to DXF on Windows: with `pywin32` installed, `auto` picks
`com` even when AutoCAD is missing, and every call answers `cad_not_running`.
DXF files open normally in AutoCAD later. Reading `.dwg` without AutoCAD needs
the free [ODA File Converter](https://www.opendesign.com/guestfiles/oda_file_converter).

## Settings used in `.mcp.json`

| Variable | Value | Why |
|---|---|---|
| `AUTOCAD_MCP_BACKEND` | `com` | Live AutoCAD. `ezdxf` for no AutoCAD (see above) |
| `CAD_LAUNCH` | `never` | Never start AutoCAD on its own; attach to the open one |
| `LISP_POLICY` | `read` | AutoLISP limited to read functions (see Gotchas) |
| `DANGEROUS_COMMANDS_ENABLED` | `false` | Blocked commands stay blocked |

To let Claude only read, never write, add `"READ_ONLY": "true"`. All 46
settings are listed in the server's
[README → Configuration](https://github.com/U-C4N/Autocad-MCP#configuration).

## First prompts

- *"List the layers in the open drawing and how many entities each has."*
- *"Find every text that names a steel profile (HEA, HEB, IPE, RHS, SHS) and list them with their position."*
- *"Draw a simply supported beam: 7200 mm line on layer GEOMETRY, support
  symbols at both ends, the label 'IPE300 S355' above it and a dimension for
  the span."*

## Gotchas

- **Full AutoCAD only** for live mode. AutoCAD LT and AutoCAD for Mac do not
  work with the `com` engine.
- **Two clients on one AutoCAD** (e.g. two Claude windows) can steal each
  other's active document (upstream issue #28). Use one Claude session per
  AutoCAD.
- A call that runs over 60 s (`COM_CALL_TIMEOUT`) can leave AutoCAD answering
  `busy` (issue #27). Press Esc in AutoCAD and retry.
- The AutoLISP safety check lets some file and registry functions through
  (issue #23). Keep `LISP_POLICY=read` and `DANGEROUS_COMMANDS_ENABLED=false`.
- Write tools change the open drawing immediately. **Test on a copy.**
- Saving to `.dwg` without AutoCAD is refused. Save as `.dxf`.
- Version 1.8.0 was released before its last fixes were re-run on live
  AutoCAD (upstream changelog). Report anything odd to the test protocol.
