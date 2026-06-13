# ============================================================================
#  ██████╗  ██████╗  ██████╗ ███████╗████████╗ █████╗
# ██╔════╝ ██╔═══██╗██╔════╝ ██╔════╝╚══██╔══╝██╔══██╗
# ██║  ███╗██║   ██║██║  ███╗█████╗     ██║   ███████║
# ██║   ██║██║   ██║██║   ██║██╔══╝     ██║   ██╔══██║
# ╚██████╔╝╚██████╔╝╚██████╔╝███████╗   ██║   ██║  ██║
#  ╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝   ╚═╝   ╚═╝  ╚═╝
# ============================================================================
# Gogeta Agent Installer for Windows
# ============================================================================
# Usage:
#   iex (irm https://raw.githubusercontent.com/the1frombeyond/gogeta-agent/main/install.ps1)
# ============================================================================

$ErrorActionPreference = "Stop"

# ── Config ────────────────────────────────────────────────────────────────
$GOGETA_HOME = "$env:USERPROFILE\.gogeta"
$REPO_URL = "https://github.com/the1frombeyond/gogeta-agent.git"
$BRANCH = "main"
$GOGETA_BIN = "$GOGETA_HOME\bin"

# ── Colors ────────────────────────────────────────────────────────────────
$C_RESET = [char]27 + "[0m"
$C_RED   = [char]27 + "[91m"
$C_GREEN = [char]27 + "[92m"
$C_YEL   = [char]27 + "[93m"
$C_BLUE  = [char]27 + "[94m"
$C_MAG   = [char]27 + "[95m"
$C_CYAN  = [char]27 + "[96m"
$C_BOLD  = [char]27 + "[1m"
$C_DIM   = [char]27 + "[2m"

# ── Banner ────────────────────────────────────────────────────────────────
function Show-Banner {
    Clear-Host
    Write-Host ""
    Write-Host "$C_CYAN    ██████╗  ██████╗  ██████╗ ███████╗████████╗ █████╗$C_RESET"
    Write-Host "$C_CYAN   ██╔════╝ ██╔═══██╗██╔════╝ ██╔════╝╚══██╔══╝██╔══██╗$C_RESET"
    Write-Host "$C_CYAN   ██║  ███╗██║   ██║██║  ███╗█████╗     ██║   ███████║$C_RESET"
    Write-Host "$C_CYAN   ██║   ██║██║   ██║██║   ██║██╔══╝     ██║   ██╔══██║$C_RESET"
    Write-Host "$C_CYAN   ╚██████╔╝╚██████╔╝╚██████╔╝███████╗   ██║   ██║  ██║$C_RESET"
    Write-Host "$C_CYAN    ╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝   ╚═╝   ╚═╝  ╚═╝$C_RESET"
    Write-Host "$C_BOLD$C_YEL       The Self-Improving AI Agent — v3.0$C_RESET"
    Write-Host "$C_DIM       Installing to: $GOGETA_HOME$C_RESET"
    Write-Host ""
}

function Write-Step   { Write-Host "$C_CYAN  ◆$C_RESET $($args[0])$C_RESET" }
function Write-OK     { Write-Host "$C_GREEN  ✓$C_RESET $($args[0])$C_RESET" }
function Write-Info   { Write-Host "$C_BLUE  ℹ$C_RESET $($args[0])$C_RESET" }
function Write-Warn   { Write-Host "$C_YEL  ⚠$C_RESET $($args[0])$C_RESET" }
function Write-Err    { Write-Host "$C_RED  ✗$C_RESET $($args[0])$C_RESET"; exit 1 }

# ── Prerequisites ─────────────────────────────────────────────────────────
function Check-Prerequisites {
    Write-Step "Checking prerequisites..."

    try {
        $pyVer = (python --version) 2>&1
        if ($pyVer -match "Python (\d+)\.(\d+)") {
            $maj = [int]$Matches[1]; $min = [int]$Matches[2]
            if ($maj -gt 3 -or ($maj -eq 3 -and $min -ge 11)) {
                Write-OK "Python $maj.$min+"
            } else {
                Write-Err "Python 3.11+ required (found $maj.$min)"
            }
        }
    } catch { Write-Err "Python not found. Install from https://python.org" }

    try { $null = git --version; Write-OK "Git" }
    catch { Write-Err "Git not found. Install from https://git-scm.com" }

    try { $null = node --version; $null = npm --version; Write-OK "Node.js + npm" }
    catch { Write-Err "Node.js + npm required. Install from https://nodejs.org" }

    # Warn about npm global gogeta conflict
    $npmGogeta = npm list -g --depth=0 2>$null | Select-String "gogeta"
    if ($npmGogeta) {
        Write-Warn "npm global package '$npmGogeta' will shadow gogeta command"
        Write-Info "We will override it with a .ps1 launcher"
    }
}

