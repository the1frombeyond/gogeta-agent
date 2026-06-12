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
    Write-Host "$C_CYAN    ██████╗  ██████╗  ██████╗ ███████╗████████╗ █████╗$C_RESET" -ForegroundColor Cyan
    Write-Host "$C_CYAN   ██╔════╝ ██╔═══██╗██╔════╝ ██╔════╝╚══██╔══╝██╔══██╗$C_RESET" -ForegroundColor Cyan
    Write-Host "$C_CYAN   ██║  ███╗██║   ██║██║  ███╗█████╗     ██║   ███████║$C_RESET" -ForegroundColor Cyan
    Write-Host "$C_CYAN   ██║   ██║██║   ██║██║   ██║██╔══╝     ██║   ██╔══██║$C_RESET" -ForegroundColor Cyan
    Write-Host "$C_CYAN   ╚██████╔╝╚██████╔╝╚██████╔╝███████╗   ██║   ██║  ██║$C_RESET" -ForegroundColor Cyan
    Write-Host "$C_CYAN    ╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝   ╚═╝   ╚═╝  ╚═╝$C_RESET" -ForegroundColor Cyan
    Write-Host "$C_BOLD$C_YEL       The Self-Improving AI Agent — v3.0$C_RESET" -ForegroundColor Yellow
    Write-Host "$C_DIM       Installing to: $GOGETA_HOME$C_RESET" -ForegroundColor DarkGray
    Write-Host ""
}

function Write-Step   { Write-Host "$C_CYAN  ◆$C_RESET $($args[0])$C_RESET" -ForegroundColor White }
function Write-OK     { Write-Host "$C_GREEN  ✓$C_RESET $($args[0])$C_RESET" -ForegroundColor Green }
function Write-Info   { Write-Host "$C_BLUE  ℹ$C_RESET $($args[0])$C_RESET" -ForegroundColor Blue }
function Write-Warn   { Write-Host "$C_YEL  ⚠$C_RESET $($args[0])$C_RESET" -ForegroundColor Yellow }
function Write-Err    { Write-Host "$C_RED  ✗$C_RESET $($args[0])$C_RESET" -ForegroundColor Red; exit 1 }

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
        if (Test-Path $GOGETA_HOME) { Remove-Item -Recurse -Force $GOGETA_HOME }
        git clone --depth 1 --branch $BRANCH $REPO_URL $GOGETA_HOME
        Write-OK "Repository cloned"
    }
}

# ── Setup venv ────────────────────────────────────────────────────────────
function Install-Python {
    Write-Step "Setting up Python virtual environment..."
    if (-not (Test-Path "$GOGETA_HOME\.venv")) {
        python -m venv "$GOGETA_HOME\.venv"
    }
    $pip = "$GOGETA_HOME\.venv\Scripts\pip.exe"
    & $pip install --upgrade pip -q
    & $pip install -e "$GOGETA_HOME" -q
    Write-OK "Python dependencies installed"
}

# ── Build TUI ─────────────────────────────────────────────────────────────
function Install-TUI {
    if (-not (Test-Path "$GOGETA_HOME\ui-tui")) { Write-Info "TUI directory not found, skipping"; return }
    Write-Step "Building Terminal UI..."
    Push-Location "$GOGETA_HOME\ui-tui"
    try {
        npm install --silent
        npm run build
        Write-OK "TUI built"
    } finally { Pop-Location }
}

# ── Launcher ──────────────────────────────────────────────────────────────
function Install-Launcher {
    Write-Step "Creating launcher..."
    if (-not (Test-Path $GOGETA_BIN)) { New-Item -ItemType Directory -Path $GOGETA_BIN -Force | Out-Null }
    $launcher = "$GOGETA_BIN\gogeta.cmd"
    "@echo off
`"%~dp0..\.venv\Scripts\gogeta.exe`" %*" | Out-File -FilePath $launcher -Encoding ascii
    Write-OK "Launcher created at $launcher"

    $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($currentPath -notlike "*$GOGETA_BIN*") {
        Write-Step "Adding to PATH..."
        [Environment]::SetEnvironmentVariable("Path", "$currentPath;$GOGETA_BIN", "User")
        $env:Path = "$env:Path;$GOGETA_BIN"
        Write-OK "Added to PATH"
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
            if (Get-Item $path -ErrorAction SilentlyContinue | Where-Object { $_.PSIsContainer }) {
                Remove-Item -Recurse -Force $path -ErrorAction SilentlyContinue
            } else {
                Remove-Item -Force $path -ErrorAction SilentlyContinue
            }
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
    Push-Location $GOGETA_HOME
    try {
        & "$GOGETA_HOME\.venv\Scripts\python.exe" -m gogeta_cli.main setup
    } finally { Pop-Location }
}

# ── Success ───────────────────────────────────────────────────────────────
function Show-Success {
    Write-Host ""
    Write-Host "$C_GREEN  ╔═══════════════════════════════════════════════╗$C_RESET" -ForegroundColor Green
    Write-Host "$C_GREEN  ║$C_RESET$C_BOLD$C_YEL      Gogeta Agent installed successfully!     $C_RESET$C_GREEN║$C_RESET" -ForegroundColor Yellow
    Write-Host "$C_GREEN  ╚═══════════════════════════════════════════════╝$C_RESET" -ForegroundColor Green
    Write-Host ""
    Write-Host "  $C_CYAN Install path:$C_RESET  $GOGETA_HOME"
    Write-Host "  $C_CYAN Command:$C_RESET       gogeta"
    Write-Host "  $C_CYAN TUI:$C_RESET           gogeta --tui"
    Write-Host ""
    Write-Host "  $C_DIM Run 'gogeta' anytime to chat with your agent.$C_RESET" -ForegroundColor DarkGray
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
