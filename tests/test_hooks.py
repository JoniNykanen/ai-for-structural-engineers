"""Tests for the learning-loop hooks in .claude/hooks/.

Every test builds a throwaway git repo (plus a bare "remote") under pytest's
tmp_path, copies the hook scripts into it and runs them the way Claude Code
does: as a subprocess with the hook JSON on stdin. The real repo is never
touched. Works on Windows and Linux/macOS.

    .venv\\Scripts\\python.exe -m pytest tests/test_hooks.py
"""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
HOOKS = REPO / ".claude" / "hooks"
SETTINGS = REPO / ".claude" / "settings.json"


# --- helpers -------------------------------------------------------------------

@pytest.fixture(autouse=True)
def isolated_git(tmp_path, monkeypatch):
    """Keep the user's global/system git config (signing, hooks, autocrlf) out."""
    cfg = tmp_path / "gitconfig"
    cfg.write_text("[user]\n\tname = Test\n\temail = test@example.invalid\n"
                   "[commit]\n\tgpgsign = false\n"
                   "[init]\n\tdefaultBranch = main\n"
                   "[core]\n\tautocrlf = false\n", encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(cfg))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.delenv("GIT_DIR", raising=False)
    monkeypatch.delenv("GIT_WORK_TREE", raising=False)


def git(cwd, *args):
    p = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    assert p.returncode == 0, f"git {args} failed: {p.stderr}"
    return p.stdout.strip()


def make_repo(tmp_path, with_remote=True):
    """A repo with the hooks installed and (optionally) a pushed upstream."""
    root = tmp_path / "repo"
    (root / ".claude" / "hooks").mkdir(parents=True)
    for name in ("capture_session.py", "push_session.py"):
        shutil.copy(HOOKS / name, root / ".claude" / "hooks" / name)
    git(tmp_path, "init", "-q", str(root))
    (root / ".gitignore").write_text(
        ".claude/autopush.enabled\n.claude/capture.disabled\n"
        ".claude/hooks/hook_errors.log\n__pycache__/\n", encoding="utf-8")
    (root / "README.md").write_text("hello\n", encoding="utf-8")
    (root / "USAGE_LOG.md").write_text("# Usage log\n\n", encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "init")
    if with_remote:
        remote = tmp_path / "remote.git"
        git(tmp_path, "init", "-q", "--bare", str(remote))
        git(root, "remote", "add", "origin", str(remote))
        git(root, "push", "-q", "-u", "origin", "main")
    return root


def run_hook(root, name, payload):
    p = subprocess.run([sys.executable, str(root / ".claude" / "hooks" / name)],
                       input=json.dumps(payload), capture_output=True,
                       text=True, cwd=root, timeout=120)
    assert p.returncode == 0, p.stderr
    return p


def write_transcript(path, turns):
    """turns: list of (role, text) with role 'user' or 'assistant'."""
    with open(path, "w", encoding="utf-8") as f:
        for i, (role, text) in enumerate(turns):
            f.write(json.dumps({
                "type": role,
                "timestamp": f"2026-10-03T12:00:{i:02d}Z",
                "message": {"role": role,
                            "content": [{"type": "text", "text": text}]},
            }) + "\n")
    return path