# ── Clone / Update ────────────────────────────────────────────────────────
function Install-Repo {
    if (Test-Path "$GOGETA_HOME\.git") {
        Write-Step "Updating existing installation..."
        Push-Location $GOGETA_HOME
        try { git pull origin $BRANCH } finally { Pop-Location }
        Write-OK "Repository updated"
    } else {
        Write-Step "Cloning Gogeta repository..."
        if (Test-Path $GOGETA_HOME) {
            Remove-Item -Recurse -Force $GOGETA_HOME -ErrorAction SilentlyContinue
            Start-Sleep -Milliseconds 500
        }

        # Retry clone up to 3 times (network issues are common)
        $cloneOk = $false
        for ($attempt = 1; $attempt -le 3; $attempt++) {
            if ($attempt -gt 1) {
                Write-Info "Retry $attempt/3..."
                Start-Sleep -Seconds 5
            }
            $result = git clone --depth 1 --single-branch --branch $BRANCH $REPO_URL $GOGETA_HOME 2>&1
            if ($LASTEXITCODE -eq 0 -and (Test-Path "$GOGETA_HOME\pyproject.toml")) {
                $cloneOk = $true
                break
            }
        }

        if (-not $cloneOk) {
            Write-Err "Failed to clone repository after 3 attempts. Check your network connection."
        }
        Write-OK "Repository cloned"
    }
}

# ── Setup venv ────────────────────────────────────────────────────────────
function Install-Python {
    Write-Step "Setting up Python virtual environment..."
    if (-not (Test-Path "$GOGETA_HOME\.venv")) {
        $result = python -m venv "$GOGETA_HOME\.venv" 2>&1
        if ($LASTEXITCODE -ne 0) { Write-Err "Failed to create venv: $result" }
    }
    $pip = "$GOGETA_HOME\.venv\Scripts\pip.exe"

    Write-Info "Upgrading pip..."
    $result = & $pip install --upgrade pip -q 2>&1
    if ($LASTEXITCODE -ne 0) { Write-Warn "pip upgrade failed: $result" }

    Write-Info "Installing Python dependencies..."
    $result = & $pip install -e "$GOGETA_HOME[cli]" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "pip install (core) failed, trying minimal..."
        $result = & $pip install --no-deps -e "$GOGETA_HOME" 2>&1
        if ($LASTEXITCODE -ne 0) { Write-Err "pip install failed: $result" }
        Write-Warn "Run 'pip install -e ""$GOGETA_HOME[cli]""' manually for full support"
    }

    if (-not (Test-Path "$GOGETA_HOME\.venv\Scripts\gogeta.exe")) {
        Write-Err "Entry point gogeta.exe not created after pip install"
    }
    Write-OK "Python dependencies installed"
}

# ── Build TUI ─────────────────────────────────────────────────────────────
function Install-TUI {
    if (-not (Test-Path "$GOGETA_HOME\ui-tui")) { Write-Info "TUI directory not found, skipping"; return }
    Write-Step "Building Terminal UI..."
    Push-Location "$GOGETA_HOME\ui-tui"
    try {
        $result = npm install 2>&1
        if ($LASTEXITCODE -ne 0) { Write-Warn "npm install failed, skipping TUI"; return }
        $result = npm run build 2>&1
        if ($LASTEXITCODE -ne 0) { Write-Warn "npm run build failed, skipping TUI"; return }
        Write-OK "TUI built"
    } finally { Pop-Location }
}

