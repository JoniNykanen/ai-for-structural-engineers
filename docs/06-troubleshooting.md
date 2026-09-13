# 06 — Troubleshooting

Common problems, in the order beginners usually hit them.

## Claude Code

**`claude: command not found`**
The install didn't add it to your PATH, or you didn't reopen the terminal.
Close every terminal window, open a new one, try again. Re-run the installer from
[docs/01](01-install-claude-code.md) if needed.

**Claude answers but won't run code / do calculations**
Make sure you started `claude` from *inside* the repo folder so it reads
[`CLAUDE.md`](../CLAUDE.md). Explicitly ask: *"Run this in Python and show the
output,"* not just *"what's the answer?"*

## Python

**`python: command not found` (or opens the Microsoft Store on Windows)**
Python isn't installed or wasn't added to PATH. Reinstall from python.org and
tick **"Add python.exe to PATH"**. On Windows, `py` sometimes works when
`python` doesn't.

**`ModuleNotFoundError: No module named 'numpy'` (or sympy, scipy, matplotlib)**
The libraries aren't installed in the environment you're using. Activate the
virtual environment, then `pip install -r requirements.txt`:
```bash
# Windows:  .\.venv\Scripts\Activate.ps1
# mac/linux: source .venv/bin/activate
pip install -r requirements.txt
```

**PowerShell won't run the `Activate.ps1` script**
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```
Then try activating again.

**A plot doesn't pop up**
The examples *save* figures to files (e.g. a `.png`) rather than opening a
window, which is more reliable. Check the folder the script printed, or ask
Claude to open/show the saved image.

## MATLAB Engine API (Method 2)

**`No module named 'matlab'`**
Engine not installed in the active environment. Re-activate `.venv` and reinstall
(see [docs/03](03-connect-matlab-engine-api.md) Step 1).

**Version mismatch on install**
`pip install matlabengine` grabbed a version that doesn't match your MATLAB
release. Pin it: `pip install matlabengine==24.2.*` (match your release from the
table in docs/03).

**`start_matlab()` is very slow**
First launch boots MATLAB — expect several seconds. Don't start a new engine per
calculation; keep one `eng` alive and reuse it.

## MATLAB MCP server (Method 3)

**`claude mcp list` doesn't show the server**
The start-command you registered is wrong. Run that exact command alone in a
terminal — it should launch and wait. Fix it, then `claude mcp remove matlab`
and add it again.

**Tools show up but error on every call**
The MCP server sits on top of the Engine API. Verify Method 2's demo runs first
([docs/03](03-connect-matlab-engine-api.md) Step 2).

## Still stuck?

Ask Claude directly — paste the *exact* error text. Include: your OS, whether the
virtual environment is active, and which method (1/2/3) you're on. Precise error
text gets a precise fix.
