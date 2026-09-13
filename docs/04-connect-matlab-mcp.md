# 04 — Method 3: MATLAB MCP server (advanced)

*Goal: let Claude Code call MATLAB **directly as a native tool**, without you
writing any Python glue. This is the most "AI-native" option but has the most
moving parts. **Requires a MATLAB license.***

## What is MCP?

**MCP (Model Context Protocol)** is a standard way to give AI tools new
abilities by running a small "server" the AI can call. An **MATLAB MCP server**
exposes MATLAB commands as tools Claude can invoke on its own — so Claude can run
MATLAB code the same way it runs its built-in tools, and read the results
(including figures) back automatically.

```
Claude Code ──(MCP tool call)──► MATLAB MCP server ──► MATLAB Engine ──► results/figures ──► Claude
```

Compared to Method 2 (Engine API): same underlying engine, but Claude calls
MATLAB *itself* instead of you/Claude writing a Python script each time.

## Prerequisites

- MATLAB installed + the **MATLAB Engine API for Python** working first — do
  [docs/03](03-connect-matlab-engine-api.md) and confirm the demo runs. The MCP
  server sits on top of it.
- **Python 3.10+** and `pip`.
- Claude Code installed ([docs/01](01-install-claude-code.md)).

## Step 1 — Pick and install a MATLAB MCP server

There are community MATLAB MCP servers on GitHub (search
"**matlab mcp server**"). They vary, so **read the specific project's README**
for exact install steps. A typical pattern:

```bash
# Example only — follow YOUR chosen server's README for the real command/name.
pip install matlab-mcp-server
```

Note the command that *starts* the server (each project documents this), e.g.:
```bash
matlab-mcp-server            # or:  python -m matlab_mcp_server
```

> ⚠️ MCP servers run with real permissions on your machine. Only install ones
> whose source you can read on GitHub and reasonably trust. Prefer projects with
> visible activity and stars.

## Step 2 — Register the server with Claude Code

Claude Code manages MCP servers with the `claude mcp` command. General shape
(replace the command/args with your server's real ones from Step 1):

```bash
claude mcp add matlab -- <command-that-starts-the-server> [args...]
```

For example, if the server starts with `python -m matlab_mcp_server`:
```bash
claude mcp add matlab -- python -m matlab_mcp_server
```

Check it registered:
```bash
claude mcp list
```

## Step 3 — Use it

Start Claude and confirm the tools are visible:
```
List your available MCP tools. Do you have MATLAB tools?
```
Then just ask for MATLAB work naturally:
```
Using the MATLAB MCP tools, solve the plastic collapse load of a fixed-fixed beam
under a central point load with plastic moment Mp = 40 kN·m and span L = 6 m.
Plot the bending moment diagram at collapse.
```
Claude will call MATLAB directly, run the analysis, and pull the figure back.

## Troubleshooting

- **`claude mcp list` doesn't show MATLAB** → the `add` command's start-command
  is wrong. Test that command by itself in a terminal first; it should launch
  and wait.
- **Tools appear but every call errors** → the underlying Engine API isn't
  working. Re-verify [docs/03](03-connect-matlab-engine-api.md) Step 2.
- **Too fiddly?** Method 2 (Engine API) gives 90% of the value with less setup,
  and the free Python path ([docs/05](05-python-sympy-fallback.md)) needs no
  MATLAB at all.

## Next step

→ [docs/07 — How to prompt Claude for engineering calcs](07-how-to-prompt-claude.md)
