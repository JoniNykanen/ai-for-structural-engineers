# setup.ps1 - one-command setup for MATLAB + Claude for Engineers (Windows)
#
# Run from the repo root in PowerShell:
#     ./setup.ps1
#
# Idempotent: safe to re-run. Sets up the Python calc environment, and (if a
# MATLAB license is present) the official MATLAB MCP Server, skills, and plugins.
# Pass -EnableAutoPush to also auto-commit/push captured sessions.
# Robot Structural Analysis MCP is installed when Robot is detected (or -WithRobot).

param(
    [switch]$EnableAutoPush,
    [switch]$WithRobot      # install the Robot MCP even if Robot isn't detected
)

$ErrorActionPreference = "Stop"
$repo = $PSScriptRoot
Write-Host "== MATLAB + Claude for Engineers - setup ==" -ForegroundColor Cyan
Write-Host "Repo: $repo`n"

# --- 1. Python virtual environment + calculation libraries ------------------
Write-Host "[1/7] Python environment..." -ForegroundColor Yellow
$py = "python"
& $py --version | Out-Null
if (-not (Test-Path "$repo\.venv")) { & $py -m venv "$repo\.venv" }
$venvPy = "$repo\.venv\Scripts\python.exe"
& $venvPy -m pip install --quiet --upgrade pip
& $venvPy -m pip install --quiet -r "$repo\requirements.txt"
Write-Host "  numpy/scipy/sympy/matplotlib installed." -ForegroundColor Green

# --- 2. Detect MATLAB -------------------------------------------------------
Write-Host "[2/7] Detecting MATLAB..." -ForegroundColor Yellow
$matlabBase = "C:\Program Files\MATLAB"
$matlabRoot = $null
if (Test-Path $matlabBase) {
    $rel = Get-ChildItem $matlabBase -Directory -ErrorAction SilentlyContinue |
           Sort-Object Name -Descending | Select-Object -First 1
    if ($rel) { $matlabRoot = $rel.FullName; $release = $rel.Name }
}
if ($matlabRoot) {
    Write-Host "  Found MATLAB $release at $matlabRoot" -ForegroundColor Green
} else {
    Write-Host "  No MATLAB found - skipping MATLAB steps. The free Python path still works." -ForegroundColor DarkYellow
}

