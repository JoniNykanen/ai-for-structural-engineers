#!/usr/bin/env python3
"""
capture_session.py — automatic session capture for the learning loop.

Runs as a Claude Code **Stop hook**. On each assistant turn it reads the hook
JSON from stdin, parses the session transcript, and writes a clean
question/solution markdown file into `solved/`, plus a one-line index entry in
`USAGE_LOG.md`.

Guarantees:
- Opt-out: does nothing if `.claude/capture.disabled` exists (gitignored).
- Privacy: obvious secrets (API keys, tokens, `password=...`, private keys) and
  email addresses are redacted BEFORE anything is written to disk.
- Size cap: each session file is capped at MAX_SESSION_BYTES, truncated with a
  note.
- Idempotent: one file + one log line per session; re-running rewrites the same
  content (and skips the write when nothing changed). Writes are atomic.
- Stdlib only. Always exits 0; errors are appended to
  `.claude/hooks/hook_errors.log` (gitignored) instead of being swallowed.

See docs/09-how-this-repo-learns.md for the full loop.
"""

import sys
import os
import re
import json
import tempfile
import traceback
from datetime import datetime, timezone

# Per-session markdown cap (bytes, UTF-8). Long sessions are truncated with a note.
MAX_SESSION_BYTES = 200 * 1024
# hook_errors.log is trimmed to its newest half once it grows past this.
MAX_ERROR_LOG_BYTES = 256 * 1024

REDACTED = "[REDACTED]"


def repo_root():
    # This file lives at <repo>/.claude/hooks/capture_session.py
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def capture_disabled(root):
    return os.path.exists(os.path.join(root, ".claude", "capture.disabled"))


def log_error(root, where, exc=None):
    """Append an error to .claude/hooks/hook_errors.log. Never raises."""
    try:
        path = os.path.join(root, ".claude", "hooks", "hook_errors.log")
        if os.path.exists(path) and os.path.getsize(path) > MAX_ERROR_LOG_BYTES:
            with open(path, "rb") as f:
                f.seek(-MAX_ERROR_LOG_BYTES // 2, os.SEEK_END)
                tail = f.read()
            with open(path, "wb") as f:
                f.write(tail)
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        detail = traceback.format_exc() if exc is not None else ""
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"[{stamp}] capture_session: {where}\n")
            if detail and detail.strip() != "NoneType: None":
                f.write(detail.rstrip() + "\n")
    except Exception:
        pass


# --- Redaction ---------------------------------------------------------------

_SECRET_PATTERNS = [
    # PEM private key blocks
    re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?"
               r"-----END [A-Z0-9 ]*PRIVATE KEY-----", re.DOTALL),
    # OpenAI / Anthropic style keys (sk-..., sk-ant-..., sk-proj-...)
    re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}"),
    # GitHub tokens
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"),
    # AWS access key ids
    re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    # Slack tokens
    re.compile(r"\bxox[abposr]-[A-Za-z0-9\-]{10,}"),
    # Google API keys
    re.compile(r"\bAIza[0-9A-Za-z_\-]{35}"),
    # JSON Web Tokens
    re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}"),
]

# Authorization: Bearer <token>
_BEARER = re.compile(r"(?i)(\bbearer\s+)[A-Za-z0-9\-._~+/]{12,}=*")

# key=value / key: value where the key name looks secret-bearing, e.g.
# password=hunter2, OPENAI_API_KEY="...", "client_secret": "...", token: abc
_KEY_VALUE = re.compile(
    r"(?i)(\b[\w.\-]*(?:password|passwd|secret|token|api[_\-]?key|apikey|"
    r"access[_\-]?key|private[_\-]?key|auth[_\-]?key|credentials?)[\w.\-]*"
    r"[\"']?\s*[:=]\s*)"
    r"(?:\"([^\"\n]{4,})\"|'([^'\n]{4,})'|([^\s\"',;]{4,}))")

_EMAIL = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*"
                    r"\.[A-Za-z]{2,}\b")


def redact(text):
    """Mask obvious secrets and email addresses. Idempotent."""
    for pat in _SECRET_PATTERNS:
        text = pat.sub(REDACTED, text)
    text = _BEARER.sub(lambda m: m.group(1) + REDACTED, text)

    def _kv(m):
        value = m.group(2) or m.group(3) or m.group(4) or ""
        if value.startswith("[REDACTED"):
            return m.group(0)
        quote = '"' if m.group(2) else ("'" if m.group(3) else "")
        return m.group(1) + quote + REDACTED + quote

    text = _KEY_VALUE.sub(_kv, text)
    text = _EMAIL.sub("[REDACTED_EMAIL]", text)
    return text


