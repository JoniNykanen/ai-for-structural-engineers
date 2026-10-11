# setup.ps1 - one-command setup for AI for Structural Engineers (Windows)
#
# Run from the repo root in PowerShell:
#     ./setup.ps1
#
# Idempotent: safe to re-run. Sets up the Python calc environment, and (if a
# MATLAB license is present) the official MATLAB MCP Server, skills, and plugins.
# Pass -EnableAutoPush to also auto-commit/push captured sessions.
# Robot Structural Analysis MCP is installed when Robot is detected (or -WithRobot).
# The Revit MCP add-on (Autodesk, installed separately) is detected and registered.
#
# Fails closed: every external command is checked. Anything that fails is
# reported with a fix hint and listed in the summary at the end (exit code 1).

param(
    [switch]$EnableAutoPush,
    [switch]$WithRobot      # install the Robot MCP even if Robot isn't detected
)

$ErrorActionPreference = "Stop"
$repo = $PSScriptRoot

# Pinned third-party versions (bump deliberately, after review).
$mcpVersion = "v0.14.0"   # github.com/matlab/matlab-mcp-server release tag
$mcpSha256  = "6697a8962f148628f11d93b36960235871de5614905d6a27c55341c2b83f4118"  # matlab-mcp-server-windows-x64.exe @ v0.14.0
$skillsCli  = "skills@1.7.0"   # npm package used via npx (vercel-labs/skills)

# --- Result tracking ----------------------------------------------------------
$script:results = New-Object System.Collections.Generic.List[object]

function Add-Result([string]$Step, [string]$Status, [string]$Detail = "") {
    $script:results.Add([pscustomobject]@{ Step = $Step; Status = $Status; Detail = $Detail })
}

function Write-Ok([string]$Step, [string]$Message) {
    Write-Host "  $Message" -ForegroundColor Green
    Add-Result $Step "OK"
}

function Write-Fail([string]$Step, [string]$Message, [string]$Hint) {
    Write-Host "  FAILED: $Message" -ForegroundColor Red
    if ($Hint) { Write-Host "    Fix: $Hint" -ForegroundColor Red }
    Add-Result $Step "FAILED" $Hint
}

function Write-Skip([string]$Step, [string]$Message) {
    Write-Host "  $Message" -ForegroundColor DarkYellow
    Add-Result $Step "SKIPPED" $Message
}

# Run a native command and return $true only if it exited 0. PowerShell 5.1
# does not throw on native failures, so check $LASTEXITCODE explicitly.
function Invoke-Native([scriptblock]$Command) {
    $global:LASTEXITCODE = 0
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"   # native stderr must not become a terminating error
    try {
        & $Command | Out-Host
        $code = $LASTEXITCODE
    } catch {
        Write-Host "    $($_.Exception.Message)" -ForegroundColor Red
        $code = 1
    } finally {
        $ErrorActionPreference = $prev
    }
    return ($code -eq 0)
}

Write-Host "== AI for Structural Engineers - setup ==" -ForegroundColor Cyan
Write-Host "Repo: $repo`n"

# --- 1. Python virtual environment + calculation libraries ------------------
Write-Host "[1/8] Python environment..." -ForegroundColor Yellow
$venvPy = "$repo\.venv\Scripts\python.exe"
$py = $null
foreach ($cand in @("python", "py")) {
    if (Get-Command $cand -ErrorAction SilentlyContinue) {
        # The Microsoft Store alias "python" exists but fails; test it really runs Python 3.
        if (Invoke-Native { & $cand -c "import sys; sys.exit(sys.version_info < (3, 9))" }) { $py = $cand; break }
    }
}
$pythonOk = $false
if (-not $py) {
    Write-Fail "Python environment" "Python 3.9+ not found." "Install Python from python.org (tick 'Add to PATH'), see docs/02, then re-run ./setup.ps1"
} else {
    $venvOk = $true
    if (-not (Test-Path $venvPy)) {
        $venvOk = Invoke-Native { & $py -m venv "$repo\.venv" }
    }
    if (-not $venvOk) {
        Write-Fail "Python environment" "could not create .venv" "Delete the .venv folder and re-run; check that '$py -m venv' works"
    } elseif (-not (Invoke-Native { & $venvPy -m pip install --quiet --disable-pip-version-check --upgrade pip })) {
        Write-Fail "Python environment" "pip upgrade failed" "Check your internet connection / proxy, then re-run"
    } elseif (-not (Invoke-Native { & $venvPy -m pip install --quiet --disable-pip-version-check -r "$repo\requirements.txt" })) {
        Write-Fail "Python environment" "pip install -r requirements.txt failed" "Read the pip error above; then run: .venv\Scripts\python -m pip install -r requirements.txt"
    } else {
        $pythonOk = $true
        Write-Ok "Python environment" "Calculation libraries from requirements.txt installed in .venv."
    }
}