# --- 3. MATLAB Engine API (matched to the release) --------------------------
if ($matlabRoot) {
    Write-Host "[3/7] MATLAB Engine API..." -ForegroundColor Yellow
    # Release-year versioning: R2026a -> 26.1, R2026b -> 26.2
    if ($release -match "R(\d{4})([ab])") {
        $yy = [int]$Matches[1] - 2000
        $n  = if ($Matches[2] -eq "a") { 1 } else { 2 }
        $ver = "$yy.$n.*"
        try {
            & $venvPy -m pip install --quiet "matlabengine==$ver"
            Write-Host "  matlabengine==$ver installed." -ForegroundColor Green
        } catch {
            Write-Host "  pip couldn't find matlabengine==$ver. Fallback:" -ForegroundColor DarkYellow
            Write-Host "    cd `"$matlabRoot\extern\engines\python`"; python setup.py install"
        }
    }
}

# --- 4. Official MATLAB MCP Server + registration ---------------------------
if ($matlabRoot) {
    Write-Host "[4/7] MATLAB MCP Server..." -ForegroundColor Yellow
    $mcpDir = "$HOME\matlab-mcp-server"
    $mcpBin = "$mcpDir\matlab-mcp-server-windows-x64.exe"
    if (-not (Test-Path $mcpBin)) {
        New-Item -ItemType Directory -Force -Path $mcpDir | Out-Null
        if (Get-Command gh -ErrorAction SilentlyContinue) {
            gh release download --repo matlab/matlab-mcp-server --pattern "*windows-x64*" --dir $mcpDir --clobber
        } else {
            $url = "https://github.com/matlab/matlab-mcp-server/releases/latest/download/matlab-mcp-server-windows-x64.exe"
            Invoke-WebRequest -Uri $url -OutFile $mcpBin
        }
    }
    if (Get-Command claude -ErrorAction SilentlyContinue) {
        $mcpList = (claude mcp list 2>$null | Out-String)
        if ($mcpList -notmatch "(?m)^matlab") {
            claude mcp add --transport stdio matlab -- "$mcpBin" "--matlab-root=$matlabRoot"
            Write-Host "  Registered MATLAB MCP server with Claude Code." -ForegroundColor Green
        } else {
            Write-Host "  MATLAB MCP server already registered." -ForegroundColor Green
        }
    } else {
        Write-Host "  'claude' CLI not found - install Claude Code, then re-run." -ForegroundColor DarkYellow
    }
}

# --- 5. Skills + plugins ----------------------------------------------------
Write-Host "[5/7] Skills and plugins..." -ForegroundColor Yellow
if (Get-Command claude -ErrorAction SilentlyContinue) {
    try {
        claude plugin marketplace add "https://github.com/matlab/matlab-agentic-toolkit" 2>$null
        claude plugin install matlab-core@matlab-agentic-toolkit 2>$null
        claude plugin install math-and-optimization@matlab-agentic-toolkit 2>$null
        Write-Host "  Installed matlab-core + math-and-optimization plugins." -ForegroundColor Green
    } catch { Write-Host "  (plugin step skipped: $($_.Exception.Message))" -ForegroundColor DarkYellow }
}
try {
    npx --yes skills add "K-Dense-AI/scientific-agent-skills@matlab" -y 2>$null
    Write-Host "  Installed K-Dense matlab skill." -ForegroundColor Green
} catch { Write-Host "  (skill step skipped)" -ForegroundColor DarkYellow }

# --- 6. Robot Structural Analysis MCP (rsap-mcp, pinned) --------------------
Write-Host "[6/7] Robot Structural Analysis MCP..." -ForegroundColor Yellow
$robotFound = Test-Path "Registry::HKEY_CLASSES_ROOT\Robot.Application"
if ($robotFound -or $WithRobot) {
    # Third-party MIT server, pinned to a reviewed commit (see docs/14).
    $rsapDir = "$repo\tools\rsap-mcp"
    $rsapCommit = "08ab805b2edae7da8bfb43e7320ff977e4503a00"
    if (-not (Test-Path $rsapDir)) {
        git clone --quiet https://github.com/nhantruong96/rsap-mcp.git $rsapDir
    }
    git -C $rsapDir fetch --quiet origin
    git -C $rsapDir checkout --quiet $rsapCommit
    if (-not (Test-Path "$rsapDir\.venv")) { & $py -m venv "$rsapDir\.venv" }
    & "$rsapDir\.venv\Scripts\python.exe" -m pip install --quiet --disable-pip-version-check -e $rsapDir
    & "$rsapDir\.venv\Scripts\python.exe" -m rsap_mcp --selfcheck 2>$null
    Write-Host "  rsap-mcp installed; registered via the repo's .mcp.json (server 'robot')." -ForegroundColor Green
} else {
    Write-Host "  Robot not detected - skipping. Re-run with -WithRobot to force." -ForegroundColor DarkYellow
}

# --- 7. Auto-push opt-in ----------------------------------------------------
Write-Host "[7/7] Learning-loop auto-push..." -ForegroundColor Yellow
$marker = "$repo\.claude\autopush.enabled"
if ($EnableAutoPush) {
    New-Item -ItemType Directory -Force -Path "$repo\.claude" | Out-Null
    Set-Content -Path $marker -Value "Auto-push enabled on this machine." -Encoding utf8
    Write-Host "  Auto-push ENABLED - captured sessions will commit & push on session end." -ForegroundColor Green
} else {
    Write-Host "  Auto-push OFF. Re-run with -EnableAutoPush to turn it on." -ForegroundColor Green
}

Write-Host "`n== Done ==" -ForegroundColor Cyan
Write-Host "Next: RESTART Claude Code in this folder so hooks/MCP/skills load, then ask:"
Write-Host '  "List your MATLAB MCP tools and run detect_matlab_toolboxes."'