def load_capture_module():
    spec = importlib.util.spec_from_file_location(
        "capture_session", HOOKS / "capture_session.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SID = "abcd1234-0000-0000-0000-000000000000"


def capture_payload(transcript):
    return {"session_id": SID, "transcript_path": str(transcript),
            "hook_event_name": "Stop"}


def error_log(root):
    p = root / ".claude" / "hooks" / "hook_errors.log"
    return p.read_text(encoding="utf-8") if p.exists() else ""


# --- push_session --------------------------------------------------------------

def test_push_commits_only_captured_paths(tmp_path):
    root = make_repo(tmp_path)
    (root / ".claude" / "autopush.enabled").write_text("on", encoding="utf-8")
    # User work: one staged unrelated file, one unstaged edit.
    (root / "notes.txt").write_text("my private draft\n", encoding="utf-8")
    git(root, "add", "notes.txt")
    (root / "README.md").write_text("hello, edited\n", encoding="utf-8")
    # Captured data.
    (root / "solved").mkdir()
    (root / "solved" / "2026-10-03_abcd1234.md").write_text("# s\n",
                                                            encoding="utf-8")
    with open(root / "USAGE_LOG.md", "a", encoding="utf-8") as f:
        f.write("- line\n")

    run_hook(root, "push_session.py", {"session_id": SID})

    committed = set(git(root, "show", "--name-only", "--pretty=format:",
                        "HEAD").split())
    assert committed == {"solved/2026-10-03_abcd1234.md", "USAGE_LOG.md"}
    assert "capture session abcd1234" in git(root, "log", "-1", "--pretty=%s")
    # User's staged file is still staged (not committed), edit still unstaged.
    assert git(root, "diff", "--cached", "--name-only") == "notes.txt"
    assert git(root, "diff", "--name-only") == "README.md"
    # Pushed.
    assert git(root, "rev-parse", "HEAD") == git(root, "rev-parse", "origin/main")
    assert error_log(root) == ""


def test_push_rebases_onto_moved_upstream_and_merges_usage_log(tmp_path):
    root = make_repo(tmp_path)
    (root / ".claude" / "autopush.enabled").write_text("on", encoding="utf-8")
    # Another machine appends to USAGE_LOG.md and pushes first.
    other = tmp_path / "other"
    git(tmp_path, "clone", "-q", str(tmp_path / "remote.git"), str(other))
    with open(other / "USAGE_LOG.md", "a", encoding="utf-8") as f:
        f.write("- from other machine\n")
    git(other, "commit", "-q", "-am", "other session")
    git(other, "push", "-q")
    # This machine captured a session; user also has a staged file.
    with open(root / "USAGE_LOG.md", "a", encoding="utf-8") as f:
        f.write("- from this machine\n")
    (root / "notes.txt").write_text("draft\n", encoding="utf-8")
    git(root, "add", "notes.txt")

    run_hook(root, "push_session.py", {"session_id": SID})

    assert error_log(root) == ""
    assert git(root, "rev-parse", "HEAD") == git(root, "rev-parse", "origin/main")
    log = (root / "USAGE_LOG.md").read_text(encoding="utf-8")
    assert "- from other machine" in log and "- from this machine" in log
    assert "<<<<<<<" not in log
    assert git(root, "diff", "--cached", "--name-only") == "notes.txt"


def test_push_does_not_push_users_own_unpushed_commits(tmp_path):
    root = make_repo(tmp_path)
    (root / ".claude" / "autopush.enabled").write_text("on", encoding="utf-8")
    (root / "work.txt").write_text("wip\n", encoding="utf-8")
    git(root, "add", "work.txt")
    git(root, "commit", "-q", "-m", "my unpushed work")
    remote_before = git(root, "rev-parse", "origin/main")
    with open(root / "USAGE_LOG.md", "a", encoding="utf-8") as f:
        f.write("- line\n")

    run_hook(root, "push_session.py", {"session_id": SID})

    assert "capture session" in git(root, "log", "-1", "--pretty=%s")
    assert git(root, "ls-remote", "origin", "main").split()[0] == remote_before
    assert "not pushed" in error_log(root)


def test_push_failure_is_logged_not_swallowed(tmp_path):
    root = make_repo(tmp_path, with_remote=False)
    (root / ".claude" / "autopush.enabled").write_text("on", encoding="utf-8")
    with open(root / "USAGE_LOG.md", "a", encoding="utf-8") as f:
        f.write("- line\n")
    run_hook(root, "push_session.py", {"session_id": SID})
    assert "no upstream" in error_log(root)


def test_push_is_noop_without_autopush_marker(tmp_path):
    root = make_repo(tmp_path)
    head = git(root, "rev-parse", "HEAD")
    with open(root / "USAGE_LOG.md", "a", encoding="utf-8") as f:
        f.write("- line\n")
    run_hook(root, "push_session.py", {"session_id": SID})
    assert git(root, "rev-parse", "HEAD") == head


# --- opt-out -------------------------------------------------------------------

def test_capture_disabled_marker_stops_capture_and_push(tmp_path):
    root = make_repo(tmp_path)
    (root / ".claude" / "capture.disabled").write_text("x", encoding="utf-8")
    (root / ".claude" / "autopush.enabled").write_text("on", encoding="utf-8")
    tr = write_transcript(tmp_path / "t.jsonl",
                          [("user", "question"), ("assistant", "answer")])
    log_before = (root / "USAGE_LOG.md").read_text(encoding="utf-8")

    run_hook(root, "capture_session.py", capture_payload(tr))
    assert not (root / "solved").exists()
    assert (root / "USAGE_LOG.md").read_text(encoding="utf-8") == log_before

    # Even with pending capture data and autopush on, nothing is committed.
    (root / "solved").mkdir()
    (root / "solved" / "x.md").write_text("x\n", encoding="utf-8")
    head = git(root, "rev-parse", "HEAD")
    run_hook(root, "push_session.py", {"session_id": SID})
    assert git(root, "rev-parse", "HEAD") == head


# --- capture: redaction, cap, idempotency --------------------------------------

def test_redaction_unit():
    cap = load_capture_module()
    secrets = {
        "openai": "sk-proj-AbCdEfGhIjKlMnOpQrStUvWx1234",
        "anthropic": "sk-ant-api03-AbCdEfGhIjKlMnOpQrStUv",
        "github": "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8",
        "aws": "AKIAIOSFODNN7EXAMPLE",
        "email": "student.name@uni.example.fi",
        "pw": "hunter2secret",
        "tok": "abc123tokenvalue",
        "jwt": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dBjftJeZ4CVPmB92K27uhbUJU1p1r_wW1gFWFOEjXk",
    }
    text = (f"key {secrets['openai']} and {secrets['anthropic']}\n"
            f"export GH={secrets['github']}\n"
            f"aws {secrets['aws']}\n"
            f"mail me at {secrets['email']}\n"
            f"password={secrets['pw']}\n"
            f'"access_token": "{secrets["tok"]}"\n'
            f"Authorization: Bearer {secrets['jwt']}\n"
            "-----BEGIN RSA PRIVATE KEY-----\nMIIEow\n-----END RSA PRIVATE KEY-----\n"
            "sigma_vm = 180 MPa, n = 1.39, see matlab-core@matlab-agentic-toolkit")
    out = cap.redact(text)
    for value in secrets.values():
        assert value not in out, value
    assert "MIIEow" not in out
    assert "password=[REDACTED]" in out
    assert "[REDACTED_EMAIL]" in out
    # Engineering content and non-email "@" ids survive.
    assert "sigma_vm = 180 MPa, n = 1.39" in out
    assert "matlab-core@matlab-agentic-toolkit" in out
    # Idempotent.
    assert cap.redact(out) == out


def test_capture_writes_redacted_file(tmp_path):
    root = make_repo(tmp_path, with_remote=False)
    tr = write_transcript(tmp_path / "t.jsonl", [
        ("user", "My key is sk-ant-api03-SECRETSECRETSECRET12 and mail "
                 "me at joe@example.com. Is σ=180 MPa yielding?"),
        ("assistant", "Set api_key=supersecretvalue. σ_vm = 158.7 MPa < 250 MPa."),
    ])
    run_hook(root, "capture_session.py", capture_payload(tr))
    md = (root / "solved" / "2026-10-03_abcd1234.md").read_text(encoding="utf-8")
    assert "SECRETSECRET" not in md and "supersecretvalue" not in md
    assert "joe@example.com" not in md
    assert "σ_vm = 158.7 MPa" in md
    assert error_log(root) == ""


def test_capture_is_idempotent_and_updates_in_place(tmp_path):
    root = make_repo(tmp_path, with_remote=False)
    turns = [("user", "q1"), ("assistant", "a1")]
    tr = write_transcript(tmp_path / "t.jsonl", turns)
    out = root / "solved" / "2026-10-03_abcd1234.md"

    run_hook(root, "capture_session.py", capture_payload(tr))
    first_md = out.read_text(encoding="utf-8")
    first_log = (root / "USAGE_LOG.md").read_text(encoding="utf-8")
    run_hook(root, "capture_session.py", capture_payload(tr))
    assert out.read_text(encoding="utf-8") == first_md
    assert (root / "USAGE_LOG.md").read_text(encoding="utf-8") == first_log
    assert first_log.count("session abcd1234") == 1
    assert "1 turns" in first_log

    # Session grows: same file, same single log line, count refreshed.
    write_transcript(tr, turns + [("user", "q2"), ("assistant", "a2")])
    run_hook(root, "capture_session.py", capture_payload(tr))
    log = (root / "USAGE_LOG.md").read_text(encoding="utf-8")
    assert log.count("session abcd1234") == 1 and "2 turns" in log
    assert "## Turn 2" in out.read_text(encoding="utf-8")
    assert sorted(p.name for p in (root / "solved").iterdir()) == [out.name]


def test_capture_caps_file_size(tmp_path):
    cap = load_capture_module()
    root = make_repo(tmp_path, with_remote=False)
    big = "x" * 5000
    turns = []
    for _ in range(100):
        turns += [("user", big), ("assistant", big)]
    tr = write_transcript(tmp_path / "t.jsonl", turns)
    run_hook(root, "capture_session.py", capture_payload(tr))
    data = (root / "solved" / "2026-10-03_abcd1234.md").read_bytes()
    assert len(data) <= cap.MAX_SESSION_BYTES
    assert b"Truncated" in data


def test_capture_bad_input_exits_zero_and_logs(tmp_path):
    root = make_repo(tmp_path, with_remote=False)
    p = subprocess.run([sys.executable,
                        str(root / ".claude" / "hooks" / "capture_session.py")],
                       input="{not json", capture_output=True, text=True)
    assert p.returncode == 0
    assert "could not parse" in error_log(root)


# --- settings.json launcher ----------------------------------------------------

def _bash():
    """bash as Claude Code uses it: Git Bash on Windows, system bash elsewhere."""
    if os.name == "nt":
        override = os.environ.get("CLAUDE_CODE_GIT_BASH_PATH")
        if override and os.path.exists(override):
            return override
        git_exe = shutil.which("git")
        if git_exe:
            # git.exe lives in <Git>/cmd, <Git>/bin, <Git>/mingw64/bin, ...
            for base in Path(git_exe).resolve().parents:
                for cand in (base / "bin" / "bash.exe",
                             base / "usr" / "bin" / "bash.exe"):
                    if cand.exists():
                        return str(cand)
        pytest.skip("Git Bash not found")
    exe = shutil.which("bash")
    if not exe:
        pytest.skip("bash not available")
    return exe


@pytest.mark.parametrize("event", ["Stop", "SessionEnd"])
def test_settings_command_runs_once_and_never_fails(tmp_path, event):
    """The hook command picks one interpreter, runs the script once, exits 0."""
    bash = _bash()
    cmd = json.loads(SETTINGS.read_text(encoding="utf-8"))[
        "hooks"][event][0]["hooks"][0]["command"]
    assert "2>/dev/null || true" not in cmd
    root = make_repo(tmp_path, with_remote=False)
    tr = write_transcript(tmp_path / "t.jsonl",
                          [("user", "q"), ("assistant", "a")])
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(root))
    # Make sure the test interpreter is found even without a repo .venv.
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env["PATH"]
    p = subprocess.run([bash, "-c", cmd], input=json.dumps(capture_payload(tr)),
                       capture_output=True, text=True, env=env, timeout=120)
    assert p.returncode == 0, p.stderr
    if event == "Stop":
        assert (root / "solved" / "2026-10-03_abcd1234.md").exists()

    # A missing script (python exits 2) must not leak exit code 2, which would
    # block Claude from stopping.
    os.remove(root / ".claude" / "hooks" /
              ("capture_session.py" if event == "Stop" else "push_session.py"))
    p = subprocess.run([bash, "-c", cmd], input="{}", capture_output=True,
                       text=True, env=env, timeout=120)
    assert p.returncode == 0
    assert error_log(root) != ""
