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

> **Activation:** hooks load at session start. After cloning or first setup,
> restart Claude Code (or open `/hooks` once) so the hook registers.

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
- To pause capture: `/hooks` → disable, or set `"disableAllHooks": true` in
  `.claude/settings.local.json`.
- To prune: delete old `solved/*.md` you've already learned from; the log line
  can stay or go.
