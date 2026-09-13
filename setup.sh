#!/usr/bin/env bash
# setup.sh - one-command setup for MATLAB + Claude for Engineers (macOS / Linux)
#
# Run from the repo root:
#     bash setup.sh                 # base setup
#     bash setup.sh --autopush      # also enable auto-commit/push of sessions
#
# Idempotent: safe to re-run. Sets up the Python calc environment and (if a
# MATLAB license is present) the official MATLAB MCP Server, skills, and plugins.

set -u
repo="$(cd "$(dirname "$0")" && pwd)"
autopush=0
[ "${1:-}" = "--autopush" ] && autopush=1

echo "== MATLAB + Claude for Engineers - setup =="
echo "Repo: $repo"

# --- 1. Python venv + libraries --------------------------------------------
echo "[1/6] Python environment..."
py="python3"; command -v "$py" >/dev/null 2>&1 || py="python"
[ -d "$repo/.venv" ] || "$py" -m venv "$repo/.venv"
venvpy="$repo/.venv/bin/python"
"$venvpy" -m pip install --quiet --upgrade pip
"$venvpy" -m pip install --quiet -r "$repo/requirements.txt"
echo "  numpy/scipy/sympy/matplotlib installed."

# --- 2. Detect MATLAB -------------------------------------------------------
echo "[2/6] Detecting MATLAB..."
matlab_root=""; release=""
for base in /usr/local/MATLAB /Applications ; do
  if [ -d "$base" ]; then
    d=$(ls -d "$base"/*MATLAB*R20* "$base"/R20* 2>/dev/null | sort -r | head -n1)
    if [ -n "$d" ]; then matlab_root="$d"; release=$(basename "$d" | grep -oE 'R20[0-9]{2}[ab]'); break; fi
  fi
done
if [ -n "$matlab_root" ]; then echo "  Found MATLAB ($release) at $matlab_root"
else echo "  No MATLAB found - skipping MATLAB steps. The free Python path still works."; fi

# --- 3. MATLAB Engine API ---------------------------------------------------
if [ -n "$matlab_root" ] && [ -n "$release" ]; then
  echo "[3/6] MATLAB Engine API..."
  yy=$(( ${release:1:4} - 2000 )); ab="${release:5:1}"
  n=1; [ "$ab" = "b" ] && n=2
  ver="${yy}.${n}.*"
  if "$venvpy" -m pip install --quiet "matlabengine==$ver"; then
    echo "  matlabengine==$ver installed."
  else
    echo "  pip couldn't find matlabengine==$ver. Fallback:"
    echo "    cd \"$matlab_root/extern/engines/python\" && python setup.py install"
  fi
fi

# --- 4. Official MATLAB MCP Server + registration ---------------------------
if [ -n "$matlab_root" ]; then
  echo "[4/6] MATLAB MCP Server..."
  mcpdir="$HOME/matlab-mcp-server"; mkdir -p "$mcpdir"
  case "$(uname -s)-$(uname -m)" in
    Darwin-arm64) asset="matlab-mcp-server-macos-arm64" ;;
    Darwin-*)     asset="matlab-mcp-server-macos-x64" ;;
    *)            asset="matlab-mcp-server-linux-x64" ;;
  esac
  mcpbin="$mcpdir/$asset"
  if [ ! -x "$mcpbin" ]; then
    if command -v gh >/dev/null 2>&1; then
      gh release download --repo matlab/matlab-mcp-server --pattern "*${asset##*server-}*" --dir "$mcpdir" --clobber
    else
      curl -L -o "$mcpbin" "https://github.com/matlab/matlab-mcp-server/releases/latest/download/$asset"
    fi
    chmod +x "$mcpbin" 2>/dev/null || true
  fi
  if command -v claude >/dev/null 2>&1; then
    if ! claude mcp list 2>/dev/null | grep -qE '^matlab'; then
      claude mcp add --transport stdio matlab -- "$mcpbin" "--matlab-root=$matlab_root"
      echo "  Registered MATLAB MCP server with Claude Code."
    else
      echo "  MATLAB MCP server already registered."
    fi
  else
    echo "  'claude' CLI not found - install Claude Code, then re-run."
  fi
fi

# --- 5. Skills + plugins ----------------------------------------------------
echo "[5/6] Skills and plugins..."
if command -v claude >/dev/null 2>&1; then
  claude plugin marketplace add "https://github.com/matlab/matlab-agentic-toolkit" 2>/dev/null || true
  claude plugin install matlab-core@matlab-agentic-toolkit 2>/dev/null || true
  claude plugin install math-and-optimization@matlab-agentic-toolkit 2>/dev/null || true
  echo "  Installed matlab-core + math-and-optimization plugins."
fi
npx --yes skills add "K-Dense-AI/scientific-agent-skills@matlab" -y 2>/dev/null || true
echo "  Installed K-Dense matlab skill."

# --- 6. Auto-push opt-in ----------------------------------------------------
echo "[6/6] Learning-loop auto-push..."
if [ "$autopush" -eq 1 ]; then
  mkdir -p "$repo/.claude"
  echo "Auto-push enabled on this machine." > "$repo/.claude/autopush.enabled"
  echo "  Auto-push ENABLED - captured sessions commit & push on session end."
else
  echo "  Auto-push OFF. Re-run with --autopush to enable."
fi

echo ""
echo "== Done =="
echo "Next: RESTART Claude Code in this folder so hooks/MCP/skills load, then ask:"
echo '  "List your MATLAB MCP tools and run detect_matlab_toolboxes."'
