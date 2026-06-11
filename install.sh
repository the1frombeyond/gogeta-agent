#!/usr/bin/env bash
# ============================================================================
# Gogeta Agent Installer for Linux / macOS
# ============================================================================
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/the1frombeyond/gogeta-agent/main/install.sh | bash
#   wget -qO- https://raw.githubusercontent.com/the1frombeyond/gogeta-agent/main/install.sh | bash
#
# Requirements: Python 3.11+, Git, Node.js, npm
# ============================================================================

set -euo pipefail

GOGETA_HOME="${HOME}/.gogeta"
REPO_URL="https://github.com/the1frombeyond/gogeta-agent.git"
BRANCH="main"

log_step()  { printf "\033[36m>>> %s\033[0m\n" "$*"; }
log_ok()    { printf "\033[32mOK  %s\033[0m\n" "$*"; }
log_err()   { printf "\033[31mERROR: %s\033[0m\n" "$*" >&2; exit 1; }

# --- Check prerequisites ---
log_step "Checking prerequisites..."

command -v python3 >/dev/null 2>&1 || log_err "Python 3 not found. Install Python 3.11+ from https://python.org"
pyver=$(python3 --version 2>&1)
if echo "$pyver" | grep -qE "Python 3\.(1[1-9]|[2-9][0-9])"; then
    log_ok "$pyver"
else
    log_err "Python 3.11+ required (found $pyver)"
fi

command -v git >/dev/null 2>&1 || log_err "Git not found. Install from https://git-scm.com"
log_ok "Git $(git --version | awk '{print $3}')"

command -v node >/dev/null 2>&1 || log_err "Node.js not found. Install from https://nodejs.org"
command -v npm >/dev/null 2>&1  || log_err "npm not found. Install from https://nodejs.org"
log_ok "Node.js $(node --version) / npm $(npm --version)"

# --- Clone or update ---
if [ -d "$GOGETA_HOME/.git" ]; then
    log_step "Updating existing installation..."
    cd "$GOGETA_HOME"
    git pull origin "$BRANCH"
    log_ok "Repository updated"
else
    log_step "Cloning Gogeta repository..."
    rm -rf "$GOGETA_HOME"
    git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$GOGETA_HOME"
    log_ok "Repository cloned to $GOGETA_HOME"
fi

cd "$GOGETA_HOME"

# --- Create Python environment ---
log_step "Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    log_ok "Virtual environment created"
fi
source .venv/bin/activate

log_step "Installing Python dependencies..."
pip install --upgrade pip -q
pip install -e . -q
log_ok "Python dependencies installed"

# --- Build TUI ---
if [ -d "ui-tui" ]; then
    log_step "Building Terminal UI..."
    cd ui-tui
    npm install --silent
    npm run build
    cd "$GOGETA_HOME"
    log_ok "TUI built"
else
    printf "\033[33m  (TUI directory not found, skipping)\033[0m\n"
fi

# --- Create launcher ---
log_step "Creating gogeta launcher..."
mkdir -p "${HOME}/.local/bin"
LAUNCHER="${HOME}/.local/bin/gogeta"
cat > "$LAUNCHER" << 'SCRIPT'
#!/usr/bin/env bash
exec "${HOME}/.gogeta/.venv/bin/gogeta" "$@"
SCRIPT
chmod +x "$LAUNCHER"
log_ok "Launcher created at $LAUNCHER"

# --- PATH hint ---
case ":${PATH}:" in
    *:"${HOME}/.local/bin":*) ;;
    *)
        log_step "Adding ~/.local/bin to PATH..."
        # Detect shell and add to appropriate rc file
        rc_file=""
        if [ -n "${ZSH_VERSION-}" ]; then
            rc_file="${HOME}/.zshrc"
        elif [ -n "${BASH_VERSION-}" ]; then
            rc_file="${HOME}/.bashrc"
        elif [ -f "${HOME}/.config/fish/config.fish" ]; then
            rc_file="${HOME}/.config/fish/config.fish"
        fi
        if [ -n "$rc_file" ]; then
            echo "" >> "$rc_file"
            echo "# Gogeta" >> "$rc_file"
            echo 'export PATH="${HOME}/.local/bin:${PATH}"' >> "$rc_file"
            log_ok "Added ~/.local/bin to PATH in $rc_file (re-login or source to apply)"
        fi
        ;;
esac

echo ""
echo -e "\033[36m============================================\033[0m"
echo -e "\033[32m  Gogeta Agent installed!\033[0m"
echo -e "\033[36m============================================\033[0m"
echo ""
echo "  Install path: ${GOGETA_HOME}"
echo ""
echo -e "\033[33m  Run:  gogeta\033[0m"
echo -e "\033[33m  TUI:  gogeta --tui\033[0m"
echo ""
echo "  Docs: https://github.com/the1frombeyond/gogeta-agent"
echo ""