# ── Launcher ──────────────────────────────────────────────────────────────
function Install-Launcher {
    Write-Step "Creating launcher..."
    if (-not (Test-Path $GOGETA_BIN)) { New-Item -ItemType Directory -Path $GOGETA_BIN -Force | Out-Null }
    $exe = "$GOGETA_HOME\.venv\Scripts\gogeta.exe"

    # .cmd launcher (cmd.exe, older PowerShell)
    $launcherCmd = "$GOGETA_BIN\gogeta.cmd"
    "@echo off
`"%~dp0..\.venv\Scripts\gogeta.exe`" %*" | Out-File -FilePath $launcherCmd -Encoding ascii

    # .ps1 launcher (modern PowerShell — overrides npm's gogeta.ps1)
    $launcherPs1 = "$GOGETA_BIN\gogeta.ps1"
    "& '$exe' @args" | Out-File -FilePath $launcherPs1 -Encoding utf8

    Write-OK "Launchers created"

    # Add to PATH — insert at front so .gogeta\bin beats npm global dir
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($currentPath -notlike "*$GOGETA_BIN*") {
        Write-Step "Adding to PATH..."
        [Environment]::SetEnvironmentVariable("Path", "$GOGETA_BIN;$currentPath", "User")
        $env:Path = "$GOGETA_BIN;$env:Path"
        Write-OK "Added to PATH"
    } else {
        Write-Info "Already in PATH"
    }

    # Warn if npm gogeta launchers exist
    $npmDir = "$env:APPDATA\npm"
    if (Test-Path "$npmDir\gogeta.ps1") {
        Write-Warn "npm gogeta.ps1 found. Run: Remove-Item '$npmDir\gogeta.ps1' -Force"
    }
}

# ── Cleanup ───────────────────────────────────────────────────────────────
function Remove-Unwanted {
    Write-Step "Cleaning up development-only folders..."
    $unwanted = @(
        ".github", "tests", "website", "scripts", "release",
        "plans", ".plans", "infographic", "datagen-config-examples",
        "optional-mcps", "packaging", "nix", "TODO-NEXT-SESSION.md",
        "GOGETA_TUI_REDESIGN.md", "GOGETA_AUTONOMY_DIRECTIVE.md"
    )
    $removed = 0
    foreach ($item in $unwanted) {
        $path = Join-Path $GOGETA_HOME $item
        if (Test-Path $path) {
            Remove-Item -Recurse -Force $path -ErrorAction SilentlyContinue
            $removed++
        }
    }
    Write-OK "Cleaned up $removed dev-only folders"
}

# ── Setup Wizard ──────────────────────────────────────────────────────────
function Invoke-Setup {
    Write-Host ""
    Write-Step "Starting Gogeta setup wizard..."
    Write-Host ""
    $python = "$GOGETA_HOME\.venv\Scripts\python.exe"
    if (-not (Test-Path $python)) {
        Write-Err "Python not found at $python"
    }
    Push-Location $GOGETA_HOME
    try {
        & $python -m gogeta_cli.main setup
        if ($LASTEXITCODE -ne 0) { Write-Warn "Setup wizard exited with code $LASTEXITCODE" }
    } finally { Pop-Location }
}

# ── Success ───────────────────────────────────────────────────────────────
function Show-Success {
    Write-Host ""
    Write-Host "$C_GREEN  ╔═══════════════════════════════════════════════╗$C_RESET"
    Write-Host "$C_GREEN  ║$C_RESET$C_BOLD$C_YEL      Gogeta Agent installed successfully!     $C_RESET$C_GREEN║$C_RESET"
    Write-Host "$C_GREEN  ╚═══════════════════════════════════════════════╝$C_RESET"
    Write-Host ""
    Write-Host "  $C_CYAN Install path:$C_RESET  $GOGETA_HOME"
    Write-Host "  $C_CYAN Command:$C_RESET       gogeta"
    Write-Host "  $C_CYAN TUI:$C_RESET           gogeta --tui"
    Write-Host ""
    Write-Host "  $C_DIM Open a NEW PowerShell window, then run 'gogeta' to chat.$C_RESET"
    Write-Host ""
}

# ── Main ──────────────────────────────────────────────────────────────────
Show-Banner
Check-Prerequisites
Install-Repo
Install-Python
Install-TUI
Install-Launcher
Remove-Unwanted
Invoke-Setup
Show-Success