# --- 2. Detect MATLAB -------------------------------------------------------
Write-Host "[2/8] Detecting MATLAB..." -ForegroundColor Yellow
$matlabBase = "C:\Program Files\MATLAB"
$matlabRoot = $null
$release = $null
if (Test-Path $matlabBase) {
    $rel = Get-ChildItem $matlabBase -Directory -ErrorAction SilentlyContinue |
           Sort-Object Name -Descending | Select-Object -First 1
    if ($rel) { $matlabRoot = $rel.FullName; $release = $rel.Name }
}
if ($matlabRoot) {
    Write-Ok "MATLAB detection" "Found MATLAB $release at $matlabRoot"
} else {
    Write-Skip "MATLAB detection" "No MATLAB found - skipping MATLAB steps. The free Python path still works."
}

# --- 3. MATLAB Engine API (matched to the release) --------------------------
if ($matlabRoot) {
    Write-Host "[3/8] MATLAB Engine API..." -ForegroundColor Yellow
    if (-not $pythonOk) {
        Write-Skip "MATLAB Engine API" "Skipped: the Python environment failed (step 1)."
    } elseif ($release -match "R(\d{4})([ab])") {
        # Release-year versioning: R2026a -> 26.1, R2026b -> 26.2
        $yy = [int]$Matches[1] - 2000
        $n  = if ($Matches[2] -eq "a") { 1 } else { 2 }
        $ver = "$yy.$n.*"
        if (Invoke-Native { & $venvPy -m pip install --quiet --disable-pip-version-check "matlabengine==$ver" }) {
            Write-Ok "MATLAB Engine API" "matlabengine==$ver installed."
        } else {
            Write-Fail "MATLAB Engine API" "pip couldn't install matlabengine==$ver" "cd `"$matlabRoot\extern\engines\python`"; $venvPy -m pip install ."
        }
    } else {
        Write-Skip "MATLAB Engine API" "Couldn't parse the MATLAB release from '$release'; see docs/03 to install the Engine API by hand."
    }
}

# --- 4. Official MATLAB MCP Server + registration ---------------------------
$mcpRegistered = $false
if ($matlabRoot) {
    Write-Host "[4/8] MATLAB MCP Server ($mcpVersion)..." -ForegroundColor Yellow
    $mcpDir = "$HOME\matlab-mcp-server"
    $mcpName = "matlab-mcp-server-windows-x64.exe"
    $mcpBin = "$mcpDir\$mcpName"
    $mcpOk = $true
    if ((Test-Path $mcpBin) -and ((Get-FileHash -Algorithm SHA256 $mcpBin).Hash.ToLower() -ne $mcpSha256)) {
        Write-Host "  Note: existing $mcpBin is not the pinned $mcpVersion build. Delete it and re-run to switch to $mcpVersion." -ForegroundColor DarkYellow
    }
    if (-not (Test-Path $mcpBin)) {
        New-Item -ItemType Directory -Force -Path $mcpDir | Out-Null
        $tmp = "$mcpBin.download"
        if (Test-Path $tmp) { Remove-Item $tmp -Force }
        $url = "https://github.com/matlab/matlab-mcp-server/releases/download/$mcpVersion/$mcpName"
        try {
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -Uri $url -OutFile $tmp -UseBasicParsing
            $hash = (Get-FileHash -Algorithm SHA256 $tmp).Hash.ToLower()
            if ($hash -ne $mcpSha256) {
                Remove-Item $tmp -Force
                Write-Fail "MATLAB MCP Server" "checksum mismatch for $mcpName ($hash)" "Do not run it. Re-run setup; if it persists, report it - the download may be tampered with"
                $mcpOk = $false
            } else {
                Move-Item $tmp $mcpBin -Force
            }
        } catch {
            if (Test-Path $tmp) { Remove-Item $tmp -Force }
            Write-Fail "MATLAB MCP Server" "download failed: $($_.Exception.Message)" "Check your connection, or download $url by hand into $mcpDir"
            $mcpOk = $false
        }
    }
    if ($mcpOk) {
        if (Get-Command claude -ErrorAction SilentlyContinue) {
            $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
            $mcpList = (claude mcp list 2>&1 | Out-String)
            $ErrorActionPreference = $prev
            if ($mcpList -match "(?m)^matlab") {
                $mcpRegistered = $true
                Write-Ok "MATLAB MCP Server" "MATLAB MCP server ($mcpVersion binary) already registered."
            } elseif (Invoke-Native { claude mcp add --transport stdio matlab -- "$mcpBin" "--matlab-root=$matlabRoot" }) {
                $mcpRegistered = $true
                Write-Ok "MATLAB MCP Server" "Registered MATLAB MCP server $mcpVersion with Claude Code."
            } else {
                Write-Fail "MATLAB MCP Server" "'claude mcp add' failed" "Run by hand: claude mcp add --transport stdio matlab -- `"$mcpBin`" `"--matlab-root=$matlabRoot`""
            }
        } else {
            Write-Fail "MATLAB MCP Server" "'claude' CLI not found" "Install Claude Code (docs/01), then re-run ./setup.ps1"
        }
    }
}

