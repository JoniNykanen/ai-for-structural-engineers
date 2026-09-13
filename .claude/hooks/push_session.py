#!/usr/bin/env python3
"""
push_session.py — auto-commit & push captured session data (SessionEnd hook).

Runs once when a session ends. Commits any changes under `solved/` and
`USAGE_LOG.md` and pushes them to origin — so the learning data reaches the repo
without a manual `git push`.

SAFETY: only acts if the opt-in marker `.claude/autopush.enabled` exists (it is
gitignored and per-machine). Without it this is a no-op, so cloners never push by
accident. Scoped to solved/ + USAGE_LOG.md only — never touches other working
changes. Stdlib only; never crashes the session.
"""

import sys
import os
import json
import subprocess


def repo_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def run(args, cwd, timeout=30):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                          timeout=timeout)


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}
    session_id = (data.get("session_id") or "unknown")[:8]

    root = repo_root()

    # Opt-in gate: do nothing unless this machine explicitly enabled autopush.
    if not os.path.exists(os.path.join(root, ".claude", "autopush.enabled")):
        return 0

    try:
        paths = ["solved", "USAGE_LOG.md"]
        # Any changes to capture?
        status = run(["git", "status", "--porcelain", "--"] + paths, root)
        if status.returncode != 0 or not status.stdout.strip():
            return 0

        run(["git", "add", "--"] + paths, root)
        msg = f"chore(auto): capture session {session_id}"
        commit = run(["git", "commit", "-m", msg], root)
        if commit.returncode != 0:
            return 0  # nothing to commit / hook not fatal

        # Push current branch to its upstream (origin). Best-effort.
        run(["git", "push"], root, timeout=60)
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
