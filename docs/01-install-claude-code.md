# 01 — Install Claude Code

*Goal: get the `claude` command working in your terminal. ~10 minutes.*

Claude Code is available as a terminal CLI, a desktop app (Windows/Mac), a web
app at claude.ai/code, and IDE extensions (VS Code, JetBrains). This guide covers
the **terminal CLI**, which is what this repo assumes.

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

## Handy things to know

- `/help` — list commands inside a session.
- `/clear` — start a fresh conversation (do this between unrelated problems to
  keep Claude focused and fast).
- Type `!` before a line to run a raw shell command (e.g. `! python --version`).

## Next step

→ [docs/02 — Set up Python (the calculation engine)](02-python-setup.md)
