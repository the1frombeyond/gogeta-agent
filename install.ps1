# ============================================================================
# Gogeta Agent Installer — thin wrapper
# ============================================================================
# Downloads and runs the full installer from scripts/install.ps1
#
# Usage:
#   iex (irm https://raw.githubusercontent.com/the1frombeyond/gogeta-agent/main/install.ps1)
#   iex (irm https://raw.githubusercontent.com/the1frombeyond/gogeta-agent/main/install.ps1) -SkipSetup
# ============================================================================

$BASE = "https://raw.githubusercontent.com/the1frombeyond/gogeta-agent/main"
$FULL_INSTALLER_URL = "$BASE/scripts/install.ps1"

Write-Host ">>> Downloading Gogeta installer..." -ForegroundColor Cyan
$scriptContent = Invoke-RestMethod -Uri $FULL_INSTALLER_URL
$scriptBlock = [ScriptBlock]::Create($scriptContent)
& $scriptBlock @args
