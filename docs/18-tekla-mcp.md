# 18 — Tekla MCP with Claude Code: read a Tekla model, check a steel beam to EC3

*Lets Claude **query and edit a live Tekla Structures model** — read beams,
profiles and materials, change a profile — and hand the member to the repo's
EN 1993-1-1 check. Windows + Tekla Structures required.*

> **Status: experimental, field-tested.** Tested on **Tekla Structures 2026 SP5
> (Educational configuration, Finland environment)**: connection, element
> queries, placing columns/beams and changing a profile all worked. Trimble has
> no official MCP server; this uses a **community** server.

```
Claude Code → MCP server "tekla" (community, Python) → Tekla Open API (.NET) → open model
                                 └── export_tekla_beam.py → JSON → steel_beam_ec3.py → calc note
```

---

## What it is

[teknovizier/tekla_mcp_server](https://github.com/teknovizier/tekla_mcp_server)
— a Python (FastMCP) server that drives Tekla through the Open API via
`pythonnet`. About 60 tools: selection, element properties and UDAs, placing
beams/columns/slabs/grids, components, views, drawings, reports, clash check.
A `read_only` switch disables every modifying tool.

**Licence:** the server is **GPLv3**. This repo does **not** include or vendor
it — clone it to its own folder outside this repo and register it in Claude
Code at local scope. The repo's own Tekla code (`examples/eurocode/steel/`)
talks to the Open API directly and does not use the server's code.

Students: **Tekla for Education** is the same Tekla Structures program with an
educational licence.

## Setup

1. **Install Tekla Structures** and start it with the environment you design
   in (e.g. **Finland**). A model's profile and material catalogs come from the
   environment it was created in — a model made in the *default* environment
   has no HEA/IPE profiles or S355 grades.
2. **Clone the server outside this repo** and make a Python 3.11+ venv:
   ```powershell
   git clone https://github.com/teknovizier/tekla_mcp_server C:\Users\<you>\Projects\tekla_mcp_server
   cd C:\Users\<you>\Projects\tekla_mcp_server
   py -3.11 -m venv .venv
   .venv\Scripts\pip install -r requirements.txt
   ```
3. **Configure:** copy the sample files in `config/` to their real names, then in
   `config/settings.json` set `tekla_path` to your Tekla `bin` folder
   (e.g. `C:\Program Files\Tekla Structures\2026.0\bin`) and keep
   `"read_only": true` until you want Claude to edit the model.
4. **Register in Claude Code** (use Git Bash — PowerShell eats the `--`):
   ```bash
   D="C:/Users/<you>/Projects/tekla_mcp_server"
   claude mcp add tekla --scope local \
     -e "PYTHONPATH=$D/src" -e "TEKLA_MCP_CONFIG_DIR=$D/config" \
     -- "$D/.venv/Scripts/python.exe" "$D/src/tekla_mcp_server/mcp_server.py"
   ```
   Without `PYTHONPATH=…/src` the server fails with
   `ModuleNotFoundError: tekla_mcp_server`.
5. **Start order matters:** open Tekla **and a model first**, then start
   Claude Code. If Tekla was not ready, the server crashes at start-up — fix it
   without restarting Claude: `/mcp` → *tekla* → *Reconnect*.
6. Ask: *"List the beams in the open Tekla model with profile, material and length."*

## Workflow: Tekla beam → EN 1993-1-1 check

Prompt:

> *"Read the IPE beam from the open Tekla model and check it to EC3 with a
> 5 kN/m uniform variable load."*

What happens:

1. `examples/eurocode/steel/export_tekla_beam.py [GUID]` (run with the server's
   venv — it has `pythonnet`) reads the beam's end points, profile, material,
   profile dimensions and catalog properties into
   `examples/eurocode/steel/tekla_beam_<profile>.json`.
2. `examples/eurocode/steel/steel_beam_ec3.py params/na_steel.yaml <json>` checks
   section class, bending, shear, lateral-torsional buckling and deflection, and
   writes a Finnish calc note `laskumuistio_teraspalkki.md`.
3. All code values come from **`params/na_steel.yaml`** (gitignored); the
   template `params/na_steel.example.yaml` lists every field with its clause.
   The script stops if a value is missing.
4. If a check fails, ask Claude to change the profile in Tekla
   (`set_elements_properties`), re-export and re-run.

**Built-in checks** (each run reports them): section properties computed from
the profile dimensions vs Tekla's catalog; M, V and deflection by numerical
integration vs closed form; M_cr closed form (C1/C2) vs a Rayleigh–Ritz
energy solution.

Example (simply supported, L = 7.2 m, 5 kN/m variable + self-weight,
unrestrained top flange, load on the top flange): **IPE300 failed on LTB
(91 %), IPE330 passed (68 %)**. Bending alone was only ~20 %; the unrestrained
compression flange governs.

## Gotchas

- Tekla's catalog gives A, I and W_el but **not** W_pl, I_t or I_w — the
  script computes them from the profile dimensions (incl. root fillets).
- The server's `AREA` report property is the **paint surface area in mm²**,
  despite an "m2" label.
- `Identifier` lives in `Tekla.Structures`, not `Tekla.Structures.Model`;
  `Tekla.Structures.dll` is in `bin\Net48Runtime`.
- The first Open API connection can return `False` while a model is still
  loading — retry.
- Write tools change the real model and are committed immediately. Save a copy
  of the model first.