# --- 5. Skills + plugins ----------------------------------------------------
Write-Host "[5/8] Skills and plugins..." -ForegroundColor Yellow
if (Get-Command claude -ErrorAction SilentlyContinue) {
    $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    $markets = (claude plugin marketplace list 2>&1 | Out-String)
    $plugins = (claude plugin list 2>&1 | Out-String)
    $ErrorActionPreference = $prev
    $marketOk = $true
    if ($markets -notmatch "matlab-agentic-toolkit") {
        $marketOk = Invoke-Native { claude plugin marketplace add "https://github.com/matlab/matlab-agentic-toolkit" }
    }
    if (-not $marketOk) {
        Write-Fail "Claude plugins" "couldn't add the matlab-agentic-toolkit marketplace" "Run: claude plugin marketplace add https://github.com/matlab/matlab-agentic-toolkit"
    } else {
        foreach ($plugin in @("matlab-core", "math-and-optimization")) {
            $id = "$plugin@matlab-agentic-toolkit"
            if ($plugins -match [regex]::Escape($id)) {
                Write-Ok "Plugin $plugin" "$id already installed."
            } elseif (Invoke-Native { claude plugin install $id }) {
                Write-Ok "Plugin $plugin" "Installed $id."
            } else {
                Write-Fail "Plugin $plugin" "couldn't install $id" "Run: claude plugin install $id"
            }
        }
    }
} else {
    Write-Fail "Claude plugins" "'claude' CLI not found" "Install Claude Code (docs/01), then re-run ./setup.ps1"
}
if (Get-Command npx -ErrorAction SilentlyContinue) {
    if (Invoke-Native { npx --yes $skillsCli add "K-Dense-AI/scientific-agent-skills@matlab" -y }) {
        Write-Ok "K-Dense matlab skill" "Installed K-Dense matlab skill (via $skillsCli)."
    } else {
        Write-Fail "K-Dense matlab skill" "npx $skillsCli add failed" "Run: npx --yes $skillsCli add K-Dense-AI/scientific-agent-skills@matlab -y"
    }
} else {
    Write-Fail "K-Dense matlab skill" "'npx' not found" "Install Node.js LTS from nodejs.org (it includes npx), then re-run"
}

