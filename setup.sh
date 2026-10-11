#!/usr/bin/env bash
# setup.sh - one-command setup for AI for Structural Engineers (macOS / Linux)
#
# Run from the repo root:
#     bash setup.sh                 # base setup
#     bash setup.sh --autopush      # also enable auto-commit/push of sessions
#
# Idempotent: safe to re-run. Sets up the Python calc environment and (if a
# MATLAB license is present) the official MATLAB MCP Server, skills, and plugins.
#
# Fails closed: every external command is checked. Anything that fails is
# reported with a fix hint and listed in the summary at the end (exit code 1).

set -u
repo="$(cd "$(dirname "$0")" && pwd)"
autopush=0
[ "${1:-}" = "--autopush" ] && autopush=1

# Pinned third-party versions (bump deliberately, after review).
mcp_version="v0.14.0"     # github.com/matlab/matlab-mcp-server release tag
skills_cli="skills@1.7.0" # npm package used via npx (vercel-labs/skills)

# SHA-256 of each matlab-mcp-server asset at $mcp_version.
mcp_sha256() {
  case "$1" in
    matlab-mcp-server-linux-x64)   echo "1a49693e757f3b1c17c1494fbd3efd87ce4b9017af0fa36fba2cf0bd11e8734a" ;;
    matlab-mcp-server-macos-arm64) echo "6e53d0fd3adcbbba60bf8dd4a63b53a64864a0d8154ae614d95789197a6142cb" ;;
    matlab-mcp-server-macos-x64)   echo "3ba477b3fbf03fd70ac594b18a21c5552b4b89c96e8dbe284c1aa7b0bcf8aead" ;;
    *) echo "" ;;
  esac
}

sha256_of() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | cut -d' ' -f1
  else shasum -a 256 "$1" | cut -d' ' -f1; fi
}

# --- Result tracking ----------------------------------------------------------
summary=""
n_failed=0
ok()   { echo "  $2"; summary="${summary}  OK       $1"$'\n'; }
skip() { echo "  $2"; summary="${summary}  SKIPPED  $1"$'\n'; }
fail() {
  echo "  FAILED: $2"
  [ -n "${3:-}" ] && echo "    Fix: $3"
  summary="${summary}  FAILED   $1"$'\n'
  n_failed=$((n_failed + 1))
}

echo "== AI for Structural Engineers - setup =="
echo "Repo: $repo"

# --- 1. Python venv + libraries --------------------------------------------
echo "[1/6] Python environment..."
py=""
for cand in python3 python; do
  if command -v "$cand" >/dev/null 2>&1 && \
     "$cand" -c 'import sys; sys.exit(sys.version_info < (3, 9))' >/dev/null 2>&1; then
    py="$cand"; break
  fi
done
venvpy="$repo/.venv/bin/python"
python_ok=0
if [ -z "$py" ]; then
  fail "Python environment" "Python 3.9+ not found." \
       "Install Python 3 (python.org, or 'brew install python' on macOS), see docs/02, then re-run"
elif [ ! -x "$venvpy" ] && ! "$py" -m venv "$repo/.venv"; then
  fail "Python environment" "could not create .venv" \
       "On Debian/Ubuntu: sudo apt install python3-venv. Then delete .venv and re-run"
elif ! "$venvpy" -m pip install --quiet --disable-pip-version-check --upgrade pip; then
  fail "Python environment" "pip upgrade failed" "Check your internet connection / proxy, then re-run"
elif ! "$venvpy" -m pip install --quiet --disable-pip-version-check -r "$repo/requirements.txt"; then
  fail "Python environment" "pip install -r requirements.txt failed" \
       "Read the pip error above; then run: .venv/bin/python -m pip install -r requirements.txt"
else
  python_ok=1
  ok "Python environment" "Calculation libraries from requirements.txt installed in .venv."
fi

