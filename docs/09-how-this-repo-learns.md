# 09 — How this repo learns from usage

*The automatic feedback loop that makes the kit better the more you use it.*

## The core idea

Claude doesn't remember anything between sessions on its own. It only "knows"
what's written in the files it reads at startup (`CLAUDE.md`, skills). So
"learning from usage" is a concrete loop:

```
  ┌─────────────┐     ┌──────────────┐     ┌────────────────────────────┐
  │  1. CAPTURE │ ──► │  2. REVIEW   │ ──► │  3. CODIFY                 │
  │ (automatic) │     │  (weekly,    │     │  write the lesson into     │
  │  every      │     │   ~10 min)   │     │  CLAUDE.md / a new example │
  │  session    │     │              │     │  / a new skill             │
  └─────────────┘     └──────────────┘     └────────────────────────────┘
        ▲                                                    │
        └────────────────────────────────────────────────────┘
                    next session is smarter
```

## 1. Capture — automatic (already set up)

A **Stop hook** (`.claude/hooks/capture_session.py`, configured in
`.claude/settings.json`) runs after every turn and writes each session's
question/solution pairs to `solved/YYYY-MM-DD_<session>.md`, indexed in
`USAGE_LOG.md`. Stdlib-only Python, never blocks your session. You do nothing —
it just accumulates.

What the capture does for you:

- **Redacts secrets before writing.** API keys (`sk-…`, `ghp_…`, `AKIA…`, …),
  bearer tokens, JWTs, private-key blocks, `password=…` / `token: …` style
  values and email addresses are replaced with `[REDACTED]` /
  `[REDACTED_EMAIL]`. This is a safety net for *obvious* patterns, not a
  guarantee — still don't paste real credentials into a session.
- **Caps the file size.** Each session file is capped at ~200 KB; anything past
  that is cut and a "Truncated" note is added at the end.
- **Is idempotent.** It runs every turn but keeps exactly one file and one
  `USAGE_LOG.md` line per session.
- **Finds Python on any OS.** The hook tries the repo `.venv` first, then
  `python3`, `python` and `py`, and runs the script exactly once.
- **Logs its own errors.** Failures never interrupt you; they are appended to
  `.claude/hooks/hook_errors.log` (gitignored). If `solved/` stops filling up,
  look there first.

> **Activation:** hooks load at session start. After cloning or first setup,
> restart Claude Code (or open `/hooks` once) so the hook registers.

### Opt out of capture on this machine

Create the (gitignored) marker file `.claude/capture.disabled`:

```bash
echo disabled > .claude/capture.disabled      # macOS/Linux/Git Bash
```
```powershell
Set-Content .claude\capture.disabled disabled  # Windows PowerShell
```

While it exists, **both** hooks do nothing: no `solved/` file, no
`USAGE_LOG.md` line, no commit, no push — even if auto-push is enabled. Delete
the file to turn capture back on.

### Optional: auto-push the data to the repo

By default, captured sessions stay **local** — the data reaches the private repo
only when you `git push`. To automate that, a **`SessionEnd` hook**
(`.claude/hooks/push_session.py`) commits `solved/` + `USAGE_LOG.md` and pushes
them once per session.

It's **opt-in per machine** for safety (so a cloner never pushes by accident): it
only runs if the file `.claude/autopush.enabled` exists (gitignored). Enable it:

```bash
# via the setup script
./setup.ps1 -EnableAutoPush        # Windows
bash setup.sh --autopush           # macOS/Linux
# …or by hand
echo enabled > .claude/autopush.enabled
```

Disable by deleting that file. What the push will and won't do:

- **Commits only `solved/` + `USAGE_LOG.md`** (explicit pathspec). Anything else
  you had staged stays staged and is *not* included in the auto-commit.
- **Never pushes your own commits.** If your branch already has unpushed
  commits of yours, the capture is committed locally but not pushed — run
  `git push` yourself when you're ready.
- **Syncs before pushing.** If the remote moved on (e.g. another machine pushed
  its sessions), it runs `git pull --rebase --autostash` first, merging
  `USAGE_LOG.md` line by line so two machines' log lines don't conflict.
- **Skips safely** on a detached HEAD or during a merge/rebase, and never waits
  for a password prompt.
- **Reports failures** (no upstream, rejected push, rebase conflict, timeout)
  in `.claude/hooks/hook_errors.log`. The local commit is kept, so the next
  session — or a manual `git push` — delivers it.

## 2. Review — weekly, ~10 minutes

Once a week, start Claude in the repo and ask:

```
Read USAGE_LOG.md and the recent files in solved/. What patterns do you see —
questions I ask repeatedly, mistakes that recur, or workflows that would be
worth turning into a reusable example or rule? Propose concrete additions to
CLAUDE.md, a new file in examples/, or a new skill.
```

## 3. Codify — turn lessons into durable knowledge

Promote what you learned into the files Claude reads next time:

| Pattern you noticed | Where it goes |
|---|---|
| A preference or recurring correction ("always show units") | a rule in **`CLAUDE.md`** |
| A problem type you solve often | a new worked file in **`examples/`** |
| A multi-step workflow that repeats | a **custom skill** (`npx skills init`, or the `skill-creator` skill) |
| A tool/toolbox tip | **`docs/08`** |

Record notable changes in `CHANGELOG.md`.

## Why this works with one user

No CI, no contributors, no automation to babysit — just one hook plus a 10-minute
weekly habit. The `solved/` archive is your searchable history; `CLAUDE.md` is
the distilled intelligence. Over a semester, the kit genuinely adapts to *how you
work*.

## Housekeeping

- `solved/` grows over time. It's committed (your knowledge base), but the repo
  is **private** — keep it private if sessions contain anything sensitive.
- To pause capture: create `.claude/capture.disabled` (see "Opt out" above).
  `/hooks` → disable, or `"disableAllHooks": true` in
  `.claude/settings.local.json`, also work but turn off *all* hooks.
- To prune: delete old `solved/*.md` you've already learned from; the log line
  can stay or go.