# --- Transcript parsing --------------------------------------------------------

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
        return bool(types) and types.issubset({"tool_result"})
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
            if not isinstance(entry, dict):
                continue
            etype = entry.get("type")
            if etype not in ("user", "assistant"):
                continue
            if first_ts is None and entry.get("timestamp"):
                first_ts = entry["timestamp"]
            msg = entry.get("message") or {}
            content = msg.get("content", "") if isinstance(msg, dict) else ""
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


def safe_session_id(session_id):
    """Session ids end up in file names: keep them filename-safe."""
    return re.sub(r"[^A-Za-z0-9_\-]", "", session_id or "")[:8] or "unknown"


def render_markdown(turns, sid, date_str):
    lines = [f"# Session {sid} — {date_str}", ""]
    lines.append("_Auto-captured by the Stop hook (see docs/09). Secrets and "
                 "emails are redacted automatically. Review periodically and "
                 "promote recurring lessons into CLAUDE.md or a new example._")
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


def cap_size(md, max_bytes=MAX_SESSION_BYTES):
    """Truncate markdown to max_bytes (UTF-8) at a line boundary, with a note."""
    data = md.encode("utf-8")
    if len(data) <= max_bytes:
        return md
    note = (f"\n\n---\n_[Truncated: this session's capture exceeded "
            f"{max_bytes // 1024} KB ({len(data) // 1024} KB total). "
            f"The rest was not saved.]_\n")
    budget = max_bytes - len(note.encode("utf-8"))
    head = data[:max(budget, 0)].decode("utf-8", errors="ignore")
    cut = head.rfind("\n")
    if cut > 0:
        head = head[:cut]
    return head.rstrip() + note


def write_if_changed(path, text):
    """Atomic write; skip when the file already has exactly this content."""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8", newline="") as f:
                if f.read() == text:
                    return False
        except OSError:
            pass
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(prefix=".tmp_", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return True


def update_usage_log(root, sid, date_str, n_turns, rel_path):
    log = os.path.join(root, "USAGE_LOG.md")
    header = ("# Usage log\n\n_One line per captured session. Auto-maintained "
              "by the Stop hook; see docs/09._\n\n")
    if os.path.exists(log):
        with open(log, "r", encoding="utf-8", errors="replace", newline="") as f:
            existing = f.read()
    else:
        existing = header
    new_line = (f"- {date_str} — session {sid} — "
                f"{n_turns} turns — [{rel_path}]({rel_path})")
    # Dedup: one entry per session (turn count is refreshed in place).
    pattern = re.compile(r"^- .*session " + re.escape(sid) + r"\b.*$",
                         re.MULTILINE)
    if pattern.search(existing):
        updated = pattern.sub(lambda _m: new_line, existing, count=1)
    else:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        updated = existing + new_line + "\n"
    write_if_changed(log, updated)


def capture(data, root):
    transcript_path = data.get("transcript_path")
    if not transcript_path or not os.path.exists(transcript_path):
        return
    sid = safe_session_id(data.get("session_id") or "unknown")

    turns, first_ts = parse_transcript(transcript_path)
    if not turns:
        return
    date_str = date_from(first_ts)
    solved_dir = os.path.join(root, "solved")
    os.makedirs(solved_dir, exist_ok=True)

    fname = f"{date_str}_{sid}.md"
    rel_path = f"solved/{fname}"
    # Redact BEFORE anything touches disk, then cap the size.
    md = cap_size(redact(render_markdown(turns, sid, date_str)))
    write_if_changed(os.path.join(solved_dir, fname), md)

    n_turns = sum(1 for r, _ in turns if r == "You")
    update_usage_log(root, sid, date_str, n_turns, rel_path)


def main():
    root = repo_root()
    try:
        raw = sys.stdin.read()
    except Exception:
        raw = ""
    if capture_disabled(root):
        return 0
    try:
        data = json.loads(raw) if raw.strip() else {}
        if not isinstance(data, dict):
            data = {}
    except Exception:
        log_error(root, "could not parse hook JSON from stdin", exc=True)
        return 0
    try:
        capture(data, root)
    except Exception:
        # Never break the session over a logging failure — but leave a trace.
        log_error(root, "capture failed", exc=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException:
        sys.exit(0)