# --- 2. Detect MATLAB -------------------------------------------------------
echo "[2/6] Detecting MATLAB..."
matlab_root=""; release=""
for base in /usr/local/MATLAB /Applications ; do
  if [ -d "$base" ]; then
    d=$(ls -d "$base"/*MATLAB*R20* "$base"/R20* 2>/dev/null | sort -r | head -n1)
    if [ -n "$d" ]; then matlab_root="$d"; release=$(basename "$d" | grep -oE 'R20[0-9]{2}[ab]'); break; fi
  fi
done
if [ -n "$matlab_root" ]; then ok "MATLAB detection" "Found MATLAB ($release) at $matlab_root"
else skip "MATLAB detection" "No MATLAB found - skipping MATLAB steps. The free Python path still works."; fi

# --- 3. MATLAB Engine API ---------------------------------------------------
if [ -n "$matlab_root" ]; then
  echo "[3/6] MATLAB Engine API..."
  if [ "$python_ok" -ne 1 ]; then
    skip "MATLAB Engine API" "Skipped: the Python environment failed (step 1)."
  elif [ -z "$release" ]; then
    skip "MATLAB Engine API" "Couldn't parse the MATLAB release; see docs/03 to install the Engine API by hand."
  else
    yy=$(( ${release:1:4} - 2000 )); ab="${release:5:1}"
    n=1; [ "$ab" = "b" ] && n=2
    ver="${yy}.${n}.*"
    if "$venvpy" -m pip install --quiet --disable-pip-version-check "matlabengine==$ver"; then
      ok "MATLAB Engine API" "matlabengine==$ver installed."
    else
      fail "MATLAB Engine API" "pip couldn't install matlabengine==$ver" \
           "cd \"$matlab_root/extern/engines/python\" && \"$venvpy\" -m pip install ."
    fi
  fi
fi

# --- 4. Official MATLAB MCP Server + registration ---------------------------
mcp_registered=0
if [ -n "$matlab_root" ]; then
  echo "[4/6] MATLAB MCP Server ($mcp_version)..."
  mcpdir="$HOME/matlab-mcp-server"; mkdir -p "$mcpdir"
  case "$(uname -s)-$(uname -m)" in
    Darwin-arm64) asset="matlab-mcp-server-macos-arm64" ;;
    Darwin-*)     asset="matlab-mcp-server-macos-x64" ;;
    *)            asset="matlab-mcp-server-linux-x64" ;;
  esac
  mcpbin="$mcpdir/$asset"
  want_sha="$(mcp_sha256 "$asset")"
  mcp_ok=1
  if [ -f "$mcpbin" ] && [ "$(sha256_of "$mcpbin")" != "$want_sha" ]; then
    echo "  Note: existing $mcpbin is not the pinned $mcp_version build. Delete it and re-run to switch."
  fi
  if [ ! -x "$mcpbin" ]; then
    url="https://github.com/matlab/matlab-mcp-server/releases/download/$mcp_version/$asset"
    tmp="$mcpbin.download"
    rm -f "$tmp"
    if ! curl -fsSL -o "$tmp" "$url"; then
      rm -f "$tmp"
      fail "MATLAB MCP Server" "download failed: $url" "Check your connection, or download it by hand into $mcpdir"
      mcp_ok=0
    elif [ "$(sha256_of "$tmp")" != "$want_sha" ]; then
      rm -f "$tmp"
      fail "MATLAB MCP Server" "checksum mismatch for $asset" \
           "Do not run it. Re-run setup; if it persists, report it - the download may be tampered with"
      mcp_ok=0
    else
      mv "$tmp" "$mcpbin" && chmod +x "$mcpbin"
    fi
  fi
  if [ "$mcp_ok" -eq 1 ]; then
    if command -v claude >/dev/null 2>&1; then
      if claude mcp list 2>/dev/null | grep -qE '^matlab'; then
        mcp_registered=1
        ok "MATLAB MCP Server" "MATLAB MCP server already registered."
      elif claude mcp add --transport stdio matlab -- "$mcpbin" "--matlab-root=$matlab_root"; then
        mcp_registered=1
        ok "MATLAB MCP Server" "Registered MATLAB MCP server $mcp_version with Claude Code."
      else
        fail "MATLAB MCP Server" "'claude mcp add' failed" \
             "Run by hand: claude mcp add --transport stdio matlab -- \"$mcpbin\" \"--matlab-root=$matlab_root\""
      fi
    else
      fail "MATLAB MCP Server" "'claude' CLI not found" "Install Claude Code (docs/01), then re-run bash setup.sh"
    fi
  fi
fi

# --- 5. Skills + plugins ----------------------------------------------------
echo "[5/6] Skills and plugins..."
if command -v claude >/dev/null 2>&1; then
  market_ok=1
  if ! claude plugin marketplace list 2>/dev/null | grep -q "matlab-agentic-toolkit"; then
    claude plugin marketplace add "https://github.com/matlab/matlab-agentic-toolkit" || market_ok=0
  fi
  if [ "$market_ok" -ne 1 ]; then
    fail "Claude plugins" "couldn't add the matlab-agentic-toolkit marketplace" \
         "Run: claude plugin marketplace add https://github.com/matlab/matlab-agentic-toolkit"
  else
    installed="$(claude plugin list 2>/dev/null || true)"
    for plugin in matlab-core math-and-optimization; do
      id="$plugin@matlab-agentic-toolkit"
      if printf '%s' "$installed" | grep -qF "$id"; then
        ok "Plugin $plugin" "$id already installed."
      elif claude plugin install "$id"; then
        ok "Plugin $plugin" "Installed $id."
      else
        fail "Plugin $plugin" "couldn't install $id" "Run: claude plugin install $id"
      fi
    done
  fi
else
  fail "Claude plugins" "'claude' CLI not found" "Install Claude Code (docs/01), then re-run bash setup.sh"
fi
if command -v npx >/dev/null 2>&1; then
  if npx --yes "$skills_cli" add "K-Dense-AI/scientific-agent-skills@matlab" -y; then
    ok "K-Dense matlab skill" "Installed K-Dense matlab skill (via $skills_cli)."
  else
    fail "K-Dense matlab skill" "npx $skills_cli add failed" \
         "Run: npx --yes $skills_cli add K-Dense-AI/scientific-agent-skills@matlab -y"
  fi
else
  fail "K-Dense matlab skill" "'npx' not found" "Install Node.js LTS (nodejs.org; includes npx), then re-run"
fi

# --- 6. Auto-push opt-in ----------------------------------------------------
echo "[6/6] Learning-loop auto-push..."
if [ "$autopush" -eq 1 ]; then
  mkdir -p "$repo/.claude"
  echo "Auto-push enabled on this machine." > "$repo/.claude/autopush.enabled"
  ok "Auto-push" "Auto-push ENABLED - captured sessions commit & push on session end."
else
  echo "  Auto-push OFF. Re-run with --autopush to enable."
  summary="${summary}  OFF      Auto-push"$'\n'
fi

# --- Summary ----------------------------------------------------------------
echo ""
echo "== Summary =="
printf '%s' "$summary"
if [ "$n_failed" -gt 0 ]; then
  echo ""
  echo "$n_failed step(s) FAILED - see the 'Fix:' hints above, then re-run bash setup.sh (it is safe to re-run)."
else
  echo ""
  echo "All steps succeeded."
fi

echo ""
echo "== Next =="
echo "Use the repo's Python, not the system one: .venv/bin/python"
echo "  (or activate it first: source .venv/bin/activate)"
echo "RESTART Claude Code in this folder so hooks/MCP/skills load, then ask:"
if [ -n "$matlab_root" ] && [ "$mcp_registered" -eq 1 ]; then
  echo '  "List your MATLAB MCP tools and run detect_matlab_toolboxes."'
else
  echo '  "A steel part has stresses σx = 180, σy = 60, τxy = 40 MPa. The yield strength is 250 MPa.'
  echo '   Is it yielding by the von Mises criterion? Use SymPy in .venv/bin/python, show the working and plot the yield surface."'
fi

[ "$n_failed" -eq 0 ]
