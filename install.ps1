# ============================================================================
# Gogeta Agent Installer for Windows
# ============================================================================
# Usage:
#   iex (irm https://raw.githubusercontent.com/the1frombeyond/gogeta-agent/main/install.ps1)
#
# Requirements: Python 3.11+, Git, Node.js, npm
# ============================================================================

$ErrorActionPreference = "Stop"

$GOGETA_HOME = "$env:USERPROFILE\.gogeta"
$REPO_URL = "https://github.com/the1frombeyond/gogeta-agent.git"
$BRANCH = "main"

function Write-Step {
    param([string]$Message)
    Write-Host ">>> $Message" -ForegroundColor Cyan
}

function Write-Error {
    param([string]$Message)
    Write-Host "ERROR: $Message" -ForegroundColor Red
    exit 1
}

function Write-Success {
    param([string]$Message)
    Write-Host "OK  $Message" -ForegroundColor Green
}

# --- Check prerequisites ---
Write-Step "Checking prerequisites..."

try {
    $pyVer = (python --version) 2>&1
    if ($pyVer -match "Python (\d+)\.(\d+)") {
        $major = [int]$Matches[1]
        $minor = [int]$Matches[2]
        if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 11)) {
            Write-Success "Python $major.$minor+"
        } else {
            Write-Error "Python 3.11+ required (found $major.$minor)"
        }
    } else {
        Write-Error "Could not detect Python version"
    }
} catch {
    Write-Error "Python not found. Install Python 3.11+ from https://python.org"
}

try {
    $gitVer = (git --version) 2>&1
    if ($gitVer -match "git version") {
        Write-Success "Git"
    }
} catch {
    Write-Error "Git not found. Install Git from https://git-scm.com"
}

try {
    $nodeVer = (node --version) 2>&1
    $npmVer = (npm --version) 2>&1
    Write-Success "Node.js $nodeVer / npm $npmVer"
} catch {
    Write-Error "Node.js and npm are required. Install from https://nodejs.org"
}

# --- Clone or update ---
if (Test-Path "$GOGETA_HOME\.git") {
    Write-Step "Updating existing installation..."
    Push-Location $GOGETA_HOME
    try {
        git pull origin $BRANCH
        Write-Success "Repository updated"
    } finally {
        Pop-Location
    }
} else {
    Write-Step "Cloning Gogeta repository..."
    if (Test-Path $GOGETA_HOME) {
        Remove-Item -Recurse -Force $GOGETA_HOME
    }
    git clone --depth 1 --branch $BRANCH $REPO_URL $GOGETA_HOME
    Write-Success "Repository cloned to $GOGETA_HOME"
}

Set-Location $GOGETA_HOME

# --- Create Python environment ---
Write-Step "Setting up Python virtual environment..."
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    Write-Success "Virtual environment created"
}

$pip = "$GOGETA_HOME\.venv\Scripts\pip.exe"
$python = "$GOGETA_HOME\.venv\Scripts\python.exe"

Write-Step "Installing Python dependencies..."
& $pip install --upgrade pip -q
& $pip install -e . -q
Write-Success "Python dependencies installed"

# --- Build TUI ---
Write-Step "Building Terminal UI..."
if (Test-Path "ui-tui") {
    Push-Location "ui-tui"
    try {
        npm install --silent
        npm run build
        Write-Success "TUI built"
    } finally {
        Pop-Location
    }
} else {
    Write-Host "  (TUI directory not found, skipping)" -ForegroundColor Yellow
}

# --- Create launcher ---
Write-Step "Creating gogeta launcher..."
$binDir = "$GOGETA_HOME\bin"
if (-not (Test-Path $binDir)) {
    New-Item -ItemType Directory -Path $binDir -Force | Out-Null
}

$launcherPath = "$binDir\gogeta.cmd"
@"
@echo off
"%~dp0..\.venv\Scripts\gogeta.exe" %*
"@ | Out-File -FilePath $launcherPath -Encoding ascii

<# Also create PowerShell launcher #>
$psLauncherPath = "$binDir\gogeta.ps1"
@"
& "$env:USERPROFILE\.gogeta\.venv\Scripts\gogeta.exe" @args
"@ | Out-File -FilePath $psLauncherPath -Encoding ascii

Write-Success "Launcher created at $launcherPath"

# --- Add to PATH if not already ---
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -notlike "*$binDir*") {
    Write-Step "Adding Gogeta to user PATH..."
    [Environment]::SetEnvironmentVariable("Path", "$currentPath;$binDir", "User")
    $env:Path = "$env:Path;$binDir"
    Write-Success "Added $binDir to PATH (re-login or restart terminal to apply)"
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Gogeta Agent installed!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Install path: $GOGETA_HOME" -ForegroundColor White
Write-Host ""
Write-Host "  Run:  gogeta" -ForegroundColor Yellow
Write-Host "  TUI:  gogeta --tui" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Docs: https://github.com/the1frombeyond/gogeta-agent" -ForegroundColor White
Write-Host ""
