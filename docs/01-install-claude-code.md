# 01 — Install Claude Code

*Goal: get the `claude` command working in your terminal. ~10 minutes.*

Claude Code is available as a terminal CLI, a desktop app (Windows/Mac), a web
app at claude.ai/code, and IDE extensions (VS Code, JetBrains). Steps 1–5 set up
the **terminal CLI**; if you prefer **VS Code** (a very common way to run Claude
Code), jump to [Using Claude Code in VS Code](#using-claude-code-in-vs-code) —
everything in this repo (tutor rules, MATLAB MCP tools, the learning-loop hooks)
works identically there.

## Step 1 — Open a terminal

- **Windows:** press `Win`, type **PowerShell**, open it.
- **macOS:** press `Cmd+Space`, type **Terminal**, open it.
- **Linux:** open your usual terminal.

## Step 2 — Install

The recommended installer (no Node.js required):

**macOS / Linux:**
```bash
curl -fsSL https://claude.ai/install.sh | bash
```

**Windows (PowerShell):**
```powershell
irm https://claude.ai/install.ps1 | iex
```

> Alternative if you already have Node.js 18+:
> `npm install -g @anthropic-ai/claude-code`
>
> Official install docs: <https://docs.anthropic.com/en/docs/claude-code/setup>

Close and reopen your terminal after installing so it picks up the new command.

## Step 3 — Sign in

Run:
```bash
claude
```
The first time, it opens your browser to log in with your Anthropic (Claude)
account. A **Claude Pro or Max** subscription, or **API credits**, is needed to
use it. Students: check whether your institution provides access.

## Step 4 — Verify it works

Inside the `claude` session, type:
```
What version are you and can you run Python?
```
If it responds, you're set.

To exit a session, type `/exit` or press `Ctrl+C` twice.

## Step 5 — Get this repo onto your computer

```bash
git clone https://github.com/JoniNykanen/matlab-claude-for-engineers.git
cd matlab-claude-for-engineers
claude
```
Starting `claude` from *inside* this folder means it automatically reads the
[`CLAUDE.md`](../CLAUDE.md) tutor instructions — Claude will show its working and
run every calculation.

## Using Claude Code in VS Code

VS Code is one of the most common ways to run Claude Code. Two options — pick
either:

### Option A — the Claude Code extension (GUI panel)

1. Open VS Code → **Extensions** (`Ctrl+Shift+X`) → search **"Claude Code"**
   (publisher **Anthropic**) → **Install**. Direct link:
   [Claude Code for VS Code (Marketplace)](https://marketplace.visualstudio.com/items?itemName=anthropic.claude-code).
2. **File → Open Folder…** and open the cloned `matlab-claude-for-engineers`
   folder. Opening it as the workspace is what makes Claude load this repo's
   [`CLAUDE.md`](../CLAUDE.md), MCP servers, skills, and hooks.
3. Open the Claude Code panel (click the Claude icon in the sidebar, or
   `Ctrl+Shift+P` → **"Claude Code: Focus"**). Sign in when prompted (same
   Claude Pro/Max or API account as the CLI).
4. Ask a question in the panel — Claude shows diffs and results inside the editor.

### Option B — the integrated terminal

If you installed the CLI (Steps 1–3), just open VS Code's terminal
(`Ctrl+` `` ` ``), `cd` into the repo, and run `claude`. It detects VS Code and
shows diffs in the editor. Nothing extra to install.

### Activating changes in VS Code (important)

Hooks, MCP servers, and skills load when a Claude session **starts**. After
running `setup.ps1`/`setup.sh` or installing anything, refresh so VS Code picks
it up:

- `Ctrl+Shift+P` → **"Developer: Reload Window"**, then start a new Claude session, **or**
- restart VS Code.

You do **not** need to reinstall anything — just reload. Verify with (works
without MATLAB):
```
Using the repo's Python (.venv), compute the von Mises stress for pure shear
τ = 100 MPa and check it equals √3·τ ≈ 173.2 MPa. Show the code you ran.
```
If you also set up MATLAB, you can additionally ask: *"List your MATLAB MCP
tools and run detect_matlab_toolboxes."*

> **Which should I use?** The extension is friendlier for beginners (buttons,
> inline diffs); the terminal CLI is identical in capability. Both read the same
> config, so the MATLAB connection and the learning loop behave the same way.

## Handy things to know

- `/help` — list commands inside a session.
- `/clear` — start a fresh conversation (do this between unrelated problems to
  keep Claude focused and fast).
- Type `!` before a line to run a raw shell command (e.g. `! python --version`).

## Official links

- Claude Code docs (home): <https://docs.anthropic.com/en/docs/claude-code>
- Install / setup: <https://docs.anthropic.com/en/docs/claude-code/setup>
- Use Claude Code in VS Code (IDE integrations): <https://docs.anthropic.com/en/docs/claude-code/ide-integrations>
- Claude Code for VS Code (Marketplace extension): <https://marketplace.visualstudio.com/items?itemName=anthropic.claude-code>
- Web app: <https://claude.ai/code>

## Next step

→ [docs/02 — Set up Python (the calculation engine)](02-python-setup.md)
