#!/usr/bin/env python3
"""
capture_session.py — automatic session capture for the learning loop.

Runs as a Claude Code **Stop hook**. On each assistant turn it reads the hook
JSON from stdin, parses the session transcript, and writes a clean
question/solution markdown file into `solved/`, plus a one-line index entry in
`USAGE_LOG.md`. Idempotent per session (safe to run every turn).

Stdlib only — no venv or packages required. Never crashes the session: any
error is swallowed and the hook exits 0.

See docs/09-how-this-repo-learns.md for the full loop.
"""

import sys
import os
import re
import json
from datetime import datetime, timezone


def repo_root():
    # This file lives at <repo>/.claude/hooks/capture_session.py
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def strip_system_reminders(text):
    return re.sub(r"<system-reminder>.*?</system-reminder>", "",
                  text, flags=re.DOTALL).strip()


def extract_text(content):
    """Return plain text from a transcript message's `content` (str or list)."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "\n".join(p for p in parts if p).strip()
    return ""


def is_tool_only_user(content):
    """True if a user entry is only tool results (not a real question)."""
    if isinstance(content, list):
        types = {b.get("type") for b in content if isinstance(b, dict)}
        return types and types.issubset({"tool_result"})
    return False


def parse_transcript(path):
    """Return (turns, first_ts) where turns is a list of ('You'|'Claude', text)."""
    turns = []
    first_ts = None
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            etype = entry.get("type")
            if etype not in ("user", "assistant"):
                continue
            if first_ts is None and entry.get("timestamp"):
                first_ts = entry["timestamp"]
            msg = entry.get("message") or {}
            content = msg.get("content", "")
            if etype == "user":
                if is_tool_only_user(content):
                    continue
                text = strip_system_reminders(extract_text(content))
                if text:
                    turns.append(("You", text))
            else:  # assistant
                text = extract_text(content)
                if text:
                    turns.append(("Claude", text))
    return turns, first_ts


def date_from(first_ts):
    if first_ts:
        try:
            return datetime.fromisoformat(
                first_ts.replace("Z", "+00:00")).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def render_markdown(turns, session_id, date_str):
    lines = [f"# Session {session_id[:8]} — {date_str}", ""]
    lines.append("_Auto-captured by the Stop hook (see docs/09). "
                 "Review periodically and promote recurring lessons into "
                 "CLAUDE.md or a new example._")
    lines.append("")
    turn_no = 0
    for role, text in turns:
        if role == "You":
            turn_no += 1
            lines.append(f"## Turn {turn_no}")
            lines.append(f"**You:** {text}")
            lines.append("")
        else:
            lines.append(f"**Claude:** {text}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def update_usage_log(root, session_id, date_str, n_turns, rel_path):
    log = os.path.join(root, "USAGE_LOG.md")
    header = ("# Usage log\n\n_One line per captured session. Auto-maintained "
              "by the Stop hook; see docs/09._\n\n")
    existing = ""
    if os.path.exists(log):
        with open(log, "r", encoding="utf-8", errors="replace") as f:
            existing = f.read()
    else:
        existing = header
    # Dedup: one entry per session_id.
    if session_id[:8] in existing and rel_path in existing:
        # Update the count on the existing line (turns may have grown).
        pattern = re.compile(r"^- .*session " + re.escape(session_id[:8]) +
                             r".*$", re.MULTILINE)
        new_line = (f"- {date_str} — session {session_id[:8]} — "
                    f"{n_turns} turns — [{rel_path}]({rel_path})")
        existing = pattern.sub(new_line, existing)
    else:
        if not existing.endswith("\n"):
            existing += "\n"
        existing += (f"- {date_str} — session {session_id[:8]} — "
                     f"{n_turns} turns — [{rel_path}]({rel_path})\n")
    with open(log, "w", encoding="utf-8") as f:
        f.write(existing)


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0

    transcript_path = data.get("transcript_path")
    session_id = data.get("session_id") or "unknown"
    if not transcript_path or not os.path.exists(transcript_path):
        return 0

    try:
        turns, first_ts = parse_transcript(transcript_path)
        if not turns:
            return 0
        date_str = date_from(first_ts)
        root = repo_root()
        solved_dir = os.path.join(root, "solved")
        os.makedirs(solved_dir, exist_ok=True)

        fname = f"{date_str}_{session_id[:8]}.md"
        rel_path = f"solved/{fname}"
        with open(os.path.join(solved_dir, fname), "w", encoding="utf-8") as f:
            f.write(render_markdown(turns, session_id, date_str))

        n_turns = sum(1 for r, _ in turns if r == "You")
        update_usage_log(root, session_id, date_str, n_turns, rel_path)
    except Exception:
        # Never break the session over a logging failure.
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
