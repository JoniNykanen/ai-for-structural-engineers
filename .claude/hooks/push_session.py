#!/usr/bin/env python3
"""
push_session.py — auto-commit & push captured session data (SessionEnd hook).

Runs once when a session ends. Commits the changes under `solved/` and
`USAGE_LOG.md` and pushes them to the branch's upstream — so the learning data
reaches the repo without a manual `git push`.

SAFETY:
- Opt-in: only acts if `.claude/autopush.enabled` exists (gitignored,
  per-machine). Without it this is a no-op, so cloners never push by accident.
- Opt-out wins: if `.claude/capture.disabled` exists, nothing happens at all.
- Scoped: the commit uses an explicit pathspec (`git commit -- solved
  USAGE_LOG.md`), so anything else you had staged stays staged and is NOT
  committed. Other working changes are never committed.
- Never pushes your own work: if the branch already had unpushed commits of
  yours, the capture is committed locally but not pushed (push those yourself).
- Before pushing it rebases ONLY its own capture commit onto the upstream
  (`git pull --rebase --autostash`; USAGE_LOG.md is merged line-wise), so a
  shared USAGE_LOG.md doesn't make the push fail.
- Stdlib only. Always exits 0; failures are appended to
  `.claude/hooks/hook_errors.log` (gitignored) instead of being swallowed.
"""

import sys
import os
import json
import tempfile
import subprocess
import traceback
from datetime import datetime, timezone

CAPTURE_PATHS = ["solved", "USAGE_LOG.md"]
MAX_ERROR_LOG_BYTES = 256 * 1024


def repo_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def log_error(root, message, exc=False):
    """Append a line to .claude/hooks/hook_errors.log. Never raises."""
    try:
        path = os.path.join(root, ".claude", "hooks", "hook_errors.log")
        if os.path.exists(path) and os.path.getsize(path) > MAX_ERROR_LOG_BYTES:
            with open(path, "rb") as f:
                f.seek(-MAX_ERROR_LOG_BYTES // 2, os.SEEK_END)
                tail = f.read()
            with open(path, "wb") as f:
                f.write(tail)
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"[{stamp}] push_session: {message.rstrip()}\n")
            if exc:
                f.write(traceback.format_exc().rstrip() + "\n")
    except Exception:
        pass


class GitError(Exception):
    pass


def run(args, cwd, timeout=30, check=True):
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"   # never hang on a credential prompt
    env.setdefault("GIT_EDITOR", "true")  # never open an editor (rebase)
    proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                          timeout=timeout, env=env, stdin=subprocess.DEVNULL)
    if check and proc.returncode != 0:
        raise GitError(f"`{' '.join(args)}` failed (exit {proc.returncode}): "
                       f"{(proc.stderr or proc.stdout).strip()}")
    return proc


def git_path_exists(root, name):
    p = run(["git", "rev-parse", "--git-path", name], root).stdout.strip()
    return os.path.exists(p if os.path.isabs(p) else os.path.join(root, p))


def repo_busy(root):
    """True if a merge/rebase/cherry-pick is in progress — don't interfere."""
    return any(git_path_exists(root, n) for n in
               ("MERGE_HEAD", "rebase-merge", "rebase-apply",
                "CHERRY_PICK_HEAD", "REVERT_HEAD"))


def commit_capture(root, session_id):
    """Commit ONLY the capture paths. Returns True if a commit was made."""
    status = run(["git", "status", "--porcelain", "--untracked-files=all",
                  "--"] + CAPTURE_PATHS, root)
    if not status.stdout.strip():
        return False
    # Pathspecs git knows about: on disk, or tracked (e.g. a deleted file).
    paths = [p for p in CAPTURE_PATHS
             if os.path.exists(os.path.join(root, p))
             or run(["git", "ls-files", "--", p], root).stdout.strip()]
    if not paths:
        return False
    # Stage new/changed/deleted capture files so the pathspec commit sees them.
    run(["git", "add", "-A", "--"] + paths, root)
    msg = f"chore(auto): capture session {session_id}"
    # `--only` + pathspec: commit just these paths; anything else the user had
    # staged is left staged and is NOT part of this commit.
    run(["git", "commit", "--quiet", "--only", "-m", msg, "--"] + paths, root)
    return True


def pull_rebase(root):
    """Rebase our capture commit onto upstream; USAGE_LOG.md merges by union."""
    fd, attrs = tempfile.mkstemp(prefix="capture_attrs_", text=True)
    try:
        with os.fdopen(fd, "w") as f:
            f.write("USAGE_LOG.md merge=union\n")
        proc = run(["git", "-c", f"core.attributesFile={attrs}",
                    "pull", "--rebase", "--autostash", "--quiet"],
                   root, timeout=25, check=False)
        if proc.returncode != 0:
            if git_path_exists(root, "rebase-merge") or \
                    git_path_exists(root, "rebase-apply"):
                run(["git", "rebase", "--abort"], root, check=False)
            raise GitError("pull --rebase failed, local capture commit kept "
                           "(push it manually): "
                           + (proc.stderr or proc.stdout).strip())
        out = (proc.stderr or "") + (proc.stdout or "")
        if "autostash" in out.lower() and "conflict" in out.lower():
            log_error(root, "autostash could not be re-applied cleanly; your "
                      "changes are safe in `git stash list`: " + out.strip())
    finally:
        try:
            os.remove(attrs)
        except OSError:
            pass


def push(root):
    # Upstream configured?
    up = run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name",
              "@{u}"], root, check=False)
    if up.returncode != 0:
        log_error(root, "no upstream branch configured; capture committed "
                  "locally but not pushed")
        return
    run(["git", "fetch", "--quiet"], root, timeout=20)
    behind = int(run(["git", "rev-list", "--count", "HEAD..@{u}"],
                     root).stdout.strip() or 0)
    if behind:
        pull_rebase(root)
    run(["git", "push", "--quiet"], root, timeout=30)


def main():
    root = repo_root()
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}
    session_id = "".join(c for c in str(data.get("session_id") or "unknown")
                         if c.isalnum() or c in "-_")[:8] or "unknown"

    # Opt-out wins over everything.
    if os.path.exists(os.path.join(root, ".claude", "capture.disabled")):
        return 0
    # Opt-in gate: do nothing unless this machine explicitly enabled autopush.
    if not os.path.exists(os.path.join(root, ".claude", "autopush.enabled")):
        return 0

    try:
        if run(["git", "rev-parse", "--is-inside-work-tree"], root,
               check=False).returncode != 0:
            log_error(root, "not a git work tree; nothing pushed")
            return 0
        if run(["git", "symbolic-ref", "-q", "HEAD"], root,
               check=False).returncode != 0:
            log_error(root, "detached HEAD; skipped auto-commit")
            return 0
        if repo_busy(root):
            log_error(root, "merge/rebase in progress; skipped auto-commit")
            return 0

        # Count the user's own unpushed commits BEFORE we add ours.
        ahead = run(["git", "rev-list", "--count", "@{u}..HEAD"], root,
                    check=False)
        user_unpushed = (int(ahead.stdout.strip() or 0)
                         if ahead.returncode == 0 else 0)

        if not commit_capture(root, session_id):
            return 0
        if user_unpushed:
            log_error(root, f"branch already had {user_unpushed} unpushed "
                      "commit(s) of yours; capture committed locally but not "
                      "pushed (run `git push` yourself)")
            return 0
        push(root)
    except subprocess.TimeoutExpired as e:
        log_error(root, f"git timed out: {e}")
    except GitError as e:
        log_error(root, str(e))
    except Exception:
        log_error(root, "unexpected error", exc=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException:
        sys.exit(0)