# --- 6. Robot Structural Analysis MCP (rsap-mcp, pinned) --------------------
Write-Host "[6/8] Robot Structural Analysis MCP..." -ForegroundColor Yellow
$robotFound = Test-Path "Registry::HKEY_CLASSES_ROOT\Robot.Application"
if ($robotFound -or $WithRobot) {
    # Third-party MIT server, pinned to a reviewed commit (see docs/14).
    $rsapDir = "$repo\tools\rsap-mcp"
    $rsapCommit = "08ab805b2edae7da8bfb43e7320ff977e4503a00"
    $rsapPy = "$rsapDir\.venv\Scripts\python.exe"
    $ok = $true
    $hint = ""
    if (-not $py) { $ok = $false; $hint = "Python 3.9+ is required first (step 1)" }
    if ($ok -and -not (Test-Path $rsapDir)) {
        $ok = Invoke-Native { git clone --quiet https://github.com/nhantruong96/rsap-mcp.git $rsapDir }
        if (-not $ok) { $hint = "git clone failed - check git is installed and you are online" }
    }
    if ($ok) {
        $ok = Invoke-Native { git -C $rsapDir fetch --quiet origin }
        if (-not $ok) { $hint = "git fetch failed in $rsapDir - check your connection" }
    }
    if ($ok) {
        $ok = Invoke-Native { git -C $rsapDir checkout --quiet $rsapCommit }
        if (-not $ok) { $hint = "couldn't check out pinned commit $rsapCommit - delete $rsapDir and re-run" }
    }
    if ($ok -and -not (Test-Path $rsapPy)) {
        $ok = Invoke-Native { & $py -m venv "$rsapDir\.venv" }
        if (-not $ok) { $hint = "couldn't create $rsapDir\.venv" }
    }
    if ($ok) {
        $ok = Invoke-Native { & $rsapPy -m pip install --quiet --disable-pip-version-check -e $rsapDir }
        if (-not $ok) { $hint = "pip install of rsap-mcp failed - read the error above" }
    }
    if ($ok) {
        $ok = Invoke-Native { & $rsapPy -m rsap_mcp --selfcheck }
        if (-not $ok) { $hint = "rsap-mcp self-check failed - is Robot installed and licensed? See docs/14" }
    }
    if ($ok) {
        Write-Ok "Robot MCP" "rsap-mcp installed; registered via the repo's .mcp.json (server 'robot')."
    } else {
        Write-Fail "Robot MCP" "rsap-mcp setup failed" $hint
    }
} else {
    Write-Skip "Robot MCP" "Robot not detected - skipping. Re-run with -WithRobot to force."
}

# --- 7. Revit MCP (Autodesk add-on, installed separately) ---------------------
Write-Host "[7/8] Revit MCP..." -ForegroundColor Yellow
$revitExe = $null
$revitDirs = @(Get-ChildItem "$env:ProgramFiles\Autodesk" -Directory -Filter "Revit 20* MCP Server*" -ErrorAction SilentlyContinue |
    Sort-Object @{ Expression = { $_.Name -match "Write-Tools" }; Descending = $true }, Name -Descending)
foreach ($d in $revitDirs) {
    $exe = Join-Path $d.FullName "Autodesk.RevitMcpServer.Stdio.exe"
    if (Test-Path $exe) { $revitExe = $exe; break }
}
if (-not $revitExe) {
    Write-Skip "Revit MCP" "Revit MCP add-on not found - skipping. To use Revit, install it from Autodesk Account (docs/17)."
} elseif ($revitExe -like "*Revit 2027 MCP Server Write-Tools Technical Preview*") {
    Write-Ok "Revit MCP" "Found $(Split-Path (Split-Path $revitExe) -Leaf); registered via the repo's .mcp.json (server 'revit')."
} elseif (Get-Command claude -ErrorAction SilentlyContinue) {
    # A different edition/path than .mcp.json: a local-scope entry overrides the project one.
    if (Invoke-Native { claude mcp add --scope local revit -- "$revitExe" }) {
        Write-Ok "Revit MCP" "Found $(Split-Path (Split-Path $revitExe) -Leaf); registered for this machine (local scope, overrides .mcp.json)."
    } else {
        Write-Fail "Revit MCP" "'claude mcp add' failed" "Run by hand: claude mcp add --scope local revit -- `"$revitExe`""
    }
} else {
    Write-Fail "Revit MCP" "Claude Code CLI not found" "Install Claude Code (docs/01), then re-run ./setup.ps1"
}

# --- 8. Auto-push opt-in ----------------------------------------------------
Write-Host "[8/8] Learning-loop auto-push..." -ForegroundColor Yellow
$marker = "$repo\.claude\autopush.enabled"
if ($EnableAutoPush) {
    New-Item -ItemType Directory -Force -Path "$repo\.claude" | Out-Null
    Set-Content -Path $marker -Value "Auto-push enabled on this machine." -Encoding utf8
    Write-Ok "Auto-push" "Auto-push ENABLED - captured sessions will commit & push on session end."
} else {
    Write-Host "  Auto-push OFF. Re-run with -EnableAutoPush to turn it on." -ForegroundColor Green
    Add-Result "Auto-push" "OFF"
}

# --- Summary ----------------------------------------------------------------
Write-Host "`n== Summary ==" -ForegroundColor Cyan
foreach ($r in $script:results) {
    $color = switch ($r.Status) { "OK" { "Green" } "FAILED" { "Red" } default { "DarkYellow" } }
    Write-Host ("  {0,-8} {1}" -f $r.Status, $r.Step) -ForegroundColor $color
}
$failed = @($script:results | Where-Object { $_.Status -eq "FAILED" })
if ($failed.Count -gt 0) {
    Write-Host "`n$($failed.Count) step(s) FAILED - see the 'Fix:' hints above, then re-run ./setup.ps1 (it is safe to re-run)." -ForegroundColor Red
} else {
    Write-Host "`nAll steps succeeded." -ForegroundColor Green
}

Write-Host "`n== Next ==" -ForegroundColor Cyan
Write-Host "Use the repo's Python, not the system one: .venv\Scripts\python"
Write-Host "  (or activate it first: .venv\Scripts\Activate.ps1)"
Write-Host "RESTART Claude Code in this folder so hooks/MCP/skills load, then ask:"
if ($matlabRoot -and $mcpRegistered) {
    Write-Host '  "List your MATLAB MCP tools and run detect_matlab_toolboxes."'
} else {
    Write-Host '  "A steel part has stresses sx = 180, sy = 60, txy = 40 MPa. The yield strength is 250 MPa.'
    Write-Host '   Is it yielding by the von Mises criterion? Use SymPy in .venv\Scripts\python, show the working and plot the yield surface."'
}

if ($failed.Count -gt 0) { exit 1 }
