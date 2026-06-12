#!/usr/bin/env bash
# ============================================================================
# Gogeta Agent Installer — thin wrapper
# ============================================================================
# Downloads and runs the full installer from scripts/install.sh
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/the1frombeyond/gogeta-agent/main/install.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/the1frombeyond/gogeta-agent/main/install.sh | bash -s -- --skip-setup
# ============================================================================

set -euo pipefail

BASE="https://raw.githubusercontent.com/the1frombeyond/gogeta-agent/main"
FULL_INSTALLER_URL="$BASE/scripts/install.sh"

echo ">>> Downloading Gogeta installer..."
if command -v curl >/dev/null 2>&1; then
    bash <(curl -fsSL "$FULL_INSTALLER_URL") "$@"
elif command -v wget >/dev/null 2>&1; then
    bash <(wget -qO- "$FULL_INSTALLER_URL") "$@"
else
    echo "ERROR: curl or wget required" >&2
    exit 1
fi
