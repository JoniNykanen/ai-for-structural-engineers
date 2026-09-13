# 04 — Method 3: MATLAB MCP server (official MathWorks)

*Goal: let Claude Code call MATLAB **directly as native tools**, without writing
any Python glue. This uses the **official MATLAB MCP Server from MathWorks** —
reputable, maintained, and the recommended MCP path. **Requires a MATLAB
license.***

> ✅ **Verified working** in this repo with MATLAB **R2026a** on Windows,
> server **v0.13.0**, registered to Claude Code and reporting `Connected`.

## What is MCP?

**MCP (Model Context Protocol)** is a standard way to give AI tools new
abilities via a small "server" the AI can call. The MATLAB MCP Server exposes
MATLAB as tools Claude can invoke on its own:

| Tool | What it does |
|---|---|
| `evaluate_matlab_code` | Run a string of MATLAB code, return the output |
| `run_matlab_file` | Run a `.m` script file |
| `run_matlab_test_file` | Run a MATLAB unit-test file, return results |
| `check_matlab_code` | Static analysis (style, errors, deprecations) — read-only |
| `detect_matlab_toolboxes` | List installed MATLAB + toolboxes and versions |

```
Claude Code ──(MCP tool call)──► MATLAB MCP Server (Go binary) ──► your local MATLAB ──► results ──► Claude
```

Vs Method 2 (Engine API): same idea, but Claude calls MATLAB *itself* instead of
you/Claude writing a Python script each time.

## Prerequisites

- **MATLAB R2021a or later**, installed locally (a license).
- **Claude Code** installed ([docs/01](01-install-claude-code.md)).
- Note your MATLAB root: in MATLAB run `matlabroot` (e.g.
  `C:\Program Files\MATLAB\R2026a`). You'll pass this to the server, so MATLAB
  does **not** need to be on your system PATH.

## Step 1 — Download the official server binary

Grab the binary for your OS from the
[latest release](https://github.com/matlab/matlab-mcp-server/releases/latest):

- **Windows:** `matlab-mcp-server-windows-x64.exe`
- **Linux:** `matlab-mcp-server-linux-x64`
- **macOS:** `matlab-mcp-server-macos-arm64` (Apple silicon) or `-x64` (Intel)

Save it somewhere stable, e.g. `C:\Users\<you>\matlab-mcp-server\`.

Using the GitHub CLI (Windows example):
```bash
mkdir -p "$HOME/matlab-mcp-server"
gh release download --repo matlab/matlab-mcp-server \
  --pattern "*windows-x64*" --dir "$HOME/matlab-mcp-server"
```

Verify it runs:
```bash
"$HOME/matlab-mcp-server/matlab-mcp-server-windows-x64.exe" --version
# -> github.com/matlab/matlab-mcp-server v0.13.0
```

## Step 2 — Register it with Claude Code

One command. Point `--matlab-root` at *your* MATLAB (no `\bin` on the end):

**Windows (PowerShell):**
```powershell
claude mcp add --transport stdio matlab -- `
  "C:\Users\<you>\matlab-mcp-server\matlab-mcp-server-windows-x64.exe" `
  "--matlab-root=C:\Program Files\MATLAB\R2026a"
```

**macOS / Linux:**
```bash
claude mcp add --transport stdio matlab -- \
  "$HOME/matlab-mcp-server/matlab-mcp-server-<os>" \
  --matlab-root=/usr/local/MATLAB/R2026a
```

Confirm it registered and is healthy:
```bash
claude mcp list          # matlab: ... - Connected
claude mcp get matlab    # shows scope, command, args
```

> **Scope:** by default this is *local* (private to you, this project). Add
> `-s user` before `--` to make it available in all your projects.

## Step 3 — Use it

**Restart Claude Code** (MCP tools load at session start), then ask:
```
List your MATLAB MCP tools, then use evaluate_matlab_code to compute the
principal stresses and von Mises stress for sigma_x=180, sigma_y=60, tau_xy=40 MPa.
Show the MATLAB code and the result.
```
Claude calls MATLAB directly, runs it, and reports back. First call boots MATLAB
(a few seconds).

## Useful server arguments

| Argument | Why you'd use it |
|---|---|
| `--matlab-root=<path>` | Pick which MATLAB to use (needed if not on PATH) |
| `--initial-working-folder=<path>` | Start MATLAB in your project folder |
| `--matlab-display-mode=nodesktop` | Don't pop the MATLAB desktop window |
| `--matlab-session-mode=existing` | Attach to an already-open MATLAB (run `shareMATLABSession()` in it first) |
| `--disable-telemetry=true` | Opt out of anonymized usage data |

## Even higher-level: the MATLAB Agentic Toolkit

MathWorks also ships the
[**MATLAB Agentic Toolkit**](https://github.com/matlab/matlab-agentic-toolkit),
which bundles a native Claude Code plugin *and can install this MCP server for
you*, plus task-specific skills for MATLAB/Simulink work. If you'd rather not do
Steps 1–2 by hand, that toolkit is the one-stop option.

## Troubleshooting

- **`claude mcp list` shows `Failed to connect`** → the binary path or
  `--matlab-root` is wrong. Test the binary's `--version` alone; check the root
  path exists and has no `\bin`.
- **Tools don't appear in a session** → restart Claude Code; MCP tools load at
  startup. Ask: *"List your MCP tools."*
- **Every call errors** → confirm MATLAB itself launches (open it once
  normally). Try `--matlab-display-mode=nodesktop`.
- **Remove it:** `claude mcp remove matlab -s local`.

## Which method should I actually use?

- **Just calculating?** Method 1 (Python, free) or Method 2 (Engine API) are
  simpler.
- **Want Claude to run MATLAB autonomously, check code style, run tests?** This
  MCP server is the most capable — that's what it's built for.

## Next step

→ [docs/07 — How to prompt Claude for engineering calcs](07-how-to-prompt-claude.md)
